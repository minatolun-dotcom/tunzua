#!/usr/bin/env bash
# Smoke test for the Tunzua static site.
# Serves the repo on a local port and verifies:
#   1. every page and key asset responds 200
#   2. no Font Awesome <i> icon tags remain
#   3. no CDN references remain (cdnjs / cdn.tailwindcss)
#   4. every <use href="#..."> resolves to an embedded <symbol> in the same page
# Usage: bash scripts/smoke-test.sh
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8099}"
python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
SRV=$!
trap 'kill "$SRV" 2>/dev/null || true' EXIT
sleep 1

fail=0
check() {
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$PORT/$1")
  if [ "$code" = "200" ]; then
    echo "ok  : $1"
  else
    echo "FAIL: $1 -> HTTP $code"
    fail=1
  fi
}

for p in \
  index.html privacy.html terms.html \
  tailwind.min.css assets/css/legal.css \
  assets/fa-sprite.svg assets/images/logo.png \
  assets/images/client-0.svg assets/images/client-1.svg \
  assets/images/client-2.svg assets/images/client-3.svg \
  favicon.svg og-image.png robots.txt sitemap.xml; do
  check "$p"
done

# 2. no leftover Font Awesome <i> icons
if grep -rE '<i class="[^"]*fa-' index.html privacy.html terms.html; then
  echo "FAIL: leftover <i> Font Awesome icons found"
  fail=1
else
  echo "ok  : no Font Awesome <i> icons"
fi

# 3. no CDN references
if grep -rE 'cdnjs|cdn\.tailwindcss' index.html privacy.html terms.html; then
  echo "FAIL: CDN references found"
  fail=1
else
  echo "ok  : no CDN references"
fi

# 4. sprite reference integrity
python3 - "$fail" <<'EOF'
import re, sys
ok = True
for page in ('index.html', 'privacy.html', 'terms.html'):
    html = open(page, encoding='utf-8').read()
    uses = set(re.findall(r'<use href="#([a-z0-9-]+)"', html))
    syms = set(re.findall(r'<symbol id="([a-z0-9-]+)"', html))
    missing = uses - syms
    if missing:
        print('FAIL: %s missing symbols %s' % (page, sorted(missing)))
        ok = False
    else:
        print('ok  : %s icon refs (%d) resolve' % (page, len(uses)))
if not ok:
    sys.exit(1)
EOF

if [ "$fail" -ne 0 ]; then
  echo "SMOKE TEST FAILED"
  exit 1
fi
echo "SMOKE TEST PASSED"
