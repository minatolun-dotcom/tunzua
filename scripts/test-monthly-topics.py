#!/usr/bin/env python3
"""Test that the monthly archive template self-registers novel data-topics.

Renders scripts/generate-digest.py's update_monthly_archive() into a temp
directory (the real repo is never touched), then verifies two layers:

1. STATIC  — the generated page contains the self-registration chip-builder
   (order filter + novel-topic append + Title-Case label fallback) and the
   digest cards carry data-topic="news".
2. BROWSER — a fake card with a novel data-topic ("audit") is injected into the
   rendered page, and the page's own JS is executed in Chromium via
   playwright-core (the same dependency scripts/xbrowser.js uses): an "Audit"
   chip must appear after the known topics, filter correctly, and record a
   topic event. Skipped gracefully when node/playwright/chromium are missing
   (static checks still run).

Usage:
    python3 scripts/test-monthly-topics.py

Exit codes:
    0  passed (or browser layer skipped)
    1  a check failed
"""

import glob
import os
import shutil
import socket
import subprocess
import sys
import tempfile

from _testutil import REPO, load_generator, verdict
MONTH = "2026-07"  # a fake month — nothing in the real repo matches this


def fake_digest(day, stories):
    """A minimal digest post with the fields update_monthly_archive parses."""
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head><title>x</title></head>\n"
        f"<body>\n<h1 class=\"legal-title\">Tax news digest — Wed, {day:02d} Jul 2026</h1>\n"
        f"<p class=\"legal-updated\">Wed, {day:02d} Jul 2026 · {stories} stories</p>\n"
        "</body>\n</html>\n"
    )


NOVEL_CARD = (
    '<article class="post-card" data-topic="audit">'
    '<p class="post-meta"><span>Test</span></p>'
    '<h2><a href="#">Audit advisory</a></h2>'
    "<p>Audit readiness checklist for small firms.</p>"
    "</article>\n"
)


def copy_site_assets(tmp):
    """Copy real assets into the temp site so the rendered page has no 404s
    (keeps the browser layer's zero-console-errors check strict — only real
    JS errors can trip it)."""
    assets_src = os.path.join(REPO, "assets")
    if os.path.isdir(assets_src):
        shutil.copytree(assets_src, os.path.join(tmp, "assets"))
    for root_file in ("favicon.svg", "apple-touch-icon.png", "og-image.png"):
        src = os.path.join(REPO, root_file)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(tmp, root_file))


def render_monthly(gd, tmp):
    """Render the monthly archive for the fake month into tmp/blog/. Returns the HTML."""
    copy_site_assets(tmp)
    blog_dir = os.path.join(tmp, "blog")
    os.makedirs(blog_dir, exist_ok=True)
    with open(os.path.join(blog_dir, "tax-news-digest-2026-07-01.html"), "w", encoding="utf-8") as f:
        f.write(fake_digest(1, 4))
    with open(os.path.join(blog_dir, "tax-news-digest-2026-07-03.html"), "w", encoding="utf-8") as f:
        f.write(fake_digest(3, 6))
    # _ensure_sitemap_monthly appends to sitemap.xml — provide a minimal one.
    with open(os.path.join(tmp, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>')
    gd.ROOT = tmp
    gd.update_monthly_archive(f"{MONTH}-10")
    with open(os.path.join(tmp, "blog", "monthly", f"{MONTH}.html"), encoding="utf-8") as f:
        return f.read()


def static_checks(html):
    # This suite deliberately does NOT use _testutil.check(): static_checks and
    # browser_checks return their own failure lists, which main() combines and
    # passes to verdict() explicitly.
    fails = []
    checks = [
        ("monthly chips container present", "monthly-topics" in html),
        ("digest cards tagged data-topic=news", html.count('data-topic="news"') == 2),
        ("known-topic order filter present", "order.filter" in html),
        ("novel-topic append present", "Object.keys(seen).sort()" in html),
        ("Title-Case label fallback present", "labelFor" in html and "charAt(0).toUpperCase()" in html),
        ("topic tracking present", "tunzua-topic-events" in html),
    ]
    for name, ok in checks:
        print(("ok  : " if ok else "FAIL: ") + name)
        if not ok:
            fails.append(name)
    return fails


def free_port():
    """Ask the OS for a free localhost port (avoids collisions with other runs)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return str(port)


def find_chromium():
    exe = os.environ.get("CHROME_PATH")
    if exe and os.path.exists(exe):
        return exe
    hits = glob.glob(os.path.expanduser("~/.cache/puppeteer/chrome/*/chrome-linux64/chrome"))
    return hits[0] if hits else None


DRIVER = r"""
const fs = require('fs');
const http = require('http');
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright-core')); }
catch (e) { console.log('SKIP | playwright-core unavailable: ' + (e.message || e).split('\n')[0]); process.exit(3); }

const ROOT = process.env.SITE_ROOT;
const PORT = Number(process.env.PORT || 8931);
const PAGE = process.env.PAGE;
const CHROME = process.env.CHROME_PATH || '';
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2' };

const results = [];
function check(name, cond, extra) {
  results.push([cond, name]);
  console.log((cond ? 'PASS' : 'FAIL') + ' | ' + name + (extra ? ' | ' + extra : ''));
}

(async () => {
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(req.url.split('?')[0]);
    const file = path.normalize(path.join(ROOT, urlPath === '/' ? 'index.html' : urlPath));
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404); res.end('not found'); return;
    }
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(r => server.listen(PORT, '127.0.0.1', r));

  let browser;
  try { browser = await chromium.launch(CHROME ? { executablePath: CHROME } : {}); }
  catch (e) {
    console.log('SKIP | chromium unavailable: ' + (e.message || e).split('\n')[0]);
    server.close(); process.exit(3);
  }
  const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
  const errs = [];
  page.on('pageerror', e => errs.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('http://127.0.0.1:' + PORT + PAGE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(200);

  const chips = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.monthly-topics .topic-chip')).map(b => ({
      t: b.getAttribute('data-topic'),
      label: b.textContent,
      pressed: b.getAttribute('aria-pressed'),
      active: b.classList.contains('active'),
    }))
  );
  const topics = chips.map(c => c.t);
  check('novel topic self-registers a chip', topics.join(',') === 'all,news,audit', JSON.stringify(topics));
  const audit = chips.find(c => c.t === 'audit');
  check('novel topic gets Title-Case label', !!audit && audit.label === 'Audit', audit && audit.label);
  check('All chip first + active', chips[0] && chips[0].t === 'all' && chips[0].active && chips[0].pressed === 'true');

  await page.click('.monthly-topics .topic-chip[data-topic="audit"]');
  await page.waitForTimeout(100);
  const st = await page.evaluate(() => ({
    visible: Array.from(document.querySelectorAll('.blog-list .post-card')).filter(c => c.style.display !== 'none').length,
    auditPressed: document.querySelector('.monthly-topics .topic-chip[data-topic="audit"]').getAttribute('aria-pressed'),
    newsPressed: document.querySelector('.monthly-topics .topic-chip[data-topic="news"]').getAttribute('aria-pressed'),
    last: JSON.parse(localStorage.getItem('tunzua-topic-events') || '[]').slice(-1)[0],
  }));
  check('audit chip filters to audit card only', st.visible === 1, 'visible=' + st.visible);
  check('aria-pressed moves to audit', st.auditPressed === 'true' && st.newsPressed === 'false');
  check('topic event recorded', st.last && st.last.t === 'audit', JSON.stringify(st.last));
  check('zero console/page errors', errs.length === 0, errs.slice(0, 3).join(' | '));

  await browser.close();
  server.close();
  const failed = results.filter(r => !r[0]);
  console.log('SUMMARY: ' + (results.length - failed.length) + '/' + results.length + ' passed');
  process.exit(failed.length ? 1 : 0);
})().catch(e => { console.error('FATAL: ' + (e && e.message || e).split('\n')[0]); process.exit(2); });
"""


def browser_checks(html, tmp):
    """Inject a novel card and run the rendered page's own JS in Chromium."""
    if shutil.which("node") is None:
        print("skip: browser layer — node not found")
        return []
    marker = '<section class="blog-list" data-folio="02">\n'
    if marker not in html:
        print("skip: browser layer — blog-list marker not found in rendered page")
        return []
    novel_html = html.replace(marker, marker + NOVEL_CARD, 1)
    page_path = os.path.join(tmp, "blog", "monthly", f"{MONTH}-novel.html")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(novel_html)

    driver = os.path.join(tmp, "driver.js")
    with open(driver, "w", encoding="utf-8") as f:
        f.write(DRIVER)
    env = dict(os.environ)
    env["SITE_ROOT"] = tmp
    env["PORT"] = free_port()
    env["PAGE"] = f"/blog/monthly/{MONTH}-novel.html"
    chrome = find_chromium()
    if chrome:
        env["CHROME_PATH"] = chrome
    env["NODE_PATH"] = os.path.join(REPO, "node_modules")
    try:
        r = subprocess.run(["node", driver], env=env, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        print("FAIL: browser layer timed out after 180s")
        return ["browser layer timed out"]
    out = (r.stdout + r.stderr).strip()
    print(out)
    if r.returncode == 3:
        print("skip: browser layer — chromium/playwright unavailable")
        return []
    if r.returncode != 0:
        return ["browser layer exited " + str(r.returncode)]
    return []


def main():
    gd = load_generator()
    tmp = tempfile.mkdtemp(prefix="tunzua-monthly-test-")
    try:
        html = render_monthly(gd, tmp)
        fails = static_checks(html)
        fails += browser_checks(html, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return verdict("Monthly topic self-registration test", fails)


if __name__ == "__main__":
    sys.exit(main())
