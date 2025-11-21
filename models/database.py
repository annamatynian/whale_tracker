"""
SQLAlchemy ORM Models for Whale Tracker

Database schema for one-hop detection, transactions, and analytics.
"""

from sqlalchemy import (
    Column, Integer, String, BigInteger, Boolean, DateTime,
    DECIMAL, Text, Index, ForeignKey, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class OneHopDetection(Base):
    """
    One-hop detection results with multi-signal analysis.

    Stores complete detection data including all signal scores
    and composite confidence.
    """
    __tablename__ = 'one_hop_detections'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core identification
    whale_address = Column(String(42), nullable=False, index=True)
    whale_tx_hash = Column(String(66), nullable=False, index=True)
    intermediate_address = Column(String(42), nullable=False, index=True)
    exchange_address = Column(String(42), nullable=True, index=True)
    exchange_tx_hash = Column(String(66), nullable=True)

    # Transaction details
    whale_tx_block = Column(BigInteger, nullable=False)
    exchange_tx_block = Column(BigInteger, nullable=True)
    whale_tx_timestamp = Column(DateTime, nullable=False)
    exchange_tx_timestamp = Column(DateTime, nullable=True)

    # Amount tracking
    whale_amount_wei = Column(String(78), nullable=False)  # Store as string for precision
    exchange_amount_wei = Column(String(78), nullable=True)
    whale_amount_eth = Column(DECIMAL(36, 18), nullable=False)
    exchange_amount_eth = Column(DECIMAL(36, 18), nullable=True)

    # Signal scores (0-100 per signal)
    time_correlation_score = Column(Integer, nullable=True)
    gas_correlation_score = Column(Integer, nullable=True)
    nonce_correlation_score = Column(Integer, nullable=True)
    amount_correlation_score = Column(Integer, nullable=True)
    address_profile_score = Column(Integer, nullable=True)

    # Composite confidence
    total_confidence = Column(Integer, nullable=False)  # Average of all signals
    num_signals_used = Column(Integer, nullable=False, default=1)
    detection_method = Column(String(50), nullable=False, default='advanced')  # 'simple', 'advanced'

    # Status tracking
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'confirmed', 'false_positive'
    alert_sent = Column(Boolean, nullable=False, default=False)
    alert_sent_at = Column(DateTime, nullable=True)

    # Metadata
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    # Signal details (JSON for flexibility)
    signal_details = Column(JSON, nullable=True)

    # Relationships
    intermediate_profile = relationship(
        'IntermediateAddress',
        foreign_keys='OneHopDetection.intermediate_address',
        primaryjoin='OneHopDetection.intermediate_address == IntermediateAddress.address',
        back_populates='detections',
        uselist=False
    )

    alerts = relationship('WhaleAlert', back_populates='detection', cascade='all, delete-orphan')

    # Indexes for performance
    __table_args__ = (
        Index('idx_whale_intermediate', 'whale_address', 'intermediate_address'),
        Index('idx_confidence', 'total_confidence'),
        Index('idx_timestamp', 'whale_tx_timestamp'),
        Index('idx_detection_method', 'detection_method'),
        Index('idx_status', 'status'),
    )

    def __repr__(self):
        return (
            f"<OneHopDetection(id={self.id}, "
            f"whale={self.whale_address[:8]}..., "
            f"intermediate={self.intermediate_address[:8]}..., "
            f"confidence={self.total_confidence}%)>"
        )


class Transaction(Base):
    """
    Ethereum transaction data.

    Stores transaction details for analysis and correlation.
    """
    __tablename__ = 'transactions'

    # Primary key
    tx_hash = Column(String(66), primary_key=True)

    # Block information
    block_number = Column(BigInteger, nullable=False, index=True)
    block_timestamp = Column(DateTime, nullable=False, index=True)
    transaction_index = Column(Integer, nullable=True)

    # Transaction parties
    from_address = Column(String(42), nullable=False, index=True)
    to_address = Column(String(42), nullable=True, index=True)

    # Transaction details
    value = Column(DECIMAL(36, 18), nullable=False)
    value_wei = Column(String(78), nullable=False)

    # Gas information
    gas_price = Column(BigInteger, nullable=True)
    gas_used = Column(BigInteger, nullable=True)
    gas_limit = Column(BigInteger, nullable=True)

    # EIP-1559 fields
    max_fee_per_gas = Column(BigInteger, nullable=True)
    max_priority_fee_per_gas = Column(BigInteger, nullable=True)

    # Nonce
    nonce = Column(BigInteger, nullable=False, index=True)

    # Input data
    input_data = Column(Text, nullable=True)
    method_id = Column(String(10), nullable=True)

    # Status
    status = Column(Boolean, nullable=False, default=True)  # True = success, False = failed

    # Metadata
    tx_type = Column(Integer, nullable=True)  # 0=legacy, 1=access_list, 2=eip1559
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_from_block', 'from_address', 'block_number'),
        Index('idx_to_block', 'to_address', 'block_number'),
        Index('idx_from_nonce', 'from_address', 'nonce'),
    )

    def __repr__(self):
        return (
            f"<Transaction(hash={self.tx_hash[:10]}..., "
            f"from={self.from_address[:8]}..., "
            f"value={self.value} ETH)>"
        )


class IntermediateAddress(Base):
    """
    Intermediate address profiles.

    Tracks characteristics of addresses used in one-hop transfers.
    """
    __tablename__ = 'intermediate_addresses'

    # Primary key
    address = Column(String(42), primary_key=True)

    # Profile classification
    profile_type = Column(String(30), nullable=False)  # 'fresh_burner', 'burner', 'professional', 'normal'
    overall_confidence = Column(Integer, nullable=False)

    # Fresh address signals
    is_fresh = Column(Boolean, nullable=False, default=False)
    fresh_confidence = Column(Integer, nullable=False, default=0)
    age_hours = Column(DECIMAL(10, 2), nullable=True)
    first_seen_at = Column(DateTime, nullable=True)

    # Empty address signals
    was_empty = Column(Boolean, nullable=False, default=False)
    empty_confidence = Column(Integer, nullable=False, default=0)

    # Single-use burner signals
    is_single_use = Column(Boolean, nullable=False, default=False)
    single_use_confidence = Column(Integer, nullable=False, default=0)
    transaction_count = Column(Integer, nullable=True)

    # Reused intermediate signals
    is_reused = Column(Boolean, nullable=False, default=False)
    reuse_confidence = Column(Integer, nullable=False, default=0)
    reuse_cycle_count = Column(Integer, nullable=True)

    # Current state
    current_balance_wei = Column(String(78), nullable=True)
    current_balance_eth = Column(DECIMAL(36, 18), nullable=True)
    current_nonce = Column(BigInteger, nullable=True)

    # Usage statistics
    times_used = Column(Integer, nullable=False, default=1)
    first_detection_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_detection_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    # Profile details (JSON)
    profile_details = Column(JSON, nullable=True)

    # Relationships
    detections = relationship(
        'OneHopDetection',
        foreign_keys='OneHopDetection.intermediate_address',
        primaryjoin='IntermediateAddress.address == OneHopDetection.intermediate_address',
        back_populates='intermediate_profile'
    )

    # Indexes
    __table_args__ = (
        Index('idx_profile_type', 'profile_type'),
        Index('idx_times_used', 'times_used'),
        Index('idx_last_detection', 'last_detection_at'),
    )

    def __repr__(self):
        return (
            f"<IntermediateAddress(address={self.address[:8]}..., "
            f"type={self.profile_type}, "
            f"used={self.times_used}x)>"
        )


class WhaleAlert(Base):
    """
    Whale alerts sent to users.

    Tracks all alerts generated and their delivery status.
    """
    __tablename__ = 'whale_alerts'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to detection
    detection_id = Column(Integer, ForeignKey('one_hop_detections.id', ondelete='CASCADE'), nullable=False, index=True)

    # Alert details
    alert_type = Column(String(30), nullable=False)  # 'one_hop', 'large_transfer', 'accumulation'
    severity = Column(String(20), nullable=False, default='medium')  # 'low', 'medium', 'high', 'critical'
    confidence = Column(Integer, nullable=False)

    # Alert message
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    alert_data = Column(JSON, nullable=True)

    # Delivery status
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    delivery_method = Column(String(30), nullable=False)  # 'telegram', 'email', 'webhook', 'discord'
    delivery_status = Column(String(20), nullable=False, default='sent')  # 'sent', 'delivered', 'failed', 'read'
    delivery_error = Column(Text, nullable=True)

    # User/recipient info
    recipient_id = Column(String(100), nullable=True)  # User ID or channel ID

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    detection = relationship('OneHopDetection', back_populates='alerts')

    # Indexes
    __table_args__ = (
        Index('idx_alert_type', 'alert_type'),
        Index('idx_sent_at', 'sent_at'),
        Index('idx_delivery_status', 'delivery_status'),
    )

    def __repr__(self):
        return (
            f"<WhaleAlert(id={self.id}, "
            f"type={self.alert_type}, "
            f"confidence={self.confidence}%)>"
        )


class SignalMetrics(Base):
    """
    Signal performance metrics.

    Tracks accuracy and performance of each detection signal.
    """
    __tablename__ = 'signal_metrics'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Signal identification
    signal_name = Column(String(50), nullable=False, index=True)  # 'time', 'gas', 'nonce', 'amount', 'address'
    date = Column(DateTime, nullable=False, index=True)

    # Performance metrics
    total_checks = Column(Integer, nullable=False, default=0)
    positive_signals = Column(Integer, nullable=False, default=0)
    true_positives = Column(Integer, nullable=False, default=0)
    false_positives = Column(Integer, nullable=False, default=0)

    # Calculated metrics
    precision = Column(DECIMAL(5, 4), nullable=True)  # TP / (TP + FP)
    signal_rate = Column(DECIMAL(5, 4), nullable=True)  # Positive / Total

    # Average scores
    avg_confidence_when_positive = Column(DECIMAL(5, 2), nullable=True)
    avg_confidence_overall = Column(DECIMAL(5, 2), nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_signal_date', 'signal_name', 'date'),
    )

    def __repr__(self):
        return (
            f"<SignalMetrics(signal={self.signal_name}, "
            f"date={self.date.date()}, "
            f"precision={self.precision})>"
        )
