import asyncio
from playwright.async_api import async_playwright
import db
from scrapers.base_scraper import BaseScraper  

VINTED_SEARCH_URL = "https://www.vinted.co.uk/catalog?search_text="
VINTED_EXTRAS = "&order=newest_first&page=1"

class VintedScraper(BaseScraper):
    async def fetch_listings(self, keyword):
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()

            new_listings = []
            url = f"{VINTED_SEARCH_URL}{keyword}{VINTED_EXTRAS}"
            await page.goto(url)

            try:
                await page.wait_for_selector('.feed-grid__item', timeout=15000)  
            except Exception as e:
                print(f"Timeout or error loading page for {keyword}: {e}")
                await browser.close()
                return new_listings

            
            items = await page.query_selector_all('.feed-grid__item')
            for item in items:
                try:
                    link_element = await item.query_selector('.new-item-box__overlay--clickable')
                    link = await link_element.get_attribute("href")
                    listing_id = link.split("/")[-1].split("-")[0]

                    if not db.is_listing_seen(listing_id):
                        db.save_listing_to_db(listing_id)
                        title = (await link_element.get_attribute("title")).split(",")[0]

                        try:
                            image_element = await item.query_selector('[data-testid*="--image--img"]')
                            image_url = await image_element.get_attribute('src') if image_element else "https://via.placeholder.com/150"
                        except Exception as e:
                            print(f"Error extracting image: {e}")
                            image_url = "https://via.placeholder.com/150"  

                        try:
                            price_element = await item.query_selector(".new-item-box__title p[data-testid*='price-text']")
                            price = await price_element.text_content() if price_element else "Price not available"
                        except Exception:
                            price = "Price not available"

                        try:
                            brand_element = await item.query_selector("p[data-testid*='description-title']")
                            brand = await brand_element.text_content() if brand_element else "Brand not available"
                        except Exception:
                            brand = "Brand not available"

                        new_listings.append({
                            "title": title,
                            "link": link,
                            "image": image_url,  
                            "price": price,
                            "brand": brand
                        })

                except Exception as e:
                    print(f"Error extracting data: {e}")

            await browser.close()
            return new_listings