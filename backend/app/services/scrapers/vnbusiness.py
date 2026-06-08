from app.services.scrapers.base import BaseScraper

class VnBusinessScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="VnBusiness",
            rss_url="https://vnbusiness.vn/rss/chung-khoan.rss"
        )
