# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary (inferred — confirm):** small and medium business owners across India who need ongoing compliance handled — GST filings, bookkeeping, payroll — plus businesses adopting or maintaining Tally Prime. They want deadlines taken off their plate.
- **Secondary (inferred — confirm):** individuals filing income-tax returns; businesses in and around Churachandpur, Manipur who may visit in person.

## Product Purpose

Tunzua Consultancy is an accounting and taxation consultancy (Est. 2008, Churachandpur, Manipur, India) selling professional services: bookkeeping & accounting, GST filing, income tax, payroll, inventory, financial consulting, data migration, and Tally Prime licensing/setup/training/support (subscription plans ₹399–₹499/month). Success: enquiries and plan sign-ups (phone/WhatsApp/contact form).

## Positioning

Inferred (confirm): deadline-never-missed compliance plus Tally Prime specialization, with a dedicated contact person — a small-firm accessibility that large CA firms can't offer.

## Operating Context

- Static GitHub Pages site (CNAME tunzua.com), no build step; plain HTML/CSS/JS.
- Contact: info@tunzua.com, phone +91 8731831178, 53 Dawn School Road, Lailam Veng, Churachandpur, Manipur 795006. Hours Mon–Sat 09:30–18:00.
- Social: Facebook, X, Instagram, YouTube (see schema sameAs).
- Repo tooling: smoke tests, xbrowser checks, Lighthouse CI, blog generator scripts (Python) that produce blog posts, feed.xml, sitemap.xml.

## Capabilities and Constraints

- All content is hand-maintained HTML; blog posts are generated into /blog/ with a pipeline that must keep working (feed.xml, sitemap.xml, blog index templates).
- Site must remain a static site — no server. Contact/enquiry via mailto/tel/WhatsApp links and/or form actions that work without a backend (confirm what the current form does).
- Analytics present (check head includes GA). 404 page exists.
- **Open decisions (unconfirmed product facts — do not present as verified):** the stats 200+ businesses, 98% satisfaction, 100% deadlines met; testimonials; whether any compliance-status ticker data is maintained by the firm ( statutory due dates themselves are public facts and safe).

## Brand Commitments

- Name: Tunzua Consultancy. Logo: assets/images/logo.png / favicon.svg — brand blue **#001743** (sampled from both) is binding.
- Voice: plain, confident, numbers-first. English.
- User-pinned visual direction (binding, chosen from presented options): Swiss Grid system — white ground, ink black, brand navy #001743 accent, hard 2px rules, Inter (display to 900) + IBM Plex Mono for data/labels; V3 poster hero ("Books. Balanced. Every time." with giant year numeral) combined with V4 data elements (compliance-calendar ticker, services-as-ledger table, mono stat blocks). Mobile responsive is a hard requirement.

## Evidence on Hand

- Full service list and Tally pricing (₹499/₹449/₹399 monthly tiers) in index.html.
- Est. 2008. Registered business details in schema.org LocalBusiness JSON-LD.
- No client testimonials, case studies, or certifications verified — none may be fabricated.

## Product Principles

1. The numbers are the brand: precise, tabular, never decorative.
2. Deadlines and compliance are the promise; surfaces should make the calendar visible.
3. Small-firm accessibility: one call, a real person, plain language.
4. Trust through precision, not through ornament.

## Accessibility & Inclusion

- WCAG AA contrast on all text (4.5:1 body, 3:1 large) — user explicitly flagged button-text readability.
- All functionality keyboard reachable; visible focus states; reduced-motion respected for the ticker/marquee.
