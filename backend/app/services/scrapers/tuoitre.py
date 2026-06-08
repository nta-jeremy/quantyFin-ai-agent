from app.services.scrapers.base import BaseScraper

class TuoiTreScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="TuoiTre",
            rss_url="https://tuoitre.vn/rss/kinh-doanh.rss"
        )
