"""Scraper for drushim.co.il — Israel's leading job board."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlencode, quote
import re

from .base import BaseSearcher, Job


class DrushimSearcher(BaseSearcher):
    source_name = "drushim.co.il"
    BASE_URL = "https://www.drushim.co.il"
    SEARCH_URL = "https://www.drushim.co.il/jobs/search/"

    def search(self, keywords: list[str], location: str = "Israel") -> list[Job]:
        jobs = []
        for keyword in keywords[:3]:  # limit requests to avoid rate limiting
            try:
                jobs.extend(self._search_keyword(keyword))
            except Exception:
                pass
        # Deduplicate by id
        seen = {}
        for job in jobs:
            seen[job.id] = job
        return list(seen.values())

    def _search_keyword(self, keyword: str) -> list[Job]:
        params = {"q": keyword, "location": "ישראל"}
        url = f"{self.SEARCH_URL}?{urlencode(params, quote_via=quote)}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        jobs = []

        # drushim.co.il job card selectors (may change with site updates)
        for card in soup.select("article.job-item, div.job-box, li.job-listing")[:15]:
            job = self._parse_card(card)
            if job:
                jobs.append(job)

        # Fallback: generic link extraction if structured cards not found
        if not jobs:
            jobs = self._fallback_parse(soup)

        return jobs

    def _parse_card(self, card) -> Job | None:
        try:
            title_el = card.select_one("h2 a, h3 a, .job-title a, a.job-name")
            company_el = card.select_one(".company-name, .employer, span.company")
            location_el = card.select_one(".location, .city, span.location")
            desc_el = card.select_one(".description, .job-desc, p.summary")

            if not title_el:
                return None

            title = self._clean_text(title_el.get_text())
            url = title_el.get("href", "")
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            return Job(
                title=title,
                company=self._clean_text(company_el.get_text()) if company_el else "Unknown",
                location=self._clean_text(location_el.get_text()) if location_el else "Israel",
                description=self._clean_text(desc_el.get_text()) if desc_el else "",
                url=url,
                source=self.source_name,
                published_at=datetime.now(),
            )
        except Exception:
            return None

    def _fallback_parse(self, soup: BeautifulSoup) -> list[Job]:
        """Generic fallback: find any job-like links."""
        jobs = []
        for a in soup.select("a[href*='/job/'], a[href*='/jobs/']")[:10]:
            title = self._clean_text(a.get_text())
            url = a.get("href", "")
            if not title or len(title) < 5:
                continue
            if url and not url.startswith("http"):
                url = self.BASE_URL + url
            jobs.append(Job(
                title=title,
                company="Unknown",
                location="Israel",
                description="",
                url=url,
                source=self.source_name,
                published_at=datetime.now(),
            ))
        return jobs
