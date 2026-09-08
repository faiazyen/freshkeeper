"""Flask application factory and REST API.

Endpoints
---------

    GET    /api/health                  liveness and model status
    GET    /api/items                   all tracked items with current state
    POST   /api/items                   register an item in a slot
    GET    /api/items/<id>              one item with its full history
    POST   /api/items/<id>/consume      record that it was eaten or binned
    POST   /api/items/<id>/snooze       silence its alerts for 24 hours
    POST   /api/items/<id>/override     set the state by hand
    GET    /api/readings/<slot_id>      recent sensor readings for a slot
    GET    /api/alerts                  currently active alerts
    GET    /api/stats                   waste-tracking summary
    GET    /api/settings                current settings
    POST   /api/settings                change settings (camera_enabled)
    POST   /api/cycle                   run one measurement cycle now

Authentication is a bearer token, generated on first run and printed to the
console. It is not much, but the device sits on a home network where anything
else on the LAN can reach it, and an unauthenticated API that reports when the
fridge was last opened is a nicer burglary aid than it first appears.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy import desc, select

from ..alerts import (
    SNOOZE_HOURS, evaluate_item, estimate_days_remaining, snooze_until,
)
from ..db.models import (
    ConsumptionEvent, FoodItem, ItemStatus, Outcome, SensorReading,
    SpoilagePrediction, SpoilageState,
)
from ..db.session import init_db, make_engine, make_session_factory, session_scope

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def create_app(db_path: str | Path = "data/freshkeeper.db",
               auth_token: str | None = None,
               inference_service=None) -> Flask:
    """Build the application.

    Args:
        db_path: SQLite file, or ":memory:" for tests.
        auth_token: bearer token; generated if not supplied.
        inference_service: object exposing ``predict_slot(slot_id)``. Injected
            so tests can run without loading a 14 MB model.
    """
    app = Flask(__name__, static_folder=None)
    engine = make_engine(db_path)
    init_db(engine)
    factory = make_session_factory(engine)

    app.config["AUTH_TOKEN"] = auth_token or secrets.token_urlsafe(24)
    app.config["SESSION_FACTORY"] = factory
    app.config["INFERENCE"] = inference_service

    def require_token(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            supplied = request.headers.get("Authorization", "")
            expected = f"Bearer {app.config['AUTH_TOKEN']}"
            # Constant-time compare: a naive == leaks the token a byte at a
            # time to anything that can measure response latency.
            if not secrets.compare_digest(supplied, expected):
                return jsonify({"error": "unauthorised"}), 401
            return view(*args, **kwargs)
        return wrapper

    # -- serving the interface --------------------------------------------

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:filename>")
    def static_files(filename):
        return send_from_directory(FRONTEND_DIR, filename)

    # -- API ---------------------------------------------------------------

    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "model_loaded": app.config["INFERENCE"] is not None,
            "time": datetime.now(timezone.utc).isoformat(),
        })

    def _latest_prediction(session, item_id: int) -> SpoilagePrediction | None:
        return session.scalars(
            select(SpoilagePrediction)
            .where(SpoilagePrediction.item_id == item_id)
            .order_by(desc(SpoilagePrediction.predicted_at))
            .limit(1)
        ).first()

    def _serialise(session, item: FoodItem) -> dict:
        latest = _latest_prediction(session, item.id)
        history = session.scalars(
            select(SpoilagePrediction)
            .where(SpoilagePrediction.item_id == item.id)
            .order_by(SpoilagePrediction.predicted_at)
        ).all()
        return {
            "id": item.id,
            "slot_id": item.slot_id,
            "name": item.name,
            "commodity": item.commodity,
            "status": item.status.value,
            "added_at": item.added_at.isoformat(),
            "initial_mass_g": item.initial_mass_g,
            "manual_state": item.manual_state,
            "snoozed_until": item.snoozed_until.isoformat() if item.snoozed_until else None,
            "state": (item.manual_state or (latest.state.value if latest else None)),
            "freshness_score": latest.freshness_score if latest else None,
            "days_remaining": estimate_days_remaining(list(history)),
            "probabilities": None if not latest else {
                "fresh": latest.p_fresh,
                "marginal": latest.p_marginal,
                "spoiled": latest.p_spoiled,
            },
            "history": [
                {"t": p.predicted_at.isoformat(), "score": p.freshness_score,
                 "state": p.state.value}
                for p in history
            ],
        }

    @app.get("/api/items")
    @require_token
    def list_items():
        with session_scope(factory) as session:
            items = session.scalars(
                select(FoodItem).where(FoodItem.status == ItemStatus.ACTIVE)
                .order_by(FoodItem.slot_id)
            ).all()
            return jsonify([_serialise(session, i) for i in items])

    @app.post("/api/items")
    @require_token
    def add_item():
        body = request.get_json(silent=True) or {}
        required = ("slot_id", "name", "commodity", "initial_mass_g")
        missing = [f for f in required if f not in body]
        if missing:
            return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400
        try:
            mass = float(body["initial_mass_g"])
        except (TypeError, ValueError):
            return jsonify({"error": "initial_mass_g must be a number"}), 400
        if mass <= 0:
            return jsonify({"error": "initial_mass_g must be positive"}), 400

        with session_scope(factory) as session:
            occupied = session.scalars(
                select(FoodItem).where(
                    FoodItem.slot_id == int(body["slot_id"]),
                    FoodItem.status == ItemStatus.ACTIVE)
            ).first()
            if occupied:
                return jsonify({
                    "error": f"slot {body['slot_id']} already holds "
                             f"'{occupied.name}'; consume it first"
                }), 409

            item = FoodItem(
                slot_id=int(body["slot_id"]), name=str(body["name"])[:120],
                commodity=str(body["commodity"]).lower(), initial_mass_g=mass,
            )
            session.add(item)
            session.flush()
            return jsonify(_serialise(session, item)), 201

    @app.get("/api/items/<int:item_id>")
    @require_token
    def get_item(item_id: int):
        with session_scope(factory) as session:
            item = session.get(FoodItem, item_id)
            if item is None:
                return jsonify({"error": "not found"}), 404
            payload = _serialise(session, item)
            payload["readings"] = [
                {"t": r.recorded_at.isoformat(), "temperature_c": r.temperature_c,
                 "humidity_pct": r.humidity_pct, "ethanol_ppm": r.ethanol_ppm,
                 "ammonia_ppm": r.ammonia_ppm, "mass_g": r.mass_g}
                for r in session.scalars(
                    select(SensorReading).where(SensorReading.slot_id == item.slot_id)
                    .order_by(SensorReading.recorded_at)).all()
            ]
            return jsonify(payload)

    @app.post("/api/items/<int:item_id>/consume")
    @require_token
    def consume(item_id: int):
        body = request.get_json(silent=True) or {}
        outcome_raw = str(body.get("outcome", "eaten")).lower()
        if outcome_raw not in ("eaten", "binned"):
            return jsonify({"error": "outcome must be 'eaten' or 'binned'"}), 400

        with session_scope(factory) as session:
            item = session.get(FoodItem, item_id)
            if item is None:
                return jsonify({"error": "not found"}), 404
            if item.status != ItemStatus.ACTIVE:
                return jsonify({"error": "item is not active"}), 409

            outcome = Outcome(outcome_raw)
            item.status = (ItemStatus.CONSUMED if outcome is Outcome.EATEN
                           else ItemStatus.DISCARDED)

            # Lead time is measured from the first spoilage prediction, which is
            # the number the evaluation reports.
            first_alert = session.scalars(
                select(SpoilagePrediction)
                .where(SpoilagePrediction.item_id == item_id,
                       SpoilagePrediction.state == SpoilageState.SPOILED)
                .order_by(SpoilagePrediction.predicted_at).limit(1)
            ).first()
            now = datetime.now(timezone.utc)
            lead = None
            if first_alert is not None:
                stamp = first_alert.predicted_at
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                lead = round((now - stamp).total_seconds() / 3600.0, 2)

            session.add(ConsumptionEvent(
                item_id=item_id, outcome=outcome, recorded_at=now,
                wasted_mass_g=body.get("wasted_mass_g"),
                alert_lead_time_hours=lead, notes=body.get("notes"),
            ))
            return jsonify({"ok": True, "outcome": outcome.value,
                            "alert_lead_time_hours": lead})

    @app.post("/api/items/<int:item_id>/snooze")
    @require_token
    def snooze(item_id: int):
        with session_scope(factory) as session:
            item = session.get(FoodItem, item_id)
            if item is None:
                return jsonify({"error": "not found"}), 404
            item.snoozed_until = snooze_until()
            return jsonify({"ok": True, "snoozed_until": item.snoozed_until.isoformat(),
                            "hours": SNOOZE_HOURS})

    @app.post("/api/items/<int:item_id>/override")
    @require_token
    def override(item_id: int):
        body = request.get_json(silent=True) or {}
        state = body.get("state")
        valid = [s.value for s in SpoilageState]
        if state is not None and state not in valid:
            return jsonify({"error": f"state must be null or one of {valid}"}), 400
        with session_scope(factory) as session:
            item = session.get(FoodItem, item_id)
            if item is None:
                return jsonify({"error": "not found"}), 404
            item.manual_state = state
            return jsonify({"ok": True, "manual_state": state})

    @app.get("/api/readings/<int:slot_id>")
    @require_token
    def readings(slot_id: int):
        limit = min(int(request.args.get("limit", 100)), 1000)
        with session_scope(factory) as session:
            rows = session.scalars(
                select(SensorReading).where(SensorReading.slot_id == slot_id)
                .order_by(desc(SensorReading.recorded_at)).limit(limit)
            ).all()
            return jsonify([
                {"t": r.recorded_at.isoformat(), "temperature_c": r.temperature_c,
                 "humidity_pct": r.humidity_pct, "ethanol_ppm": r.ethanol_ppm,
                 "ammonia_ppm": r.ammonia_ppm, "mass_g": r.mass_g,
                 "mass_delta_g": r.mass_delta_g}
                for r in reversed(rows)
            ])

    @app.get("/api/alerts")
    @require_token
    def alerts():
        out = []
        with session_scope(factory) as session:
            items = session.scalars(
                select(FoodItem).where(FoodItem.status == ItemStatus.ACTIVE)).all()
            for item in items:
                history = session.scalars(
                    select(SpoilagePrediction)
                    .where(SpoilagePrediction.item_id == item.id)
                    .order_by(desc(SpoilagePrediction.predicted_at)).limit(2)
                ).all()
                if not history:
                    continue
                alert = evaluate_item(item, history[0],
                                      history[1] if len(history) > 1 else None)
                if alert:
                    out.append({
                        "item_id": alert.item_id, "item_name": alert.item_name,
                        "type": alert.alert_type.value, "message": alert.message,
                        "freshness_score": alert.freshness_score,
                        "raised_at": alert.raised_at.isoformat(),
                    })
        return jsonify(out)

    @app.get("/api/stats")
    @require_token
    def stats():
        with session_scope(factory) as session:
            events = session.scalars(select(ConsumptionEvent)).all()
            eaten = [e for e in events if e.outcome is Outcome.EATEN]
            binned = [e for e in events if e.outcome is Outcome.BINNED]
            leads = [e.alert_lead_time_hours for e in events
                     if e.alert_lead_time_hours is not None]
            wasted = [e.wasted_mass_g for e in binned if e.wasted_mass_g]
            return jsonify({
                "items_tracked": session.query(FoodItem).count(),
                "active": session.query(FoodItem).filter(
                    FoodItem.status == ItemStatus.ACTIVE).count(),
                "eaten": len(eaten),
                "binned": len(binned),
                "waste_rate": round(len(binned) / len(events), 3) if events else None,
                "wasted_mass_g": round(sum(wasted), 1) if wasted else 0.0,
                "mean_alert_lead_time_hours": (
                    round(sum(leads) / len(leads), 2) if leads else None),
            })

    @app.get("/api/settings")
    @require_token
    def get_settings():
        service = app.config["INFERENCE"]
        enabled = (service.backend.camera_enabled if service is not None
                   else app.config.get("CAMERA_ENABLED", True))
        return jsonify({"camera_enabled": bool(enabled)})

    @app.post("/api/settings")
    @require_token
    def set_settings():
        """The privacy switch. Turning the camera off is honoured by the
        backend itself, so no code path above it can photograph the shelf."""
        body = request.get_json(silent=True) or {}
        if "camera_enabled" not in body or not isinstance(body["camera_enabled"], bool):
            return jsonify({"error": "camera_enabled must be true or false"}), 400
        enabled = body["camera_enabled"]
        app.config["CAMERA_ENABLED"] = enabled
        service = app.config["INFERENCE"]
        if service is not None:
            service.backend.camera_enabled = enabled
        return jsonify({"camera_enabled": enabled})

    @app.post("/api/cycle")
    @require_token
    def cycle():
        service = app.config["INFERENCE"]
        if service is None:
            return jsonify({"error": "no inference service configured"}), 503
        return jsonify(service.run_cycle())

    return app
