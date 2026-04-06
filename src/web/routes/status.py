"""Status blueprint — the main P1 read-only health page.

Routes:
    GET /              HTML status page
    GET /api/status    JSON health snapshot
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template

from src.web.state_reader import (
    is_quiet_hours_now,
    read_breakers,
    read_cache_ages,
    read_host_metrics,
    read_last_success,
    read_quota,
)

status_bp = Blueprint("status", __name__)


def _build_status() -> dict:
    """Assemble the full status payload from all state sources."""
    cfg = current_app.config["DASH_CFG"]
    state_dir = current_app.config["STATE_DIR"]
    output_dir = current_app.config["OUTPUT_DIR"]
    ttls = current_app.config["SOURCE_TTLS"]

    last_run = read_last_success(output_dir)
    breakers = read_breakers(state_dir)
    cache_ages = read_cache_ages(state_dir, ttls)
    quota = read_quota(state_dir)

    sources: dict = {}
    for source in ("events", "weather", "birthdays", "air_quality"):
        b = breakers.get(source, {})
        c = cache_ages.get(source, {})
        sources[source] = {
            "breaker_state": b.get("state", "closed"),
            "consecutive_failures": b.get("consecutive_failures", 0),
            "last_failure_at": b.get("last_failure_at"),
            "cache_age_minutes": c.get("cache_age_minutes"),
            "staleness": c.get("staleness", "unknown"),
            "fetched_at": c.get("fetched_at"),
            "quota_today": quota.get(source, quota.get(_quota_key(source), 0)),
        }

    return {
        "last_run": last_run["timestamp"],
        "seconds_since_run": last_run["seconds_since"],
        "current_theme": cfg.theme,
        "quiet_hours_active": is_quiet_hours_now(
            cfg.schedule.quiet_hours_start, cfg.schedule.quiet_hours_end
        ),
        "quiet_hours_start": cfg.schedule.quiet_hours_start,
        "quiet_hours_end": cfg.schedule.quiet_hours_end,
        "host": read_host_metrics(),
        "sources": sources,
    }


def _quota_key(source: str) -> str:
    """Map source names to quota tracker keys (Google Calendar uses 'google')."""
    return "google" if source == "events" else source


@status_bp.route("/")
def index():
    return render_template("status.html")


@status_bp.route("/api/status")
def api_status():
    return jsonify(_build_status())
