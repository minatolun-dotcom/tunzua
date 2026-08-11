#!/usr/bin/env python3
"""Test scripts/generate-digest.py's update_feed() and update_sitemap().

Runs both functions against fixture feed.xml / sitemap.xml files in a temp
directory (the real repo is never touched) and verifies:

FEED
1. PREPEND — a new <item> lands right after the atom:link marker with the
   right title/link/guid, and existing items are intact.
2. TRIM    — more than MAX_LIST_ITEMS items are capped to the newest
   MAX_LIST_ITEMS (oldest removed, newest stays first).
3. GUARD   — a missing atom:link marker raises RuntimeError.

SITEMAP
4. PREPEND — a new digest <url> entry lands right before </urlset>.
5. TRIM    — more than MAX_LIST_ITEMS digest URLs are capped to the newest
   MAX_LIST_ITEMS (oldest digest URLs removed); evergreen URLs are never
   touched (the trim only matches digest locs).
6. GUARD   — a missing </urlset> raises RuntimeError.

Usage:
    python3 scripts/test-feed-sitemap.py

Exit codes:
    0  all checks passed
    1  a check failed
"""

import importlib.util
import os
import re
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Seed this many items ABOVE the cap so the trim math is explicit.
SEED_OVER = 3

ATOM_MARKER = '    <atom:link href="https://tunzua.com/feed.xml" rel="self" type="application/rss+xml"/>\n'
FEED_ITEM_RE = r"    <item>.*?</item>\n"
SITEMAP_DIGEST_RE = r"  <url>\n    <loc>https://tunzua.com/blog/tax-news-digest-[^<]+</loc>.*?</url>\n"

fails = []


def check(name, cond, extra=""):
    print(("ok  : " if cond else "FAIL: ") + name + ((" | " + extra) if extra else ""))
    if not cond:
        fails.append(name)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_digest", os.path.join(REPO, "scripts", "generate-digest.py")
    )
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)
    return gd


def feed_item(day_iso):
    url = f"https://tunzua.com/blog/tax-news-digest-{day_iso}.html"
    return f'    <item><title>Tax news digest — {day_iso}</title><link>{url}</link><guid>{url}</guid></item>\n'


def build_feed(items):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>\n'
        + ATOM_MARKER
        + "".join(feed_item(d) for d in items)
        + "</channel>\n</rss>\n"
    )


def sitemap_digest_url(day_iso):
    return (
        "  <url>\n"
        f"    <loc>https://tunzua.com/blog/tax-news-digest-{day_iso}.html</loc>\n"
        "  </url>\n"
    )


def sitemap_evergreen_url(slug):
    return (
        "  <url>\n"
        f"    <loc>https://tunzua.com/{slug}</loc>\n"
        "  </url>\n"
    )


def build_sitemap(digest_days_oldest_first, evergreen_slugs):
    urls = "".join(sitemap_digest_url(d) for d in digest_days_oldest_first)
    urls += "".join(sitemap_evergreen_url(s) for s in evergreen_slugs)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls
        + "</urlset>\n"
    )


def test_feed_prepend(gd, tmp):
    src = build_feed(["2026-08-09", "2026-08-08"])
    path = os.path.join(tmp, "feed.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    gd.ROOT = tmp
    items = [{"title": "GST story one", "source": "Taxscan"}, {"title": "ITR story", "source": "Economic Times"}]
    gd.update_feed(items, "Mon, 10 Aug 2026", "2026-08-10")
    out = open(path, encoding="utf-8").read()
    # Generated items are multi-line; the first line after the marker is <item>.
    check("feed: new item right after atom:link marker", out.split(ATOM_MARKER, 1)[1].startswith('    <item>'))
    check("feed: guid/link present", "https://tunzua.com/blog/tax-news-digest-2026-08-10.html" in out)
    check("feed: description built from items", "GST story one (Taxscan)" in out)
    check("feed: old items intact", "2026-08-09" in out and "2026-08-08" in out)
    check("feed: marker not duplicated", out.count(ATOM_MARKER) == 1)


def test_feed_trim(gd, tmp):
    max_items = gd.MAX_LIST_ITEMS
    days = [f"2026-06-{i:02d}" for i in range(max_items + SEED_OVER, 0, -1)]  # newest first
    src = build_feed(days)
    path = os.path.join(tmp, "feed.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    gd.ROOT = tmp
    gd.update_feed([{"title": "New", "source": "Taxscan"}], "Wed, 01 Jul 2026", "2026-07-01")
    out = open(path, encoding="utf-8").read()
    blocks = re.findall(FEED_ITEM_RE, out, flags=re.S)
    check("feed trim: capped at MAX_LIST_ITEMS", len(blocks) == max_items, f"items={len(blocks)} max={max_items}")
    check("feed trim: newest first", out.index("2026-07-01") < out.index("2026-06-" + str(max_items + SEED_OVER).zfill(2)))
    check("feed trim: oldest removed", "2026-06-01" not in out and "2026-06-04" not in out)
    check("feed trim: boundary kept", "2026-06-05" in out)


def test_feed_guard(gd, tmp):
    path = os.path.join(tmp, "feed.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write("<rss><channel></channel></rss>\n")
    gd.ROOT = tmp
    raised = False
    try:
        gd.update_feed([{"title": "x", "source": "Taxscan"}], "d", "2026-08-10")
    except RuntimeError as e:
        raised = "atom:link marker not found" in str(e)
    check("feed guard: missing atom:link raises", raised)


def test_sitemap_prepend(gd, tmp):
    src = build_sitemap(["2026-08-09"], ["privacy.html", "terms.html"])
    path = os.path.join(tmp, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    gd.ROOT = tmp
    gd.update_sitemap("2026-08-10")
    out = open(path, encoding="utf-8").read()
    before_close = out.split("</urlset>", 1)[0]
    check("sitemap: new digest url before </urlset>", before_close.endswith("  </url>\n") and "2026-08-10.html</loc>" in before_close)
    check("sitemap: new loc present", "https://tunzua.com/blog/tax-news-digest-2026-08-10.html" in out)
    check("sitemap: evergreen urls intact", "privacy.html" in out and "terms.html" in out)
    check("sitemap: urlset closed once", out.count("</urlset>") == 1)


def test_sitemap_trim(gd, tmp):
    max_items = gd.MAX_LIST_ITEMS
    # Sitemap digest URLs accumulate OLDEST FIRST (new entries are appended).
    days_oldest_first = [f"2026-01-{i:02d}" for i in range(1, max_items + SEED_OVER + 1)]
    src = build_sitemap(days_oldest_first, ["privacy.html", "terms.html"])
    path = os.path.join(tmp, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    gd.ROOT = tmp
    gd.update_sitemap("2026-08-10")
    out = open(path, encoding="utf-8").read()
    digests = re.findall(SITEMAP_DIGEST_RE, out, flags=re.S)
    check("sitemap trim: digest urls capped at MAX_LIST_ITEMS", len(digests) == max_items, f"digests={len(digests)} max={max_items}")
    check("sitemap trim: oldest digest urls removed", "2026-01-01" not in out and "2026-01-04" not in out)
    check("sitemap trim: boundary kept", "2026-01-05" in out)
    check("sitemap trim: new digest url kept", "2026-08-10" in out)
    check("sitemap trim: evergreen urls untouched", out.count("privacy.html") == 1 and out.count("terms.html") == 1)


def test_sitemap_guard(gd, tmp):
    path = os.path.join(tmp, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write("<urlset></urlset")
    gd.ROOT = tmp
    raised = False
    try:
        gd.update_sitemap("2026-08-10")
    except RuntimeError as e:
        raised = "</urlset> marker not found" in str(e)
    check("sitemap guard: missing </urlset> raises", raised)


def main():
    gd = load_generator()
    tmp = tempfile.mkdtemp(prefix="tunzua-feed-sitemap-test-")
    try:
        test_feed_prepend(gd, tmp)
        test_feed_trim(gd, tmp)
        test_feed_guard(gd, tmp)
        test_sitemap_prepend(gd, tmp)
        test_sitemap_trim(gd, tmp)
        test_sitemap_guard(gd, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("== update_feed / update_sitemap test FAILED ==")
        for f in fails:
            print("  FAIL: " + f)
        return 1
    print("== update_feed / update_sitemap test PASSED ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
