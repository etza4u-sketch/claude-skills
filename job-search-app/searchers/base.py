"""Base searcher and Job data model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib


@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    salary: Optional[str] = None
    tags: list = field(default_factory=list)
    tier: Optional[str] = None          # Bronze / Silver / Gold
    urgency_score: float = 0.0
    is_senior: bool = False

    @property
    def id(self) -> str:
        """Stable unique ID based on title+company+url."""
        raw = f"{self.title}|{self.company}|{self.url}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description[:500],
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "salary": self.salary,
            "tags": self.tags,
            "tier": self.tier,
            "urgency_score": self.urgency_score,
            "is_senior": self.is_senior,
        }


class BaseSearcher:
    """Abstract base class for all job board scrapers."""

    source_name: str = "unknown"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def search(self, keywords: list[str], location: str = "Israel") -> list[Job]:
        raise NotImplementedError

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        return " ".join(text.split()).strip()
