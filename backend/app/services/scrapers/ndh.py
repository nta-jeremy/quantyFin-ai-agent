from app.services.scrapers.base import BaseScraper

class NDHScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="NDH",
            rss_url="https://ndh.vn/rss/market.rss"
        )
