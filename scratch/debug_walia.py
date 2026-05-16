
import asyncio
import logging
import sys
import os
from bs4 import BeautifulSoup

# Add project root to path
sys.path.append(os.getcwd())

from scrapers.tenders.waliatender_scraper import WaliaTenderScraper

async def debug_walia():
    logging.basicConfig(level=logging.INFO)
    scraper = WaliaTenderScraper()
    
    await scraper._init_browser()
    page = await scraper.context.new_page()
    
    print(f"Navigating to {scraper.base_url}...")
    await page.goto(scraper.base_url, wait_until="networkidle", timeout=60000)
    await asyncio.sleep(5) # Give it more time
    
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")
    
    # Let's try to find more general items if the specific ones fail
    tender_items = soup.select(".tender-item, .tender-card, .list-group-item, article, .post, .entry, .card")
    print(f"Found {len(tender_items)} potential tender items")
    
    with open("scratch/walia_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Found {len(tender_items)} potential tender items\n\n")
        
        if tender_items:
            first_item = tender_items[0]
            f.write("\n--- RAW HTML OF FIRST ITEM ---\n")
            f.write(first_item.prettify())
            f.write("\n--- END RAW HTML ---\n\n")
            
            for i, item in enumerate(tender_items):
                listing = scraper._parse_tender_item(item)
                if listing:
                    f.write(f"Item {i}: Title='{listing.title}', Price={listing.price}, Location='{listing.location}'\n")
                else:
                    f.write(f"Item {i}: FAILED TO PARSE\n")
                    f.write(f"Snippet: {item.get_text(strip=True)[:200]}...\n")

    await page.close()
    await scraper._close_browser()

if __name__ == "__main__":
    asyncio.run(debug_walia())
