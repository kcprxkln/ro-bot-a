import logging
import queue
import threading

log = logging.getLogger(__name__)

_worker = None
_lock = threading.Lock()


class _PlaywrightWorker:
    def __init__(self):
        self._queue = queue.Queue()

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="playwright-worker"
        )
        self._thread.start()

    def _run(self) -> None:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = None
        try:
            browser = pw.chromium.launch(headless=True)
            while True:
                fn, result_queue = self._queue.get()
                if fn is None:
                    break
                try:
                    result_queue.put(("ok", fn(browser)))
                except Exception as e:
                    log.exception("playwright task failed")
                    result_queue.put(("err", e))
        finally:
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass
            try:
                pw.stop()
            except Exception:
                pass

    def run(self, fn):
        result_queue = queue.Queue()
        self._queue.put((fn, result_queue))
        status, value = result_queue.get()
        if status == "err":
            raise value
        return value


def _ensure_worker() -> _PlaywrightWorker:
    global _worker
    with _lock:
        if _worker is None:
            _worker = _PlaywrightWorker()
            _worker.start()
        return _worker


def run(fn):
    """Run fn(browser) on the dedicated playwright thread.

    The sync API refuses to run inside an asyncio event loop (Jupyter etc.);
    executing on a plain worker thread sidesteps that.
    """
    return _ensure_worker().run(fn)


def close_browser() -> None:
    global _worker
    with _lock:
        if _worker is not None:
            _worker._queue.put((None, None))
            _worker = None
