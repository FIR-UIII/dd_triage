import json
import logging
import os
import uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

import config
import dd_client

_upload_store: dict = {}  # upload_id -> list of result dicts

# Лимиты для загрузки файлов от DoS
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10 MB total file size
_MAX_LINE_BYTES   = 512 * 1024         # 512 KB per single line
_MAX_LINES        = 5_000              # max findings per file
_MAX_STORE_SLOTS  = 50                 # max concurrent uploads kept in memory
_ALLOWED_EXTENSIONS = {".jsonl", ".json"}

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# тут буду логгировать
os.makedirs("logs", exist_ok=True)
_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
triage_log = logging.getLogger("triage")
triage_log.setLevel(logging.INFO)
triage_log.addHandler(_handler)


# Задаем пути

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        prefixurl = "https://ddojo.dev.rosatom.local/finding/"
        raw = request.form.get("finding_ids", "")
        ids = [line.strip().removeprefix(prefixurl) for line in raw.splitlines() if line.strip().removeprefix(prefixurl).isdigit()]
        if not ids:
            return render_template("index.html", error="Введите хотя бы один числовой ID.")
        session.pop("upload_id", None)
        session["finding_ids"] = ids
        return redirect(url_for("findings"))
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("jsonl_file")
    if not f or not f.filename:
        return render_template("index.html", error="Выберите JSONL-файл.", active_tab="upload")

    # Проверка по расширению
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        return render_template("index.html", error="Допустимы только файлы .jsonl или .json.", active_tab="upload")

    results = []
    parse_errors = []
    total_bytes = 0
    finding_count = 0

    for i, raw_line in enumerate(f.stream, 1):
        # Проверка общего размера файла
        total_bytes += len(raw_line)
        if total_bytes > _MAX_UPLOAD_BYTES:
            return render_template("index.html",
                                   error=f"Файл превышает допустимый размер ({_MAX_UPLOAD_BYTES // 1024 // 1024} МБ).",
                                   active_tab="upload")

        # Проверка размера строки
        if len(raw_line) > _MAX_LINE_BYTES:
            parse_errors.append(f"Строка {i}: слишком длинная, пропущена")
            continue

        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue

        # Проверка количества записей
        finding_count += 1
        if finding_count > _MAX_LINES:
            return render_template("index.html",
                                   error=f"Файл содержит более {_MAX_LINES} записей.",
                                   active_tab="upload")

        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            # Don't echo parse details — they contain raw input fragments
            parse_errors.append(f"Строка {i}: некорректный JSON")
            continue

        # Защита json.loads проверка что это валидный JSON-объект, а не массив или примитив
        if not isinstance(obj, dict):
            parse_errors.append(f"Строка {i}: ожидается JSON-объект, получен {type(obj).__name__}")
            continue

        # Проверка наличия обязательного поля "id"
        if "id" not in obj:
            parse_errors.append(f"Строка {i}: отсутствует поле 'id'")
            continue

        obj["_notes"] = obj.get("notes") or []
        results.append({"ok": True, "finding": obj})

    if not results:
        msg = "Файл пуст или не содержит валидных JSON-объектов."
        if parse_errors:
            msg += f" Ошибок парсинга: {len(parse_errors)}."
        return render_template("index.html", error=msg, active_tab="upload")

    # Ограничение количества хранимых загрузок в памяти, удаляя самые старые
    if len(_upload_store) >= _MAX_STORE_SLOTS:
        _upload_store.pop(next(iter(_upload_store)))

    uid = str(uuid.uuid4())
    _upload_store[uid] = results
    session.pop("finding_ids", None)
    session["upload_id"] = uid
    return redirect(url_for("findings"))


@app.route("/findings")
def findings():
    upload_id = session.get("upload_id")
    if upload_id and upload_id in _upload_store:
        return render_template("findings.html", results=_upload_store[upload_id])

    ids = session.get("finding_ids", [])
    if not ids:
        return redirect(url_for("index"))

    results = []
    for fid in ids:
        try:
            finding = dd_client.get_finding(int(fid))
            inline_notes = finding.get("notes") or []
            if not inline_notes:
                inline_notes = dd_client.get_notes(int(fid))
            finding["_notes"] = inline_notes
            results.append({"ok": True, "finding": finding})
        except Exception as exc:
            results.append({"ok": False, "id": fid, "error": str(exc)})

    return render_template("findings.html", results=results)


# API для работы самой приложки (обработка запросов с фронта)

# закрыть сработка как есть - разметка верная, в дд закрываем как FP
@app.route("/api/accept/<int:finding_id>", methods=["POST"])
def accept(finding_id):
    try:
        dd_client.close_as_false_positive(finding_id)
        triage_log.info("ACCEPT | finding_id=%s | closed as false-positive", finding_id)
        return jsonify({"status": "ok", "message": "Сработка закрыта как false-positive."})
    except Exception as exc:
        triage_log.error("ACCEPT ERROR | finding_id=%s | %s", finding_id, exc)
        return jsonify({"status": "error", "message": str(exc)}), 500

# отклонить разметку - в дд ничего не пишем, записываем в лог
@app.route("/api/reject/<int:finding_id>", methods=["POST"])
def reject(finding_id):
    body = request.get_json(silent=True) or {}
    reason = (body.get("reason") or "").strip()
    triage_log.info(
        "REJECT | finding_id=%s | комментарий_ИБ=%r", finding_id, reason or "<no reason>"
    )
    return jsonify({"status": "ok", "message": "Отклонение записано в лог."})

# принять но скорректировать - в дд закрываем как FP и добавляем свой комментарий
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
    app.run(debug=True, host="0.0.0.0", port=5000) # пока не дебаге, немаршрутизируемый интерфейс для запуска в образе
