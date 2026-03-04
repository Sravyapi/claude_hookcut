"""Tests for HookEngine — LLM-powered hook identification engine."""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.hook_engine import HookEngine, HookCandidate, HookEngineResult
from app.llm.provider import LLMResponse
from app.exceptions import HookEngineError


def _make_valid_hook_json(num_hooks: int = 5) -> str:
    """Build a valid JSON response with the given number of hooks."""
    hooks = []
    for i in range(num_hooks):
        hooks.append({
            "rank": i + 1,
            "hook_text": f"This is hook number {i + 1} with a curiosity gap",
            "start_time": f"{i}:00",
            "end_time": f"{i}:30",
            "hook_type": "Curiosity Gap",
            "funnel_role": "curiosity_opener",
            "scores": {
                "scroll_stop": 8,
                "curiosity_gap": 9,
                "stakes_intensity": 7,
                "emotional_voltage": 8,
                "standalone_clarity": 8,
                "thematic_focus": 7,
                "thought_completeness": 8,
            },
            "attention_score": 8.5,
            "platform_dynamics": "High scroll-stop potential",
            "viewer_psychology": "Creates strong curiosity",
            "improvement_suggestion": "Add more urgency",
        })
    return json.dumps({"hooks": hooks})


def _make_llm_response(text: str) -> LLMResponse:
    """Create a mock LLM response."""
    return LLMResponse(
        text=text,
        provider="gemini",
        model="gemini-2.5-flash",
        input_tokens=100,
        output_tokens=200,
    )


# ─── analyze — successful path ────────────────────────────────────────────


class TestAnalyzeSuccess:
    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_provider")
    def test_successful_analysis(self, mock_get_provider, mock_settings):
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")
        mock_provider = MagicMock()
        mock_provider.name = "gemini"
        mock_provider.generate.return_value = _make_llm_response(_make_valid_hook_json())
        mock_get_provider.return_value = mock_provider

        engine = HookEngine()
        result = engine.analyze("Fake transcript text", "Generic", "English")

        assert isinstance(result, HookEngineResult)
        assert len(result.hooks) == 5
        assert result.provider == "gemini"
        assert result.model == "gemini-2.5-flash"
        assert result.attempts == 1
        assert result.input_tokens == 100
        assert result.output_tokens == 200

    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_provider")
    def test_hooks_parsed_correctly(self, mock_get_provider, mock_settings):
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")
        mock_provider = MagicMock()
        mock_provider.name = "gemini"
        mock_provider.generate.return_value = _make_llm_response(_make_valid_hook_json())
        mock_get_provider.return_value = mock_provider

        engine = HookEngine()
        result = engine.analyze("Fake transcript", "Generic")

        hook = result.hooks[0]
        assert isinstance(hook, HookCandidate)
        assert hook.rank == 1
        assert hook.hook_text == "This is hook number 1 with a curiosity gap"
        assert hook.start_time == "0:00"
        assert hook.end_time == "0:30"
        assert hook.start_seconds == 0.0
        assert hook.end_seconds == 30.0
        assert hook.hook_type == "Curiosity Gap"
        assert hook.funnel_role == "curiosity_opener"
        assert hook.attention_score == 8.5
        assert hook.scores["scroll_stop"] == 8
        assert hook.is_composite is False

    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_provider")
    def test_markdown_fenced_json(self, mock_get_provider, mock_settings):
        """Engine handles JSON wrapped in markdown code fences."""
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")
        mock_provider = MagicMock()
        mock_provider.name = "gemini"
        fenced = f"```json\n{_make_valid_hook_json()}\n```"
        mock_provider.generate.return_value = _make_llm_response(fenced)
        mock_get_provider.return_value = mock_provider

        engine = HookEngine()
        result = engine.analyze("Transcript", "Generic")

        assert len(result.hooks) == 5

    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_provider")
    def test_with_rules_parameter(self, mock_get_provider, mock_settings):
        """When rules are provided, build_hook_prompt_from_rules is used."""
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")
        mock_provider = MagicMock()
        mock_provider.name = "gemini"
        mock_provider.generate.return_value = _make_llm_response(_make_valid_hook_json())
        mock_get_provider.return_value = mock_provider

        custom_rules = [
            {"rule_key": "A", "title": "Custom rule", "content": "Custom content"},
        ]

        engine = HookEngine()
        with patch("app.llm.prompts.hook_identification.build_hook_prompt_from_rules") as mock_build:
            mock_build.return_value = "custom prompt"
            result = engine.analyze(
                "Transcript", "Generic", "English", rules=custom_rules
            )
            mock_build.assert_called_once_with(custom_rules, "Generic", "Transcript", "English")

        assert len(result.hooks) == 5


# ─── analyze — malformed responses ────────────────────────────────────────


class TestMalformedResponse:
    @patch("app.services.hook_engine.time")
    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_fallback_provider")
    @patch("app.services.hook_engine.get_provider")
    def test_invalid_json_all_attempts_fail(
        self, mock_get_provider, mock_get_fallback, mock_settings, mock_time
    ):
        mock_time.sleep = MagicMock()  # Skip real sleeps
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")
        mock_provider = MagicMock()
        mock_provider.name = "gemini"
        mock_provider.generate.return_value = _make_llm_response("not valid json {{{")
        mock_get_provider.return_value = mock_provider
        mock_get_fallback.return_value = mock_provider

        engine = HookEngine()
        with pytest.raises(HookEngineError, match="All 3 hook analysis attempts failed"):
            engine.analyze("Transcript", "Generic")

    @patch("app.services.hook_engine.time")
    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_fallback_provider")
    @patch("app.services.hook_engine.get_provider")
    def test_wrong_hook_count(
        self, mock_get_provider, mock_get_fallback, mock_settings, mock_time
    ):
        """LLM returns valid JSON but with wrong number of hooks."""
        mock_time.sleep = MagicMock()
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")
        mock_provider = MagicMock()
        mock_provider.name = "gemini"
        # Return 3 hooks instead of 5
        mock_provider.generate.return_value = _make_llm_response(_make_valid_hook_json(3))
        mock_get_provider.return_value = mock_provider
        mock_get_fallback.return_value = mock_provider

        engine = HookEngine()
        with pytest.raises(HookEngineError, match="All 3 hook analysis attempts failed"):
            engine.analyze("Transcript", "Generic")

    @patch("app.services.hook_engine.time")
    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_fallback_provider")
    @patch("app.services.hook_engine.get_provider")
    def test_missing_required_field(
        self, mock_get_provider, mock_get_fallback, mock_settings, mock_time
    ):
        """LLM returns hook with missing required field."""
        mock_time.sleep = MagicMock()
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")
        mock_provider = MagicMock()
        mock_provider.name = "gemini"

        bad_hooks = {"hooks": [{"rank": 1}] * 5}  # Missing most fields
        mock_provider.generate.return_value = _make_llm_response(json.dumps(bad_hooks))
        mock_get_provider.return_value = mock_provider
        mock_get_fallback.return_value = mock_provider

        engine = HookEngine()
        with pytest.raises(HookEngineError, match="All 3 hook analysis attempts failed"):
            engine.analyze("Transcript", "Generic")


# ─── analyze — fallback behavior ──────────────────────────────────────────


class TestFallbackBehavior:
    @patch("app.services.hook_engine.time")
    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_fallback_provider")
    @patch("app.services.hook_engine.get_provider")
    def test_primary_fails_fallback_succeeds(
        self, mock_get_provider, mock_get_fallback, mock_settings, mock_time
    ):
        mock_time.sleep = MagicMock()
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")

        # Primary provider fails
        primary_provider = MagicMock()
        primary_provider.name = "gemini"
        primary_provider.generate.side_effect = Exception("Rate limited")
        mock_get_provider.return_value = primary_provider

        # Fallback provider succeeds
        fallback_provider = MagicMock()
        fallback_provider.name = "anthropic"
        fallback_provider.generate.return_value = LLMResponse(
            text=_make_valid_hook_json(),
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            input_tokens=150,
            output_tokens=250,
        )
        mock_get_fallback.return_value = fallback_provider

        engine = HookEngine()
        result = engine.analyze("Transcript", "Generic")

        assert len(result.hooks) == 5
        assert result.provider == "anthropic"
        assert result.attempts == 3  # Failed 2x on primary, succeeded on 3rd (fallback)
        assert primary_provider.generate.call_count == 2
        assert fallback_provider.generate.call_count == 1

    @patch("app.services.hook_engine.time")
    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_fallback_provider")
    @patch("app.services.hook_engine.get_provider")
    def test_all_attempts_fail(
        self, mock_get_provider, mock_get_fallback, mock_settings, mock_time
    ):
        mock_time.sleep = MagicMock()
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")

        primary = MagicMock()
        primary.name = "gemini"
        primary.generate.side_effect = Exception("Primary down")
        mock_get_provider.return_value = primary

        fallback = MagicMock()
        fallback.name = "anthropic"
        fallback.generate.side_effect = Exception("Fallback also down")
        mock_get_fallback.return_value = fallback

        engine = HookEngine()
        with pytest.raises(HookEngineError, match="All 3 hook analysis attempts failed"):
            engine.analyze("Transcript", "Generic")

    @patch("app.services.hook_engine.time")
    @patch("app.services.hook_engine.get_settings")
    @patch("app.services.hook_engine.get_provider")
    def test_second_attempt_succeeds(self, mock_get_provider, mock_settings, mock_time):
        """Primary fails first attempt, succeeds on second."""
        mock_time.sleep = MagicMock()
        mock_settings.return_value = MagicMock(LLM_PRIMARY_PROVIDER="gemini")

        mock_provider = MagicMock()
        mock_provider.name = "gemini"
        mock_provider.generate.side_effect = [
            Exception("Temporary failure"),
            _make_llm_response(_make_valid_hook_json()),
        ]
        mock_get_provider.return_value = mock_provider

        engine = HookEngine()
        result = engine.analyze("Transcript", "Generic")

        assert len(result.hooks) == 5
        assert result.attempts == 2


# ─── _parse_and_validate edge cases ───────────────────────────────────────


class TestParseAndValidate:
    def test_score_clamping(self):
        """Scores are clamped to 0-10 range."""
        engine = HookEngine()
        hook_data = {
            "rank": 1,
            "hook_text": "Test",
            "start_time": "0:00",
            "end_time": "0:30",
            "hook_type": "Curiosity Gap",
            "funnel_role": "curiosity_opener",
            "scores": {
                "scroll_stop": 15,  # Above max
                "curiosity_gap": -3,  # Below min
                "stakes_intensity": 7,
                "emotional_voltage": 8,
                "standalone_clarity": 8,
                "thematic_focus": 7,
                "thought_completeness": 8,
            },
            "attention_score": 12,  # Above max
        }
        result = engine._validate_hook(hook_data)

        assert result.scores["scroll_stop"] == 10.0  # Clamped to max
        assert result.scores["curiosity_gap"] == 0.0  # Clamped to min
        assert result.attention_score == 10.0  # Clamped to max

    def test_composite_hook_detection(self):
        """Hooks with '+' in timestamp are marked as composite."""
        engine = HookEngine()
        hook_data = {
            "rank": 1,
            "hook_text": "Composite hook",
            "start_time": "1:30+3:45",
            "end_time": "1:55+4:10",
            "hook_type": "Story-Based",
            "funnel_role": "curiosity_opener",
            "scores": {},
            "attention_score": 7,
        }
        result = engine._validate_hook(hook_data)

        assert result.is_composite is True
        assert result.start_seconds == 90.0  # 1:30

    def test_fuzzy_hook_type_match(self):
        """Case-insensitive hook type matching."""
        engine = HookEngine()
        hook_data = {
            "rank": 1,
            "hook_text": "Test",
            "start_time": "0:00",
            "end_time": "0:30",
            "hook_type": "curiosity gap",  # Lowercase
            "funnel_role": "curiosity_opener",
            "scores": {},
            "attention_score": 7,
        }
        result = engine._validate_hook(hook_data)

        assert result.hook_type == "Curiosity Gap"

    def test_invalid_timestamp_defaults_to_zero(self):
        """Invalid timestamps default to 0.0 seconds."""
        engine = HookEngine()
        hook_data = {
            "rank": 1,
            "hook_text": "Test",
            "start_time": "invalid",
            "end_time": "also-invalid",
            "hook_type": "Curiosity Gap",
            "funnel_role": "curiosity_opener",
            "scores": {},
            "attention_score": 7,
        }
        result = engine._validate_hook(hook_data)

        assert result.start_seconds == 0.0
        assert result.end_seconds == 0.0
