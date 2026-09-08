"""Shared fixtures."""

from __future__ import annotations

import pytest

from freshkeeper.db.session import init_db, make_engine, make_session_factory


@pytest.fixture
def session_factory():
    """A fresh in-memory database per test."""
    engine = make_engine(":memory:")
    init_db(engine)
    return make_session_factory(engine)


@pytest.fixture
def client(session_factory):
    """Flask test client with a known token and no model loaded."""
    from freshkeeper.api.app import create_app
    app = create_app(":memory:", auth_token="testtoken")
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def auth():
    return {"Authorization": "Bearer testtoken"}
