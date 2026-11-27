#!/usr/bin/env python3
"""DNS + TLS watchdog for tunzua.com.

Catches the failure modes from the Nov 2026 hijack, where the Cloudflare zone
gained a wildcard record plus a catch-all redirect and had all MX/TXT records
wiped. Checks, in order:

  1. Apex A records are exactly GitHub Pages' four IPs (no proxy, no hijack).
  2. A random subdomain returns NXDOMAIN (a wildcard record is back if not).
  3. www still resolves (the apex-only GitHub cert relies on Cloudflare for www).
  4. MX records exist (their absence silently breaks contact + digest mail).
  5. https://tunzua.com/ returns 200, keeps its certificate valid, and does not
     redirect off-domain.

Failure exits 1 so the scheduled workflow flags it. Usage: python3 scripts/dns-watchdog.py
"""
import json
import socket
import ssl
import sys
import urllib.parse
import urllib.request

DOMAIN = "tunzua.com"
BASE = f"https://{DOMAIN}"
GITHUB_PAGES_A = {
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153",
}
# Two independent resolvers: one lying resolver should not raise a false alarm.
RESOLVERS = ("https://dns.google/resolve", "https://cloudflare-dns.com/dns-query")

failed = []


def fail(msg):
    print(f"FAIL: {msg}")
    failed.append(msg)


def ok(msg):
    print(f"ok  : {msg}")


def warn(msg):
    print(f"warn: {msg}")


def dns(name, rtype):
    """Return (status, [answers]) from the first resolver that responds."""
    for resolver in RESOLVERS:
        url = f"{resolver}?{urllib.parse.urlencode({'name': name, 'type': rtype})}"
        req = urllib.request.Request(
            url, headers={"Accept": "application/dns-json", "User-Agent": "tunzua-dns-watchdog"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.load(resp)
        except Exception as exc:  # resolver down / blocked: try the next one
            warn(f"resolver {urllib.parse.urlsplit(resolver).netloc} failed ({exc})")
            continue
        answers = [a.get("data", "").rstrip(".") for a in data.get("Answer", [])]
        return data.get("Status"), answers
    return None, []


def check_apex():
    status, answers = dns(DOMAIN, "A")
    if status != 0:
        return fail(f"{DOMAIN} A lookup failed (status={status})")
    got = set(answers)
    if got == GITHUB_PAGES_A:
        ok(f"apex A records are GitHub Pages' four IPs")
    elif any(a.startswith(("104.", "172.")) for a in got):
        fail(f"apex resolves to Cloudflare proxy IPs {sorted(got)} — proxy should be off")
    else:
        fail(f"apex A records wrong: {sorted(got)}")


def check_wildcard():
    probe = "nx-probe-do-not-use-a1b2c3." + DOMAIN
    status, answers = dns(probe, "A")
    if status == 3:  # NXDOMAIN — correct
        ok("no wildcard record (random subdomain is NXDOMAIN)")
    else:
        fail(f"wildcard record is back: {probe} -> {answers or 'status ' + str(status)}")


def check_www():
    status, answers = dns("www." + DOMAIN, "A")
    if status == 0 and answers:
        ok(f"www resolves ({len(answers)} address(es))")
    else:
        fail(f"www does not resolve (status={status}) — www→apex redirect will 404")


def check_mx():
    status, answers = dns(DOMAIN, "MX")
    if status == 0 and answers:
        ok(f"MX present: {', '.join(sorted(answers))}")
    else:
        fail("no MX records — info@tunzua.com cannot receive mail (contact form + digest)")


def check_https():
    req = urllib.request.Request(BASE + "/", headers={"User-Agent": "tunzua-dns-watchdog"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            final = resp.geturl()
            code = resp.status
            body = resp.read(200_000).decode("utf-8", "replace")
    except ssl.SSLError as exc:
        return fail(f"TLS error on {BASE}: {exc}")
    except urllib.error.HTTPError as exc:  # non-2xx still means DNS is pointed somewhere
        return fail(f"{BASE} returned HTTP {exc.code}")
    except Exception as exc:
        return fail(f"{BASE} unreachable: {exc}")

    if code == 200:
        ok(f"{BASE}/ -> 200")
    else:
        fail(f"{BASE}/ -> {code}")

    if urllib.parse.urlsplit(final).hostname != DOMAIN:
        fail(f"redirected off-domain to {final}")
    else:
        ok(f"no off-domain redirect (final URL {final})")

    # Cheap content sanity: a hijack/placeholder page would not carry our title.
    if "Tunzua Consultancy" in body:
        ok("page content is the real site")
    else:
        fail("served page does not contain the site title — wrong content?")


def main():
    for resolver in RESOLVERS:
        host = urllib.parse.urlsplit(resolver).hostname
        try:
            socket.create_connection((host, 443), timeout=10).close()
        except Exception as exc:
            fail(f"cannot reach resolver {host} ({exc}) — checks below may be inconclusive")

    check_apex()
    check_wildcard()
    check_www()
    check_mx()
    check_https()

    if failed:
        print(f"\n== DNS watchdog FAILED ({len(failed)} check(s)) ==")
        return 1
    print("\n== DNS watchdog PASSED ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
