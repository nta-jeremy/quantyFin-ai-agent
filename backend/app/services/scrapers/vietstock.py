from app.services.scrapers.base import BaseScraper

class VietstockScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="Vietstock",
            rss_url="https://vietstock.vn/rss/chung-khoan.rss"
        )
