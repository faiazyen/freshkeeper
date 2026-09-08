"""Inference service: sensors and camera in, stored predictions out.

This is what runs on the device. One measurement cycle:

    read every slot -> store the raw readings -> embed the image (or fall back
    to the sensor-only model when there is no camera) -> classify -> compute a
    freshness score and days-remaining -> store the prediction

The camera fallback matters. The simulated backend has no camera, and a real
one can fail or be switched off for privacy. Rather than refusing to run, the
service drops to the sensor-only model, which the evaluation shows is the
stronger of the two on this task anyway.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from sqlalchemy import desc, select

from ..alerts import estimate_days_remaining, freshness_score
from ..db.models import (
    FoodItem, ItemStatus, SensorReading, SpoilagePrediction, SpoilageState,
)
from ..db.session import session_scope
from ..hardware.base import SensorBackend
from .model import CLASS_NAMES

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models"


class InferenceService:
    """Runs measurement cycles and records what the model concludes."""

    def __init__(self, backend: SensorBackend, session_factory,
                 model_dir: Path = MODEL_DIR, load_models: bool = True) -> None:
        self.backend = backend
        self.session_factory = session_factory
        self.model_dir = model_dir
        self.fusion = None
        self.sensor_only = None
        self.backbone = None
        self.scaler = None
        if load_models:
            self._load()

    def _load(self) -> None:
        from tensorflow import keras
        scaler_path = self.model_dir / "sensor_scaler.npy"
        if scaler_path.exists():
            self.scaler = np.load(scaler_path)
        for attr, filename in (("fusion", "fusion.keras"),
                               ("sensor_only", "sensor_only.keras")):
            path = self.model_dir / filename
            if path.exists():
                setattr(self, attr, keras.models.load_model(path))

    def _standardise(self, features: list[float]) -> np.ndarray:
        array = np.asarray(features, dtype=np.float32)[None, :]
        if self.scaler is None:
            return array
        mean, std = self.scaler
        return ((array - mean) / std).astype(np.float32)

    def _embed(self, image_path: str | None) -> np.ndarray | None:
        if not image_path or not Path(image_path).exists():
            return None
        import tensorflow as tf
        from tensorflow import keras
        from .model import IMAGE_SIZE, build_backbone
        if self.backbone is None:
            self.backbone = build_backbone(trainable=False)
        raw = tf.io.read_file(image_path)
        image = tf.image.resize(tf.io.decode_jpeg(raw, channels=3), IMAGE_SIZE)
        batch = keras.applications.mobilenet_v2.preprocess_input(
            tf.expand_dims(image, 0))
        return self.backbone(batch, training=False).numpy()

    def predict(self, features: list[float], image_path: str | None
                ) -> tuple[np.ndarray, float, str]:
        """Classify one item. Returns (probabilities, milliseconds, model used)."""
        z = self._standardise(features)
        embedding = self._embed(image_path)
        start = time.perf_counter()

        if embedding is not None and self.fusion is not None:
            probs = self.fusion([embedding, z], training=False).numpy()[0]
            used = "fusion"
        elif self.sensor_only is not None:
            probs = self.sensor_only(z, training=False).numpy()[0]
            used = "sensor_only"
        else:
            # No model available. Return a flat distribution rather than a
            # confident guess; the alert layer's confidence floor then keeps
            # the system quiet, which is the right behaviour when it knows
            # nothing.
            probs = np.full(len(CLASS_NAMES), 1.0 / len(CLASS_NAMES))
            used = "uniform_fallback"

        return probs, (time.perf_counter() - start) * 1000.0, used

    def run_cycle(self) -> dict:
        """One full measurement cycle across every slot."""
        samples = self.backend.read_all()
        results = []

        with session_scope(self.session_factory) as session:
            for sample in samples:
                item = session.scalars(
                    select(FoodItem).where(
                        FoodItem.slot_id == sample.slot_id,
                        FoodItem.status == ItemStatus.ACTIVE)
                ).first()

                # Mass delta is meaningful only against a registered item.
                delta = (round(sample.mass_g - item.initial_mass_g, 1)
                         if item else 0.0)
                session.add(SensorReading(
                    slot_id=sample.slot_id, recorded_at=sample.timestamp,
                    temperature_c=sample.temperature_c,
                    humidity_pct=sample.humidity_pct,
                    ethanol_ppm=sample.ethanol_ppm,
                    ammonia_ppm=sample.ammonia_ppm,
                    mass_g=sample.mass_g, mass_delta_g=delta,
                    image_path=sample.image_path,
                ))
                if item is None:
                    continue

                features = sample.feature_vector()
                features[-1] = delta
                probs, elapsed_ms, used = self.predict(features, sample.image_path)
                score = freshness_score(*probs)

                history = session.scalars(
                    select(SpoilagePrediction)
                    .where(SpoilagePrediction.item_id == item.id)
                    .order_by(desc(SpoilagePrediction.predicted_at)).limit(12)
                ).all()

                prediction = SpoilagePrediction(
                    item_id=item.id, predicted_at=sample.timestamp,
                    state=SpoilageState(CLASS_NAMES[int(probs.argmax())]),
                    p_fresh=float(probs[0]), p_marginal=float(probs[1]),
                    p_spoiled=float(probs[2]), freshness_score=score,
                    days_remaining=estimate_days_remaining(list(history)),
                    inference_ms=elapsed_ms,
                )
                session.add(prediction)
                results.append({
                    "slot_id": sample.slot_id, "item": item.name,
                    "state": prediction.state.value, "freshness_score": score,
                    "model": used, "inference_ms": round(elapsed_ms, 3),
                })

        return {"cycle_completed": True, "slots": len(samples), "items": results}
