"""
Pydantic Validation Schemas for Whale Tracker

Separate validation layer from database models.
Provides input validation and API serialization.
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


# ==================== Transaction Schemas ====================

class TransactionBase(BaseModel):
    """Base transaction schema with common fields"""
    tx_hash: str = Field(..., min_length=66, max_length=66, description="Transaction hash")
    block_number: int = Field(..., ge=0, description="Block number")
    from_address: str = Field(..., min_length=42, max_length=42, description="Sender address")
    to_address: Optional[str] = Field(None, min_length=42, max_length=42, description="Recipient address")
    value_wei: str = Field(..., description="Transaction value in Wei (as string)")
    value_eth: Decimal = Field(..., description="Transaction value in ETH")
    nonce: int = Field(..., ge=0, description="Transaction nonce")

    @validator('tx_hash')
    def validate_tx_hash(cls, v):
        """Validate transaction hash format"""
        if not v.startswith('0x'):
            raise ValueError('Transaction hash must start with 0x')
        return v.lower()

    @validator('from_address', 'to_address')
    def validate_address(cls, v):
        """Validate Ethereum address format"""
        if v is None:
            return v
        if not v.startswith('0x'):
            raise ValueError('Address must start with 0x')
        return v.lower()


class TransactionCreate(TransactionBase):
    """Schema for creating new transaction"""
    block_timestamp: datetime = Field(..., description="Block timestamp")
    transaction_index: Optional[int] = Field(None, ge=0)

    # Gas information
    gas_price: Optional[int] = Field(None, ge=0)
    gas_used: Optional[int] = Field(None, ge=0)
    gas_limit: Optional[int] = Field(None, ge=0)

    # EIP-1559 fields
    max_fee_per_gas: Optional[int] = Field(None, ge=0)
    max_priority_fee_per_gas: Optional[int] = Field(None, ge=0)

    # Transaction details
    input_data: Optional[str] = None
    method_id: Optional[str] = Field(None, max_length=10)
    status: bool = Field(True, description="Transaction status (success/failed)")
    tx_type: Optional[int] = Field(None, ge=0, le=2, description="Transaction type (0/1/2)")


class TransactionResponse(TransactionBase):
    """Schema for transaction API responses"""
    block_timestamp: datetime
    transaction_index: Optional[int]
    gas_price: Optional[int]
    gas_used: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== One-Hop Detection Schemas ====================

class OneHopDetectionBase(BaseModel):
    """Base one-hop detection schema"""
    whale_address: str = Field(..., min_length=42, max_length=42)
    whale_tx_hash: str = Field(..., min_length=66, max_length=66)
    intermediate_address: str = Field(..., min_length=42, max_length=42)
    exchange_address: Optional[str] = Field(None, min_length=42, max_length=42)

    @validator('whale_address', 'intermediate_address', 'exchange_address')
    def validate_addresses(cls, v):
        """Validate address format"""
        if v is None:
            return v
        if not v.startswith('0x'):
            raise ValueError('Address must start with 0x')
        return v.lower()


class OneHopDetectionCreate(OneHopDetectionBase):
    """Schema for creating one-hop detection"""
    exchange_tx_hash: Optional[str] = Field(None, min_length=66, max_length=66)

    # Transaction details
    whale_tx_block: int = Field(..., ge=0)
    exchange_tx_block: Optional[int] = Field(None, ge=0)
    whale_tx_timestamp: datetime
    exchange_tx_timestamp: Optional[datetime] = None

    # Amounts
    whale_amount_wei: str
    exchange_amount_wei: Optional[str] = None
    whale_amount_eth: Decimal
    exchange_amount_eth: Optional[Decimal] = None

    # Signal scores (0-100)
    time_correlation_score: Optional[int] = Field(None, ge=0, le=100)
    gas_correlation_score: Optional[int] = Field(None, ge=0, le=100)
    nonce_correlation_score: Optional[int] = Field(None, ge=0, le=100)
    amount_correlation_score: Optional[int] = Field(None, ge=0, le=100)
    address_profile_score: Optional[int] = Field(None, ge=0, le=100)

    # Composite confidence
    total_confidence: int = Field(..., ge=0, le=100, description="Average confidence score")
    num_signals_used: int = Field(..., ge=1, description="Number of signals analyzed")
    detection_method: str = Field('advanced', description="Detection method used")

    # Optional details
    signal_details: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

    @validator('detection_method')
    def validate_detection_method(cls, v):
        """Validate detection method"""
        allowed = ['simple', 'advanced', 'manual']
        if v not in allowed:
            raise ValueError(f'Detection method must be one of: {allowed}')
        return v


class OneHopDetectionResponse(OneHopDetectionBase):
    """Schema for one-hop detection API responses"""
    id: int
    exchange_tx_hash: Optional[str]

    # Transaction details
    whale_tx_block: int
    exchange_tx_block: Optional[int]
    whale_tx_timestamp: datetime
    exchange_tx_timestamp: Optional[datetime]

    # Amounts
    whale_amount_eth: Decimal
    exchange_amount_eth: Optional[Decimal]

    # Scores
    time_correlation_score: Optional[int]
    gas_correlation_score: Optional[int]
    nonce_correlation_score: Optional[int]
    amount_correlation_score: Optional[int]
    address_profile_score: Optional[int]

    # Confidence
    total_confidence: int
    num_signals_used: int
    detection_method: str

    # Status
    status: str
    notes: Optional[str] = None
    alert_sent: bool
    alert_sent_at: Optional[datetime]

    # Metadata
    detected_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OneHopDetectionUpdate(BaseModel):
    """Schema for updating one-hop detection"""
    status: Optional[str] = Field(None, description="Detection status")
    notes: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        """Validate status"""
        if v is not None:
            allowed = ['pending', 'confirmed', 'false_positive']
            if v not in allowed:
                raise ValueError(f'Status must be one of: {allowed}')
        return v


# ==================== Intermediate Address Schemas ====================

class IntermediateAddressBase(BaseModel):
    """Base intermediate address schema"""
    address: str = Field(..., min_length=42, max_length=42)

    @validator('address')
    def validate_address(cls, v):
        """Validate address format"""
        if not v.startswith('0x'):
            raise ValueError('Address must start with 0x')
        return v.lower()


class IntermediateAddressCreate(IntermediateAddressBase):
    """Schema for creating intermediate address profile"""
    profile_type: str = Field(..., description="Profile classification")
    overall_confidence: int = Field(..., ge=0, le=100)

    # Fresh address signals
    is_fresh: bool = False
    fresh_confidence: int = Field(0, ge=0, le=100)
    age_hours: Optional[Decimal] = Field(None, ge=0)
    first_seen_at: Optional[datetime] = None

    # Empty address signals
    was_empty: bool = False
    empty_confidence: int = Field(0, ge=0, le=100)

    # Single-use burner signals
    is_single_use: bool = False
    single_use_confidence: int = Field(0, ge=0, le=100)
    transaction_count: Optional[int] = Field(None, ge=0)

    # Reused intermediate signals
    is_reused: bool = False
    reuse_confidence: int = Field(0, ge=0, le=100)
    reuse_cycle_count: Optional[int] = Field(None, ge=0)

    # Current state
    current_balance_wei: Optional[str] = None
    current_balance_eth: Optional[Decimal] = None
    current_nonce: Optional[int] = Field(None, ge=0)

    # Profile details
    profile_details: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

    @validator('profile_type')
    def validate_profile_type(cls, v):
        """Validate profile type"""
        allowed = ['fresh_burner', 'burner', 'professional', 'fresh', 'empty', 'normal', 'unknown', 'error']
        if v not in allowed:
            raise ValueError(f'Profile type must be one of: {allowed}')
        return v


class IntermediateAddressResponse(IntermediateAddressBase):
    """Schema for intermediate address API responses"""
    profile_type: str
    overall_confidence: int

    # Signals
    is_fresh: bool
    fresh_confidence: int
    is_single_use: bool
    single_use_confidence: int
    is_reused: bool
    reuse_confidence: int

    # Statistics
    times_used: int
    first_detection_at: datetime
    last_detection_at: datetime

    # Metadata
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Whale Alert Schemas ====================

class WhaleAlertBase(BaseModel):
    """Base whale alert schema"""
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field('medium', description="Alert severity")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score")

    @validator('alert_type')
    def validate_alert_type(cls, v):
        """Validate alert type"""
        allowed = ['one_hop', 'large_transfer', 'accumulation', 'unusual_activity']
        if v not in allowed:
            raise ValueError(f'Alert type must be one of: {allowed}')
        return v

    @validator('severity')
    def validate_severity(cls, v):
        """Validate severity"""
        allowed = ['low', 'medium', 'high', 'critical']
        if v not in allowed:
            raise ValueError(f'Severity must be one of: {allowed}')
        return v


class WhaleAlertCreate(WhaleAlertBase):
    """Schema for creating whale alert"""
    detection_id: int = Field(..., ge=1, description="Associated detection ID")

    # Alert content
    title: str = Field(..., max_length=200)
    message: str = Field(..., description="Alert message")
    alert_data: Optional[Dict[str, Any]] = None

    # Delivery
    delivery_method: str = Field(..., description="Delivery method")
    recipient_id: Optional[str] = Field(None, max_length=100)

    @validator('delivery_method')
    def validate_delivery_method(cls, v):
        """Validate delivery method"""
        allowed = ['telegram', 'email', 'webhook', 'discord', 'slack']
        if v not in allowed:
            raise ValueError(f'Delivery method must be one of: {allowed}')
        return v


class WhaleAlertResponse(WhaleAlertBase):
    """Schema for whale alert API responses"""
    id: int
    detection_id: int

    # Content
    title: str
    message: str
    alert_data: Optional[Dict[str, Any]]

    # Delivery
    sent_at: datetime
    delivery_method: str
    delivery_status: str
    delivery_error: Optional[str]
    recipient_id: Optional[str]

    # Metadata
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Signal Metrics Schemas ====================

class SignalMetricsBase(BaseModel):
    """Base signal metrics schema"""
    signal_name: str = Field(..., description="Signal name")
    date: datetime = Field(..., description="Metrics date")


class SignalMetricsCreate(SignalMetricsBase):
    """Schema for creating signal metrics"""
    total_checks: int = Field(0, ge=0)
    positive_signals: int = Field(0, ge=0)
    true_positives: int = Field(0, ge=0)
    false_positives: int = Field(0, ge=0)

    # Calculated metrics
    precision: Optional[Decimal] = Field(None, ge=0, le=1)
    signal_rate: Optional[Decimal] = Field(None, ge=0, le=1)

    # Average scores
    avg_confidence_when_positive: Optional[Decimal] = Field(None, ge=0, le=100)
    avg_confidence_overall: Optional[Decimal] = Field(None, ge=0, le=100)

    @validator('signal_name')
    def validate_signal_name(cls, v):
        """Validate signal name"""
        allowed = ['time', 'gas', 'nonce', 'amount', 'address', 'composite']
        if v not in allowed:
            raise ValueError(f'Signal name must be one of: {allowed}')
        return v


class SignalMetricsResponse(SignalMetricsBase):
    """Schema for signal metrics API responses"""
    id: int

    # Performance metrics
    total_checks: int
    positive_signals: int
    true_positives: int
    false_positives: int

    # Calculated metrics
    precision: Optional[Decimal]
    signal_rate: Optional[Decimal]

    # Average scores
    avg_confidence_when_positive: Optional[Decimal]
    avg_confidence_overall: Optional[Decimal]

    # Metadata
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Query/Filter Schemas ====================

class OneHopDetectionFilter(BaseModel):
    """Schema for filtering one-hop detections"""
    whale_address: Optional[str] = Field(None, min_length=42, max_length=42)
    intermediate_address: Optional[str] = Field(None, min_length=42, max_length=42)
    exchange_address: Optional[str] = Field(None, min_length=42, max_length=42)

    min_confidence: Optional[int] = Field(None, ge=0, le=100)
    max_confidence: Optional[int] = Field(None, ge=0, le=100)

    detection_method: Optional[str] = None
    status: Optional[str] = None

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    limit: int = Field(100, ge=1, le=1000, description="Results limit")
    offset: int = Field(0, ge=0, description="Results offset")


class IntermediateAddressFilter(BaseModel):
    """Schema for filtering intermediate addresses"""
    profile_type: Optional[str] = None
    min_confidence: Optional[int] = Field(None, ge=0, le=100)
    min_times_used: Optional[int] = Field(None, ge=1)

    is_fresh: Optional[bool] = None
    is_single_use: Optional[bool] = None
    is_reused: Optional[bool] = None

    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# ==================== Bulk Operations Schemas ====================

class BulkTransactionCreate(BaseModel):
    """Schema for bulk transaction creation"""
    transactions: List[TransactionCreate] = Field(..., min_length=1, max_length=1000)


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation responses"""
    success: bool
    created_count: int = 0
    updated_count: int = 0
    failed_count: int = 0
    errors: Optional[List[str]] = None
