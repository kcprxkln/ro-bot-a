import logging
import re

import httpx

from config import POLAND_KEYWORDS, Company
from models import Job

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class ScraperError(Exception):
    pass


def is_poland(location: str, remote_ok: bool = False) -> bool:
    text = location.lower()
    if any(k in text for k in POLAND_KEYWORDS):
        return True
    if remote_ok and ("remote" in text or "anywhere" in text or "global" in text):
        return True
    return False


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


class BaseScraper:
    name = "base"

    def __init__(self, company: Company):
        self.company = company
        self.client = httpx.Client(
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30,
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def fetch(self) -> list[Job]:
        raise NotImplementedError

    def job(self, title: str, location: str, url: str, salary: str = "") -> Job:
        return Job(
            company=self.company.name,
            title=title.strip(),
            location=location.strip(),
            url=url,
            salary=salary.strip(),
        )
