#!/usr/bin/env python3
"""Test scripts/generate-digest.py's update_blog_index() in isolation.

Runs the function against fixture blog.html files in a temp directory (the real
repo is never touched) and verifies the three behaviours that keep blog.html
correct as daily digests accumulate:

1. PREPEND   — a new digest card (data-topic="news") is inserted immediately
   after the <section class="blog-list" ...> marker, with the right href,
   title, story count, and the existing cards (digest + evergreen) intact.
2. ROLLOVER  — the footer's "Monthly archive" link follows the digest's month
   (blog/monthly/YYYY-MM.html), so it never goes stale across month changes.
3. TRIM      — when digest cards exceed MAX_LIST_ITEMS, only the OLDEST digest
   cards are removed (back to MAX_LIST_ITEMS); hand-written evergreen posts
   are never trimmed.
4. GUARD     — a missing blog-list marker raises RuntimeError instead of
   silently corrupting the page.

Usage:
    python3 scripts/test-blog-index.py

Exit codes:
    0  all checks passed
    1  a check failed
"""

import os
import re
import shutil
import sys
import tempfile

from _testutil import check, load_generator, verdict
MARKER = '            <section class="blog-list" data-folio="02" id="blogList">\n'
# Seed this many digests ABOVE MAX_LIST_ITEMS in the trim test (34 total,
# 33 seeded + 1 prepended -> 4 removed, 06-01..06-04 gone, 06-05 kept).
SEED_OVER = 3
# Same pattern the generator uses to recognise cards (with optional attributes,
# e.g. data-topic="news") — duplicated here for counting in assertions.
CARD_RE = r'<article class="post-card"[^>]*>.*?</article>\n'

def digest_card(day_iso, stories=5):
    return (
        '                <article class="post-card" data-topic="news">\n'
        f'                    <p class="post-meta"><span>{day_iso}</span><span class="dot"></span><span>News digest</span><span class="dot"></span><span>{stories} stories</span></p>\n'
        f'                    <h2><a href="blog/tax-news-digest-{day_iso}.html">Tax news digest — {day_iso}</a></h2>\n'
        f"                    <p>The day's tax and GST stories.</p>\n"
        f'                    <a class="post-link" href="blog/tax-news-digest-{day_iso}.html">Read digest</a>\n'
        "                </article>\n"
    )


def evergreen_card(slug, topic="gst"):
    return (
        f'                <article class="post-card" data-topic="{topic}">\n'
        '                    <p class="post-meta"><span>1 Aug 2026</span><span class="dot"></span><span>GST</span></p>\n'
        f'                    <h2><a href="blog/{slug}.html">{slug}</a></h2>\n'
        "                    <p>Evergreen content.</p>\n"
        f'                    <a class="post-link" href="blog/{slug}.html">Read article</a>\n'
        "                </article>\n"
    )


def build_page(digest_days, evergreen_slugs, monthly_link="blog/monthly/2026-07.html"):
    """digest_days must be newest-first (as blog.html is maintained)."""
    cards = "".join(digest_card(d) for d in digest_days)
    cards += "".join(evergreen_card(s) for s in evergreen_slugs)
    footer = f'    <footer>\n        <a href="{monthly_link}">Monthly archive</a>\n    </footer>\n'
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head><title>t</title></head>\n<body>\n"
        + MARKER
        + cards
        + "            </section>\n"
        + footer
        + "</body>\n</html>\n"
    )


def run_update(gd, tmp, source, day_iso="2026-08-10", label="Mon, 10 Aug 2026", stories=4):
    """Write source to tmp/blog.html, run update_blog_index, return the result."""
    path = os.path.join(tmp, "blog.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(source)
    gd.ROOT = tmp
    gd.update_blog_index([{}] * stories, label, day_iso)
    with open(path, encoding="utf-8") as f:
        return f.read()


def count_digest_cards(html):
    return sum(1 for b in re.findall(CARD_RE, html, flags=re.S) if "tax-news-digest-" in b)


def test_prepend(gd, tmp):
    src = build_page(digest_days=["2026-08-09", "2026-08-08"], evergreen_slugs=["gst-return-due-dates-2026-27"])
    out = run_update(gd, tmp, src)
    check("prepend: new card after marker", out.split(MARKER, 1)[1].startswith('                <article class="post-card" data-topic="news">'))
    check("prepend: href + link present", out.count("blog/tax-news-digest-2026-08-10.html") == 2, "hrefs=" + str(out.count("blog/tax-news-digest-2026-08-10.html")))
    check("prepend: title rendered", "Tax news digest — Mon, 10 Aug 2026" in out)
    check("prepend: story count", "4 stories" in out)
    check("prepend: new card is first", out.index("tax-news-digest-2026-08-10") < out.index("tax-news-digest-2026-08-09"))
    check("prepend: old digests kept", "tax-news-digest-2026-08-09.html" in out and "tax-news-digest-2026-08-08.html" in out)
    check("prepend: evergreen kept", "gst-return-due-dates-2026-27" in out)
    check("prepend: marker not duplicated", out.count(MARKER) == 1)


def test_rollover(gd, tmp):
    # blog.html currently has exactly one monthly link (the footer); the
    # generator replaces only the first occurrence (count=1).
    src = build_page(digest_days=["2026-08-09"], evergreen_slugs=[], monthly_link="blog/monthly/2026-07.html")
    out = run_update(gd, tmp, src, day_iso="2026-08-10", label="Mon, 10 Aug 2026")
    check("rollover: footer link now current month", "blog/monthly/2026-08.html" in out)
    check("rollover: old month link gone", "blog/monthly/2026-07.html" not in out)


def test_trim(gd, tmp):
    max_items = gd.MAX_LIST_ITEMS
    # SEED_OVER above the cap, newest first: 33 seeded + 1 prepended = 34,
    # trimmed to MAX (30) -> the 4 oldest (06-01..06-04) are removed.
    days = [f"2026-06-{i:02d}" for i in range(max_items + SEED_OVER, 0, -1)]
    evergreen = ["five-records-every-business-must-keep", "tally-vs-manual-bookkeeping"]
    src = build_page(digest_days=days, evergreen_slugs=evergreen)
    out = run_update(gd, tmp, src, day_iso="2026-07-01", label="Wed, 01 Jul 2026")
    after = count_digest_cards(out)
    check("trim: digest cards capped at MAX_LIST_ITEMS", after == max_items, f"digests={after} max={max_items}")
    blocks = re.findall(CARD_RE, out, flags=re.S)
    evergreens = [b for b in blocks if "tax-news-digest-" not in b]
    check("trim: evergreen posts never trimmed", len(evergreens) == len(evergreen), f"evergreens={len(evergreens)}")
    check("trim: every evergreen slug still present", all(slug in out for slug in evergreen))
    # Oldest four (06-01..06-04) removed; 06-05 kept.
    check("trim: oldest digests removed", "2026-06-01" not in out and "2026-06-04" not in out)
    check("trim: boundary card kept", "2026-06-05" in out)
    check("trim: newest first", out.index("tax-news-digest-2026-07-01") < out.index("tax-news-digest-2026-06-" + str(max_items + SEED_OVER).zfill(2)))
    check("trim: footer still rolled over", "blog/monthly/2026-07.html" in out)


def test_guard(gd, tmp):
    src = "<html><body><h1>no marker</h1></body></html>"
    path = os.path.join(tmp, "blog.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    gd.ROOT = tmp
    raised = False
    try:
        gd.update_blog_index([{}], "Mon, 10 Aug 2026", "2026-08-10")
    except RuntimeError as e:
        raised = "marker not found" in str(e)
    check("guard: missing marker raises RuntimeError", raised)


def main():
    gd = load_generator()
    tmp = tempfile.mkdtemp(prefix="tunzua-blogindex-test-")
    try:
        test_prepend(gd, tmp)
        test_rollover(gd, tmp)
        test_trim(gd, tmp)
        test_guard(gd, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return verdict('update_blog_index test')


if __name__ == "__main__":
    sys.exit(main())
