# HookCut — Brand Identity Guide

> Version 1.0 · March 2026 · Maintained by the HookCut design team

---

## 1. Brand Essence

### Mission
Surface the scroll-stopping moments hiding inside every YouTube video — so creators never have to guess which clip will go viral.

### Vision
Become the default hook intelligence layer for short-form video creation across India and beyond.

### Tagline (locked)
> **"Find the hook. Stop the scroll."**

This line does not change. It is used verbatim across all touchpoints: homepage hero, OG tags, email subjects, App Store description, social bios.

### Brand Personality
| Trait | What it means in practice |
|-------|--------------------------|
| **Precise** | We show scores, not opinions. Numbers, not vibes. |
| **Confident** | We don't hedge. "The hook is at 1:32." Not "maybe around 1:32." |
| **Creator-forward** | We speak to creators, not IT departments. Casual but never sloppy. |
| **Transparent (selectively)** | We explain what we found and why it matters. We don't expose how we found it. |
| **Energetic** | Fast, sharp, direct. No filler. No corporate speak. |

### What HookCut Is NOT
- ❌ An "AI clipper" — we are a **hook analysis engine** / **hook scoring platform**
- ❌ A generic video editor
- ❌ A batch clip factory (volume ≠ quality)
- ❌ An enterprise SaaS tool
- ❌ A purple brand (purple = OpusClip territory — we are orange)

---

## 2. Logo

### Wordmark
**HookCut** — rendered in Outfit 800 (ExtraBold), letter-spacing `-0.02em`.

The capital **C** in "Cut" is intentional and locked. It creates a visual rhythm: `Hook` + `Cut` read as two strong words fused into one brand name.

- ✅ `HookCut` — correct
- ❌ `Hookcut` — incorrect (loses the visual split)
- ❌ `HOOKCUT` — incorrect (all-caps loses personality)
- ❌ `hookcut` — incorrect (too casual, loses brand hierarchy)

### Logo Mark (Icon)
A minimal hook glyph — a stylized fishhook or bent play-cursor, 20×20px SVG path. Used as:
- Favicon (32×32, 16×16)
- App icon companion to wordmark
- Loading spinner variant

### Color Variants
| Context | Wordmark color | Background |
|---------|---------------|------------|
| Marketing site (light) | `#0A0A0A` (near-black) | `#FAFAF8` or white |
| Product UI (dark) | `#F5F5F5` (near-white) | `#111111` |
| On orange/colored bg | `#FFFFFF` | `#E84A2F` |

### Logo Rules
- **No gradients** on the logo — solid color only
- **No drop shadows**, glows, or 3D effects
- **No stretching** — maintain aspect ratio always
- **Minimum size**: 80px wide (digital), 25mm wide (print)
- **Clear space**: equal to the height of the "H" on all sides

---

## 3. Color System

### Primary Brand Color
| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| **Vermillion Orange** | `#E84A2F` | `232, 74, 47` | Primary CTA, active states, hook scores 66–80, brand accent |
| Vermillion Dark | `#D13F25` | `209, 63, 37` | Hover state for primary buttons |
| Vermillion Glow | `rgba(232,74,47,0.12)` | — | Subtle backgrounds, focus rings |

**Why this orange?** It sits between bold warm red and energetic orange — closer to "urgent creative" than "construction warning." It reads as confident and viral-energy on both light and dark backgrounds. It is deliberately NOT neon orange, NOT coral, NOT saffron.

### Marketing Site Palette (Light)
| Token | Hex | Use |
|-------|-----|-----|
| `--bg` | `#FAFAF8` | Page background — warm off-white (not pure white) |
| `--surface` | `#FFFFFF` | Card backgrounds |
| `--surface-raised` | `#F4F4F5` | Alternate section backgrounds |
| `--text-primary` | `#0A0A0A` | Headings, primary text |
| `--text-muted` | `#71717A` | Body text, descriptions |
| `--text-light` | `#A1A1AA` | Captions, metadata, timestamps |
| `--border` | `#E4E4E7` | Card borders, dividers |
| `--border-strong` | `#D4D4D8` | Input borders on focus |

### Product UI Palette (Dark)
| Token | CSS Variable | Hex | Use |
|-------|-------------|-----|-----|
| Background | `--color-bg` | `#111111` | Page background — warm dark (not cold blue-black) |
| Surface 1 | `--color-surface-1` | `#1A1A1A` | Card backgrounds |
| Surface 2 | `--color-surface-2` | `#212121` | Elevated surfaces |
| Surface 3 | `--color-surface-3` | `#2A2A2A` | Hover / active states |
| Primary | `--color-primary` | `#E84A2F` | Same orange — unified across light/dark |
| Primary Glow | `--color-primary-glow` | `rgba(232,74,47,0.18)` | Glow effects |
| Text | `--color-text` | `#F5F5F5` | Body text on dark |
| Muted | `--color-muted` | `#A1A1AA` | Secondary text |
| Border Sub | `--color-border-sub` | `rgba(255,255,255,0.04)` | Very subtle dividers |
| Border Default | `--color-border-def` | `rgba(255,255,255,0.08)` | Standard borders |
| Border Strong | `--color-border-str` | `rgba(255,255,255,0.14)` | Emphasized borders |
| Success | `--color-success` | `#16A34A` | Completed states |
| Warning | `--color-warning` | `#F59E0B` | Caution states |
| Error | `--color-error` | `#EF4444` | Error states |

### Hook Score Color Ramp
Scores map visually to engagement potential:

| Score Range | Color | Hex | Label |
|-------------|-------|-----|-------|
| 0–40 | Red | `#DC2626` | Poor |
| 41–65 | Amber | `#F59E0B` | Moderate |
| 66–80 | Orange | `#E84A2F` | Good (brand) |
| 81–100 | Green | `#16A34A` | Exceptional |

The 66–80 "Good" range uses the brand orange intentionally — mid-tier high performers carry the brand color, reinforcing recognition.

### Color Don'ts
- ❌ No purple (`#8b5cf6`, `violet-*`, `purple-*`) — this is OpusClip's color
- ❌ No jet-black (`#000000` or `#06060e`) background — too cold/techy
- ❌ No pure white (`#FFFFFF`) as the only background — use `#FAFAF8`
- ❌ No gold gradient effects — reads as AI slop
- ❌ No saffron as a primary color — India section uses it as a pill accent only
- ❌ No neon / glow background blobs

---

## 4. Typography

### Type Scale
| Role | Font | Weight | Size | Letter Spacing | Line Height |
|------|------|--------|------|---------------|-------------|
| Display (marketing hero) | Outfit | 800 | 64px | -0.04em | 1.05 |
| H1 | Outfit | 700 | 44px | -0.03em | 1.1 |
| H2 | Outfit | 700 | 30px | -0.02em | 1.15 |
| H3 | Outfit | 600 | 22px | -0.01em | 1.2 |
| Body | Geist Sans | 400 | 17px | 0 | 1.6 |
| Body Small | Geist Sans | 400 | 14px | 0 | 1.5 |
| Label / Eyebrow | Geist Sans | 600 | 12px | +0.08em uppercase | 1.2 |
| Score / Timestamp | Geist Mono | 700 | varies | 0 | 1 |
| Code / Debug | Geist Mono | 400 | 13px | 0 | 1.5 |

### Font Loading (Next.js)
```typescript
import { Geist, Geist_Mono, Outfit } from 'next/font/google'

const geist = Geist({ subsets: ['latin'], variable: '--font-sans' })
const geistMono = Geist_Mono({ subsets: ['latin'], variable: '--font-mono' })
const outfit = Outfit({ subsets: ['latin'], weight: ['600','700','800'], variable: '--font-display' })
```

### Tailwind Usage
```tsx
// Display headlines (marketing)
className="font-[family-name:--font-display] font-extrabold text-[64px] tracking-[-0.04em]"

// Scores and timestamps
className="font-mono tabular-nums"

// Body text
className="font-sans text-base leading-relaxed"
```

### Typography Rules
- **Never use default system fonts** for brand-facing surfaces
- **Display font (Outfit)** only for headlines — not body text
- **Monospace (Geist Mono)** for all numeric values: scores, timestamps, credit balances, percentages
- **Tracking**: Always negative for headlines (-0.02em to -0.04em). Never positive for headlines.
- **Orphans**: Headlines over 2 lines should not leave a single word on the last line — rewrite copy or use `max-w` to force wrap

---

## 5. Voice & Tone

### Core Principles
1. **Say what it does, not how it does it** — "HookCut surfaces the moments most likely to stop a scroll." Not "Our proprietary 7-dimension scoring engine analyzes attention retention coefficients."
2. **Numbers over adjectives** — "87 out of 100" beats "really high score"
3. **Creator-peer, not SaaS-vendor** — Write like a sharp creator friend who also ships code, not like enterprise software
4. **Active, not passive** — "HookCut identifies…" not "Hooks are identified by…"

### Vocabulary Guide
| Use this | Not this |
|----------|----------|
| Hook analysis engine | AI clipper |
| Hook scoring platform | Automatic clipping tool |
| Surfaces scroll-stopping moments | Generates clips |
| Hook Score | Virality score / engagement score |
| Find My Hooks → | Submit / Analyze / Generate |
| Start Analyzing → | Try for free / Sign up |
| Intelligently surfaces | Uses AI to find |
| Scroll-stopping potential | Viral potential (overused) |
| Penalty / rejects | Filters out |
| Creator | Content creator / Youtuber |
| ₹499/month | $X/month (for India audiences) |

### Error Messages
Errors should be:
- Specific: say what failed, not just "something went wrong"
- Actionable: tell them what to do next
- Human: not technical/stacktrace language

| Scenario | Copy |
|----------|------|
| Invalid YouTube URL | "That doesn't look like a YouTube URL. Paste a link starting with youtube.com/watch?v=" |
| Video too long | "This video is over 3 hours — try a shorter one for best results." |
| Analysis failed | "Analysis didn't complete. Your credits haven't been charged. Try again in a moment." |
| No hooks found | "We couldn't find strong hook moments in this video. Try a different video or a shorter segment." |
| Network error | "Connection issue. Check your internet and try again." |

### Copy Length Rules
- **Hero headlines**: 4–8 words max
- **Sub-headlines**: 1–2 sentences, under 30 words
- **CTA buttons**: 2–5 words, always with directional arrow →
- **Micro-copy** (below inputs): under 10 words
- **Feature descriptions**: 1–3 sentences
- **Blog posts**: 1,500–2,000 words, SEO-optimized

---

## 6. UI Component Language

### Buttons
| Variant | Use | Color |
|---------|-----|-------|
| Primary | Main CTA ("Find My Hooks →", "Start Analyzing →") | `#E84A2F` bg, white text |
| Secondary | Supporting actions ("See Pricing", "Learn More") | Outline / ghost |
| Destructive | Delete / permanent actions | Red (`#EF4444`) |
| Ghost | Low-emphasis actions | Transparent + muted text |

CTA copy always ends with `→` — it signals forward momentum.

### Cards
- Border radius: `1rem` (cards), `0.625rem` (small elements)
- Marketing cards: white bg, `1px solid #E4E4E7`, subtle `box-shadow`
- Product cards: `#1A1A1A` bg, `rgba(255,255,255,0.08)` border
- No glassmorphism on marketing cards — clean solid surfaces only
- Minimal glassmorphism permitted in product UI for depth (not decoration)

### Spacing Scale
Built on Tailwind's default 4px base:
- Tight (within components): 4px, 8px, 12px
- Standard (between elements): 16px, 20px, 24px
- Generous (between sections): 48px, 64px, 96px
- Marketing section padding: `py-24` (96px vertical)

### Animations
| Element | Animation | Duration |
|---------|-----------|----------|
| Page transitions | Slide right (`slideRight` variant) | 300ms ease |
| Cards entering | Fade up (`fadeUpItem` variant) | 200ms, staggered |
| Hook score ring | Spring fill | stiffness 45, damping 18 |
| Timeline marker pulse | Radial expand + fade | 1.2s, infinite loop |
| Ticker | Linear translate | 24s, infinite |
| Error banner | Fade down | 200ms ease |

**Animation philosophy**: Purposeful, never decorative. Every animation communicates state or guides attention. No spinning logos, no parallax scrolling, no scroll-triggered particle effects.

---

## 7. The Hook Timeline (Brand Identity Element)

The `<HookTimeline />` SVG component is a signature visual element — it appears across:
- The marketing homepage (Section 4: "The Problem")
- The hooks step in the product UI (above hook card grid)
- FigJam architecture diagrams
- Canva reference designs
- Social media assets

**Visual spec:**
- Full-width horizontal track line — `rgba(255,255,255,0.08)` on dark, `rgba(0,0,0,0.08)` on light
- Triangle markers (▲) at each hook timestamp — colored by score ramp
- Timestamp labels below each marker — monospace, muted
- Active hook: orange glow ring animation (2px stroke, radial expand, 1.2s loop)
- Dark background required when using white SVG strokes

This visual communicates the core product value instantly: *your video has hidden moments of viral potential, and we found them.*

---

## 8. Photography & Illustration

### Creator Testimonials
Use abstract circular avatar illustrations — geometric or painterly, not photos of real people. This avoids:
- Fake review appearance
- Privacy/consent issues
- Stock photo "corporate" feel

**Color palette for avatars**: Use brand-adjacent colors — blue, emerald, teal. Not purple.

### Product Screenshots
When showing the UI in marketing contexts:
- Use real product components rendered with mock data (not browser screenshots)
- Dark UI always renders on a dark background — never float a dark window on a white page without a containing card
- Add 1–2° rotation for "placed on a surface" feel — never straight-on floating

### Icons
Use Lucide React icons throughout (already installed). Style: `strokeWidth={1.5}` for decorative, `strokeWidth={2}` for interactive.

No icon libraries mixing (no Heroicons, no FontAwesome alongside Lucide).

---

## 9. Brand Application Examples

### ✅ Correct Usage
- "Find the hook. Stop the scroll." on the hero
- "87 score · CURIOSITY GAP · 0:14 → 0:47" on a hook card
- "₹499/month · UPI accepted" in the India section
- "HookCut intelligently surfaces the moments most likely to stop a scroll."
- Score gauge with orange ring at 74, green ring at 87

### ❌ Incorrect Usage
- "Our AI-powered algorithm analyzes your content using machine learning…" (too generic)
- "Generate unlimited clips automatically" (sounds like a bulk clipper)
- Any purple color in the UI
- "Try for free" as the primary CTA (implies confusion about free tier)
- "Submit" or "Upload" on the main action button
- Showing 7 scoring dimensions in marketing copy (never expose internals)

---

## 10. Algorithm Messaging Rules

HookCut uses a proprietary scoring system. In all public-facing copy:

### DO say:
- "HookCut intelligently surfaces the moments most likely to stop a scroll"
- "Each hook gets a score from 0–100 based on scroll-stopping potential"
- "HookCut automatically rejects filler segments, greetings, and sponsor reads"
- "Composite hooks layer multiple engagement techniques for maximum impact"
- "18 hook type classifications including Curiosity Gap, Pain Escalation, Social Proof…"

### NEVER say:
- The names of the 7 scoring dimensions (attention_score, hook_type_strength, etc.)
- How the transcript is processed
- Which LLM powers the analysis
- The threshold scores used for rejection
- Specific weights in the scoring formula

The score is the output. The output is the product. The algorithm is the secret.

---

## 11. SEO & Metadata

### Default OG Image
Size: 1200×630px
Background: `#0A0A0A`
Center: HookCut wordmark (white) + tagline "Find the hook. Stop the scroll." (white/60)
Bottom-right: Example hook score gauge (87, green ring)

### Page Title Format
```
[Page-Specific Title] | HookCut
```
Examples:
- `Find the hook. Stop the scroll. | HookCut` (homepage)
- `HookCut vs OpusClip: Which Tool Finds Better Hooks? | HookCut` (blog)
- `YouTube Hook Ideas for Finance Creators | HookCut` (niche page)

### Meta Description Length
150 characters max. Always includes: primary keyword + benefit + brand name.

---

## 12. India Brand Considerations

HookCut has explicit India-first positioning:

### Language
- Primary: English
- Secondary: Hinglish copy acceptable in social/email ("Bhai, ye hook toh fire hai 🔥")
- Never mix scripts in UI (no Devanagari in the product)
- 12+ Indian languages supported for video analysis — state this as a feature, not the interface language

### Pricing Display
- Always show ₹ (rupee) price first for Indian audiences
- Never show only USD pricing on Indian-facing pages
- "No dollar conversion surprises" is a valid, specific marketing claim

### Payment
- Highlight UPI support explicitly — it's a true differentiator vs. Western competitors
- "UPI accepted" pill in the India section

### Visual
- Indian flag emoji (🇮🇳) acceptable in India-specific pills
- No saffron, white, green color combinations that read as the Indian flag pattern in the UI
- Saffron (`#FF9933`) only as a pill/badge accent — never as a dominant UI color

---

## 13. File Naming & Asset Organization

```
public/
  og-image.png          # 1200×630 OG image
  logo-dark.svg         # White wordmark (for dark backgrounds)
  logo-light.svg        # Dark wordmark (for light backgrounds)
  favicon.ico
  icon-32.png
  icon-16.png
  apple-touch-icon.png  # 180×180

src/
  app/
    globals.css         # Product UI CSS variables (dark palette)
    marketing.css       # Marketing site CSS variables (light palette)
  components/
    hook-timeline.tsx   # Brand identity SVG component
    hero-hook-preview.tsx
```

---

## 14. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | March 2026 | Initial brand identity — complete rebrand from purple/glassmorphism to orange/warm-dark |

---

*This document is the single source of truth for HookCut's visual identity, voice, and design decisions. All new components, copy, and marketing materials should be validated against it.*
