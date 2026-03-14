# HookCut Eval Framework — PRD & CTO Strategy

**Last updated**: 2026-03-14

---

## Part A: CTO Strategy — Hook Engine Quality Roadmap

### The Core Problem

The hook engine has a sophisticated prompt (4-stage pipeline, 10 dimensions, 18 rules, virality scoring, cognitive tension types) — but it's flying blind. The LLM scores its own output. There is zero external validation that an "8/10 attention_score" hook actually performs well on YouTube. We're optimizing a loss function we've never measured.

**This is the #1 mistake in LLM-powered products: confusing prompt complexity with output quality.**

---

### Phase 1: Build the Ground Truth Dataset (Week 1-3)

Nothing else matters until we have data.

#### 1A. Manual Evaluation Dataset (THIS FRAMEWORK — In Progress)

- 550 diverse YouTube videos across 7 niches (61 English Indian creators)
- Run current hook engine → 5 hooks per video = 2,750 hooks
- Manual review: rate each hook on quality, boundary accuracy, would-pick
- Diversified review order (10% batches across all niches/creators)
- After 440 training videos reviewed → iterate prompt → test on 110 test videos

#### 1B. Competitive Benchmark

Take the same 50 videos, run them through:
- **Opus Clip** (market leader — uses "virality score" with actual YouTube data)
- **Vizard.ai** (AI clip detection)
- **Gling** (if accessible)
- **HookCut engine**

Compare: Do they pick the same moments? Where do they diverge? When our tool picks a different moment, is it better or worse according to human evaluators?

This tells us where we stand relative to competitors and whether our 10-dimension scoring is actually adding value over simpler approaches.

#### 1C. YouTube Analytics Feedback Loop (The Real Moat)

**The single most important feature to build next:**

User publishes Short → connects YouTube channel (OAuth) → HookCut pulls Analytics API data (retention curve, avg view duration, impressions, CTR, shares) → maps back to hook_id → stores as PerformanceLog

Why this is the moat: Opus Clip claims to use "virality scores" but doesn't have per-user feedback loops. If we build a system where every Short published through HookCut feeds back real performance data, we can:
- Calibrate LLM scores against reality (is a 7/10 hook actually a 7/10?)
- Discover which of our 10 dimensions actually correlate with performance
- Fine-tune or few-shot with real winners/losers

```
New model: PerformanceLog — hook_id, short_id, youtube_short_id, views_24h, views_7d, avg_retention_pct, ctr, shares, comments, fetched_at
New scheduled task: fetch_performance_metrics — runs daily, pulls YouTube Analytics for all published Shorts via OAuth.
```

---

### Phase 2: Simplify Before You Complexify (Week 3-5)

#### 2A. Prompt Ablation Study

The prompt is ~3,500 tokens of instructions before the transcript starts. That's a LOT of cognitive load. Hypothesis: 40% of the prompt could be removed with same or better results.

Run this experiment with the 50-video dataset:

| Variant | Description | Hypothesis |
|---------|-------------|------------|
| A (current) | Full 4-stage, 18 rules, 10 dims | Baseline |
| B (minimal) | "Find 5 best hook segments. Score each 1-10. Return JSON." (~200 tokens) | Gemini 2.5 Flash is smart enough without a 3,500-token rubric |
| C (medium) | Objective + 5 key rules (A, E, J, K, R) + 4 core dimensions (scroll_stop, curiosity_gap, standalone_clarity, thought_completeness) | Sweet spot between guidance and cognitive load |
| D (two-pass) | Pass 1: "Find 15 candidates" (minimal). Pass 2: "Score and rank → pick top 5" (full rubric) | Separates discovery from evaluation |

**Why simpler may win:**
- Instruction following degrades with prompt length — LLM spends capacity "remembering instructions" instead of "analyzing transcript"
- 10-dimension scoring forces the LLM to **rationalize, not evaluate** — it picks hooks it "likes" then reverse-engineers scores to justify
- Two-pass decouples discovery (divergent) from judgment (convergent)

#### 2B. Kill Dimensions That Don't Predict Performance

Once ground truth exists, run correlations:

```python
for dim in SCORE_DIMENSIONS:
    r = pearsonr(llm_scores[dim], human_ratings)
    print(f"{dim}: r={r[0]:.3f}, p={r[1]:.4f}")
```

Predictions:
- `linguistic_compression` and `information_density` are highly correlated (measuring the same thing) — merge or drop one
- `novelty_delta` is unreliable (too subjective, LLMs score inconsistently)
- `scroll_stop`, `curiosity_gap`, and `thought_completeness` are the 3 that actually matter

Fewer dimensions = more reliable scoring = less LLM cognitive load = better hooks.

---

### Phase 3: The Two-Pass Architecture (Week 5-8)

#### Pass 1: Discovery (cheap, fast, divergent)
- **Model**: Gemini 2.5 Flash (fast, cheap)
- **Prompt**: ~500 tokens
- **Task**: "Find 12-15 hook-worthy moments. For each: timestamp range, 1-line reason, signal strength (high/medium/low)."
- **Output**: Simple JSON list of candidates

#### Pass 2: Evaluation (careful, precise, convergent)
- **Model**: Claude Sonnet 4 (better at nuanced judgment)
- **Prompt**: ~1,000 tokens of scoring rubric + candidates from Pass 1
- **Task**: "Score each candidate on [4-5 validated dimensions]. Select top 5. Justify."
- **Output**: Final 5 hooks with scores

**Why this is better:**
- Discovery and evaluation use different cognitive skills. Flash excels at scanning/pattern matching. Claude excels at nuanced judgment and calibration.
- Pass 1 results are cacheable. Regeneration only re-runs Pass 2 — saving 60% of LLM cost.
- Pass 2 sees candidates side-by-side, enabling **comparative ranking** instead of absolute scoring. Comparative ranking is more reliable for LLMs.

#### Optional Pass 3: Calibration

Once enough PerformanceLog data exists:

> "Here are 3 example hooks that scored 8+ and performed well on YouTube, and 3 that scored 8+ but underperformed. Calibrate your scores accordingly."

This is few-shot calibration — the most effective prompt technique for scoring tasks.

---

### Phase 4: Rule Evolution via Data, Not Intuition (Week 8-12)

#### 4A. Replace NARM with Data-Driven Rule Mining

Current NARM uses LLM to analyze LearningLog aggregates and produce "insights." This is LLM-on-LLM — compounding hallucination risk. Replace with:

```python
# Statistical Rule Discovery
# Which hook_types get selected most by niche?
# Which attention_score ranges correlate with selection?
# Are users consistently picking rank-1 hooks or rank-3/4/5?
# Do composite hooks get selected more or less than non-composite?
```

Surface these as dashboards, not LLM-generated prose. Let humans interpret patterns.

#### 4B. A/B Test Rules, Not Prompts

- Create 3 rule variants (current baseline, stripped-down, enhanced)
- Randomly assign incoming analyses to variants (hash user_id % 3)
- Track selection_rate per variant
- After N=100 per variant, pick the winner

The infrastructure (PromptRule model, versioning, `build_hook_prompt_from_rules`) already exists — just need assignment and tracking logic.

---

### Phase 5: Competitive Moats (Month 3-6)

#### 5A. YouTube Most-Replayed Heatmap Integration

Currently the engine only sees transcript text. Throwing away:
- **Audio energy** — volume spikes, pace changes, laughter, gasps
- **Visual signals** — scene changes, text overlays, face close-ups
- **Engagement signals** — YouTube chapters, most-replayed segments (heatmap data)

**Most-Replayed Heatmap is the killer feature.** YouTube's API doesn't expose it directly, but `yt-dlp --write-info-json` includes heatmap data for many videos. This is real engagement data from millions of viewers.

```python
def fetch_heatmap(video_id: str) -> list[dict]:
    """Fetch YouTube's most-replayed heatmap data via yt-dlp."""
    # yt-dlp --write-info-json --skip-download
    # Parse .info.json -> heatmap field
    # Returns: [{"start_time": 0, "end_time": 5, "value": 0.8}, ...]
```

Inject into prompt:
```
ENGAGEMENT HEATMAP (from YouTube's most-replayed data):
Peak moments: 1:23-1:45 (95th percentile), 3:10-3:30 (90th percentile), ...
Low engagement: 0:00-0:30, 5:00-5:30
```

This single feature would leap past Opus Clip — combining LLM content analysis with actual viewer behavior data.

#### 5B. Creator Feedback Loop (The Flywheel)

Creator uses HookCut → publishes Shorts → connects YouTube → performance data flows back → calibrates scoring model → better hooks for next creator → more creators → more data → ...

This data flywheel makes the product defensible. Every creator who uses HookCut makes it better for the next.

#### 5C. Niche-Specific Few-Shot Examples

Build a library of proven hooks per niche:

```python
class HookExample(Base):
    id: str
    niche: str
    hook_text: str
    scores: dict
    youtube_performance: dict  # views, retention, shares
    source_video_url: str
    verified: bool  # admin-verified as high-quality example
```

Inject top 2-3 examples for the user's niche into the prompt. Few-shot examples are the single most effective technique for improving LLM output quality. They beat elaborate instructions every time.

---

### Priority Stack

| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| **P0** | Manual eval dataset (550 videos, human review) | Unlocks everything else | 3 weeks |
| **P0** | Ablation study (4 prompt variants) | Kill complexity that doesn't help | 1 week |
| **P1** | YouTube most-replayed heatmap integration | Massive quality jump, competitive moat | 2 weeks |
| **P1** | Two-pass architecture (discovery → evaluation) | Better hooks, cacheable Pass 1 | 2 weeks |
| **P2** | YouTube Analytics feedback loop (OAuth + PerformanceLog) | Long-term data flywheel | 3 weeks |
| **P2** | Dimension reduction (drop non-predictive scores) | Simpler, more reliable | 1 week |
| **P3** | Few-shot example library per niche | Highest-leverage prompt improvement | 2 weeks |
| **P3** | A/B testing infrastructure for rules | Scientific rule evolution | 2 weeks |
| **P4** | Audio energy analysis (volume/pace signals) | Incremental quality improvement | 3 weeks |

### The One Sentence Summary

**Stop adding more rules to the prompt. Start measuring which rules actually work. Build the feedback loop (heatmap data + YouTube Analytics) that turns HookCut from a fancy prompt wrapper into a data-driven product with compounding advantages.**

The engineering is excellent — the architecture, service layer isolation, rule engine, learning infrastructure. What's missing is the evaluation methodology. We've built a racecar but we're tuning it by ear instead of with a dyno.

---

## Part B: Eval Framework Implementation (Phase 1A)

### Design Principles

- **Pluggable filters**: Creator's country, target audience country, content language, and niche are configurable — same framework reused across datasets
- **Start with**: English Indian content creators, Indian audience
- **Reusable**: Hindi/Hinglish iteration uses same infrastructure (60 creators already seeded in `seed_creators_hindi.py`)

### Dataset Structure

#### Tier 1 — 7 niches × 10 creators × 10 videos = 500 videos

| Niche | Why Tier 1 | Hookability | Example Creators |
|-------|-----------|-------------|-----------------|
| **Finance** | Highest CPM, highest WTP for tools. Bad hook = lost money. Strong India signals (SIP, Nifty, crore, LPA). | Stakes-driven | Pranjal Kamra, Akshat Shrivastava, CA Rachana Ranade |
| **Tech / AI** | Fastest-growing segment. High-intent audience, paid tool users. English-first = higher CPM. | Disruption/novelty | Technical Guruji, Ishan Sharma, Varun Mayya |
| **Entrepreneurship** | Founder stories, harsh lessons, startup stakes. 30-90 min podcast-style = ideal for Short extraction. | Narrative arcs | Nikhil Kamath, Ranveer Allahbadia, Raj Shamani |
| **Education** | Massive volume (UPSC, JEE, NEET). Strong India-specific identity signals. Educators want "why this hook works." | Transformation | Physics Wallah, Aman Dhattarwal |
| **Podcast / Interview** | Long-form native. Every podcast is a hook mine. Founders + celebrities = automatic credibility. Benefits most from composite hooks. | Multi-segment | Raj Shamani, The Ranveer Show |
| **Fitness** | Strong transformation narratives. Supplement brands = high CPM sponsorships. Myth-busting tone scores well. | Before/after | Beerbiceps, Fit Tuber |
| **Drama / Commentary** | Huge audience (CarryMinati tier). Lower CPM/WTP but conflict/controversy = naturally high hook quality. | Conflict-driven | CarryMinati, Slayy Point |

#### Tier 2 — 2 niches × 5 creators × 5 videos = 50 videos

Fitness and Drama/Commentary as Tier 2 with smaller sample.

**Total**: 500 + 50 = **550 videos**

### Data Split

- **Training**: 440 videos (80%) — diversified across niches and creators
- **Test**: 110 videos (20%) — held out for final prompt validation
- Review order: round-robin across niches/creators for diversity

### Review Workflow

1. Pick URL from training set (diversified order — 10% of each niche per batch)
2. Generate transcript (cached in `transcripts/` folder, path linked in DB)
3. Run hook engine → 5 hooks per video
4. Reviewer rates each hook:
   - **Rating** (1-5 scale)
   - **Boundary accuracy** (perfect / slightly_off / wrong)
   - **Would pick** (yes / maybe / no)
   - **Justification** (free text)
5. Reviewer can flag **missed hooks** (timestamps + description)
6. Overall video feedback (optional free text)
7. Submit → recorded in DB → move to next video
8. Progress bar tracks completion across batches

### Batch System

- 10% batches = 44 videos per batch
- After each batch: aggregate analysis (rating distribution, failure modes, by-niche, by-hook-type, LLM calibration)
- Iterate prompt between batches
- 10 batches × 44 videos = 440 training videos

### Data Persistence

All data persisted for future reuse:
- **Transcripts**: cached as text files in `transcripts/`, paths stored in DB
- **Hooks**: stored per (video_id, prompt_version, rank) — can compare across versions
- **Reviews**: per-hook ratings, boundary accuracy, would_pick, justification
- **Missed hooks**: reviewer-flagged moments the LLM missed
- **Video reviews**: overall feedback per video per prompt version
- **Prompt snapshots**: SHA256-hashed, full text stored for reproducibility

This data will be reused when we create a YouTube channel to post Shorts and measure real performance (A/B testing — future phase).

---

## Part C: Current Implementation Status

### Pipeline Status (as of 2026-03-14)

| Step | Status | Details |
|------|--------|---------|
| Creators seeded | Done | 61 English creators, 7 niches |
| YouTube API enrichment | Done | All channel_ids + subscriber counts |
| Videos fetched | Done | 550 videos (best/mid/recent per creator) |
| Train/test split | Done | 440 train / 110 test |
| Transcripts | Done | 538/550 have text (12 failed — private/deleted) |
| Prompt v1 registered | Done | 4-stage pipeline, 18 rules (A-R), 10 dimensions |
| **Hooks generated** | **Partial** | **19/44 batch-1 videos done (95 hooks)** |
| Reviews | Not started | 0 reviewed |

### Blocking Issue: Gemini API Daily Quota

- Free tier: **20 requests/day** per model per project
- Primary key (`...YIyU`): exhausted for 2026-03-14
- Backup key (`...VDEI`): exhausted for 2026-03-14 (got 19 videos before hitting limit)
- **To unblock**: Add billing to Google Cloud project (removes 20 RPD limit) OR add `ANTHROPIC_API_KEY` to `.env`

### Key Files

```
tools/eval/
├── app.py              — Streamlit UI (5 pages)
├── run.py              — Entry point (UI + background pipeline)
├── db.py               — SQLite schema + CRUD
├── config.py           — EvalConfig, BATCH_SIZE_PCT = 10
├── hook_generator.py   — Batch generation with rate limit handling
├── transcript_fetcher.py — Transcript fetch with fallback cascade
├── dataset_builder.py  — CLI: seed/enrich/fetch-videos/split/export
├── analysis.py         — Batch review aggregation
├── seed_creators.py    — 61 English Indian creators
├── seed_creators_hindi.py — 60 Hindi/Hinglish creators (future)
├── eval.db             — SQLite database
├── transcripts/        — Cached transcript files
└── transcripts_hindi/  — 359 Hindi transcripts (future iteration)
```

### Code Fixes Applied This Session

1. **Version-scoped queries** — `load_batch_videos()` now filters hooks/reviews by selected prompt version
2. **URL query param persistence** — Browser refresh preserves review position via `st.query_params`
3. **Rate limit handling** — HookEngine waits 20s (not 1s) between retries on 429; outer retry loop with 65s escalating backoff
4. **UI generation feedback** — Progress bar shows success/failure counts; warning on failures

### .env Keys

```
GEMINI_API_KEY=AIzaSyAIrKjZluVlnF6SvEdf5MyTkuiNWsvVDEI  (backup, currently active)
Primary: AIzaSyB16SAt0kmr8ped9RiGirm4LiXTf1yYIyU
```

### Running the Framework

```bash
cd hookcut-backend/tools/eval
python3 run.py              # Launch UI + background pipeline
python3 run.py --no-ui      # Pipeline only

# Manual hook generation
python3 hook_generator.py v1                          # All videos
python3 hook_generator.py v1 --video-id VIDEO_ID      # Single video
python3 hook_generator.py register v2 "description"   # New prompt version
```

---

## Part D: Future Iterations

### Hindi/Hinglish Dataset (Iteration 2)

- 60 creators already seeded in `seed_creators_hindi.py`
- 359 transcripts preserved in `transcripts_hindi/`
- Same framework, just change content_language filter

### YouTube Channel A/B Testing (Future Phase)

- Create HookCut YouTube channel
- Post Shorts generated from reviewed hooks
- Measure real performance (views, retention, CTR, shares)
- Feed back into PerformanceLog for score calibration
- This data bridges the gap between human review and actual YouTube performance
