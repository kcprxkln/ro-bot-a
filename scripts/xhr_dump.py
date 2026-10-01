import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers import xhr
from scrapers.playwright_util import close_browser


def summarize(data, depth=0):
    if isinstance(data, dict):
        return {k: summarize(v, depth + 1) for k, v in list(data.items())[:12]}
    if isinstance(data, list):
        return [summarize(data[0], depth + 1)] if data else []
    return type(data).__name__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--patterns", nargs="*", default=None)
    parser.add_argument("--no-scroll", action="store_true")
    args = parser.parse_args()
    try:
        responses = xhr.capture_json(args.url, url_patterns=args.patterns, scroll=not args.no_scroll)
        print(f"captured {len(responses)} JSON responses")
        for r in responses:
            print("=" * 80)
            print("URL:", r["url"])
            print(json.dumps(summarize(r["data"]), indent=1)[:1500])
    finally:
        close_browser()


if __name__ == "__main__":
    main()
