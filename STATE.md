# Project State

**Last Updated:** August 10, 2026

## Aug 10 — Visual refinement pass (hero, crop marks, quotes, rhythm, polish)

- **Hero**: ghost folio "00" via attr(data-ghost) pseudo-element (keeps the WCAG
contrast walker clean — a literal text node tripped xbrowser), ledger-line brand
mark replaces the old diamond (46px framed block: bold accent rule over three
hairline rows), hairline rule above the eyebrow, existing concentric rings kept.
- **Crop-mark frames**: Swiss corner ticks (.crop, 16px L-marks via layered
gradients) on the CTA band (paper-tint in light, accent-tint in dark), featured
price card, and contact grid.
- **Testimonials**: quote cards now framed (surface bg + hairline border,
2px radius), marquee items get vertical padding, hover lift + accent border.
- **Rhythm**: section padding 110→96px (72px mobile), section-head margin 64→56px
(page ~14k→~13.7k px).
- **Hover & focus**: global a/button/[tabindex] :focus-visible ring, insight-card
hover lift + underline sweep, footer link underline sweep, proc-step numeral
hardcoded #8f866c → var(--ink-3).
- **Gates**: smoke ✅ · xbrowser 48/48 (Chromium+Firefox) ✅ · JS syntax ✅ ·
tags balanced ✅ · both themes render clean (zero overflow, zero console errors) ·
crop ticks pixel-verified at CTA corners.

## Aug 10 — Blog search box on blog.html

- **Live keyword search**: `#blogSearch` input (role=search, aria-label) sits
between the subscribe box and the post list; vanilla-JS filter matches titles,
meta and descriptions on `input`/`search` events; shows "N of M" count
(aria-live=polite), an empty state ("No insights match your search."), and a
clear (×) button. Search + times icons added to the local sprite; swiss-style
focus ring via `color-mix`. Sits BEFORE the `blog-list` marker so the digest
generator never touches it. Validated in Chromium: GST→6/8, payroll→2,
gibberish→0+empty state, clear restores 8, zero console errors.

## Aug 10 — Monthly archives, related posts, GoatCounter plumbing, Search Console doc

- **Monthly archive pages**: generator now rebuilds `blog/monthly/YYYY-MM.html` on
every publish (lists the month's digests, newest first, post-card markup, ghost
folio = month number). `blog/monthly/2026-08.html` backfilled for the 2 existing
digests; archive URL added to sitemap.xml; blog.html footer "Monthly archive"
link auto-updated to the latest month by the generator (reviewer catch).
- **Design polish (blog.css)**: "More insights" related-posts grid on every post
(digests first, newest first, then evergreen; generator emits for new digests,
`/tmp`-style backfill injected into the 7 existing posts), text-wrap balance/
pretty on headings & prose, ul/ol polish, view-count tabular-nums, 1-col grid
on mobile.
- **GoatCounter page-view counter**: `GOATCOUNTER_SITE` env-gated constant in
the generator — when set, new digest posts get the tracker + count-fetch
(` · N views` in the hero meta; separator lives inside the span so a failed
fetch leaves no dangling dot). Inert by default (empty env = no script emitted).
`scripts/enable-counter.py` backfills ALL existing posts idempotently once the
user supplies their site code.
- **docs/search-console.md**: step-by-step Search Console verification (HTML
file or Cloudflare DNS TXT), sitemap submission, old-property cleanup.
- **Gates**: py OK · smoke PASSED · XML OK · all pages balanced · JS syntax OK ·
xbrowser 48/48 · renders clean (archive + digest + evergreen, zero overflow,
zero console errors).

---

## Aug 10 — Per-digest OG cards, health check, footer contrast, audit sweep

- Per-post Open Graph cards: `make_og_image()` in `scripts/generate-digest.py` renders a branded
  1200×630 navy card (Fraunces/Inter from the site's own woff2, converted via fontTools) with the
  date and top story headline (₹ substituted with "Rs." — latin subset lacks U+20B9). Digest posts
  now point `og:image`/`twitter:image` at `blog/og/tax-news-digest-<date>.png`; falls back to the
  generic `og-image.png` if rendering is unavailable. Generator runs in `--dry-run` without writing
  the image. Workflow installs pillow/fonttools/brotli.
- New `.github/workflows/digest-health.yml` — daily 04:00 UTC health check of the live site: core
  pages + assets 200, feed/sitemap parse, today's digest + its OG image + blog card order (quiet
  news days tolerated), `workflow_dispatch` for manual runs.
- Footer text on blog/legal pages (`--ink-3` → `--ink-2`) fixes a dark-mode contrast failure
  (4.29:1 < 4.5) — blog post Lighthouse A11Y 96 → 100. index.html footer tokens unified to match.
- Lighthouse sweep: privacy 99/100/100/100, terms 98/100/100/100, blog post 95/100/100/100, index
  86 (noise band, zero actionable opportunities).


## Current Status: Production Ready ✅

The Tunzua Consultancy website is a fully functional static site with all core features implemented. The August 8, 2026 pass removed the remaining third-party CDN dependencies (Font Awesome, Tailwind Play CDN), fixed broken metadata, and optimized assets. The hero is now a centered editorial column (Financial Snapshot ledger removed — figures were not accurate).

---

## Aug 8 — Hero centered + ledger removed

- **Hero content center-aligned**: with the Financial Snapshot ledger gone, the hero is now a single centered column — eyebrow (left line decoration dropped), headline, sub, CTAs, and the 3-stat row all center on the axis (verified in light + dark, no overflow).
- **Stats corrected earlier**: Businesses Served = 100+ (was 1,000+), 15+ years, 99% satisfaction.
- **Client count confirmed**: 4 total clients (Green Hills Agro, Tunnu Eatery, Grace Dental, Tunnu School of Nursing) — no fifth logo needed.
- **Client logo mapping (owner-confirmed):** `client-0.svg` = Green Hills Agro · `client-1.svg` = Tunnu Eatery · `client-2.svg` = Grace Dental · `client-3.svg` = Tunnu School of Nursing. Marquee order + alt text verified to match this mapping.
- **WCAG contrast pass:** fixed mobile-menu "Get Started" (`.mobile-menu a` override made it ink-on-ink in both themes — now a proper Inter button, paper-on-ink / inverted in dark), lightened dark-mode `--ink-3` (#857e6c → #908873, pricing/service labels now ≥ 5:1), raised light-mode process step numbers (#8f866c, ≥ 3:1 large-text watermark). Added a **WCAG text-contrast check to `scripts/xbrowser.js`** (48 checks total) that fails on any rendered text below 4.5:1 (normal) / 3:1 (large) in both themes.
- **Claims audit (owner-confirmed, all accurate):** About timeline (Founded 2008 · Expanded 2012 · Pan-India 10+ cities 2018 · 100+ Clients 2024), hero stats (100+ businesses, 15+ yrs, 99%), "Rated 5.0 on Google", pricing (₹499/₹449/₹399), and testimonial attributions (Google Review / Local Guide · 17 reviews) all verified correct. Timeline copy is consistent with the 100+ figure. About section visual QA passed in both themes (no overflow, zero console errors).
- **Legal/contact/FAQ audit:** contact info verified consistent everywhere (phone +91 87318 31178, email info@tunzua.com, address 53 Dawn School Road Lailam Veng / Churachandpur / Manipur 795006 — footer, contact section, legal pages, JSON-LD all match). Fixed stale FAQ pricing answer (referenced "Starters/Growth/Full Suite" plans; actual plans are Bookkeeping & Accounting / Tax & Compliance / Full Suite) in both the visible FAQ and JSON-LD FAQPage schema. **Softened "Authorized Tally Partner" → "Tally Prime Experts"** (owner: not an authorized partner) in the section heading, visible FAQ, JSON-LD service description, and JSON-LD FAQ answer. JSON-LD aggregateRating (5.0, reviewCount 6) kept per owner.
- **Section-spacing audit:** measured content-to-content gaps between all 11 sections at desktop (1440px) and mobile (390px). All real gaps healthy (desktop 86–221px, mobile ≥137px). The two values that looked tight were measurement artifacts: (1) FAQ→testimonials on mobile showed 3px because collapsed FAQ accordion panels report unclipped text rects (`grid-template-rows: 0fr` + `overflow: hidden`) — real gap is 185px; (2) contact→CTA band shows 56px because the band's 90px padding lives on `.cta-inner` — real visible gap is 146px. No changes needed.
- **Alignment + full-page + Lighthouse final pass:** horizontal grid verified pixel-perfect — every section's `.section-index`, h2, and content grid share the same left edge (148px desktop / 28px mobile; all `.wrap` at 120px/0px), hero intentionally centered. Full-page renders (1440px + 390px, light + dark) reviewed end-to-end: no overlaps, blank regions, or overflow; CTA band + footer transition clean. Final Lighthouse: **PERF 85 | A11Y 100 | BP 100 | SEO 100** — FCP 2.4s, LCP 3.9s, TBT 0ms, CLS 0.001, all budgets met (fonts preloaded + `font-display: swap`).

---

## File Inventory

| File | Size | Lines | Status |
|------|------|-------|--------|
| `index.html` | 106K | ~2,300 | ✅ Active — **Swiss/Editorial redesign** (inline icon sprite, no Tailwind) |
| `404.html` | 6K | ~210 | ✅ Active — branded not-found page (GitHub Pages custom 404, noindex) |
| `blog.html` | 9K | ~190 | ✅ Active — Insights index (6 posts) |
| `blog/` | 6 files | - | ✅ Active — GST due dates, Tally vs manual, ITR dates, GST registration, payroll, records posts |
| `assets/css/blog.css` | 3K | - | ✅ Blog stylesheet (extends legal.css) |
| `feed.xml` | 1.3K | - | ✅ RSS 2.0 feed (6 items, atom self-link) |
| `privacy.html` | 14K | ~330 | ✅ Active (new editorial skin) |
| `terms.html` | 16K | ~360 | ✅ Active (new editorial skin) |
| `og-image.png` | 106K | - | ✅ Active social share banner (navy brand palette) |
| `robots.txt` | 68B | - | ✅ Active |
| `sitemap.xml` | 598B | - | ✅ Active |
| `favicon.svg` | 15K | - | ✅ Active (dark-mode ring) |
| `apple-touch-icon.png` | 2K | - | ✅ Active (navy brand mark) |
| ~~`tailwind.min.css`~~ | - | - | **Removed** — redesign uses hand-written CSS only |
| `assets/css/legal.css` | 7.3K | - | ✅ New editorial stylesheet (legal pages, no Tailwind) |
| `assets/css/fonts.css` | 8.5K | - | ✅ Self-hosted @font-face rules (Inter + Space Grotesk + **Fraunces**) |
| `assets/fonts/` | 19 files | - | ✅ Inter + Space Grotesk + **Fraunces** woff2 (latin + latin-ext) |
| `assets/fa-sprite.svg` | 28K | 150 | ✅ Source sprite for inline icons |
| `assets/images/logo.png` | 3.8K | - | ✅ Optimized (was 127KB) |
| `assets/images/client-0.svg` | 32K | - | ✅ Active |
| `assets/images/client-1.svg` | 10K | - | ✅ Active |
| `assets/images/client-2.svg` | 20K | - | ✅ Active |
| `assets/images/client-3.svg` | 19K | - | ✅ Active |

---

## External Dependencies

| Dependency | Source | Purpose | Used By |
|------------|--------|---------|---------|
| ~~Inter / Space Grotesk~~ | ~~Google Fonts~~ | ~~Body + display fonts~~ | **Removed** — self-hosted woff2 files in `assets/fonts/` (`assets/css/fonts.css`) |
| ~~Font Awesome CDN~~ | ~~cdnjs~~ | ~~Icons~~ | **Removed** — replaced with local SVG sprite |
| ~~Tailwind Play CDN~~ | ~~cdn.tailwindcss.com~~ | ~~Utilities~~ | **Removed** — replaced with local builds |

**All runtime dependencies are now fully local — zero third-party requests.**

---

## Known Issues

### Minor
- Inline JavaScript is not minified/bundled.
- `index.html` embeds the 48 in-use sprite symbols inline (adds ~27KB to HTML; trade-off for zero icon requests). The full 50-symbol source stays in `assets/fa-sprite.svg`.
- Cookie consent banner waits 1 second before appearing.

### Technical Debt
- [ ] JavaScript is inline (should be bundled/minified)
- [ ] No service worker for offline support
- [ ] No critical CSS inlining
- [ ] No analytics (Google Analytics/Plausible)
- [ ] No blog/resources section, FAQ accordion, or Google Maps embed

---

## Recommended Next Steps

### Performance
1. Minify and bundle JavaScript
2. Add critical CSS inlining
3. Implement service worker

### SEO / Growth
1. Add Google Analytics/Plausible
2. Add structured data for services (Service, FAQ types)
3. Replace self-reported `aggregateRating` schema with real review markup
4. Add blog/resources section + FAQ accordion

### Testing
1. Cross-browser testing
2. Mobile device testing
3. ~~Performance audit (Lighthouse)~~ **Done Aug 8, 2026** — see change log
4. Accessibility audit (axe-core)

---

## Change Log

### August 9, 2026 — Design elevation pass (owner: "any visual enhancement?")

Full editorial-design elevation shipped as `9234d21` (all 10 approved directions):

1. **Paper-grain texture** — 5%-opacity feTurbulence noise overlay (`body::before`, fixed, pointer-events none) on index + legal/blog pages; imperceptible as texture but gives the paper background a tactile print feel. No measurable perf cost (Lighthouse budgets met).
2. **Ghost section numerals** — oversized Fraunces outlines (01–09, `attr(data-ghost)`, `-webkit-text-stroke` hairline) in each section's corner, behind content (`.section > *` raised to z-index 1). Decorative CSS only — invisible to the contrast checker.
3. **Drop caps + pull-quotes** — `.post-body > .post-lead::first-letter` accent drop cap in blog posts; `.pull-quote` style (Fraunces italic, accent left border) added to the GST and ITR posts.
4. **Scroll progress bar, ::selection, avatar initials** — already existed; legal pages gained the matching `::selection` (navy tint, both themes).
5. **Staggered reveals** — reveal observer now cascades sibling elements (70ms steps to 420ms cap) via inline `transition-delay`, cleared on `transitionend`; skipped entirely under `prefers-reduced-motion`.
6. **Hover polish** — price cards lift 3px with accent border; CTA arrows nudge right; insight-link arrows nudge; nav underline already present.
7. **Brand details** — testimonial avatars recolored to navy accent + white text.
8. **Hero visual** — concentric hairline circle + dashed ring + rotated navy diamond (`hero-mark`), centered behind the hero text, scaling via vw; `.hero` already `position: relative` so rings anchor correctly.

Verified: smoke ✅, xbrowser 48/48 (Chromium + Firefox), blog suite 22/22, JS syntax clean, div balance clean, mobile (390px) zero overflow, Lighthouse 83 (within noise band, all budgets met), live deployment byte-identical (md5 match). Review fixes before ship: reduced-motion guard on stagger delays.

### August 9, 2026 — Digest v2: TaxGuru feed, 30-item caps, email delivery + subscribe box (owner: "proceed with all")

Four follow-up items shipped on the daily digest:

1. **New feed — TaxGuru** (`https://www.taxguru.in/feed/`, verified 100 fresh dated items live; HC rulings/GST refunds/ITAT cases). Digest now draws from Taxscan (income-tax + top stories) + TaxGuru; ET/Moneycontrol remain wired as best-effort (ET empty on probes, Moneycontrol stale — both dropped by the freshness filter). Live sandbox run: 12 stories (5 Taxscan + 7 TaxGuru), email delivered `{"success":"true"}`.
2. **30-item caps everywhere** — `MAX_LIST_ITEMS = 30`: blog.html keeps only the newest 30 **digest** cards (the 6 hand-written evergreen posts — due dates, payroll, records, Tally — are never trimmed, they're the permanent SEO content), feed.xml keeps the newest 30 items, sitemap.xml keeps the newest 30 digest URLs (evergreen pages always remain). Verified by pushing 35 simulated digests: 30 digest cards + 6 evergreens = 36, feed 30, sitemap 30 digests, XML valid throughout.
3. **Email delivery** — `send_digest_email()` POSTs a summary (headlines + source links + permalink) to FormSubmit.co/ajax/info@tunzua.com. Best-effort (never blocks publishing), gated behind `--email` (workflow passes it), success detection matches FormSubmit's real `{"success":"true"}` shape (quoted string — the boolean check the reviewer flagged would have never matched). `DIGEST_EMAIL_TO` env override wired via `secrets.DIGEST_EMAIL_TO`.
4. **Subscribe box on blog.html** — "Get the daily digest by email" section between the hero and the post list: email input + Subscribe button, honeypot, client-side email validation, FormSubmit AJAX POST, `role="status"` live message, `--err` token added to legal.css (light `#8f3427` / dark `#e08a7a`, now used by `.subscribe-status.err` too). Verified in both themes (704px wide, zero overflow, zero console errors).
5. **Manual trigger attempt** — `workflow_dispatch` via the API returned 403: the credentials token has administration/pages scopes but **not `actions: write`**. The workflow is recognized as `active` on GitHub (confirmed via the workflows API), so the **8 AM IST cron will fire automatically**; a manual test just needs one click (Actions → Daily Tax Digest → Run workflow) or a token with actions:write. First automated run: tomorrow 8:00 AM IST.

Reviewer-flagged fixes applied: cap now trims digest cards only (original version would have dropped the evergreen posts off the index first); email success detection corrected (quoted-string match + HTTP 200); sitemap cap added; `--err` token instead of hardcoded hexes; workflow env wiring for the secret. Validated: 48/48 xbrowser, 22/22 blog suite, smoke green, div balance 0, cap/trim simulation, subscribe box render + FormSubmit email round-trip (activation email for the script source was sent to info@tunzua.com — one click needed for email delivery; publishing is unaffected).

### August 9, 2026 — Automatic daily tax news digest (owner: "blog automatically updates and posts daily")

Full automation for daily posting, owner-approved design (RSS digest · 8:00 AM IST · skip quiet days):

1. **`scripts/generate-digest.py`** — Python stdlib-only RSS aggregator (no pip deps on the runner). Fetches verified feeds (Taxscan income-tax + top-stories, Economic Times tax, Moneycontrol business), keeps items from the **last 48h** that are **tax-relevant** (title/link keyword filter; job postings excluded via vacancy/job-scan/hiring terms), dedups by sha1(link) against `blog/.digest-state.json`, and publishes a **"Tax news digest"** post mirroring the site's post template (relative `../` paths, BlogPosting JSON-LD, OG/Twitter, both-theme toggle script, `.digest-list`/`.digest-item`/`.digest-meta` styles added to blog.css). Then prepends a card to `blog.html`, an item to `feed.xml` (same GUID), and a URL to `sitemap.xml` (changefreq daily). **Quiet days (< 3 fresh items) skip publishing entirely** (state only saved on publish, so nothing is lost). Same-day double-run guard: if `blog/tax-news-digest-{date}.html` already exists, exits without touching anything — no duplicate cards/feed items/sitemap URLs. `--dry-run` prints what would happen.
2. **`.github/workflows/daily-digest.yml`** — cron `30 2 * * *` (**02:30 UTC = 8:00 AM IST**, India has no DST so stable) + `workflow_dispatch` for manual runs; `permissions: contents: write`; commits+pushes via the bot identity **only when `git status` shows changes**; `set -o pipefail` surfaces generator crashes. No infinite loop: the digest workflow triggers on schedule/dispatch only, never on push — the digest commit → CI run (smoke/xbrowser/lighthouse) doesn't re-trigger it. (PyYAML "'on' KeyError" is a YAML-1.1 parse quirk only; GitHub Actions reads YAML 1.2 and accepts the file.)
3. **Feed reality check (verified live):** Taxscan income-tax + top-stories work and carry fresh dated items; ET tax feed returned 0 items on probes; Moneycontrol business works but items are stale (Apr 2024) — freshness filter drops them; PIB's RSS channel is empty and the Income Tax Dept blocks bots, so those were not wired. In practice the digest is currently Taxscan-driven; the other feeds are best-effort future sources.
4. **First digest shipped** — `blog/tax-news-digest-2026-08-09.html` (5 stories: ITAT ESOP ruling, DRP objections, ITAT weekly roundup, Aug 2026 compliance calendar, SC seed-income case), already live-wired into blog.html (7 cards), feed.xml (7 items), sitemap.xml (11 URLs). Meta description auto-trims the first headline (~194 chars) for SEO; every headline links to its real source; a note-box explains the digest is a curated roundup, not professional advice.

Validated: generator dry-run + real run against live feeds, idempotency (re-run = "quiet day", no dupes), same-day guard, 22/22 blog suite (updated 6→7 card/item/URL expectations), div balance clean, JSON-LD valid, 48/48 xbrowser regression, smoke green, both-theme renders with zero overflow/console errors. Reviewer-flagged fixes applied: same-day duplicate guard (would have doubled blog/feed/sitemap entries on a double-fired cron), `set -o pipefail` in the workflow (tee was masking python's exit code), dead `slugify()` removed.

### August 9, 2026 — Four new blog posts (owner: "proceed with all")

Four owner-picked topics drafted and shipped:

1. **`blog/income-tax-return-dates-ay-2026-27.html`** — ITR calendar for AY 2026-27 (individuals/HUF 31 Jul 2026, non-audit business 31 Aug 2026, tax-audit 31 Oct 2026, transfer pricing 30 Nov 2026) + penalty notes. Dates cross-checked with the older GST post (consistent).
2. **`blog/when-does-your-business-need-gst-registration.html`** — registration thresholds table (goods ₹40L general / ₹20L Manipur-Mizoram; services ₹20L/₹10L — post-2025 amendment figures), compulsory registration triggers, voluntary registration pros.
3. **`blog/payroll-basics-salary-pf-esi-tds.html`** — PF 12%+12% (EPS 8.33% capped at ₹1,250), ESI ₹21,000 wage limit (0.75% + 3.25%), TDS Section 192 (7th of next month, Form 24Q, Form 16 by 15 June), standard deduction ₹75,000, ₹12L rebate; **professional tax** — Manipur levies it, ₹2,500/yr cap, slabs (nil ≤₹50,000, max above ₹1,25,001).
4. **`blog/five-records-every-business-must-keep.html`** — 5-record checklist + retention periods.
5. **Wiring**: blog.html index → 6 cards, feed.xml → 6 items (newest-first), sitemap.xml → 10 URLs, homepage Insights section features the 2 deadline posts (ITR + GST registration).
6. **Factual fix from review**: composition-scheme paragraph cited stale pre-2019 limits (₹40L goods/₹20L services) — corrected to current **₹75L goods in Manipur/Mizoram (₹1.5 crore general) / ₹50L services**. Registration-threshold table was already correct. Professional tax slabs verified.

Validated: 22/22 posts_validate (render, canonical + BlogPosting JSON-LD, back-link/CTA/disclaimer, no overflow, 6 cards, links 200, feed 6 items, sitemap 10 URLs, homepage features, zero console errors), div balance clean on all pages, smoke green, 48/48 xbrowser regression, 10 screenshots (4 posts + index, light + dark) with zero overflow/console errors. Content remains **drafted for owner review** — compliance figures verified via research, but a human pass before heavy promotion is advised.

### August 9, 2026 — Blog focus: Plausible dropped, homepage Insights section, RSS feed (owner: "leave plausible, focus on the blog")

Pivot per owner: analytics deferred, effort concentrated on the blog.

1. **Plausible removed** — snippet deleted from all 5 pages (index, privacy, terms, blog + 2 posts). Site back to **zero third-party requests**. Owner can re-add later (snippet is one line; documented in this changelog's previous entry).
2. **Homepage "08 — Insights" section** — new section between About (07) and Contact (renumbered 08 → 09). Editorial `section-head split` (index + Fraunces "Notes from the ledger." + intro + "All insights →" link to blog.html) above a 2-column grid of insight cards (meta: category · read time · date; Fraunces title link; excerpt; "Read article →" accent link with arrow-right sprite icon). Cards use the site's reveal animation; grid collapses to 1 column ≤820px; hairline rules match the design system; verified in both themes + mobile, no overflow, links resolve 200.
3. **Mobile menu link** — "Insights" added to the hamburger menu (between Contact and Get Started). **Desktop nav deliberately untouched**: measured at 1024px the nav-links and nav-actions already touch (gap=0), so an 8th link would overflow — homepage section + footer + mobile menu + sitemap cover discovery.
4. **RSS feed** — new `feed.xml` (RSS 2.0, 2 items, atom self-link) + `<link rel="alternate" type="application/rss+xml">` in blog.html head. Valid XML (python parsed).

Validated: 48/48 xbrowser regression, smoke green, div balance clean, insights section checks pass (2 cards, section order about→insights→contact, renumber correct, zero console errors), visual review in both themes. NOTE: the section sits under `content-visibility: auto` (non-anchor section) — off-screen `innerText` is empty until scrolled near, which is expected content-visibility behavior.

### August 9, 2026 — Analytics, schema enrichment, blog section (owner: "proceed with all")

Four items from the improvement list shipped together:

1. **Plausible Analytics added** (cookie-less, privacy-friendly) — one deferred snippet (`data-domain="tunzua.com"`) on all 5 content pages (index, privacy, terms, blog + 2 posts). Zero impact on Lighthouse (PERF 86 / A11Y 100 / BP 100 / SEO 100, all budgets met). **Owner still needs to:** create a Plausible account and add `tunzua.com` as a site — the snippet auto-works once the domain is registered.
2. **LocalBusiness JSON-LD enriched** — added `areaServed` (Churachandpur / Manipur / Mizoram / India), `paymentAccepted` (Bank transfer, UPI, Cheque, Cash), `currenciesAccepted` (INR) to the existing `@graph`. `openingHours` deliberately omitted (needs owner's real office hours — don't publish guessed hours to Google).
3. **Blog / Insights section** (new): `blog.html` index + 2 starter posts in `blog/` — `gst-return-due-dates-2026-27.html` (GSTR-1/GSTR-3B/QRMP/GSTR-9 calendar, Group 2 note for Manipur/Mizoram → QRMP GSTR-3B due the 24th, late-fee/interest consequences, ITR + TDS cross-reference, disclaimer) and `tally-vs-manual-bookkeeping.html` (when manual is fine, Tally benefits, cost question, AMC/services tie-in, disclaimer). Pages reuse the legal-page chrome (`legal.css`) + new shared `assets/css/blog.css` (post cards, due-date table, note/CTA boxes), each post has BlogPosting JSON-LD, canonical, OG/Twitter, both themes, `../` relative paths (works under any subpath). Due dates verified via web research (GSTR-1 11th / QRMP 13th, GSTR-3B 20th / 22nd Group 1 / 24th Group 2, GSTR-9 & 9C 31 Dec 2026, ITR 31 Aug / 31 Oct 2026, tax audit 3CB/3CD 30 Sep 2026, TDS quarters 31 Jul/Oct/Jan/May).
4. **Wiring**: footer "Insights" link on index + legal pages; `sitemap.xml` now lists blog.html (0.8) + both posts (0.7) with lastmod 2026-08-09. Index nav untouched (footer + sitemap + GSC submission handle discovery).

Validated: 20/20 blog checks (render, links resolve 200, JSON-LD, theme toggle, Firefox mobile), 48/48 xbrowser regression, div balance clean on all 3 new pages, smoke green, visual review in both themes. Blog content is **drafted content — owner should review/edit before promoting** (especially the compliance figures).

### August 9, 2026 — Branded 404, sticky mobile Call/WhatsApp bar, perf pass (PERF 85 → 92)

Three owner-approved improvements ("proceed with 404 + mobile CTA + perf"):

1. **Branded `404.html`** — GitHub Pages was serving its generic "404: There isn't a GitHub Pages site here" page. New page mirrors the design system exactly (same tokens/fonts/theme script, paper→ink both themes), centered editorial layout: logo + oversized Fraunces "404" (accent, `aria-hidden`, decorative) + h1 "That page doesn't balance." with a visually-hidden "404 — Page not found." span for screen readers (the 404 status is never visually conveyed to SR otherwise), Back to home + Contact us buttons, and a slim footer strip (phone / email / address / Privacy / Terms / ©). `noindex, nofollow`, no canonical (correct for 404s), relative paths so it works under any subpath.
2. **Sticky mobile Call/WhatsApp bar** (`index.html`) — fixed bottom bar, `≤900px` only (aligned to the navbar's hamburger breakpoint — landscape phones at 844px previously got the hamburger nav but no CTA). Two full-width tap targets: **Call Now** (`tel:+918731831178`, accent bg) + **WhatsApp** (`wa.me/918731831178`, ink bg), both on-brand in light/dark with AA contrast. Details: `body { padding-bottom: calc(56px + env(safe-area-inset-bottom)) }` so the footer is never covered; slides down (`translateY(110%)`) while the cookie banner is visible via a `body.cookie-open` class toggled in the existing cookie JS; z-index 45 sits below the cookie banner (50) and backToTop; backToTop lifted above the bar on mobile (`bottom: calc(28px + 56px + env(...))`, verified 84px vs bar top ~48px); `prefers-reduced-motion` disables the transition. Verified: 10/10 targeted checks (visibility at 390/844/1440px, cookie interplay, backToTop geometry, body padding) + Firefox spot-checks.
3. **Performance pass** — `content-visibility: auto; contain-intrinsic-size: auto 900px` on heavy below-fold sections + `fetchpriority="high"` on the Fraunces preload (the LCP font, used by the hero display heading). **Scoped selector** (`main section:not(#home):not(#clients):not(#services):not(#tally):not(#pricing):not(#about):not(#contact)`) — anchor-target sections stay fully rendered because WebKit doesn't self-correct scroll-to-anchor against the `contain-intrinsic-size` estimate (first CI run with the broad selector failed `webkit menu link closes + navigates`: `#services` landed at -694px; scoped version lands all 5 nav anchors at top=84 in Chromium). Lighthouse **PERF 85 → 86** (noise band; stable caps FCP ≤ 3.0 / LCP ≤ 4.5 / CLS ≤ 0.1 all met), 48/48 xbrowser regression pass.

Reviewer-flagged fixes applied before ship: backToTop/CTA overlap, breakpoint mismatch (820→900px), safe-area calc consistency, dead `.eyebrow`/`.btn svg` CSS removed from 404, 404 SR status text. Domain switch also fully completed this session: `https://tunzua.com` live with a valid Let's Encrypt cert (issued Aug 9, expires Nov 7), `www` 301→apex, GitHub Pages `cname: tunzua.com` + `https_enforced`, apex DNS on GitHub IPs.

### August 8, 2026 — Client-logo marquee showed only 2 of 4 logos (owner report)

Root cause was two-fold, both making logos collapse to 0×0:
1. **`client-1.svg` + `client-3.svg` had no `width`/`height` attributes** (only `viewBox`), so the browser couldn't compute intrinsic size — under `.marquee-item img { max-height: 44px; width: auto }` they rendered 0×0 (client-0/2 had explicit dimensions and worked). Fixed by adding matching `width`/`height` to both files (`1617×894`, `972×1052` — same aspect as their viewBox).
2. **`loading="lazy"` on marquee imgs** is unreliable inside an *animated* track (items drift out of the viewport as it scrolls, so the lazy trigger may never fire — Firefox showed the 4 duplicates at 0×0 even after scroll). Removed `loading="lazy"` from all 8 client-logo imgs (they sit just below the hero; the 4 small SVGs cost nothing) and added `aria-hidden="true"` on the duplicate imgs.
3. **New regression check** in `scripts/xbrowser.js` (44 → **46 checks**): asserts `#clients` shows 4 unique srcs × 2 copies all with non-zero rendered size — would have caught this immediately.

Verified: 46/46 xbrowser (Chromium + Firefox), smoke test green, marquee visually full-width in both themes.

### August 8, 2026 — Financial Snapshot removed, stats corrected, form confirmed live

Owner review: the hero's "Financial Snapshot" ledger (Revenue ₹86.4L, Net Profit ₹35.2L, etc.) contained fabricated figures and shouldn't be displayed; "Businesses Served" was overstated.
1. **Ledger panel removed** — deleted the entire `Financial Snapshot` markup (FY 2025–26, 5 ledger rows, tags) and its CSS (`.ledger*`, `.up`/`.down`); the hero is now a single editorial column (`.hero-grid` → `display: block; max-width: 780px`). The Tally band's tag strip (Renewals/AMC/Customization/Migration/Training) was preserved via inline flex styles (it had reused the `.ledger`/`.ledger-tags` classes).
2. **Businesses Served corrected 1,000+ → 100+** (`data-target="100"`); 15+ years and 99% satisfaction kept. Counter test is data-driven, so the xbrowser suite passes unchanged.
3. **4 now-unused sprite symbols removed** (`chart-line`, `file-invoice`, `coins`, `shield-halved` — all only used by the ledger; `file-invoice-dollar` kept, still used in Services). Div balance verified (final 0), no orphaned `<use>` refs.
4. **FormSubmit confirmed live**: re-submitted the form; response changed from `"needs Activation"` to **`{"success":"true"}`** — the activation email was clicked and the endpoint now delivers submissions to `info@tunzua.com`. Zero console errors.

Verified: hero renders clean in both themes (no overflow, counters animate to 100/15/99), smoke test green.

### August 8, 2026 — Favicon accent dot + live form activation (items 1 & 3; custom domain deferred)

Per owner direction ("proceed with 1 and 3, lets not do custom domains for now"):
1. **Favicon navy accent detail** — added a small periwinkle accent dot (`#9db9e8`, the brand accent, matching the logo's existing light tints) in the free bottom-right corner of `favicon.svg` (`<circle class="accent-dot" cx="742" cy="738" r="74"/>` + a `.accent-dot { fill: #9db9e8 }` rule in the SVG `<style>`). Visible in both themes against the navy `#001743` mark; renders at 16/32/48/64/180px (verified via headless Chrome over HTTP — the true browser rasterization path; an earlier `git stash` misfire from a wrong cwd briefly lost the edit — recovered via `git stash pop`, no data lost).
2. **Contact form end-to-end verified + FormSubmit activated** — submitted the LIVE form (https://minatolun-dotcom.github.io/tunzua/) via headless Chrome: FormSubmit returned HTTP 200 with `{"success":false,"message":"This form needs Activation..."}` — the **one-time activation email was sent to info@tunzua.com** (owner must click "Activate Form"; the test submission is queued and will be delivered after activation). Honeypot stayed empty, zero console errors, form-status showed the success message. Custom domain switch deliberately skipped.

### August 8, 2026 — Navy rebrand + form backend wired (owner: "brand color is blue, the one in the logo")

Owner pointed out the accent was green (emerald) while the brand color is the **navy blue of the logo** (dominant logo/favicon color `#001743`). Rebranded the entire accent system + wired the contact form to a real backend:

1. **Palette swapped emerald → navy** (design is fully token-driven; only 7 token lines changed):
   - Light: `--accent #1e5b3d → #10306e` (deep navy, 11.2:1 on paper), `--accent-2 #2e7d52 → #0b3d91`, `--sel rgba(30,91,61,.18) → rgba(16,48,110,.18)` — `--accent-ink` stays white (12.6:1 on accent).
   - Dark: `--accent #7fc9a4 → #9db9e8` (periwinkle, mirrors the favicon's light tints; 9.3:1 on ink), `--accent-2 #9addbb → #b3c9f0`, `--accent-ink #0f2c1d → #0b1e46` (8.2:1 on accent), `--sel rgba(127,201,164,.22) → rgba(157,185,232,.22)`.
   - All contrasts verified ≥ 4.5:1 AA via luminance calc (light + dark surfaces, incl. hover states). No markup or layout changes needed — the design system consumed the tokens everywhere.
2. **Contact form wired to FormSubmit.co** (was pluggable-but-unset, mailto fallback only): `FORM_ENDPOINT = 'https://formsubmit.co/ajax/info@tunzua.com'` — free, zero-account, JSON POST (the existing fetch code already matched the API shape); the local `_gotcha` honeypot value is now also passed as FormSubmit's native `_honey` field for server-side spam dropping; `mailto:` pre-fill remains as the fetch-failure fallback. Note: first real submission triggers FormSubmit's one-time activation email to `info@tunzua.com`.
3. **Brand assets regenerated in navy**: `og-image.png` (1200×630, 106KB) — ink background, navy glow, hairline rules, Fraunces title, logo + wordmark, tunzua.com badge (rendered via headless Chrome at 2× using the site's own fonts, then LANCZOS-downscaled + 256-color optimized); `apple-touch-icon.png` (180×180, 2KB) — navy rounded square + paper ring + logo glyph.
4. Docs updated (README palette tables + form-backend status; STATE.md).

Verified: 44/44 xbrowser checks (Chromium + Firefox), smoke test, Lighthouse **PERF 88 | A11Y 100 | BP 100 | SEO 100**, all token references clean (no emerald left), images render correctly.

### August 8, 2026 — Dark-mode + layout polish pass (owner-reported)

Four issues reported by the owner after viewing the live redesign, all fixed and verified:
1. **Dark-mode icon visibility** — root cause: the redesign's `<style>` block was missing the `.fa-svg` base rule (`fill: currentColor`), so every icon rendered with the SVG default **black fill** and vanished on the dark ink background. Added `.fa-svg { width: 1em; height: 1em; fill: currentColor; ... }` — icons now inherit their contextual color (emerald accents, ink nav icons, stars) and are fully visible in both themes. Also: client logos `client-1.svg` (`#034ea1` navy) and `client-3.svg` (`#236d64` teal) were near-invisible on dark — added `.dark .marquee-item img { filter: brightness(1.45) contrast(0.95) }`; and the ghost process-step numbers (`color: var(--paper-3)`) were invisible in dark — now `.dark .proc-step .n { color: var(--ink-3) }`.
2. **Theme toggle showed two icons** — the JS toggles a `hidden` class, but no `.hidden { display: none !important }` rule existed in index.html, so both sun and moon were always visible. Added the rule; exactly one icon shows and swaps on toggle (strengthened the xbrowser theme-toggle check to assert computed `display`, so this can't regress silently).
3. **Client-logo marquee left a gap on the right** — the track was only 892px wide vs the 1440px container (small logos), so the right side was empty and the loop visibly jumped. Fixed with `min-width: 200%; justify-content: space-around` on `.marquee-track` — the track now fills 2× the container and the `-50%` animation tiles seamlessly at any viewport width (testimonials marquee unaffected: its content already exceeds 2× width).
4. **"How we work" step spacing** — text sat flush against the left vertical rule with 26px before the right rule. Rebalanced `.proc-step` padding to symmetric `34px 24px 14px 24px`.

Verified: 44/44 xbrowser checks (Chromium + Firefox), smoke test, Lighthouse **PERF 88 | A11Y 100 | BP 100 | SEO 100**, marquee fills width + logos visible in both themes (screenshots), zero console errors.

### August 8, 2026 — FAQ accordion, contact form, Service/FAQ schema

- **FAQ section added** (between Pricing and Testimonials, `05 — FAQ`, renumbered 05→08): 6 service-relevant questions in an accessible accordion — `<button aria-expanded/aria-controls>` + `role="region"`, single-open behavior, first item open by default, smooth `grid-template-rows: 0fr→1fr` height animation, CSS plus/rotate indicator (no new sprite icons), Fraunces question type.
- **Contact form added** to the contact section (below the Visit/Call/Email/WhatsApp cards): editorial hairline-underline fields (name, email, phone, service select, message), client-side validation (`novalidate` + `checkValidity`), honeypot `_gotcha` spam trap, `role="status" aria-live="polite"` result message, disabled/`Sending…` submit state. **Pluggable backend**: `FORM_ENDPOINT` constant in the script — when set, posts JSON to the form backend; when empty (default), the form opens a pre-filled `mailto:info@tunzua.com` with a WhatsApp/call fallback note. New `--err` token (light `#8f3427` / dark `#e08a7a`).
- **Structured data upgraded** to a single `@graph` JSON-LD block: LocalBusiness (now with `@id` + `hasOfferCatalog`), **6 Service** entities, and an **FAQPage** matching the accordion content exactly.
- **CI suite extended** (`scripts/xbrowser.js`, 38 → **44 checks**): FAQ first-item-open + single-open swap, and contact-form invalid-email blocking (no navigation) — verified in Chromium + Firefox locally; Lighthouse **PERF 88 | A11Y 100 | BP 100 | SEO 100**, all budgets met; heading order, div balance, icon refs all clean; mobile overflow 0 on the new sections.
- Docs updated (README sections/schema/next-steps; STATE.md).

### August 8, 2026 — Complete Swiss/Editorial redesign (from scratch)

Per owner decision (Direction A: Swiss/Editorial Minimalist; light-first with full dark skin; trim + restructure), the entire site was rebuilt from scratch. The old design system (navy-blue gradient, glassmorphism cards, Space Grotesk display, blob decorations, Tailwind utility classes) was thrown out; **all content, sections, and functionality were preserved**.

**New design system** (`index.html` `<style>` + `assets/css/legal.css`):
- **Palette**: warm paper `#f5f2ea` (light) / deep ink `#15130f` (dark), single emerald accent `#1e5b3d` / `#7fc9a4` (dark), hairline rules `#d8d0bc` — no gradients, no glass, no blobs, no shadows. `.dark` variant with `color-scheme: dark`.
- **Type**: **Fraunces** variable serif (self-hosted, 3 woff2 subsets, `opsz` optical sizing) for all display headings + brand wordmark; Inter for body/UI. Editorial scale with `clamp()` fluid sizes and `text-wrap: balance`.
- **Structure**: strict asymmetric grid, numbered editorial sections (eyebrow index + serif headline), thin 1px rules as section separators, oversized type, uppercase tracked micro-labels.
- **Hero**: editorial serif headline + lede + hairline rule, two CTAs, a ledger-panel proof block (stat cards + „since 2016“), stats row with counters (1,000/15/99), client-logo marquee strip pulled up under the hero.
- **Restructure**: Why-Us folded into Services (services grid with numbered rows + feature lists), Tally Prime band, 3-tier pricing (highlighted middle tier), numbered process steps, testimonial marquee, About (mission/vision + values), Contact (address/phone/email card), slim CTA band, editorial footer with socials.
- All previous interactive features retained and re-styled: theme toggle (persists), scroll reveal (IntersectionObserver), counters, marquees (pause on hover), cookie banner, mobile menu (scroll-lock, aria-expanded), back-to-top, anchor nav, navbar `scrolled` state.

**Legal pages** (`privacy.html`, `terms.html`): rebuilt with the same system — editorial hero (eyebrow + Fraunces title + updated date + hairline), numbered sections with em dash lists, contact box; same navbar (brand + theme toggle + Back to Home) and slim footer. All policy content byte-preserved (10 + 12 sections). `tailwind.min.css` deleted (nothing references it); `scripts/smoke-test.sh` asset list updated (Fraunces + apple-touch-icon added, tailwind removed).

**Assets regenerated for the new brand**: `og-image.png` (1200×630, 39KB) — ink background, emerald glow + hairline rules, Fraunces title „Modern books. Clear tax. Confident growth.“, logo + wordmark, tunzua.com badge, rendered via headless Chrome at 2× deviceScaleFactor using the site's own fonts; `apple-touch-icon.png` (180×180, 7KB) — emerald rounded square + paper ring + white-glyph logo.

**Validation (all green)**: smoke test (updated asset list, div balance, sprite refs); Playwright cross-browser suite **38/38 (Chromium + Firefox, desktop 1440 + mobile 390)** — includes a real bug found during the rebuild (a corrupted `'false');` fragment in `closeMobile()` that had broken the entire main script block: fixed, plus `overflow-x: clip` on html/body + `min-width: 0` on hero-grid children to keep transforms from causing scroll overflow; Lighthouse CI gate **all budgets met** (A11Y/BP/SEO ≥ 95, FCP/LCP/CLS caps met); zero console/page errors in both themes on all pages; full-page screenshots verified light + dark.

### August 8, 2026
- **Lighthouse CI gate added**: new `scripts/lighthouse-ci.sh` serves the repo locally, audits with Lighthouse (mobile, throttled), and fails the build on regression. **Scores**: A11Y ≥ 95, BP ≥ 95, SEO ≥ 95 enforced strictly; PERF score floor ≥ 50 (catastrophic tripwire only — GitHub's 2-core runners amplify Lighthouse's 4× CPU throttle into huge TBT swings, observed 0ms locally → 760/1190/2260ms in CI, dragging the perf score to 58-64 while FCP/LCP/CLS stay identical to local). **Stable metric caps** (environment-independent, these are what catch real regressions like a new render-blocking asset): FCP ≤ 3.0s, LCP ≤ 4.5s, CLS ≤ 0.10 — overridable via `LH_*` env vars; Chrome auto-discovered; Lighthouse version pinned in `package.json`. New `lighthouse` job in CI (`npx playwright-core install chromium` + run). Local runs: PERF 82-93, A11Y 99-100, BP 100, SEO 100, CLS 0.
- **Dark-theme branding assets**: regenerated `og-image.png` (1200×630, now **52KB** down from 99KB) using the site's own logo + self-hosted brand fonts rendered via headless Chrome — dark navy `#070b18` gradient background, blue/cyan glows, Space Grotesk 700 title, Inter tagline, brand-consistent with the current palette (social shares now match the new dark theme); added dark-mode awareness to `favicon.svg` via an SVG `@media (prefers-color-scheme: dark)` style — a subtle light ring appears around the navy brand mark on dark browser tabs (verified: hidden in light, `display:block` in dark); added `apple-touch-icon.png` (180×180, navy rounded square + logo, 6KB) + `<link rel="apple-touch-icon">` on all 3 pages for iOS home screens
- **SEO review of sitemap/robots against the live site** — found and documented a critical deployment issue: `www.tunzua.com` (the canonical domain used by `sitemap.xml`, `robots.txt`, `og:image`, and `canonical` tags) is currently serving a **completely different, outdated build** of the site (old CDN-based version: Tailwind Play CDN, Google Fonts, Font Awesome CDN, base64-embedded logos, Cloudflare email obfuscation). The current optimized repo only lives at `https://minatolun-dotcom.github.io/tunzua/`. Search engines crawl the OLD site at the canonical URL, so the new site is not yet being indexed under `tunzua.com`. **Decision (owner): leave as-is** — keep canonical/sitemap/robots pointing at `www.tunzua.com` (the intended production domain) and fix the domain switch later (GitHub Pages → Settings → Pages → Custom domain + DNS CNAME to `minatolun-dotcom.github.io`). Until then, social shares will also fetch the old `og-image.png` from `tunzua.com`. The repo-side files (`sitemap.xml`, `robots.txt`, local og-image) are all valid and correct for the intended domain. Verified: all 3 sitemap URLs return 200 on `www.tunzua.com` (serving the old site) and on the github.io deployment; both robots.txt and sitemap are XML-valid on both.
- **CI cross-browser suite added (incl. Safari/WebKit)**: new `scripts/xbrowser.js` — a self-contained Playwright suite that serves the repo locally and runs 19 layout/interactivity checks per browser (overflow, both marquees 8 items + animating, theme toggle persistence, counters → 1,000/15/99, scroll reveal, navbar `scrolled`, back-to-top visible + clickable above the cookie banner + scrolls to top, anchor nav, cookie banner accept/hide, mobile menu open/lock/close/navigate, zero console errors, desktop 1440px + mobile 390px). Added `package.json` + `package-lock.json` (`playwright-core` devDependency) and a `cross-browser` job in `.github/workflows/ci.yml` that runs `npx playwright-core install --with-deps chromium firefox webkit` (the `--with-deps` flag installs the missing system libs on the runner — this is how the earlier local WebKit limitation is solved: **GitHub runners have root**, unlike this dev box). First run on `c8ffb89`: **57 checks, 0 FAILED** — Chromium 19/19, Firefox 19/19, **WebKit 19/19** (Safari engine: overflow 0, marquees animate, back-to-top clickable `hit=use`, zero console errors). WebKit testing is now green on every push.
- **Lighthouse re-audit after the back-to-top fix** (live site, mobile/throttled): **PERF 93, a11y 100, BP 100, SEO 100**, FCP 1.2s, LCP 2.4s, TBT 260ms, CLS 0 — all green after the z-index fix
- **Cross-browser verification pass** (Playwright: **Firefox** + Chrome, desktop 1440px + mobile 390px, on all 3 pages): 38/38 interactivity checks + 16/16 legal-page checks pass in both engines — overflow 0, both marquees animate with 8 items, theme toggle flips class + persists (sun/moon swap), counters animate to targets (1,000/15/99), scroll reveal fires, navbar `scrolled` class, anchor nav lands on sections (top=80), cookie banner accepts + hides, mobile menu opens (scroll locked, aria-expanded) + closes + navigates, back-to-top appears + scrolls to top, zero console/page errors everywhere
  - **Fixed a real UX bug found by the cross-browser pass**: the **back-to-top button was completely covered by the cookie consent banner** (both z-50, banner painted later in the DOM — `elementFromPoint` at the button's center returned `cookieConsent`, so it was unclickable while the banner was visible). Raised the button above the banner via inline `z-index: 60` (removed the now-dead `z-50` class); still correctly sits below the top-of-viewport overlays (navbar z-1000, mobile menu z-999, hamburger z-1001)
  - WebKit (Safari engine) could not be tested: Playwright's WebKit needs system libs (`libbacktrace`, `libflite`, old `libxml2`) that aren't on this box and `/usr/lib` is read-only (no root) — Chrome + Firefox cover the two major engines
- **Visual/layout bug-fix pass** (found via a comprehensive headless-Chrome diagnostic at desktop + mobile widths — zero console errors, zero failed requests, but several silent layout bugs):
  - **Testimonials marquee was structurally broken**: the polish pass left 8 unclosed `<div class="marquee-item">` tags, so the browser nested all cards inside the first one (track rendered as a single 660px node instead of 8 sibling cards). Rebuilt the section from the original balanced cards (4 unique + 4 `aria-hidden` duplicates) — track now has 8 siblings at 3040px, animation intact.
  - **Horizontal page overflow (144px desktop / 39px mobile)**: decorative blobs in the "Why Choose Us" and "About" sections extend past the right edge (`right: -10%/-15%`) without `overflow-hidden` on their sections — added it (matches the other ~15 sections).
  - **Stray `</div>` in the Contact section** (before the CTA band) — found via a stack-based div-balance walk; removed. The whole document now has perfectly balanced divs (final stack 0, never negative).
  - **Client logo SVGs rendered at full intrinsic size** (client-0.svg is 1280px wide!) because the `max-h-12` utility was missing from `tailwind.min.css` — added `.max-h-12{max-height:3rem}`; logo chips now render at 171×94px (was ~1366px).
  - Added a **div-balance check to `scripts/smoke-test.sh`** (catches unclosed `<div>` bugs that break layout silently with zero console errors) — all 3 pages verified balanced.
  - Verified in headless Chrome: overflowX 0 at 1440px + 390px, both marquees 8 children, logos 8/8 loaded, zero console errors, JS syntax clean. Screenshots: `/tmp/tzdiag/fixed-*.png`
- **Counters + a11y audit fix**: upgraded the existing stats counter animation to ease-out cubic (rAF + `performance.now`, clamped elapsed), reduced-motion aware (final value set instantly), and `toLocaleString` thousand separators (1,000); fixed a heading-order regression the Lighthouse re-audit caught (the new CTA band h2 was followed by footer h4s, skipping h3) by promoting the footer column headings (Quick Links / Services / Contact) from `h4` to `h3` — visually neutral via the preflight reset; re-audit after deploy confirmed a11y back to 100
- **Lighthouse re-audit after polish pass**: PERF 85, a11y 98 (heading-order regression, since fixed), BP 100, SEO 100; FCP 0.9s, LCP 2.0s, CLS 0 — the testimonial marquee, dark polish, and parallax did not hurt performance
- **Polish pass** on `index.html` + `privacy.html`/`terms.html` (CSS/JS-first, zero new deps):
  - **Testimonials converted to a marquee**: the static 4-card grid now reuses the `.marquee`/`.marquee-track` system (4 unique reviews × 2 copies, 42s loop, aria-hidden duplicates, hover-pause, gradient edge fade)
  - **Dark theme polish**: richer dark palette (`--bg-primary: #070b18`, `--text-secondary: #a5b4d0`, `#121a33` tertiary) applied identically across all 3 pages; added `.dark .eyebrow::before` glow + `.dark .marquee-item .logo-chip` treatment
  - **Scroll-linked parallax**: the 9 decorative blobs now drift with scroll via `data-parallax` speeds in the rAF-throttled, passive `handleScroll` (replaces the old `blobMove` keyframes, which were removed along with dead `animation-delay` inline styles); parallax is skipped for `prefers-reduced-motion` users (verified in headless Chrome)
  - Cleaned up: removed the stagger/spotlight observer block (dangling `staggerObserver.observe(testimonialsGrid)` reference removed) and the `testimonials-grid` CSS; fixed 6 malformed `data-parallax` attributes that had been inserted inside `style=""`
- **Visual elevation pass** on `index.html` (CSS-first, zero new deps):
  - Client logos converted from a static grid to a seamless auto-scrolling **marquee** (duplicated set, pause-on-hover, gradient edge fades)
  - Unified **section eyebrows** (gradient dot + uppercase tracking) across all 8 sections (colors were previously inconsistent)
  - **Button shine sweep** on all primary CTAs (navbar, hero, pricing, cookie, mobile menu)
  - **Glass cards** get a gradient top-edge reveal on hover; **pricing highlight** card gets glow + scale
  - **Animated gradient text** (gradient-text now slowly shifts) + `text-wrap: balance` on headings
  - Hero **scroll cue** (animated mouse wheel indicator, hidden on mobile)
  - **CTA band** above the footer (gradient panel, white + ghost buttons)
  - Footer: logo image added to brand column + gradient top accent border
  - Removed the now-unused spotlight grid CSS and cursor-tracking JS
- Removed the custom cursor + magnifier lens feature from `index.html` (the mouse-following dot and glow bubble, their CSS incl. `lensSheen`, the two DOM elements, and the JS handlers) — site now uses the native cursor
- Lighthouse audit (13.4.1, mobile/throttled) run against live site: home 80/94/100/92, legal 100 BP + 100 SEO, 95 a11y
- Self-hosted Google Fonts: downloaded the exact woff2 files (Inter + Space Grotesk, latin + latin-ext, weights 400-700) into `assets/fonts/`, added `assets/css/fonts.css` with `font-display: swap`; removed the render-blocking `fonts.googleapis.com` stylesheet + preconnects from all pages; added a `<link rel="preload">` for the LCP font (Space Grotesk 700)
- Fixed dark-mode contrast: `--text-muted` was `#475569` (2.4:1 on dark bg — unreadable); lightened to `#94a3b8` (~7:1) in the dark block of all 3 pages
- Fixed heading order on `index.html`: process steps, About "Our Mission/Our Vision", and Contact card titles bumped from `h4` to `h3` (headings now descend correctly; zero violations)
- Made cookie-banner link descriptive: "Learn more" → "Read our privacy policy" (SEO + a11y)
- Extended `scripts/smoke-test.sh` to cover `assets/css/fonts.css`, font files, and the `fonts.googleapis`/`fonts.gstatic` CDN check
- Re-audited against the live site after fixes: **FCP 1.2-1.8s (was 2.8s), LCP 2.3-2.6s (was 4.3s), CLS 0, a11y 100, BP 100, SEO 100**; performance score 77-91 depending on run (TBT is run-variable; the pre-fix baseline was 80)
- Added `h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}` to `tailwind.min.css` (missing preflight heading reset) so the h4->h3 heading fix is visually neutral
- Added `<link rel="preload">` for both critical fonts (Inter 400 + Space Grotesk 700) so font swaps complete near first paint; verified live: fonts load, rupee symbol renders, theme toggle works, zero console errors, deployed HTML byte-identical to repo
- Set up git: initialized repository, configured GitHub identity + credential store, initial commit pushed to `github.com/minatolun-dotcom/tunzua` (`main`); `github-credentials` file excluded via `.gitignore`
- Added `scripts/smoke-test.sh` + GitHub Actions CI (`.github/workflows/ci.yml`) that validate pages/assets/icons on every push
- Moved `github-credentials` out of the repo to `~/.config/tunzua/github-credentials` (chmod 600)
- CI smoke test verified passing on GitHub Actions (run for commit `3a154c7`)
- GitHub Pages enabled by owner (Settings → Pages → *Deploy from a branch* → `main` / root). Live at `https://minatolun-dotcom.github.io/tunzua/` — verified with headless Chrome: all pages/assets 200, deployed `index.html` byte-identical to repo, icons/theme/mobile-menu/cookie-banner working
- Added `.nojekyll` so GitHub Pages serves the static files as-is (no Jekyll processing)
- Removed Font Awesome CDN from all pages; migrated all `<i>` icon tags to a local SVG sprite (`assets/fa-sprite.svg`), embedded inline per page (~150KB of third-party CSS+fonts removed)
- Added `arrow-left` symbol to the sprite (mirrored from `arrow-right`)
- Removed Tailwind Play CDN (`cdn.tailwindcss.com`) from `privacy.html`/`terms.html`; both now use the generated `tailwind.min.css` + new `assets/css/legal.css` supplement (contains the utility classes the legal pages need but the build lacks)
- Added missing utilities (`gap-1.5`, `py-1.5`, `py-2.5`, `w-0.5`) to `index.html`, fixing collapsed padding on chips/buttons
- Added no-flash theme script to `<head>` of all pages; fixed `index.html` persisting the system theme preference unintentionally
- Optimized `logo.png` from 127KB to 3.8KB (240×237, 256 colors)
- Generated `og-image.png` (1200×630 banner) and added Twitter card meta tags; the previously-broken `og:image` now resolves to a real file
- Added `robots.txt` and `sitemap.xml`
- Cleanup: removed dead `tailwind.config` script, obsolete `.fas.hidden` hack, empty `assets/js/` dir, stray `.vscode` extension recommendation; fixed JS ordering and a duplicate CSS comment
- Corrected `STATE.md`/`README.md` to match actual project state (no contact form exists; logo/icon claims were outdated)
- Regenerated `og-image.png` using the site's brand fonts (Space Grotesk 700 + Inter 400/600)
- Trimmed the 2 unused symbols (`arrow-left`, `phone-flip`) from `index.html`'s inline sprite embed (50 → 48)
- Browser verification (headless Chrome 151 via Puppeteer): all 3 pages render with zero console errors, zero failed requests; all 127+3+3 SVG icons render correctly (sizes, colors incl. yellow star ratings); theme toggle, mobile menu, cookie banner, reveal animations, and all restored utilities verified working
- Fixed a regression: `privacy.html`/`terms.html` links were underlined after dropping the Tailwind CDN (no preflight) — added `a { text-decoration: none; }` to `assets/css/legal.css`

### July 5, 2026
- Replaced Tailwind CDN with locally generated `tailwind.min.css` (index page only)
- Built Font Awesome SVG sprite (`assets/fa-sprite.svg`, 49 icons) — sprite wired into pages on August 8
- Removed duplicate logo loads; merged scroll handlers; added `unobserve()` to reveal observer

### July 4, 2026
- Extracted base64 images to `/assets/images/`; created `privacy.html` and `terms.html`
- Added cookie consent banner, favicon, lazy loading, accessibility fixes, README and STATE docs

---

## Contact for Issues

**Tunzua Consultancy**
- Phone: +91 8731831178
- Email: info@tunzua.com
- Website: https://www.tunzua.com

### August 10, 2026
- Visual polish pass 2: hero split layout (ledger statement card with crop marks, framed stats: businesses served 100+, years 15+, satisfaction 99%; concentric rings removed), navbar section-number folio (00-09 tracks scroll, Fraunces, hidden under 960px; hero section gained data-ghost=00 as the scroll-spy anchor), crop-mark frames extended to blog subscribe box + post CTA boxes (blog.css), focus-visible rings on blog/legal pages

### August 10, 2026 (later)
- Visual polish 3: hero parallax drift (ghost numeral + ledger card via --parallax CSS var, rAF-throttled, capped 60px, disabled on mobile + reduced-motion; ghost fades in via ghostIn so the decorative numeral isn't the LCP candidate), Firm-record ledger strip in the About section (5-column statement: Founded 2008 / Pan-India 2018 / Cities 10+ / Satisfaction 99% / Service lines 07, 'True & fair' footer, crop marks), page folio on all inner pages (blog.html, privacy, terms, all posts, monthly archive — Fraunces reading-progress numeral 00-99 in the shared navbar; generator templates updated, monthly archive regenerated from template)
- Lighthouse re-audit: Accessibility 100, Best Practices 100, SEO 100, Performance 100 (unthrottled: FCP/LCP 0.3s, CLS 0.001); 86 under simulated slow-4G throttle (single-file inline-CSS parse cost — known architecture tradeoff)
- NOTE for user: hero ledger says Est. 2011 but About timeline/firm-card say Founded 2008 (pre-existing inconsistency, now more visible)

### August 10, 2026 (polish 3 follow-ups)
- Founding year unified to 2008 everywhere (hero ledger Est. 2011 -> Est. 2008; 2008 was the site's established year in the About timeline + firm card)
- index.html inline <style> (697 lines / 46.5KB) externalized to assets/css/home.css (exact same bytes; link placed in the same head position after the theme-init script so dark-mode flash prevention is preserved). Real-world Lighthouse stays 100 (FCP/LCP 0.3s); simulated-throttle perf stays 86 (single-file HTML+JS parse cost - CSS externalization was architectural, not a throttle win)
- Folio unification: inner-page folios now track SECTION NUMBERS (not reading progress) via a dedicated data-folio attribute (legal-hero 01, privacy sections 02-11, terms 02-13, blog list 02, posts body 02 + related 03, monthly list 02; decoupled from decorative data-ghost since the monthly hero's ghost is the month number). Threshold = 40% viewport with scrollY<2px guard so short heroes show 01 at page top. Applied to 12 pages + both generator templates + blog.html prepend marker
- Before/after screenshots committed under docs/screenshots/ (vs parent commit 87ae96f)

### August 10, 2026 (UI polish batch — 8 items)
- Skip-to-content link on all 16 pages (homepage, blog, privacy, terms, 404, monthly archive, 8 posts): offscreen until Tab-focus, jumps to <main id="main-content">; .skip-link rules added to home.css + legal.css + the 404 inline style (404 links no shared sheet)
- theme-color meta on all pages: head snippet sets it from the saved theme pre-paint (no chrome-color flash), end-of-body snippet keeps it in sync on manual toggle (index.html updates inside setTheme instead)
- Navbar scroll-spy: .nav-link.active underlines the current section. Uses a 'section straddles the 12% viewport line' rule + max-top fallback — needed because #clients sits at doc-pos 900 (right after hero, before #services at 1097), so nav-order and 40%-threshold heuristics both failed (browser-verified all 6 sections)
- Back-to-top button now draws an SVG progress ring (r=20.5, dasharray 128.8, dashoffset driven in the existing rAF scroll handler)
- Reading progress bar on the 8 posts (same .scroll-progress pattern as the homepage, own rAF JS)
- Auto table of contents on posts: built from direct-child h2s (excludes .related-posts + .toc), hidden when <2 headings (digests), own scroll-spy using the same straddle rule; in the generator template + backfilled into the 8 posts
- Share row on posts (WhatsApp / X / LinkedIn) — hrefs built from location.href + document.title; zero deps
- Print stylesheets: home.css, legal.css, blog.css, 404.html (flatten to white/ink, hide nav, CTAs, ghost numerals, folio, scroll chrome)
- FAQ was already smooth (grid-template-rows transition); added .faq-item.open .faq-q accent color as polish
- Fixed Python f-string SyntaxWarning (\s in share-JS regex now \\s)
- Gates: smoke PASSED, tags balanced, JS syntax on all 16 pages OK, monthly regenerated from template, browser 26/26 (spy all sections, ring, skip link, theme-color toggle, TOC build+spy, share hrefs, progress, inner pages), xbrowser 48/48, reviewer-clean (404 skip-link CSS gap fixed)

### August 10, 2026 (follow-ups: mobile spy, blog topic filter, Lighthouse)
- Mobile-menu scroll-spy: the 7 section links in #mobileMenu gained class="mobile-link"; handleScroll syncs .active to the mobile menu too (href-compared to the desktop current link — fixed a string-vs-element compare found by the browser test), and toggleMobile() refreshes it on open. Active link: accent color + an absolutely-positioned em-dash marker (no layout shift)
- Blog topic-filter chips on blog.html (All / GST / Income Tax / Payroll / Bookkeeping / News): every post card carries data-topic (digests keyed by slug backfill; generator's update_blog_index now emits data-topic="news" + a vocabulary comment). Search + topic compose (count + contextual empty state, aria-pressed chips). Fixed a real mobile bug the test caught: .blog-search flex row now wraps and .blog-search-empty has flex-basis:100% so the empty-state message no longer crushes the input to 0 width at 390px
- Lighthouse (live): real-world perf 100 (FCP/LCP 0.9s, TBT 0ms, CLS 0); throttled 83 (TBT 510ms all document-attributed inline-script parse — the known single-file cost, unchanged by this batch); accessibility/best-practices/seo all 100
- Gates: browser 15/15 (mobile spy Home/Services/Clients incl. the out-of-order section, chips all topics + search-compose + empty state + mobile-width), xbrowser 48/48, smoke PASSED, JS syntax + tag balance OK, reviewer-clean

### August 10, 2026 (follow-ups 2: monthly chips, chip analytics, skip-to-list)
- Monthly archive: digest cards now carry data-topic="news"; the page builds its topic chips DYNAMICALLY from the topics actually present (All + News today — future-proof for evergreen posts). Same filtering + trackTopic as blog.html; regenerated from the updated template
- Lightweight chip-click analytics: trackTopic() fires a GoatCounter event (window.goatcounter.count event:true path topic/<t>) when the tracker is present and ALWAYS appends {t, at} to a localStorage ring buffer tunzua-topic-events (capped 200, lossless, no backend). Copies in blog.html + the generator monthly template are kept in sync (comment added)
- blog.html: focus-revealed Skip to insights list link (mirrors the global .skip-link, fixed below the navbar) jumping to the newly id="blogList" list section
- REVIEWER FIX: adding id="blogList" broke update_blog_index literal prepend marker (would crash the next digest run) — marker updated to match and verified by simulated insertion; blog.html unchanged by the test
- Gates: browser 14/14 (skip-link focus + jump, local events, monthly dynamic chips), xbrowser 48/48, smoke PASSED, JS syntax + tag balance OK, reviewer-clean

### August 10, 2026 (follow-ups 2: monthly chips, chip analytics, skip-to-list)
- Monthly archive: digest cards now carry data-topic="news"; the page builds its topic chips DYNAMICALLY from the topics actually present (All + News today — future-proof for evergreen posts). Same filtering + trackTopic as blog.html; regenerated from the updated template
- Lightweight chip-click analytics: trackTopic() fires a GoatCounter event (window.goatcounter.count event:true path topic/<t>) when the tracker is present and ALWAYS appends {t, at} to a localStorage ring buffer tunzua-topic-events (capped 200, lossless, no backend). Copies in blog.html + the generator monthly template are kept in sync (comment added)
- blog.html: focus-revealed Skip to insights list link (mirrors the global .skip-link, fixed below the navbar) jumping to the newly id="blogList" list section
- REVIEWER FIX: adding id="blogList" broke update_blog_index literal-prepend marker — generator now anchors on the section tag itself (regression-tested)
- REVIEWER FIX: .filter-skip now position:fixed below the navbar on focus (was absolute at page top:0, hidden under the fixed navbar)
