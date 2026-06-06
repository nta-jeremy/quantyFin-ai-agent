from app.services.scrapers.base import BaseScraper

class VnEconomyScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="VnEconomy",
            rss_url="https://vneconomy.vn/rss/chung-khoan.rss"
        )
