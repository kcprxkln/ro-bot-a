import xml.etree.ElementTree as ET

from models import Job

from .base import BaseScraper, is_poland


class SmartRecruitersScraper(BaseScraper):
    """Scrapes the SmartRecruiters RSS feed (works without Cloudflare challenges)."""

    name = "smartrecruiters"

    def __init__(self, company, feed_url: str):
        super().__init__(company)
        self.feed_url = feed_url

    def fetch(self) -> list[Job]:
        resp = self.client.get(self.feed_url)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        jobs = []
        for item in root.findall("job"):
            title = (item.findtext("title") or "").strip()
            url = (item.findtext("url") or "").strip()
            city = (item.findtext("city") or "").strip()
            country = (item.findtext("country") or "").strip()
            location = ", ".join(p for p in (city, country) if p)
            if not title or not url:
                continue
            if not is_poland(location):
                continue
            jobs.append(self.job(title, location, url))
        return jobs
