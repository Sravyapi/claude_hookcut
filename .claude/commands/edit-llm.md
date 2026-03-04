# Edit LLM Module

You are editing files in `hookcut-backend/app/llm/`.

## Before Making ANY Changes
1. Read `hookcut-backend/app/llm/CONTRACTS.md` completely
2. If modifying prompts, read `hookcut-backend/app/llm/prompts/constants.py`
3. Read the specific provider/prompt file you're modifying

## Rules
- All providers MUST implement the `LLMProvider` ABC (generate + name)
- All providers MUST return `LLMResponse` dataclass
- Gemini: `maxOutputTokens` needs 2x buffer (thinking tokens consume budget)
- Gemini: uses `responseMimeType: "application/json"` for structured output
- Gemini: fallback is `anthropic` (NOT self — this was a critical bug)
- Never change the fallback chain without updating CONTRACTS.md
- Adding a hook type? Follow the checklist in llm/CONTRACTS.md (HOOK_TYPES + FUNNEL_ROLES + SCORE_DIMENSIONS + niche config)
- Adding a niche? Follow the checklist in llm/CONTRACTS.md
- Adding a language? Follow the checklist in llm/CONTRACTS.md
- Prompt templates use f-strings — ensure all interpolated variables exist in constants
- After changes, update llm/CONTRACTS.md
