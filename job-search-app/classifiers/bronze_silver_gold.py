"""
Bronze / Silver / Gold tier classifier.

Bronze  — Public, visible jobs on major job boards. High competition.
Silver  — Semi-visible: jobs at companies with recent funding or expansions,
           distributed via recruiters or communities before formal posting.
Gold    — Hidden signals: early indicators of future hiring — funding rounds,
           new office openings, leadership changes, team announcements.
"""
import re
from searchers.base import Job
from config import FUNDED_COMPANIES, SENIOR_KEYWORDS


# Companies known to be in rapid-growth mode (Silver+)
GROWTH_COMPANIES = {
    "gong", "ai21", "lemonade", "monday", "wiz", "snyk",
    "aqua security", "cato", "armis", "cybereason", "talon",
    "claroty", "hunter", "octup", "noma", "nvidia", "mobileye",
    "deloitte", "booking", "intuit", "palo alto", "dell", "citi",
    "jfrog", "uveye", "sensi", "anyword", "cyabra", "package.ai",
    "automat-it", "automat",
}

# Gold-tier signals: these phrases in description suggest hidden opportunity
GOLD_SIGNAL_PATTERNS = [
    r'new\s+(r&d|research)\s+center',
    r'expanding\s+(team|operations)',
    r'opening\s+new\s+office',
    r'recently\s+raised',
    r'series\s+[abcde]',
    r'seed\s+round',
    r'backed\s+by',
    r'stealth\s+mode',
    r'founding\s+(engineer|team)',
    r'building\s+from\s+scratch',
    # Hebrew
    r'גיוס\s+הון', r'סבב\s+(א|ב|ג|d|a|b|c)',
    r'פותחים\s+מרכז', r'מרכז\s+פיתוח\s+חדש',
]

# Silver-tier: company known to be in growth but job is standard posting
SILVER_SIGNAL_PATTERNS = [
    r'hybrid', r'flexible', r'remote.?first',
    r'growing\s+team', r'fast.?growing', r'scale.?up',
    r'join\s+our\s+team', r'mission.?driven',
]


class BSGClassifier:
    """Assigns each job a Bronze/Silver/Gold tier."""

    def classify(self, job: Job) -> Job:
        text = f"{job.title} {job.company} {job.description}".lower()
        company_lower = job.company.lower()

        # --- Gold detection ---
        gold_signals = sum(
            1 for p in GOLD_SIGNAL_PATTERNS if re.search(p, text)
        )
        is_known_funded = any(fc in company_lower for fc in FUNDED_COMPANIES)
        is_founding_role = bool(re.search(r'founding|first\s+\w+\s+hire|build\s+from', text))

        if gold_signals >= 2 or is_founding_role or (is_known_funded and job.is_senior):
            job.tier = "Gold"
            job.urgency_score = min(job.urgency_score + 0.5, 5.0)
            return job

        # --- Silver detection ---
        is_growth_company = any(gc in company_lower for gc in GROWTH_COMPANIES)
        silver_signals = sum(
            1 for p in SILVER_SIGNAL_PATTERNS if re.search(p, text)
        )
        has_senior_role = job.is_senior or any(
            re.search(rf'\b{kw}\b', text) for kw in SENIOR_KEYWORDS
        )

        if is_growth_company or silver_signals >= 2 or (has_senior_role and is_known_funded):
            job.tier = "Silver"
            job.urgency_score = min(job.urgency_score + 0.3, 5.0)
            return job

        # --- Bronze (default) ---
        job.tier = "Bronze"
        return job

    def classify_many(self, jobs: list[Job]) -> list[Job]:
        return [self.classify(j) for j in jobs]
