from __future__ import annotations

from typing import Protocol, TypeVar

InT = TypeVar("InT")
OutT = TypeVar("OutT")


class FeatureBuilder(Protocol[InT, OutT]):
    def build(self, raw: InT) -> OutT:
        ...

