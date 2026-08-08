#!/usr/bin/env node
/**
 * Cross-browser verification suite for the Tunzua static site.
 *
 * Serves the repo on a local port (default 8098) and runs a layout +
 * interactivity check on Chromium, Firefox and WebKit at desktop (1440x900)
 * and mobile (390x844) widths. Exits non-zero if any browser fails.
 *
 * Requirements: playwright-core installed (npm i playwright-core) and the
 * browsers installed via `npx playwright-core install --with-deps chromium
 * firefox webkit` (the --with-deps flag installs the system libraries that
 * WebKit needs — needs root, which CI runners have).
 *
 * Usage: node scripts/xbrowser.js          # all browsers
 *        BROWSERS=chromium,firefox node scripts/xbrowser.js
 *        PORT=8098 node scripts/xbrowser.js
 */
'use strict';

const { spawn } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');

const ROOT = path.join(__dirname, '..');
const PORT = parseInt(process.env.PORT || '8098', 10);
const BROWSERS = (process.env.BROWSERS || 'chromium,firefox,webkit')
  .split(',').map(s => s.trim().toLowerCase()).filter(Boolean);

// --- tiny static file server (mirrors smoke-test.sh behaviour) ---
function startServer() {
  const mime = {
    '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
    '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2',
    '.txt': 'text/plain', '.xml': 'application/xml', '.json': 'application/json',
    '.webmanifest': 'application/manifest+json',
  };
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(req.url.split('?')[0]);
    const file = path.normalize(path.join(ROOT, urlPath === '/' ? 'index.html' : urlPath));
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404); res.end('not found'); return;
    }
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(resolve => server.listen(PORT, '127.0.0.1', () => resolve(server)));
}

const results = [];
function report(name, ok, detail) {
  results.push({ name, ok });
  console.log((ok ? 'PASS' : 'FAIL') + ' | ' + name + (detail ? ' | ' + detail : ''));
}

// Scroll by setting scrollTop directly (avoids racing scroll-smooth animations)
async function scrollTo(page, y, steps) {
  await page.evaluate(async ({ y, steps }) => {
    for (let i = 1; i <= steps; i++) {
      document.documentElement.scrollTop = Math.round(y * (i / steps));
      await new Promise(r => setTimeout(r, 30));
    }
  }, { y, steps });
}

async function auditBrowser(pw, bname, launcher) {
  console.log('\n===== ' + bname + ' =====');
  let browser;
  try {
    browser = await launcher.launch({ headless: true });
  } catch (e) {
    report(bname + ' launches', false, (e.message || '').split('\n')[0].slice(0, 140));
    return;
  }
  const errs = [];
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 120)); });
  page.on('pageerror', e => errs.push('PAGEERR: ' + String(e).slice(0, 140)));
  await page.goto('http://127.0.0.1:' + PORT + '/index.html', { waitUntil: 'networkidle0', timeout: 45000 });

  // ---- layout ----
  const layout = await page.evaluate(() => {
    const ov = document.documentElement.scrollWidth - document.documentElement.clientWidth;
    const tracks = [...document.querySelectorAll('.marquee-track')];
    return { ov, anims: tracks.map(t => getComputedStyle(t).animationName), items: tracks.map(t => t.children.length) };
  });
  report(bname + ' desktop overflow', layout.ov === 0, 'overflowX=' + layout.ov);
  report(bname + ' both marquees animate with 8 items',
    layout.anims.length === 2 && layout.anims.every(a => a === 'marquee') && layout.items.every(n => n === 8),
    'anims=' + layout.anims + ' items=' + layout.items);

  // ---- client logos actually render (non-zero size, distinct) ----
  // (scroll into view first so the lazy-loaded duplicates below the fold load)
  await scrollTo(page, 900, 8);
  await page.waitForTimeout(1200);
  const clientLogos = await page.evaluate(() => {
    const srcs = [...document.querySelectorAll('#clients img')].map(im => im.getAttribute('src'));
    const sizes = [...document.querySelectorAll('#clients img')].map(im => {
      const r = im.getBoundingClientRect();
      return Math.round(r.width) + 'x' + Math.round(r.height);
    });
    const unique = [...new Set(srcs)].length;
    const nonzero = sizes.filter(s => !s.startsWith('0x') && !s.endsWith('x0'));
    return { unique, sizes, nonzeroCount: nonzero.length, total: sizes.length };
  });
  report(bname + ' all client logos render non-zero (4 unique x 2)',
    clientLogos.unique === 4 && clientLogos.nonzeroCount === clientLogos.total,
    'unique=' + clientLogos.unique + ' sizes=' + clientLogos.sizes.join(','));

  // ---- theme toggle ----
  const darkBefore = await page.evaluate(() => document.documentElement.classList.contains('dark'));
  await page.click('#themeToggle');
  await page.waitForTimeout(400);
  const theme = await page.evaluate(() => ({
    dark: document.documentElement.classList.contains('dark'),
    stored: localStorage.getItem('theme'),
    sunHidden: document.getElementById('sunIcon').classList.contains('hidden'),
    moonHidden: document.getElementById('moonIcon').classList.contains('hidden'),
    sunVis: getComputedStyle(document.getElementById('sunIcon')).display !== 'none',
    moonVis: getComputedStyle(document.getElementById('moonIcon')).display !== 'none'
  }));
  // exactly one icon must be visibly rendered (the hidden class must be backed by CSS)
  report(bname + ' theme toggle flips + persists',
    theme.dark !== darkBefore && theme.stored === (theme.dark ? 'dark' : 'light') &&
    theme.sunHidden === theme.dark && theme.moonHidden === !theme.dark &&
    theme.sunVis === !theme.dark && theme.moonVis === theme.dark,
    'dark ' + darkBefore + '->' + theme.dark + ' stored=' + theme.stored);
  await page.click('#themeToggle');
  await page.waitForTimeout(300);

  // ---- WCAG text contrast audit (light + dark) ----
  // Flags any rendered text whose contrast vs its effective background is below
  // 4.5:1 (normal) / 3:1 (large) — catches invisible buttons like the mobile-menu
  // "Get Started" (ink-on-ink) and dark-mode label regressions.
  const contrastVio = [];
  for (const t of ['light', 'dark']) {
    await page.evaluate(th => { localStorage.setItem('theme', th); }, t);
    await page.reload({ waitUntil: 'networkidle0', timeout: 45000 });
    await page.waitForTimeout(600);
    const vio = await page.evaluate(() => {
      const parseColor = s => {
        const m = s.match(/rgba?\(([^)]+)\)/);
        if (!m) return null;
        const p = m[1].split(',').map(v => parseFloat(v.trim()));
        return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
      };
      const lum = c => {
        const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
        return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
      };
      const ratio = (a, b) => {
        const l1 = lum(a), l2 = lum(b);
        return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      };
      const htmlBg = getComputedStyle(document.documentElement).backgroundColor;
      const effBg = el => {
        let col = null, node = el;
        while (node) {
          const m = getComputedStyle(node).backgroundColor.match(/rgba?\(([^)]+)\)/);
          if (m) {
            const p = m[1].split(',').map(v => parseFloat(v.trim()));
            const a = p.length > 3 ? p[3] : 1;
            if (a > 0.02) {
              const rgb = [p[0], p[1], p[2], a];
              col = col ? [rgb[0] * a + col[0] * (1 - a), rgb[1] * a + col[1] * (1 - a), rgb[2] * a + col[2] * (1 - a), 1] : rgb;
              if (col[3] >= 0.99) return col;
            }
          }
          node = node.parentElement;
        }
        const m = htmlBg.match(/rgba?\(([^)]+)\)/);
        return m ? m[1].split(',').map(v => parseFloat(v.trim())) : [255, 255, 255, 1];
      };
      const bad = [];
      const seen = new Set();
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const node = walker.currentNode;
        const text = node.textContent;
        if (!text.trim()) continue;
        const el = node.parentElement;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 4 || r.height < 4) continue;
        const fs = parseFloat(cs.fontSize);
        const large = fs >= 24 || (fs >= 18.66 && parseInt(cs.fontWeight, 10) >= 700);
        const min = large ? 3 : 4.5;
        const fg = parseColor(cs.color);
        if (!fg) continue;
        if (ratio(fg, effBg(el)) < min) {
          const key = (typeof el.className === 'string' ? el.className : '') + '|' + text.trim().slice(0, 24);
          if (seen.has(key)) continue;
          seen.add(key);
          bad.push((el.tagName + '.' + (typeof el.className === 'string' ? el.className : '')).slice(0, 40) + ':' + text.trim().slice(0, 16));
        }
      }
      return bad.slice(0, 6);
    });
    contrastVio.push(...vio.map(v => t + ' ' + v));
  }
  report(bname + ' WCAG text contrast (light+dark)', contrastVio.length === 0,
    contrastVio.length ? contrastVio.join(' | ').slice(0, 240) : 'clean');
  // restore light theme for the remaining checks
  await page.evaluate(() => { localStorage.setItem('theme', 'light'); });
  await page.reload({ waitUntil: 'networkidle0', timeout: 45000 });
  await page.waitForTimeout(500);

  // ---- hamburger hidden on desktop ----
  const hbgDesk = await page.evaluate(() => {
    const h = document.getElementById('hamburger');
    const cs = getComputedStyle(h);
    return cs.display !== 'none' && cs.visibility !== 'hidden';
  });
  report(bname + ' hamburger hidden on desktop', !hbgDesk, 'visible=' + hbgDesk);

  // ---- slow scroll down: counters + reveal ----
  await scrollTo(page, 2600, 26);
  await page.waitForTimeout(2600);
  const counters = await page.evaluate(() => [...document.querySelectorAll('.counter')].map(c => c.textContent));
  const targets = await page.evaluate(() => [...document.querySelectorAll('.counter')].map(c => c.dataset.target));
  report(bname + ' counters animate to targets',
    counters.every((v, i) => String(parseInt(v.replace(/,/g, ''), 10)) === String(parseInt(targets[i], 10))),
    'values=' + counters.join(','));
  const reveal = await page.evaluate(() =>
    document.querySelectorAll('.reveal.active, .reveal-left.active, .reveal-right.active, .reveal-scale.active').length > 0);
  report(bname + ' scroll reveal activates', reveal);

  // ---- navbar scrolled + back-to-top visible + clickable ----
  await scrollTo(page, 4200, 10);
  await page.waitForTimeout(700);
  const btt = await page.evaluate(() => {
    const b = document.getElementById('backToTop');
    const r = b.getBoundingClientRect();
    const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return {
      navScrolled: document.getElementById('navbar').classList.contains('scrolled'),
      opacity: getComputedStyle(b).opacity,
      o0: b.classList.contains('opacity-0'),
      pe: b.classList.contains('pointer-events-none'),
      topHit: el ? (el.id || el.tagName) : 'none' // 'backToTop' or its 'use' child = button wins
    };
  });
  report(bname + ' navbar scrolled class', btt.navScrolled, 'scrolled=' + btt.navScrolled);
  report(bname + ' back-to-top visible', btt.opacity === '1' && !btt.o0 && !btt.pe, 'opacity=' + btt.opacity);
  report(bname + ' back-to-top clickable above cookie banner', btt.topHit === 'backToTop' || btt.topHit === 'use', 'hit=' + btt.topHit);
  await page.click('#backToTop', { timeout: 10000 });
  await page.waitForTimeout(1500);
  const scrolledUp = await page.evaluate(() => window.scrollY < 300);
  report(bname + ' back-to-top scrolls to top', scrolledUp, 'scrollY=' + (await page.evaluate(() => Math.round(window.scrollY))));

  // ---- anchor navigation ----
  await page.click('#navbar a[href="#pricing"]');
  await page.waitForTimeout(1800);
  const pricingTop = await page.evaluate(() => Math.round(document.getElementById('pricing').getBoundingClientRect().top));
  report(bname + ' navbar anchor navigates to #pricing', Math.abs(pricingTop) < 200, 'top=' + pricingTop);

  // ---- cookie banner ----
  const bannerVisible = await page.evaluate(() => {
    const c = document.getElementById('cookieConsent');
    return c.getBoundingClientRect().top < window.innerHeight;
  });
  if (bannerVisible) {
    await page.evaluate(() => {
      const btns = [...document.querySelectorAll('#cookieConsent button')];
      if (btns.length) btns[0].click();
    });
    await page.waitForTimeout(800);
    const hidden = await page.evaluate(() => document.getElementById('cookieConsent').getBoundingClientRect().top >= window.innerHeight);
    report(bname + ' cookie banner accepts + hides', hidden, 'hides=' + hidden);
  } else {
    report(bname + ' cookie banner flow', true, 'already dismissed');
  }

  report(bname + ' zero console/page errors (desktop)', errs.length === 0, errs.length ? errs.join(' | ').slice(0, 200) : 'clean');

  // ---- FAQ accordion ----
  await scrollTo(page, 5600, 10);
  await page.waitForTimeout(900);
  const faq = await page.evaluate(() => {
    const first = document.getElementById('faq-b1');
    const firstOpen = first.getAttribute('aria-expanded') === 'true';
    const panelOpen = document.getElementById('faq-a1').getBoundingClientRect().height > 20;
    document.getElementById('faq-b2').click();
    return new Promise(res => setTimeout(() => res({
      firstOpen,
      panelOpen,
      second: document.getElementById('faq-b2').getAttribute('aria-expanded'),
      firstAfter: document.getElementById('faq-b1').getAttribute('aria-expanded'),
      secondPanel: document.getElementById('faq-a2').getBoundingClientRect().height > 20
    }), 500));
  });
  report(bname + ' FAQ first item open by default', faq.firstOpen && faq.panelOpen, JSON.stringify(faq));
  report(bname + ' FAQ click swaps open item (single-open)',
    faq.second === 'true' && faq.firstAfter === 'false' && faq.secondPanel,
    JSON.stringify(faq));

  // ---- contact form validation ----
  const urlBefore = page.url();
  const form = await page.evaluate(() => {
    const f = document.getElementById('contactForm');
    const email = document.getElementById('cf-email');
    email.value = 'not-an-email';
    f.requestSubmit();
    return new Promise(res => setTimeout(() => res({
      valid: f.checkValidity(),
      statusText: (document.getElementById('formStatus').textContent || '').slice(0, 60)
    }), 400));
  });
  const urlAfter = page.url();
  report(bname + ' contact form blocks invalid email',
    form.valid === false && urlAfter === urlBefore,
    JSON.stringify(form) + ' urlStayed=' + (urlAfter === urlBefore));

  await page.close();

  // ================= MOBILE =================
  const mPage = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const merrs = [];
  mPage.on('console', m => { if (m.type() === 'error') merrs.push(m.text().slice(0, 120)); });
  mPage.on('pageerror', e => merrs.push('PAGEERR: ' + String(e).slice(0, 140)));
  await mPage.goto('http://127.0.0.1:' + PORT + '/index.html', { waitUntil: 'networkidle0', timeout: 45000 });

  const mlayout = await mPage.evaluate(() => ({
    ov: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    items: [...document.querySelectorAll('.marquee-track')].map(t => t.children.length)
  }));
  report(bname + ' mobile overflow', mlayout.ov === 0, 'overflowX=' + mlayout.ov);
  report(bname + ' mobile marquee items', mlayout.items.every(n => n === 8), 'items=' + mlayout.items);

  const hbgMob = await mPage.evaluate(() => {
    const h = document.getElementById('hamburger');
    const cs = getComputedStyle(h);
    return cs.display !== 'none' && cs.visibility !== 'hidden';
  });
  report(bname + ' hamburger visible on mobile', hbgMob, 'visible=' + hbgMob);

  if (hbgMob) {
    await mPage.click('#hamburger');
    await mPage.waitForTimeout(600);
    const menu = await mPage.evaluate(() => ({
      active: document.getElementById('mobileMenu').classList.contains('active'),
      expanded: document.getElementById('hamburger').getAttribute('aria-expanded'),
      overflow: document.body.style.overflow
    }));
    report(bname + ' mobile menu opens + locks scroll', menu.active && menu.expanded === 'true' && menu.overflow === 'hidden', JSON.stringify(menu));

    await mPage.click('#mobileMenu a[href="#services"]');
    await mPage.waitForTimeout(1100);
    const nav = await mPage.evaluate(() => ({
      closed: !document.getElementById('mobileMenu').classList.contains('active'),
      overflow: document.body.style.overflow,
      svcTop: Math.round(document.getElementById('services').getBoundingClientRect().top)
    }));
    report(bname + ' menu link closes + navigates', nav.closed && nav.overflow === '' && Math.abs(nav.svcTop) < 250, JSON.stringify(nav));
  }

  report(bname + ' zero console/page errors (mobile)', merrs.length === 0, merrs.length ? merrs.join(' | ').slice(0, 200) : 'clean');
  await mPage.close();
  await browser.close();
}

(async () => {
  const server = await startServer();
  const pw = require('playwright-core');
  const available = { chromium: pw.chromium, firefox: pw.firefox, webkit: pw.webkit };
  const missing = BROWSERS.filter(b => !available[b]);
  if (missing.length) {
    console.error('Unknown browsers requested: ' + missing.join(',') + ' (expected chromium/firefox/webkit)');
    process.exit(2);
  }
  for (const b of BROWSERS) {
    await auditBrowser(pw, b, available[b]);
  }
  server.close();
  const fails = results.filter(r => !r.ok);
  console.log('\n===== XBROWSER SUMMARY: ' + results.length + ' checks, ' + fails.length + ' FAILED =====');
  for (const f of fails) console.log('  FAILED: ' + f.name);
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.error('FATAL:', (e && e.message || e).split('\n')[0]); process.exit(2); });
