import re

from models import Job

from . import playwright_util
from .base import BaseScraper, USER_AGENT, is_poland

CARD_RE = re.compile(
    r'<a[^>]*data-id="([^"]+)"[^>]*>(.*?)</a><div[^>]*>(.*?)</div>', re.S
)
TAG_RE = re.compile(r"<[^>]+>")


class BalyasnyScraper(BaseScraper):
    name = "balyasny"

    def fetch(self) -> list[Job]:
        browser = playwright_util.get_browser()
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        page.goto("https://bambusdev.my.site.com/s/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(15000)
        for _ in range(12):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1000)
        page.wait_for_timeout(3000)
        html = page.content()
        context.close()

        jobs = []
        seen = set()
        for data_id, body, meta in CARD_RE.findall(html):
            title = TAG_RE.sub("", body).strip()
            meta_text = re.sub(r"\s+", " ", TAG_RE.sub(" ", meta)).strip()
            # meta looks like: "REQ8283 | Warsaw | Posted 7 Days Ago"
            parts = [p.strip() for p in meta_text.split("|")]
            location = parts[1] if len(parts) > 1 else ""
            if not is_poland(location):
                continue
            if data_id in seen:
                continue
            seen.add(data_id)
            url = f"https://bambusdev.my.site.com/s/details?jobReq={data_id}"
            jobs.append(self.job(title, location, url))
        return jobs
