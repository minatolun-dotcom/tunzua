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
- **Responsive Design** - Fully responsive across all device sizes (mobile, tablet, desktop)
- **Dark/Light Mode** - Toggle with system preference detection and localStorage persistence
- **Smooth Scroll Navigation** - Anchor-based navigation with smooth scrolling
- **Mobile Menu** - Hamburger menu with full-screen overlay on mobile devices
- **Scroll Animations** - Intersection Observer-based reveal animations
- **Custom Cursor** - Desktop-only custom cursor with hover effects
- **Magnetic Buttons** - Interactive button hover effects
- **Infinite Marquee** - Client logos and testimonials auto-scrolling

### Sections
1. **Hero** - Main value proposition with animated dashboard preview
2. **Trust Indicators** - Counter animations for key statistics
3. **Services** - Bento grid layout showcasing all services
4. **Why Choose Us** - Feature highlights with glass cards
5. **Tally Prime** - Dedicated section with pricing plans
6. **Pricing** - Service packages with call-to-action
7. **Process** - 5-step horizontal timeline (desktop) / vertical (mobile)
8. **Testimonials** - Auto-scrolling client reviews
9. **Clients** - Logo marquee with 3D hover effects
10. **About** - Company story, mission, vision, and timeline
11. **Contact** - Contact cards, WhatsApp quick link, Google rating
12. **Footer** - Links, social icons, and copyright

### Additional Pages
- **Privacy Policy** (`privacy.html`)
- **Terms of Service** (`terms.html`)

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| HTML5 | Semantic markup |
| CSS3 | Custom properties, animations, glassmorphism |
| JavaScript (ES6+) | Interactivity, animations, routing |
| Tailwind CSS (generated build) | Utility-first CSS framework |
| Google Fonts | Inter + Space Grotesk |
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
├── favicon.svg             # Site favicon
├── tailwind.min.css        # Generated Tailwind build (tree-shaken)
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

- **No build step required** - The site uses Tailwind CSS via CDN for development
- **No framework dependencies** - Pure vanilla JS with no transpilation needed
- **CSS Custom Properties** - Theme colors defined in `:root` and `.dark` selectors
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

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs `scripts/smoke-test.sh` on every push/PR — it verifies all pages and assets return 200, that no Font Awesome `<i>` tags or CDN references remain, and that every icon `<use>` resolves to an embedded sprite symbol. Run it locally anytime with `bash scripts/smoke-test.sh`.

### DNS Configuration

For production deployment at `tunzua.com`:

```
A Record    -> Hosting IP
CNAME       -> www.tunzua.com -> tunzua.com
```

### SSL/HTTPS

Ensure SSL certificate is configured for:
- `tunzua.com`
- `www.tunzua.com`

---

## Performance Optimizations

### Implemented

| Optimization | Status | Details |
|--------------|--------|---------|
| Image Optimization | ✅ | SVG logos extracted from base64 |
| Logo Optimization | ✅ | Compressed 127KB PNG to 3.8KB |
| Lazy Loading | ✅ | Added to client logos |
| Icon Delivery | ✅ | Font Awesome CDN replaced with local SVG sprite |
| Tailwind CSS | ✅ | CDN replaced with generated local build + supplements |
| Font Loading | ✅ | Preconnect to Google Fonts |
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

```json
{
  "@type": "LocalBusiness",
  "name": "Tunzua Consultancy",
  "telephone": "+91-8731831178",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Churachandpur",
    "addressRegion": "Manipur",
    "postalCode": "795006"
  }
}
```

### Recommended SEO Improvements

1. Add Google Analytics/Plausible
2. Implement structured data for services (Service, FAQ types)
3. Replace the self-reported `aggregateRating` schema with real review markup

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
| `--bg-primary` | `#ffffff` | Main background |
| `--bg-secondary` | `#f8fafc` | Section backgrounds |
| `--text-primary` | `#0f172a` | Headings |
| `--text-secondary` | `#475569` | Body text |
| `--text-muted` | `#475569` | Captions |
| `--border-color` | `#e2e8f0` | Borders |

### Dark Mode
| Variable | Value | Usage |
|----------|-------|-------|
| `--bg-primary` | `#0a0a1a` | Main background |
| `--bg-secondary` | `#0f1729` | Section backgrounds |
| `--text-primary` | `#f1f5f9` | Headings |
| `--text-secondary` | `#94a3b8` | Body text |
| `--border-color` | `#1e293b` | Borders |

### Accent Colors
| Color | Hex | Usage |
|-------|-----|-------|
| Blue | `#2563eb` | Primary accent |
| Cyan | `#06b6d4` | Secondary accent |
| Green | `#10b981` | Success states |
| Purple | `#8b5cf6` | Tertiary accent |
| Gold | `#f59e0b` | Highlights |

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

© 2025 Tunzua Consultancy. All rights reserved.
