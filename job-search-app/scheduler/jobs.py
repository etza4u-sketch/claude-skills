"""Scheduler: runs scans hourly (immediate alerts) and weekly (full report)."""
import json
import os
import time
from datetime import datetime

import schedule

from config import (
    AI_KEYWORDS, ALERT_URGENCY_THRESHOLD, DATA_FILE,
    ALERTS_FILE, WEEKLY_REPORT_DAY, WEEKLY_REPORT_HOUR,
    HOURLY_CHECK_INTERVAL,
)
from searchers import DrushimSearcher, IndeedSearcher, RSSSearcher
from classifiers import BSGClassifier, SeniorityClassifier
from signals import FundingSignalDetector, MarketSignalAnalyzer
from reports import ReportGenerator


class JobScheduler:
    def __init__(self):
        self.searchers = [DrushimSearcher(), IndeedSearcher(), RSSSearcher()]
        self.seniority_clf = SeniorityClassifier()
        self.bsg_clf = BSGClassifier()
        self.funding_detector = FundingSignalDetector()
        self.market_analyzer = MarketSignalAnalyzer()
        self.reporter = ReportGenerator()
        self._known_ids: set[str] = self._load_known_ids()

    # ------------------------------------------------------------------ #
    # Public interface                                                      #
    # ------------------------------------------------------------------ #

    def run_once(self, verbose: bool = True) -> dict:
        """Single scan: fetch, classify, return results."""
        jobs = self._fetch_all_jobs()
        funding = self.funding_detector.scan()
        analysis = self.market_analyzer.analyze(jobs, funding)

        if verbose:
            self.reporter.print_market_summary(analysis)
            self.reporter.print_jobs_table(jobs)
            self.reporter.print_funding_signals(funding)

        self._save_cache(jobs)
        return {"jobs": jobs, "funding": funding, "analysis": analysis}

    def start_daemon(self) -> None:
        """Start background scheduler (blocking)."""
        from rich.console import Console
        console = Console()

        # Weekly full report
        getattr(schedule.every(), WEEKLY_REPORT_DAY).at(WEEKLY_REPORT_HOUR).do(
            self._weekly_report_job
        )

        # Hourly immediate-alert scan
        schedule.every(HOURLY_CHECK_INTERVAL).minutes.do(self._immediate_alert_job)

        console.print(
            f"[bold green]Scheduler started.[/bold green] "
            f"Weekly report: {WEEKLY_REPORT_DAY.capitalize()} at {WEEKLY_REPORT_HOUR}. "
            f"Immediate alerts: every {HOURLY_CHECK_INTERVAL} min."
        )
        while True:
            schedule.run_pending()
            time.sleep(30)

    # ------------------------------------------------------------------ #
    # Private helpers                                                       #
    # ------------------------------------------------------------------ #

    def _fetch_all_jobs(self):
        jobs = []
        for searcher in self.searchers:
            try:
                fetched = searcher.search(AI_KEYWORDS)
                jobs.extend(fetched)
            except Exception:
                pass

        # Classify each job
        classified = []
        for job in jobs:
            job = self.seniority_clf.classify(job)
            job = self.bsg_clf.classify(job)
            classified.append(job)

        return classified

    def _weekly_report_job(self) -> None:
        from rich.console import Console
        Console().rule("[bold magenta]Weekly AI Jobs Report[/bold magenta]")
        self.run_once(verbose=True)

    def _immediate_alert_job(self) -> None:
        jobs = self._fetch_all_jobs()
        new_senior = [
            j for j in jobs
            if j.id not in self._known_ids
            and j.urgency_score >= ALERT_URGENCY_THRESHOLD
            and j.is_senior
        ]
        for job in new_senior:
            self.reporter.print_immediate_alert(job)
            self._known_ids.add(job.id)
        self._save_known_ids()

    def _load_known_ids(self) -> set[str]:
        if os.path.exists(ALERTS_FILE):
            try:
                with open(ALERTS_FILE) as f:
                    return set(json.load(f).get("known_ids", []))
            except Exception:
                pass
        return set()

    def _save_known_ids(self) -> None:
        try:
            with open(ALERTS_FILE, "w") as f:
                json.dump({"known_ids": list(self._known_ids), "updated": datetime.now().isoformat()}, f)
        except Exception:
            pass

    def _save_cache(self, jobs) -> None:
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(
                    {
                        "scanned_at": datetime.now().isoformat(),
                        "count": len(jobs),
                        "jobs": [j.to_dict() for j in jobs],
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass
