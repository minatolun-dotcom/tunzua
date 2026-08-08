# Tunzua Consultancy Website

A modern, responsive single-page website for Tunzua Consultancy - a professional accounting, taxation, and business consulting firm based in Manipur, India.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Development](#setup--development)
- [Deployment](#deployment)
- [Performance Optimizations](#performance-optimizations)
- [Accessibility](#accessibility)
- [SEO](#seo)
- [Browser Support](#browser-support)

---

## Overview

This is a single-page application (SPA) built with vanilla HTML, CSS, and JavaScript. It showcases Tunzua Consultancy's services including bookkeeping, GST filing, income tax, Tally Prime solutions, payroll management, and business consulting.

**Live URL:** https://www.tunzua.com

---

## Features

### Core Features
- **Swiss/Editorial design system** - warm paper + deep ink palette, single navy accent (from the brand logo), Fraunces serif display, hairline rules, numbered sections — no gradients, no glass, no CDN
- **Responsive Design** - Fully responsive across all device sizes (mobile, tablet, desktop)
- **Dark/Light Mode** - Light-first, full dark skin with system-preference detection and localStorage persistence
- **Smooth Scroll Navigation** - Anchor-based navigation with smooth scrolling
- **Mobile Menu** - Hamburger menu with scroll-lock and ARIA state on mobile devices
- **Scroll Animations** - Intersection Observer-based reveal animations (reduced-motion aware)
- **Infinite Marquee** - Client logos (under hero) and testimonials auto-scrolling, pause on hover

### Sections
1. **Hero** - Editorial serif headline, lede, CTAs, stats counters (100+/15+/99%)
2. **Clients** - Logo marquee strip pulled up under the hero
3. **Services** - Numbered service rows (bookkeeping, GST, income tax, Tally, payroll, consulting) with feature lists
4. **Tally Prime** - Dedicated band with feature checklist
5. **Pricing** - 3-tier packages with highlighted middle tier
6. **Process** - 5 numbered steps (desktop row / mobile stack)
7. **FAQ** - Accessible accordion (single-open, ARIA) with common service questions
8. **Testimonials** - Auto-scrolling client reviews (marquee)
9. **About** - Mission, vision, timeline milestones, values
10. **Contact** - Visit/Call/Email/WhatsApp cards + **contact form** (validated, honeypot spam trap, FormSubmit.co endpoint with pre-filled-email fallback)
11. **CTA band + Footer** - Editorial footer with socials and legal links

### Additional Pages
- **Privacy Policy** (`privacy.html`)
- **Terms of Service** (`terms.html`)

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| HTML5 | Semantic markup |
| CSS3 | Custom properties, Swiss/Editorial layout, animations |
| JavaScript (ES6+) | Interactivity, animations (theme, reveal, counters, marquees, menu) |
| Hand-written CSS | Design system in page `<style>` + `assets/css/legal.css` (no Tailwind) |
| Self-hosted Google Fonts | **Fraunces** (serif display) + Inter + Space Grotesk (woff2, `font-display: swap`, no CDN) |
| Font Awesome 6.5 (local SVG sprite) | Icons (no CDN) |

---

## Project Structure

```
tunzua/
├── index.html              # Main landing page
├── privacy.html            # Privacy Policy page
├── terms.html              # Terms of Service page
├── og-image.png            # Social share banner (1200x630)
├── robots.txt              # Crawler rules
├── sitemap.xml             # XML sitemap
├── favicon.svg             # Site favicon (dark-mode ring)
├── apple-touch-icon.png    # iOS home-screen icon (navy brand mark)
├── README.md               # This documentation
├── STATE.md                # Project state tracking
└── assets/
    ├── fa-sprite.svg       # Local Font Awesome sprite (source for inline icons)
    ├── css/
    │   └── legal.css       # Supplemental utilities for legal pages
    └── images/
        ├── logo.png        # Tunzua logo (optimized)
        ├── client-0.svg    # Green Hills Agro logo
        ├── client-1.svg    # Tunnu Eatery / Tunnu School of Nursing logo
        ├── client-2.svg    # Grace Dental logo
        └── client-3.svg    # Client logo
```

---

## Setup & Development

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Text editor or IDE
- Local development server (optional)

### Quick Start

1. Clone or download the project files
2. Open `index.html` in a browser, or
3. Run a local server:

```bash
# Using Python
python3 -m http.server 8000

# Using Node.js (if installed)
npx serve .

# Using PHP
php -S localhost:8000
```

4. Visit `http://localhost:8000`

### Development Notes

- **No build step required** - The design system is hand-written CSS in each page's `<style>` block (index) and `assets/css/legal.css` (legal pages); no Tailwind
- **No framework dependencies** - Pure vanilla JS with no transpilation needed
- **CSS Custom Properties** - Theme tokens (`--paper`, `--ink`, `--accent`, `--hairline`) defined in `:root` and `.dark` selectors
- **Modular JavaScript** - All scripts are inline but organized by feature

---

## Deployment

### Static Hosting

This is a static site that can be deployed to any web hosting service:

- **Netlify** - Drag and drop the folder
- **Vercel** - Connect to Git repository
- **GitHub Pages** - This repo can serve directly from `main` (Settings → Pages → *Deploy from a branch* → `main` / root). Preview: `https://minatolun-dotcom.github.io/tunzua/`
- **Traditional Hosting** - Upload via FTP/SFTP

### Continuous Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs three jobs on every push/PR:

| Job | Script | Checks |
|-----|--------|--------|
| `smoke-test` | `scripts/smoke-test.sh` | All pages/assets return 200; no Font Awesome `<i>` tags or CDN references; every icon `<use>` resolves to an embedded sprite symbol; div balance |
| `cross-browser` | `scripts/xbrowser.js` | 19 layout/interactivity checks × Chromium, Firefox, **WebKit** (Safari engine) at desktop + mobile — overflow, marquees, theme toggle, counters, back-to-top, mobile menu, zero console errors (`npx playwright-core install --with-deps` provides the browsers incl. WebKit's system libs) |
| `lighthouse` | `scripts/lighthouse-ci.sh` | Lighthouse audit — A11Y/BP/SEO score budgets (≥ 95) + stable metric caps (FCP ≤ 3.0s, LCP ≤ 4.5s, CLS ≤ 0.10) + low PERF floor (≥ 50); the perf score itself isn't enforced because CI-runner TBT noise swings it 58–93 while FCP/LCP/CLS stay stable — overridable via `LH_*` env vars |

Run them locally anytime: `npm run test:smoke`, `npm run test:xbrowser`, `npm run test:lighthouse` (requires `npm ci` + `npx playwright-core install chromium` first).

### DNS Configuration

⚠️ **Important**: the custom domain `www.tunzua.com` currently serves an **outdated build** of the site (old CDN-based version), not this repo. The canonical tags, `sitemap.xml`, `robots.txt`, and OG image URLs point at `www.tunzua.com`, so until the domain is switched, search engines and social crawlers see the OLD site. The new site is live at the Pages preview: `https://minatolun-dotcom.github.io/tunzua/`.

To point `www.tunzua.com` at this repo (GitHub Pages custom domain):

1. Repo → **Settings → Pages → Custom domain** → enter `www.tunzua.com` → Save (GitHub verifies and issues the certificate)
2. At your DNS provider, add a `CNAME` record:

```
www  CNAME  minatolun-dotcom.github.io
```

3. Wait for certificate issuance, then verify `https://www.tunzua.com/` serves this site. (If `tunzua.com` itself should also serve the site, add an `A` record per GitHub's current IPs or a root redirect.)

### SSL/HTTPS

GitHub Pages issues a certificate automatically for the custom domain once the CNAME propagates. No manual certificate setup needed.

---

## Performance Optimizations

### Implemented

| Optimization | Status | Details |
|--------------|--------|---------|
| Image Optimization | ✅ | SVG logos extracted from base64 |
| Logo Optimization | ✅ | Compressed 127KB PNG to 3.8KB |
| Lazy Loading | ✅ | Added to client logos |
| Icon Delivery | ✅ | Font Awesome CDN replaced with local SVG sprite |
| Styling | ✅ | Tailwind CDN removed — hand-written design system, no framework CSS |
| Font Loading | ✅ | Self-hosted woff2 + `preload` for the LCP font (Fraunces latin) |
| Theme Persistence | ✅ | localStorage for dark mode + no-flash head script |
| Reduced Motion | ✅ | Respects `prefers-reduced-motion` |

### Recommended Future Optimizations

1. **JavaScript Bundling** - Minify and bundle inline scripts
2. **Critical CSS** - Inline above-the-fold styles
3. **Service Worker** - Add offline support

---

## Accessibility

### Implemented

- ✅ Skip navigation link
- ✅ Semantic HTML structure
- ✅ ARIA labels on interactive elements
- ✅ Keyboard navigation support
- ✅ Color contrast (WCAG AA compliant)
- ✅ Focus states for form elements
- ✅ Reduced motion support

### Form Accessibility

- Labels associated with inputs
- Required field indicators
- Error states (visual)
- Success feedback

---

## SEO

### On-Page SEO

- ✅ Semantic HTML headings (h1, h2, h3)
- ✅ Meta title and description
- ✅ Open Graph tags
- ✅ Canonical URL
- ✅ robots meta tag
- ✅ Schema.org structured data (LocalBusiness)

### Schema.org Data

Single `@graph` JSON-LD block containing: **LocalBusiness** (with `hasOfferCatalog`), **6 Service** entries (bookkeeping, GST, income tax, Tally Prime, payroll, consulting), and an **FAQPage** matching the on-page FAQ accordion.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "LocalBusiness", "@id": "https://www.tunzua.com/#business", "name": "Tunzua Consultancy", ... },
    { "@type": "Service", "@id": "https://www.tunzua.com/#svc-gst", "serviceType": "GST Filing", ... },
    { "@type": "FAQPage", "mainEntity": [ ... ] }
  ]
}
```

### Recommended SEO Improvements

1. Add Google Analytics/Plausible
2. ~~Implement structured data for services (Service, FAQ types)~~ **Done Aug 8, 2026** — Service + FAQPage in the JSON-LD `@graph`
3. Replace the self-reported `aggregateRating` schema with real review markup
4. ~~Wire the contact form to a form backend~~ **Done Aug 8, 2026** — `FORM_ENDPOINT` set to FormSubmit.co AJAX endpoint (`info@tunzua.com`); zero-account, one-time activation email on first submission, built-in spam filters + local honeypot (`_gotcha`/`_honey`). Falls back to a pre-filled `mailto:` if the fetch fails.

---

## Browser Support

| Browser | Version |
|---------|---------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |
| Mobile Safari | 14+ |
| Chrome Android | 90+ |

---

## Color Palette

### Light Mode
| Variable | Value | Usage |
|----------|-------|-------|
| `--paper` | `#f5f2ea` | Main background (warm paper) |
| `--paper-2` | `#ece7da` | Alt section / footer background |
| `--surface` | `#fbfaf5` | Cards |
| `--ink` | `#1a1713` | Headings / primary text |
| `--ink-2` | `#57513f` | Body text |
| `--ink-3` | `#6d6554` | Muted text (AA ≥ 4.5:1) |
| `--accent` | `#10306e` | Navy accent (brand logo `#001743` family) |
| `--hairline` | `#d8d0bc` | 1px rules / borders |

### Dark Mode
| Variable | Value | Usage |
|----------|-------|-------|
| `--paper` | `#15130f` | Main background (deep ink) |
| `--paper-2` | `#1d1a14` | Alt section / footer background |
| `--surface` | `#1a1712` | Cards |
| `--ink` | `#ede8dc` | Headings / primary text |
| `--ink-2` | `#b3ac9b` | Body text |
| `--ink-3` | `#857e6c` | Muted text |
| `--accent` | `#9db9e8` | Periwinkle accent (light navy, mirrors favicon tints) |
| `--hairline` | `#322c20` | 1px rules / borders |

---

## Contact Information

**Tunzua Consultancy**
- Address: 53, Dawn School Road, Lailam Veng, Churachandpur, Manipur 795006
- Phone: +91 8731831178
- Email: info@tunzua.com
- WhatsApp: https://wa.me/918731831178

### Social Links
- Facebook: https://www.facebook.com/tunzuaconsultancy/
- X (Twitter): https://x.com/jammangguite
- Instagram: https://www.instagram.com/tunzuaconsultancy/
- YouTube: https://www.youtube.com/channel/UCcl0Yn-8bnv7dDuS6NJxCWQ

---

## License

© 2026 Tunzua Consultancy. All rights reserved.
