from scrapers.base_scraper import BaseScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
from stem import Signal
from stem.control import Controller
import db
from dotenv import load_dotenv
import os


DEPOP_SEARCH_URL = "https://www.depop.com/search/?q="
DEPOP_EXTRAS = "&sort=newlyListed"

load_dotenv()

# def renew_tor_ip():
#     control_port = 9051
#     tor_password = os.getenv("TOR_PASSWORD")

#     with Controller.from_port(port=control_port) as controller:
#         # Authenticate with the plain-text password
#         controller.authenticate(password=tor_password)
#         print("Successfully authenticated with Tor!")

#             # Request a new IP address (NEWNYM signal)
#         controller.signal(Signal.NEWNYM)
#         print("New IP address requested.")
#         time.sleep(5)

class DepopScraper(BaseScraper):
    def fetch_listings(self, keyword):

        firefox_options = Options()
        firefox_options.add_argument("--headless")  
        firefox_options.add_argument("--no-sandbox")  
        firefox_options.add_argument("--disable-dev-shm-usage")  
        # firefox_options.add_argument("window-size=1920,1080")

        # firefox_options.set_preference("network.proxy.type", 1)  
        # firefox_options.set_preference("network.proxy.socks", "127.0.0.1")  
        # firefox_options.set_preference("network.proxy.socks_port", 9050)  

        capabilities = DesiredCapabilities.FIREFOX.copy()

        firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        driver = webdriver.Firefox(options=firefox_options, desired_capabilities=capabilities)

        # try:
        #     renew_tor_ip()
        # except Exception as e:
        #     print(f"Error rotating Tor IP: {e}")
        #     driver.quit()
        #     driver = webdriver.Firefox(options=firefox_options)

        new_listings = []
        url = f"{DEPOP_SEARCH_URL}{keyword}{DEPOP_EXTRAS}"
        driver.get(url)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "styles__ProductCardContainer-sc-ec533c9e-7"))
            )
        except Exception as e:
            print(f"Timeout or error loading page for {keyword}: {e}")
            driver.quit()
            return new_listings

        items = driver.find_elements(By.CSS_SELECTOR, "li.styles__ProductCardContainer-sc-ec533c9e-7")
        for item in items:
            try:
                
                title_tag = item.find_element(By.CSS_SELECTOR, "a.styles__ProductCard-sc-ec533c9e-4.elBVWz")
                link = title_tag.get_attribute('href')  
                print(f"link: {link}")
                if link.endswith('/'):
                    link = link[:-1]  
                listing_id = link.split("/")[-1]
                print(f"Listing ID: {listing_id}")

                if not db.is_listing_seen(listing_id):
                    db.save_listing_to_db(listing_id)

                    id_parts = listing_id.split('-')
                    title = " ".join(id_parts[1:])

                    
                    try:
                        image_tag = item.find_element(By.CSS_SELECTOR, "img.sc-htehQK.fmdgqI")
                        srcset = image_tag.get_attribute('srcset')
                        image_urls = srcset.split(", ")
                        image_url = image_urls[-1].split(" ")[0]
                    except Exception:
                        image_url = "https://via.placeholder.com/150"  

                    
                    try:
                        price_element = item.find_element(By.XPATH, '//*[@aria-label="Price"]')
                        price = price_element.text
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

        driver.quit()
        return new_listings