# Project State

**Last Updated:** August 8, 2026

---

## Current Status: Production Ready ✅

The Tunzua Consultancy website is a fully functional static site with all core features implemented. The August 8, 2026 pass removed the remaining third-party CDN dependencies (Font Awesome, Tailwind Play CDN), fixed broken metadata, and optimized assets.

---

## File Inventory

| File | Size | Lines | Status |
|------|------|-------|--------|
| `index.html` | 106K | ~2,300 | ✅ Active — **Swiss/Editorial redesign** (inline icon sprite, no Tailwind) |
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
