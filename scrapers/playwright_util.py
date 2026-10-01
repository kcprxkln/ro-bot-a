import logging
import threading

log = logging.getLogger(__name__)

_pw = None
_browser = None
_lock = threading.Lock()


def get_browser():
    global _pw, _browser
    with _lock:
        if _browser is None:
            from playwright.sync_api import sync_playwright

            _pw = sync_playwright().start()
            _browser = _pw.chromium.launch(headless=True)
        return _browser


def close_browser():
    global _pw, _browser
    with _lock:
        if _browser is not None:
            try:
                _browser.close()
            except Exception:
                pass
            _browser = None
        if _pw is not None:
            try:
                _pw.stop()
            except Exception:
                pass
            _pw = None
