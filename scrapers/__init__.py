from urllib.parse import urlparse

from config import Company

from .ashby import AshbyScraper
from .atlassian import AtlassianScraper
from .balyasny import BalyasnyScraper
from .block import BlockScraper
from .bolt import BoltScraper
from .eightfold import EightfoldScraper
from .gitlab import GitlabScraper
from .greenhouse import GreenhouseScraper
from .point72 import Point72Scraper
from .revolut import RevolutScraper
from .smartrecruiters import SmartRecruitersScraper
from .snowflake import SnowflakeScraper


def _ashby_org(url: str) -> str:
    return urlparse(url).path.strip("/").split("/")[0]


def get_scraper(company: Company):
    name = company.name
    if name == "waymo":
        return GreenhouseScraper(company, "waymo")
    if name in {"squarepoint", "squarepoint cap"}:
        return GreenhouseScraper(company, "squarepointcapital")
    if name in {"mapbox", "mistral", "kraken"}:
        return AshbyScraper(company, _ashby_org(company.url))
    if name == "cohere":
        return AshbyScraper(company, "cohere", location_mode="remote")
    if name == "revolut":
        return RevolutScraper(company)
    if name == "bolt":
        return BoltScraper(company)
    if name == "netflix":
        return EightfoldScraper(company, "explore.jobs.netflix.net", "790318622925", "netflix.com")
    if name == "gitlab":
        return GitlabScraper(company)
    if name == "atlassian":
        return AtlassianScraper(company)
    if name == "dropbox":
        return SmartRecruitersScraper(company, "https://www.dropbox.jobs/en/jobs/xml/?rss=true")
    if name == "box":
        return SmartRecruitersScraper(company, "https://careers.box.com/en/jobs/xml/?rss=true")
    if name == "snowflake":
        return SnowflakeScraper(company)
    if name == "block":
        return BlockScraper(company)
    if name == "point72":
        return Point72Scraper(company)
    if name == "balyasny":
        return BalyasnyScraper(company)
    raise ValueError(f"no scraper for {name}")
