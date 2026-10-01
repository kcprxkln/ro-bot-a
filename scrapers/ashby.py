from models import Job

from .base import BaseScraper, is_poland


class AshbyScraper(BaseScraper):
    name = "ashby"

    def __init__(self, company, org: str, location_mode: str = "poland"):
        super().__init__(company)
        self.org = org
        # poland = only Poland-located jobs, remote = all remote jobs
        self.location_mode = location_mode

    @staticmethod
    def _salary(item: dict) -> str:
        compensation = item.get("compensation")
        if isinstance(compensation, dict):
            value = compensation.get("scrapeableCompensationSalarySummary")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def fetch(self) -> list[Job]:
        resp = self.client.get(
            f"https://api.ashbyhq.com/posting-api/job-board/{self.org}",
            params={"includeCompensation": "true"},
        )
        resp.raise_for_status()
        jobs = []
        for item in resp.json().get("jobs", []):
            if item.get("isListed") == "False":
                continue
            location = item.get("location", "")
            if self.location_mode == "poland":
                if not is_poland(location):
                    continue
            else:
                if item.get("workplaceType") != "Remote" and item.get("isRemote") != "True":
                    continue
            url = item.get("jobUrl") or f"https://jobs.ashbyhq.com/{self.org}/{item['id']}"
            jobs.append(self.job(item.get("title", ""), location, url, self._salary(item)))
        return jobs
