# scripts/strain_scraper.py

from scripts.scrapers.leafly import scrape_leafly
from scripts.scrapers.allbud import scrape_allbud
from scripts.scrapers.weedmaps import scrape_weedmaps


def merge_sources(*sources):
    """
    Merge multiple strain data dictionaries from different sources.
    Prioritizes list merging and removes duplicates while preserving order.
    """
    merged = {}

    for source in sources:
        for key, value in source.items():
            # Initialize if key is new
            if key not in merged:
                merged[key] = value if isinstance(value, list) else [value]
            else:
                # Ensure current merged[key] is a list
                if not isinstance(merged[key], list):
                    merged[key] = [merged[key]]

                # Extend merged list with unique items
                if isinstance(value, list):
                    merged[key].extend(v for v in value if v not in merged[key])
                elif value not in merged[key]:
                    merged[key].append(value)

    return merged


def scrape_all_sources(leafly_url=None, allbud_url=None, weedmaps_url=None):
    """
    Scrapes strain data from multiple sources and merges them.
    Skips any source where a URL is not provided.
    """
    leafly_data = scrape_leafly(leafly_url) if leafly_url else {}
    allbud_data = scrape_allbud(allbud_url) if allbud_url else {}
    weedmaps_data = scrape_weedmaps(weedmaps_url) if weedmaps_url else {}

    return merge_sources(leafly_data, allbud_data, weedmaps_data)
