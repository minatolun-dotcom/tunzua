#!/usr/bin/env python3
"""
Tunzua daily tax news digest generator.

Fetches verified Indian tax/GST RSS feeds, keeps items from the last 48 hours
that are tax-relevant (and not job postings), and publishes a "Tax news digest"
post in the site's design. Updates blog.html, feed.xml and sitemap.xml.

Usage:
    python3 scripts/generate-digest.py            # real run (writes files)
    python3 scripts/generate-digest.py --dry-run  # print what would happen

Exit codes:
    0  ok (post published, or nothing to publish)
    2  fatal error (feeds all failed)

Design notes:
- Python stdlib only (urllib + xml.etree) so GitHub Actions needs no pip install.
- State (published item GUIDs) lives in blog/.digest-state.json, committed to the
  repo so dedup survives across runs.
- Quiet days (fewer than MIN_ITEMS fresh relevant items) skip publishing entirely.
- Every headline links to its real source; the post carries a disclaimer.
"""

import argparse
import email.utils
import hashlib
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(ROOT, "blog", ".digest-state.json")

# How far back an item's pubDate may be and still count as "today's news".
FRESHNESS_HOURS = 48
# Publish only when at least this many fresh relevant items are found.
MIN_ITEMS = 3
# Cap the digest at this many items.
MAX_ITEMS = 12

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 TunzuaDigest/1.0"
)

FEEDS = [
    {
        "name": "Taxscan — Income Tax",
        "url": "https://www.taxscan.in/income-tax/feed",
        "filter": "tax",  # category feed: keep tax-relevant, drop job posts
    },
    {
        "name": "Taxscan — Top stories",
        "url": "https://www.taxscan.in/feed",
        "filter": "tax",
    },
    {
        "name": "TaxGuru — Tax & GST news",
        "url": "https://www.taxguru.in/feed/",
        "filter": "tax",
    },
    {
        "name": "Economic Times — Tax",
        "url": "https://economictimes.indiatimes.com/wealth/tax/rssfeeds/13358845.cms",
        "filter": "tax",
    },
    {
        "name": "Moneycontrol — Business",
        "url": "https://www.moneycontrol.com/rss/business.xml",
        "filter": "tax",
    },
]

# Cap blog.html digest cards and feed.xml items at this many latest entries.
# Keeps the index and feed from growing unbounded after months of digests;
# older digest pages stay live (sitemap still lists them).
MAX_LIST_ITEMS = 30

# Terms that make an item tax/accounting relevant (title or link, case-insensitive).
TAX_TERMS = [
    "gst", "income tax", "it department", "cbd", "it department", "tds", "tcs",
    "itr", "tax", "assessment", "tribunal", "itat", "gstin", "e-way", "customs",
    "excise", "cgst", "sgst", "gst council", "refund", "notice", "compliance",
    "accounting", "audit", "ca ", "chartered accountant", "bookkeeping", "payroll",
    "pf ", "esi", "tax audit", "44ab", "gstr", "e-invoice", "e-invoicing",
    "input tax credit", "itc", "taxation", "scanner", "due date", "deadline",
]

# Terms that make an item a job posting or otherwise off-topic (dropped).
JOB_TERMS = [
    "vacancy", "job-scan", "hiring", "recruitment", "interview", "jobs in",
    "placement", "career",
]

# Feed name -> displayed source for the post.
SOURCE_LABELS = {
    "Taxscan — Income Tax": "Taxscan",
    "Taxscan — Top stories": "Taxscan",
    "TaxGuru — Tax & GST news": "TaxGuru",
    "Economic Times — Tax": "Economic Times",
    "Moneycontrol — Business": "Moneycontrol",
}


def fetch(url, timeout=25):
    """Fetch a URL with a browser-ish UA. Returns bytes or raises."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_items(data):
    """Parse RSS/Atom into a list of dicts: title, link, date(datetime|None)."""
    root = ET.fromstring(data)
    items = []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag != "item" and tag != "entry":
            continue
        title = node.findtext("title") or node.findtext("{http://www.w3.org/2005/Atom}title") or ""
        link_el = node.find("link")
        if isinstance(link_el, ET.Element):
            link = link_el.get("href") or link_el.text or ""
        else:
            link = ""
        pub = node.findtext("pubDate")
        if pub is None:
            pub = node.findtext("{http://purl.org/dc/elements/1.1/}date")
        if pub is None:
            pub = node.findtext("{http://www.w3.org/2005/Atom}updated")
        dt = None
        if pub:
            try:
                dt = email.utils.parsedate_to_datetime(pub)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                dt = None
        items.append({
            "title": html.unescape(re.sub(r"\s+", " ", title)).strip(),
            "link": (link or "").strip(),
            "date": dt,
        })
    return items


def is_tax_relevant(item):
    """True when the item looks like tax/accounting news, not a job posting."""
    hay = (item["title"] + " " + item["link"]).lower()
    if any(t in hay for t in JOB_TERMS):
        return False
    return any(t in hay for t in TAX_TERMS)


def categorize(title):
    """Pick a short category label from the headline."""
    t = title.lower()
    if any(w in t for w in ["gst", "gstin", "gstr", "e-way", "input tax credit", "cgst", "sgst", "composition"]):
        return "GST"
    if any(w in t for w in ["payroll", "pf ", "esi", "epf"]):
        return "Payroll"
    if any(w in t for w in ["audit", "44ab", "icai", "accounting", "bookkeeping", "ca "]):
        return "Accounting"
    if any(w in t for w in ["itr", "income tax", "tds", "tcs", "assessment", "tribunal", "itat", "tax audit", "refund", "notice"]):
        return "Income Tax"
    return "Tax"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"published": []}
    return {"published": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def esc(text):
    return html.escape(text, quote=True)


def fmt_date(dt):
    """e.g. 'Sun, 09 Aug 2026'"""
    return dt.strftime("%a, %d %b %Y") if dt else ""


def rss_date(dt):
    return dt.strftime("%a, %d %b %Y 00:00:00 +0000")


def send_digest_email(items, date_label, day_iso):
    """Best-effort: email a digest summary to the firm via FormSubmit.

    Never raises — the digest must publish even if emailing fails.
    Returns True on success.
    """
    target = os.environ.get("DIGEST_EMAIL_TO", "info@tunzua.com")
    lines = [
        f"Tax news digest for {date_label} — {len(items)} stories:",
        "",
    ]
    for it in items[:12]:
        src = SOURCE_LABELS.get(it["source"], it["source"])
        lines.append(f"• {it['title']}")
        lines.append(f"  ({src}) {it['link']}")
        lines.append("")
    lines.append(f"Read it online: https://tunzua.com/blog/tax-news-digest-{day_iso}.html")
    lines.append("")
    lines.append("— Sent automatically by the Tunzua daily digest.")
    payload = {
        "email": "digest@tunzua.com",
        "subject": f"Tax news digest — {date_label}",
        "message": "\n".join(lines),
        "_captcha": "false",
        "_honey": "",
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://formsubmit.co/ajax/{target}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "Referer": "https://tunzua.com/",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            print(f"[email] FormSubmit HTTP {resp.status}: {body[:120]}")
            # FormSubmit returns {"success":"true",...} — success is a quoted
            # string, so match that exact shape (or just the key).
            return resp.status == 200 and '"success":"true"' in body
    except Exception as exc:
        print(f"[email] failed (non-fatal): {exc}", file=sys.stderr)
        return False


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def update_blog_index(items, date_label, day_iso):
    """Prepend a digest card to blog.html after the opening <section class="blog-list">."""
    path = os.path.join(ROOT, "blog.html")
    content = read(path)
    card = (
        '                <article class="post-card">\n'
        f'                    <p class="post-meta"><span>{esc(date_label)}</span><span class="dot"></span><span>News digest</span><span class="dot"></span><span>{len(items)} stories</span></p>\n'
        f'                    <h2><a href="blog/tax-news-digest-{day_iso}.html">Tax news digest — {esc(date_label)}</a></h2>\n'
        f"                    <p>The day's tax and GST stories from Indian news sources, curated and linked at source — tribunal rulings, department updates, due dates and compliance changes.</p>\n"
        f'                    <a class="post-link" href="blog/tax-news-digest-{day_iso}.html">Read digest <svg viewBox="0 0 448 512" fill="currentColor" aria-hidden="true"><path d="M438.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-160-160c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L338.8 224 32 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l306.7 0L233.4 393.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l160-160z"/></svg></a>\n'
        "                </article>\n"
    )
    marker = '            <section class="blog-list">\n'
    if marker not in content:
        raise RuntimeError("blog.html: <section class=\"blog-list\"> marker not found")
    content = content.replace(marker, marker + card, 1)
    # Trim: cap only the auto-generated digest cards. Hand-written evergreen
    # posts (due dates, payroll, records…) must NEVER be trimmed — they are the
    # site's permanent SEO content. Digest cards are identified by the
    # tax-news-digest- slug in their href.
    digest_blocks = [
        b for b in re.findall(r"<article class=\"post-card\">.*?</article>\n", content, flags=re.S)
        if "tax-news-digest-" in b
    ]
    if len(digest_blocks) > MAX_LIST_ITEMS:
        for old in digest_blocks[MAX_LIST_ITEMS:]:
            content = content.replace(old, "", 1)
    write(path, content)


def update_feed(items, date_label, day_iso):
    """Prepend a digest item to feed.xml right after the atom:link line."""
    path = os.path.join(ROOT, "feed.xml")
    content = read(path)
    pub = datetime.now(timezone.utc)
    descriptions = " ".join(f"{it['title']} ({SOURCE_LABELS.get(it['source'], it['source'])})." for it in items[:3])
    item = (
        "    <item>\n"
        f"      <title>Tax news digest — {esc(date_label)}</title>\n"
        f"      <link>https://tunzua.com/blog/tax-news-digest-{day_iso}.html</link>\n"
        f"      <guid>https://tunzua.com/blog/tax-news-digest-{day_iso}.html</guid>\n"
        f"      <pubDate>{rss_date(pub)}</pubDate>\n"
        f"      <description>{esc(descriptions)}</description>\n"
        "    </item>\n"
    )
    marker = '    <atom:link href="https://tunzua.com/feed.xml" rel="self" type="application/rss+xml"/>\n'
    if marker not in content:
        raise RuntimeError("feed.xml: atom:link marker not found")
    content = content.replace(marker, marker + item, 1)
    # Trim: keep only the newest MAX_LIST_ITEMS feed items.
    items_blocks = re.findall(r"    <item>.*?</item>\n", content, flags=re.S)
    if len(items_blocks) > MAX_LIST_ITEMS:
        for old in items_blocks[MAX_LIST_ITEMS:]:
            content = content.replace(old, "", 1)
    write(path, content)


def update_sitemap(day_iso):
    """Insert a digest URL entry into sitemap.xml before the closing </urlset>."""
    path = os.path.join(ROOT, "sitemap.xml")
    content = read(path)
    entry = (
        "  <url>\n"
        f"    <loc>https://tunzua.com/blog/tax-news-digest-{day_iso}.html</loc>\n"
        f"    <lastmod>{day_iso}</lastmod>\n"
        "    <changefreq>daily</changefreq>\n"
        "    <priority>0.7</priority>\n"
        "  </url>\n"
    )
    marker = "</urlset>"
    if marker not in content:
        raise RuntimeError("sitemap.xml: </urlset> marker not found")
    content = content.replace(marker, entry + marker, 1)
    # Trim: keep only the newest MAX_LIST_ITEMS digest URLs in the sitemap.
    # (Digest entries are appended at the end, so excess ones sit just before
    # the evergreen pages — remove the oldest digest <url> blocks.)
    digest_urls = re.findall(r"  <url>\n    <loc>https://tunzua.com/blog/tax-news-digest-[^<]+</loc>.*?</url>\n", content, flags=re.S)
    if len(digest_urls) > MAX_LIST_ITEMS:
        for old in digest_urls[: len(digest_urls) - MAX_LIST_ITEMS]:
            content = content.replace(old, "", 1)
    write(path, content)


def build_post_html(items, date_label, day_iso, date_long):
    """Generate the digest post HTML file (mirrors the site's post template)."""
    rows = []
    for it in items:
        rows.append(
            '                    <li class="digest-item">\n'
            f'                        <p class="digest-meta"><span>{esc(categorize(it["title"]))}</span><span class="dot"></span><span>{esc(SOURCE_LABELS.get(it["source"], it["source"]))}</span>{(" · " + esc(fmt_date(it["date"]))) if it["date"] else ""}</p>\n'
            f'                        <h3><a href="{esc(it["link"])}" target="_blank" rel="noopener">{esc(it["title"])}</a></h3>\n'
            "                    </li>\n"
        )
    items_html = "\n".join(rows)

    # Unique description for SEO (avoids duplicate content across digests).
    first = items[0]
    first_short = first["title"]
    if len(first_short) > 96:
        first_short = first_short[:93].rsplit(" ", 1)[0] + "…"
    desc = f"Today's Indian tax and GST news roundup — {len(items)} stories including “{first_short}” — curated from verified sources with links."

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/svg+xml" href="../favicon.svg">
    <link rel="apple-touch-icon" href="../apple-touch-icon.png">
    <title>Tax news digest — {esc(date_label)} | Tunzua Consultancy</title>
    <meta name="description" content="{esc(desc)}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://tunzua.com/blog/tax-news-digest-{day_iso}.html">

    <!-- Open Graph -->
    <meta property="og:title" content="Tax news digest — {esc(date_label)} | Tunzua Consultancy">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://tunzua.com/blog/tax-news-digest-{day_iso}.html">
    <meta property="og:image" content="https://tunzua.com/og-image.png">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Tax news digest — {esc(date_label)} | Tunzua Consultancy">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="twitter:image" content="https://tunzua.com/og-image.png">

    <!-- Schema.org: BlogPosting -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "Tax news digest — {esc(date_label)}",
        "description": "{esc(desc)}",
        "datePublished": "{day_iso}",
        "dateModified": "{day_iso}",
        "author": {{ "@type": "Organization", "name": "Tunzua Consultancy", "url": "https://tunzua.com" }},
        "publisher": {{ "@type": "Organization", "name": "Tunzua Consultancy", "url": "https://tunzua.com" }},
        "mainEntityOfPage": {{ "@type": "WebPage", "@id": "https://tunzua.com/blog/tax-news-digest-{day_iso}.html" }}
    }}
    </script>

    <!-- Brand fonts (self-hosted) -->
    <link rel="preload" href="../assets/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="../assets/fonts/inter-400-latin.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="stylesheet" href="../assets/css/fonts.css">
    <link rel="stylesheet" href="../assets/css/legal.css">
    <link rel="stylesheet" href="../assets/css/blog.css">

    <!-- Apply saved theme before first paint (prevents dark-mode flash) -->
    <script>
        (function () {{
            try {{
                var t = localStorage.getItem('theme');
                if (t === 'dark' || (!t && window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
                    document.documentElement.classList.add('dark');
                }}
            }} catch (e) {{}}
        }})();
    </script>
</head>
<body>

    <!-- Icon sprite (local) -->
<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">
    <symbol id="moon" viewBox="0 0 384 512">
<path d="M223.5 32C100 32 0 132.3 0 256S100 480 223.5 480c60.6 0 115.5-24.2 155.8-63.4c5-4.9 6.3-12.5 3.1-18.7s-10.1-9.7-17-8.5c-9.8 1.7-19.8 2.6-30.1 2.6c-96.9 0-175.5-78.8-175.5-176c0-65.8 36-123.1 89.3-153.3c6.1-3.5 9.2-10.5 7.7-17.3s-7.3-11.9-14.3-12.5c-6.3-.5-12.6-.8-19-.8z"/>
</symbol>
    <symbol id="sun" viewBox="0 0 512 512">
<path d="M361.5 1.2c5 2.1 8.6 6.6 9.6 11.9L391 121l107.9 19.8c5.3 1 9.8 4.6 11.9 9.6s1.5 10.7-1.6 15.2L446.9 256l62.3 90.3c3.1 4.5 3.7 10.2 1.6 15.2s-6.6 8.6-11.9 9.6L391 391 371.1 498.9c-1 5.3-4.6 9.8-9.6 11.9s-10.7 1.5-15.2-1.6L256 446.9l-90.3 62.3c-4.5 3.1-10.2 3.7-15.2 1.6s-8.6-6.6-9.6-11.9L121 391 13.1 371.1c-5.3-1-9.8-4.6-11.9-9.6s-1.5-10.7 1.6-15.2L65.1 256 2.8 165.7c-3.1-4.5-3.7-10.2-1.6-15.2s6.6-8.6 11.9-9.6L121 121 140.9 13.1c1-5.3 4.6-9.8 9.6-11.9s10.7-1.5 15.2 1.6L256 65.1 346.3 2.8c4.5-3.1 10.2-3.7 15.2-1.6zM160 256a96 96 0 1 1 192 0 96 96 0 1 1 -192 0zm224 0a128 128 0 1 0 -256 0 128 128 0 1 0 256 0z"/>
</symbol>
    <symbol id="arrow-left" viewBox="0 0 448 512"><path d="M438.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-160-160c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L338.8 224 32 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l306.7 0L233.4 393.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l160-160z" transform="translate(448 0) scale(-1 1)"/></symbol>
    </svg>

    <nav class="navbar">
        <div class="wrap navbar-inner">
            <a href="../index.html" class="brand">
                <img src="../assets/images/logo.png" alt="Tunzua Consultancy" width="34" height="34">
                <span class="brand-text">Tunzua<small>Consultancy</small></span>
            </a>
            <div class="nav-actions">
                <button id="themeToggle" class="theme-btn" aria-label="Toggle theme">
                    <svg class="fa-svg" id="sunIcon"><use href="#sun"></use></svg>
                    <svg class="fa-svg hidden" id="moonIcon"><use href="#moon"></use></svg>
                </button>
                <a href="../index.html" class="btn btn-ink btn-back"><svg class="fa-svg"><use href="#arrow-left"></use></svg>Back to Home</a>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="legal-main">
        <div class="wrap legal-wrap">
            <header class="legal-hero">
                <a class="back-link" href="../blog.html"><svg class="fa-svg"><use href="#arrow-left"></use></svg>All insights</a>
                <p class="legal-eyebrow">Daily digest — Tax &amp; GST news</p>
                <h1 class="legal-title">Tax news digest — {esc(date_label)}</h1>
                <p class="legal-updated">{esc(date_long)} · {len(items)} stories</p>
            </header>

            <article class="post-body">
                <p class="post-lead">A quick morning roundup of the tax and GST stories making news in India — tribunal rulings, department updates, due dates and compliance changes. Headlines are curated automatically from public sources; every item links to the original story.</p>

                <h2>The day's stories</h2>
                <ul class="digest-list">
{items_html}                </ul>

                <div class="cta-box">
                    <h3>Need help with any of these?</h3>
                    <p>If a new rule, ruling or deadline affects your business, we'll tell you what it means and what to do about it.</p>
                    <div class="cta-actions">
                        <a class="btn btn-ink" href="../index.html#contact">Contact us</a>
                        <a class="btn" href="https://wa.me/918731831178" target="_blank" rel="noopener">WhatsApp us</a>
                    </div>
                </div>

                <div class="note-box">
                    <p><strong>How this digest works:</strong> stories are selected automatically from public RSS feeds (Taxscan, Economic Times, Moneycontrol) and published with links to the original source. The digest is a news roundup, not professional advice — always check the linked source for details, and ask us if a change affects your business.</p>
                </div>
            </article>
        </div>
    </main>

    <!-- Footer -->
    <footer>
        <div class="wrap">
            <div class="foot-mini">
                <a href="../index.html" class="brand">
                    <img src="../assets/images/logo.png" alt="Tunzua Consultancy" width="34" height="34">
                    <span class="brand-text">Tunzua<small>Consultancy</small></span>
                </a>
                <p>Professional accounting, taxation and business consulting solutions for modern businesses.</p>
            </div>
            <div class="foot-bottom">
                <p>&copy; 2026 Tunzua Consultancy. All rights reserved.</p>
                <div class="legal">
                    <a href="../privacy.html">Privacy Policy</a>
                    <a href="../terms.html">Terms of Service</a>
                    <a href="../index.html">Home</a>
                </div>
            </div>
        </div>
    </footer>

    <script>
        (function () {{
            var savedTheme = localStorage.getItem('theme');
            var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            var isDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

            if (isDark) {{
                document.documentElement.classList.add('dark');
            }}

            var themeToggle = document.getElementById('themeToggle');
            var sunIcon = document.getElementById('sunIcon');
            var moonIcon = document.getElementById('moonIcon');

            function updateIcons() {{
                var dark = document.documentElement.classList.contains('dark');
                sunIcon.classList.toggle('hidden', dark);
                moonIcon.classList.toggle('hidden', !dark);
            }}

            updateIcons();

            themeToggle.addEventListener('click', function () {{
                var dark = document.documentElement.classList.toggle('dark');
                localStorage.setItem('theme', dark ? 'dark' : 'light');
                updateIcons();
            }});
        }})();
    </script>
</body>
</html>
"""
    return body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print what would happen, write nothing")
    parser.add_argument("--max-items", type=int, default=MAX_ITEMS, help="cap digest size")
    parser.add_argument("--email", action="store_true", help="email the digest summary to the firm (best-effort)")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=FRESHNESS_HOURS)
    day_iso = now.strftime("%Y-%m-%d")
    date_label = now.strftime("%a, %d %b %Y")
    date_long = now.strftime("%A, %d %B %Y")

    # Guard: if today's digest file already exists, a previous run this UTC day
    # already published — never duplicate the card/feed/sitemap entries.
    existing_post = os.path.join(ROOT, "blog", f"tax-news-digest-{day_iso}.html")
    if os.path.exists(existing_post):
        print(f"{date_label}: digest already published today — skipping (no duplicates).")
        return 0

    state = load_state()
    published = set(state.get("published", []))
    new_items = []
    seen_links = set(published)
    feed_failures = 0

    for feed in FEEDS:
        try:
            data = fetch(feed["url"])
            for it in parse_items(data):
                if not it["title"] or not it["link"]:
                    continue
                if it["date"] and it["date"] < cutoff:
                    continue  # stale
                if not is_tax_relevant(it):
                    continue
                guid = hashlib.sha1(it["link"].encode()).hexdigest()
                if guid in seen_links:
                    continue
                seen_links.add(guid)
                it["guid"] = guid
                it["source"] = feed["name"]
                new_items.append(it)
        except Exception as exc:
            feed_failures += 1
            print(f"  [warn] feed failed: {feed['name']} — {exc}", file=sys.stderr)

    # Dedup by normalized title (same story in two feeds).
    by_title = {}
    for it in new_items:
        key = re.sub(r"[^a-z0-9]+", "", it["title"].lower())
        by_title.setdefault(key, it)
    new_items = list(by_title.values())

    new_items.sort(key=lambda it: it["date"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    new_items = new_items[: args.max_items]

    if feed_failures == len(FEEDS):
        print("FATAL: all feeds failed — no digest published.")
        return 2

    if len(new_items) < MIN_ITEMS:
        print(f"Quiet news day: only {len(new_items)} fresh relevant item(s) (< {MIN_ITEMS}). Skipping publication.")
        return 0

    print(f"Publishing digest for {date_label} with {len(new_items)} stories:")
    for it in new_items:
        print(f"  - [{categorize(it['title'])}] {it['title'][:75]} ({SOURCE_LABELS.get(it['source'], it['source'])})")

    post_path = os.path.join(ROOT, "blog", f"tax-news-digest-{day_iso}.html")
    post_html = build_post_html(new_items, date_label, day_iso, date_long)

    if args.dry_run:
        print(f"[dry-run] would write: {post_path} ({len(post_html)} bytes)")
        print("[dry-run] would prepend card to blog.html")
        print("[dry-run] would prepend item to feed.xml")
        print("[dry-run] would add URL to sitemap.xml")
        return 0

    write(post_path, post_html)
    update_blog_index(new_items, date_label, day_iso)
    update_feed(new_items, date_label, day_iso)
    update_sitemap(day_iso)
    state["published"] = sorted(seen_links)
    save_state(state)
    print(f"Wrote {post_path}")
    print("Updated blog.html, feed.xml, sitemap.xml, .digest-state.json")
    if args.email:
        send_digest_email(new_items, date_label, day_iso)
    return 0


if __name__ == "__main__":
    sys.exit(main())
