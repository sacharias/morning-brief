---
name: Morning Brief
description: A daily AI/startup intelligence brief that reads like a native iOS briefing room.
colors:
  burnt-sienna: "#b4540a"
  paper: "#faf8f4"
  surface: "#ffffff"
  ink: "#1c1a17"
  ink-soft: "#6b655a"
  line: "#e7e2d9"
typography:
  display:
    fontFamily: "Newsreader, Georgia, serif"
    fontSize: "clamp(1.6rem, 5.5vw, 2.25rem)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Newsreader, Georgia, serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "normal"
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.08em"
rounded:
  card: "0.75rem"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "28px"
components:
  card-item:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "14px 16px"
  link:
    textColor: "{colors.ink}"
  link-hover:
    textColor: "{colors.burnt-sienna}"
  chip-metric:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.pill}"
    padding: "2px 8px"
  badge-new:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.burnt-sienna}"
    rounded: "{rounded.pill}"
    padding: "1px 6px"
  segment-indicator:
    backgroundColor: "{colors.burnt-sienna}"
    textColor: "{colors.surface}"
    rounded: "{rounded.pill}"
  tab-active:
    textColor: "{colors.burnt-sienna}"
---

# Design System: Morning Brief

## 1. Overview

**Creative North Star: "The Native Briefing Room"**

Morning Brief is a daily intelligence briefing rendered as a native iOS app. The
substance is editorial — a curated, ranked, opinionated read on what moved
overnight in AI, startups, open source, and research — but the *vehicle* is a
phone app, not a web page. A bottom tab bar owns navigation. Panels are sections
of a briefing, not scrollable feeds. Type carries the authority of a well-set
morning paper (Newsreader serif headlines over a warm paper ground) while
interaction carries the momentum of native software: segmented controls with a
sliding indicator, springy tap feedback, safe-area awareness. The reader is a
single person glancing one-handed over coffee with sixty seconds of attention.

The system is deliberately flat and quiet so the content can be sharp. Depth
comes from tonal layering — white surfaces floating on warm paper, hairline
borders — never from heavy shadows or chrome. One signal color, Burnt Sienna,
does all the pointing: links, the active tab, the "new today" badge. Everything
else is ink on paper.

It explicitly rejects four things, carried straight from the product brief: the
**generic SaaS dashboard** (card grids, gradient hero-metrics, purple-blue
startup palette), the **cluttered news portal** (ad density, thumbnail walls,
infinite scroll), the **social feed** (engagement-bait, like-count chrome), and
the **crypto/AI-hype aesthetic** (neon, dark-by-default, glassmorphism, "the
future is here" bombast).

**Key Characteristics:**
- Native-app interaction model: bottom tab bar, segmented controls, tap feedback.
- Warm paper ground (#faf8f4), not a cold white or a cream-tinted near-white.
- One accent only — Burnt Sienna — spent sparingly on signal.
- Editorial serif/sans pairing: Newsreader display, Inter body.
- Flat by default; depth via borders and tone, not shadow.
- Finite and calm: a complete morning read with a clear top and bottom.

## 2. Colors

A warm, low-chroma paper palette with a single saturated signal accent. The
restraint is the point: with only one color that carries meaning, the eye learns
that Burnt Sienna always means "go here / new / active."

### Primary
- **Burnt Sienna** (#b4540a): The lone signal color. Used for links on hover,
  the active bottom-tab label and icon, the sliding segmented-control indicator
  (as a fill, with white text on top), the "new" badge, tag chips, and the
  short dash before each executive-summary line. Never decorative — it always
  marks something the reader can act on or should notice.

### Neutral
- **Ink** (#1c1a17): Primary text — headlines, link labels, item titles. A
  near-black warmed slightly toward the paper so it never looks like cold
  printer black.
- **Ink-Soft** (#6b655a): Secondary text — body copy under items, descriptions,
  metric labels, run notes, timestamps. Holds ≥4.5:1 on both paper and surface.
- **Paper** (#faf8f4): The body ground. A warm off-white — the page itself.
  Also the fill of metric chips so they read as inset against white surfaces.
- **Surface** (#ffffff): Pure white. Item cards, the segmented-control track,
  empty-state panels — the floating layer that sits one step above paper.
- **Line** (#e7e2d9): Hairline borders and dividers. Section-head underlines,
  card outlines, the sticky header/tab-bar edges, the dashed "show more" border.

### Named Rules
**The One Signal Rule.** Burnt Sienna appears on ≤10% of any screen and only on
things that are actionable or genuinely new. If a second element wants to be
orange "for emphasis," the answer is weight or size, not color. Its rarity is
what makes it legible at a glance in morning light.

**The Warm-Black Rule.** Text is never `#000`. Ink is `#1c1a17` — black pulled
toward the paper's hue — so the page reads as printed, not backlit.

## 3. Typography

**Display Font:** Newsreader (with Georgia, serif fallback)
**Body Font:** Inter (with ui-sans-serif, system-ui fallback)

**Character:** A true contrast-axis pairing — a literary optical-size serif
against a neutral grotesque sans. Newsreader brings the editorial, considered,
morning-paper authority to anything that ranks or headlines; Inter handles the
dense, scannable working text. They never compete because they're built for
opposite jobs.

### Hierarchy
- **Display** (Newsreader, 600, `clamp(1.6rem, 5.5vw, 2.25rem)`, line-height
  1.2, `text-wrap: balance`): The day's headline at the top of Today. One per
  brief. Tight tracking, balanced line lengths.
- **Headline** (Newsreader, 600, 1.25rem / ~1.3): Section titles ("Top X
  Threads", "Trending GitHub") and the "Morning Brief" wordmark in the header.
  Sits over a hairline underline.
- **Body** (Inter, 400, 0.9375rem / 1.55, →1rem on md+): Item descriptions,
  follow-ups, prose lists. Reading column capped at ~680px (well under 75ch).
- **Label** (Inter, 500, 0.75rem, letter-spacing 0.08em, UPPERCASE): The single
  dated eyebrow above the headline (in Burnt Sienna) and the "new" badge. Tiny,
  tracked, used sparingly.
- **Micro** (Inter, 500, 0.65–0.7rem, tabular-nums): Rank numbers (`01`, `02`),
  tab-bar labels, metric values. Tabular figures so ranked lists stay aligned.

### Named Rules
**The One Eyebrow Rule.** The uppercase tracked label appears exactly once per
view — the date over the headline. It is a deliberate masthead device, not a
per-section scaffold. Section titles are serif headlines, never eyebrows.

## 4. Elevation

This system is **flat by default**. There are no drop shadows anywhere. Depth is
built from two materials only: **tonal layering** (white `surface` cards
floating on warm `paper`, separated by `line` hairline borders) and **a 4px
backdrop blur** on the two sticky chrome elements — the top header and the bottom
tab bar — which use a translucent paper fill (`paper/90`–`/95`) so content
softly passes beneath them. That blur is functional (it signals "this bar floats
over scrolling content"), never decorative glass.

### Named Rules
**The No-Shadow Rule.** Surfaces never cast shadows. If an element needs to feel
raised, give it the white `surface` fill and a `line` border, not a shadow. A
shadow here would read as 2014-era Material and break the paper metaphor.

**The Tactile-Press Rule.** Because the system is flat at rest, *motion* carries
tactility. Pressable elements (cards, the show-more button) scale to ~0.985 on
`:active` — a small physical "give" that makes taps feel native. This is the
only transform surfaces are allowed.

## 5. Components

Components are **tactile and confident**: quiet at rest, springy under the
finger. The bordered, flat surface is the resting state; motion supplies the
feedback.

### Buttons
- **Shape:** Pill (`rounded-full`) for controls; rounded card (12px) for the
  full-width "show more" affordance.
- **Show-more:** Full-width, dashed `line` border, `ink-soft` label. On hover the
  border and text shift to Burnt Sienna; on `:active` it scales to 0.985.
- **Hover / Focus:** Color transition only (200ms). Press feedback is the scale.

### Chips
- **Metric chips:** Pill, `paper` fill, `line` border, `ink-soft` text with the
  value in bold `ink`. Used for engagement/star counts. Tabular figures.
- **Tag chips:** Pill, Burnt Sienna at 10% fill with a 25% Burnt Sienna border
  and Burnt Sienna text. Marks categorical tags.
- **"New" badge:** Pill, `surface`/Burnt Sienna-10% fill, Burnt Sienna 30%
  border, uppercase micro label. Flags items new to today's brief.

### Cards / Containers
- **Corner Style:** 12px (`rounded-xl`).
- **Background:** White `surface` on the `paper` page.
- **Shadow Strategy:** None — see Elevation. Border + tone only.
- **Border:** 1px `line` (#e7e2d9) on all sides. **Never a colored side-stripe.**
- **Internal Padding:** ~14px vertical / 16px horizontal.
- **Press:** `:active` scale 0.985.
- **Anatomy:** A leading 2-digit tabular rank, the title (a Burnt-Sienna-hover
  link or plain text), an optional "new" badge, body line, then a wrap row of
  metric and tag chips.

### Inputs / Fields
- **Day picker:** A native `<select>` styled as a pill — `surface` fill, `line`
  border, `ink` text, custom chevron. Native control on purpose: it gets the OS
  picker on mobile, which is the most native interaction available.

### Navigation
- **Bottom Tab Bar:** Fixed to the bottom, four tabs (Today / X / Code /
  Papers), each a stroked 24px icon over a micro label. Inactive = `ink-soft`;
  active = Burnt Sienna. Translucent `paper/95` fill with 4px backdrop blur and
  `pb-[env(safe-area-inset-bottom)]` so it hugs the home indicator. This is the
  app's primary navigation — the single most "native iOS" element in the system.
- **Segmented Control:** Within X and Code pages, an iOS-style segmented control:
  a pill track (`surface`, `line` border) with a Burnt Sienna indicator that
  *slides* (translateX + width, 200ms ease-out) between segments; the active
  segment's text flips to white. Inactive text is `ink-soft`.
- **Sticky Header:** Top bar with the serif "Morning Brief" wordmark and (when
  >1 day exists) the day picker. Translucent `paper/90`, 4px blur, `line` bottom
  border.

## 6. Do's and Don'ts

### Do:
- **Do** keep Burnt Sienna (#b4540a) to ≤10% of any screen, only on actionable
  or genuinely-new elements — the One Signal Rule.
- **Do** convey depth with the white-surface-on-paper tonal step plus a 1px
  `line` border. Flat is the house style.
- **Do** make taps feel physical: `:active` scale ~0.985 on pressables, sliding
  indicators on segmented controls, color transitions ≤200ms ease-out.
- **Do** respect the device: safe-area insets, native `<select>` for the day
  picker, tab-bar navigation, a reading column capped near 680px.
- **Do** set headlines in Newsreader with `text-wrap: balance`; set working text
  in Inter ≤75ch.
- **Do** use tabular figures for ranks, metrics, and any aligned number column.
- **Do** give every transition a `prefers-reduced-motion: reduce` fallback
  (crossfade or instant) — the slide and the press-scale included.

### Don't:
- **Don't** build the **generic SaaS dashboard**: no identical card grids, no
  gradient hero-metric blocks, no purple-blue startup palette.
- **Don't** drift toward the **cluttered news portal**: no thumbnail walls, no
  ad slots, no infinite scroll. The brief is finite — give it a clear bottom.
- **Don't** adopt **social-feed** chrome: no vanity like-counts, no
  engagement-bait. Metrics exist to justify ranking, nothing more.
- **Don't** touch the **crypto/AI-hype aesthetic**: no neon glow, no
  dark-by-default, no glassmorphism-as-decoration, no "the future is here" copy.
- **Don't** add drop shadows. If it needs to lift, it gets a border and a tonal
  step — the No-Shadow Rule.
- **Don't** use a colored `border-left`/`border-right` stripe on cards or items.
  Borders are full and hairline `line`, or nothing.
- **Don't** scatter uppercase tracked eyebrows above sections — there is exactly
  one, the date masthead. Section labels are serif headlines.
- **Don't** introduce a second accent color "for emphasis." Reach for weight or
  size instead.
