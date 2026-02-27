"""
Repository pattern for database operations.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.models import PredictionRecord, AlertRecord, GridLoadRecord
from api.schemas import PredictionOut


class PredictionRepository:
    """Repository for prediction records."""

    @staticmethod
    def create(db: Session, prediction: PredictionOut, region: str, request_date: datetime) -> PredictionRecord:
        """Save a prediction to database."""
        record = PredictionRecord(
            region=region,
            timestamp=prediction.timestamp,
            request_date=request_date,
            temperature=prediction.diagnostics.get("temperature", 0),
            wind_speed=prediction.diagnostics.get("wind_speed", 0),
            solar_irradiance=prediction.diagnostics.get("solar_irradiance", 0),
            q50_load_mw=prediction.q50_load_mw,
            q90_load_mw=prediction.q90_load_mw,
            q95_load_mw=prediction.q95_load_mw,
            q99_load_mw=prediction.q99_load_mw,
            risk_level=prediction.risk_level.value,
            risk_score=prediction.risk_score,
            capacity_mw=prediction.diagnostics.get("capacity_used", 60000),
            margin_mw=prediction.diagnostics.get("capacity_used", 60000) - prediction.q99_load_mw,
            eue_mwh=prediction.financial.eue_mwh if prediction.financial else None,
            estimated_loss=prediction.financial.estimated_loss if prediction.financial else None,
            model_version=prediction.diagnostics.get("model_version", "unknown"),
            backend_type=prediction.diagnostics.get("backend_type", "unknown"),
            data_source=prediction.diagnostics.get("data_source"),
            real_load_mw=prediction.diagnostics.get("real_load_mw"),
            diagnostics=prediction.diagnostics,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_latest(db: Session, region: Optional[str] = None, limit: int = 100) -> List[PredictionRecord]:
        """Get latest predictions, optionally filtered by region."""
        query = db.query(PredictionRecord)
        if region:
            query = query.filter(PredictionRecord.region == region)
        return query.order_by(desc(PredictionRecord.timestamp)).limit(limit).all()

    @staticmethod
    def get_by_date_range(
        db: Session,
        start: datetime,
        end: datetime,
        region: Optional[str] = None,
    ) -> List[PredictionRecord]:
        """Get predictions within a date range."""
        query = db.query(PredictionRecord).filter(
            PredictionRecord.timestamp >= start,
            PredictionRecord.timestamp <= end,
        )
        if region:
            query = query.filter(PredictionRecord.region == region)
        return query.order_by(PredictionRecord.timestamp).all()


class AlertRepository:
    """Repository for alert records."""

    @staticmethod
    def create(
        db: Session,
        region: str,
        risk_level: str,
        risk_score: float,
        p99_load: float,
        capacity: float,
        margin: float,
        channels_attempted: List[str],
        channels_successful: List[str],
        reason: Optional[str] = None,
    ) -> AlertRecord:
        """Save an alert to database."""
        record = AlertRecord(
            region=region,
            timestamp=datetime.now(),
            risk_level=risk_level,
            risk_score=risk_score,
            p99_load_mw=p99_load,
            capacity_mw=capacity,
            margin_mw=margin,
            channels_attempted=channels_attempted,
            channels_successful=channels_successful,
            reason=reason,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_latest(db: Session, region: Optional[str] = None, limit: int = 50) -> List[AlertRecord]:
        """Get latest alerts."""
        query = db.query(AlertRecord)
        if region:
            query = query.filter(AlertRecord.region == region)
        return query.order_by(desc(AlertRecord.timestamp)).limit(limit).all()


class GridLoadRepository:
    """Repository for grid load records."""

    @staticmethod
    def create(
        db: Session,
        region: str,
        timestamp: datetime,
        current_load_mw: float,
        capacity_mw: float,
        data_source: str,
        forecast_load_mw: Optional[float] = None,
    ) -> GridLoadRecord:
        """Save grid load data to database."""
        record = GridLoadRecord(
            region=region,
            timestamp=timestamp,
            current_load_mw=current_load_mw,
            capacity_mw=capacity_mw,
            utilization_percent=(current_load_mw / capacity_mw) * 100,
            forecast_load_mw=forecast_load_mw,
            data_source=data_source,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_latest(db: Session, region: Optional[str] = None, limit: int = 100) -> List[GridLoadRecord]:
        """Get latest grid load records."""
        query = db.query(GridLoadRecord)
        if region:
            query = query.filter(GridLoadRecord.region == region)
        return query.order_by(desc(GridLoadRecord.timestamp)).limit(limit).all()
