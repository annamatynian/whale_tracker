"""
Configuration Constants - Crypto Multi-Agent System
Бизнес-логические константы для алгоритмов и scoring.
Системные настройки (API keys, URLs) находятся в config/settings.py
"""

# Import system settings
from config.settings import get_settings

# Get USDT threshold from settings instead of duplicating
def get_usdt_threshold():
    return get_settings().USDT_DOMINANCE_THRESHOLD

# =============================================================================
# DISCOVERY AGENT BUSINESS LOGIC - ОПТИМИЗИРОВАННЫЕ ФИЛЬТРЫ
# =============================================================================
MIN_LIQUIDITY_USD = 30000        # Было: 15000 → Удвоено для лучшего качества
MIN_VOLUME_H24_USD = 10000       # Было: 5000 → Удвоено для активности
MIN_DISCOVERY_SCORE = 50

# =============================================================================
# DISCOVERY AGENT  
# =============================================================================

# Token filtering thresholds - УЛУЧШЕННЫЕ ПОРОГИ
MIN_LIQUIDITY_USD = 30000        # Оптимизировано: снижает шум, повышает качество
MIN_VOLUME_H24_USD = 10000       # Оптимизировано: фильтрует неактивные токены
MAX_PAIR_AGE_HOURS = 24          # Maximum age for "new" tokens

# Discovery scoring thresholds
MIN_DISCOVERY_SCORE = 50         # Minimum score to proceed to security analysis
LIQUIDITY_THRESHOLD_HIGH = 50000 # High liquidity bonus threshold
VOLUME_THRESHOLD_HIGH = 100000   # High volume bonus threshold

# Age-based scoring
AGE_THRESHOLD_VERY_NEW_MINUTES = 60    # < 1 hour = very new
AGE_THRESHOLD_NEW_HOURS = 6            # < 6 hours = new

# Price change thresholds  
PRICE_CHANGE_THRESHOLD_HIGH = 50       # > 50% = high momentum
PRICE_CHANGE_THRESHOLD_MEDIUM = 20     # > 20% = medium momentum

# Multi-chain configuration
CHAINS_TO_SCAN = ["ethereum", "solana", "base", "arbitrum"]

# =============================================================================
# SECURITY AGENT
# =============================================================================

# Risk scoring weights
HONEYPOT_RISK_SCORE = 90              # Critical - almost certain scam
HIGH_TAX_RISK_SCORE = 40              # High taxes are suspicious  
MEDIUM_TAX_RISK_SCORE = 20            # Medium taxes are concerning
UNVERIFIED_CONTRACT_RISK = 25         # Unverified contracts are risky
NO_LOCKED_LIQUIDITY_RISK = 15         # Unlocked liquidity is concerning

# Tax rate thresholds
HIGH_TAX_THRESHOLD = 0.15             # 15% tax rate = high
MEDIUM_TAX_THRESHOLD = 0.05           # 5% tax rate = medium

# Risk category thresholds
SAFE_THRESHOLD = 20                   # 0-20 = SAFE
CAUTION_THRESHOLD = 40                # 21-40 = CAUTION  
HIGH_RISK_THRESHOLD = 70              # 41-70 = HIGH_RISK, 71+ = SCAM

# =============================================================================
# ORCHESTRATOR BUSINESS LOGIC
# =============================================================================

# Token analysis limits
MAX_TOKENS_TO_ANALYZE = 10            # Limit security checks to top N tokens
MAX_ALERTS_PER_RUN = 5                # Maximum alerts per pipeline run

# Alert generation criteria  
MIN_DISCOVERY_SCORE_FOR_ANALYSIS = 50 # Must match MIN_DISCOVERY_SCORE
MAX_SECURITY_RISK_SCORE = 40          # Must be below CAUTION_THRESHOLD
MIN_LIQUIDITY_FOR_ALERT = 30000       # ОБНОВЛЕНО: совпадает с новым MIN_LIQUIDITY_USD

# Market regime behavior
AGGRESSIVE_MODE_DISCOVERY = True       # Enable discovery in aggressive market
CONSERVATIVE_MODE_DISCOVERY = False    # Disable discovery in conservative market

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Rate limiting (calls per minute)
COINGECKO_RATE_LIMIT = 50
DEXSCREENER_RATE_LIMIT = 100  # No official limit, conservative estimate
GOPLUS_RATE_LIMIT = 100       # 1000 calls/day = ~42/hour = ~1.4/minute

# Retry configuration
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY_SECONDS = 2
API_TIMEOUT_SECONDS = 15

# =============================================================================
# COST MANAGEMENT
# =============================================================================

# Daily budget limits (USD)
DEFAULT_DAILY_BUDGET_USD = 5.0

# API costs (USD per call) - estimates for budget tracking
API_COSTS = {
    'coingecko': 0.0,      # Free tier
    'dexscreener': 0.0,    # Free
    'goplus': 0.0,         # Free tier  
    'telegram': 0.0,       # Free
    'openai_gpt4': 0.03,   # Future use
}

# =============================================================================
# FUNNEL CONFIGURATION - ИСПРАВЛЯЕТ KeyError: 'top_n_for_onchain'
# =============================================================================

FUNNEL_CONFIG = {
    'discovery_limit': 200,        # Лимит для уровня 1 (Discovery)
    'enrichment_limit': 50,        # Лимит для уровня 2 (Enrichment)
    'top_n_for_onchain': 10,       # ← ИСПРАВЛЯЕТ КРАШ KeyError
    'min_final_score': 60,         # Минимальный балл для финального отбора
    'max_alerts': 5               # Максимум алертов за цикл
}

# =============================================================================
# КОНСЕРВАТИВНЫЕ RATE LIMITS - ИСПРАВЛЯЕТ API ПЕРЕГРУЗКУ
# =============================================================================

# Увеличенные задержки для избежания 429 ошибок
ULTRA_CONSERVATIVE_LIMITS = {
    'coingecko': {
        'calls_per_minute': 20,    # Было: 50 → Снижено в 2.5 раза
        'delay_between_calls': 4.0, # Было: 2.0 → Удвоено
    },
    'goplus': {
        'calls_per_minute': 10,    # Было: 100 → Снижено в 10 раз
        'delay_between_calls': 7.0, # Было: 2.0 → Увеличено в 3.5 раза
    }
}

# =============================================================================
# ВРЕМЕННЫЕ ПОРОГИ ДЛЯ ПОЛУЧЕНИЯ РЕЗУЛЬТАТОВ
# =============================================================================

# Снизить пороги чтобы получить результаты для анализа
TEMP_SCORING_THRESHOLDS = {
    'min_discovery_score': 30,     # Было: 50
    'min_final_score': 40,         # Было: 60
    'min_enrichment_score': 25,    # Новый параметр
}

# =============================================================================
# МНОГОУРОВНЕВАЯ СИСТЕМА СКОРИНГА ЛИКВИДНОСТИ
# =============================================================================

# Уровни ликвидности с бонусными баллами
LIQUIDITY_SCORING_TIERS = {
    'premium': {
        'min_liquidity': 100000,   # $100k+ = премиум уровень
        'bonus_points': 20,        # Максимальный бонус
        'description': 'Институциональная ликвидность'
    },
    'high': {
        'min_liquidity': 50000,    # $50k+ = CoinGecko уровень
        'bonus_points': 15,        # Высокий бонус
        'description': 'Высокая ликвидность (CoinGecko)'
    },
    'good': {
        'min_liquidity': 30000,    # $30k+ = наш новый минимум
        'bonus_points': 8,         # Средний бонус
        'description': 'Хорошая ликвидность'
    },
    'acceptable': {
        'min_liquidity': 15000,    # $15k+ = старый минимум
        'bonus_points': 3,         # Минимальный бонус
        'description': 'Приемлемая ликвидность'
    }
}

# Дополнительные множители для объема торгов
VOLUME_MULTIPLIERS = {
    'very_high': {'min_volume': 50000, 'multiplier': 1.5},    # >$50k объем
    'high': {'min_volume': 25000, 'multiplier': 1.3},        # >$25k объем
    'medium': {'min_volume': 10000, 'multiplier': 1.1},      # >$10k объем (новый минимум)
    'low': {'min_volume': 5000, 'multiplier': 1.0}           # >$5k объем (базовый)
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_constants():
    """
    Validates that constants are consistent across agents.
    Call this during system startup to catch configuration errors.
    """
    errors = []
    
    # Check consistency between discovery and orchestrator
    if MIN_LIQUIDITY_FOR_ALERT != MIN_LIQUIDITY_USD:
        errors.append("MIN_LIQUIDITY_FOR_ALERT must equal MIN_LIQUIDITY_USD")
    
    if MIN_DISCOVERY_SCORE_FOR_ANALYSIS != MIN_DISCOVERY_SCORE:
        errors.append("MIN_DISCOVERY_SCORE_FOR_ANALYSIS must equal MIN_DISCOVERY_SCORE")
    
    if MAX_SECURITY_RISK_SCORE >= CAUTION_THRESHOLD:
        errors.append("MAX_SECURITY_RISK_SCORE should be below CAUTION_THRESHOLD")
    
    # Check thresholds make sense
    if SAFE_THRESHOLD >= CAUTION_THRESHOLD:
        errors.append("SAFE_THRESHOLD must be less than CAUTION_THRESHOLD")
    
    if CAUTION_THRESHOLD >= HIGH_RISK_THRESHOLD:
        errors.append("CAUTION_THRESHOLD must be less than HIGH_RISK_THRESHOLD")
    
    if HIGH_TAX_THRESHOLD <= MEDIUM_TAX_THRESHOLD:
        errors.append("HIGH_TAX_THRESHOLD must be greater than MEDIUM_TAX_THRESHOLD")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    return True

# =============================================================================
# EXPORT ALL CONSTANTS
# =============================================================================

__all__ = [
    # Market conditions
    'USDT_DOMINANCE_THRESHOLD',
    
    # Discovery
    'MIN_LIQUIDITY_USD', 'MIN_VOLUME_H24_USD', 'MAX_PAIR_AGE_HOURS',
    'MIN_DISCOVERY_SCORE', 'LIQUIDITY_THRESHOLD_HIGH', 'VOLUME_THRESHOLD_HIGH',
    'AGE_THRESHOLD_VERY_NEW_MINUTES', 'AGE_THRESHOLD_NEW_HOURS',
    'PRICE_CHANGE_THRESHOLD_HIGH', 'PRICE_CHANGE_THRESHOLD_MEDIUM',
    'CHAINS_TO_SCAN',
    
    # Security  
    'HONEYPOT_RISK_SCORE', 'HIGH_TAX_RISK_SCORE', 'MEDIUM_TAX_RISK_SCORE',
    'UNVERIFIED_CONTRACT_RISK', 'NO_LOCKED_LIQUIDITY_RISK',
    'HIGH_TAX_THRESHOLD', 'MEDIUM_TAX_THRESHOLD',
    'SAFE_THRESHOLD', 'CAUTION_THRESHOLD', 'HIGH_RISK_THRESHOLD',
    
    # Orchestrator
    'MAX_TOKENS_TO_ANALYZE', 'MAX_ALERTS_PER_RUN',
    'MIN_DISCOVERY_SCORE_FOR_ANALYSIS', 'MAX_SECURITY_RISK_SCORE', 'MIN_LIQUIDITY_FOR_ALERT',
    'AGGRESSIVE_MODE_DISCOVERY', 'CONSERVATIVE_MODE_DISCOVERY',
    
    # API & Cost
    'COINGECKO_RATE_LIMIT', 'DEXSCREENER_RATE_LIMIT', 'GOPLUS_RATE_LIMIT',
    'API_RETRY_ATTEMPTS', 'API_RETRY_DELAY_SECONDS', 'API_TIMEOUT_SECONDS',
    'DEFAULT_DAILY_BUDGET_USD', 'API_COSTS',
    
    # Funnel Configuration
    'FUNNEL_CONFIG', 'ULTRA_CONSERVATIVE_LIMITS', 'TEMP_SCORING_THRESHOLDS',
    
    # Validation
    'validate_constants'
]

# Validate constants on import
if __name__ != "__main__":
    validate_constants()
