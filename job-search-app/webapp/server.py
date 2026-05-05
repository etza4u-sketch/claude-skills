"""Flask web application — AI Job Search dashboard."""
import sys, os, json, threading, csv, io
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from config import AI_KEYWORDS, ALERT_URGENCY_THRESHOLD, DATA_FILE
from searchers import DrushimSearcher, IndeedSearcher, RSSSearcher
from classifiers import BSGClassifier, SeniorityClassifier
from signals import FundingSignalDetector, MarketSignalAnalyzer

app = Flask(__name__)

# ── shared state ─────────────────────────────────────────────────────────────
_state = {
    "scanning": False,
    "last_scan": None,
    "jobs": [],
    "funding": [],
    "analysis": {},
    "log": [],
}
_lock = threading.Lock()

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", DATA_FILE)


def _log(msg: str):
    with _lock:
        _state["log"].append(msg)


# ── scan worker ───────────────────────────────────────────────────────────────
def _run_scan():
    with _lock:
        _state["scanning"] = True
        _state["log"] = []

    _log("🔍 מתחיל סריקה…")
    sc = SeniorityClassifier()
    bc = BSGClassifier()
    jobs = []

    for label, searcher in [
        ("drushim.co.il",  DrushimSearcher()),
        ("indeed.com",     IndeedSearcher()),
        ("RSS / חדשות",    RSSSearcher()),
    ]:
        _log(f"📡 סורק {label}…")
        try:
            fetched = searcher.search(AI_KEYWORDS)
            for j in fetched:
                sc.classify(j)
                bc.classify(j)
            jobs.extend(fetched)
            _log(f"✅ {label}: נמצאו {len(fetched)} משרות")
        except Exception as e:
            _log(f"⚠️ {label}: {e}")

    seen = {}
    for j in jobs:
        seen[j.id] = j
    jobs = list(seen.values())
    _log(f"🧹 לאחר ניקוי כפילויות: {len(jobs)} משרות ייחודיות")

    _log("💰 סורק חדשות גיוס הון…")
    try:
        funding = FundingSignalDetector().scan()
        _log(f"✅ נמצאו {len(funding)} איתותי גיוס הון")
    except Exception as e:
        _log(f"⚠️ גיוס הון: {e}")
        funding = []

    analysis = MarketSignalAnalyzer().analyze(jobs, funding)
    _log("📊 הניתוח הושלם. סיום!")

    now = datetime.now().isoformat()
    with _lock:
        _state["jobs"]      = [j.to_dict() for j in jobs]
        _state["funding"]   = [f.to_dict() for f in funding]
        _state["analysis"]  = analysis
        _state["last_scan"] = now
        _state["scanning"]  = False

    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"scanned_at": now, "count": len(jobs),
                       "jobs": _state["jobs"],
                       "funding_signals": _state["funding"]},
                      f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def api_scan():
    with _lock:
        if _state["scanning"]:
            return jsonify({"status": "already_running"}), 409
    threading.Thread(target=_run_scan, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/api/progress")
def api_progress():
    """Server-Sent Events — streams log lines while scanning."""
    def generate():
        import time
        sent = 0
        while True:
            with _lock:
                msgs     = list(_state["log"])
                scanning = _state["scanning"]
            while sent < len(msgs):
                yield f"data: {json.dumps({'msg': msgs[sent]})}\n\n"
                sent += 1
            if not scanning and sent >= len(msgs):
                yield f"data: {json.dumps({'done': True})}\n\n"
                break
            time.sleep(0.35)
    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/api/jobs")
def api_jobs():
    tier       = request.args.get("tier", "all").lower()
    senior     = request.args.get("senior") == "1"
    min_score  = float(request.args.get("min_score", 0))
    q          = request.args.get("q", "").lower().strip()
    page       = int(request.args.get("page", 1))
    per_page   = int(request.args.get("per_page", 20))

    with _lock:
        jobs = list(_state["jobs"])

    if tier != "all":
        jobs = [j for j in jobs if (j.get("tier") or "bronze").lower() == tier]
    if senior:
        jobs = [j for j in jobs if j.get("is_senior")]
    if min_score > 0:
        jobs = [j for j in jobs if j.get("urgency_score", 0) >= min_score]
    if q:
        jobs = [j for j in jobs
                if q in (j.get("title","") + j.get("company","") + j.get("description","")).lower()]

    jobs.sort(key=lambda j: (
        {"gold": 3, "silver": 2, "bronze": 1}.get((j.get("tier") or "bronze").lower(), 0),
        j.get("urgency_score", 0),
    ), reverse=True)

    total   = len(jobs)
    start   = (page - 1) * per_page
    paginated = jobs[start: start + per_page]

    return jsonify({"jobs": paginated, "total": total,
                    "page": page, "per_page": per_page,
                    "pages": max(1, -(-total // per_page))})


@app.route("/api/job/<job_id>")
def api_job_detail(job_id):
    with _lock:
        jobs = _state["jobs"]
    for j in jobs:
        if j.get("id") == job_id:
            return jsonify(j)
    return jsonify({"error": "not found"}), 404


@app.route("/api/funding")
def api_funding():
    with _lock:
        return jsonify({"signals": _state["funding"]})


@app.route("/api/analysis")
def api_analysis():
    with _lock:
        a = dict(_state["analysis"])
        # Convert Counter tuples to plain lists for JSON
        for k in ("top_skills", "hot_domains", "top_hiring_companies", "top_cities"):
            if k in a:
                a[k] = [[item[0], item[1]] for item in a[k]]
        return jsonify({"analysis": a,
                        "last_scan": _state["last_scan"],
                        "scanning":  _state["scanning"]})


@app.route("/api/status")
def api_status():
    with _lock:
        return jsonify({"scanning":      _state["scanning"],
                        "last_scan":     _state["last_scan"],
                        "job_count":     len(_state["jobs"]),
                        "funding_count": len(_state["funding"])})


@app.route("/api/export/csv")
def api_export_csv():
    with _lock:
        jobs = list(_state["jobs"])
    if not jobs:
        return jsonify({"error": "no data"}), 404

    buf = io.StringIO()
    w   = csv.DictWriter(buf, fieldnames=[
        "id","tier","urgency_score","is_senior","title","company",
        "location","source","published_at","salary","url","description"])
    w.writeheader()
    for j in jobs:
        row = {k: j.get(k,"") for k in w.fieldnames}
        row["description"] = (row.get("description") or "")[:200]
        w.writerow(row)

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ai_jobs.csv"}
    )


# ── startup ───────────────────────────────────────────────────────────────────
def _load_cache():
    if not os.path.exists(CACHE_PATH):
        return
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            cached = json.load(f)
        with _lock:
            _state["jobs"]      = cached.get("jobs", [])
            _state["funding"]   = cached.get("funding_signals", [])
            _state["last_scan"] = cached.get("scanned_at")
        print(f"  Loaded {len(_state['jobs'])} cached jobs from disk.")
    except Exception as e:
        print(f"  Cache load failed: {e}")


if __name__ == "__main__":
    _load_cache()
    port = int(os.environ.get("PORT", 5050))
    print(f"\n🚀  AI Job Search  →  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
