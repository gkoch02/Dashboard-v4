"""Image blueprint — serves rendered dashboard PNGs.

Routes:
    GET /image/latest          Most recent dashboard render (output/latest.png)
    GET /image/theme/<name>    Pre-generated theme preview (output/theme_<name>.png)
"""

from __future__ import annotations

import re
from pathlib import Path

from flask import Blueprint, current_app, send_file
from werkzeug.exceptions import NotFound

image_bp = Blueprint("image", __name__)

# Allowlist: only filenames matching [a-z0-9_] to prevent path traversal.
_SAFE_NAME_RE = re.compile(r"^[a-z0-9_]+$")


@image_bp.route("/image/latest")
def latest():
    path = Path(current_app.config["OUTPUT_DIR"]) / "latest.png"
    if not path.exists():
        raise NotFound("No dashboard image has been rendered yet.")
    response = send_file(path, mimetype="image/png", max_age=0)
    # Prevent all caching so the browser always fetches a fresh copy.
    response.headers["Cache-Control"] = "no-store"
    return response


@image_bp.route("/image/theme/<name>")
def theme_preview(name: str):
    if not _SAFE_NAME_RE.match(name):
        raise NotFound("Invalid theme name.")
    path = Path(current_app.config["OUTPUT_DIR"]) / f"theme_{name}.png"
    if not path.exists():
        raise NotFound(f"No preview for theme '{name}'. Run 'make previews' to generate them.")
    return send_file(path, mimetype="image/png", max_age=3600)
