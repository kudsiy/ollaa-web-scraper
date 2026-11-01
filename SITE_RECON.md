# Site reconnaissance (task W16)

Read-only recon of 1 November 2026, for the multi-site plan. For each candidate Ethiopian
property site I fetched, with an honest research user agent, paced a few seconds apart: the
homepage, `robots.txt` and `sitemap.xml`. Nothing was bypassed; a Cloudflare challenge is
recorded as a wall. The advert pages (which hold agents' phone numbers) were **not** fetched
in this recon and are never committed.

**The rule stands: never get past Cloudflare, a CAPTCHA, a login or any other bot
protection, on any site, for any reason.** A walled site is a NO, or an ASK (request the
data from the owner).

## What the marks mean
- **GO** — reachable now, and `robots.txt` allows the listing pages for a general reader.
- **ASK** — reachable, but the site's terms (not its robots file) likely forbid automated
  collection, so the owner should request a data extract instead of scraping.
- **NO** — blocked by a bot wall, down, or not actually a property site.

## The table

| Site | Listings (rough) | Sitemap | Hidden JSON API | Bot wall | robots.txt for us | Best tool | Verdict |
|---|---|---|---|---|---|---|---|
| **betdelala.com** | ~4,076 (sitemap) | yes, flat, 4,076 URLs | `/api/` exists but robots forbids it | no | allows all but `/_next/`, `/api/` | sitemap → listing pages (Next.js; use the data in the page, not `/api/`) | **GO** |
| **realethio.com** | WordPress | yes, `sitemap_index.xml` | WordPress REST maybe | no | allows | sitemap → HTML (WordPress) | **GO** |
| **ethiopiarealty.com** | ~1,280 claimed | yes, `wp-sitemap.xml` | WordPress REST maybe | no | allows | sitemap → HTML (WordPress) | **GO** |
| **livingethio.com** | small | yes, index | WordPress REST maybe | no | allows | sitemap → HTML (WordPress) | **GO** |
| **ethiopianproperties.com** | WordPress | yes, `sitemap_index.xml` | WordPress REST maybe | no | allows | sitemap → HTML (WordPress) | **GO** |
| **www.ethiorealestates.com** | small sitemap + API sitemap | yes, plus a Supabase sitemap | **yes — Supabase JSON backend** | no | allows (old `/realestate/` is dead, blocked) | the Supabase JSON API (cleanest) | **GO** |
| **shegahome.com** | unknown (verify) | yes, index | unknown | no | allows | verify it is a property site and its size, then sitemap → HTML | **GO (verify size)** |
| **ethiopiapropertycentre.com** | ~5,000 | yes, `sitemaps/index.xml` | unknown | **intermittent Cloudflare** | **allows** (even AI bots) except a report path | sitemap → HTML, and stop at the first challenge | **GO (cautious)** |
| **jiji.com.et** | large | no `/sitemap.xml`; has `/llms.txt` | internal API exists | Cloudflare present, let us in this time | allows listing paths | — | **ASK** (check its terms; big sites' terms usually forbid scraping) |
| **engocha.com** | — | blocked | — | **yes, HTTP 403** | says allow, but the wall blocks us | — | **NO** (bot wall) |
| **qefira.com** | — | — | — | — | — | — | **NO** (site down / unreachable) |
| **etrealtor.com.et** | — | — | — | — | — | — | **NO** (unreachable, broken certificate) |
| **afrobet.com** | ? | no | — | no | 5 rules | — | **NO** (name suggests betting; not confirmed a property site — do not touch until confirmed) |
| **zegebeya.com** | sitemap index, 9 | yes | — | no | allows (asks: no AI-training use) | — | **VERIFY** (unclear it is a property site) |
| **temerproperties.com** | one developer's stock | no | — | no | no robots file | Playwright / HTML | **LOW** (a single developer's own new-builds, a different price signal) |
| **et.loozap.com** | classifieds | no root sitemap | — | no | no robots file | Playwright / HTML | **LOW / verify** |

## What this means

- **Start with BetDelala.** It is permissive, reachable, and its sitemap already lists about
  4,076 pages. It was also the second-best source in the old data.
- **Five WordPress sites** (realethio, ethiopiarealty, livingethio, ethiopianproperties, and
  Ethio Real Estates via its Supabase API) are clean, permissive, and easy. Together they
  could add a few thousand adverts.
- **EPC** is the biggest, and its rules allow us, but Cloudflare may challenge automated
  access at any time. We try politely through its sitemap and stop the moment it challenges.
  We never force the challenge.
- **Jiji** is reachable and its robots file is permissive, but its terms of use almost
  certainly forbid automated collection (true of most large marketplaces). So it is an ASK:
  the owner should ask Jiji for a data extract rather than scrape it.

## Still to confirm before a full scrape
- The **terms of use** of each GO site (robots.txt is permission for machines; the terms are
  the legal word). The pilots below read only public listing pages, which robots allows; the
  terms get checked before any full scrape.
- Whether **shegahome** and **zegebeya** are really property-listing sites and how big.
- Whether **afrobet.com** is a property site at all.

## Method order (from the plan)
1. Sitemap → the list of every listing page.
2. The site's own JSON data in the page or a public endpoint its pages read (not a forbidden
   `/api/` path).
3. A slow, polite HTML scraper (Scrapy, with AutoThrottle and robots respected) — **Scrapy
   is not installed yet; installing it needs the owner's approval.**
4. A real browser (Playwright, already installed) only for sites that need JavaScript.
