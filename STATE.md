# Project State

**Last Updated:** August 8, 2026

---

## Current Status: Production Ready ✅

The Tunzua Consultancy website is a fully functional static site with all core features implemented. The August 8, 2026 pass removed the remaining third-party CDN dependencies (Font Awesome, Tailwind Play CDN), fixed broken metadata, and optimized assets.

---

## File Inventory

| File | Size | Lines | Status |
|------|------|-------|--------|
| `index.html` | 165K | ~2,200 | ✅ Active (inline icon sprite) |
| `privacy.html` | 21K | ~540 | ✅ Active (local Tailwind + sprite) |
| `terms.html` | 23K | ~560 | ✅ Active (local Tailwind + sprite) |
| `og-image.png` | 40K | - | ✅ Active social share banner |
| `robots.txt` | 68B | - | ✅ Active |
| `sitemap.xml` | 598B | - | ✅ Active |
| `favicon.svg` | 14K | - | ✅ Active |
| `tailwind.min.css` | 16K | - | ✅ Generated Tailwind CSS (index page) |
| `assets/css/legal.css` | 885B | - | ✅ Supplemental utilities (legal pages) |
| `assets/css/fonts.css` | 6.5K | - | ✅ Self-hosted @font-face rules (Inter + Space Grotesk) |
| `assets/fonts/` | 16 files | - | ✅ Inter + Space Grotesk woff2 (latin + latin-ext, weights 400-700) |
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

### August 8, 2026
- **Lighthouse CI gate added**: new `scripts/lighthouse-ci.sh` serves the repo locally, audits with Lighthouse (mobile, throttled), and fails the build if any category drops below budget (PERF ≥ 70 — set below the documented headless-CI noise band so it catches real regressions without flaking; A11Y ≥ 95, BP ≥ 95, SEO ≥ 95 — overridable via `LH_*` env vars; Chrome auto-discovered; Lighthouse version pinned in `package.json`). New `lighthouse` job in CI (`npx playwright-core install chromium` + run). Local runs: PERF 82-93, A11Y 99-100, BP 100, SEO 100, CLS 0.
- **Dark-theme branding assets**: regenerated `og-image.png` (1200×630, now **52KB** down from 99KB) using the site's own logo + self-hosted brand fonts rendered via headless Chrome — dark navy `#070b18` gradient background, blue/cyan glows, Space Grotesk 700 title, Inter tagline, brand-consistent with the current palette (social shares now match the new dark theme); added dark-mode awareness to `favicon.svg` via an SVG `@media (prefers-color-scheme: dark)` style — a subtle light ring appears around the navy brand mark on dark browser tabs (verified: hidden in light, `display:block` in dark); added `apple-touch-icon.png` (180×180, navy rounded square + logo, 6KB) + `<link rel="apple-touch-icon">` on all 3 pages for iOS home screens
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
