"""Model definitions: the visual CNN and the sensor-fusion network.

Two models are defined here.

``build_visual_cnn`` is a MobileNetV2 transfer-learning classifier that decides
fresh vs rotten from a photograph. It is trained on real labelled images.

``build_fusion_model`` is the late-fusion network described in the thesis. It
takes the CNN's 1280-dimensional embedding alongside five numeric sensor
features, pushes the sensor features through a small MLP, concatenates the two
embeddings and classifies into three states. Late fusion, joining the
branches after each has formed its own representation, is used rather than
early fusion because the two modalities have wildly different dimensionality
and scale, and concatenating raw pixels with five floats lets the pixels
dominate the gradient.

MobileNetV2 is the backbone because the target device is a Raspberry Pi 4. Its
depthwise separable convolutions cut the parameter count by roughly an order
of magnitude against VGG16 at comparable ImageNet accuracy, which is what
makes on-device inference feasible.
"""

from __future__ import annotations

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

#: Input resolution MobileNetV2 was trained at.
IMAGE_SIZE = (224, 224)
#: Width of the pooled MobileNetV2 feature vector.
CNN_EMBEDDING_DIM = 1280
#: Number of numeric sensor features; must match
#: :data:`freshkeeper.hardware.base.SENSOR_FEATURE_NAMES`.
SENSOR_FEATURE_DIM = 5
#: The three reported states, in the label order used everywhere downstream.
CLASS_NAMES = ["fresh", "marginal", "spoiled"]


def build_backbone(trainable: bool = False) -> keras.Model:
    """MobileNetV2 up to the pooled feature vector, without its classifier."""
    base = keras.applications.MobileNetV2(
        input_shape=(*IMAGE_SIZE, 3),
        include_top=False,
        weights="imagenet",
        pooling="avg",
    )
    base.trainable = trainable
    return base


def build_visual_cnn(dropout: float = 0.3) -> keras.Model:
    """Binary fresh/rotten classifier over images.

    The output is a single sigmoid unit rather than two softmax units. For a
    binary problem the two are equivalent in expressive power, but the sigmoid
    gives a calibrated P(rotten) directly, and the fusion stage uses that
    probability as a scalar measure of how spoiled the item *looks*.
    """
    inputs = keras.Input(shape=(*IMAGE_SIZE, 3), name="image")
    x = keras.applications.mobilenet_v2.preprocess_input(inputs)
    backbone = build_backbone(trainable=False)
    x = backbone(x, training=False)
    x = layers.Dropout(dropout, name="head_dropout")(x)
    outputs = layers.Dense(1, activation="sigmoid", name="p_rotten")(x)

    model = keras.Model(inputs, outputs, name="visual_cnn")
    model.backbone = backbone  # kept as an attribute so fine-tuning can reach it
    return model


def build_visual_head(dropout: float = 0.3) -> keras.Model:
    """Just the classifier head, for training on precomputed embeddings.

    Forward passes through a frozen backbone are the expensive part of stage-one
    transfer learning, and they are identical every epoch. Computing the
    embeddings once and fitting this head over them gives exactly the same
    result as training the full frozen model, in a fraction of the time.
    """
    inputs = keras.Input(shape=(CNN_EMBEDDING_DIM,), name="embedding")
    x = layers.Dropout(dropout, name="head_dropout")(inputs)
    outputs = layers.Dense(1, activation="sigmoid", name="p_rotten")(x)
    return keras.Model(inputs, outputs, name="visual_head")


def build_fusion_model(
    sensor_dim: int = SENSOR_FEATURE_DIM,
    n_classes: int = len(CLASS_NAMES),
    dropout: float = 0.3,
    image_projection: int | None = 64,
) -> keras.Model:
    """Late-fusion classifier over a CNN embedding plus sensor features.

    Args:
        sensor_dim: number of numeric sensor features.
        n_classes: number of output states.
        dropout: dropout rate applied after each dense block.
        image_projection: width to project the 1280-dimensional visual
            embedding down to before joining. ``None`` concatenates it raw.

    On ``image_projection``. Concatenating a 1280-wide visual embedding with a
    32-wide sensor embedding gives the image branch forty times the width, and
    the first fusion layer allocates its capacity accordingly. In this task the
    visual features are the *weaker* signal, appearance lags physiology --
    so the raw concatenation trained to a lower accuracy than the sensor
    branch achieved on its own. Projecting the image embedding down to a
    comparable width lets both modalities actually compete. The thesis reports
    both variants, because the failure is more instructive than the fix.

    The sensor branch stays small deliberately. Five inputs do not need
    capacity, they need regularisation.
    """
    image_input = keras.Input(shape=(CNN_EMBEDDING_DIM,), name="image_embedding")
    sensor_input = keras.Input(shape=(sensor_dim,), name="sensor_features")

    if image_projection:
        v = layers.Dense(image_projection, activation="relu",
                         name="image_projection")(image_input)
        v = layers.Dropout(dropout, name="image_dropout")(v)
    else:
        v = image_input

    # Sensor branch: 5 -> 64 -> 32.
    s = layers.Dense(64, activation="relu", name="sensor_dense_1")(sensor_input)
    s = layers.BatchNormalization(name="sensor_bn")(s)
    s = layers.Dropout(dropout, name="sensor_dropout")(s)
    s = layers.Dense(32, activation="relu", name="sensor_dense_2")(s)

    joined = layers.Concatenate(name="fusion_concat")([v, s])
    x = layers.Dense(256, activation="relu", name="fusion_dense_1")(joined)
    x = layers.Dropout(dropout, name="fusion_dropout_1")(x)
    x = layers.Dense(128, activation="relu", name="fusion_dense_2")(x)
    x = layers.Dropout(dropout, name="fusion_dropout_2")(x)
    outputs = layers.Dense(n_classes, activation="softmax", name="state")(x)

    return keras.Model([image_input, sensor_input], outputs, name="fusion_model")


def build_sensor_only_model(
    sensor_dim: int = SENSOR_FEATURE_DIM,
    n_classes: int = len(CLASS_NAMES),
    dropout: float = 0.3,
) -> keras.Model:
    """Sensor branch on its own, as an ablation baseline.

    Comparing this and the vision-only model against the fusion model is what
    justifies the extra hardware. If fusion does not beat both, the gas sensors
    are not earning their place in the bill of materials.
    """
    sensor_input = keras.Input(shape=(sensor_dim,), name="sensor_features")
    s = layers.Dense(64, activation="relu")(sensor_input)
    s = layers.BatchNormalization()(s)
    s = layers.Dropout(dropout)(s)
    s = layers.Dense(32, activation="relu")(s)
    s = layers.Dense(64, activation="relu")(s)
    s = layers.Dropout(dropout)(s)
    outputs = layers.Dense(n_classes, activation="softmax", name="state")(s)
    return keras.Model(sensor_input, outputs, name="sensor_only_model")


def compile_binary(model: keras.Model, learning_rate: float = 1e-3) -> keras.Model:
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate),
        loss="binary_crossentropy",
        metrics=[
            keras.metrics.BinaryAccuracy(name="accuracy"),
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
            keras.metrics.AUC(name="auc"),
        ],
    )
    return model


def compile_multiclass(model: keras.Model, learning_rate: float = 1e-3) -> keras.Model:
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=[keras.metrics.SparseCategoricalAccuracy(name="accuracy")],
    )
    return model
