"""
Database Models for Crypto Multi-Agent System
Designed for easy migration from SQLite to PostgreSQL
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()


class AnalysisSession(Base):
    """Session of analysis - represents one monitoring cycle"""
    __tablename__ = 'analysis_sessions'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    cycle_number = Column(Integer, nullable=False)
    
    # Discovery stage metrics
    total_candidates_found = Column(Integer, default=0)
    candidates_passed_filters = Column(Integer, default=0)
    
    # Enrichment stage metrics  
    enrichment_attempts = Column(Integer, default=0)
    enrichment_successful = Column(Integer, default=0)
    enrichment_success_rate = Column(Float, default=0.0)
    
    # Final results
    top_candidates_selected = Column(Integer, default=0)
    onchain_analyses_performed = Column(Integer, default=0)
    alerts_generated = Column(Integer, default=0)
    
    # Performance metrics
    cycle_duration_seconds = Column(Float, default=0.0)
    api_calls_coingecko = Column(Integer, default=0)
    api_calls_goplus = Column(Integer, default=0)
    api_calls_rpc = Column(Integer, default=0)
    api_calls_etherscan = Column(Integer, default=0)
    
    # System status
    errors_encountered = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    
    # Relationships
    token_analyses = relationship("TokenAnalysis", back_populates="session")
    alerts = relationship("Alert", back_populates="session")


class Token(Base):
    """Token master data"""
    __tablename__ = 'tokens'
    
    token_address = Column(String(50), primary_key=True)  # Primary key
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(100))
    chain_id = Column(String(20), nullable=False, index=True)
    
    # DEX information
    dex = Column(String(50))
    pair_address = Column(String(50), index=True)
    quote_token_symbol = Column(String(10), default='WETH')
    
    # Discovery metadata
    first_discovered_at = Column(DateTime, default=datetime.utcnow)
    first_discovered_session_id = Column(Integer, ForeignKey('analysis_sessions.id'))
    discovery_count = Column(Integer, default=1)  # How many times discovered
    
    # Current status
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Classification flags
    is_confirmed_scam = Column(Boolean, default=False)
    is_confirmed_pump = Column(Boolean, default=False)
    manual_notes = Column(Text)
    
    # Relationships
    analyses = relationship("TokenAnalysis", back_populates="token")
    alerts = relationship("Alert", back_populates="token")
    performance_history = relationship("TokenPerformance", back_populates="token")


class TokenAnalysis(Base):
    """Individual token analysis result"""
    __tablename__ = 'token_analyses'
    
    id = Column(Integer, primary_key=True)
    token_address = Column(String(50), ForeignKey('tokens.token_address'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Discovery stage data
    discovery_score = Column(Integer, default=0)
    passed_initial_filters = Column(Boolean, default=False)
    filter_reasons = Column(Text)  # JSON string of filter results
    
    # Market data at time of analysis
    price_usd = Column(Float)
    liquidity_usd = Column(Float)
    volume_h24 = Column(Float)
    volume_h6 = Column(Float)
    volume_h1 = Column(Float)
    fdv = Column(Float)
    
    # Price movements
    price_change_m5 = Column(Float)
    price_change_h1 = Column(Float)
    price_change_h6 = Column(Float)
    price_change_h24 = Column(Float)
    
    # Token age and activity
    token_age_hours = Column(Float)
    volume_ratio = Column(Float)  # volume/liquidity
    is_volume_accelerating = Column(Boolean, default=False)
    
    # Enrichment stage data
    coingecko_found = Column(Boolean, default=False)
    coingecko_score = Column(Float)
    coingecko_categories = Column(Text)  # JSON array
    
    goplus_checked = Column(Boolean, default=False)
    is_honeypot = Column(Boolean, default=True)  # Default to safe assumption
    is_open_source = Column(Boolean, default=False)
    buy_tax_percent = Column(Float, default=100.0)  # Default high tax
    sell_tax_percent = Column(Float, default=100.0)
    
    # Narrative analysis
    narrative_type = Column(String(50), default='UNKNOWN')
    has_trending_narrative = Column(Boolean, default=False)
    
    # OnChain analysis data
    onchain_analysis_performed = Column(Boolean, default=False)
    lp_locked_percentage = Column(Float, default=0.0)
    lp_risk_level = Column(String(20), default='CRITICAL')
    holder_concentration_top10 = Column(Float, default=100.0)  # Default high risk
    holder_risk_level = Column(String(20), default='HIGH')
    onchain_overall_risk = Column(String(20), default='CRITICAL')
    
    # Scoring results
    narrative_score = Column(Integer, default=0)
    security_score = Column(Integer, default=0)
    social_score = Column(Integer, default=0)
    onchain_score = Column(Integer, default=0)
    final_score = Column(Integer, default=0)
    
    # Final recommendation
    recommendation = Column(String(30), default='NO_POTENTIAL')
    confidence_level = Column(Float, default=0.0)
    
    # Processing metadata
    enrichment_successful = Column(Boolean, default=False)
    errors_encountered = Column(Text)  # JSON array of error messages
    processing_time_seconds = Column(Float, default=0.0)
    
    # Raw data storage (for debugging and reprocessing)
    raw_dexscreener_data = Column(JSON)
    raw_coingecko_data = Column(JSON)
    raw_goplus_data = Column(JSON)
    raw_onchain_data = Column(JSON)
    
    # Relationships
    token = relationship("Token", back_populates="analyses")
    session = relationship("AnalysisSession", back_populates="token_analyses")
    alert = relationship("Alert", back_populates="analysis", uselist=False)


class Alert(Base):
    """Generated alerts for high-potential tokens"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    token_address = Column(String(50), ForeignKey('tokens.token_address'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('token_analyses.id'), nullable=False)
    
    # Alert metadata
    alert_timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String(30), nullable=False)  # HIGH_POTENTIAL, MEDIUM_POTENTIAL, etc.
    final_score = Column(Integer, nullable=False)
    confidence_level = Column(Float, default=0.0)
    
    # Snapshot data (key metrics at time of alert)
    price_usd_at_alert = Column(Float)
    liquidity_usd_at_alert = Column(Float)
    volume_24h_at_alert = Column(Float)
    
    # Notification status
    telegram_sent = Column(Boolean, default=False)
    telegram_sent_at = Column(DateTime)
    telegram_message_id = Column(String(50))
    
    # Manual tracking
    manually_reviewed = Column(Boolean, default=False)
    manual_notes = Column(Text)
    user_rating = Column(Integer)  # 1-5 star rating from user
    
    # Relationships
    token = relationship("Token", back_populates="alerts")
    session = relationship("AnalysisSession", back_populates="alerts")
    analysis = relationship("TokenAnalysis", back_populates="alert")


class TokenPerformance(Base):
    """Historical price and performance tracking"""
    __tablename__ = 'token_performance'
    
    id = Column(Integer, primary_key=True)
    token_address = Column(String(50), ForeignKey('tokens.token_address'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Price data
    price_usd = Column(Float)
    price_change_1h = Column(Float)
    price_change_24h = Column(Float)
    price_change_7d = Column(Float)
    price_change_30d = Column(Float)
    
    # Market data
    volume_24h = Column(Float)
    market_cap = Column(Float)
    liquidity_usd = Column(Float)
    
    # Performance metrics
    max_price_since_discovery = Column(Float)
    max_gain_percent = Column(Float)
    days_since_discovery = Column(Float)
    
    # Alert correlation (if this record relates to an alert)
    related_alert_id = Column(Integer, ForeignKey('alerts.id'), nullable=True)
    hours_since_alert = Column(Float, nullable=True)
    
    # Data source
    data_source = Column(String(20), default='SYSTEM')  # SYSTEM, MANUAL, COINGECKO
    
    # Relationships
    token = relationship("Token", back_populates="performance_history")


class SystemMetrics(Base):
    """Overall system performance metrics"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow, unique=True)
    
    # Daily statistics
    total_sessions = Column(Integer, default=0)
    total_tokens_discovered = Column(Integer, default=0)
    total_tokens_analyzed = Column(Integer, default=0)
    total_alerts_generated = Column(Integer, default=0)
    
    # Success rates
    enrichment_success_rate = Column(Float, default=0.0)
    alert_generation_rate = Column(Float, default=0.0)  # alerts/tokens analyzed
    
    # API usage
    total_coingecko_calls = Column(Integer, default=0)
    total_goplus_calls = Column(Integer, default=0)
    total_rpc_calls = Column(Integer, default=0)
    total_etherscan_calls = Column(Integer, default=0)
    
    # Performance metrics
    avg_cycle_duration = Column(Float, default=0.0)
    avg_tokens_per_cycle = Column(Float, default=0.0)
    system_uptime_hours = Column(Float, default=0.0)
    
    # Quality metrics (updated manually or by analysis scripts)
    confirmed_true_positives = Column(Integer, default=0)  # Alerts that led to actual pumps
    confirmed_false_positives = Column(Integer, default=0)  # Alerts that didn't materialize
    prediction_accuracy_percent = Column(Float, default=0.0)
    
    # Error tracking
    total_errors = Column(Integer, default=0)
    total_warnings = Column(Integer, default=0)
    critical_failures = Column(Integer, default=0)


# Indexes for performance
from sqlalchemy import Index

# Create composite indexes for common queries
Index('idx_token_analyses_token_time', TokenAnalysis.token_address, TokenAnalysis.timestamp)
Index('idx_token_analyses_session', TokenAnalysis.session_id, TokenAnalysis.final_score)
Index('idx_alerts_time_type', Alert.alert_timestamp, Alert.alert_type)
Index('idx_performance_token_time', TokenPerformance.token_address, TokenPerformance.timestamp)
