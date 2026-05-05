"""Flask web application for the AI Job Search dashboard."""
import sys
import os
import json
import threading
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, jsonify, request, Response
from config import AI_KEYWORDS, ALERT_URGENCY_THRESHOLD, DATA_FILE
from searchers import DrushimSearcher, IndeedSearcher, RSSSearcher
from classifiers import BSGClassifier, SeniorityClassifier
from signals import FundingSignalDetector, MarketSignalAnalyzer

app = Flask(__name__)

# ── In-memory state ──────────────────────────────────────────────────────────
_state = {
    "scanning": False,
    "last_scan": None,
    "jobs": [],
    "funding": [],
    "analysis": {},
    "progress": [],          # list of progress messages streamed to UI
}
_lock = threading.Lock()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _push(msg: str):
    with _lock:
        _state["progress"].append(msg)


def _run_scan():
    with _lock:
        _state["scanning"] = True
        _state["progress"] = []

    _push("🔍 Starting scan…")
    searchers = [
        ("drushim.co.il", DrushimSearcher()),
        ("indeed.com",    IndeedSearcher()),
        ("RSS feeds",     RSSSearcher()),
    ]
    sc = SeniorityClassifier()
    bc = BSGClassifier()
    jobs = []

    for name, searcher in searchers:
        _push(f"📡 Scanning {name}…")
        try:
            fetched = searcher.search(AI_KEYWORDS)
            for job in fetched:
                sc.classify(job)
                bc.classify(job)
            jobs.extend(fetched)
            _push(f"✅ {name}: {len(fetched)} jobs found")
        except Exception as exc:
            _push(f"⚠️ {name}: {exc}")

    # Deduplicate
    seen = {}
    for job in jobs:
        seen[job.id] = job
    jobs = list(seen.values())
    _push(f"🧹 Deduplicated → {len(jobs)} unique jobs")

    _push("💰 Scanning funding news…")
    try:
        funding = FundingSignalDetector().scan()
        _push(f"✅ {len(funding)} funding signals found")
    except Exception as exc:
        _push(f"⚠️ Funding scan: {exc}")
        funding = []

    analysis = MarketSignalAnalyzer().analyze(jobs, funding)
    _push("📊 Analysis complete. Done!")

    with _lock:
        _state["jobs"] = [j.to_dict() for j in jobs]
        _state["funding"] = [f.to_dict() for f in funding]
        _state["analysis"] = {
            **analysis,
            "top_skills": analysis.get("top_skills", []),
            "hot_domains": analysis.get("hot_domains", []),
            "top_hiring_companies": analysis.get("top_hiring_companies", []),
            "top_cities": analysis.get("top_cities", []),
        }
        _state["last_scan"] = datetime.now().isoformat()
        _state["scanning"] = False

    # Persist to disk
    try:
        with open(os.path.join(os.path.dirname(__file__), "..", DATA_FILE), "w") as f:
            json.dump({"scanned_at": _state["last_scan"],
                       "count": len(jobs),
                       "jobs": _state["jobs"],
                       "funding_signals": _state["funding"]},
                      f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def api_scan():
    with _lock:
        if _state["scanning"]:
            return jsonify({"status": "already_running"}), 409
    t = threading.Thread(target=_run_scan, daemon=True)
    t.start()
    return jsonify({"status": "started"})


@app.route("/api/progress")
def api_progress():
    """Server-Sent Events stream for scan progress."""
    def generate():
        sent = 0
        import time
        while True:
            with _lock:
                msgs = _state["progress"]
                scanning = _state["scanning"]
            while sent < len(msgs):
                yield f"data: {json.dumps({'msg': msgs[sent]})}\n\n"
                sent += 1
            if not scanning and sent >= len(msgs):
                yield f"data: {json.dumps({'done': True})}\n\n"
                break
            time.sleep(0.4)
    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/jobs")
def api_jobs():
    tier = request.args.get("tier", "all").lower()
    senior_only = request.args.get("senior") == "1"
    min_score = float(request.args.get("min_score", 0))

    with _lock:
        jobs = list(_state["jobs"])

    if tier != "all":
        jobs = [j for j in jobs if (j.get("tier") or "bronze").lower() == tier]
    if senior_only:
        jobs = [j for j in jobs if j.get("is_senior")]
    if min_score > 0:
        jobs = [j for j in jobs if j.get("urgency_score", 0) >= min_score]

    jobs.sort(key=lambda j: (
        {"gold": 3, "silver": 2, "bronze": 1}.get((j.get("tier") or "bronze").lower(), 0),
        j.get("urgency_score", 0),
    ), reverse=True)

    return jsonify({"jobs": jobs, "total": len(jobs)})


@app.route("/api/funding")
def api_funding():
    with _lock:
        return jsonify({"signals": _state["funding"]})


@app.route("/api/analysis")
def api_analysis():
    with _lock:
        return jsonify({
            "analysis": _state["analysis"],
            "last_scan": _state["last_scan"],
            "scanning": _state["scanning"],
        })


@app.route("/api/status")
def api_status():
    with _lock:
        return jsonify({
            "scanning": _state["scanning"],
            "last_scan": _state["last_scan"],
            "job_count": len(_state["jobs"]),
            "funding_count": len(_state["funding"]),
        })


if __name__ == "__main__":
    # Try to load previous scan from disk on startup
    cache_path = os.path.join(os.path.dirname(__file__), "..", DATA_FILE)
    if os.path.exists(cache_path):
        try:
            with open(cache_path) as f:
                cached = json.load(f)
            _state["jobs"] = cached.get("jobs", [])
            _state["funding"] = cached.get("funding_signals", [])
            _state["last_scan"] = cached.get("scanned_at")
            _state["analysis"] = MarketSignalAnalyzer().analyze(
                [], []
            )  # empty placeholder
        except Exception:
            pass

    port = int(os.environ.get("PORT", 5050))
    print(f"\n🚀  AI Job Search webapp → http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
