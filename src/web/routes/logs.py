"""Logs blueprint — serves recent log lines.

Routes:
    GET /api/logs?lines=100    Last N lines from output/dashboard.log
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from src.web.state_reader import read_log_tail

logs_bp = Blueprint("logs", __name__)

_MAX_LINES = 500
_DEFAULT_LINES = 100


@logs_bp.route("/api/logs")
def api_logs():
    try:
        n = int(request.args.get("lines", _DEFAULT_LINES))
    except (ValueError, TypeError):
        n = _DEFAULT_LINES
    n = max(1, min(n, _MAX_LINES))
    lines = read_log_tail(current_app.config["OUTPUT_DIR"], n)
    return jsonify({"lines": lines, "count": len(lines)})
