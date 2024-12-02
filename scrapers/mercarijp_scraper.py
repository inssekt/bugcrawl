import asyncio
from playwright.async_api import async_playwright
import db
from scrapers.base_scraper import BaseScraper  
from bs4 import BeautifulSoup, Comment
import re
import json

MERCARI_SEARCH_URL = "https://buyee.jp/mercari/search?keyword="
MERCARI_EXTRAS = "&category_id=3088&order-sort=desc-created_time&status=on_sale"

class MercariJPScraper(BaseScraper):
    """
    Scraper for Mercari.jp (through Buyee) using Playwright
    """
    async def fetch_listings(self, keyword):
        
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()

            new_listings = []
            url = f"{MERCARI_SEARCH_URL}{keyword}{MERCARI_EXTRAS}"
            await page.goto(url)

            
            await page.wait_for_selector('body')
            html_content = await page.content()

            soup = BeautifulSoup(html_content, 'html.parser')

            script_tag = soup.find("script", text=re.compile(r"var searchData"))
            if script_tag:
                try:
                    match = re.search(r"var searchData\s*=\s*(\{.*?\});", script_tag.string)
                    if match:
                        raw_json = match.group(1)
                        data = json.loads(raw_json)

                        items = data.get("impressions", {}).get("items", [])

                        for item in items:
                            if not db.is_listing_seen(item.get("id")):
                                db.save_listing_to_db(item.get("id"))
                                title = item.get("name", "No Title")
                                price_raw = item.get("price", "No Price")
                                price = f"¥ {price_raw}"
                                link = f"https://buyee.jp.mercari/item/{item.get('id')}"
                                image = f"https://static.mercdn.net/item/detail/orig/photos/{item.get('id')}_1.jpg"
                                print(f"Title: {title}, Price: {price}")
                                new_listings.append({
                                    "title": title,
                                    "link": link,
                                    "image": image,
                                    "price": price,
                                    "brand": ""
                                })
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
            else:
                print("No matching script tag found.")

            await browser.close()
            return new_listings