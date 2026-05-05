"""RSS feed searcher — reads job listings from RSS/Atom feeds using requests + lxml."""
import re
import requests
from datetime import datetime
from dateutil import parser as dateparser
from bs4 import BeautifulSoup

from .base import BaseSearcher, Job


KNOWN_JOB_FEEDS = [
    "https://www.geektime.co.il/category/jobs/feed/",
    "https://il.indeed.com/rss?q=AI+engineer&l=Israel&sort=date",
]


class RSSSearcher(BaseSearcher):
    source_name = "rss"

    def __init__(self, extra_feeds: list[str] | None = None):
        self.feeds = KNOWN_JOB_FEEDS + (extra_feeds or [])

    def search(self, keywords: list[str], location: str = "Israel") -> list[Job]:
        jobs = []
        kw_lower = [k.lower() for k in keywords]

        for feed_url in self.feeds:
            try:
                resp = requests.get(feed_url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                parsed_jobs = self._parse_feed(resp.text, feed_url)
                for job in parsed_jobs:
                    if self._matches_keywords(job, kw_lower):
                        jobs.append(job)
            except Exception:
                continue

        seen = {}
        for job in jobs:
            seen[job.id] = job
        return list(seen.values())

    def _parse_feed(self, xml_text: str, feed_url: str) -> list[Job]:
        jobs = []
        try:
            soup = BeautifulSoup(xml_text, "lxml-xml")
            items = soup.find_all("item") or soup.find_all("entry")
            for item in items[:30]:
                job = self._item_to_job(item, feed_url)
                if job:
                    jobs.append(job)
        except Exception:
            pass
        return jobs

    def _item_to_job(self, item, feed_url: str) -> Job | None:
        try:
            title_el = item.find("title")
            title = self._clean_text(title_el.get_text()) if title_el else ""
            if not title:
                return None

            link_el = item.find("link")
            if link_el:
                link = link_el.get("href") or link_el.get_text().strip()
            else:
                link = ""

            desc_el = item.find("description") or item.find("summary") or item.find("content")
            description = ""
            if desc_el:
                raw = desc_el.get_text()
                # Strip HTML from description
                description = self._clean_text(
                    BeautifulSoup(raw, "html.parser").get_text()
                )

            pub_el = item.find("pubDate") or item.find("published") or item.find("updated")
            published = None
            if pub_el:
                try:
                    published = dateparser.parse(pub_el.get_text())
                except Exception:
                    pass

            company = self._extract_company(item, description)
            location = self._extract_location(item, description)

            return Job(
                title=title,
                company=company,
                location=location,
                description=description[:600],
                url=link,
                source=f"rss:{feed_url[:40]}",
                published_at=published or datetime.now(),
            )
        except Exception:
            return None

    def _extract_company(self, item, description: str) -> str:
        author_el = item.find("author") or item.find("dc:creator")
        if author_el:
            return self._clean_text(author_el.get_text())
        match = re.search(r'(?:at|@|by|חברת)\s+([A-Z][A-Za-z0-9\.\-]+)', description)
        if match:
            return match.group(1)
        return "Unknown"

    def _extract_location(self, item, description: str) -> str:
        loc_el = item.find("location")
        if loc_el:
            return self._clean_text(loc_el.get_text())
        for city in ["Tel Aviv", "Herzliya", "Jerusalem", "Haifa", "Petah Tikva",
                     "Ramat Gan", "Be'er Sheva", "ישראל", "תל אביב"]:
            if city.lower() in description.lower():
                return city
        return "Israel"

    def _matches_keywords(self, job: Job, keywords: list[str]) -> bool:
        haystack = f"{job.title} {job.description} {job.company}".lower()
        return any(kw in haystack for kw in keywords)
