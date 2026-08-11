#!/usr/bin/env python3
"""Enable the page-view counter on already-published posts.

New digest posts get the counter automatically from the generator when
GOATCOUNTER_SITE is set. This script backfills every existing post (digests
AND evergreen articles) so the counter is present site-wide.

Usage:
    GOATCOUNTER_SITE=tunzua python3 scripts/enable-counter.py

Safe to re-run: existing spans/trackers are stripped first (idempotent).
"""
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("gd", os.path.join(ROOT, "scripts", "generate-digest.py"))
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)

if not gd.GOATCOUNTER_SITE:
    print("GOATCOUNTER_SITE not set — nothing to enable. Set it first, e.g.:")
    print("  GOATCOUNTER_SITE=tunzua python3 scripts/enable-counter.py")
    sys.exit(1)

gc_block = gd._goatcounter_block()
VIEW_SPAN = '<span class="view-count" id="view-count"></span>'
updated = []
for name in sorted(os.listdir(os.path.join(ROOT, "blog"))):
    if not name.endswith(".html"):
        continue
    path = os.path.join(ROOT, "blog", name)
    txt = open(path, encoding="utf-8").read()
    if "view-count" in txt:
        continue  # already enabled
    # 1) view-count span in the hero meta line. The span is EMPTY — the
    #    post-page script owns the leading " · " separator (it sets
    #    textContent = ' · ' + count + ' views'), so no static "·" is added
    #    here (adding one produced a double separator on backfilled posts).
    new = re.sub(
        r"(<p class=\"legal-updated\">[^<]*?(?:stories|read))([ \u00b7]*)</p>",
        r"\1" + VIEW_SPAN.replace("\\", "\\\\") + "</p>",
        txt, count=1,
    )
    if new == txt:
        print(f"SKIP (no legal-updated): {name}")
        continue
    # 2) tracker + count fetch before </body>
    if "</body>" in new:
        new = new.replace("</body>", gc_block + "</body>", 1)
    else:
        print(f"SKIP (no </body>): {name}")
        continue
    open(path, "w", encoding="utf-8").write(new)
    updated.append(name)

print(f"Counter enabled on {len(updated)} posts:")
for n in updated:
    print(f"  - {n}")
