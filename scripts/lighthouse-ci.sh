#!/usr/bin/env bash
# Lighthouse CI gate for the Tunzua static site.
#
# Serves the repo on a local port, runs Lighthouse (mobile emulation, throttled)
# against it, and fails the build if a category score drops below its budget or a
# key metric blows past its cap:
#
#   Scores:  Accessibility >= 95, Best Practices >= 95, SEO >= 95
#   Perf:    score floor >= 50 (catastrophic tripwire) + stable metric caps
#            FCP <= 3.0s, LCP <= 4.5s, CLS <= 0.10
#
# The perf SCORE is deliberately not enforced strictly: on GitHub's 2-core
# runners, Lighthouse's 4x CPU throttle amplifies shared-runner contention into
# huge TBT swings (observed 0ms locally -> 760/1190/2260ms in CI) while FCP/LCP/
# CLS stay identical to local runs. So we gate on those stable metrics instead
# (they catch real regressions like a new render-blocking asset), and keep a low
# score floor only for catastrophic failures.
#
# Budgets are overridable, e.g.:
#   LH_PERF=50 LH_A11Y=100 LH_FCP=3500 LH_LCP=5000 LH_CLS=0.1 bash scripts/lighthouse-ci.sh
#
# Chrome discovery order: $CHROME_PATH, Playwright Chromium, Puppeteer Chromium,
# then the system google-chrome / chromium binary.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8097}"
URL="http://127.0.0.1:$PORT/index.html"
LH_PERF="${LH_PERF:-50}"  # score floor: catastrophic-regression tripwire only (CI TBT noise keeps scores 58-93)
LH_A11Y="${LH_A11Y:-95}"
LH_BP="${LH_BP:-95}"
LH_SEO="${LH_SEO:-95}"
LH_FCP="${LH_FCP:-3000}"  # first-contentful-paint cap, ms (stable in CI: ~2.4s)
LH_LCP="${LH_LCP:-4500}"  # largest-contentful-paint cap, ms (stable in CI: ~3.5s)
LH_CLS="${LH_CLS:-0.10}"  # cumulative-layout-shift cap (stable in CI: ~0.006)

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
python3 - "$OUT" "$LH_PERF" "$LH_A11Y" "$LH_BP" "$LH_SEO" "$LH_FCP" "$LH_LCP" "$LH_CLS" <<'EOF'
import json, sys
out, p_min, a_min, b_min, s_min = sys.argv[1], *map(float, sys.argv[2:6])
fcp_max, lcp_max, cls_max = map(float, sys.argv[6:])
d = json.load(open(out, encoding='utf-8'))
c = d['categories']
a = d['audits']
def score(name):
    return round(c[name]['score'] * 100)
def num(k):
    return a[k].get('numericValue') or 0
scores = {'performance': score('performance'), 'accessibility': score('accessibility'),
          'best-practices': score('best-practices'), 'seo': score('seo')}
fcp, lcp, tbt, cls, si = (num('first-contentful-paint'), num('largest-contentful-paint'),
                          num('total-blocking-time'), a['cumulative-layout-shift'].get('numericValue') or 0,
                          num('speed-index'))
print('lighthouse-ci: PERF %d | A11Y %d | BP %d | SEO %d' % (
    scores['performance'], scores['accessibility'], scores['best-practices'], scores['seo']))
print('  FCP %.1fs | LCP %.1fs | TBT %dms | CLS %.3f | SI %.1fs' % (fcp/1000, lcp/1000, tbt, cls, si/1000))
fails = []
for k, v in (('accessibility', a_min), ('best-practices', b_min), ('seo', s_min)):
    if scores[k] < v:
        fails.append('%s score %d < %d' % (k, scores[k], v))
if scores['performance'] < p_min:
    fails.append('perf score %d < %d (floor)' % (scores['performance'], p_min))
for label, val, cap in (('FCP', fcp, fcp_max), ('LCP', lcp, lcp_max)):
    if val > cap:
        fails.append('%s %.1fs > %.1fs' % (label, val/1000, cap/1000))
if cls > cls_max:
    fails.append('CLS %.3f > %.2f' % (cls, cls_max))
if fails:
    print('lighthouse-ci: FAILED budgets: %s' % '; '.join(fails))
    sys.exit(1)
print('lighthouse-ci: all budgets met')
EOF
