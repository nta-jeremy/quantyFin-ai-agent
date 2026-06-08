import httpx
import re
import html
import xml.etree.ElementTree as ET
import email.utils
import datetime as dt
from urllib.parse import urljoin
from app.core.logging import logger

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    # Remove HTML tags
    clean_re = re.compile('<.*?>')
    cleaned = re.sub(clean_re, '', raw_html).strip()
    return html.unescape(cleaned)

def parse_pub_date(pub_date_str: str) -> dt.datetime:
    if not pub_date_str:
        return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    try:
        dt_obj = email.utils.parsedate_to_datetime(pub_date_str)
        if dt_obj.tzinfo:
            dt_obj = dt_obj.astimezone(dt.timezone.utc).replace(tzinfo=None)
        else:
            dt_obj = dt_obj.replace(tzinfo=None)
        return dt_obj
    except Exception as e:
        logger.warning(f"Failed to parse publication date '{pub_date_str}': {str(e)}. Using current time.")
        return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)

class BaseScraper:
    def __init__(self, source_name: str, rss_url: str):
        self.source_name = source_name
        self.rss_url = rss_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_rss(self, client: httpx.Client) -> bytes:
        logger.info(f"[{self.source_name}] Fetching RSS feed from URL: {self.rss_url}")
        response = client.get(self.rss_url)
        response.raise_for_status()
        return response.content

    def parse_rss(self, xml_content: bytes) -> list[dict]:
        articles = []
        try:
            # Parse XML safely
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"[{self.source_name}] XML parsing failed: {str(e)}")
            return []

        items = root.findall(".//item")
        logger.info(f"[{self.source_name}] Found {len(items)} items in RSS feed.")
        for item in items:
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            pub_date_el = item.find("pubDate")

            title = title_el.text if title_el is not None else ""
            url = link_el.text if link_el is not None else ""
            description = desc_el.text if desc_el is not None else ""
            pub_date_raw = pub_date_el.text if pub_date_el is not None else ""

            # Standard clean up
            title = title[:500].strip() if title else ""
            url = url.strip() if url else ""
            if url:
                url = urljoin(self.rss_url, url)
            content = clean_html(description) if description else ""
            published_at = parse_pub_date(pub_date_raw)

            if not title or not url:
                continue

            articles.append({
                "title": title,
                "content": content,
                "url": url,
                "published_at": published_at,
                "source": self.source_name
            })

        return articles

    def scrape(self, client: httpx.Client) -> list[dict]:
        """
        Main interface to scrape and parse the RSS feed.
        """
        try:
            xml_content = self.fetch_rss(client)
            return self.parse_rss(xml_content)
        except Exception as e:
            logger.error(f"[{self.source_name}] Error during scraping: {str(e)}")
            raise e
