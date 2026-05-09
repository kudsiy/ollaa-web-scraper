# Ollaa Web Scraper

Ethiopian Property Intelligence Platform - Web Scraping Module

A fully automated scraper system that continuously monitors Ethiopian bank auction, tender, and real estate websites, normalizing all extracted property data into the Ollaa PostgreSQL database.

## Features

- **Bank Auction Scrapers**: AddisList
- **Tender Scrapers**: 2merkato
- **Real Estate Listings**: Engocha
- **PDF Notice Parser**: Extracts property data from auction PDFs
- **Amharic Text Support**: Handles Ethiopian language content
- **ETB Price Extraction**: Normalizes Ethiopian Birr amounts
- **Deduplication**: Hash-based and fuzzy matching to prevent duplicates
- **Scheduled Execution**: Configurable intervals for each scraper group

## Project Structure

```
.
├── scrapers/
│   ├── base_scraper.py          # Abstract base class
│   ├── banks/
│   │   └── addislist_scraper.py  # AddisList Bank Auction
│   ├── tenders/
│   │   └── merkato_scraper.py    # 2merkato Tenders
│   └── listings/
│       └── engocha_scraper.py   # Real estate listings
├── parsers/
│   ├── pdf_parser.py            # PDF notice extraction
│   ├── amharic_parser.py        # Amharic text handling
│   └── price_extractor.py       # ETB amount parsing
├── etl/
│   ├── normalizer.py            # Schema mapping
│   ├── deduplicator.py          # Duplicate detection
│   └── db_writer.py            # PostgreSQL insertion
├── config.py                    # Configuration settings
├── scheduler.py                # Scheduled execution
└── requirements.txt
```

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables for database connection:

```bash
export OLLAADB_HOST=localhost
export OLLAADB_PORT=5432
export OLLAADB_NAME=ollaa
export OLLAADB_USER=postgres
export OLLAADB_PASSWORD=postgres
```

## Usage

### Initialize Database

```bash
python scheduler.py --init-db
```

### Run All Scrapers Once

```bash
python scheduler.py --run-once
```

### Run Specific Scraper

```bash
python scheduler.py --run-once --scraper cbe
```

### Start Scheduled Service

```bash
python scheduler.py
```

### View Statistics

```bash
python scheduler.py --stats
```

## Database Schema

The scraper writes to `web_scraped_listings` table:

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| source_url | TEXT | Source URL |
| source_name | VARCHAR(100) | Bank/tender site name |
| title | TEXT | Listing title |
| description | TEXT | Full description |
| price | DECIMAL(15,2) | Price in ETB |
| price_currency | VARCHAR(10) | Currency (default: ETB) |
| property_type | VARCHAR(50) | apartment/house/land/etc |
| location | VARCHAR(255) | Property location |
| area_sqm | DECIMAL(10,2) | Area in sqm |
| bedrooms | INTEGER | Number of bedrooms |
| bathrooms | INTEGER | Number of bathrooms |
| images | TEXT[] | Array of image URLs |
| posted_date | TIMESTAMP | When listing was posted |
| closing_date | TIMESTAMP | Auction/tender closing |
| listing_type | VARCHAR(20) | auction/rent/sale |
| content_hash | VARCHAR(64) | Unique content hash |
| scraped_at | TIMESTAMP | When scraped |
| raw_data | JSONB | Original scraped data |

## Scheduling

Default intervals:
- Banks: Every 30 minutes
- Tenders: Every 60 minutes
- Listings: Every 15 minutes

## License

Proprietary - Ollaa Property Intelligence Platform