from models import Job

from .base import BaseScraper, is_poland


class AtlassianScraper(BaseScraper):
    name = "atlassian"

    def fetch(self) -> list[Job]:
        resp = self.client.get("https://www.atlassian.com/endpoint/careers/listings")
        resp.raise_for_status()
        jobs = []
        for item in resp.json():
            locations = item.get("locations") or []
            location = ", ".join(locations)
            if not is_poland(location):
                continue
            url = (item.get("portalJobPost") or {}).get("portalUrl", "")
            jobs.append(self.job(item.get("title", ""), location, url))
        return jobs
