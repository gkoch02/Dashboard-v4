"""Simple CSRF protection helpers for the Dashboard web UI.

This is intentionally lightweight: we mint a random session-bound token and
require clients to echo it in an ``X-CSRF-Token`` header for all mutating
requests. The token is also exposed to templates so the existing vanilla JS can
pick it up without any framework/session dependency.
"""

from __future__ import annotations

import secrets

from flask import abort, request, session

_SESSION_KEY = "csrf_token"


def get_csrf_token() -> str:
    token = session.get(_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[_SESSION_KEY] = token
    return token


def csrf_protect() -> None:
    expected = get_csrf_token()
    provided = request.headers.get("X-CSRF-Token", "")
    if not provided or provided != expected:
        abort(403)
