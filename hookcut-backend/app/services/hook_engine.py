import json
import time
import logging
from dataclasses import dataclass
from typing import Optional

from app.llm.provider import get_provider, get_fallback_provider
from app.llm.prompts.hook_identification import build_hook_prompt
from app.llm.prompts.constants import HOOK_TYPES, FUNNEL_ROLES
from app.utils.time_format import timestamp_to_seconds
from app.config import get_settings
from app.exceptions import HookEngineError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [0, 5, 30]  # seconds before each attempt (longer for rate limits)


@dataclass
class HookCandidate:
    rank: int
    hook_text: str
    start_time: str
    end_time: str
    start_seconds: float
    end_seconds: float
    hook_type: str
    funnel_role: str
    scores: dict
    attention_score: float
    platform_dynamics: str
    viewer_psychology: str
    improvement_suggestion: str
    is_composite: bool


@dataclass
class HookEngineResult:
    hooks: list[HookCandidate]
    provider: str
    model: str
    attempts: int
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class HookEngine:
    """
    LLM-only hook identification engine.
    Sends full transcript to LLM in one pass, returns exactly 5 hook candidates.
    Retry: 3 attempts with backoff (0s, 5s, 30s). 3rd attempt uses fallback provider.
    """

    def analyze(
        self, transcript: str, niche: str, language: str = "English",
        rules: list[dict] | None = None,
    ) -> HookEngineResult:
        settings = get_settings()
        if rules:
            from app.llm.prompts.hook_identification import build_hook_prompt_from_rules
            prompt = build_hook_prompt_from_rules(rules, niche, transcript, language)
        else:
            prompt = build_hook_prompt(niche, transcript, language)
        primary = get_provider(settings.LLM_PRIMARY_PROVIDER)

        last_error = None
        for attempt in range(MAX_RETRIES):
            if attempt > 0:
                time.sleep(RETRY_DELAYS[attempt])

            # Use fallback provider on the last attempt
            provider = primary if attempt < MAX_RETRIES - 1 else self._get_retry_provider(primary)

            try:
                logger.info(
                    f"Hook analysis attempt {attempt + 1}/{MAX_RETRIES} "
                    f"via {provider.name}"
                )
                response = provider.generate(prompt, max_tokens=8000, json_mode=True)
                hooks = self._parse_and_validate(response.text)

                return HookEngineResult(
                    hooks=hooks,
                    provider=response.provider,
                    model=response.model,
                    attempts=attempt + 1,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Hook analysis attempt {attempt + 1} failed: {e}"
                )

        raise HookEngineError(
            f"All {MAX_RETRIES} hook analysis attempts failed. Last error: {last_error}"
        )

    def _get_retry_provider(self, primary):
        """Try fallback provider on last attempt, fall back to primary if not configured."""
        try:
            return get_fallback_provider(primary.name)
        except Exception as e:
            logger.warning("Fallback provider unavailable, using primary: %s", e)
            return primary

    def _parse_and_validate(self, raw_text: str) -> list[HookCandidate]:
        """Parse LLM JSON response and validate exactly 5 hooks."""
        # Clean markdown fences if present
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.startswith("json"):
            text = text[4:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise HookEngineError(f"LLM returned invalid JSON: {e}")

        hooks_data = data.get("hooks", [])
        if len(hooks_data) != 5:
            raise HookEngineError(
                f"Expected exactly 5 hooks, got {len(hooks_data)}"
            )

        hooks = []
        for h in hooks_data:
            hook = self._validate_hook(h)
            hooks.append(hook)

        # Verify non-overlapping timestamps
        self._check_no_overlaps(hooks)

        return hooks

    def _validate_hook(self, h: dict) -> HookCandidate:
        """Validate a single hook dict from LLM output."""
        required = ["rank", "hook_text", "start_time", "end_time", "hook_type", "funnel_role"]
        for field in required:
            if field not in h:
                raise HookEngineError(f"Hook missing required field: {field}")

        # Validate hook_type
        hook_type = h["hook_type"]
        if hook_type not in HOOK_TYPES:
            # Attempt fuzzy match
            for ht in HOOK_TYPES:
                if ht.lower() == hook_type.lower():
                    hook_type = ht
                    break
            else:
                logger.warning(f"Unknown hook type '{hook_type}', keeping as-is")

        # Validate funnel_role
        funnel_role = h["funnel_role"]
        if funnel_role not in FUNNEL_ROLES:
            for fr in FUNNEL_ROLES:
                if fr.lower() == funnel_role.lower().replace(" ", "_"):
                    funnel_role = fr
                    break
            else:
                logger.warning(f"Unknown funnel role '{funnel_role}', keeping as-is")

        # Parse scores
        scores = h.get("scores", {})
        for dim in ["scroll_stop", "curiosity_gap", "stakes_intensity",
                     "emotional_voltage", "standalone_clarity",
                     "thematic_focus", "thought_completeness"]:
            val = scores.get(dim, 0)
            scores[dim] = max(0, min(10, float(val)))

        # Parse timestamps
        start_time = str(h["start_time"])
        end_time = str(h["end_time"])
        is_composite = "+" in start_time or "composite" in start_time.lower()

        try:
            start_seconds = timestamp_to_seconds(start_time)
            end_seconds = timestamp_to_seconds(end_time)
        except ValueError:
            start_seconds = 0.0
            end_seconds = 0.0

        attention_score = max(0, min(10, float(h.get("attention_score", 0))))

        return HookCandidate(
            rank=int(h["rank"]),
            hook_text=str(h["hook_text"]),
            start_time=start_time,
            end_time=end_time,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            hook_type=hook_type,
            funnel_role=funnel_role,
            scores=scores,
            attention_score=attention_score,
            platform_dynamics=str(h.get("platform_dynamics", "")),
            viewer_psychology=str(h.get("viewer_psychology", "")),
            improvement_suggestion=str(h.get("improvement_suggestion", "")),
            is_composite=is_composite,
        )

    def _check_no_overlaps(self, hooks: list[HookCandidate]):
        """Warn (but don't fail) if hook timestamps overlap."""
        non_composite = [h for h in hooks if not h.is_composite]
        sorted_hooks = sorted(non_composite, key=lambda h: h.start_seconds)
        for i in range(len(sorted_hooks) - 1):
            if sorted_hooks[i].end_seconds > sorted_hooks[i + 1].start_seconds:
                logger.warning(
                    f"Hook overlap detected: hook {sorted_hooks[i].rank} "
                    f"({sorted_hooks[i].start_time}-{sorted_hooks[i].end_time}) "
                    f"overlaps with hook {sorted_hooks[i + 1].rank} "
                    f"({sorted_hooks[i + 1].start_time}-{sorted_hooks[i + 1].end_time})"
                )
