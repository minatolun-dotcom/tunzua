#!/usr/bin/env bash
# Lighthouse CI gate for the Tunzua static site.
#
# Serves the repo on a local port, runs Lighthouse (mobile emulation, throttled)
# against it, and fails the build if any category score drops below its budget:
#
#   Performance      >= 70   (headless-CI perf is noisy — TBT alone swings 230-760ms
#                             between runs; 70 still catches real regressions like a
#                             new render-blocking asset or LCP doubling)
#   Accessibility    >= 95
#   Best Practices   >= 95
#   SEO              >= 95
#
# Budgets are overridable: LH_PERF=80 LH_A11Y=100 bash scripts/lighthouse-ci.sh
#
# Chrome discovery order: $CHROME_PATH, Playwright Chromium, Puppeteer Chromium,
# then the system google-chrome / chromium binary.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8097}"
URL="http://127.0.0.1:$PORT/index.html"
LH_PERF="${LH_PERF:-70}"
LH_A11Y="${LH_A11Y:-95}"
LH_BP="${LH_BP:-95}"
LH_SEO="${LH_SEO:-95}"

# --- find a Chrome ---
CHROME=""
if [ -n "${CHROME_PATH:-}" ] && [ -x "$CHROME_PATH" ]; then
  CHROME="$CHROME_PATH"
else
  for c in \
    "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux/chrome \
    "$HOME"/.cache/puppeteer/chrome/*/chrome-linux64/chrome \
    "$(command -v google-chrome 2>/dev/null || true)" \
    "$(command -v chromium 2>/dev/null || true)"; do
    if [ -n "$c" ] && [ -x "$c" ]; then CHROME="$c"; break; fi
  done
fi
if [ -z "$CHROME" ]; then
  echo "lighthouse-ci: no Chrome found. Install one with: npx playwright-core install chromium" >&2
  exit 2
fi
echo "lighthouse-ci: using Chrome at $CHROME"

# --- serve the repo ---
python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
SRV=$!
trap 'kill "$SRV" 2>/dev/null || true' EXIT
sleep 1

# --- run Lighthouse ---
OUT="/tmp/tunzua-lh-$$.json"
echo "lighthouse-ci: auditing $URL ..."
npx lighthouse "$URL" \
  --chrome-path="$CHROME" \
  --chrome-flags='--headless=new --no-sandbox --disable-gpu --disable-background-networking --disable-component-update --no-first-run --no-default-browser-check --disable-features=OptimizationHints,MediaRouter' \
  --output=json --output-path="$OUT" --quiet --max-wait-for-load=60000
trap - EXIT
kill "$SRV" 2>/dev/null || true

# --- enforce budgets ---
python3 - "$OUT" "$LH_PERF" "$LH_A11Y" "$LH_BP" "$LH_SEO" <<'EOF'
import json, sys
out, p_min, a_min, b_min, s_min = sys.argv[1], *map(float, sys.argv[2:])
d = json.load(open(out, encoding='utf-8'))
c = d['categories']
a = d['audits']
def score(name):
    return round(c[name]['score'] * 100)
scores = {'performance': score('performance'), 'accessibility': score('accessibility'),
          'best-practices': score('best-practices'), 'seo': score('seo')}
print('lighthouse-ci: PERF %d | A11Y %d | BP %d | SEO %d' % (
    scores['performance'], scores['accessibility'], scores['best-practices'], scores['seo']))
for k in ('first-contentful-paint', 'largest-contentful-paint', 'total-blocking-time',
          'cumulative-layout-shift', 'speed-index'):
    print('  %s: %s' % (k, a[k].get('displayValue')))
budgets = {'performance': p_min, 'accessibility': a_min, 'best-practices': b_min, 'seo': s_min}
fails = [k for k, v in budgets.items() if scores[k] < v]
if fails:
    print('lighthouse-ci: FAILED budgets: %s' % ', '.join(
        '%s (%d < %d)' % (k, scores[k], budgets[k]) for k in fails))
    sys.exit(1)
print('lighthouse-ci: all budgets met')
EOF
