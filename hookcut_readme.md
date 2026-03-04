# HookCut — Project README
**NyxPath** | Last updated: March 2026

---

## What is HookCut?

HookCut extracts high-performing hook segments from long-form YouTube videos and converts them into polished YouTube Shorts — with explanations of why each hook works.

Built by NyxPath. Global from V1. Supports Indian English, Hindi, and 11 other languages at launch.

---

## Current State: V1

HookCut V1 is functionally complete. The full pipeline works end-to-end:

```
YouTube URL → validate → analyze → transcript cascade → LLM hook identification
→ 5 hooks with scores, insights, improvement tips → user selects 1-3
→ pick caption style + trim boundaries → Short generation (Celery per hook)
→ yt-dlp + FFmpeg → inline video preview → download
```

### V1 Features
- **18 hook types** with 7-dimension holistic scoring + editorial attention_score
- **4 caption style presets**: Clean, Bold, Neon, Minimal
- **Hook boundary trimming**: ±10s adjustment before generating Shorts
- **Improvement suggestions**: LLM-generated creator tips per hook
- **Inline video preview**: HTML5 player before download
- **Analysis speed badge**: Elapsed timer during processing
- **Google OAuth** via NextAuth.js
- **120 free watermarked minutes/month** with INR + USD pricing
- **8 niches**, **13 languages**, **6 funnel roles**
- **Admin Dashboard** — role-based admin panel with NARM recommendations, prompt rule engine, model management, and audit logging

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI, Celery + Redis |
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4, TypeScript 5, shadcn/ui |
| **Auth** | NextAuth.js (Google OAuth) |
| **Database** | Supabase PostgreSQL |
| **LLM** | Gemini 2.5 Flash (primary), Claude Sonnet 4 (fallback), GPT-4o (tertiary) |
| **Storage** | Cloudflare R2 (presigned URLs, auto-TTL cleanup) |
| **Payments** | Razorpay (India) + Stripe (international) — pending setup |
| **Hosting** | Railway (backend) + Vercel (frontend) |
| **Monitoring** | Sentry + PostHog (code ready, DSN/keys pending) |

---

## Architecture

```
hookcut-backend/           FastAPI + Celery workers
├── app/routers/           HTTP endpoints (analysis, shorts, tasks, user, billing)
├── app/tasks/             Celery async tasks (analyze, generate_short, scheduled)
├── app/services/          Business logic (hook engine, short generator, credits, storage)
├── app/llm/               LLM providers (Gemini, Anthropic, OpenAI) + prompts
├── app/models/            SQLAlchemy models (session, hook, short, user, billing)
├── app/schemas/           Pydantic request/response schemas
└── app/utils/             YouTube URL parsing, FFmpeg commands, timestamps

hookcut-frontend/          Next.js 16 app
├── src/app/               Pages (main flow, dashboard, auth)
├── src/components/        UI components (hook-card, shorts-step, trim-slider, etc.)
└── src/lib/               API client, types, constants, utilities
```

### Key Design Decisions

- **Admin RBAC** — `get_admin_user` dependency enforces role check; 20 endpoints under `/api/admin/`
- **Rule engine** — 17 base rules (A-Q) editable via admin UI, versioned with revert capability
- **NARM insights** — LLM analyzes LearningLog data to generate natural language recommendations

---

## Hook Engine — Key Facts

- **LLM-only.** No deterministic pre-filtering. Full transcript sent in one pass.
- **Provider cascade:** Gemini 2.5 Flash (primary) → Claude Sonnet 4 (fallback) → GPT-4o (tertiary)
- **Output:** Exactly 5 hooks per video
- **Scoring:** 7 dimensions (scroll_stop, curiosity_gap, stakes_intensity, emotional_voltage, standalone_clarity, thematic_focus, thought_completeness) + editorial attention_score
- **18 hook types:** Curiosity Gap, Direct Benefit, Fear-Based, Authority, Contrarian, Counterintuitive, Story-Based, Pattern Interrupt, High Stakes Warning, Social Proof, Elimination, Objection Handler, Pain Escalation, Personal Transformation, Live Proof, FOMO Setup, Zero-Second Claim, Extended Demo
- **6 funnel roles:** curiosity_opener, pain_escalation, solution_reveal, proof_authority, retention_hook, extended_demo
- **Retry:** 3 attempts with [0s, 5s, 30s] backoff, fallback provider on 3rd attempt
- **Per-hook insights:** platform_dynamics, viewer_psychology, improvement_suggestion

---

## Language Support (13 languages)

| Language | Notes |
|---|---|
| English | Indian English + Global English. Hinglish code-switching accepted. |
| Hinglish | Hindi + English mix. Output in original mixed form. |
| Hindi | Devanagari or romanized. English tech terms allowed. |
| Tamil | Tamil or Tanglish (Tamil + English). |
| Telugu | Telugu or Telugu + English mix. |
| Kannada | Kannada or Kannada + English mix. |
| Malayalam | Malayalam or Manglish. |
| Marathi | Marathi or Marathi + Hindi/English mix. |
| Gujarati | Gujarati or Gujarati + English/Hindi mix. |
| Punjabi | Punjabi (Gurmukhi or romanized) or mixed. |
| Bengali | Bengali or Banglish (Bengali + English). |
| Odia | Odia or Odia + English/Hindi mix. |
| Other | Auto-detect from transcript. All rules apply. |

> **Source of truth:** `hookcut-backend/app/llm/prompts/constants.py` → `LANGUAGES` dict

---

## Billing Model

- Billed on **source video duration**, not Short duration
- All users get **120 free watermarked minutes/month** (auto-reset on 1st)
- Plans (INR): Free ₹0 | Lite ₹499 (100 clean min) | Pro ₹999 (500 clean min) | PAYG ₹100/100min
- Plans (USD): Free $0 | Lite $7 (100 clean min) | Pro $13 (500 clean min) | PAYG $2/100min
- Credits deducted at "Generate Hook Segments" click
- First regeneration free; 2nd+ charged (tiered INR, flat $0.30 USD)
- All failures refund credits automatically

---

## Non-Negotiables

1. **LLM-ONLY for hook identification** — deterministic heuristics were tested and abandoned
2. **Never download full video** — `yt-dlp --download-sections` only
3. **Single-pass FFmpeg** — no multi-pass pipelines
4. **Fail loudly** — missing data = explicit error, never silent recovery
5. **Global from V1** — INR + USD, 13 languages, dual payment gateway

---

## Canonical Documents

| Document | Purpose | Location |
|---|---|---|
| `hookcut_prd.md` | Product Requirements Document (v4.0) | project root |
| `CLAUDE.md` | Claude Code project instructions | project root |
| `hookcut-backend/CLAUDE.md` | Backend-specific instructions | backend/ |
| `hookcut-frontend/CLAUDE.md` | Frontend-specific instructions | frontend/ |
| `app/*/CONTRACTS.md` | Layer-specific API contracts | backend/app/ |

---

*HookCut • NyxPath • Confidential*
