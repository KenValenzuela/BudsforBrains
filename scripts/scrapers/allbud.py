import requests
from bs4 import BeautifulSoup

def scrape_allbud(url: str) -> dict:
    result = {
        "description": "",
        "effects": [],
        "may_relieve": [],
        "flavors": [],
        "aromas": []
    }
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        desc = soup.find("div", class_="strain-info")
        if desc:
            result["description"] = desc.get_text(strip=True)

        sidebar = soup.find("div", class_="strain-properties")
        if sidebar:
            def get_section(label):
                block = sidebar.find("div", string=lambda x: x and label in x)
                if block:
                    values = block.find_next("div")
                    return [x.strip() for x in values.get_text(",").split(",") if x.strip()]
                return []

            result["effects"] = get_section("Effects")
            result["may_relieve"] = get_section("May Relieve")
            result["flavors"] = get_section("Flavors")
            result["aromas"] = get_section("Aromas")

        return result
    except:
        return result
