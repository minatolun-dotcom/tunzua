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
import tempfile
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

# Privacy-friendly page-view counter (GoatCounter). Leave empty to disable;
# set to your GoatCounter site code (e.g. "tunzua") to enable per-post counts.
GOATCOUNTER_SITE = os.environ.get("GOATCOUNTER_SITE", "").strip()

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


def post_formsubmit(subject, body, sender="digest@tunzua.com"):
    """Best-effort: POST a plain-text message to FormSubmit /ajax/.

    Never raises — returns True if accepted (HTTP 200 without explicit
    \"success\":false).  The recipient defaults to DIGEST_EMAIL_TO env var
    or info@tunzua.com.
    """
    target = os.environ.get("DIGEST_EMAIL_TO", "info@tunzua.com")
    payload = {
        "email": sender,
        "subject": subject,
        "message": body,
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
            "X-Requested-With": "XMLHttpRequest",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_text = resp.read().decode()
            print(f"[email] FormSubmit HTTP {resp.status}: {body[:120]}")
            return resp.status == 200 and '"success":"false"' not in resp_text
    except Exception as exc:
        print(f"[email] failed (non-fatal): {exc}", file=sys.stderr)
        return False


def send_weekly_recap():
    """Sunday-only: email a recap of the week's digest stories via FormSubmit.

    Reads feed.xml (newest-first), keeps items from the last 7 days, and
    emails the firm a concise list. Never raises; writes nothing.
    Returns True on success.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    try:
        tree = ET.parse(os.path.join(ROOT, "feed.xml"))
    except Exception as exc:
        print(f"[weekly] could not read feed.xml: {exc}", file=sys.stderr)
        return False
    rows = []
    for item in tree.getroot().iter("item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        pub = item.findtext("pubDate") or ""
        dt = None
        try:
            dt = email.utils.parsedate_to_datetime(pub).replace(tzinfo=timezone.utc)
        except Exception:
            pass
        if "digest" not in title.lower():
            continue
        if dt is not None and dt < cutoff:
            continue
        rows.append((dt, title, link))
    rows.sort(key=lambda r: (r[0] is None, r[0] or now), reverse=True)
    if not rows:
        print("[weekly] no digest stories in the last 7 days — skipping email.")
        return False
    lines = [
        f"Weekly tax & GST recap — {len(rows)} stories from the last 7 days:",
        "",
    ]
    for dt, title, link in rows[:25]:
        day = dt.strftime("%a, %d %b") if dt else ""
        lines.append(f"• [{day}] {title}")
        lines.append(f"  {link}")
        lines.append("")
    lines.append("Read all digests: https://tunzua.com/blog.html")
    lines.append("")
    lines.append("— Sent automatically by the Tunzua weekly recap.")
    ok = post_formsubmit("Weekly tax & GST recap", "\n".join(lines), sender="digest@tunzua.com")
    print(f"[weekly] emailed {len(rows)} stories (ok={ok})")
    return ok


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
    return post_formsubmit(
        f"Tax news digest — {date_label}",
        "\n".join(lines),
        sender="digest@tunzua.com",
    )


def _ensure_ttf(woff2_path, cache_dir):
    """Convert a woff2 font to ttf (cached) so PIL can load it."""
    ttf = os.path.join(cache_dir, os.path.basename(woff2_path).replace(".woff2", ".ttf"))
    if os.path.exists(ttf):
        return ttf
    from fontTools.ttLib import TTFont
    font = TTFont(woff2_path)
    font.flavor = None  # decompress woff2 -> ttf
    font.save(ttf)
    return ttf


def make_og_image(items, date_label, day_iso):
    """Render a branded 1200x630 Open Graph card for the digest post.

    Returns the absolute URL of the per-post image
    (https://tunzua.com/blog/og/tax-news-digest-<day>.png) or None if the
    render isn't possible (missing pillow/fonttools/brotli) — callers then
    fall back to the generic og-image.png. Never raises.
    """
    W, H = 1200, 630
    NAVY = (15, 42, 94)          # deep brand navy
    CREAM = (237, 232, 220)      # paper ink (dark theme)
    LIGHT = (157, 185, 232)      # accent light blue
    MARGIN = 70
    out_dir = os.path.join(ROOT, "blog", "og")
    out_path = os.path.join(out_dir, f"tax-news-digest-{day_iso}.png")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        print("[og] pillow unavailable — skipping per-post OG image", file=sys.stderr)
        return None
    try:
        cache = os.path.join(tempfile.gettempdir(), "tunzua-og-fonts")
        os.makedirs(cache, exist_ok=True)
        fraunces = _ensure_ttf(os.path.join(ROOT, "assets", "fonts", "fraunces-latin.woff2"), cache)
        inter600 = _ensure_ttf(os.path.join(ROOT, "assets", "fonts", "inter-600-latin.woff2"), cache)
        inter500 = _ensure_ttf(os.path.join(ROOT, "assets", "fonts", "inter-500-latin.woff2"), cache)
    except Exception as exc:
        print(f"[og] font prep failed: {exc}", file=sys.stderr)
        return None
    try:
        img = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(img)
        f_brand = ImageFont.truetype(inter600, 30)
        f_title = ImageFont.truetype(fraunces, 88)
        f_date = ImageFont.truetype(inter500, 32)
        f_head = ImageFont.truetype(fraunces, 40)
        f_foot = ImageFont.truetype(inter600, 26)
    except Exception as exc:
        print(f"[og] font load failed: {exc}", file=sys.stderr)
        return None

    # Hairline accent + brand mark
    d.rectangle([MARGIN, 52, MARGIN + 56, 54], fill=LIGHT)
    d.text((MARGIN, 74), "TUNZUA CONSULTANCY", font=f_brand, fill=LIGHT)
    # Title
    d.text((MARGIN, 148), "Tax news digest", font=f_title, fill=CREAM)
    # Date + rule
    d.text((MARGIN + 2, 268), date_label, font=f_date, fill=LIGHT)
    d.rectangle([MARGIN, 330, MARGIN + 240, 332], fill=LIGHT)

    # Top story headline, wrapped to 3 lines
    headline = html.unescape(items[0]["title"]) if items else "Your morning tax & GST briefing."
    # The latin subset TTF lacks U+20B9 (rupee sign) — substitute to avoid tofu.
    headline = headline.replace("\u20b9", "Rs.")
    headline = re.sub(r"\s+", " ", headline).strip()
    max_w = W - 2 * MARGIN
    words = headline.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f_head) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    y = 372
    for ln in lines[:3]:
        d.text((MARGIN, y), ln, font=f_head, fill=CREAM)
        y += 56

    # Footer: site + story count
    d.text((MARGIN, H - 78), "tunzua.com", font=f_foot, fill=LIGHT)
    if items:
        d.text((W - MARGIN, H - 78), f"{len(items)} stories", font=f_foot, fill=LIGHT, anchor="ra")

    try:
        os.makedirs(out_dir, exist_ok=True)
        img.save(out_path, "PNG")
    except Exception as exc:
        print(f"[og] save failed: {exc}", file=sys.stderr)
        return None
    print(f"[og] wrote {out_path}")
    return f"https://tunzua.com/blog/og/tax-news-digest-{day_iso}.png"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def update_blog_index(items, date_label, day_iso):
    """Prepend a digest card to blog.html after the opening <section class="blog-list">."""
    # NOTE: digest cards are tagged data-topic="news" for the topic filter on
    # blog.html. Hand-written evergreen posts must carry their own data-topic
    # (vocabulary: gst | income-tax | payroll | bookkeeping | news) or they will
    # only appear under "All". The chips themselves are built dynamically from
    # the data-topics present on the page, so a new topic self-registers with
    # no further edits (same behaviour as the monthly archive template).
    path = os.path.join(ROOT, "blog.html")
    content = read(path)
    card = (
        '                <article class="post-card" data-topic="news">\n'
        f'                    <p class="post-meta"><span>{esc(date_label)}</span><span class="dot"></span><span>News digest</span><span class="dot"></span><span>{len(items)} stories</span></p>\n'
        f'                    <h2><a href="blog/tax-news-digest-{day_iso}.html">Tax news digest — {esc(date_label)}</a></h2>\n'
        f"                    <p>The day's tax and GST stories from Indian news sources, curated and linked at source — tribunal rulings, department updates, due dates and compliance changes.</p>\n"
        f'                    <a class="post-link" href="blog/tax-news-digest-{day_iso}.html">Read digest <svg viewBox="0 0 448 512" fill="currentColor" aria-hidden="true"><path d="M438.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-160-160c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L338.8 224 32 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l306.7 0L233.4 393.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l160-160z"/></svg></a>\n'
        "                </article>\n"
    )
    marker = '            <section class="blog-list" data-folio="02" id="blogList">\n'
    if marker not in content:
        raise RuntimeError("blog.html: <section class=\"blog-list\"> marker not found")
    content = content.replace(marker, marker + card, 1)
    # Keep the footer's "Monthly archive" link pointing at the latest month
    # (it would otherwise go stale when the calendar month rolls over).
    content = re.sub(r"blog/monthly/\d{4}-\d{2}\.html", f"blog/monthly/{day_iso[:7]}.html", content, count=1)
    # Trim: cap only the auto-generated digest cards. Hand-written evergreen
    # posts (due dates, payroll, records…) must NEVER be trimmed — they are the
    # site's permanent SEO content. Digest cards are identified by the
    # tax-news-digest- slug in their href. The [^>]* allows the optional
    # data-topic attribute on cards (regression-tested by
    # scripts/test-blog-index.py).
    digest_blocks = [
        b for b in re.findall(r"<article class=\"post-card\"[^>]*>.*?</article>\n", content, flags=re.S)
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
    og_url = f"https://tunzua.com/blog/og/tax-news-digest-{day_iso}.png"
    item = (
        "    <item>\n"
        f"      <title>Tax news digest — {esc(date_label)}</title>\n"
        f"      <link>https://tunzua.com/blog/tax-news-digest-{day_iso}.html</link>\n"
        f"      <guid>https://tunzua.com/blog/tax-news-digest-{day_iso}.html</guid>\n"
        f"      <pubDate>{rss_date(pub)}</pubDate>\n"
        f"      <description>{esc(descriptions)}</description>\n"
        # RSS 2.0 enclosure + mrss media:content so feed readers display the OG card
        f"      <enclosure url=\"{esc(og_url)}\" length=\"60000\" type=\"image/png\"/>\n"
        f"      <media:content url=\"{esc(og_url)}\" medium=\"image\" type=\"image/png\" width=\"1200\" height=\"630\"/>\n"
        f"      <media:thumbnail url=\"{esc(og_url)}\" width=\"1200\" height=\"630\"/>\n"
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
    og_url = f"https://tunzua.com/blog/og/tax-news-digest-{day_iso}.png"
    entry = (
        "  <url>\n"
        f"    <loc>https://tunzua.com/blog/tax-news-digest-{day_iso}.html</loc>\n"
        f"    <image:image>\n"
        f"      <image:loc>{esc(og_url)}</image:loc>\n"
        f"      <image:title>Tax news digest — {esc(day_iso)}</image:title>\n"
        f"    </image:image>\n"
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


def _related_posts(day_iso, limit=3):
    """Return up to `limit` other posts for a "More insights" block (digests first)."""
    posts = []
    blog_dir = os.path.join(ROOT, "blog")
    for name in sorted(os.listdir(blog_dir)):
        if not name.endswith(".html"):
            continue
        path = os.path.join(blog_dir, name)
        txt = read(path)
        title_m = re.search(r'<h1 class="legal-title">(.*?)</h1>', txt, re.S)
        if not title_m:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", title_m.group(1))).strip()
        eyebrow_m = re.search(r'<p class="legal-eyebrow">(.*?)</p>', txt, re.S)
        eyebrow = html.unescape(re.sub(r"<[^>]+>", "", eyebrow_m.group(1))).strip() if eyebrow_m else "Insights"
        m = re.match(r"tax-news-digest-(\d{4}-\d{2}-\d{2})\.html", name)
        posts.append({
            "name": name, "title": title, "eyebrow": eyebrow,
            "key": m.group(1) if m else "0", "is_digest": bool(m),
        })
    posts = [p for p in posts if p["name"] != f"tax-news-digest-{day_iso}.html"]
    # Digests first (newest first), then evergreen posts in name order.
    posts.sort(key=lambda p: (1 if p["is_digest"] else 0, p["key"]), reverse=True)
    return posts[:limit]


def _related_html(posts):
    """Render the "More insights" related-posts block (empty string if none)."""
    if not posts:
        return ""
    cards = []
    for p in posts:
        cards.append(
            '                        <a class="related-card" href="' + p["name"] + '">\n'
            '                            <span class="related-meta">' + esc(p["eyebrow"]) + '</span>\n'
            '                            <span class="related-title">' + esc(p["title"]) + '</span>\n'
            '                        </a>\n'
        )
    return (
        '\n                <section class="related-posts" aria-label="More insights" data-folio="03">\n'
        '                    <h2>More insights</h2>\n'
        '                    <div class="related-grid">\n'
        + "".join(cards)
        + '                    </div>\n'
        '                </section>\n'
    )


# Daily-digest subscribe box. KEEP IN SYNC with the copy in blog.html and the
# injected copy on blog/*.html (same FormSubmit endpoint, copy and honeypot).
_SUBSCRIBE_HTML = '''
                <section class="subscribe-box" aria-labelledby="subscribeTitle">
                    <span class="crop" aria-hidden="true"></span>
                    <div class="subscribe-copy">
                        <h2 id="subscribeTitle">Get the daily digest by email</h2>
                        <p>Every morning at 8 AM, the day's tax and GST stories — tribunal rulings, due dates and compliance changes — in one short email. No spam, unsubscribe anytime.</p>
                    </div>
                    <form class="subscribe-form" id="subscribeForm" novalidate>
                        <label for="subscribeEmail">Your email address</label>
                        <input type="email" id="subscribeEmail" name="email" placeholder="you@example.com" autocomplete="email" required>
                        <input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
                        <button type="submit" class="btn btn-ink">Subscribe</button>
                    </form>
                    <p class="subscribe-status" id="subscribeStatus" role="status" aria-live="polite"></p>
                </section>
'''

_SUBSCRIBE_JS = '''
    <script>
        (function () {
            var form = document.getElementById('subscribeForm');
            if (!form) return;
            var status = document.getElementById('subscribeStatus');
            var btn = form.querySelector('button[type="submit"]');
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                if (form.querySelector('[name="_gotcha"]').value) return;
                var email = form.querySelector('[name="email"]');
                if (!email.value || !/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email.value)) {
                    status.textContent = 'Please enter a valid email address.';
                    status.className = 'subscribe-status err';
                    email.focus();
                    return;
                }
                btn.disabled = true;
                btn.textContent = 'Subscribing…';
                var data = {
                    email: email.value,
                    subject: 'New digest subscriber: ' + email.value,
                    message: 'Someone subscribed to the daily tax digest.\\n\\nEmail: ' + email.value,
                    _captcha: 'false',
                    _honey: ''
                };
                fetch('https://formsubmit.co/ajax/info@tunzua.com', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                    body: JSON.stringify(data)
                }).then(function (res) {
                    if (!res.ok) throw new Error('bad response');
                    status.textContent = 'You\\'re on the list — the next digest lands in your inbox at 8 AM.';
                    status.className = 'subscribe-status ok';
                    form.reset();
                }).catch(function () {
                    status.textContent = 'Could not subscribe right now — email us at info@tunzua.com and we\\'ll add you.';
                    status.className = 'subscribe-status err';
                }).finally(function () {
                    btn.disabled = false;
                    btn.textContent = 'Subscribe';
                });
            });
        })();
    </script>
'''


def _goatcounter_block():
    """GoatCounter tracking + count-display snippet (empty string when disabled)."""
    site = GOATCOUNTER_SITE
    if not site:
        return ""
    host = f"https://{site}.goatcounter.com"
    return (
        f'\n    <script data-goatcounter="{host}/count" async src="https://gc.zgo.at/count.js"></script>\n'
        '    <script>\n'
        '        (function () {\n'
        "            var el = document.getElementById('view-count');\n"
        '            if (!el) return;\n'
        "            var p = location.pathname.replace(/\\/$/, '');\n"
        "            fetch('" + host + "/counter/' + encodeURIComponent(p) + '.json')\n"
        '                .then(function (r) { if (!r.ok) throw 0; return r.json(); })\n'
        "                .then(function (d) { el.textContent = ' · ' + (d.count || 0) + ' views'; })\n"
        '                .catch(function () { el.remove(); });\n'
        '        })();\n'
        '    </script>\n'
    )


def _ensure_sitemap_monthly(month, day_iso):
    """Idempotently add the monthly archive URL to sitemap.xml."""
    path = os.path.join(ROOT, "sitemap.xml")
    content = read(path)
    url = f"https://tunzua.com/blog/monthly/{month}.html"
    if url in content:
        return
    entry = (
        "  <url>\n"
        f"    <loc>{url}</loc>\n"
        f"    <lastmod>{day_iso}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>0.5</priority>\n"
        "  </url>\n"
    )
    content = content.replace("</urlset>", entry + "</urlset>", 1)
    write(path, content)


def update_monthly_archive(day_iso):
    """Rebuild blog/monthly/YYYY-MM.html listing that month's digests (newest first)."""
    month = day_iso[:7]
    month_num = day_iso[5:7]
    month_label = datetime.strptime(month + "-01", "%Y-%m-%d").strftime("%B %Y")
    cards = []
    total_stories = 0
    blog_dir = os.path.join(ROOT, "blog")
    for name in sorted(os.listdir(blog_dir), reverse=True):
        m = re.match(r"tax-news-digest-(\d{4}-\d{2}-\d{2})\.html$", name)
        if not m or not m.group(1).startswith(month):
            continue
        day = m.group(1)
        txt = read(os.path.join(blog_dir, name))
        title_m = re.search(r'<h1 class="legal-title">(.*?)</h1>', txt, re.S)
        title = html.unescape(re.sub(r"<[^>]+>", "", title_m.group(1))).strip() if title_m else f"Tax news digest — {day}"
        upd_m = re.search(r'<p class="legal-updated">(.*?)</p>', txt, re.S)
        upd = html.unescape(re.sub(r"<[^>]+>", "", upd_m.group(1))).strip() if upd_m else ""
        stories_m = re.search(r"(\d+)\s+stories", upd)
        stories = int(stories_m.group(1)) if stories_m else 0
        total_stories += stories
        label = title.replace("Tax news digest — ", "", 1)
        cards.append(
            '                <article class="post-card" data-topic="news">\n'
            f'                    <p class="post-meta"><span>{esc(label)}</span><span class="dot"></span><span>News digest</span><span class="dot"></span><span>{stories} stories</span></p>\n'
            f'                    <h2><a href="../{name}">{esc(title)}</a></h2>\n'
            "                    <p>The day's tax and GST stories from Indian news sources, curated and linked at source — tribunal rulings, department updates, due dates and compliance changes.</p>\n"
            f'                    <a class="post-link" href="../{name}">Read digest <svg viewBox="0 0 448 512" fill="currentColor" aria-hidden="true"><path d="M438.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-160-160c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L338.8 224 32 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l306.7 0L233.4 393.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l160-160z"/></svg></a>\n'
            "                </article>\n"
        )
    if not cards:
        return
    cards_html = "\n".join(cards)
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/svg+xml" href="../../favicon.svg">
    <link rel="apple-touch-icon" href="../../apple-touch-icon.png">
    <title>Tax news digest — {esc(month_label)} | Tunzua Consultancy</title>
    <meta name="description" content="Every daily tax and GST news digest published by Tunzua Consultancy in {esc(month_label)} — {len(cards)} digests, {total_stories} stories, all linked at source.">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://tunzua.com/blog/monthly/{month}.html">
    <link rel="alternate" type="application/rss+xml" title="Tunzua Consultancy — Insights" href="https://tunzua.com/feed.xml">

    <!-- Open Graph -->
    <meta property="og:title" content="Tax news digest — {esc(month_label)} | Tunzua Consultancy">
    <meta property="og:description" content="Every daily tax and GST news digest from {esc(month_label)} — {len(cards)} digests, {total_stories} stories.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://tunzua.com/blog/monthly/{month}.html">
    <meta property="og:image" content="https://tunzua.com/og-image.png">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Tax news digest — {esc(month_label)} | Tunzua Consultancy">
    <meta name="twitter:description" content="Every daily tax and GST news digest from {esc(month_label)}.">
    <meta name="twitter:image" content="https://tunzua.com/og-image.png">

    <!-- Brand fonts (self-hosted) -->
    <link rel="preload" href="../../assets/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="../../assets/fonts/inter-400-latin.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="stylesheet" href="../../assets/css/fonts.css">
    <link rel="stylesheet" href="../../assets/css/legal.css">
    <link rel="stylesheet" href="../../assets/css/blog.css">

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

    <!-- Browser chrome matches the paper background -->
    <meta name="theme-color" content="#f5f2ea">
    <script>
        (function () {{
            var m = document.querySelector('meta[name="theme-color"]');
            if (!m) return;
            m.setAttribute('content', document.documentElement.classList.contains('dark') ? '#15130f' : '#f5f2ea');
        }})();
    </script>
</head>
<body>
    <a class="skip-link" href="#main-content">Skip to main content</a>

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
            <a href="../../index.html" class="brand">
                <img src="../../assets/images/logo.png" alt="Tunzua Consultancy" width="34" height="34">
                <span class="brand-text">Tunzua<small>Consultancy</small></span>
            </a>
            <span class="sec-counter" id="secCounter" aria-hidden="true">00</span>
            <div class="nav-actions">
                <button id="themeToggle" class="theme-btn" aria-label="Toggle theme">
                    <svg class="fa-svg" id="sunIcon"><use href="#sun"></use></svg>
                    <svg class="fa-svg hidden" id="moonIcon"><use href="#moon"></use></svg>
                </button>
                <a href="../../index.html" class="btn btn-ink btn-back"><svg class="fa-svg"><use href="#arrow-left"></use></svg>Back to Home</a>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="legal-main" id="main-content">
        <div class="wrap legal-wrap">
            <header class="legal-hero" data-ghost="{month_num}" data-folio="01">
                <a class="back-link" href="../blog.html"><svg class="fa-svg"><use href="#arrow-left"></use></svg>All insights</a>
                <p class="legal-eyebrow">Monthly archive</p>
                <h1 class="legal-title">Tax news digest — {esc(month_label)}</h1>
                <p class="legal-updated">{len(cards)} digests · {total_stories} stories</p>
            </header>

{_SUBSCRIBE_HTML}
            <div class="topic-chips monthly-topics" role="group" aria-label="Filter insights by topic"></div>

            <section class="blog-list" data-folio="02">
{cards_html}
            </section>
        </div>
    </main>

    <!-- Footer -->
    <footer>
        <div class="wrap">
            <div class="foot-mini">
                <a href="../../index.html" class="brand">
                    <img src="../../assets/images/logo.png" alt="Tunzua Consultancy" width="34" height="34">
                    <span class="brand-text">Tunzua<small>Consultancy</small></span>
                </a>
                <p>Professional accounting, taxation and business consulting solutions for modern businesses.</p>
            </div>
            <div class="foot-bottom">
                <p>&copy; 2026 Tunzua Consultancy. All rights reserved.</p>
                <div class="legal">
                    <a href="../../privacy.html">Privacy Policy</a>
                    <a href="../../terms.html">Terms of Service</a>
                    <a href="../../blog.html">Insights</a>
                    <a href="../../index.html">Home</a>
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
    <script>
        (function () {{
            var c = document.getElementById('secCounter');
            if (!c) return;
            var secs = document.querySelectorAll('main [data-folio]');
            if (!secs.length) return;
            var ticking = false;
            function upd() {{
                ticking = false;
                var cur = secs[0].getAttribute('data-folio');
                if (window.scrollY >= 2) {{
                    for (var i = secs.length - 1; i >= 0; i--) {{
                        if (secs[i].getBoundingClientRect().top <= window.innerHeight * 0.4) {{
                            cur = secs[i].getAttribute('data-folio');
                            break;
                        }}
                    }}
                }}
                if (c.textContent !== cur) c.textContent = cur;
            }}
            function onScroll() {{ if (!ticking) {{ ticking = true; requestAnimationFrame(upd); }} }}
            window.addEventListener('scroll', onScroll, {{ passive: true }});
            upd();
        }})();
    </script>
    <script>
        (function () {{
            var m = document.querySelector('meta[name="theme-color"]');
            var t = document.getElementById('themeToggle');
            if (!m || !t) return;
            t.addEventListener('click', function () {{
                m.setAttribute('content', document.documentElement.classList.contains('dark') ? '#15130f' : '#f5f2ea');
            }});
        }})();
    </script>
    <script>
        (function () {{
            // Keep trackTopic and the dynamic chip builder in sync with the
            // copies in blog.html (same logic).
            function trackTopic(t) {{
                try {{ if (window.goatcounter && goatcounter.count) goatcounter.count({{ event: true, path: 'topic/' + t }}); }} catch (e) {{}}
                try {{
                    var arr = JSON.parse(localStorage.getItem('tunzua-topic-events') || '[]');
                    arr.push({{ t: t, at: Date.now() }});
                    if (arr.length > 200) arr = arr.slice(-200);
                    localStorage.setItem('tunzua-topic-events', JSON.stringify(arr));
                }} catch (e) {{}}
            }}
            var wrap = document.querySelector('.monthly-topics');
            if (!wrap) return;
            var cards = [].slice.call(document.querySelectorAll('.blog-list .post-card'));
            var order = ['news', 'gst', 'income-tax', 'payroll', 'bookkeeping'];
            var labels = {{ news: 'News', gst: 'GST', 'income-tax': 'Income Tax', payroll: 'Payroll', bookkeeping: 'Bookkeeping', msme: 'MSME', business: 'Business' }};
            var seen = {{}};
            cards.forEach(function (c) {{ var t = c.getAttribute('data-topic'); if (t) seen[t] = true; }});
            // Known topics first (in display order), then any NEW topics found
            // on the cards — a future post self-registers even outside the
            // vocabulary above (fallback label: Title Case).
            var topics = order.filter(function (t) {{ return seen[t]; }});
            Object.keys(seen).sort().forEach(function (t) {{ if (order.indexOf(t) === -1) topics.push(t); }});
            var labelFor = function (t) {{
                if (labels[t]) return labels[t];
                return t.split('-').map(function (w) {{ return w.charAt(0).toUpperCase() + w.slice(1); }}).join(' ');
            }};
            function makeChip(t, label, active) {{
                var b = document.createElement('button');
                b.type = 'button';
                b.className = 'topic-chip' + (active ? ' active' : '');
                b.setAttribute('data-topic', t);
                b.setAttribute('aria-pressed', active ? 'true' : 'false');
                b.textContent = label;
                return b;
            }}
            wrap.appendChild(makeChip('all', 'All', true));
            topics.forEach(function (t) {{ wrap.appendChild(makeChip(t, labelFor(t), false)); }});
            var current = 'all';
            wrap.addEventListener('click', function (e) {{
                var chip = e.target.closest('.topic-chip');
                if (!chip || !wrap.contains(chip)) return;
                current = chip.getAttribute('data-topic');
                [].slice.call(wrap.children).forEach(function (c) {{
                    var on = c === chip;
                    c.classList.toggle('active', on);
                    c.setAttribute('aria-pressed', on ? 'true' : 'false');
                }});
                cards.forEach(function (card) {{
                    var t = (card.getAttribute('data-topic') || '').toLowerCase();
                    var hit = current === 'all' || t.indexOf(current) !== -1;
                    card.style.display = hit ? '' : 'none';
                }});
                trackTopic(current);
            }});
        }})();
    </script>
{_SUBSCRIBE_JS}
</body>
</html>
"""
    month_dir = os.path.join(ROOT, "blog", "monthly")
    os.makedirs(month_dir, exist_ok=True)
    write(os.path.join(month_dir, f"{month}.html"), body)
    _ensure_sitemap_monthly(month, day_iso)


def build_post_html(items, date_label, day_iso, date_long, og_image=None):
    """Generate the digest post HTML file (mirrors the site's post template)."""
    og_image = og_image or "https://tunzua.com/og-image.png"
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

    related_html = _related_html(_related_posts(day_iso, limit=3))
    gc_block = _goatcounter_block()
    # The "·" separator lives INSIDE the span so that a failed count fetch
    # (span removed) never leaves a dangling separator in the meta line.
    # The span is EMPTY: the post-page script owns the leading " · " separator
    # (it sets textContent = ' · ' + count + ' views'), so the meta line never
    # shows a double separator even before/without the count fetch.
    view_span = '<span class="view-count" id="view-count"></span>' if GOATCOUNTER_SITE else ""
    view_suffix = view_span

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
    <meta property="og:image" content="{og_image}">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Tax news digest — {esc(date_label)} | Tunzua Consultancy">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="twitter:image" content="{og_image}">

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

    <!-- Browser chrome matches the paper background -->
    <meta name="theme-color" content="#f5f2ea">
    <script>
        (function () {{
            var m = document.querySelector('meta[name="theme-color"]');
            if (!m) return;
            m.setAttribute('content', document.documentElement.classList.contains('dark') ? '#15130f' : '#f5f2ea');
        }})();
    </script>
</head>
<body>
    <a class="skip-link" href="#main-content">Skip to main content</a>

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

    <div class="scroll-progress" id="scrollProgress"></div>

    <nav class="navbar">
        <div class="wrap navbar-inner">
            <a href="../index.html" class="brand">
                <img src="../assets/images/logo.png" alt="Tunzua Consultancy" width="34" height="34">
                <span class="brand-text">Tunzua<small>Consultancy</small></span>
            </a>
            <span class="sec-counter" id="secCounter" aria-hidden="true">00</span>
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
    <main class="legal-main" id="main-content">
        <div class="wrap legal-wrap">
            <header class="legal-hero" data-ghost="01" data-folio="01">
                <a class="back-link" href="../blog.html"><svg class="fa-svg"><use href="#arrow-left"></use></svg>All insights</a>
                <p class="legal-eyebrow">Daily digest — Tax &amp; GST news</p>
                <h1 class="legal-title">Tax news digest — {esc(date_label)}</h1>
                <p class="legal-updated">{esc(date_long)} · {len(items)} stories{view_suffix}</p>
            </header>

            <article class="post-body" data-folio="02">
                <nav class="toc" id="toc" aria-label="On this page" hidden>
                    <span class="toc-label">On this page</span>
                    <ol></ol>
                </nav>
                <p class="post-lead">A quick morning roundup of the tax and GST stories making news in India — tribunal rulings, department updates, due dates and compliance changes. Headlines are curated automatically from public sources; every item links to the original story.</p>

                <h2>The day's stories</h2>
                <ul class="digest-list">
{items_html}                </ul>

                <div class="cta-box">
                    <span class="crop" aria-hidden="true"></span>
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
{_SUBSCRIBE_HTML}
{related_html}
                <div class="share-row">
                    <span class="share-label">Share this insight</span>
                    <div class="share-btns">
                        <a class="share-btn" data-share="wa" href="#" target="_blank" rel="noopener">WhatsApp</a>
                        <a class="share-btn" data-share="x" href="#" target="_blank" rel="noopener">X</a>
                        <a class="share-btn" data-share="in" href="#" target="_blank" rel="noopener">LinkedIn</a>
                    </div>
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
    <script>
        (function () {{
            var c = document.getElementById('secCounter');
            if (!c) return;
            var secs = document.querySelectorAll('main [data-folio]');
            if (!secs.length) return;
            var ticking = false;
            function upd() {{
                ticking = false;
                var cur = secs[0].getAttribute('data-folio');
                if (window.scrollY >= 2) {{
                    for (var i = secs.length - 1; i >= 0; i--) {{
                        if (secs[i].getBoundingClientRect().top <= window.innerHeight * 0.4) {{
                            cur = secs[i].getAttribute('data-folio');
                            break;
                        }}
                    }}
                }}
                if (c.textContent !== cur) c.textContent = cur;
            }}
            function onScroll() {{ if (!ticking) {{ ticking = true; requestAnimationFrame(upd); }} }}
            window.addEventListener('scroll', onScroll, {{ passive: true }});
            upd();
        }})();
    </script>
{gc_block}
    <script>
        (function () {{
            var m = document.querySelector('meta[name="theme-color"]');
            var t = document.getElementById('themeToggle');
            if (!m || !t) return;
            t.addEventListener('click', function () {{
                m.setAttribute('content', document.documentElement.classList.contains('dark') ? '#15130f' : '#f5f2ea');
            }});
        }})();
    </script>
    <script>
        (function () {{
            var sp = document.getElementById('scrollProgress');
            if (sp) {{
                var spTicking = false;
                function updP() {{
                    spTicking = false;
                    var dh = document.documentElement.scrollHeight - window.innerHeight;
                    sp.style.width = (dh > 0 ? Math.min(window.scrollY / dh, 1) * 100 : 0) + '%';
                }}
                window.addEventListener('scroll', function () {{ if (!spTicking) {{ spTicking = true; requestAnimationFrame(updP); }} }}, {{ passive: true }});
                updP();
            }}
            var toc = document.getElementById('toc');
            if (toc) {{
                var art = document.querySelector('.post-body');
                var hs = art ? [].slice.call(art.children).filter(function (el) {{ return el.tagName === 'H2' && !el.closest('.related-posts') && !el.closest('.toc'); }}) : [];
                if (hs.length >= 2) {{
                    var ol = toc.querySelector('ol');
                    hs.forEach(function (h, i) {{
                        if (!h.id) h.id = 'sec-' + (i + 1);
                        var li = document.createElement('li');
                        var a = document.createElement('a');
                        a.href = '#' + h.id;
                        a.textContent = h.textContent;
                        li.appendChild(a);
                        ol.appendChild(li);
                    }});
                    toc.hidden = false;
                    var links = ol.querySelectorAll('a');
                    var lastId = '';
                    function spy() {{
                        var line = window.innerHeight * 0.12, cur = null;
                        for (var i = 0; i < hs.length; i++) {{
                            var r = hs[i].getBoundingClientRect();
                            if (r.top <= line && r.bottom > line) {{ cur = hs[i].id; break; }}
                        }}
                        if (!cur) {{
                            for (var i = 0; i < hs.length; i++) {{
                                var r = hs[i].getBoundingClientRect();
                                if (r.top <= line) cur = hs[i].id;
                            }}
                        }}
                        if (cur !== lastId) {{
                            lastId = cur;
                            links.forEach(function (a) {{ a.classList.toggle('active', a.getAttribute('href') === '#' + cur); }});
                        }}
                    }}
                    window.addEventListener('scroll', function () {{ requestAnimationFrame(spy); }}, {{ passive: true }});
                    spy();
                }}
            }}
            var share = {{ wa: document.querySelector('.share-btn[data-share="wa"]'), x: document.querySelector('.share-btn[data-share="x"]'), inb: document.querySelector('.share-btn[data-share="in"]') }};
            if (share.wa || share.x || share.inb) {{
                var url = encodeURIComponent(window.location.href);
                var title = encodeURIComponent(document.title.replace(/\\s*\\|\\s*Tunzua Consultancy$/, ''));
                if (share.wa) share.wa.href = 'https://wa.me/?text=' + title + '%20' + url;
                if (share.x) share.x.href = 'https://twitter.com/intent/tweet?text=' + title + '&url=' + url;
                if (share.inb) share.inb.href = 'https://www.linkedin.com/sharing/share-offsite/?url=' + url;
            }}
        }})();
    </script>
{_SUBSCRIBE_JS}
</body>
</html>
"""
    return body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print what would happen, write nothing")
    parser.add_argument("--max-items", type=int, default=MAX_ITEMS, help="cap digest size")
    parser.add_argument("--email", action="store_true", help="email the digest summary to the firm (best-effort)")
    parser.add_argument("--weekly", action="store_true", help="email the weekly recap of digest stories (no files written)")
    args = parser.parse_args()

    if args.weekly:
        send_weekly_recap()
        return 0

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
    og_url = f"https://tunzua.com/blog/og/tax-news-digest-{day_iso}.png"

    if args.dry_run:
        post_html = build_post_html(new_items, date_label, day_iso, date_long, og_url)
        print(f"[dry-run] would write: {post_path} ({len(post_html)} bytes)")
        print(f"[dry-run] would write per-post OG image: blog/og/tax-news-digest-{day_iso}.png")
        print("[dry-run] would prepend card to blog.html")
        print("[dry-run] would prepend item to feed.xml")
        print("[dry-run] would add URL to sitemap.xml")
        print(f"[dry-run] would rebuild monthly archive: blog/monthly/{day_iso[:7]}.html")
        return 0

    og_image = make_og_image(new_items, date_label, day_iso)
    post_html = build_post_html(new_items, date_label, day_iso, date_long, og_image)

    write(post_path, post_html)
    update_blog_index(new_items, date_label, day_iso)
    update_feed(new_items, date_label, day_iso)
    update_sitemap(day_iso)
    update_monthly_archive(day_iso)
    state["published"] = sorted(seen_links)
    save_state(state)
    print(f"Wrote {post_path}")
    print("Updated blog.html, feed.xml, sitemap.xml, monthly archive, .digest-state.json")
    if args.email:
        send_digest_email(new_items, date_label, day_iso)
    return 0


if __name__ == "__main__":
    sys.exit(main())
