import re
from urllib.parse import unquote, urlencode

from models import Job

from . import playwright_util
from .base import BaseScraper, USER_AGENT, is_poland

DETAIL_RE = re.compile(
    r'<a[^>]*href="(/CSJobDetail\?jobName=[^"]*)"[^>]*>(.*?)</a>', re.S
)
TAG_RE = re.compile(r"<[^>]+>")


class Point72Scraper(BaseScraper):
    name = "point72"

    def fetch(self) -> list[Job]:
        browser = playwright_util.get_browser()
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        page.goto(self.company.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(10000)
        for _ in range(12):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1000)
        page.wait_for_timeout(3000)
        html = page.content()
        context.close()

        jobs = []
        seen = set()
        for href, body in DETAIL_RE.findall(html):
            location_match = re.search(r"location=([^&\"']+)", href)
            location = unquote(location_match.group(1)) if location_match else ""
            if not is_poland(location):
                continue
            title = TAG_RE.sub("", body).strip()
            if href in seen:
                continue
            seen.add(href)
            url = f"https://careers.point72.com{href.replace('&amp;', '&')}"
            jobs.append(self.job(title, location, url))
        return jobs
