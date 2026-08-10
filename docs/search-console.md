# Google Search Console — tunzua.com

Goal: verify ownership of `tunzua.com` in Search Console, submit the sitemap,
and (optionally) clean up the old Cloudflare Pages property.

## Step 1 — Add the property

1. Go to <https://search.google.com/search-console> and sign in with the Google
   account that manages your business.
2. Click **Add property** → **URL prefix**.
3. Enter `https://tunzua.com/` exactly.

## Step 2 — Verify ownership (pick ONE)

### Option A: HTML file (fastest if you're working with this repo)

1. Choose the **HTML file** verification method — Google shows a token like
   `google4f2a9c1b3d8e0f5a.html`.
2. Send that filename to the AI agent (or drop the file into the repo root
   yourself) and push — GitHub Pages deploys it in ~1 minute.
3. Click **Verify** in Search Console.

### Option B: DNS TXT record (via Cloudflare, no deploy needed)

1. In Cloudflare → **DNS → Records**, add:
   - Type: `TXT`
   - Name: `tunzua.com`
   - Content: the `google-site-verification=...` string Google shows
   - Proxy status: DNS only (grey cloud)
2. Click **Verify** in Search Console. Propagation is usually minutes.

## Step 3 — Submit the sitemap

In the new property, go to **Sitemaps** and submit:

```
sitemap.xml
```

The site also exposes `feed.xml` (RSS) and `robots.txt` (which already points
Google at the sitemap).

## Step 4 — Clean up the old property (optional)

The site previously ran on Cloudflare Pages. If an old
`tunzua.com` property exists in Search Console, you can leave it (harmless) or
remove it under **Settings → Property removal** once the new property is
confirmed showing data.

## Notes

- The per-digest OG images and the monthly archives are already in
  `sitemap.xml` with `<image:image>` tags, so Google will pick them up
  automatically.
- Digests publish daily at 08:00 UTC; the sitemap `lastmod` is updated by the
  generator on each publish.
