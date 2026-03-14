# HookCut Eval Framework — Status & Context

**Last updated**: 2026-03-15

---

## Why This Exists — The CTO's Core Diagnosis

The hook engine has a sophisticated prompt (4-stage pipeline, 10 scoring dimensions, 18 rules, virality scoring, cognitive tension types) but **no external validation**. The LLM scores its own output. There is zero evidence that an "8/10 attention_score" hook actually performs well on YouTube. We are optimizing a loss function we've never measured.

**The one-sentence problem**: We've built a racecar but are tuning it by ear instead of with a dyno.

---

## The Roadmap (CTO-Advised)

### P0 — Phase 1: Build Ground Truth (Weeks 1–3) ← WE ARE HERE

**1A. Manual Evaluation Dataset**
- 50 diverse videos across 7 niches (we have 400 — well beyond this)
- Run current hook engine → 5 hooks per video = 250 hooks
- 3 human raters (you + 2 Upwork freelancers who run YouTube channels) rate each hook:
  - Would you watch this Short to the end? (1–5)
  - Would you click through to the source video? (1–5)
  - Would you share this? (1–5)
- Calculate inter-rater agreement (Krippendorff's alpha). If < 0.6, the rubric is ambiguous — fix human rubric before touching the LLM prompt
- Cost: ~$500 for evaluators, 1 week

**1B. Competitive Benchmark**
- Run same 50 videos through Opus Clip, Vizard.ai, HookCut
- Compare which moments each tool picks — where do they diverge?
- Human raters judge which is better when they diverge
- This reveals whether our 10-dimension scoring adds value over simpler approaches

**1C. YouTube Analytics Feedback Loop (Future Moat)**
- User publishes Short → connects YouTube OAuth → HookCut pulls Analytics API
- Maps retention curves, CTR, shares back to `hook_id`
- New model: `PerformanceLog(hook_id, short_id, youtube_short_id, views_24h, views_7d, avg_retention_pct, ctr, shares)`
- This is what makes HookCut defensible vs Opus Clip — per-creator real feedback loop

### P0 — Phase 2: Ablation Study (Weeks 3–5)

The current prompt is ~3,500 tokens of instructions before the transcript starts. The CTO's hypothesis: we could remove 40% and get better results. Test 4 variants:

| Variant | Description | Tokens |
|---------|-------------|--------|
| A (current) | Full 4-stage, 18 rules, 10 dims | ~3,500 |
| B (minimal) | "Find 5 best hook segments. Score 1-10. Return JSON." | ~200 |
| C (medium) | Top 5 rules + 4 core dimensions (scroll_stop, curiosity_gap, standalone_clarity, thought_completeness) | ~800 |
| D (two-pass) | Pass 1: find 15 candidates (minimal). Pass 2: score and rank (full rubric) | ~1,200 |

Evaluate all 4 with human raters. The CTO predicts C or D beats A because:
- Instruction following degrades with prompt length
- 10-dimension scoring forces the LLM to rationalize, not evaluate (scores are post-hoc)
- Two-pass decouples discovery (divergent) from judgment (convergent)

### P1 — Phase 3: Two-Pass Architecture (Weeks 5–8)

**Pass 1 — Discovery** (Gemini 2.5 Flash, ~500 tokens):
"Find 12–15 hook-worthy moments. For each: timestamp, 1-line reason, signal strength."

**Pass 2 — Evaluation** (Claude Sonnet 4, ~1,000 tokens):
"Score each candidate on 4–5 validated dimensions. Select top 5. Justify."

Benefits: Pass 1 is cacheable (re-run only Pass 2 to test new rules). Comparative ranking in Pass 2 is more reliable than absolute scoring. Different models for different cognitive tasks.

### P1 — YouTube Most-Replayed Heatmap (Weeks 5–8)

The single biggest quality jump available:
- `yt-dlp --write-info-json` includes YouTube's most-replayed heatmap data
- Inject into the prompt: "Peak engagement: 1:23–1:45 (95th pct), 3:10–3:30 (90th pct)..."
- This combines LLM content analysis with actual viewer behavior from millions of views
- Opus Clip uses their own ML model — we'd be using YouTube's own signal

### P2 — Dimension Reduction (Week 6)

Once human ratings exist, run Pearson correlations: `llm_scores[dim]` vs `human_ratings`.
CTO predicts:
- `linguistic_compression` and `information_density` are redundant (merge or drop one)
- `novelty_delta` is unreliable (too subjective, inconsistent LLM scoring)
- `scroll_stop`, `curiosity_gap`, `thought_completeness` are the 3 that actually matter

### P3 — Few-Shot Example Library (Month 2)

Most effective prompt technique for scoring tasks — beats elaborate instructions.
- Build `HookExample` table: niche, hook_text, youtube_performance (views/retention), verified
- Inject top 2–3 examples per niche into the prompt as calibration anchors
- New model: `HookExample(niche, hook_text, scores, views, retention_pct, source_url, verified)`

### P3 — A/B Testing Infrastructure (Month 2)

The rule engine is already built — just needs assignment + tracking:
- Hash `user_id % 3` → assign to rule variant
- Track `selection_rate` per variant
- After N=100 per variant, pick the winner

### P4 — Audio Energy Analysis (Month 3)

Volume spikes, pace changes, laughter, gasps as additional signals. Lower priority — heatmap data already covers most of this.

---

## Current Dataset State (as of 2026-03-15)

### English Train Set: 400 videos ✓
- **Triple-verified English-only** (3 full Devanagari/Tamil scans, all 0% non-Latin)
- **All ≥ 10 minutes** (hard minimum, enforced — 79 short videos replaced)
- **7 niches**: Tech/AI (79), Finance (77), Podcast (73), Entrepreneurship (69), Education (69), Fitness (17), Drama/Commentary (16)
- **10 batches of 40** — all 7 niches represented in every batch (round-robin review_order)
- **Transcripts**: 393/400 have text (7 permanently blocked: 3×Simplilearn, 1×Gaurav Sen, 2×Startup Stories, 1×edureka — chapter-split or subtitles disabled; worth trying Whisper fallback later)

### Test Set: 110 videos
- Held out, not touched until prompt is finalized

### Hindi/Tamil Set: ~170 videos tagged `content_language='Hindi'` or `'Tamil'`
- Preserved in DB, excluded from English eval
- Will be iteration 2 after English prompt is tuned

### Creators: 61 English Indian creators across 7 niches

---

## Pipeline Status

| Step | Status | Details |
|------|--------|---------|
| Dataset built | ✅ Done | 400 English train, 110 test |
| Transcripts | ✅ Done | 393/400 (7 permanently blocked) |
| Prompt v1 registered | ✅ Done | v1-pro + v1-flash in DB |
| Hook import (manual) | 🔄 In progress | v1-pro: 4 videos (manually pasted from Gem); v1-flash: 35 videos (API-generated by hook_generator.py on 2026-03-14, kept as valid baseline) |
| Reviews | ⏳ Not started | Start after hooks imported for Batch 1 |
| Batch 1 analysis | ⏳ Waiting | Run `analysis.py` after Batch 1 reviewed |

---

## Dual-Model Setup

We are testing two models side-by-side for the same prompt:

| Version | Model | Method |
|---------|-------|--------|
| `v1-pro` | Gemini 2.0 Pro (Gem) | Manual paste |
| `v1-flash` | Gemini 2.5 Flash (Gem) | Manual paste |

Both are pasted manually via Gemini Gems (not API) because the Gemini free tier is exhausted. The eval tool's Import Hooks page handles this workflow.

---

## Daily Workflow — How to Pick Up Each Day

### Step 1: Open the eval UI
```bash
cd hookcut-backend/tools/eval
.venv/bin/python3 -m streamlit run app.py --server.headless true --server.port 8502
# Then open http://localhost:8502
```

### Step 2: Open Gemini Gems
- Pro Gem: [your Gemini Pro Gem URL]
- Flash Gem: [your Gemini Flash Gem URL]
- Make sure the system prompt in each Gem is loaded from **Prompt Lab → Copy Prompt** in the UI

### Step 3: Import hooks for Batch 1 videos
1. Go to **Dashboard → Batch 1**
2. Filter by "Needs Import"
3. Click any video title → lands on Import Hooks page
4. Click **📋 Copy Full Transcript** → paste into Gemini Gem → submit
5. Copy the JSON response → paste into the right-side text area → **💾 Save Hooks**
6. Repeat for remaining videos in Batch 1
7. Switch model (sidebar) and repeat for the other model

### Step 4: Review hooks (once all 40 videos in Batch 1 have hooks)
1. Go to **Review** page
2. Rate each hook: 1–5 stars, boundary accuracy, would-pick
3. Note any missed hooks
4. Submit and move to next video

### Step 5: After all 40 reviewed
```bash
cd hookcut-backend/tools/eval
.venv/bin/python3 analysis.py  # Aggregates batch 1 results
```
Check **Analytics** page for patterns. Use findings to iterate on prompt.

---

## Key Files

```
tools/eval/
├── app.py                  — Streamlit UI (Dashboard, Import Hooks, Review, Analytics, Dataset, Prompt Lab)
├── db.py                   — SQLite schema + CRUD (hooks saved here via insert_hook)
├── config.py               — BATCH_SIZE_PCT = 10 (10 batches of 40)
├── hook_generator.py       — Batch hook gen via API (blocked by rate limits; use manual paste instead)
├── transcript_fetcher.py   — youtube-transcript-api + innertube_android fallback
├── dataset_builder.py      — CLI: seed/enrich/fetch-videos/split/export
├── topup_videos.py         — Adds videos + reassigns review_order (run after any dataset changes)
├── analysis.py             — Aggregates review data per batch
├── seed_creators.py        — 61 English Indian creators
├── eval.db                 — SQLite database (WAL mode) — single source of truth
├── transcripts/            — Cached transcript .txt files
└── transcripts_hindi/      — 359 Hindi transcripts preserved for iteration 2
```

---

## Known Issues / Deferred

- **7 videos with no transcript**: Simplilearn/edureka use chapter-split auto-captions not fetchable as one block; Gaurav Sen/Startup Stories have subtitles disabled. Potential fix: yt-dlp audio → Whisper as 3rd fallback tier in `transcript_fetcher.py`.
- **Gemini API rate limits**: Free tier = 20 req/day. Use manual paste workflow (Gems) instead of API. To unblock API: add billing to Google Cloud project or use `ANTHROPIC_API_KEY` in `.env`.
- **Hindi iteration**: 60 creators, ~359 transcripts ready in `seed_creators_hindi.py` + `transcripts_hindi/`. Start after English prompt is validated.

---

## Prompt v1 Summary (Current Baseline)

4-stage pipeline, ~3,500 tokens before transcript:
1. **Discovery** — Scan transcript, detect 10–15 hook clusters
2. **Scoring** — 10 dimensions: scroll_stop, curiosity_gap, stakes_intensity, emotional_voltage, standalone_clarity, thought_completeness, click_through_likelihood, linguistic_compression, novelty_delta, information_density
3. **Selection** — Top 5 by editorial judgment (attention_score + virality_score)
4. **Output** — JSON: hook_type, funnel_role, cognitive_tension, scores, justification, algorithm_dynamics, viewer_psychology, improvement_suggestion

18 rules (A–R), 19 hook types, 6 funnel roles, 6 cognitive tension types.

**CTO note**: This prompt is over-engineered. The ablation study (Phase 2) will determine which parts actually contribute to quality.

---

## What "Done" Looks Like for Phase 1

- [ ] Batch 1 (40 videos): hooks imported for both v1-pro and v1-flash
- [ ] Batch 1: all 40 videos reviewed (ratings, boundary accuracy, would-pick)
- [ ] `analysis.py` run on Batch 1 — patterns identified
- [ ] Prompt v2 drafted based on findings
- [ ] Ablation study designed (4 variants ready to test)
- [ ] Second human rater recruited (Upwork — YouTube creator, ~$200–300)
