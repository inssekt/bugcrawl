import asyncio
from playwright.async_api import async_playwright
import db
from dotenv import load_dotenv
import os
from scrapers.base_scraper import BaseScraper 

DEPOP_SEARCH_URL = "https://www.depop.com/search/?q="
DEPOP_EXTRAS = "&sort=newlyListed"

load_dotenv()

class DepopScraper(BaseScraper):
    async def fetch_listings(self, keyword):
        """
        Fetch listings from Depop for the given keyword using Playwright.
        This method uses Playwright for async scraping.
        """
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()

            new_listings = []
            url = f"{DEPOP_SEARCH_URL}{keyword}{DEPOP_EXTRAS}"
            await page.goto(url)

            try:
                
                await page.wait_for_selector(".styles__ProductCardContainer-sc-ec533c9e-7", timeout=15000)
            except Exception as e:
                print(f"Timeout or error loading page for {keyword}: {e}")
                await browser.close()
                return new_listings

            
            items = await page.query_selector_all("li.styles__ProductCardContainer-sc-ec533c9e-7")
            for item in items:
                try:
                    title_tag = await item.query_selector("a.styles__ProductCard-sc-ec533c9e-4.elBVWz")
                    link = await title_tag.get_attribute('href')
                    if link.endswith('/'):
                        link = f"https://depop.com{link[:-1]}"
                    listing_id = link.split("/")[-1]

                    if not db.is_listing_seen(listing_id):
                        db.save_listing_to_db(listing_id)
                        id_parts = listing_id.split('-')
                        title = " ".join(id_parts[1:])

                        try:
                            image_tag = await item.query_selector("img.sc-htehQK.fmdgqI")
                            srcset = await image_tag.get_attribute('srcset')
                            image_urls = srcset.split(", ")
                            image_url = image_urls[-1].split(" ")[0]
                        except Exception:
                            image_url = "https://via.placeholder.com/150"

                        try:
                            price_element = await item.query_selector('[aria-label="Price"]')
                            price = await price_element.text_content()
                        except Exception:
                            price = "Price not available"

                        new_listings.append({
                            "title": title,
                            "link": link,
                            "image": image_url,
                            "price": price,
                            "brand": "Unknown"  
                        })
                except Exception as e:
                    print(f"Error extracting data: {e}")

            await browser.close()
            return new_listings
