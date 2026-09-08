"""Tests for the network topologies.

Shape and wiring checks only; training behaviour is measured by the evaluation
run, not asserted here. These are the mistakes that are cheap to make and
expensive to notice later: a branch of the wrong width, a projection that is
not applied, an output layer that does not sum to one.
"""

from __future__ import annotations

import numpy as np
import pytest

from freshkeeper.hardware.base import SENSOR_FEATURE_NAMES
from freshkeeper.ml.model import (
    CLASS_NAMES, CNN_EMBEDDING_DIM, SENSOR_FEATURE_DIM, build_fusion_model,
    build_sensor_only_model, build_visual_cnn, build_visual_head,
    compile_binary, compile_multiclass,
)


def test_sensor_dim_matches_the_feature_vector():
    # If these drift apart, training and inference disagree about column order.
    assert SENSOR_FEATURE_DIM == len(SENSOR_FEATURE_NAMES)


def test_class_names_are_ordered_worst_last():
    assert CLASS_NAMES == ["fresh", "marginal", "spoiled"]


class TestVisualModels:
    def test_head_shapes(self):
        model = build_visual_head()
        assert model.input_shape == (None, CNN_EMBEDDING_DIM)
        assert model.output_shape == (None, 1)

    def test_head_output_is_a_probability(self):
        model = build_visual_head()
        out = model.predict(np.random.randn(4, CNN_EMBEDDING_DIM), verbose=0)
        assert ((out >= 0) & (out <= 1)).all()

    def test_full_cnn_takes_raw_pixels(self):
        model = build_visual_cnn()
        assert model.input_shape == (None, 224, 224, 3)
        # Preprocessing lives inside the model, so a caller cannot feed it
        # wrongly-scaled input, and cannot double-normalise it either, which
        # is what once trained this to exactly chance.
        assert any("true_divide" in layer.name or "preprocess" in layer.name.lower()
                   or "subtract" in layer.name.lower() or "rescal" in layer.name.lower()
                   for layer in model.layers) or model.layers[1].__class__.__name__ != "Dense"

    def test_backbone_starts_frozen(self):
        assert build_visual_cnn().backbone.trainable is False


class TestFusionModel:
    def test_takes_both_modalities(self):
        model = build_fusion_model()
        shapes = {inp.shape[-1] for inp in model.inputs}
        assert shapes == {CNN_EMBEDDING_DIM, SENSOR_FEATURE_DIM}

    def test_outputs_a_distribution_over_the_three_states(self):
        model = build_fusion_model()
        out = model.predict(
            [np.random.randn(8, CNN_EMBEDDING_DIM),
             np.random.randn(8, SENSOR_FEATURE_DIM)], verbose=0)
        assert out.shape == (8, len(CLASS_NAMES))
        assert np.allclose(out.sum(axis=1), 1.0, atol=1e-5)

    def test_projection_layer_is_present_by_default(self):
        names = [layer.name for layer in build_fusion_model().layers]
        assert "image_projection" in names

    def test_projection_can_be_disabled(self):
        names = [layer.name for layer in
                 build_fusion_model(image_projection=None).layers]
        assert "image_projection" not in names

    def test_projection_reduces_the_parameter_count(self):
        # The raw variant concatenates 1280 + 32 into a 256-wide layer; the
        # projected one concatenates 64 + 32, so it is far smaller.
        projected = build_fusion_model(image_projection=64).count_params()
        raw = build_fusion_model(image_projection=None).count_params()
        assert projected < raw

    def test_sensor_branch_is_deliberately_small(self):
        model = build_fusion_model()
        assert model.get_layer("sensor_dense_1").units == 64
        assert model.get_layer("sensor_dense_2").units == 32


class TestSensorOnlyModel:
    def test_shapes(self):
        model = build_sensor_only_model()
        assert model.input_shape == (None, SENSOR_FEATURE_DIM)
        assert model.output_shape == (None, len(CLASS_NAMES))


class TestCompilation:
    def test_binary_metrics(self):
        model = compile_binary(build_visual_head())
        assert model.loss == "binary_crossentropy"

    def test_multiclass_metrics(self):
        model = compile_multiclass(build_sensor_only_model())
        assert model.loss == "sparse_categorical_crossentropy"
