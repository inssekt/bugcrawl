# vinted_scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import db
from scrapers.scrapers import BaseScraper  # Import the BaseScraper

VINTED_SEARCH_URL = "https://www.vinted.co.uk/catalog?search_text="
VINTED_EXTRAS = "&order=newest_first&page=1"

class VintedScraper(BaseScraper):
    """
    Scraper for Vinted, inherited from BaseScraper.
    """

    def fetch_listings(self, keyword):
        """
        Fetch listings from Vinted for the given keyword.
        This method uses Selenium to scrape data from the Vinted website.
        """

        driver = webdriver.Chrome()
        new_listings = []
        url = f"{VINTED_SEARCH_URL}{keyword}{VINTED_EXTRAS}"
        driver.get(url)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "feed-grid__item"))
            )
        except Exception as e:
            print(f"Timeout or error loading page for {keyword}: {e}")
            driver.quit()
            return new_listings

        items = driver.find_elements(By.CLASS_NAME, "feed-grid__item")
        for item in items:
            try:
                link_element = item.find_element(By.CLASS_NAME, "new-item-box__overlay--clickable")
                link = link_element.get_attribute("href")
                listing_id = link.split("/")[-1].split("-")[0]

                if not db.is_listing_seen(listing_id):
                    db.save_listing_to_db(listing_id)
                    title = link_element.get_attribute("title").split(",")[0]

                    # Extracting the image URL from the <img> tag with the class 'web_ui__Image__content'
                    try:
                        image_element = item.find_element(By.CSS_SELECTOR, '[data-testid*="--image--img"]')
                        image_url = image_element.get_attribute('src')
                    except Exception as e:
                        print(f"Error extracting image: {e}")
                        image_url = "https://via.placeholder.com/150"  # Fallback image if not found

                    # Extracting the price
                    try:
                        price_element = item.find_element(By.CSS_SELECTOR, ".new-item-box__title p[data-testid*='price-text']")
                        price = price_element.text if price_element else "Price not available"
                    except Exception:
                        price = "Price not available"

                    # Extracting the brand
                    try:
                        brand_element = item.find_element(By.CSS_SELECTOR, "p[data-testid*='description-title']")
                        brand = brand_element.text if brand_element else "Brand not available"
                    except Exception:
                        brand = "Brand not available"

                    # Ensure all required fields are present
                    new_listings.append({
                        "title": title,
                        "link": link,
                        "image": image_url,  # Ensure image is always included
                        "price": price,
                        "brand": brand
                    })

            except Exception as e:
                print(f"Error extracting data: {e}")

        driver.quit()
        return new_listings