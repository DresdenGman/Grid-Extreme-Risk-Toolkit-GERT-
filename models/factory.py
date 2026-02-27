from __future__ import annotations

import os
import logging

from models.interfaces import ModelInterface
from models.real_adapter import RealModelAdapter
from models.stub import QuantileModelStub

logger = logging.getLogger("gert_backend")


def get_model_service() -> ModelInterface:
    backend = os.getenv("MODEL_BACKEND", "stub").lower()
    if backend == "real":
        return RealModelAdapter()
    if backend == "stub":
        return QuantileModelStub()

    logger.warning(f"Unknown backend '{backend}', falling back to stub.")
    return QuantileModelStub()

