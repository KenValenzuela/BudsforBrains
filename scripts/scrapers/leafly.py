import requests
from bs4 import BeautifulSoup
import re

def scrape_leafly(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0"}
    result = {"feelings": [], "helps_with": [], "negatives": [], "terpenes": [], "description": ""}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        ul = soup.find("ul", class_="flex flex-col gap-sm")
        if ul:
            for li in ul.find_all("li"):
                raw = li.get_text(separator=" ", strip=True)
                if ":" in raw:
                    label, values = raw.split(":", 1)
                    parsed = [v.strip() for v in re.split(r"[·•,;]|\\s{2,}", values) if v.strip()]
                    if "feelings" in label.lower():
                        result["feelings"] = parsed
                    elif "helps with" in label.lower():
                        result["helps_with"] = parsed
                    elif "negatives" in label.lower():
                        result["negatives"] = parsed
                    elif "terpenes" in label.lower():
                        result["terpenes"] = parsed
        return result
    except:
        return result
