import argparse
import logging
import threading
import time

import config
from db import JobsDB
from notifier import Notifier
from scrapers import get_scraper
from scrapers.playwright_util import close_browser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("jobot")


def run_scan(db: JobsDB, notifier: Notifier) -> int:
    companies = config.load_companies()
    baseline = db.count() == 0
    total_new = 0
    for comp in companies:
        scraper = None
        try:
            scraper = get_scraper(comp)
            jobs = scraper.fetch()
        except Exception:
            log.exception("failed to fetch %s", comp.name)
            continue
        finally:
            if scraper is not None:
                scraper.close()
        new = db.new_jobs(jobs)
        db.mark_seen(jobs)
        log.info("%s: %d jobs, %d new", comp.name, len(jobs), len(new))
        if not baseline:
            for job in new:
                if notifier.send_job(job, db):
                    total_new += 1
    if baseline:
        log.info("first run: stored %d jobs as baseline, nothing sent", db.count())
    return total_new


def start_poller(db: JobsDB, token: str) -> None:
    poller = Notifier(token, config.TELEGRAM_CHAT_ID)
    count = len(config.load_companies())

    def loop() -> None:
        while True:
            try:
                poller.poll(db, count)
            except Exception:
                log.exception("poller iteration failed")
                time.sleep(5)

    threading.Thread(target=loop, daemon=True, name="telegram-poller").start()


def main() -> None:
    parser = argparse.ArgumentParser(description="roBOTa job offer watcher")
    parser.add_argument("--once", action="store_true", help="run a single scan and exit")
    args = parser.parse_args()

    db = JobsDB(config.DB_PATH)
    notifier = Notifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    log.info(
        "interval: %d min, telegram: %s",
        config.INTERVAL_MINUTES,
        "enabled" if notifier.enabled else "disabled (set TELEGRAM_BOT_TOKEN in .env)",
    )
    if notifier.enabled:
        log.info("message the bot /start to subscribe (or set TELEGRAM_CHAT_ID in .env)")
        start_poller(db, config.TELEGRAM_BOT_TOKEN)
    try:
        while True:
            try:
                run_scan(db, notifier)
            except Exception:
                log.exception("scan failed")
            if args.once:
                break
            time.sleep(config.INTERVAL_MINUTES * 60)
    finally:
        close_browser()


if __name__ == "__main__":
    main()
