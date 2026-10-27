"""Smoke test for app.py imports and configuration."""

import pytest


def test_app_imports_and_definitions():
    """Verify app.py imports and health check function without starting UI server."""
    import app

    # Check health check function runs without uncaught crash
    is_conn, info, err = app.check_db_health()
    assert isinstance(is_conn, bool)
    if not is_conn:
        assert err is not None
