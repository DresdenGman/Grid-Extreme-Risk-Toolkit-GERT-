"""
SQLAlchemy ORM models for GERT database.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func

from db.connection import Base


class PredictionRecord(Base):
    """
    Stores prediction history for analysis and backtesting.
    """

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Request context
    region = Column(String(50), index=True, nullable=False)
    timestamp = Column(DateTime, default=func.now(), index=True, nullable=False)
    request_date = Column(DateTime, nullable=False)
    
    # Weather features
    temperature = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    solar_irradiance = Column(Float, nullable=False)
    
    # Prediction results
    q50_load_mw = Column(Float, nullable=False)
    q90_load_mw = Column(Float, nullable=False)
    q95_load_mw = Column(Float, nullable=False)
    q99_load_mw = Column(Float, nullable=False)
    
    # Risk assessment
    risk_level = Column(String(20), index=True, nullable=False)  # LOW, MODERATE, HIGH, EXTREME
    risk_score = Column(Float, nullable=False)
    
    # Capacity and margin
    capacity_mw = Column(Float, nullable=False)
    margin_mw = Column(Float, nullable=False)  # capacity - q99
    
    # Financial impact
    eue_mwh = Column(Float, nullable=True)
    estimated_loss = Column(Float, nullable=True)
    
    # Metadata
    model_version = Column(String(50), nullable=False)
    backend_type = Column(String(50), nullable=False)
    data_source = Column(String(20), nullable=True)  # 'real_time' or 'simulated'
    real_load_mw = Column(Float, nullable=True)  # If real data was available
    
    # Additional diagnostics (JSON)
    diagnostics = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)


class AlertRecord(Base):
    """
    Stores alert history for audit and analysis.
    """

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    
    # Alert context
    region = Column(String(50), index=True, nullable=False)
    timestamp = Column(DateTime, default=func.now(), index=True, nullable=False)
    
    # Risk information
    risk_level = Column(String(20), index=True, nullable=False)
    risk_score = Column(Float, nullable=False)
    
    # Load and capacity
    p99_load_mw = Column(Float, nullable=False)
    capacity_mw = Column(Float, nullable=False)
    margin_mw = Column(Float, nullable=False)
    
    # Notification channels attempted
    channels_attempted = Column(JSON, nullable=False)  # List of channel names
    channels_successful = Column(JSON, nullable=False)  # List of successful channels
    
    # Alert reason
    reason = Column(String(200), nullable=True)  # Why alert was triggered
    
    created_at = Column(DateTime, default=func.now(), nullable=False)


class GridLoadRecord(Base):
    """
    Stores historical grid load data from ISO APIs.
    """

    __tablename__ = "grid_loads"

    id = Column(Integer, primary_key=True, index=True)
    
    # Load data
    region = Column(String(50), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    current_load_mw = Column(Float, nullable=False)
    capacity_mw = Column(Float, nullable=False)
    utilization_percent = Column(Float, nullable=False)
    
    # Forecast (if available)
    forecast_load_mw = Column(Float, nullable=True)
    
    # Data source
    data_source = Column(String(50), nullable=False)  # 'ercot', 'caiso', etc.
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
