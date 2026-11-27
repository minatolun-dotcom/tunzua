# tunzua.com hardening checklist

Post-incident actions after the **Nov 2026 DNS hijack**, where a compromised Cloudflare
account served a wildcard record plus a catch-all redirect to `cloudcheck.click` and wiped
all MX/TXT records. The site itself (this repo, `CNAME`, GitHub Pages) was never modified.

Run through this quarterly, and immediately after any credential scare.

## Cloudflare

- [ ] **2FA on, re-enrolled** since the incident; recovery codes stored offline.
- [ ] **Password unique** to Cloudflare (password manager, not reused anywhere).
- [ ] **Global API Key rotated** — a password change does *not* invalidate it.
- [ ] **Zero API tokens** unless one is actively needed. This site deploys via GitHub Pages
      and never calls the Cloudflare API, so nothing here requires a token.
- [ ] Any token you do create is **scoped to one zone, with an expiry** — never "All zones",
      never account-wide `Full` access.
- [ ] **Members list** contains only you; no pending invitations you did not send.
- [ ] Account email address is one you control and can still log in to.
- [ ] Zone list contains only your domains (attacker-created zones are a common leftover).
- [ ] No unexpected **Workers**, **Workers Routes**, **Bulk Redirects**, or
      **Redirect/Transform Rules**. Only the `www` → apex redirect should exist.
- [ ] **Audit Log** shows no token creation, DNS edit, or login you cannot account for.

### DNS baseline (what "correct" looks like)

| Type | Name | Value | Proxy |
|---|---|---|---|
| A | `@` | `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` | DNS only |
| CNAME | `www` | `minatolun-dotcom.github.io` | **Proxied** — GitHub's cert covers only the apex |
| MX / TXT | `@` | mail provider's records + SPF | DNS only |
| TXT | `_dmarc` | DMARC policy | DNS only |

No wildcard `*` record should exist. A CNAME target is a hostname — never a URL with a path.

## Squarespace Domains (registrar)

- [ ] **2FA on**, password unique, recovery codes stored offline.
- [ ] **Registrar lock** enabled (`clientTransferProhibited` is set — keep it).
- [ ] Nameservers are **`jihoon.ns.cloudflare.com`** and **`olivia.ns.cloudflare.com`**, and
      only those two.
- [ ] Registrant **email address is current** — registrar notices are the first warning of
      transfer attempts.
- [ ] Renewal not left to chance: auto-renew on, card current, domain expiry **2027-09-11**.

## GitHub

- [ ] **2FA on** the account owning `minatolun-dotcom/tunzua`; review active sessions, SSH
      keys, and authorized OAuth apps for anything unfamiliar.
- [ ] Repo **Settings → Pages**: custom domain `tunzua.com`, **Enforce HTTPS** ticked, and a
      current certificate.
- [ ] The only Actions secret is `DIGEST_EMAIL_TO`. Re-issue credentials used by the digest
      workflow if mail was ever routed through the compromised period.
- [ ] Review who has write access to the repo and to the `main` branch.

## Certificate and DNS monitoring

- [ ] **Certificate expiry** — Let's Encrypt certs are 90 days; the previous one lapsed
      because renewal failed while DNS pointed away from GitHub. Check
      `Settings → Pages` monthly, and record the current expiry (Feb 2027) as a calendar
      reminder set ~3 weeks earlier.
- [ ] **Scheduled watchdog** — `.github/workflows/dns-watchdog.yml` runs every 6 hours and
      opens (or comments on) a labelled issue when any check in `scripts/dns-watchdog.py`
      fails: wrong apex A records, a wildcard record, `www` not resolving, missing MX, or an
      HTTPS failure. Run it by hand with `python3 scripts/dns-watchdog.py`.
- [ ] **DNS spot-check** — confirm a random subdomain (e.g. `nope.tunzua.com`) returns
      NXDOMAIN. A response means a wildcard record is back.
- [ ] **MX spot-check** — confirm the mail provider's MX records still resolve; their absence
      breaks the contact form and digest mail silently.

## If it happens again

1. Screenshot the token list and **Audit Log** before deleting anything.
2. Change the Cloudflare password, re-enrol 2FA, revoke all sessions.
3. Revoke every API token and rotate the Global API Key.
4. Check members, zones, Workers, and redirect rules.
5. Only then repair DNS — otherwise a surviving token reverts your work.
