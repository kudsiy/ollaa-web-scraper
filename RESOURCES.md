# Ethiopian Real Estate & Auction Resources

This document provides a list of verified websites for gathering real property valuation data in Ethiopia, categorized by their primary function and scrapability.

## 1. Dedicated Real Estate Listing Platforms (Market Value)
These platforms are the primary sources for current market asking prices and property specifications.

| Website | URL | Usefulness | Scrapability |
|---------|-----|------------|--------------|
| **BetDelala** | https://betdelala.com | High | High (Structured listings, detailed features) |
| **Living Ethio** | https://livingethio.com | High | Medium (Detailed property info) |
| **Ethio Real Estates** | https://ethiorealestates.com | High | Medium (Community-driven listings) |
| **Ethiopia Property Centre** | https://ethiopiapropertycentre.com | High | High (Aggregated listings) |
| **Ethiopia Realty** | https://ethiopiarealty.com | High | Medium (High-end properties) |
| **Real Ethio** | https://realethio.com | Medium | Medium (General listings) |

## 2. Tender & Auction Aggregators (Liquidation Value)
Critical for understanding the lower bound of property values ("Forced Sale" values).

| Website | URL | Usefulness | Scrapability |
|---------|-----|------------|--------------|
| **Ethiopian Tender** | https://ethiopiantender.com | Very High | High (Aggregates bank/gov auctions) |
| **Arif Chereta** | https://arifchereta.com | High | High (Dedicated auction portal) |
| **Reporter Tenders** | https://reportertenders.com | High | High (Official digital notices) |
| **Habesha Tender** | https://www.habeshatender.com | High | Medium (Listing aggregator) |
| **Walia Tender** | https://www.waliatender.com | Medium | Medium (Free tender listings) |

## 3. Banking & Institutional Auction Sources (Primary Source)
Most property auctions in Ethiopia are foreclosures by banks. These provide the most accurate legal descriptions.

| Bank / Institution | URL | Notes |
|-------------------|-----|-------|
| **Bank of Abyssinia** | https://www.bankofabyssinia.com | Check "የሐራጅ ሽያጭ ማስታወቂያ" section |
| **Berhan Bank** | https://berhanbanksc.com | Dedicated "Residential House Auctions" page |
| **Abay Bank** | https://www.abaybanksc.com | Official foreclosure notices |
| **Amhara Bank** | https://www.facebook.com/amharabanksc1 | Active auction postings on social media |
| **Development Bank of Ethiopia** | https://dbe.com.et | Large-scale commercial/industrial auctions |

## 4. Specialized Platforms
| Website | URL | Notes |
|---------|-----|-------|
| **Auction Ethiopia** | https://auction.et | Modern online auctioning platform (requires session management) |
| **Delala App** | https://delalaapp.com | Mobile-first broker connections |

## Data Points to Capture for Valuation Moat
For effective property valuation, focus on scraping the following fields:
*   **Property Type:** (Apartment, G+1, Warehouse, Land Only)
*   **Location:** (Sub-city, District/Woreda, Specific neighborhood)
*   **Area:** Size in square meters (sq.m)
*   **Price:** Asking price vs. Starting bid (for auctions)
*   **Status:** (New construction, Renovated, Foreclosure)
*   **Date:** Publication date to track market trends over time.

---
*Verified on May 6, 2024*
