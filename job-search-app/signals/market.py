"""
Market signal analyzer — detects hot areas, trending skills,
and summarizes the overall hiring landscape.
"""
from collections import Counter
from searchers.base import Job
from signals.funding import FundingSignal


HOT_SKILLS = [
    "LLM", "RAG", "GenAI", "Generative AI", "Computer Vision",
    "NLP", "MLOps", "Agentic AI", "Fine-tuning", "Prompt Engineering",
    "Vector DB", "Transformer", "PyTorch", "LangChain", "Hugging Face",
    "SageMaker", "Kubernetes", "Deep Learning",
]

HOT_DOMAINS = [
    "Cybersecurity", "FinTech", "HealthTech", "Autonomous Vehicles",
    "Defense", "E-Commerce", "EdTech", "Agriculture AI",
]

DOMAIN_KEYWORDS = {
    "Cybersecurity": ["security", "cyber", "threat", "malware", "siem", "soc"],
    "FinTech": ["finance", "fintech", "banking", "payment", "trading", "investment"],
    "HealthTech": ["health", "medical", "clinical", "pharma", "diagnostic"],
    "Autonomous Vehicles": ["autonomous", "self-driving", "adas", "lidar", "automotive"],
    "Defense": ["defense", "military", "idf", "intelligence", "surveillance"],
    "E-Commerce": ["ecommerce", "retail", "marketplace", "shopping"],
    "EdTech": ["education", "learning", "student", "university", "course"],
    "Agriculture AI": ["agriculture", "agri", "crop", "farm"],
}


class MarketSignalAnalyzer:
    def analyze(
        self,
        jobs: list[Job],
        funding_signals: list[FundingSignal],
    ) -> dict:
        skill_counts = Counter()
        domain_counts = Counter()
        tier_counts = Counter()
        company_counts = Counter()
        location_counts = Counter()

        for job in jobs:
            text = f"{job.title} {job.description}".lower()

            # Count skills
            for skill in HOT_SKILLS:
                if skill.lower() in text:
                    skill_counts[skill] += 1

            # Count domains
            for domain, keywords in DOMAIN_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    domain_counts[domain] += 1

            tier_counts[job.tier or "Bronze"] += 1
            if job.company and job.company != "Unknown":
                company_counts[job.company] += 1
            if job.location:
                for city in ["Tel Aviv", "Herzliya", "Jerusalem", "Haifa",
                             "Be'er Sheva", "Petah Tikva", "Ramat Gan"]:
                    if city.lower() in job.location.lower():
                        location_counts[city] += 1

        # Summary
        total = len(jobs)
        gold_count = tier_counts.get("Gold", 0)
        silver_count = tier_counts.get("Silver", 0)
        bronze_count = tier_counts.get("Bronze", 0)

        return {
            "total_jobs": total,
            "tier_breakdown": {
                "Gold": gold_count,
                "Silver": silver_count,
                "Bronze": bronze_count,
            },
            "top_skills": skill_counts.most_common(8),
            "hot_domains": domain_counts.most_common(5),
            "top_hiring_companies": company_counts.most_common(10),
            "top_cities": location_counts.most_common(5),
            "funding_signals": len(funding_signals),
            "gold_funding": sum(
                1 for fs in funding_signals if fs.tier == "Gold"
            ),
            "market_heat": self._heat_index(total, gold_count, len(funding_signals)),
        }

    def _heat_index(self, total: int, gold: int, funding: int) -> str:
        score = min(total / 10, 5) + gold * 0.5 + funding * 0.3
        if score >= 8:
            return "🔥🔥🔥 Very Hot"
        elif score >= 5:
            return "🔥🔥 Hot"
        elif score >= 2:
            return "🔥 Warm"
        return "❄️ Cool"
