# Product

## Register

product

## Users

A single reader — the owner — checking the brief on a phone first thing each
morning, usually one-handed, often in bright daylight, with maybe 60 seconds of
attention before the day starts. The job: catch up on what moved overnight in
AI, business, startups, open source, and research without wading through feeds,
ads, or noise. It is public and occasionally shareable, but every design
decision optimizes for this one reader's fast daily scan, not for a broad
audience.

## Product Purpose

Morning Brief turns a nightly automated fetch (X threads & bookmarks, GitHub
Trending, a custom star-acceleration trending algorithm, Hugging Face papers)
into a single, opinionated daily read. An agent writes the day's JSON; the app
renders it. Success is the reader opening it once each morning, scanning the
headline + executive summary, dipping into the X / Code / Papers tabs as
interest pulls them, and closing it feeling caught up — not the reader leaving
to hunt elsewhere. The content is the product; the app's job is to make it feel
effortless and native to glance through.

## Brand Personality

Sharp, confident, editorial. Three words: **decisive, considered, quiet-fast.**
The voice has a point of view — it ranks, frames, and names what matters rather
than presenting a neutral firehose. The feel is a well-set morning paper crossed
with a native iOS app: editorial typographic hierarchy (Newsreader serif
headlines, Inter body) carried by genuine mobile-app craft — a real tab bar,
fluid transitions, momentum, and motion that feels physical rather than
decorative. Reference touchstones: **Every.to** and **Digg's tech section** for
curated-with-voice editorial framing; native iOS for the interaction model,
animation quality, and the sense that it belongs on a phone.

## Anti-references

- **Generic SaaS dashboard** — card grids, gradient hero-metric blocks, the
  purple-blue startup palette, icon + heading + text repeated endlessly.
- **Cluttered news portal** — ad-dense, thumbnail-heavy, infinite-scroll content
  farm (CNN/Yahoo-style noise). The brief is finite and curated; never make it
  feel bottomless.
- **Social feed** — engagement-bait, like-count chrome everywhere, algorithmic
  doomscroll framing. Metrics serve ranking, not vanity.
- **Crypto / AI-hype aesthetic** — neon glows, dark-mode-by-default,
  glassmorphism, "the future is here" bombast.

## Design Principles

- **Native app, not a web page.** The reader should feel they're in an iOS app:
  a tab bar that owns navigation, transitions with real momentum and direction,
  safe-area awareness, tap feedback. Web-page scroll-jank or instant hard cuts
  break the spell.
- **Editorial voice over neutral display.** The brief has opinions — ranking,
  framing, "new today" signals. Typography and hierarchy should read like a
  considered publication, not a data dump.
- **Finite and calm.** This is a complete morning read, not a feed. Lean into a
  clear top, a clear bottom, and the confidence that the reader saw what
  mattered. No infinite scroll, no fear-of-missing-out chrome.
- **Earn every element.** One signal accent (the burnt orange), restrained
  surface, no ornament that doesn't aid the scan. Motion and color are spent on
  what helps the reader decide what to read next.
- **Sunlight-legible.** Read on a phone in morning light: contrast and tap
  targets must hold up outdoors, not just in a design tool.

## Accessibility & Inclusion

WCAG AA targets: body text ≥4.5:1, large/UI text ≥3:1 against its background —
verified against the warm paper, not assumed. Every animation needs a
`prefers-reduced-motion: reduce` alternative (crossfade or instant). Comfortable
mobile tap targets (≥44px effective). Sensible defaults overall; no specialized
assistive requirements declared, but contrast is held a touch above the minimum
given the bright-light reading context.
