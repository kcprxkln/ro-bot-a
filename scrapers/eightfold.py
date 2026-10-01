from models import Job

from .base import BaseScraper, is_poland


class EightfoldScraper(BaseScraper):
    name = "eightfold"

    def __init__(self, company, host: str, pid: str, domain: str):
        super().__init__(company)
        self.host = host
        self.pid = pid
        self.domain = domain

    def fetch(self) -> list[Job]:
        jobs = []
        offset = 0
        num = 100
        while True:
            resp = self.client.get(
                f"https://{self.host}/api/apply/v2/jobs/{self.pid}/jobs",
                params={"domain": self.domain, "num": num, "offset": offset, "location": "Poland"},
            )
            resp.raise_for_status()
            data = resp.json()
            positions = data.get("positions") or []
            for item in positions:
                if item.get("isPrivate"):
                    continue
                location = item.get("location", "")
                if not is_poland(location):
                    continue
                url = item.get("canonicalPositionUrl") or ""
                jobs.append(self.job(item.get("name", ""), location, url))
            count = data.get("count") or 0
            offset += len(positions)
            if offset >= count or not positions:
                break
        return jobs
