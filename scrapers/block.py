import re

from models import Job

from .base import BaseScraper, is_poland

JOB_OBJ_RE = re.compile(r'\{[^{}]*\}')
TITLE_RE = re.compile(r'title:"((?:[^"\\]|\\.)*)"')
LOCATION_RE = re.compile(r'location:"((?:[^"\\]|\\.)*)"')
JOB_ID_RE = re.compile(r'id:(\d+)')
REMOTE_RE = re.compile(r'isRemote:(true|false)')


def _scan_array(text: str, start_index: int) -> str:
    depth = 0
    for i in range(start_index, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[start_index : i + 1]
    return ""


class BlockScraper(BaseScraper):
    """Block embeds its job list in the SvelteKit SSR payload."""

    name = "block"

    def fetch(self) -> list[Job]:
        resp = self.client.get(self.company.url)
        resp.raise_for_status()
        html = resp.text
        marker = "jobs:{currentPage:["
        index = html.find(marker)
        if index == -1:
            raise RuntimeError("jobs payload not found")
        start = index + len(marker) - 1
        array_text = _scan_array(html, start)
        jobs = []
        for obj_text in JOB_OBJ_RE.findall(array_text):
            title_match = TITLE_RE.search(obj_text)
            location_match = LOCATION_RE.search(obj_text)
            id_match = JOB_ID_RE.search(obj_text)
            if not title_match or not id_match:
                continue
            remote_match = REMOTE_RE.search(obj_text)
            if not remote_match or remote_match.group(1) != "true":
                continue
            location = location_match.group(1) if location_match else ""
            url = f"https://block.xyz/careers/jobs/{id_match.group(1)}"
            jobs.append(self.job(title_match.group(1), location, url))
        return jobs
