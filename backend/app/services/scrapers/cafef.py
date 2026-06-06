from app.services.scrapers.base import BaseScraper

class CafeFScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="CafeF",
            rss_url="https://cafef.vn/rss/thi-truong-chung-khoan.rss"
        )
