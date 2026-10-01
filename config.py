import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parent
COMPANIES_FILE = ROOT / "companies.md"


def _load_env_file() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip())
    except ValueError:
        return default


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
INTERVAL_MINUTES = _env_int("INTERVAL_MINUTES", 15)
DB_PATH = os.environ.get("DB_PATH", "").strip() or str(ROOT / "jobs.db")

POLAND_KEYWORDS = (
    "poland",
    "warsaw",
    "warszawa",
    "kraków",
    "krakow",
    "gdańsk",
    "gdansk",
    "wrocław",
    "wroclaw",
    "poznań",
    "poznan",
    "łódź",
    "lodz",
    "katowice",
    "gdynia",
    "szczecin",
)

# companies whose URLs intentionally include remote jobs anywhere (not just Poland)
REMOTE_OK_COMPANIES = {"block"}


@dataclass(frozen=True)
class Company:
    name: str
    url: str


def load_companies() -> list[Company]:
    companies = []
    for line in COMPANIES_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "," not in line:
            continue
        name, _, url = line.partition(",")
        companies.append(Company(name=name.strip().lower(), url=url.strip()))
    return companies
