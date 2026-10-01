from models import Job

from .base import BaseScraper, is_poland


class GreenhouseScraper(BaseScraper):
    name = "greenhouse"

    def __init__(self, company, board: str):
        super().__init__(company)
        self.board = board

    def fetch(self) -> list[Job]:
        resp = self.client.get(
            f"https://boards-api.greenhouse.io/v1/boards/{self.board}/jobs",
            params={"content": "true"},
        )
        resp.raise_for_status()
        jobs = []
        for item in resp.json().get("jobs", []):
            location = (item.get("location") or {}).get("name", "")
            if not is_poland(location):
                continue
            jobs.append(self.job(item.get("title", ""), location, item.get("absolute_url", "")))
        return jobs
