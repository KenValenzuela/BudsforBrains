# scripts/scrapers/weedmaps.py

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_weedmaps(url: str) -> dict:
    """
    Scrapes strain information from a Weedmaps strain page.
    Returns a dictionary with common keys: description, feelings, etc.
    """
    result = {
        "feelings": [],
        "helps_with": [],
        "negatives": [],
        "terpenes": [],
        "description": ""
    }

    if not url or not url.startswith("http"):
        return result

    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        with webdriver.Chrome(service=service, options=options) as driver:
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")

        container = soup.find("div", {"data-testid": "page-layout"})
        if container:
            text_blob = container.get_text(separator=" ").strip()
            result["description"] = text_blob[:500]  # fallback summary

    except Exception as e:
        print(f"[Weedmaps Scraper] Error scraping {url}: {e}")

    return result