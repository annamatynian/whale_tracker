"""
Database models and schemas for Whale Tracker

This package contains:
- SQLAlchemy ORM models (database.py)
- Pydantic validation schemas (schemas.py)
- Database connection setup (db_connection.py)
"""

from models.database import (
    Base,
    OneHopDetection,
    Transaction,
    IntermediateAddress,
    WhaleAlert,
    SignalMetrics
)

from models.schemas import (
    TransactionCreate,
    TransactionResponse,
    OneHopDetectionCreate,
    OneHopDetectionResponse,
    IntermediateAddressCreate,
    IntermediateAddressResponse,
    WhaleAlertCreate,
    WhaleAlertResponse,
    SignalMetricsResponse
)

__all__ = [
    # SQLAlchemy Models
    'Base',
    'OneHopDetection',
    'Transaction',
    'IntermediateAddress',
    'WhaleAlert',
    'SignalMetrics',

    # Pydantic Schemas
    'TransactionCreate',
    'TransactionResponse',
    'OneHopDetectionCreate',
    'OneHopDetectionResponse',
    'IntermediateAddressCreate',
    'IntermediateAddressResponse',
    'WhaleAlertCreate',
    'WhaleAlertResponse',
    'SignalMetricsResponse'
]
