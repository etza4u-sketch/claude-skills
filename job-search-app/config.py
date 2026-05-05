"""Configuration for the job search application."""

# Job search keywords for AI engineer positions
AI_KEYWORDS = [
    "AI engineer", "machine learning engineer", "ML engineer",
    "deep learning", "NLP engineer", "LLM engineer",
    "generative AI", "GenAI", "computer vision engineer",
    "MLOps engineer", "data scientist AI", "AI researcher",
    "artificial intelligence engineer", "מהנדס בינה מלאכותית",
    "מהנדס AI", "מדען נתונים", "LLM", "RAG engineer",
]

# Seniority keywords that trigger Gold/Silver alerts
SENIOR_KEYWORDS = [
    "senior", "lead", "principal", "head", "chief", "staff",
    "architect", "director", "manager", "בכיר", "מוביל", "ראש",
]

# Companies with recent funding (Gold signals)
FUNDED_COMPANIES = [
    "gong", "ai21", "aqua security", "lemonade", "monday.com",
    "wiz", "snyk", "cato networks", "talon", "claroty",
    "armis", "cybereason", "hunter.io", "octup", "noma",
]

# Funding signal keywords
FUNDING_KEYWORDS = [
    "raises", "funding", "seed round", "series a", "series b",
    "series c", "million", "investment", "backed by", "venture",
    "גייסה", "גיוס הון", "השקעה", "מימון",
]

# Job board URLs
JOB_BOARDS = {
    "drushim": "https://www.drushim.co.il/jobs/cat9/",  # hi-tech category
    "alljobs": "https://www.alljobs.co.il/SearchResults.aspx?position=artificial+intelligence",
    "linkedin_feed": "https://www.linkedin.com/jobs/search/?keywords=AI+engineer&location=Israel",
    "indeed_il": "https://il.indeed.com/jobs?q=AI+engineer&l=Israel",
    "glassdoor_il": "https://www.glassdoor.com/Job/israel-ai-engineer-jobs-SRCH_IL.0,6_IN119_KO7,18.htm",
}

# RSS / API feeds for funding news
NEWS_FEEDS = [
    "https://techcrunch.com/tag/israel/feed/",
    "https://www.calcalist.co.il/rss/0,7340,L-8,00.xml",
    "https://www.geektime.co.il/feed/",
]

# Alert thresholds
ALERT_URGENCY_THRESHOLD = 3.5  # minimum score to trigger immediate alert
WEEKLY_REPORT_DAY = "friday"
WEEKLY_REPORT_HOUR = "09:00"
HOURLY_CHECK_INTERVAL = 60  # minutes

# Output settings
MAX_JOBS_PER_REPORT = 20
DATA_FILE = "jobs_cache.json"
ALERTS_FILE = "alerts_history.json"
