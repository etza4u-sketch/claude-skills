"""Generate formatted reports with Rich tables and panels."""
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.style import Style

from searchers.base import Job
from signals.funding import FundingSignal

console = Console()

TIER_COLORS = {
    "Gold": "bold yellow",
    "Silver": "bold white",
    "Bronze": "bold dark_orange",
}

TIER_ICONS = {
    "Gold": "🥇",
    "Silver": "🥈",
    "Bronze": "🥉",
}


class ReportGenerator:

    def print_jobs_table(
        self,
        jobs: list[Job],
        title: str = "AI Engineer Jobs — Israel",
        max_rows: int = 20,
    ) -> None:
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_lines=True,
            header_style="bold cyan",
            title_style="bold magenta",
        )
        table.add_column("Tier", width=8)
        table.add_column("Score", width=6, justify="right")
        table.add_column("Title", min_width=30)
        table.add_column("Company", min_width=15)
        table.add_column("Location", min_width=12)
        table.add_column("Source", min_width=12)
        table.add_column("Published", min_width=10)

        sorted_jobs = sorted(
            jobs, key=lambda j: ({"Gold": 3, "Silver": 2, "Bronze": 1}.get(j.tier, 0),
                                  j.urgency_score), reverse=True
        )

        for job in sorted_jobs[:max_rows]:
            tier = job.tier or "Bronze"
            color = TIER_COLORS.get(tier, "white")
            icon = TIER_ICONS.get(tier, "")

            pub = job.published_at.strftime("%Y-%m-%d") if job.published_at else "—"

            table.add_row(
                Text(f"{icon} {tier}", style=color),
                Text(f"{job.urgency_score:.1f}", style="bold"),
                Text(job.title[:55], style="bold"),
                Text(job.company[:25]),
                Text(job.location[:18]),
                Text(job.source[:18]),
                Text(pub),
            )

        console.print()
        console.print(table)

    def print_funding_signals(self, signals: list[FundingSignal]) -> None:
        if not signals:
            console.print("[dim]No funding signals found.[/dim]")
            return

        table = Table(
            title="💰 Funding Signals → Future Hiring",
            box=box.ROUNDED,
            header_style="bold green",
            title_style="bold green",
        )
        table.add_column("Tier", width=8)
        table.add_column("Company", min_width=18)
        table.add_column("Amount", width=10)
        table.add_column("Round", min_width=10)
        table.add_column("Predicted Hiring", min_width=40)
        table.add_column("Date", width=12)

        sorted_signals = sorted(
            signals,
            key=lambda s: {"Gold": 3, "Silver": 2, "Bronze": 1}.get(s.tier, 0),
            reverse=True,
        )

        for sig in sorted_signals[:15]:
            color = TIER_COLORS.get(sig.tier, "white")
            icon = TIER_ICONS.get(sig.tier, "")
            pub = sig.published_at.strftime("%Y-%m-%d") if sig.published_at else "—"

            table.add_row(
                Text(f"{icon} {sig.tier}", style=color),
                Text(sig.company[:20], style="bold"),
                Text(sig.amount),
                Text(sig.round_type),
                Text(sig.hiring_prediction[:55]),
                Text(pub),
            )

        console.print()
        console.print(table)

    def print_market_summary(self, analysis: dict) -> None:
        total = analysis.get("total_jobs", 0)
        tiers = analysis.get("tier_breakdown", {})
        heat = analysis.get("market_heat", "—")
        top_skills = analysis.get("top_skills", [])
        hot_domains = analysis.get("hot_domains", [])
        top_companies = analysis.get("top_hiring_companies", [])
        top_cities = analysis.get("top_cities", [])

        # Summary panel
        summary_lines = [
            f"[bold cyan]Total jobs found:[/bold cyan] {total}",
            f"  [yellow]🥇 Gold:[/yellow]   {tiers.get('Gold', 0)}",
            f"  [white]🥈 Silver:[/white] {tiers.get('Silver', 0)}",
            f"  [dark_orange]🥉 Bronze:[/dark_orange] {tiers.get('Bronze', 0)}",
            "",
            f"[bold green]Market Heat Index:[/bold green] {heat}",
            f"[bold green]Funding Signals:[/bold green] "
            f"{analysis.get('funding_signals', 0)} "
            f"(Gold rounds: {analysis.get('gold_funding', 0)})",
        ]
        console.print(Panel(
            "\n".join(summary_lines),
            title="📊 Market Summary",
            border_style="blue",
        ))

        # Skills panel
        if top_skills:
            skill_text = "  ".join(
                f"[bold]{skill}[/bold] ({count})" for skill, count in top_skills
            )
            console.print(Panel(skill_text, title="🔥 Hottest Skills", border_style="yellow"))

        # Domains panel
        if hot_domains:
            domain_text = "  ".join(
                f"[bold]{domain}[/bold] ({count})" for domain, count in hot_domains
            )
            console.print(Panel(domain_text, title="🏭 Hot Domains", border_style="green"))

        # Cities
        if top_cities:
            cities_text = "  ".join(
                f"[bold]{city}[/bold] ({count})" for city, count in top_cities
            )
            console.print(Panel(cities_text, title="📍 Top Hiring Cities", border_style="magenta"))

    def print_immediate_alert(self, job: Job) -> None:
        tier = job.tier or "Bronze"
        color = TIER_COLORS.get(tier, "white")
        icon = TIER_ICONS.get(tier, "")
        console.print(Panel(
            f"{icon} [{color}]{tier}[/{color}] — Urgency: [bold]{job.urgency_score}/5.0[/bold]\n\n"
            f"[bold]{job.title}[/bold]\n"
            f"Company: {job.company}\n"
            f"Location: {job.location}\n"
            f"Source: {job.source}\n"
            f"URL: [link={job.url}]{job.url[:60]}[/link]\n\n"
            f"{job.description[:200]}...",
            title="🚨 Immediate Alert — Senior/Unique AI Job",
            border_style="red",
        ))

    def print_bsg_explainer(self) -> None:
        explainer = """
[bold yellow]🥇 GOLD[/bold yellow] — Hidden opportunities. These appear before formal job postings:
   • Companies that recently raised funding
   • New R&D centres opening
   • Leadership changes signalling team build-outs
   • "Founding engineer" / stealth-mode roles

[bold white]🥈 SILVER[/bold white] — Semi-visible. Distributed via recruiters and communities:
   • Fast-growing companies expanding teams
   • Jobs at known high-growth companies
   • Roles shared in professional networks before public posting
   • Senior positions at funded startups

[bold dark_orange]🥉 BRONZE[/bold dark_orange] — Visible public jobs on job boards:
   • High competition, short window to apply
   • Act fast — many applicants within hours of posting
        """
        console.print(Panel(
            explainer.strip(),
            title="📖 Bronze / Silver / Gold Model",
            border_style="cyan",
        ))
