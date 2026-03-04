# HookCut LLM Layer -- Contracts Reference

> Generated from source code in `hookcut-backend/app/llm/`.
> Canonical files: `provider.py`, `gemini_provider.py`, `anthropic_provider.py`, `openai_provider.py`, `prompts/constants.py`, `prompts/hook_identification.py`, `prompts/caption_cleanup.py`, and `app/config.py`.

---

## Table of Contents

1. [Provider Interface (ABC)](#1-provider-interface-abc)
2. [LLMResponse Dataclass](#2-llmresponse-dataclass)
3. [Factory Functions and Fallback Chain](#3-factory-functions-and-fallback-chain)
4. [Provider Implementations](#4-provider-implementations)
   - [GeminiProvider](#41-geminiprovider)
   - [AnthropicProvider](#42-anthropicprovider)
   - [OpenAIProvider](#43-openaiprovider)
5. [Prompt System](#5-prompt-system)
   - [Hook Identification Prompt](#51-hook-identification-prompt)
   - [Caption Cleanup Prompt](#52-caption-cleanup-prompt)
   - [Title Generation Prompt](#53-title-generation-prompt)
6. [Constants Registry](#6-constants-registry)
   - [HOOK_TYPES (18)](#61-hook_types-18-entries)
   - [SCORE_DIMENSIONS (7)](#62-score_dimensions-7-entries)
   - [FUNNEL_ROLES (6)](#63-funnel_roles-6-entries)
   - [NICHES (8)](#64-niches-8-entries)
   - [LANGUAGES (13)](#65-languages-13-entries)
   - [Regeneration Fee Tiers](#66-regeneration-fee-tiers)
7. [Configuration](#7-configuration)
8. [Consumption Patterns](#8-consumption-patterns)
9. [Checklists for Extending the System](#9-checklists-for-extending-the-system)

---

## 1. Provider Interface (ABC)

**File:** `provider.py`

```python
class LLMProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 4000) -> LLMResponse:
        """Send a single-turn prompt and return the LLM's response.

        Args:
            prompt:     The fully-assembled prompt string.
            max_tokens: Maximum output tokens (provider may interpret differently).

        Returns:
            LLMResponse with the generated text and usage metadata.

        Raises:
            RuntimeError: If the API call or response parsing fails.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical lowercase name: 'gemini' | 'anthropic' | 'openai'."""
        pass
```

Key points:
- The interface is intentionally minimal: one method (`generate`) and one property (`name`).
- All prompts are pre-assembled strings -- the provider never sees structured messages, system prompts, or multi-turn context.
- `max_tokens` is a hint. Gemini doubles it internally (see Section 4.1).

---

## 2. LLMResponse Dataclass

**File:** `provider.py`

```python
@dataclass
class LLMResponse:
    text: str                          # The generated text content
    provider: str                      # Canonical name: "gemini", "anthropic", "openai"
    model: str                         # Exact model ID used (e.g., "gemini-2.5-flash")
    input_tokens: Optional[int] = None   # Prompt token count (None if unavailable)
    output_tokens: Optional[int] = None  # Completion token count (None if unavailable)
```

| Field | Type | Description |
|---|---|---|
| `text` | `str` | Raw generated text. For Gemini this is always JSON (via `responseMimeType`). For Anthropic/OpenAI it may contain markdown fences that the caller strips. |
| `provider` | `str` | One of `"gemini"`, `"anthropic"`, `"openai"`. Set by each provider implementation, not the ABC. |
| `model` | `str` | The exact model string sent to the API. |
| `input_tokens` | `Optional[int]` | Prompt tokens consumed. `None` when the API does not report usage (e.g., OpenAI `usage` is `None` on some error paths). |
| `output_tokens` | `Optional[int]` | Completion tokens generated. Same caveat as `input_tokens`. |

---

## 3. Factory Functions and Fallback Chain

**File:** `provider.py`

### `get_provider(provider_name: str) -> LLMProvider`

Factory that lazily imports and instantiates the requested provider.

| `provider_name` | Class instantiated |
|---|---|
| `"gemini"` | `GeminiProvider()` |
| `"anthropic"` | `AnthropicProvider()` |
| `"openai"` | `OpenAIProvider()` |
| anything else | raises `ValueError` |

Imports are deferred (inside the function body) to avoid circular imports and to skip loading SDKs for unused providers.

### `get_fallback_provider(primary: str) -> LLMProvider`

Returns the designated fallback provider when the primary fails.

**Fallback map (hardcoded):**

| Primary | Fallback |
|---|---|
| `"gemini"` | `"anthropic"` |
| `"anthropic"` | `"openai"` |
| `"openai"` | `"anthropic"` |
| unknown key | `"anthropic"` (default) |

**Critical historical fix:** Gemini previously fell back to itself, causing infinite retry loops. The fix ensures `gemini -> anthropic`, never `gemini -> gemini`.

---

## 4. Provider Implementations

### 4.1 GeminiProvider

**File:** `gemini_provider.py`

| Property | Value |
|---|---|
| `name` | `"gemini"` |
| `model` | `"gemini-2.5-flash"` |
| `base_url` | `https://generativelanguage.googleapis.com/v1beta` |
| HTTP client | `httpx.Client` (synchronous, 180s timeout) |
| API key source | `settings.GEMINI_API_KEY` |

**How `generate()` works:**

1. Builds a REST URL: `{base_url}/models/{model}:generateContent?key={api_key}`
2. Sends a POST with this payload:
   ```json
   {
     "contents": [{"parts": [{"text": "<prompt>"}]}],
     "generationConfig": {
       "maxOutputTokens": "<max_tokens * 2>",
       "temperature": 0.7,
       "responseMimeType": "application/json"
     }
   }
   ```
3. Extracts text from `data["candidates"][0]["content"]["parts"][0]["text"]`.
4. Reads usage from `data["usageMetadata"]` (`promptTokenCount`, `candidatesTokenCount`).

**Provider-specific quirks:**

| Quirk | Detail |
|---|---|
| **`maxOutputTokens` needs 2x buffer** | Gemini's thinking tokens consume the output budget. The code multiplies `max_tokens` by 2 so the actual JSON content is not truncated. If you request 4000 tokens, the API receives 8000. |
| **`responseMimeType: "application/json"`** | Forces Gemini to return structured JSON directly, eliminating markdown fence wrapping. This is critical for reliable parsing. |
| **No SDK -- raw HTTP** | Uses `httpx` directly (not the Google AI Python SDK). Auth is via query parameter, not OAuth. |
| **180-second timeout** | Long timeout to accommodate large transcripts. |

**Errors raised:**
- `RuntimeError("Gemini API request failed: ...")` -- any `httpx` or HTTP error.
- `RuntimeError("LLM response parsing failed: ...")` -- response structure mismatch (`KeyError`, `IndexError`, `TypeError`).

---

### 4.2 AnthropicProvider

**File:** `anthropic_provider.py`

| Property | Value |
|---|---|
| `name` | `"anthropic"` |
| `model` | `"claude-sonnet-4-20250514"` |
| SDK | `anthropic.Anthropic` (official Python SDK) |
| API key source | `settings.ANTHROPIC_API_KEY` |

**How `generate()` works:**

1. Calls `self.client.messages.create()` with:
   - `model`: `"claude-sonnet-4-20250514"`
   - `max_tokens`: passed through directly (no multiplier)
   - `messages`: single user message `[{"role": "user", "content": prompt}]`
   - No `system` parameter, no `temperature` override (SDK default)
2. Iterates over `response.content` blocks, concatenating all `text` blocks.
3. Token usage comes from `response.usage.input_tokens` and `response.usage.output_tokens`.

**Provider-specific quirks:**

| Quirk | Detail |
|---|---|
| **No temperature set** | Uses the SDK default (likely 1.0). Gemini and OpenAI both set 0.7 explicitly. |
| **Multi-block response** | Anthropic responses can contain multiple content blocks. The code concatenates all text blocks. |
| **No `responseMimeType` equivalent** | JSON output is not enforced at the API level. The caller must strip markdown fences if the model wraps JSON. |

**Errors raised:**
- Any exception from the `anthropic` SDK (e.g., `anthropic.APIError`, `anthropic.AuthenticationError`). These propagate unwrapped.

---

### 4.3 OpenAIProvider

**File:** `openai_provider.py`

| Property | Value |
|---|---|
| `name` | `"openai"` |
| `model` | `"gpt-4o"` |
| SDK | `openai.OpenAI` (official Python SDK) |
| API key source | `settings.OPENAI_API_KEY` |

**How `generate()` works:**

1. Calls `self.client.chat.completions.create()` with:
   - `model`: `"gpt-4o"`
   - `max_tokens`: passed through directly
   - `messages`: single user message `[{"role": "user", "content": prompt}]`
   - `temperature`: 0.7
2. Takes `response.choices[0].message.content` (falls back to `""` if `None`).
3. Token usage from `response.usage.prompt_tokens` / `response.usage.completion_tokens` (guarded against `None` usage object).

**Provider-specific quirks:**

| Quirk | Detail |
|---|---|
| **`response.usage` can be `None`** | The code guards with `if response.usage else None`. |
| **No JSON mode** | Unlike Gemini, no `response_format` is set. JSON output depends entirely on prompt instruction. |

**Errors raised:**
- Any exception from the `openai` SDK (e.g., `openai.APIError`, `openai.RateLimitError`). These propagate unwrapped.

---

## 5. Prompt System

All prompt construction lives in `prompts/`. Prompts are pure f-string templates that interpolate constants from `constants.py`.

### 5.1 Hook Identification Prompt

**File:** `prompts/hook_identification.py`

**Function:** `build_hook_prompt(niche: str, transcript: str, language: str = "English") -> str`

**Imports used:** `NICHES`, `LANGUAGES`, `HOOK_TYPES`, `FUNNEL_ROLES`

**Structure of the generated prompt:**

1. **Role assignment:** "You are a hook evaluator for YouTube Shorts."
2. **Niche context block:** `NICHE: {niche} | DURATION: {softRange} | STAKES: {stakes} | TONE: {tone}` plus `PREFERRED TYPES`.
3. **Language instruction:** The `promptNote` from the matched `LANGUAGES` entry.
4. **Filler detection rules:** Contextual filler exclusion (greetings, CTAs, stalling).
5. **3-tier signal patterns:** Tier 1 (strongest), Tier 2 (strong), Tier 3 (enhancement).
6. **Boundary rules:** Sentence boundaries, standalone test, peak tension ending.
7. **17 rules (A-Q):** One topic per hook, contextual grounding, specificity, character arcs, breathing room, urgency, narrative escalation, composite hooks, landing points, unresolved mechanism, pain escalation, elimination, objection handling, funnel diversity, strip labels, workflow demos.
8. **Scoring dimensions:** 7 dimensions (0-10 scale) plus editorial `attention_score`.
9. **Classification instructions:** Hook type from `HOOK_TYPES`, funnel role from `FUNNEL_ROLES`.
10. **Output schema:** Exact JSON structure for 5 hooks.
11. **Transcript:** The full transcript appended at the end.

**Expected output:** Exactly 5 hooks in JSON format with fields: `rank`, `hook_text`, `start_time`, `end_time`, `hook_type`, `funnel_role`, `scores` (7 dims), `attention_score`, `platform_dynamics`, `viewer_psychology`, `improvement_suggestion`.

### Dynamic Hook Prompt from Admin Rules

**Function:** `build_hook_prompt_from_rules(rules: list[dict], niche, transcript, language="English") -> str`
**File:** `prompts/hook_identification.py`

Extends `build_hook_prompt()` by accepting admin-defined rules instead of using the hardcoded 17 rules (A-Q). This function does NOT access the database — it receives plain dicts with `rule_key` and `content` keys.

**Logic:**
1. If `rules` list is empty → falls back to `build_hook_prompt()` (hardcoded)
2. Reconstructs the "RULES" section from the provided rule dicts, keeps everything else (signal patterns, scoring, output format) unchanged

**Used by:**
- `AdminService.preview_prompt()` — assembles rules from DB, passes as dicts
- `AdminService.get_active_rules_as_dicts(db)` — helper that queries DB and returns `list[dict]`
- `HookEngine.analyze(rules=...)` — optional parameter; when provided, uses `build_hook_prompt_from_rules` instead of `build_hook_prompt`

**Design note:** The LLM layer accepts plain data (dicts), never DB sessions. The service layer is responsible for querying the database and passing rules as dicts. This keeps the LLM layer isolated from SQLAlchemy.

### 5.2 Caption Cleanup Prompt

**File:** `prompts/caption_cleanup.py`

**Function:** `build_caption_cleanup_prompt(hook_text: str, language: str = "English") -> str`

Cleans transcript text for YouTube Short captions. Rules: fix punctuation/capitalization, remove fillers (um, uh, like, you know, basically, right, so), remove false starts, keep original language (never translate), keep code-switching, output clean text only.

**Called with `max_tokens=500`.**

### 5.3 Title Generation Prompt

**File:** `prompts/caption_cleanup.py`

**Function:** `build_title_generation_prompt(hook_text: str, niche: str, language: str = "English") -> str`

Generates a YouTube Shorts title. Rules: under 60 characters, no clickbait, no ALL CAPS, match content language, include curiosity hook or benefit, minimal emojis.

**Called with `max_tokens=100`.**

---

## 6. Constants Registry

**File:** `prompts/constants.py`

This file is the single source of truth for all domain enumerations used in prompts, validation, and the frontend. The header comment documents the provenance:

```
# Ported from hookcut_engine.jsx
# LANGUAGES: 13 entries (12 + Other)
# NICHES: 8 entries
# HOOK_TYPES: 18 entries -- union of PRD (13) + engine (15)
# FUNNEL_ROLES: 6 entries
# SCORE_DIMENSIONS: 7 entries (engine's holistic approach)
```

### 6.1 HOOK_TYPES (18 entries)

A flat list of strings. The union of PRD-defined types (13) and engine-defined types (15), deduplicated.

| # | Hook Type | Typical Use |
|---|---|---|
| 1 | Curiosity Gap | Incomplete information that compels the viewer to keep watching |
| 2 | Direct Benefit | Clear value proposition stated upfront |
| 3 | Fear-Based | Threat, risk, or negative consequence framing |
| 4 | Authority | Credibility signal (expert, credential, experience) |
| 5 | Contrarian | Goes against conventional wisdom |
| 6 | Counterintuitive | Surprising or paradoxical claim |
| 7 | Story-Based | Narrative arc, personal anecdote |
| 8 | Pattern Interrupt | Breaks expected content flow, grabs attention |
| 9 | High Stakes Warning | Urgent risk or consequence |
| 10 | Social Proof | Numbers, testimonials, crowd validation |
| 11 | Elimination | Systematically removing expected answers |
| 12 | Objection Handler | Catches viewer at the bounce moment |
| 13 | Pain Escalation | Layers frustration progressively |
| 14 | Personal Transformation | Before/after or growth narrative |
| 15 | Live Proof | Real-time demonstration ("watch this") |
| 16 | FOMO Setup | Exclusivity, scarcity, or urgency trigger |
| 17 | Zero-Second Claim | High-stakes claim delivered immediately at second zero |
| 18 | Extended Demo | Full workflow/demo sequence (can run 30-50s) |

**Validation behavior:** The `HookEngine._validate_hook()` method does a case-insensitive fuzzy match against this list. Unknown types are logged as warnings but kept as-is (not rejected).

### 6.2 SCORE_DIMENSIONS (7 entries)

Not stored as a standalone constant in `constants.py`, but embedded in the prompt and validated in `hook_engine.py`. The canonical list:

| Dimension | What it measures | Gating rule |
|---|---|---|
| `scroll_stop` | Would a viewer stop scrolling in the first 1-2 seconds? | -- |
| `curiosity_gap` | Does the hook create an information gap the viewer needs resolved? | -- |
| `stakes_intensity` | How high are the perceived consequences? | -- |
| `emotional_voltage` | Strength of emotional reaction provoked | -- |
| `standalone_clarity` | Can a stranger understand this with zero prior context? | -- |
| `thematic_focus` | Does the hook stay on one topic? | **GATING: score < 5 means the hook cannot be ranked in the top 3** |
| `thought_completeness` | Does the hook end at the right moment? | Cuts early = 4 or less; goes past landing = 5 or less; delivers value while withholding = 8+ |

All dimensions are scored 0-10 (float, clamped by `max(0, min(10, float(val)))`).

**`attention_score`** is a separate field (not part of the 7 dimensions). It is the LLM's independent editorial judgment (0-10), explicitly not a formula over the other dimensions.

### 6.3 FUNNEL_ROLES (6 entries)

```python
FUNNEL_ROLES = [
    "curiosity_opener",    # Opens with intrigue, draws viewer in
    "pain_escalation",     # Layers frustration to build urgency
    "solution_reveal",     # Delivers the payoff or answer
    "proof_authority",     # Establishes credibility
    "retention_hook",      # Keeps the viewer watching through the Short
    "extended_demo",       # Full step-by-step demonstration
]
```

The prompt instructs the LLM to assign diverse funnel roles across the 5 hooks (Rule O: "5 hooks serve different purposes").

**Validation behavior:** Case-insensitive fuzzy match with underscore normalization (spaces replaced with underscores). Unknown roles are logged as warnings but kept.

### 6.4 NICHES (8 entries)

A dictionary keyed by niche name. Each entry contains:

| Key | Type | Description |
|---|---|---|
| `softRange` | `str` | Recommended hook duration range (e.g., `"12-30s"`) |
| `stakes` | `str` | Niche-specific stakes language injected into the prompt |
| `tone` | `str` | Tone guidance for hook evaluation |
| `preferredTypes` | `list[str]` | Subset of `HOOK_TYPES` that work best for this niche |

**The 8 niches:**

| Niche | Soft Range | Preferred Types |
|---|---|---|
| **Tech / AI** | 12-30s | Zero-Second Claim, Curiosity Gap, Counterintuitive, High Stakes Warning, Live Proof |
| **Finance** | 15-35s | Fear-Based, High Stakes Warning, Direct Benefit, Contrarian, FOMO Setup |
| **Fitness** | 10-25s | Contrarian, Direct Benefit, Personal Transformation, Counterintuitive |
| **Relationships** | 10-25s | Story-Based, Pattern Interrupt, Curiosity Gap, Personal Transformation |
| **Drama / Commentary** | 12-30s | Pattern Interrupt, High Stakes Warning, Zero-Second Claim, Fear-Based |
| **Entrepreneurship** | 15-30s | Story-Based, High Stakes Warning, Contrarian, Personal Transformation, Curiosity Gap |
| **Podcast** | 15-40s | Curiosity Gap, Counterintuitive, Authority, Story-Based, Contrarian |
| **Generic** | 12-30s | Curiosity Gap, Counterintuitive, Direct Benefit, Story-Based |

"Generic" is the fallback when the requested niche key is not found.

**Validation:** The `AnalyzeRequest` Pydantic schema (in `schemas/analysis.py`) validates that the submitted niche exists in `NICHES.keys()`. Requests with unknown niches are rejected at the API layer.

### 6.5 LANGUAGES (13 entries)

A dictionary keyed by language name. Each entry contains:

| Key | Type | Description |
|---|---|---|
| `label` | `str` | Human-readable display name |
| `promptNote` | `str` | Language-specific instruction injected into the prompt |

**The 13 languages:**

| Key | Label | Notable Prompt Guidance |
|---|---|---|
| `English` | English | Accepts Indian English with Hinglish code-switching |
| `Hinglish` | Hinglish (Hindi + English) | Natural Hindi-English mix; never normalize to either pure language |
| `Hindi` | Hindi | Devanagari or romanized; English technical terms acceptable |
| `Tamil` | Tamil | Tanglish (Tamil + English) recognized |
| `Telugu` | Telugu | Telugu-English code-switching recognized |
| `Kannada` | Kannada | Kannada-English code-switching recognized |
| `Malayalam` | Malayalam | Manglish (Malayalam + English) recognized |
| `Marathi` | Marathi | Marathi-English/Hindi code-switching recognized |
| `Gujarati` | Gujarati | Gujarati-English/Hindi code-switching; common in business/finance |
| `Punjabi` | Punjabi | Gurmukhi or romanized; Punjabi-English/Hindi recognized |
| `Bengali` | Bengali | Banglish (Bengali + English) recognized |
| `Odia` | Odia | Odia-English/Hindi code-switching recognized |
| `Other` | Other Language | Auto-detect from transcript; all rules apply identically |

All `promptNote` values enforce the rule: **output hook_text in the ORIGINAL language -- NEVER translate.**

**Validation:** The `AnalyzeRequest` Pydantic schema validates that the submitted language exists in `LANGUAGES.keys()`.

### 6.6 Regeneration Fee Tiers

```python
REGEN_FEE_TIERS_INR = [
    (15 * 60, 1000),        # <=15 min source video: Rs 10 (1000 paisa)
    (30 * 60, 1500),        # <=30 min: Rs 15 (1500 paisa)
    (60 * 60, 2000),        # <=60 min: Rs 20 (2000 paisa)
    (float("inf"), 2500),   # >60 min: Rs 25 (2500 paisa)
]
REGEN_FEE_USD_CENTS = 30    # Flat $0.30

def get_regen_fee(video_duration_seconds: float, currency: str) -> int:
    """Return regeneration fee in smallest currency unit (paisa/cents)."""
```

- INR fees are tiered by source video duration.
- USD is a flat rate regardless of duration.
- All values are in smallest currency unit (paisa for INR, cents for USD).

---

## 7. Configuration

**File:** `app/config.py`

### Environment Variables for LLM

| Variable | Default | Description |
|---|---|---|
| `LLM_PRIMARY_PROVIDER` | `"gemini"` | Which provider to use first. One of: `"gemini"`, `"anthropic"`, `"openai"`. |
| `GEMINI_API_KEY` | `""` | Google AI API key for Gemini |
| `ANTHROPIC_API_KEY` | `""` | Anthropic API key for Claude |
| `OPENAI_API_KEY` | `""` | OpenAI API key for GPT-4o |
| `WHISPER_API_KEY` | `""` | Whisper transcription key (falls back to `OPENAI_API_KEY` if empty) |

### Startup Validation

The `Settings` model validator enforces:
- **At least one LLM API key must be set** (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`). Otherwise the app fails to start.
- This check is skipped when `TESTING=true` is set in the environment.

### Model Selection

Models are hardcoded in each provider class (not configurable via environment):

| Provider | Model ID |
|---|---|
| Gemini | `gemini-2.5-flash` |
| Anthropic | `claude-sonnet-4-20250514` |
| OpenAI | `gpt-4o` |

### Token Limits and Budgets

| Use Case | `max_tokens` passed | Effective budget |
|---|---|---|
| Hook identification | 4000 | Gemini: 8000 (2x), Anthropic/OpenAI: 4000 |
| Caption cleanup | 500 | Gemini: 1000 (2x), Anthropic/OpenAI: 500 |
| Title generation | 100 | Gemini: 200 (2x), Anthropic/OpenAI: 100 |

The 2x multiplier for Gemini is automatic in `GeminiProvider.generate()` and does not need to be accounted for by callers.

---

## 8. Consumption Patterns

The LLM layer is consumed by two services:

### HookEngine (`services/hook_engine.py`)

- **Purpose:** Analyze a transcript and extract 5 hook candidates.
- **Provider:** Uses `LLM_PRIMARY_PROVIDER` from config.
- **Retry strategy:** 3 attempts with delays [0s, 5s, 30s]. Attempts 1-2 use the primary provider. Attempt 3 uses the fallback provider (via `get_fallback_provider`). If the fallback provider cannot be instantiated, falls back to the primary again.
- **Prompt:** `build_hook_prompt(niche, transcript, language)` with `max_tokens=4000`. If optional `rules` parameter is provided (list of dicts with `rule_key` and `content`), uses `build_hook_prompt_from_rules(rules, niche, transcript, language)` instead.
- **Response parsing:** Strips markdown fences, parses JSON, validates exactly 5 hooks, fuzzy-matches hook types and funnel roles, clamps scores to [0, 10], checks for timestamp overlaps (warns but does not fail).
- **Error type:** `HookEngineError` (from `app.exceptions`) for all failures after retries exhausted.

### ShortGenerator (`services/short_generator.py`)

- **Purpose:** Generate a YouTube Short from a selected hook.
- **Provider:** Uses `LLM_PRIMARY_PROVIDER` from config (no fallback -- failures return raw text or default title).
- **Two LLM calls (run in parallel via `ThreadPoolExecutor`):**
  1. Caption cleanup: `build_caption_cleanup_prompt(hook_text, language)` with `max_tokens=500`. On failure, returns the raw `hook_text` as-is.
  2. Title generation: `build_title_generation_prompt(hook_text, niche, language)` with `max_tokens=100`. On failure, returns `"Hook Segment"`.
- **No retry logic.** Both calls are fire-once with graceful fallback.

---

## 9. Checklists for Extending the System

### Adding a New Hook Type

Files to modify:

1. **`prompts/constants.py` -- `HOOK_TYPES` list**
   - Append the new type string to the list (e.g., `"Cliffhanger"`).
   - The name must be title-case and unique.
   - Position in the list does not affect behavior.

2. **`prompts/constants.py` -- `NICHES` dict**
   - For each niche where this hook type is especially relevant, add it to that niche's `preferredTypes` list.
   - This is optional but recommended. If omitted, the LLM can still assign the type; it just won't be listed as "preferred" for any niche.

3. **`prompts/hook_identification.py` -- Signal patterns (optional)**
   - If the new hook type has specific signal patterns, add them to the appropriate tier (Tier 1/2/3) in the prompt template.
   - If it requires a new rule, add it to the 17 rules (A-Q) section. Update the rule count in the prompt text.

4. **No changes needed in:**
   - `hook_engine.py` -- Validation uses the `HOOK_TYPES` list dynamically with fuzzy matching.
   - `provider.py` -- Provider layer is type-agnostic.
   - `schemas/analysis.py` -- Schemas don't validate hook types.
   - Frontend -- The frontend receives hook types from the API response and renders them dynamically.

### Adding a New Niche

Files to modify:

1. **`prompts/constants.py` -- `NICHES` dict**
   - Add a new key-value pair. The key is the niche name (displayed to users). The value must contain:
     ```python
     "New Niche Name": {
         "softRange": "12-30s",     # Recommended hook duration range
         "stakes": "...",           # Niche-specific stakes language
         "tone": "...",             # Tone guidance
         "preferredTypes": [        # Subset of HOOK_TYPES
             "Curiosity Gap", "Direct Benefit", ...
         ],
     }
     ```
   - All `preferredTypes` entries must be exact strings from the `HOOK_TYPES` list.

2. **No changes needed in:**
   - `schemas/analysis.py` -- Validation reads `NICHES.keys()` dynamically.
   - `hook_identification.py` -- Prompt template reads from `NICHES` dict dynamically.
   - `provider.py`, `hook_engine.py` -- Niche-agnostic.
   - Frontend -- **However**, the frontend niche selector must be updated to include the new niche. Check the frontend component that renders niche pill chips.

### Adding a New Language

Files to modify:

1. **`prompts/constants.py` -- `LANGUAGES` dict**
   - Add a new key-value pair. The key is the language name. The value must contain:
     ```python
     "NewLanguage": {
         "label": "NewLanguage",    # Display label
         "promptNote": (
             "LANGUAGE: NewLanguage (or NewLanguage mixed with English). "
             "Code-switching is common. Output hook_text in the ORIGINAL "
             "language -- NEVER translate."
         ),
     }
     ```
   - The `promptNote` MUST include the "NEVER translate" instruction.
   - If the language has a common code-switching pattern (e.g., "Spanglish"), document it in the `promptNote`.

2. **No changes needed in:**
   - `schemas/analysis.py` -- Validation reads `LANGUAGES.keys()` dynamically.
   - `hook_identification.py`, `caption_cleanup.py` -- Both read from `LANGUAGES` dict dynamically.
   - `provider.py`, `hook_engine.py` -- Language-agnostic.
   - Frontend -- **However**, the frontend language auto-detection or any language selector must be updated to recognize the new language.

### Adding a New LLM Provider

Files to modify:

1. **Create `{name}_provider.py`** in `app/llm/`
   - Subclass `LLMProvider`.
   - Implement `generate(self, prompt: str, max_tokens: int = 4000) -> LLMResponse`.
   - Implement the `name` property returning a unique lowercase string.
   - Read the API key from `get_settings()`.

2. **`provider.py` -- `get_provider()`**
   - Add an `elif` branch for the new provider name.

3. **`provider.py` -- `get_fallback_provider()`**
   - Add the new provider to the `fallback_map` dict (both as a key and potentially as a fallback value for another provider).

4. **`config.py` -- `Settings` class**
   - Add the new API key field (e.g., `NEW_PROVIDER_API_KEY: str = ""`).
   - Add it to the `any([...])` check in `validate_required_settings`.

### Adding a New Score Dimension

Files to modify:

1. **`prompts/hook_identification.py`**
   - Add the new dimension to the `SCORING` section of the prompt template.
   - Add it to the JSON output schema in the prompt.

2. **`services/hook_engine.py` -- `_validate_hook()`**
   - Add the new dimension name to the list in the score validation loop (the `for dim in [...]` block).

3. **No changes needed in:**
   - `constants.py` -- Score dimensions are not stored as a constant (they are embedded in the prompt and validation code).
   - `provider.py` -- Score-agnostic.

### Adding a New Funnel Role

Files to modify:

1. **`prompts/constants.py` -- `FUNNEL_ROLES` list**
   - Append the new role string (snake_case).

2. **No changes needed in:**
   - `hook_identification.py` -- Reads `FUNNEL_ROLES` dynamically via `"|".join(FUNNEL_ROLES)`.
   - `hook_engine.py` -- Validation uses `FUNNEL_ROLES` list dynamically.

---

*End of LLM layer contracts.*
