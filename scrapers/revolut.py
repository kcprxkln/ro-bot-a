import json
import re

from models import Job

from .base import BaseScraper, is_poland, slugify


class RevolutScraper(BaseScraper):
    name = "revolut"

    def fetch(self) -> list[Job]:
        resp = self.client.get("https://www.revolut.com/en-US/careers/")
        resp.raise_for_status()
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            resp.text,
            re.S,
        )
        if not match:
            raise RuntimeError("__NEXT_DATA__ not found")
        data = json.loads(match.group(1))
        positions = data["props"]["pageProps"]["positions"]
        jobs = []
        for item in positions:
            locations = ", ".join(
                loc.get("name", "") for loc in item.get("locations", []) if loc.get("name")
            )
            if not is_poland(locations):
                continue
            title = item.get("text", "")
            url = (
                f"https://www.revolut.com/en-US/careers/position/"
                f"{slugify(title)}-{item['id']}/"
            )
            jobs.append(self.job(title, locations, url))
        return jobs
