import json
import re

from models import Job

from .base import BaseScraper, is_poland

ITEM_RE = re.compile(
    r'\{"link": \{"text": "([^"]*)", "config": \{"href": '
    r'"(https://job-boards\.greenhouse\.io/gitlabcrm/jobs/\d+)"\}\}, "location": "([^"]*)"\}'
)


class GitlabScraper(BaseScraper):
    """GitLab jobs are talent pools embedded in a Nuxt _payload.json file."""

    name = "gitlab"

    def _resolve(self, node, seen=None):
        if seen is None:
            seen = set()
        if isinstance(node, int):
            if node in seen:
                return f"<ref {node}>"
            seen = seen | {node}
            if 0 <= node < len(self.payload):
                return self._resolve(self.payload[node], seen)
            return node
        if isinstance(node, list):
            return [self._resolve(v, seen) for v in node]
        if isinstance(node, dict):
            return {k: self._resolve(v, seen) for k, v in node.items()}
        return node

    def fetch(self) -> list[Job]:
        resp = self.client.get(self.company.url)
        resp.raise_for_status()
        match = re.search(r'_payload\.json\?([0-9a-f-]+)', resp.text)
        if not match:
            raise RuntimeError("nuxt payload hash not found")
        payload_url = (
            f"https://about.gitlab.com/jobs/all-jobs/_payload.json?{match.group(1)}"
        )
        payload_resp = self.client.get(payload_url)
        payload_resp.raise_for_status()
        self.payload = payload_resp.json()
        resolved = json.dumps(self._resolve(self.payload), ensure_ascii=False)
        jobs = []
        seen = set()
        for title, url, location in ITEM_RE.findall(resolved):
            if url in seen:
                continue
            seen.add(url)
            # gitlab lists remote talent pools; accept them regardless of location
            if location and not is_poland(location, remote_ok=True):
                continue
            jobs.append(self.job(title, location, url))
        return jobs
