from app.services.scrapers.base import BaseScraper

class ThanhNienScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="ThanhNien",
            rss_url="https://thanhnien.vn/rss/kinh-te.rss"
        )
