from __future__ import annotations

import os
import logging

from models.interfaces import ModelInterface
from models.real_adapter import RealModelAdapter
from models.stub import QuantileModelStub

logger = logging.getLogger("gert_backend")


def get_model_service() -> ModelInterface:
    """Return a ModelInterface implementation based on MODEL_BACKEND env var.

    Accepted values:
        unset / "stub" — QuantileModelStub (demonstration backend)
        "real"         — RealModelAdapter (loads artifact from MODEL_ARTIFACT_DIR)

    Any other value raises a configuration error.
    """
    backend = os.getenv("MODEL_BACKEND", "stub").lower()

    if backend == "stub":
        return QuantileModelStub()

    if backend == "real":
        return RealModelAdapter()

    raise RuntimeError(
        f"Unsupported MODEL_BACKEND value: '{backend}'. "
        "Accepted values: stub, real."
    )
