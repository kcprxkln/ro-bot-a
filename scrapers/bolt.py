import re

from models import Job

from .base import BaseScraper, is_poland

# bolt embeds job cards in a Next.js RSC payload where every quote is escaped
# as \" and special chars as \u00xx sequences.
_VALUE = r"(?:\\u[0-9a-fA-F]{4}|[^\"\\])*"

JOB_RE = re.compile(
    r'\\"header\\":\{\\"roleTitle\\":\\"(?P<title>' + _VALUE + r')\\",\\"parentTeamTitle\\":\\"(?:'
    + _VALUE + r')\\",\\"locations\\":(?P<locs>\[.*?\]|null)'
)
HREF_RE = re.compile(r'\\"applyLinkProps\\":\{.*?\\"href\\":\\"(?P<href>[^\"\\]*)\\"')
CITY_RE = re.compile(r'\\"city\\":\\"(' + _VALUE + r')\\",\\"country\\":\\"(' + _VALUE + r')\\"')

_ESCAPES = {"\\u0026": "&", "\\u0027": "'", "\\u003c": "<", "\\u003e": ">"}


def _unescape(text: str) -> str:
    for esc, char in _ESCAPES.items():
        text = text.replace(esc, char)
    return text


class BoltScraper(BaseScraper):
    name = "bolt"

    def fetch(self) -> list[Job]:
        resp = self.client.get("https://bolt.eu/en/careers/positions/")
        resp.raise_for_status()
        html = resp.text
        jobs = []
        seen = set()
        for match in JOB_RE.finditer(html):
            title = _unescape(match.group("title"))
            cities = CITY_RE.findall(match.group("locs"))
            location = ", ".join(
                f"{_unescape(c)}, {_unescape(co)}" for c, co in cities
            )
            if not is_poland(location):
                continue
            href_match = HREF_RE.search(html, match.end())
            href = href_match.group("href") if href_match else ""
            if href in seen:
                continue
            seen.add(href)
            url = href if href.startswith("http") else f"https://bolt.eu{href}"
            jobs.append(self.job(title, location, url))
        return jobs
