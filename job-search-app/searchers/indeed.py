"""Scraper for il.indeed.com."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlencode, quote

from .base import BaseSearcher, Job


class IndeedSearcher(BaseSearcher):
    source_name = "indeed.com"
    SEARCH_URL = "https://il.indeed.com/jobs"

    def search(self, keywords: list[str], location: str = "Israel") -> list[Job]:
        jobs = []
        query = " OR ".join(f'"{kw}"' for kw in keywords[:4])
        try:
            jobs.extend(self._fetch_page(query, location, start=0))
            jobs.extend(self._fetch_page(query, location, start=10))
        except Exception:
            pass
        seen = {}
        for job in jobs:
            seen[job.id] = job
        return list(seen.values())

    def _fetch_page(self, query: str, location: str, start: int = 0) -> list[Job]:
        params = {"q": query, "l": location, "start": start}
        url = f"{self.SEARCH_URL}?{urlencode(params, quote_via=quote)}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=12)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        jobs = []

        for card in soup.select("div.job_seen_beacon, li.css-5lfssm, div[data-jk]")[:15]:
            job = self._parse_card(card)
            if job:
                jobs.append(job)

        return jobs

    def _parse_card(self, card) -> Job | None:
        try:
            title_el = card.select_one("h2.jobTitle a, a[data-jk], span[title]")
            company_el = card.select_one("span.companyName, [data-testid='company-name']")
            location_el = card.select_one("div.companyLocation, [data-testid='text-location']")
            desc_el = card.select_one("div.job-snippet, ul.css-1lyr5hv")
            salary_el = card.select_one("div.salary-snippet, [data-testid='attribute_snippet_testid']")

            if not title_el:
                return None

            title = self._clean_text(title_el.get("title") or title_el.get_text())
            href = title_el.get("href", "")
            if href and not href.startswith("http"):
                href = "https://il.indeed.com" + href

            return Job(
                title=title,
                company=self._clean_text(company_el.get_text()) if company_el else "Unknown",
                location=self._clean_text(location_el.get_text()) if location_el else "Israel",
                description=self._clean_text(desc_el.get_text()) if desc_el else "",
                url=href,
                source=self.source_name,
                published_at=datetime.now(),
                salary=self._clean_text(salary_el.get_text()) if salary_el else None,
            )
        except Exception:
            return None
