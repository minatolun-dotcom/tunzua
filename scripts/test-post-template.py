#!/usr/bin/env python3
"""Test scripts/generate-digest.py's build_post_html() post template.

Renders the digest post into a string (no files are written) and verifies:

1. HEAD      — <title>, canonical URL, og:type=article, og:image (custom vs
   generic fallback), Twitter meta, and a valid JSON-LD BlogPosting block.
2. BODY      — every story becomes a <li class="digest-item"> with a linked,
   escaped headline, its SOURCE_LABELS source and a categorize() label; the
   CTA box, the "How this digest works" note, the sticky TOC and the share row
   (WhatsApp / X / LinkedIn) are all present.
3. ESCAPING  — HTML metacharacters in titles/links/descriptions are escaped in
   both the HTML output and the JSON-LD block; long first titles truncate the
   meta description with an ellipsis.
4. VIEWCOUNT — with GOATCOUNTER_SITE set the tracker script + id="view-count"
   span are emitted; with it empty both are absent.
5. RELATED   — with other posts in blog/, a "More insights" grid is emitted
   (digests first, today's post excluded); with no other posts, none.
6. SHARE     — the share row carries the three data-share buttons.

Usage:
    python3 scripts/test-post-template.py

Exit codes:
    0  all checks passed
    1  a check failed
"""

import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

from _testutil import check, load_generator, verdict

DAY_ISO = "2026-08-10"
POST_URL = f"https://tunzua.com/blog/tax-news-digest-{DAY_ISO}.html"


def make_items():
    dt = datetime(2026, 8, 10, 2, 30, tzinfo=timezone.utc)
    return [
        {
            "title": "GST e-invoice deadline \"extended\" & confirmed for 30 Sep with very long explanatory text that keeps going well beyond ninety six characters to force truncation of the meta description",
            "link": "https://taxscan.in/gst-einvoice?src=rss&tab=1",
            "source": "Taxscan — Income Tax",
            "date": dt,
        },
        {"title": "ITR filing utility <b>launched</b> for FY 2026-27", "link": "https://taxguru.in/itr-utility", "source": "TaxGuru — Tax & GST news", "date": dt},
        {"title": "CBDT updates TDS rates for AY 2026-27", "link": "https://economictimes.indiatimes.com/cbdt-tds", "source": "Economic Times — Tax", "date": dt},
    ]


def fake_post(title, eyebrow):
    return (
        "<!DOCTYPE html>\n<html>\n<body>\n"
        f'<p class="legal-eyebrow">{eyebrow}</p>\n'
        f'<h1 class="legal-title">{title}</h1>\n'
        "</body>\n</html>\n"
    )


def seed_related_posts(tmp):
    blog_dir = os.path.join(tmp, "blog")
    os.makedirs(blog_dir, exist_ok=True)
    posts = {
        "tax-news-digest-2026-08-09.html": ("Tax news digest — Sun, 09 Aug 2026", "Daily digest"),
        "tax-news-digest-2026-08-08.html": ("Tax news digest — Sat, 08 Aug 2026", "Daily digest"),
        "tally-vs-manual-bookkeeping.html": ("Tally Prime vs. manual bookkeeping", "Bookkeeping"),
        "when-does-your-business-need-gst-registration.html": ("When does your business need GST registration?", "GST"),
    }
    for name, (title, eyebrow) in posts.items():
        with open(os.path.join(blog_dir, name), "w", encoding="utf-8") as f:
            f.write(fake_post(title, eyebrow))


def test_template(gd, tmp):
    items = make_items()
    args = (items, "Mon, 10 Aug 2026", DAY_ISO, "Monday, 10 August 2026")

    # --- HEAD + BODY + ESCAPING (no related posts seeded yet) ---
    # _related_posts scans blog/ unconditionally, so the dir must exist.
    os.makedirs(os.path.join(tmp, "blog"), exist_ok=True)
    gd.ROOT = tmp
    out = gd.build_post_html(*args)
    check("template: title", "<title>Tax news digest — Mon, 10 Aug 2026 | Tunzua Consultancy</title>" in out)
    check("template: canonical", f'<link rel="canonical" href="{POST_URL}">' in out)
    check("template: og:type article", 'property="og:type" content="article"' in out)
    check("template: og:image falls back to generic", 'property="og:image" content="https://tunzua.com/og-image.png"' in out)
    custom = "https://tunzua.com/blog/og/tax-news-digest-2026-08-10.png"
    out_custom = gd.build_post_html(*args, og_image=custom)
    check("template: custom og:image used", f'property="og:image" content="{custom}"' in out_custom)
    check("template: twitter card", 'name="twitter:card" content="summary_large_image"' in out)

    # Guarded find(): a template regression produces a clean FAIL line rather
    # than a ValueError traceback.
    jsonld_start = out.find('"@type": "BlogPosting"')
    jsonld_end = out.find("</script>", jsonld_start) if jsonld_start != -1 else -1
    jsonld = out[jsonld_start:jsonld_end] if jsonld_start != -1 and jsonld_end != -1 else ""
    check("template: JSON-LD present", bool(jsonld))
    check("template: JSON-LD headline + date", '"headline": "Tax news digest — Mon, 10 Aug 2026"' in jsonld and '"datePublished": "2026-08-10"' in jsonld)
    check("template: JSON-LD escapes quotes/amps", '&quot;extended&quot;' in jsonld and '&amp;' in jsonld)

    check("template: description truncated with ellipsis", "…" in out)
    check("template: 3 digest items", out.count('<li class="digest-item">') == 3)
    check("template: item link escaped + target", 'href="https://taxscan.in/gst-einvoice?src=rss&amp;tab=1" target="_blank" rel="noopener"' in out)
    check("template: <b> escaped in headline", "&lt;b&gt;launched&lt;/b&gt;" in out and "<b>launched</b>" not in out)
    check("template: source labels rendered", "Taxscan" in out and "TaxGuru" in out)
    check("template: category labels rendered", "Income Tax" in out and "GST" in out)
    check("template: CTA + WhatsApp", "https://wa.me/918731831178" in out and "Contact us" in out)
    check("template: how-this-works note", "How this digest works" in out)
    check("template: sticky TOC", '<nav class="toc" id="toc" aria-label="On this page"' in out)
    check("template: share row has wa/x/in", out.count('class="share-btn"') == 3 and 'data-share="wa"' in out and 'data-share="x"' in out and 'data-share="in"' in out)

    # --- VIEW-COUNT GATING ---
    gd.GOATCOUNTER_SITE = "tunzua"
    out_on = gd.build_post_html(*args)
    check("viewcount: tracker emitted when enabled", 'data-goatcounter="https://tunzua.goatcounter.com/count"' in out_on and "gc.zgo.at/count.js" in out_on)
    check("viewcount: view-count span emitted", 'id="view-count"' in out_on)
    gd.GOATCOUNTER_SITE = ""
    out_off = gd.build_post_html(*args)
    check("viewcount: absent when disabled", 'id="view-count"' not in out_off and "gc.zgo.at" not in out_off)

    # --- RELATED POSTS ---
    seed_related_posts(tmp)
    out_rel = gd.build_post_html(*args)
    rel_start = out_rel.find('class="related-posts"')
    check("related: block present with posts", rel_start != -1)
    rel = out_rel[rel_start:] if rel_start != -1 else ""
    check("related: capped at 3 cards", rel.count("related-card") == 3)
    check("related: digests first", rel.index("tax-news-digest-2026-08-09") < rel.index("tally-vs-manual-bookkeeping"))
    check("related: today's post excluded", "tax-news-digest-2026-08-10" not in rel)
    for name in os.listdir(os.path.join(tmp, "blog")):
        os.remove(os.path.join(tmp, "blog", name))
    out_no = gd.build_post_html(*args)
    # The string 'related-posts' also appears in the TOC JS, so assert on the
    # section MARKUP, which only exists when related posts are present.
    check("related: absent with no posts", 'class="related-posts" aria-label="More insights"' not in out_no)


def main():
    gd = load_generator()
    tmp = tempfile.mkdtemp(prefix="tunzua-post-template-test-")
    try:
        test_template(gd, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return verdict("build_post_html template test")


if __name__ == "__main__":
    sys.exit(main())
