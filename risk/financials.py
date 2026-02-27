from __future__ import annotations

from api.schemas import FinancialImpact
from risk.config import VOLL_PRICE


def calculate_financials(p99_load_mw: float, capacity_mw: float) -> FinancialImpact:
    """
    Expected Unserved Energy (EUE) and economic loss using VOLL.
    Kept independent from HTTP so it can be unit tested and reused in scenarios/bulletins.
    """
    shortfall = max(0.0, p99_load_mw - capacity_mw)
    eue = shortfall * 1.0  # 1h window in this MVP
    loss = eue * VOLL_PRICE
    return FinancialImpact(
        eue_mwh=round(eue, 2),
        voll_price=float(VOLL_PRICE),
        estimated_loss=round(loss, 2),
    )

