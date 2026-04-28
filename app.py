import logging
import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

import config
import dd_client

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# --- logging setup ---
os.makedirs("logs", exist_ok=True)
_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
triage_log = logging.getLogger("triage")
triage_log.setLevel(logging.INFO)
triage_log.addHandler(_handler)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw = request.form.get("finding_ids", "")
        ids = [line.strip() for line in raw.splitlines() if line.strip().isdigit()]
        if not ids:
            return render_template("index.html", error="Введите хотя бы один числовой ID.")
        session["finding_ids"] = ids
        return redirect(url_for("findings"))
    return render_template("index.html")


@app.route("/findings")
def findings():
    ids = session.get("finding_ids", [])
    if not ids:
        return redirect(url_for("index"))

    results = []
    for fid in ids:
        try:
            finding = dd_client.get_finding(int(fid))
            # Try to enrich inline notes if not already present
            inline_notes = finding.get("notes") or []
            if not inline_notes:
                inline_notes = dd_client.get_notes(int(fid))
            finding["_notes"] = inline_notes
            results.append({"ok": True, "finding": finding})
        except Exception as exc:
            results.append({"ok": False, "id": fid, "error": str(exc)})

    return render_template("findings.html", results=results)


# ---------------------------------------------------------------------------
# API endpoints called by the front-end JS
# ---------------------------------------------------------------------------

@app.route("/api/accept/<int:finding_id>", methods=["POST"])
def accept(finding_id):
    try:
        dd_client.close_as_false_positive(finding_id)
        triage_log.info("ACCEPT | finding_id=%s | closed as false-positive", finding_id)
        return jsonify({"status": "ok", "message": "Сработка закрыта как false-positive."})
    except Exception as exc:
        triage_log.error("ACCEPT ERROR | finding_id=%s | %s", finding_id, exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/reject/<int:finding_id>", methods=["POST"])
def reject(finding_id):
    body = request.get_json(silent=True) or {}
    reason = (body.get("reason") or "").strip()
    triage_log.info(
        "REJECT | finding_id=%s | reason=%r", finding_id, reason or "<no reason>"
    )
    return jsonify({"status": "ok", "message": "Отклонение записано в лог."})


@app.route("/api/correct/<int:finding_id>", methods=["POST"])
def correct(finding_id):
    body = request.get_json(silent=True) or {}
    comment = (body.get("comment") or "").strip()
    if not comment:
        return jsonify({"status": "error", "message": "Комментарий не может быть пустым."}), 400
    try:
        dd_client.close_as_false_positive(finding_id)
        dd_client.add_note(finding_id, comment)
        triage_log.info(
            "CORRECT | finding_id=%s | closed as false-positive + note added | comment=%r",
            finding_id,
            comment,
        )
        return jsonify({"status": "ok", "message": "Закрыто как false-positive, комментарий добавлен."})
    except Exception as exc:
        triage_log.error("CORRECT ERROR | finding_id=%s | %s", finding_id, exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
