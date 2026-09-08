"""Tests for the REST API: auth, validation, and the state machine."""

from __future__ import annotations

import json


def add_item(client, auth, slot=0, name="Strawberries",
             commodity="strawberry", mass=250.0):
    return client.post("/api/items", headers=auth, json={
        "slot_id": slot, "name": name, "commodity": commodity,
        "initial_mass_g": mass,
    })


class TestAuth:
    def test_health_is_public(self, client):
        assert client.get("/api/health").status_code == 200

    def test_protected_routes_need_a_token(self, client):
        for path in ("/api/items", "/api/alerts", "/api/stats", "/api/readings/0"):
            assert client.get(path).status_code == 401

    def test_a_wrong_token_is_rejected(self, client):
        assert client.get("/api/items",
                          headers={"Authorization": "Bearer nope"}).status_code == 401

    def test_a_malformed_header_is_rejected(self, client):
        assert client.get("/api/items",
                          headers={"Authorization": "testtoken"}).status_code == 401


class TestItems:
    def test_create_and_list(self, client, auth):
        response = add_item(client, auth)
        assert response.status_code == 201
        body = response.get_json()
        assert body["name"] == "Strawberries" and body["slot_id"] == 0
        assert len(client.get("/api/items", headers=auth).get_json()) == 1

    def test_missing_fields_are_reported(self, client, auth):
        response = client.post("/api/items", headers=auth, json={"slot_id": 0})
        assert response.status_code == 400
        assert "missing fields" in response.get_json()["error"]

    def test_mass_must_be_a_positive_number(self, client, auth):
        assert add_item(client, auth, mass=-5).status_code == 400
        assert add_item(client, auth, slot=1, mass="heavy").status_code == 400

    def test_a_slot_holds_one_item_at_a_time(self, client, auth):
        add_item(client, auth, slot=0)
        conflict = add_item(client, auth, slot=0, name="Apples", commodity="apple")
        assert conflict.status_code == 409
        assert "already holds" in conflict.get_json()["error"]

    def test_a_slot_is_reusable_once_the_item_is_consumed(self, client, auth):
        add_item(client, auth, slot=0)
        client.post("/api/items/1/consume", headers=auth, json={"outcome": "eaten"})
        assert add_item(client, auth, slot=0, name="Apples",
                        commodity="apple").status_code == 201

    def test_unknown_item_is_404(self, client, auth):
        assert client.get("/api/items/999", headers=auth).status_code == 404


class TestLifecycle:
    def test_consume_requires_a_valid_outcome(self, client, auth):
        add_item(client, auth)
        response = client.post("/api/items/1/consume", headers=auth,
                               json={"outcome": "composted"})
        assert response.status_code == 400

    def test_an_item_cannot_be_consumed_twice(self, client, auth):
        add_item(client, auth)
        client.post("/api/items/1/consume", headers=auth, json={"outcome": "eaten"})
        assert client.post("/api/items/1/consume", headers=auth,
                           json={"outcome": "eaten"}).status_code == 409

    def test_snooze_returns_a_deadline(self, client, auth):
        add_item(client, auth)
        body = client.post("/api/items/1/snooze", headers=auth).get_json()
        assert body["ok"] and body["snoozed_until"]

    def test_override_accepts_valid_states_and_null(self, client, auth):
        add_item(client, auth)
        assert client.post("/api/items/1/override", headers=auth,
                           json={"state": "marginal"}).status_code == 200
        assert client.post("/api/items/1/override", headers=auth,
                           json={"state": None}).status_code == 200

    def test_override_rejects_nonsense(self, client, auth):
        add_item(client, auth)
        assert client.post("/api/items/1/override", headers=auth,
                           json={"state": "rancid"}).status_code == 400


class TestStats:
    def test_empty_database(self, client, auth):
        body = client.get("/api/stats", headers=auth).get_json()
        assert body["items_tracked"] == 0 and body["waste_rate"] is None

    def test_waste_rate_counts_outcomes(self, client, auth):
        add_item(client, auth, slot=0)
        add_item(client, auth, slot=1, name="Apples", commodity="apple")
        client.post("/api/items/1/consume", headers=auth,
                    json={"outcome": "binned", "wasted_mass_g": 200})
        client.post("/api/items/2/consume", headers=auth, json={"outcome": "eaten"})
        body = client.get("/api/stats", headers=auth).get_json()
        assert body["binned"] == 1 and body["eaten"] == 1
        assert body["waste_rate"] == 0.5
        assert body["wasted_mass_g"] == 200.0


class TestCycle:
    def test_cycle_without_a_model_is_unavailable(self, client, auth):
        assert client.post("/api/cycle", headers=auth).status_code == 503


class TestFrontend:
    def test_index_is_served(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"FreshKeeper" in response.data
