from models import Job

from . import playwright_util
from .base import BaseScraper, USER_AGENT, is_poland


class SnowflakeScraper(BaseScraper):
    name = "snowflake"

    def fetch(self) -> list[Job]:
        def work(browser):
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1366, "height": 900},
                locale="en-US",
            )
            page = context.new_page()
            page.goto(
                "https://careers.snowflake.com/us/en/search-results?keywords=Poland",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(10000)
            cards = page.eval_on_selector_all(
                "a[data-ph-at-job-title-text]",
                "els => els.map(e => ({"
                "title: e.getAttribute('data-ph-at-job-title-text'),"
                "loc: e.getAttribute('data-ph-at-job-location-text'),"
                "href: e.href}))",
            )
            context.close()
            return cards

        cards = playwright_util.run(work)
        jobs = []
        seen = set()
        for card in cards:
            title = (card.get("title") or "").strip()
            if not title or title.startswith("${"):
                continue
            location = (card.get("loc") or "").strip()
            if not is_poland(location):
                continue
            if card["href"] in seen:
                continue
            seen.add(card["href"])
            jobs.append(self.job(title, location, card["href"]))
        return jobs
