#!/usr/bin/env python3
"""
AI Job Search — Bronze / Silver / Gold
======================================
Scan Israeli job boards for AI engineer positions, classify them by
opportunity tier, detect funding signals, and alert on senior/unique roles.

Usage:
    python app.py scan                   # one-time scan + full report
    python app.py scan --tier gold       # only Gold-tier jobs
    python app.py scan --senior          # only senior/unique jobs
    python app.py scan --min-score 3.5   # filter by urgency score
    python app.py signals                # show funding signals only
    python app.py explain                # show BSG model explainer
    python app.py watch                  # start hourly+weekly daemon
    python app.py export                 # export last scan to JSON
"""

import json
import sys
import os

import click
from rich.console import Console
from rich.rule import Rule

# Ensure project root is on sys.path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from config import AI_KEYWORDS, ALERT_URGENCY_THRESHOLD, DATA_FILE
from searchers import DrushimSearcher, IndeedSearcher, RSSSearcher
from classifiers import BSGClassifier, SeniorityClassifier
from signals import FundingSignalDetector, MarketSignalAnalyzer
from reports import ReportGenerator
from scheduler import JobScheduler

console = Console()


def _run_full_scan():
    """Fetch, classify and return (jobs, funding, analysis)."""
    searchers = [DrushimSearcher(), IndeedSearcher(), RSSSearcher()]
    seniority_clf = SeniorityClassifier()
    bsg_clf = BSGClassifier()
    funding_detector = FundingSignalDetector()
    market_analyzer = MarketSignalAnalyzer()

    console.print("[bold cyan]Scanning job boards…[/bold cyan]")
    jobs = []
    for searcher in searchers:
        try:
            fetched = searcher.search(AI_KEYWORDS)
            console.print(
                f"  [green]✓[/green] {searcher.source_name}: {len(fetched)} jobs"
            )
            jobs.extend(fetched)
        except Exception as exc:
            console.print(f"  [red]✗[/red] {searcher.source_name}: {exc}")

    # Classify
    for job in jobs:
        seniority_clf.classify(job)
        bsg_clf.classify(job)

    # Deduplicate
    seen = {}
    for job in jobs:
        seen[job.id] = job
    jobs = list(seen.values())

    console.print(f"\n[bold green]Total unique jobs:[/bold green] {len(jobs)}\n")

    console.print("[bold cyan]Scanning funding news…[/bold cyan]")
    try:
        funding = funding_detector.scan()
        console.print(f"  [green]✓[/green] {len(funding)} funding signals found\n")
    except Exception as exc:
        console.print(f"  [red]✗[/red] Funding scan failed: {exc}\n")
        funding = []

    analysis = market_analyzer.analyze(jobs, funding)
    return jobs, funding, analysis


@click.group()
def cli():
    """AI Job Search — Bronze / Silver / Gold model for Israeli market."""


@cli.command()
@click.option("--tier", type=click.Choice(["bronze", "silver", "gold", "all"]), default="all")
@click.option("--senior", is_flag=True, help="Show only senior/unique positions")
@click.option("--min-score", type=float, default=0.0, help="Minimum urgency score")
@click.option("--max-rows", type=int, default=25)
@click.option("--export", "do_export", is_flag=True, help="Save results to JSON after scan")
def scan(tier, senior, min_score, max_rows, do_export):
    """Scan job boards and display classified results."""
    console.rule("[bold magenta]AI Job Search — Bronze / Silver / Gold[/bold magenta]")

    jobs, funding, analysis = _run_full_scan()

    reporter = ReportGenerator()
    reporter.print_market_summary(analysis)

    # Apply filters
    filtered = jobs
    if tier != "all":
        filtered = [j for j in filtered if (j.tier or "bronze").lower() == tier]
    if senior:
        filtered = [j for j in filtered if j.is_senior]
    if min_score > 0:
        filtered = [j for j in filtered if j.urgency_score >= min_score]

    title = "AI Engineer Jobs — Israel"
    if tier != "all":
        title += f" ({tier.capitalize()})"
    if senior:
        title += " [Senior/Unique only]"

    reporter.print_jobs_table(filtered, title=title, max_rows=max_rows)
    reporter.print_funding_signals(funding)

    if do_export:
        _save_export(jobs, funding, analysis)

    # Remind user about immediate alerts
    immediate = [j for j in jobs if j.urgency_score >= ALERT_URGENCY_THRESHOLD and j.is_senior]
    if immediate:
        console.print(
            f"\n[bold red]🚨 {len(immediate)} position(s) qualify for immediate alert "
            f"(score ≥ {ALERT_URGENCY_THRESHOLD}).[/bold red]"
        )
        for job in sorted(immediate, key=lambda j: j.urgency_score, reverse=True)[:3]:
            reporter.print_immediate_alert(job)


@cli.command()
def signals():
    """Show funding signals and predicted future hiring."""
    console.rule("[bold green]Funding Signals → Future Hiring[/bold green]")
    detector = FundingSignalDetector()
    reporter = ReportGenerator()
    console.print("[bold cyan]Scanning funding news…[/bold cyan]")
    try:
        funding = detector.scan()
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        return
    reporter.print_funding_signals(funding)


@cli.command()
def explain():
    """Explain the Bronze / Silver / Gold model."""
    ReportGenerator().print_bsg_explainer()


@cli.command()
def watch():
    """Start daemon: hourly immediate alerts + weekly full report."""
    console.rule("[bold blue]Starting Job Watch Daemon[/bold blue]")
    JobScheduler().start_daemon()


@cli.command()
@click.option("--output", default="ai_jobs_export.json", help="Output file path")
def export(output):
    """Export the last scan cache to a JSON file."""
    if not os.path.exists(DATA_FILE):
        console.print("[red]No cached data found. Run `python app.py scan` first.[/red]")
        return
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        console.print(f"[green]Exported {data.get('count', '?')} jobs to {output}[/green]")
    except Exception as exc:
        console.print(f"[red]Export failed: {exc}[/red]")


def _save_export(jobs, funding, analysis):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "scanned_at": __import__("datetime").datetime.now().isoformat(),
                    "count": len(jobs),
                    "analysis": analysis,
                    "jobs": [j.to_dict() for j in jobs],
                    "funding_signals": [fs.to_dict() for fs in funding],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        console.print(f"[green]Results saved to {DATA_FILE}[/green]")
    except Exception as exc:
        console.print(f"[yellow]Could not save cache: {exc}[/yellow]")


if __name__ == "__main__":
    cli()
