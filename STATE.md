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
