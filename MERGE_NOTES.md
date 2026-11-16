# Merge notes for Phase 2 (Telegram + web in one database)

Written 16 November 2026, before Phase 2 starts. **Nothing is built yet.** This file lists
every field of this project's table `web_listings` with the matching field in the sister
project Ollaa-Telegram, and every difference that must be decided before the two are
merged. The sister project was only read (its `database/schema.sql` and `src/` code); nothing
there was changed.

Sister tables used for comparison: `processed_listings` (sale listings, the main table),
`rental_listings` (rents), `listing_units` (several units in one advert),
`developer_projects`, `listing_overrides` (protected hand corrections). Both projects
already share the database `ollaa` and the place codes of the sister project's
`src/locations.py`.

## 1. Field by field

| `web_listings` (this project) | Ollaa-Telegram | Notes |
|---|---|---|
| `id` (serial number) | `processed_listings.id` (text, from the message) | Different id kinds; see §2.1. |
| `content_hash` = sha256(site + web address) | — | The web listing's stable key. |
| `source` (betdelala, ethiopiarealty) | `source_channel` | Same idea: where it came from. |
| `source_url` (phone numbers masked) | — (Telegram has channel + message) | |
| `listing_type` sale / rent | `intent` SALE / RENT / MIXED (+ `listing_class` PURE_SALE, PROMOTIONAL, MIXED, ADVERTISEMENT, …); rents also go to `rental_listings` | §2.4 |
| `property_type` apartment, house, land, building, shop, office, empty | `property_type` APARTMENT, VILLA, CONDOMINIUM, LAND, COMMERCIAL, COMMERCIAL_BUILDING, OFFICE, WAREHOUSE, STUDIO, TOWNHOUSE, SINGLE_ROOM, UNKNOWN (+ `property_subtype`) | §2.5 |
| `price` (always a total, birr) | `sale_price_birr` (bigint) or `rent_price_birr` / `monthly_rent_birr` | §2.6 |
| `price_basis` (total as advertised / calculated from price per m² / per m² only / corrected by hand) | — (rule is inside the pipeline) | §2.6 |
| `price_as_advertised` | — | |
| `price_per_m2` (the advertised per-m² number) | `price_per_sqm_stated` | Same meaning. |
| `stated_price_per_m2`, `price_per_m2_semi`, `price_per_m2_full` | `price_per_sqm_stated`, `price_options`, `cash_price_per_sqm`, `instalment_price_per_sqm` | Telegram splits cash vs instalment; web splits semi vs full finish. |
| — | `price_per_builtup_sqm`, `price_per_plot_sqm` | Web computes nothing yet. |
| — | `cash_price_birr`, `instalment_price_birr` | Web has no such split. |
| `currency` (ETB / USD) | `price_currency` + `price_usd` | Web keeps no USD amount. |
| `price_unusable`, `price_note` | — | Web-only flags (old ethiopiarealty reader). |
| `area_sqm` (one size) | `builtup_sqm` and `plot_sqm` | §2.7 |
| `bedrooms` | `bedrooms` (+ `bathrooms`, `floor_level`) | Web has no bathrooms or floor. |
| `location_code` | `location` | Same codes, plus 3 web-only codes (§2.2). |
| `neighbourhood` | — (name comes from the code) | |
| `sub_city`, `sub_city_unsure` | — (taken from `locations.py` when needed) | §2.2: the sub-cities differ. |
| `city` | `city` | Same values (ADDIS_ABABA, SHEGER_CITY, …). |
| `latitude`, `longitude` | — (from `locations.py`) | |
| `developer` | `developer` (one canonical name, `src/developers.py`) | §2.3 |
| `construction_status` (under construction / probably off-plan / ready, or several joined) | `finish_state` (unfinished / semi_finished / finished / furnished), `listing_status` | §2.8 |
| `construction_progress_pct` | `construction_progress_pct` (integer) | Same meaning. |
| `finish_level` (semi-finished / fully finished / both offered) | `finish_state` | §2.8 |
| `down_payment_pct`, `down_payment_amount` | `down_payment_pct` (integer); `telegram_listings.down_payment_amount` | Web keeps decimals. |
| `instalment_plan` (free text) | `instalment_count`, `instalment_months`, `interest_free` | §2.9 |
| `stage_linked` | `instalments_follow_construction` | Same meaning. |
| `bank_loan` (free text, e.g. "50% bank loan over 20 years") | `bank_loan_pct` (integer), `payment_type` CASH_ONLY / BANK_POSSIBLE / UNKNOWN | §2.9 |
| `handover` (free text: "12 months", "2.5 years", Amharic) | `handover_months` (integer), `handover_date` | §2.9 |
| `discount_schedule` ("100% paid -> 7% off; 75% paid -> 5% off" or "X% discount (terms not stated)") | `discount_schedule` ("100:7; 75:5") | §2.9 |
| `has_payment_terms` | — (Telegram uses `developer_analytics_eligible`) | |
| `ad_text_masked` (phones, e-mails, handles hidden) | `raw_text` (**not masked**) | §2.10 |
| — | `contact_phone`, `contact_username` | §2.10 |
| `property_group` (adverts of one property) | `listing_units` (several units inside one advert) | §2.11 |
| `exact_repeat`, `probable_dup` | Telegram's own dedup (rows removed or excluded) | §2.12 |
| `scraped_at`, `loaded_at`, `reader` | `posted_at`, `created_at`, `listing_age_days`, `listing_status` | Web has no posting date. |
| — | `valuation_eligible`, `sale_analytics_eligible`, `developer_analytics_eligible`, `confidence_json` | §2.13 |
| — | `media_queue`, `has_media` | Phase 3. |

The old web table `web_scraped_listings` (the scraper before W16) is not used any more; it
should be left out of the merge (or retired by the owner after a backup).

## 2. Differences to decide before merging

### 2.1 Ids
Web rows are keyed by `content_hash` (sha256 of site + address); Telegram rows by a text id
from the message. A merged table needs one id that says where a row comes from, e.g.
`web:<hash>` and `tg:<id>`, and the sister project's `listing_overrides` (keyed by
`listing_id`) must accept web ids too.

### 2.2 Place codes and sub-cities — **the biggest difference**
- Both use the sister project's place codes, but this project added three names the list
  lacks: `extra_feyel_bet`, `extra_yetebaberut`, `extra_safari` (`data/extra_places.csv`).
- The owner (land administration) set sub-cities that **differ from the sister project's
  place list**. Telegram today takes the sub-city from `locations.py`; web takes it from
  `data/neighbourhood_subcity.csv` and `data/subcity_rules.csv`. Differences:

| Place | Sister place list | Owner's decision (used for web) |
|---|---|---|
| Ayat, Ayat 49, Ayat Mekdonia | Bole | **Lemi Kura** |
| CMC | Yeka | **Lemi Kura** |
| Summit, Summit 72, Summit Figa, Figa, Figa Mebrat | (none) | **Lemi Kura** |
| Gurd Shola | Yeka | **Lemi Kura** |
| Wesen | (none) | **Lemi Kura** |
| Feyel Bet, Safari, Yetebaberut | not in the list | **Lemi Kura** |
| Gerji | Yeka | **Bole** |
| Bole Arabsa | Bole | **Lemi Kura** |
| Haya Hulet (22) | Bole | Bole (confirmed) |
| Sarbet / Old Airport | Nifas Silk | **Kirkos** |
| Bulgaria | (none) | **Kirkos** |
| Awere | (none) | **Yeka** |
| Wello Sefer, Urael, Atlas and every other "Bole …" name | Bole / (none) | Bole |

  **Decision needed:** one place → sub-city table, owned in one place (most likely the
  sister project's `locations.py`, changed in an Ollaa-Telegram session), so Telegram and
  web listings in Ayat or CMC land in the same sub-city. Until then, sub-city counts from
  the two sources cannot be added together.

### 2.3 Developer names
Telegram has **one canonical name per developer** (`src/developers.py`: "Temer Real
Estate", "Gift Real Estate", "Ayat Real Estate", "MetroHomes", "Jambo Real Estate", …,
with Amharic spellings and the developers' own channels). Web stores the name as found:
"ayat real estate", "AYAT REAL ESTATE", "Ayat share Company", "ጊፍት ሪል ስቴት", "metro
Real Estate / altera Real Estate", "family realestate". **Decision:** the web loader should
use the sister project's `find_developer` (read-only import, as with the place list), so
both sources use the same names.

### 2.4 Sale / rent
Web: `listing_type` sale/rent in one table. Telegram: `intent` SALE/RENT/MIXED, a
`listing_class`, and rents in a separate `rental_listings` table (monthly rent + advance).
Web rents are still guessed partly from the price (1,000–300,000 birr → rent) unless the
page says; Telegram reads the words. **Decision:** map web sale → SALE, rent → RENT
(listing_class PURE_SALE / PURE_RENT), and put web rents into the rental table or keep one
table with intent.

### 2.5 Property types
| Web | Telegram |
|---|---|
| apartment | APARTMENT (or CONDOMINIUM when the advert says condominium; web does not tell them apart) |
| house | VILLA (or TOWNHOUSE) |
| land | LAND |
| building | COMMERCIAL_BUILDING (sometimes a G+N residential building) |
| shop | COMMERCIAL |
| office | OFFICE |
| (empty — 834 rows) | UNKNOWN |
Web has no STUDIO, WAREHOUSE, SINGLE_ROOM. **Decision:** run the sister project's type
reader on the web advert text (it is stored, masked), instead of the web's word list.

### 2.6 Price rules
- Both hold totals in birr, but the rules differ:
  - **Web** (owner, 16 Nov 2026): a "price" of 20,000–400,000 birr on a clear sale advert
    is a price per m²; the total = price per m² × size, marked in `price_basis`.
  - **Telegram**: if a price per m² is given and the total does not fit a home of 15–600 m²,
    the total = price per m² × size.
- Telegram stores bigint (no decimals); web numeric.
- Telegram keeps cash and instalment prices apart (`cash_price_birr`,
  `instalment_price_birr`); web keeps semi- and full-finished prices per m² apart.
- Web has `price_unusable` (709 old ethiopiarealty rows, until re-scraped). These must stay
  out of every price figure after the merge.
**Decision:** one price rule for both, and which price is "the" price when an advert
offers several (cash / instalment / semi / full).

### 2.7 Size
Web has one `area_sqm`; for a flat it is the flat's size, but for a house it may be the
plot, the building, or (seen in the accuracy check) a floor count. Telegram separates
`builtup_sqm` and `plot_sqm`. **Decision:** for web apartments map `area_sqm` →
`builtup_sqm`; for houses and land, read the text again (stored) to tell plot from built-up.

### 2.8 Construction and finish
Web `construction_status` mixes "under construction", "probably off-plan" and "ready" (and
joins them when two adverts of one property disagree); `finish_level` is semi / full.
Telegram `finish_state` mixes construction and finish in one field (unfinished,
semi_finished, finished, furnished). **Decision:** two separate fields in the merged table:
construction stage (off-plan / under construction / ready) and finish (semi / full /
furnished), filled the same way from both sources.

### 2.9 Payment terms
The sister project's `src/payment_terms.py` reads more, and into numbers: instalment count
and months, interest-free, handover in months or a date, a discount schedule as
"100:7; 75:5". Web keeps free text ("12 months", "rest paid በአንድ አመት ከስድስቶር"). **Decision:**
in Phase 2 run the sister project's payment-terms reader on the masked web text and keep
the web fields only as a check.

### 2.10 Phone numbers — **must be decided first**
This project's rule (owner, 13 Nov 2026): never store an unmasked phone number; web text and
addresses are masked. The sister project stores `contact_phone`, `contact_username` and
`raw_text` **unmasked**. A merged database cannot follow both rules. **Decision for the
owner:** mask in the merged tables (keeping contacts, if needed, in one protected table),
or allow contacts for Telegram only.

### 2.11 Several units in one advert
Developer adverts often list several units (e.g. 70 / 85 / 115 / 122 / 165 m², each with its
down payment). Telegram splits them into `listing_units`; web keeps one row per advert
(and joins repeated adverts of one property with `property_group`). **Decision:** use
`listing_units` for web adverts too.

### 2.12 Duplicates between web and Telegram
The W16 check found 87 web listings that look like a property already on Telegram (same
place code, price and size within 5%). After the merge one property must be counted once.
**Decision:** the matching rule (and which copy wins) for cross-source duplicates.

### 2.13 Eligibility flags
Telegram decides `valuation_eligible`, `sale_analytics_eligible`,
`developer_analytics_eligible`; web has none, only `price_unusable`, `exact_repeat`,
`probable_dup`. **Decision:** compute the same flags for web rows with the same rules.

### 2.14 Dates
Web has only `scraped_at` (when we read the page), no posting date; Telegram has
`posted_at` and `listing_age_days`. Estate IQ's recency weighting needs a date: web rows
would use the first time the advert was seen.

## 3. Suggested order for Phase 2 (when the owner starts it)
1. Owner decides §2.10 (phone numbers) and §2.2 (one sub-city table).
2. One id scheme (§2.1), one type list (§2.5), one price rule (§2.6), one size rule (§2.7).
3. Re-read the stored web text with the sister project's readers (developer, payment
   terms, type, intent) instead of this project's own.
4. Cross-source duplicates (§2.12), then eligibility flags (§2.13).
5. Only then build the merged table or view, with a backup and a row count before and after.
