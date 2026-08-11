#!/usr/bin/env python3
"""Test the daily digest generator's publish/skip decisions (offline).

Runs scripts/generate-digest.py's main() against a temp directory with
monkeypatched fetch() returning real RSS XML (parse_items does the actual
parsing) and temp ROOT/STATE_FILE — the real repo is never touched.

Covers the quiet-day path and the other decision branches in main():
1. QUIET DAY  — fewer than MIN_ITEMS fresh relevant items -> "Quiet news day",
   exit 0, NOTHING written (no post, blog.html/feed/sitemap unchanged).
2. FILTERING  — stale items (> FRESHNESS_HOURS old) and job postings are
   dropped before the count, so a feed full of noise stays a quiet day.
3. FATAL      — every feed failing -> exit 2, nothing written.
4. DUPLICATE  — a post already published today -> skip, nothing duplicated.

Usage:
    python3 scripts/test-quiet-day.py

Exit codes:
    0  all checks passed
    1  a check failed
"""

import contextlib
import email.utils
import importlib.util
import io
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKER = '            <section class="blog-list" data-folio="02" id="blogList">\n'
ATOM_MARKER = '    <atom:link href="https://tunzua.com/feed.xml" rel="self" type="application/rss+xml"/>\n'

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


def rss_with(items):
    """items: list of (title, hours_ago, link). Real RSS XML."""
    now = datetime.now(timezone.utc)
    rows = []
    for title, hours_ago, link in items:
        pub = email.utils.format_datetime(now - timedelta(hours=hours_ago), usegmt=True)
        rows.append(f"<item><title>{title}</title><link>{link}</link><pubDate>{pub}</pubDate></item>")
    return ("<rss><channel>" + "".join(rows) + "</channel></rss>").encode()


def write_fixtures(tmp):
    # Reset between sub-tests: an earlier publish run leaves today's post and
    # the state file, which would trip the no-duplicate guard in later tests.
    shutil.rmtree(os.path.join(tmp, "blog"), ignore_errors=True)
    os.makedirs(os.path.join(tmp, "blog"), exist_ok=True)
    blog_html = (
        "<!DOCTYPE html>\n<html>\n<body>\n"
        + MARKER
        + '                <article class="post-card" data-topic="gst">\n'
        + '                    <h2><a href="blog/gst-return-due-dates-2026-27.html">Evergreen</a></h2>\n'
        + "                </article>\n"
        + "            </section>\n"
        + '    <footer><a href="blog/monthly/2026-08.html">Monthly archive</a></footer>\n'
        + "</body>\n</html>\n"
    )
    with open(os.path.join(tmp, "blog.html"), "w", encoding="utf-8") as f:
        f.write(blog_html)
    with open(os.path.join(tmp, "feed.xml"), "w", encoding="utf-8") as f:
        f.write('<rss><channel>\n' + ATOM_MARKER + "</channel></rss>\n")
    with open(os.path.join(tmp, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n')


def run_main(gd, tmp, fetch_impl):
    gd.ROOT = tmp
    gd.STATE_FILE = os.path.join(tmp, "blog", ".digest-state.json")
    gd.fetch = fetch_impl
    old_argv = sys.argv
    sys.argv = ["generate-digest.py"]
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            code = gd.main()
    finally:
        sys.argv = old_argv
    return code, out.getvalue()


def snapshot(tmp):
    """Return a fingerprint of the temp repo state to detect any writes."""
    blog_html = open(os.path.join(tmp, "blog.html"), encoding="utf-8").read()
    feed = open(os.path.join(tmp, "feed.xml"), encoding="utf-8").read()
    sitemap = open(os.path.join(tmp, "sitemap.xml"), encoding="utf-8").read()
    posts = sorted(os.listdir(os.path.join(tmp, "blog")))
    return (blog_html, feed, sitemap, posts)


def test_quiet_day(gd, tmp):
    write_fixtures(tmp)
    before = snapshot(tmp)
    fresh = [("GST rate cut on exports", 2, "https://example.in/a"), ("ITR filing deadline reminder", 3, "https://example.in/b")]
    code, stdout = run_main(gd, tmp, lambda url, timeout=25: rss_with(fresh))
    check("quiet: exit 0", code == 0)
    check("quiet: 'Quiet news day' printed", "Quiet news day" in stdout, stdout.strip().splitlines()[-1] if stdout.strip() else "")
    check("quiet: nothing written", snapshot(tmp) == before)


def test_filtering_makes_quiet(gd, tmp):
    write_fixtures(tmp)
    before = snapshot(tmp)
    # 1 fresh relevant + 3 stale relevant + 2 job postings -> 1 fresh relevant < MIN_ITEMS.
    items = [
        ("GST e-way bill rule change", 2, "https://example.in/fresh"),
        ("Budget reaction from tax experts", 70, "https://example.in/stale1"),
        ("CBDT circular on TDS", 90, "https://example.in/stale2"),
        ("GST Council meet summary", 140, "https://example.in/stale3"),
        ("CA vacancy at Big Four", 2, "https://example.in/job1"),
        ("Hiring: tax consultants wanted", 2, "https://example.in/job2"),
    ]
    code, stdout = run_main(gd, tmp, lambda url, timeout=25: rss_with(items))
    check("filter: only fresh relevant counted", "Quiet news day: only 1 fresh relevant item(s)" in stdout, stdout.strip().splitlines()[-1] if stdout.strip() else "")
    check("filter: nothing written", snapshot(tmp) == before)


def test_publish_threshold(gd, tmp):
    write_fixtures(tmp)
    fresh = [(f"GST compliance news story {i}", 2, f"https://example.in/{i}") for i in range(4)]
    code, stdout = run_main(gd, tmp, lambda url, timeout=25: rss_with(fresh))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    check("threshold: 4 items publish (exit 0)", code == 0)
    check("threshold: post written", os.path.exists(os.path.join(tmp, "blog", f"tax-news-digest-{today}.html")))
    check("threshold: publish message", "Publishing digest" in stdout)


def test_fatal_all_feeds_fail(gd, tmp):
    write_fixtures(tmp)
    before = snapshot(tmp)

    def boom(url, timeout=25):
        raise RuntimeError("network down")

    code, stdout = run_main(gd, tmp, boom)
    check("fatal: all feeds failed -> exit 2", code == 2, f"code={code}")
    check("fatal: FATAL message", "FATAL: all feeds failed" in stdout)
    check("fatal: nothing written", snapshot(tmp) == before)


def test_duplicate_guard(gd, tmp):
    write_fixtures(tmp)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(os.path.join(tmp, "blog", f"tax-news-digest-{today}.html"), "w", encoding="utf-8") as f:
        f.write("<html><body>already published</body></html>")
    fresh = [(f"GST story {i}", 2, f"https://example.in/d{i}") for i in range(4)]
    code, stdout = run_main(gd, tmp, lambda url, timeout=25: rss_with(fresh))
    check("duplicate: skipped with message", code == 0 and "already published today" in stdout)
    blog_html = open(os.path.join(tmp, "blog.html"), encoding="utf-8").read()
    check("duplicate: no card added", blog_html.count(f"tax-news-digest-{today}") == 0)


def test_tax_relevance_helper(gd):
    check("helper: tax item is relevant", gd.is_tax_relevant({"title": "GST input tax credit rules", "link": "https://x.in/1"}))
    check("helper: job posting dropped", not gd.is_tax_relevant({"title": "Vacancy: hire a chartered accountant", "link": "https://x.in/2"}))
    check("helper: plain business story not tax", not gd.is_tax_relevant({"title": "Company launches new product line", "link": "https://x.in/3"}))


def main():
    gd = load_generator()
    tmp = tempfile.mkdtemp(prefix="tunzua-quiet-day-test-")
    try:
        test_quiet_day(gd, tmp)
        test_filtering_makes_quiet(gd, tmp)
        test_publish_threshold(gd, tmp)
        test_fatal_all_feeds_fail(gd, tmp)
        test_duplicate_guard(gd, tmp)
        test_tax_relevance_helper(gd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("== quiet-day / decision test FAILED ==")
        for f in fails:
            print("  FAIL: " + f)
        return 1
    print("== quiet-day / decision test PASSED ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
