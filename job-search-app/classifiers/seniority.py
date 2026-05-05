"""Classify job seniority level and compute urgency score."""
import re
from searchers.base import Job

SENIOR_PATTERNS = [
    r'\bsenior\b', r'\blead\b', r'\bprincipal\b', r'\bstaff\b',
    r'\bhead of\b', r'\bchief\b', r'\bdirector\b', r'\barchitect\b',
    r'\bmanager\b', r'\bvp\b', r'\bvice president\b',
    # Hebrew
    r'בכיר', r'מוביל', r'ראש', r'מנהל', r'אדריכל',
]

JUNIOR_PATTERNS = [
    r'\bjunior\b', r'\bentry.?level\b', r'\bintern\b', r'\bgraduate\b',
    r'\bjr\.\b', r'ג\'וניור', r'מתחיל',
]

# Bonus score per AI-speciality keyword found in title/description
SPECIALITY_SCORES = {
    "llm": 0.5,
    "large language model": 0.5,
    "generative ai": 0.5,
    "genai": 0.5,
    "rag": 0.4,
    "retrieval augmented": 0.4,
    "computer vision": 0.4,
    "nlp": 0.3,
    "mlops": 0.3,
    "deep learning": 0.3,
    "transformer": 0.3,
    "fine.?tun": 0.3,
    "agent": 0.2,
    "prompt engineering": 0.2,
    "vector db": 0.2,
    "embedding": 0.2,
}


class SeniorityClassifier:
    def classify(self, job: Job) -> Job:
        text = f"{job.title} {job.description}".lower()

        job.is_senior = any(re.search(p, text) for p in SENIOR_PATTERNS)

        # Base urgency: seniority raises score
        base = 2.0 if job.is_senior else 1.0
        if any(re.search(p, text) for p in JUNIOR_PATTERNS):
            base = 0.5

        # Add specialty bonuses (capped at 2.0 total bonus)
        bonus = 0.0
        for pattern, score in SPECIALITY_SCORES.items():
            if re.search(pattern, text):
                bonus += score
        bonus = min(bonus, 2.0)

        # Recency bonus (max 0.5 for jobs published today)
        recency = 0.0
        if job.published_at:
            from datetime import datetime, timezone
            try:
                pub = job.published_at
                if pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - pub).days
                recency = max(0.0, 0.5 - age_days * 0.1)
            except Exception:
                pass

        job.urgency_score = round(min(base + bonus + recency, 5.0), 1)
        return job
