---
name: Morning Brief
description: A daily AI/startup intelligence brief that reads like a native iOS briefing room.
colors:
  burnt-sienna: "#b4540a"
  burnt-sienna-deep: "#93430a"
  paper: "#faf8f4"
  surface: "#ffffff"
  ink: "#1c1a17"
  ink-mid: "#4a443a"
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
  group-list:
    backgroundColor: "{colors.surface}"
    rounded: "1rem"
    border: "1px {colors.line}"
    dividers: "1px {colors.line}"
  row-item:
    textColor: "{colors.ink}"
    padding: "14px 16px"
    pressed: "{colors.paper}"
  link-hover:
    textColor: "{colors.burnt-sienna-deep}"
  meta-line:
    textColor: "{colors.ink-soft}"
    fontSize: "0.75rem"
  flag-new:
    textColor: "{colors.burnt-sienna}"
    fontSize: "0.625rem"
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
- **Burnt Sienna** (#b4540a): The lone signal color. Used for the active
  bottom-tab label and icon, the sliding segmented-control indicator (as a
  fill, with white text on top), the "new" flag, inline tags, the show-more
  row, and the short dash before each executive-summary line. Never
  decorative — it always marks something the reader can act on or should
  notice. Hover/press states darken to Burnt Sienna Deep.

### Neutral
- **Ink** (#1c1a17): Primary text — headlines, item titles, the main read of
  each row. A near-black warmed slightly toward the paper so it never looks
  like cold printer black.
- **Ink-Mid** (#4a443a): Emphasis prose — the executive summary and follow-up
  lines. Darker than ink-soft because these are primary reading content, held
  high for bright-light legibility.
- **Ink-Soft** (#6b655a): Secondary text — descriptions, bylines, meta lines,
  run notes, timestamps. Holds ≥4.5:1 on both paper and surface.
- **Paper** (#faf8f4): The body ground. A warm off-white — the page itself.
  Also the pressed-row highlight inside white group lists.
- **Surface** (#ffffff): Pure white. Group lists, the segmented-control track,
  empty-state panels — the floating layer that sits one step above paper.
- **Line** (#e7e2d9): Hairline borders and dividers. Row separators inside
  group lists, group outlines, the sticky header/tab-bar edges, the end-cap
  rules.
- **Burnt Sienna Deep** (#93430a): The hover/pressed shade of the accent —
  row titles shift to it on hover so links darken instead of glowing.

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
  Posts", "GitHub Trending") and the "Morning Brief" wordmark in the header.
  Carries an item count at the far baseline in micro `ink-soft` figures.
- **Body** (Inter, 400, 0.9375rem / 1.55, →1rem on md+): Item descriptions,
  follow-ups, prose lists. Reading column capped at ~680px (well under 75ch).
- **Label** (Inter, 500, 0.75rem, letter-spacing 0.08em, UPPERCASE): The single
  dated eyebrow above the headline (in Burnt Sienna) and the "new" flag. Tiny,
  tracked, used sparingly.
- **Rank** (Newsreader italic, 0.875rem, `ink-soft`): The row number in every
  ranked list — a serif italic figure, right-aligned in its gutter, like a
  numbered list in a well-set magazine.
- **Micro** (Inter, 400–500, 0.65–0.75rem, tabular-nums): Tab-bar labels,
  meta lines, timestamps. Tabular figures so numbers stay aligned.

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

**The Tactile-Press Rule.** Because the system is flat at rest, *feedback*
carries tactility. Rows inside a group list highlight to `paper` on `:active`
(the iOS cell press); standalone pills and buttons scale to ~0.985. Both are
small physical "gives" that make taps feel native.

## 5. Components

Components are **tactile and confident**: quiet at rest, springy under the
finger. The bordered, flat surface is the resting state; motion supplies the
feedback.

### Group Lists (the core content container)
- **Shape:** One white `surface` container per section, 16px corners
  (`rounded-2xl`), 1px `line` border, rows separated by hairline `line`
  dividers — the iOS inset-grouped-list, set like a newspaper column.
- **Row anatomy:** A serif-italic rank in a right-aligned gutter, then the
  content column. The *entire row* is the tap target (a stretched link covers
  it); pressing highlights the row to `paper`.
- **Content-aware hierarchy:** rows lead with whatever carries the story. X
  posts put the summary in `ink` as the main read with the @handle above it as
  a micro byline; repos and papers lead with their title in medium `ink`, the
  description in `ink-soft` below.
- **Meta line:** One quiet micro line under the body — compacted metrics
  joined by middots (`102K likes · 14.2K reposts · 4,734 replies`), capped at
  three, tabular figures. Tags append in Burnt Sienna. No chips, no borders —
  metrics justify the ranking, nothing more.
- **"New" flag:** A 4px Burnt Sienna dot plus a tiny tracked uppercase "New"
  inline after the title/byline. Flags items new to today's brief.
- **Show-more:** The last row of the group — centered Burnt Sienna micro
  label ("Show all 20"), `paper` highlight on hover/press. Newly revealed rows
  re-run the entrance stagger from zero.

### Buttons & Inputs
- **Shape:** Pill (`rounded-full`) for standalone controls; press feedback is
  scale 0.985 plus a ≤200ms color transition.
- **Day picker:** A native `<select>` styled as a pill — `surface` fill, `line`
  border, `ink` text, chevron glyph, dates formatted "Thu, Jun 11". Native
  control on purpose: it gets the OS picker on mobile, which is the most
  native interaction available.

### States
- **Loading:** A skeleton shaped like the brief itself — masthead bar, summary
  lines, one group list — pulsing `line`-tone blocks. Never a spinner.
- **Empty page:** A `surface` panel with a serif "Nothing here today" and one
  sentence of explanation. Teaches the rhythm: check back tomorrow.
- **Error:** Serif headline, the message in `ink-soft`, and a pill "Try again"
  button. Centered in the viewport.

### Navigation
- **Bottom Tab Bar:** Fixed to the bottom, four tabs (Today / X / Code /
  Papers), each a stroked 24px icon over a micro label. Inactive = `ink-soft`;
  active = Burnt Sienna with the icon popping up 1px, scaling to 1.1 and its
  stroke thickening 1.8→2.3 — the iOS outline→emphasized cue. Translucent
  `paper/95` fill with 4px backdrop blur and
  `pb-[env(safe-area-inset-bottom)]` so it hugs the home indicator. This is the
  app's primary navigation — the single most "native iOS" element in the system.
  Switching tabs scrolls to the top of the new page.
- **Segmented Control:** Within X and Code pages, an iOS-style segmented control:
  a pill track (`surface`, `line` border) with a Burnt Sienna indicator that
  *slides* (translateX + width, 250ms ease-out-quart) between segments; the
  active segment's text flips to white. Inactive text is `ink-soft`.
- **Scroll-Aware Header:** Top bar with the serif "Morning Brief" wordmark and
  (when >1 day exists) the day picker. At rest it sits flush with the paper —
  no border, no blur, part of the page. Once content scrolls beneath it
  (>8px), the hairline `line` border and `paper/90` blur fade in over 300ms —
  the iOS large-title cue that chrome now floats over content.
- **End Cap:** The Today page closes with hairline rules flanking a serif
  italic "That's the brief" and the generated timestamp — the explicit,
  finite bottom the product promises.

## 6. Do's and Don'ts

### Do:
- **Do** keep Burnt Sienna (#b4540a) to ≤10% of any screen, only on actionable
  or genuinely-new elements — the One Signal Rule.
- **Do** convey depth with the white-surface-on-paper tonal step plus a 1px
  `line` border. Flat is the house style.
- **Do** make taps feel physical: full-row tap targets with a `paper` press
  highlight inside group lists, `:active` scale ~0.985 on standalone pills,
  sliding indicators on segmented controls, color transitions ≤200ms ease-out.
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
