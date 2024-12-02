from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import db
from scrapers.base_scraper import BaseScraper  
from bs4 import BeautifulSoup, Comment
import re
import json
import time

MERCARI_SEARCH_URL = "https://buyee.jp/mercari/search?keyword="
MERCARI_EXTRAS = "&category_id=3088&order-sort=desc-created_time&status=on_sale"

class MercariJPScraper(BaseScraper):
    """
    Scraper for Mercari.jp (through Buyee)
    """
    def fetch_listings(self, keyword):

        firefox_options = Options()
        firefox_options.add_argument("--headless")  # Run Chrome in headless mode
        firefox_options.add_argument("--no-sandbox")  # For Linux environments
        firefox_options.add_argument("--disable-dev-shm-usage")  # For Linux environments
        
        firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        driver = webdriver.Firefox(options=firefox_options)

        new_listings = []
        url = f"{MERCARI_SEARCH_URL}{keyword}{MERCARI_EXTRAS}"
        driver.get(url)

        time.sleep(10)

        html_content = driver.page_source

        with open("page_source.html", "w", encoding="utf-8") as file:
            file.write(html_content)

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
                            price = item.get("price", "No Price")
                            link = f"https://buyee.jp.mercari/item/{item.get("id")}"
                            image = f"https://static.mercdn.net/item/detail/orig/photos/{item.get("id")}_1.jpg"
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

        driver.quit()
        return new_listings