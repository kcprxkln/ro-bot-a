from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    company: str
    title: str
    location: str
    url: str
    salary: str = ""

    @property
    def key(self) -> str:
        return f"{self.company}:{self.url}"
