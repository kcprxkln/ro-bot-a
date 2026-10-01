import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from scrapers import get_scraper
from scrapers.playwright_util import close_browser

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="run one or all scrapers standalone")
    parser.add_argument("company", nargs="?", help="company name from companies.md, or omit for all")
    args = parser.parse_args()

    companies = config.load_companies()
    if args.company:
        companies = [c for c in companies if c.name == args.company]
        if not companies:
            raise SystemExit(f"unknown company: {args.company}")

    for comp in companies:
        scraper = get_scraper(comp)
        try:
            jobs = scraper.fetch()
        except Exception as e:
            print(f"{comp.name}: ERROR {type(e).__name__}: {e}")
            continue
        finally:
            scraper.close()
        print(f"{comp.name}: {len(jobs)} jobs")
        for job in jobs[:3]:
            print(f"  - {job.title} | {job.location} | {job.url}")
    close_browser()


if __name__ == "__main__":
    main()
