"""
Detect funding signals from tech news RSS feeds.
Maps funded companies to expected future hiring.
"""
import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from datetime import datetime
from dateutil import parser as dateparser
from config import NEWS_FEEDS, FUNDING_KEYWORDS


@dataclass
class FundingSignal:
    company: str
    amount: str
    round_type: str
    description: str
    url: str
    published_at: datetime
    hiring_prediction: str
    tier: str = "Silver"

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "amount": self.amount,
            "round_type": self.round_type,
            "description": self.description[:300],
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "hiring_prediction": self.hiring_prediction,
            "tier": self.tier,
        }


AMOUNT_PATTERN = re.compile(
    r'\$\s*(\d+(?:\.\d+)?)\s*(million|billion|M|B)\b', re.IGNORECASE
)
ROUND_PATTERN = re.compile(
    r'\b(seed|pre.?seed|series\s+[a-e]|series\s+[A-E]|growth\s+round|'
    r'bridge\s+round|ipo|spac)\b', re.IGNORECASE
)
COMPANY_PATTERN = re.compile(
    r'([A-Z][A-Za-z0-9\.\-]+(?:\s+[A-Z][A-Za-z0-9\.\-]+)?)\s+'
    r'(?:raises|raised|secures|secured|closes|closed|announces)',
    re.IGNORECASE
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


class FundingSignalDetector:
    def __init__(self, extra_feeds: list[str] | None = None):
        self.feeds = NEWS_FEEDS + (extra_feeds or [])

    def scan(self) -> list[FundingSignal]:
        signals = []
        for feed_url in self.feeds:
            try:
                resp = requests.get(feed_url, headers=HEADERS, timeout=10)
                resp.raise_for_status()
                signals.extend(self._parse_feed(resp.text))
            except Exception:
                continue
        return signals

    def _parse_feed(self, xml_text: str) -> list[FundingSignal]:
        signals = []
        try:
            soup = BeautifulSoup(xml_text, "lxml-xml")
            items = soup.find_all("item") or soup.find_all("entry")
            for item in items[:50]:
                signal = self._parse_item(item)
                if signal:
                    signals.append(signal)
        except Exception:
            pass
        return signals

    def _parse_item(self, item) -> FundingSignal | None:
        title_el = item.find("title")
        desc_el = item.find("description") or item.find("summary")
        link_el = item.find("link")
        pub_el = item.find("pubDate") or item.find("published")

        title = title_el.get_text() if title_el else ""
        summary = BeautifulSoup(
            desc_el.get_text() if desc_el else "", "html.parser"
        ).get_text()
        text = f"{title} {summary}"

        if not any(kw.lower() in text.lower() for kw in FUNDING_KEYWORDS):
            return None

        amount_match = AMOUNT_PATTERN.search(text)
        if not amount_match:
            return None

        amount_val = float(amount_match.group(1))
        amount_unit = amount_match.group(2).upper()
        amount_str = f"${amount_match.group(1)}{amount_unit}"

        round_match = ROUND_PATTERN.search(text)
        round_type = round_match.group(0).strip().lower() if round_match else "unknown"

        company_match = COMPANY_PATTERN.search(text)
        company = company_match.group(1).strip() if company_match else "Unknown Company"

        if amount_unit in ("B", "BILLION") or (
            amount_unit in ("M", "MILLION") and amount_val >= 100
        ):
            tier = "Gold"
        elif amount_val >= 20:
            tier = "Silver"
        else:
            tier = "Bronze"

        prediction = self._predict_hiring(company, amount_val, amount_unit, round_type)

        published = None
        if pub_el:
            try:
                published = dateparser.parse(pub_el.get_text())
            except Exception:
                pass

        link = ""
        if link_el:
            link = link_el.get("href") or link_el.get_text().strip()

        return FundingSignal(
            company=company,
            amount=amount_str,
            round_type=round_type,
            description=title[:200],
            url=link,
            published_at=published or datetime.now(),
            hiring_prediction=prediction,
            tier=tier,
        )

    def _predict_hiring(self, company: str, amount: float, unit: str, round_type: str) -> str:
        role_hints = {
            "seed": "founding engineers, ML researchers",
            "series a": "senior ML/AI engineers, product managers",
            "series b": "team leads, AI architects, MLOps engineers",
            "series c": "principal engineers, heads of AI",
        }
        roles = role_hints.get(round_type.lower(), "AI/ML engineers")
        if unit in ("B", "BILLION"):
            size_desc = "major expansion"
        elif amount >= 50:
            size_desc = "significant growth"
        elif amount >= 10:
            size_desc = "team build-out"
        else:
            size_desc = "early team formation"
        return (
            f"{company} likely hiring for {roles} "
            f"({size_desc} — {amount}{unit} {round_type})"
        )
