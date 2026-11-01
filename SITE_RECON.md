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

## First pilot: BetDelala (1 November 2026)

50 listing pages, sampled evenly across the 4,067 in the sitemap, read once each, 5 seconds
apart, honest user agent, read-only. No blocks and no errors. Price and currency came from
each page's `ld+json` block; bedrooms, size and place from the page URL and text. Results
saved to a local file only (no phone numbers, no descriptions, never committed).

| Field | Filled | Note |
|---|---|---|
| price | 50/50 (100%) | all in ETB, clean numbers from `ld+json` — none were phone numbers |
| size (m²) | 50/50 (100%) | from the URL and page text |
| location | ~36/50 (~72%) | my quick parser got 30%; a proper read of the page's location field would get most |
| bedrooms | 35/50 (70%) | — |
| price + size + location together | ~30–72% | depends only on the location parser, which is easy to improve |

Of the 50: 38 sale, 12 rent, all ETB. Median sale price per m² about **106,000 ETB**.

This is far better than the old data (where size was known for only 37% of EPC rows), and it
needed no Scrapy, no browser and no blocked API — just the sitemap and the page's own
`ld+json`. It confirms BetDelala as the best first source and that the method works.

## Second pilot: the other GO sites (1 November 2026)

~30 listings each, sampled across each sitemap, read politely (honest UA, 4 s apart,
read-only), stopping at the first block or error. Price/size/location taken from each page's
`ld+json` when present, else visible text and the URL. No site was bypassed.

| Site | Listings in sitemap | Sampled | Price | Size | Location | Currency | Verdict |
|---|---|---|---|---|---|---|---|
| **realethio.com** | 1,728 | 30 | 100% | 100% | 96% | **mostly USD** (29/30) | works well; but priced in US dollars |
| **ethiopiarealty.com** | 1,594 | 30 | 100% | 93% | 60% | ETB | **works well, in birr** |
| **ethiopianproperties.com** | 895 | 30 | 83% | 3%* | 83% | **USD** ($) | good except size (*parser miss, not the site); US dollars |
| **livingethio.com** | 2,009 | 30 | 30% | 0%* | 0%* | mixed | inconclusive — needs a site-specific parser |
| **ethiorealestates.com** | — | — | — | — | — | — | inconclusive — listings are behind its Supabase API, not the plain sitemap |
| **shegahome.com** | 18 | 1 | — | — | — | — | inconclusive — HTTP 500 on the 2nd page; small sitemap |
| **ethiopiapropertycentre.com** | (nested index) | 3 | 0% | 0% | — | — | inconclusive — my crawler found only 3 index pages, not real listings; did **not** challenge this time |

`*` A 0–3% size or location figure here is my quick general parser missing a site's layout,
not the site lacking the data. Those sites need a short site-specific parser before a real
verdict.

### What this tells us
- **The method clearly works** on BetDelala, realethio and ethiopiarealty: near-complete
  price and size straight from structured data, no blocks, no bypass.
- **Currency is the catch for the thesis.** realethio and ethiopianproperties quote mostly
  **US dollars**. Ollaa-Telegram's hedonic model uses birr only and drops USD listings, so
  the directly comparable birr inventory is **BetDelala + ethiopiarealty** (both ETB), plus
  the ETB share of the others. USD listings can still be kept for reference or converted at
  a stated rate, but that is the owner's call.
- **Four sites are inconclusive**, not dead: livingethio and ethiopianproperties need a
  small size/price parser for their layout; Ethio Real Estates needs its Supabase JSON
  endpoint (cleaner anyway); shegahome looks small and returned a server error; EPC needs
  its nested sitemap followed properly (and still must be treated as GO-cautious).

### Rough reachable birr inventory (very approximate)
BetDelala ~4,067 (sale + rent) and ethiopiarealty ~1,594, both in ETB, are the solid core —
already several times the 154 usable adverts in the old Google Sheet. realethio (~1,728) and
ethiopianproperties (~895) add more if USD is acceptable or converted.

## Full scrape of the birr sites — progress (owner approved 1 November 2026)

A resumable, capped, polite scraper (`scrape_site.py`): honest UA, random 3–6 s pauses,
read-only, stops at the first block or error, a daily cap of 500 per site, and a done-log so
each run continues where the last stopped. Structured fields only go to a local CSV per site
(`saved_pages/<site>/full.csv`); no phone numbers, no descriptions, never committed.

First batch, 1 November 2026 (no blocks, no errors):

| Site | Done / total | Price | Size | Location | Bedrooms |
|---|---|---|---|---|---|
| betdelala | 200 / 4,059 | 100% | 97% | 98% (raw text, needs tidying into sub-city codes) | 78% |
| ethiopiarealty | 200 / 1,594 | 100% | 97% | 22% (its sub-city is in the page text, not the URL) | 32% |

Notes:
- The scrape is **not finished**: ~3,859 BetDelala and ~1,394 ethiopiarealty pages remain, to
  be read over later runs within the daily cap (a few days at 500/site/day; the cap can be
  raised if the owner wants).
- **Location still needs normalizing.** BetDelala's location text is messy
  ("… 6 bedroom 250 sqm lebu addis ababa") and ethiopiarealty's is mostly missing from the
  URL. Both get resolved to Ollaa-Telegram's sub-city codes when the data is mapped and
  loaded into the database (the next step, step 4) — that step reads the listing text with
  the same `locations.py` rules and will recover ethiopiarealty's places too.
- **Currency** is ETB for both, as expected.

## Method order (from the plan)
1. Sitemap → the list of every listing page.
2. The site's own JSON data in the page or a public endpoint its pages read (not a forbidden
   `/api/` path).
3. A slow, polite HTML scraper (Scrapy, with AutoThrottle and robots respected) — **Scrapy
   is not installed yet; installing it needs the owner's approval.**
4. A real browser (Playwright, already installed) only for sites that need JavaScript.
