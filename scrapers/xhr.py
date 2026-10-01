import logging
import re

from . import playwright_util
from .base import USER_AGENT

log = logging.getLogger(__name__)

# keys that may hold a link to the job posting
JOB_LINK_KEYS = (
    "url",
    "jobUrl",
    "applyUrl",
    "postingUrl",
    "postingURL",
    "absoluteUrl",
    "absolute_url",
    "externalPath",
    "href",
    "link",
    "detailUrl",
    "careerSiteUrl",
    "canonicalPositionUrl",
    "positionUrl",
)


def iter_json_objects(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from iter_json_objects(value)
    elif isinstance(node, list):
        for value in node:
            yield from iter_json_objects(value)


def capture_json(page_url, url_patterns, timeout_ms=45000, scroll=True):
    """Load page_url in a headless browser and collect JSON responses."""
    browser = playwright_util.get_browser()
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1366, "height": 900},
        locale="en-US",
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    page = context.new_page()
    captured = []

    def on_response(resp):
        try:
            if "json" not in resp.headers.get("content-type", ""):
                return
            if url_patterns and not any(re.search(p, resp.url) for p in url_patterns):
                return
            captured.append({"url": resp.url, "data": resp.json()})
        except Exception:
            pass

    page.on("response", on_response)
    page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(7000)
    if scroll:
        for _ in range(6):
            page.mouse.wheel(0, 2200)
            page.wait_for_timeout(1200)
    page.wait_for_timeout(2500)
    context.close()
    return captured


def looks_like_job(d):
    if not isinstance(d.get("title"), str) or not d["title"].strip():
        return False
    location_keys = (
        "location",
        "locations",
        "locationsText",
        "locationName",
        "city",
        "cities",
        "workplace",
    )
    if not any(k in d for k in location_keys):
        return False
    if not any(k in d for k in JOB_LINK_KEYS) and not any(
        k in d for k in ("id", "requisitionId", "positionId", "jobId", "reqId")
    ):
        return False
    return True


def location_str(d) -> str:
    for key in ("locationsText", "locationName", "location"):
        value = d.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    locations = d.get("locations") or d.get("cities")
    if isinstance(locations, list) and locations:
        parts = []
        for item in locations:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(
                    item.get("name") or item.get("city") or item.get("label") or ""
                )
        joined = ", ".join(p for p in parts if p)
        if joined:
            return joined
    if isinstance(d.get("city"), str):
        return d["city"]
    return ""


def job_link(d) -> str:
    for key in JOB_LINK_KEYS:
        value = d.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""
