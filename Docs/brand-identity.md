# HookCut Brand Identity

> v1.0 · March 2026 · **tl;dr:** orange, Outfit font, "Find the hook. Stop the scroll." — don't mess with any of that.

---

## What We're Building Here

HookCut is not a generic AI tool. It's not a clipper. It's not a SaaS dashboard for people who wear lanyards.

It's a **hook intelligence engine** for creators who know that the first 2 seconds decide everything — and are tired of guessing.

Our brand has two jobs:
1. Make creators instantly feel like *"yes, this gets me"*
2. Make competitors feel faintly embarrassed by comparison

Everything in this doc — the colors, the words, the animations — serves those two jobs.

---

## The Tagline (It's Locked. Don't Touch It.)

> **"Find the hook. Stop the scroll."**

Short. Sharp. Does what it says. Used verbatim everywhere:  
homepage H1, OG tags, app store listings, email subjects, the tweet when we hit 10k users.

No variations. No "Find YOUR hook." No "Stop THE scroll." No emoji in the tagline. No period at the end in H1 context.

---

## Brand Personality — The Vibe Check

Think: **sharp creative friend who also knows how to ship code.**

| Trait | In practice |
|-------|-------------|
| 🎯 **Precise** | We show scores, not opinions. "87 score" beats "pretty viral." |
| 💪 **Confident** | "The hook is at 1:32." Not "there might be a hook around 1:32." |
| 🙋 **Creator-peer** | We talk like creators, not IT managers. Casual but never sloppy. |
| ⚡ **Fast** | Short sentences. Direct. No filler. No "it's important to note that…" |
| 🔍 **Honest (selectively)** | We tell you *what* we found and *why it works*. We don't explain *how* we found it. |

### We Are NOT:
- ❌ An "AI clipper" — say **hook analysis engine** or **hook scoring platform**
- ❌ A bulk clip factory (volume ≠ quality — we hate this about competitors)
- ❌ An enterprise product (no lanyards, no "enterprise plan," no "solution" as a noun)
- ❌ A purple brand (purple = OpusClip. We are orange. Very different.)

---

## Logo

### The Wordmark

**HookCut** — rendered in **Outfit ExtraBold (800)**, tracking `-0.02em`.

The capital **C** in "Cut" is **locked and intentional**. `Hook` + `Cut` are two strong words fused into one brand name. The capital C creates a visual beat — Hook *[pause]* Cut.

```
Hook  →  what we find
Cut   →  what we do with it
```

On dark backgrounds (header, product UI):
- `Hook` = `#FFFFFF` (white)
- `Cut` = `#E84A2F` (brand orange)

On light backgrounds (marketing site):
- `Hook` = `#0A0A0A` (near-black)
- `Cut` = `#E84A2F` (brand orange)

The two-tone wordmark is the logo. No box, no badge, no container. Just the type.

### What the Cap-C Wordmark Inspired By
The cap-C style was chosen from our design exploration (Canva reference `DAHDHk_nRRs`, slide 1) — the bold all-caps C in "Cut" gives the word visual weight and makes the brand name scannable at small sizes.

### The Hook Icon (Secondary Mark)
For favicons, app icons, and loading states: a minimal fishhook/bent-cursor SVG glyph, 20×20px. Clean 2px stroke. Used only when the full wordmark can't fit.

```
Color on dark bg:  #E84A2F (orange stroke)
Color on light bg: #0A0A0A (dark stroke)
Minimum size:      16×16px (favicon only)
```

### Logo Rules — The Hard Ones
| ✅ Do | ❌ Don't |
|-------|---------|
| `HookCut` — exact casing | `Hookcut`, `hookcut`, `HOOKCUT` |
| Two-tone type mark | Colored background box/"chip" around the logo |
| Solid orange on "Cut" | Gradient, glow, 3D effect on wordmark |
| Maintain aspect ratio | Stretch or squash |
| 80px wide minimum | Smaller than 80px in digital |
| Clear space = cap-height on all sides | Crowding with other elements |

### Logo in Context
- **Header (dark):** `Hook` white + `Cut` orange, no icon container, sits naturally in the nav bar
- **Footer:** Same as header
- **OG image:** White wordmark on `#0A0A0A` background, large
- **Favicon:** Orange hook glyph on dark bg, no wordmark
- **On orange CTAs:** White `HookCut` — both words white

---

## Colors

### The One That Matters

**Vermillion Orange — `#E84A2F`**

This is not construction orange. Not coral. Not salmon. Not neon. It's the color of urgency, creativity, and "wait, what?" — the feeling of a great hook.

```
Hex:   #E84A2F
RGB:   232, 74, 47
HSL:   ~10°, 79%, 55%
Hover: #D13F25
Glow:  rgba(232, 74, 47, 0.12)  — light bg
Glow:  rgba(232, 74, 47, 0.18)  — dark bg
```

It's the same orange on both marketing (light) and product (dark) — intentional. One brand, two contexts.

### Marketing Site — Light Palette

Used on: homepage, `/features`, `/blog`, `/pricing`, all marketing routes.

| Token | Value | Use |
|-------|-------|-----|
| Page background | `#FAFAF8` | Warm off-white — not pure white |
| Card background | `#FFFFFF` | With `1px solid #E4E4E7` |
| Alt section bg | `#F4F4F5` | Every other marketing section |
| Text — primary | `#0A0A0A` | Headlines, body |
| Text — muted | `#71717A` | Descriptions, body text |
| Text — light | `#A1A1AA` | Captions, timestamps, metadata |
| Border | `#E4E4E7` | Cards, dividers, inputs |
| Border — strong | `#D4D4D8` | Focused inputs |
| Primary | `#E84A2F` | CTAs, active states, brand accents |

### Product UI — Dark Palette

Used on: dashboard, `/analyze` flow, settings, admin.

| CSS Variable | Hex | Use |
|-------------|-----|-----|
| `--color-bg` | `#111111` | Page background — warm dark, never jet black |
| `--color-surface-1` | `#1A1A1A` | Cards |
| `--color-surface-2` | `#212121` | Elevated cards |
| `--color-surface-3` | `#2A2A2A` | Hover/active states |
| `--color-primary` | `#E84A2F` | Same orange everywhere |
| `--color-text` | `#F5F5F5` | Body text on dark |
| `--color-muted` | `#A1A1AA` | Secondary text |
| `--color-border-def` | `rgba(255,255,255,0.08)` | Standard borders |
| `--color-border-str` | `rgba(255,255,255,0.14)` | Emphasized borders |
| `--color-success` | `#16A34A` | ✓ Completed |
| `--color-warning` | `#F59E0B` | ⚠ Caution |
| `--color-error` | `#EF4444` | ✗ Error |

### Hook Score Color Ramp

This is how scores map to colors in the UI. Creators see this on every hook card.

```
0  ────── 40   →  #DC2626  (red)     "Not great, don't post this"
41 ────── 65   →  #F59E0B  (amber)   "Decent, maybe"
66 ────── 80   →  #E84A2F  (orange)  "Good — brand zone"
81 ─────  100  →  #16A34A  (green)   "Post this immediately"
```

The 66–80 "Good" range uses our brand orange on purpose — mid-tier high performers carry the brand color and reinforce recall.

### The Forbidden Colors

| Color | Why banned |
|-------|-----------|
| Any purple (`#8b5cf6`, `violet-*`, `purple-*`) | That's OpusClip's color. We are not OpusClip. |
| Jet black `#000000` | Too cold. Too techy. Too "edgy startup." Use `#111111`. |
| Pure white `#FFFFFF` as page bg | Use `#FAFAF8` — slightly warm, less harsh |
| Gold gradient effects | Reads as AI slop. Banned. |
| Saffron as dominant UI color | India accent only, pill badges, never primary |
| Neon anything | Nope |

---

## Typography

### The Stack

| Role | Font | Weight | Size | Notes |
|------|------|--------|------|-------|
| **Display** (marketing H1) | Outfit | 800 | 64px | `-0.04em` tracking |
| **H1** | Outfit | 700 | 44px | `-0.03em` tracking |
| **H2** | Outfit | 700 | 30px | `-0.02em` tracking |
| **H3** | Outfit | 600 | 22px | `-0.01em` tracking |
| **Body** | Geist Sans | 400 | 17px | `1.6` line height |
| **Body small** | Geist Sans | 400 | 14px | — |
| **Label / eyebrow** | Geist Sans | 600 | 12px | `+0.08em`, uppercase |
| **Score / timestamp** | Geist Mono | 700 | varies | `tabular-nums` |

**Outfit** = personality, punch, creator energy. Headlines only.  
**Geist Sans** = legible, clean, does what it needs to do. Body text.  
**Geist Mono** = scores, timestamps, credit balances. Anything that's a number.

### In Tailwind:
```tsx
// Marketing headline
className="font-[family-name:--font-display] font-extrabold text-[64px] tracking-[-0.04em]"

// Score display
className="font-mono tabular-nums text-2xl font-bold"

// Eyebrow label
className="text-xs font-semibold uppercase tracking-widest text-[#E84A2F]"
```

### Typography Rules
- Monospace for **every number** that matters (scores, minutes, prices, timestamps)
- Headline tracking always **negative** — never positive for H1/H2
- Display font (Outfit) **only** for headlines, never body paragraphs
- No orphans — if a headline wraps, the last line needs at least 2 words

---

## Voice & Tone

### The Quick Test
Before publishing copy, ask: *"Would a sharp creator friend actually say this, or does it sound like a press release?"*

**Creator friend says:** "HookCut found 5 hooks in your podcast. The best one scored 87."  
**Press release says:** "Our proprietary AI-powered engagement detection system has identified 5 potential viral content segments."

Write like the first.

### Vocabulary Guide

| ✅ Say this | ❌ Not this |
|------------|------------|
| Hook analysis engine | AI clipper |
| Hook scoring platform | Automatic clipping tool |
| Surfaces scroll-stopping moments | Generates clips |
| Hook Score | Virality score / Engagement score |
| Find My Hooks → | Submit / Analyze / Process |
| Start Analyzing → | Try for free / Sign up / Get started |
| Intelligently surfaces | Uses AI to find |
| Rejects / Penalizes | Filters out |
| Creator | Content creator / YouTuber |
| ₹499/month | $X/month (for Indian audiences) |
| Scroll-stopping potential | Viral potential |

### CTA Copy Rules
- Always ends with ` →` (space + arrow)
- 2–5 words max
- Verb-first: "Find My Hooks →", "Start Analyzing →", "See Pricing →"
- Never: "Click here", "Learn more" (alone), "Submit"

### Error Messages — Be a Human, Not a Stack Trace

| What broke | What to say |
|-----------|-------------|
| Bad YouTube URL | "That doesn't look like a YouTube URL. Try one that starts with `youtube.com/watch?v=`" |
| Video too long | "This video is over 3 hours — try a shorter one for faster results." |
| Analysis failed | "Analysis didn't complete. Your credits haven't been charged. Give it another go." |
| No hooks found | "We couldn't find strong hook moments here. Try a different video or a punchier segment." |
| Network error | "Connection hiccup. Check your internet and try again." |
| [object Object] | 🚫 This should never reach the user. Fix the error handling. |

---

## UI Patterns

### Buttons

| Variant | Style | When to use |
|---------|-------|-------------|
| Primary | `#E84A2F` bg, white text, `rounded-xl` | Main CTA — max 1 per section |
| Secondary | Outline / ghost | Supporting actions |
| Destructive | `#EF4444` text, subtle bg | Delete, remove |
| Ghost | Transparent | Low-emphasis links |

### Cards

- **Marketing:** white bg, `1px solid #E4E4E7`, gentle shadow, `radius: 1rem`
- **Product (dark):** `#1A1A1A` bg, `rgba(255,255,255,0.08)` border, `radius: 1rem`
- **No glassmorphism on marketing cards** — solid surfaces, clean
- Acceptable glassmorphism: product UI depth cues only, not decoration

### The Hook Timeline (Our Signature Visual)

The `<HookTimeline />` SVG is a brand identity element. It appears everywhere:
- Marketing homepage Section 4 ("Most viewers decide to scroll in 2 seconds")
- The hooks step above the hook card grid
- FigJam architecture diagrams
- Social media assets

**Important:** The timeline uses white SVG strokes. It needs a dark background container (`#111111`) to be visible. Don't put it on `#FAFAF8` — it'll disappear.

### Animation Philosophy

Every animation earns its place. Ask: *"Does this help the user understand what happened, or is it just for show?"*

| Element | Animation | Vibe |
|---------|-----------|------|
| Page transitions | Slide right | Directional, purposeful |
| Cards entering view | Fade up, staggered | Organic, not flashy |
| Score ring fill | Spring physics | Satisfying, game-like |
| Timeline marker pulse | Radial expand + fade | "We found something" |
| Error banner | Fade down | Urgent but calm |

Banned: spinning logos, scroll-triggered particle effects, parallax, entrance animations on every single element.

---

## Algorithm Messaging (Important)

Our scoring system is the product. The internals are the secret.

### Always OK to say:
- "HookCut intelligently surfaces the moments most likely to stop a scroll"
- "Each hook gets a score from 0–100 based on scroll-stopping potential"
- "HookCut automatically rejects filler, greetings, and sponsor reads"
- "18 hook type classifications including Curiosity Gap, Pain Escalation, Social Proof..."
- "Composite hooks layer multiple techniques for maximum impact"

### Never say publicly:
- The names of the 7 scoring dimensions
- Which LLM powers the analysis (Gemini/Claude/GPT)
- The specific rejection thresholds
- How transcript processing works
- Scoring weights or formulas

The score is the output. The output is the brand. The algorithm is the moat.

---

## India Positioning

HookCut has an explicit India-first stance. This isn't a footnote — it's a differentiator.

- **Pricing:** Show ₹ first, always. "₹499/month · No dollar conversion surprises."
- **Payment:** UPI support is a real differentiator vs. all Western competitors. Lead with it.
- **Languages:** 12+ Indian languages for video analysis. State this as a feature.
- **Hinglish:** Acceptable in social copy and email. ("Bhai, ye hook toh fire hai 🔥"). Never in product UI.
- **Flag emoji 🇮🇳:** OK in India-specific pills and social content. Don't overdo it.
- **Saffron:** Pill/badge accent only. Not a primary UI color. Not a background.

---

## What Good Looks Like

### ✅ Nailed it
```
"87 · CURIOSITY GAP · 0:14 → 0:47"
"Find the hook. Stop the scroll."
"₹499/month · UPI accepted · 12+ languages"
"HookCut intelligently surfaces the moments most likely to stop a scroll."
"Your next viral Short is already in your video."
```

### ❌ Miss
```
"Our AI-powered algorithm analyzes content using machine learning…"
"Generate unlimited clips automatically at scale"
[any purple in the UI]
"Try for free" as the primary CTA
"Submit" on the main action button
Showing 7 scoring dimensions in public copy
```

---

## File Organization

```
public/
  og-image.png           # 1200×630, dark bg, white wordmark
  logo-dark.svg          # White+orange wordmark (for dark bg)
  logo-light.svg         # Dark+orange wordmark (for light bg)
  favicon.ico
  icon-32.png            # Orange hook glyph

src/app/
  globals.css            # Product dark palette CSS variables
  marketing.css          # Marketing light palette
  layout.tsx             # Font loading (Outfit + Geist)

src/components/
  hook-timeline.tsx      # Brand identity SVG component ← iconic
  hero-hook-preview.tsx  # Hero right-column visual
  header.tsx             # Two-tone wordmark logo, no icon box
  footer.tsx             # SEO footer, 4-column
```

---

## Reference Designs

| Artifact | ID / URL | What's in it |
|----------|----------|--------------|
| Canva — logo wordmark (cap-C style) | `DAHDHk_nRRs` slide 1 | The HookCut wordmark style we're using |
| Canva — eye-with-flower motif | `DAHDHqqjBzY` | Decorative icon concept for future exploration |
| Canva — Hook Score Infographic | `DAH8bPTyp6A` (approx) | Score gauge, color ramp, what scores mean |
| Canva — Marketing Homepage Mockup | See memory file | Full 13-section scroll |
| Canva — Product UI Presentation | See memory file | All 4 flow steps |
| FigJam diagrams | 7 boards | Architecture, state machines, user journey |

---

## Version History

| Version | Date | What changed |
|---------|------|-------------|
| 1.0 | March 2026 | Initial brand identity — full rebrand from purple/glassmorphism → orange/warm-dark |

---

*Single source of truth for HookCut's visual identity, copy standards, and design decisions. When in doubt, come back here.*
