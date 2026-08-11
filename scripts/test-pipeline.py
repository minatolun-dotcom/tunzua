#!/usr/bin/env python3
"""End-to-end pipeline test for the daily digest generator (offline).

Runs scripts/generate-digest.py's main() against a temp directory with
fixture blog.html / feed.xml / sitemap.xml files, monkeypatching fetch() to
return real RSS XML (parse_items still does the actual parsing) and pointing
ROOT/STATE_FILE at the temp dir — the real repo is never read or written.

Verifies one full publish day produces every artifact consistently:
  - the digest post file  blog/tax-news-digest-<today>.html
  - blog.html             new card first + footer monthly-link rollover
  - feed.xml              new <item> with the canonical link/guid
  - sitemap.xml           new digest URL + the monthly-archive URL
  - blog/monthly/<m>.html archive that lists today's digest
  - .digest-state.json    published GUIDs persisted
and that a second run the same day hits the no-duplicate guard.

Usage:
    python3 scripts/test-pipeline.py

Exit codes:
    0  all checks passed
    1  a check failed
"""

import contextlib
import email.utils
import io
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone

from _testutil import check, load_generator, verdict
MARKER = '            <section class="blog-list" data-folio="02" id="blogList">\n'
ATOM_MARKER = '    <atom:link href="https://tunzua.com/feed.xml" rel="self" type="application/rss+xml"/>\n'

def make_rss(n_items, hours=2):
    """Real RSS XML with n_items fresh, tax-relevant items."""
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(n_items):
        dt = now - timedelta(hours=hours)
        pub = email.utils.format_datetime(dt, usegmt=True)
        rows.append(
            f"<item><title>GST e-invoice deadline update {i}</title>"
            f"<link>https://example.in/tax-story-{i}</link>"
            f"<pubDate>{pub}</pubDate></item>"
        )
    return ("<rss><channel>" + "".join(rows) + "</channel></rss>").encode()


def write_fixtures(tmp, seed_month="2026-07"):
    """blog.html / feed.xml / sitemap.xml fixtures + an empty blog/ dir.

    seed_month is the footer's "previous month" link; callers pass a month
    guaranteed to differ from the current one (see test_publish_day).
    """
    os.makedirs(os.path.join(tmp, "blog"), exist_ok=True)
    blog_html = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head><title>t</title></head>\n<body>\n"
        + MARKER
        + '                <article class="post-card" data-topic="news">\n'
        + '                    <h2><a href="blog/tax-news-digest-2026-07-01.html">Old digest</a></h2>\n'
        + "                </article>\n"
        + '                <article class="post-card" data-topic="gst">\n'
        + '                    <h2><a href="blog/gst-return-due-dates-2026-27.html">Evergreen</a></h2>\n'
        + "                </article>\n"
        + "            </section>\n"
        + f'    <footer><a href="blog/monthly/{seed_month}.html">Monthly archive</a></footer>\n'
        + "</body>\n</html>\n"
    )
    with open(os.path.join(tmp, "blog.html"), "w", encoding="utf-8") as f:
        f.write(blog_html)
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>\n'
        + ATOM_MARKER
        + '    <item><title>Old</title><link>https://tunzua.com/blog/tax-news-digest-2026-07-01.html</link><guid>https://tunzua.com/blog/tax-news-digest-2026-07-01.html</guid></item>\n'
        + "</channel>\n</rss>\n"
    )
    with open(os.path.join(tmp, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(feed)
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url>\n    <loc>https://tunzua.com/</loc>\n  </url>\n"
        "  <url>\n    <loc>https://tunzua.com/blog.html</loc>\n  </url>\n"
        "</urlset>\n"
    )
    with open(os.path.join(tmp, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)


def run_main(gd, tmp, rss_bytes):
    """Run main() with fake fetch + temp ROOT/STATE_FILE; returns (code, stdout)."""
    gd.ROOT = tmp
    gd.STATE_FILE = os.path.join(tmp, "blog", ".digest-state.json")
    gd.fetch = lambda url, timeout=25: rss_bytes
    old_argv = sys.argv
    sys.argv = ["generate-digest.py"]
    out = io.StringIO()
    err = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gd.main()
    finally:
        sys.argv = old_argv
    return code, out.getvalue()


def test_publish_day(gd, tmp):
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    month = today[:7]
    # A month ~40 days back can never equal the current month, so the
    # "old link replaced" assertion holds on any date the test ever runs.
    seed_month = (now - timedelta(days=40)).strftime("%Y-%m")
    write_fixtures(tmp, seed_month)
    code, stdout = run_main(gd, tmp, make_rss(4))
    check("pipeline: exits 0", code == 0, f"code={code}")

    post = os.path.join(tmp, "blog", f"tax-news-digest-{today}.html")
    check("pipeline: digest post written", os.path.exists(post))
    if os.path.exists(post):
        body = open(post, encoding="utf-8").read()
        check("pipeline: post has 4 stories", "4 stories" in body)

    blog_html = open(os.path.join(tmp, "blog.html"), encoding="utf-8").read()
    check("pipeline: blog.html lists new digest first", blog_html.index(f"tax-news-digest-{today}") < blog_html.index("tax-news-digest-2026-07-01"))
    check("pipeline: blog.html footer rolled to current month", f"blog/monthly/{month}.html" in blog_html and f"blog/monthly/{seed_month}.html" not in blog_html)
    check("pipeline: evergreen card intact", "gst-return-due-dates-2026-27" in blog_html)

    feed = open(os.path.join(tmp, "feed.xml"), encoding="utf-8").read()
    check("pipeline: feed has new item", f"tax-news-digest-{today}.html" in feed)

    sitemap = open(os.path.join(tmp, "sitemap.xml"), encoding="utf-8").read()
    check("pipeline: sitemap has digest url", f"tax-news-digest-{today}.html" in sitemap)
    check("pipeline: sitemap has monthly archive url", f"blog/monthly/{month}.html" in sitemap)

    monthly = os.path.join(tmp, "blog", "monthly", f"{month}.html")
    check("pipeline: monthly archive built", os.path.exists(monthly))
    if os.path.exists(monthly):
        mbody = open(monthly, encoding="utf-8").read()
        check("pipeline: monthly archive lists today's digest", f"tax-news-digest-{today}.html" in mbody)

    state_path = os.path.join(tmp, "blog", ".digest-state.json")
    check("pipeline: state file persisted", os.path.exists(state_path))
    if os.path.exists(state_path):
        state = json.load(open(state_path, encoding="utf-8"))
        check("pipeline: 4 guids recorded", len(state.get("published", [])) == 4, f"guids={len(state.get('published', []))}")

    # Second run the same UTC day must hit the no-duplicate guard.
    code2, stdout2 = run_main(gd, tmp, make_rss(4))
    check("pipeline: second run skipped (no duplicates)", code2 == 0 and "already published today" in stdout2)
    blog_html2 = open(os.path.join(tmp, "blog.html"), encoding="utf-8").read()
    check("pipeline: no duplicate card on re-run", blog_html2.count(f"tax-news-digest-{today}.html") == 2, f"hrefs={blog_html2.count(f'tax-news-digest-{today}.html')}")


def main():
    gd = load_generator()
    tmp = tempfile.mkdtemp(prefix="tunzua-pipeline-test-")
    try:
        test_publish_day(gd, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return verdict('pipeline test')


if __name__ == "__main__":
    sys.exit(main())
