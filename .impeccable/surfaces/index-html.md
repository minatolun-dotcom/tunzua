---
version: 1
slug: "index-html"
primary_target: "index.html"
related_targets: ["blog.html","privacy.html","terms.html","404.html"]
---

## Scope

Whole-site redesign (Persuade: home; Read: blog + post pages; legal pages; 404). Static GitHub Pages site, plain HTML/CSS/JS, no build step. Blog pipeline markup contract (post-card, blog-list marker, subscribe-box, legal-title classes) is binding.

## Direction contract

THESIS: An accounting firm whose pages are set like its own working papers — hard rules, tabular truth, one navy — refusing the soft cream-serif CA template and the fintech-glow cliché alike.

OWN-WORLD: White ground, ink #0A0A0A, brand navy #001743 as the only accent (sampled from the logo), hard 1.5–2px rules, ledger tables with tabular IBM Plex Mono numerals, Inter 400–900 for voice, mono only for data/labels/dates. Navy owns whole bands (ticker, CTA, footer); borders do the structure; shadows almost never.

STORY: Visitor sees a compliance calendar running on time, a poster-scale promise (Books. Balanced. Every time.), a services ledger priced honestly, real client reviews and names — then calls, WhatsApps, or sends the form.

FIRST VIEWPORT: Full-bleed white; nav (logo left, links center, navy CTA right) over navy compliance ticker; hero grid: 84px black headline "Books. Balanced. Every time." left with body copy and Get Started (navy) + Explore Services (outline) beneath; giant navy "17 / years of clean books · since 2008" right-aligned against a 2px rule. Primary action: Get Started → #contact.

FORM: User-pinned whole (quoting the user's choice): "combination of V3 hero section with V4, but brand color is blue you can find it from the brand logo" — V3 = Zurich Red poster hero, V4 = Data Desk (ticker, services ledger table, mono stat row), recolored to logo navy. seed: none (pinned).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

## Constraints

- WCAG AA contrast everywhere (user-flagged button text); visible focus; reduced-motion support.
- Content visible by default — no scroll-hidden reveals (fixed defect from incumbent).
- Preserve: theme toggle, formsubmit AJAX form (IDs), FAQ answers, real reviews, client logos, all SEO head/JSON-LD, analytics.
- Responsive verified at 390px and 1280px minimum.

## Unresolved

- Stats (100+ clients, 99% satisfaction) come from the incumbent's own copy — treated as supplied truth; user should confirm before launch.
