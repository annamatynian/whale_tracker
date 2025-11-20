"""
Реалистичные модели для Pump Detection MVP
Основаны только на данных, доступных через бесплатные API

Author: Based on Gemini corrected plan
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NarrativeType(str, Enum):
    """Трендовые нарративы из исследования"""
    AI = "ai"
    LAYER2 = "layer-2" 
    RWA = "real-world-assets"
    DEFI = "defi"
    GAMING = "gaming"
    UNKNOWN = "unknown"

# === ONCHAIN ANALYSIS MODELS ===

class OnChainRiskLevel(str, Enum):
    """Risk level classifications for onchain analysis"""
    SAFE = "SAFE"
    MODERATE = "MODERATE"
    HIGH = "HIGH" 
    CRITICAL = "CRITICAL"

class LiquidityAnalysisResult(BaseModel):
    """LP token distribution analysis result"""
    total_lp_supply: int = Field(default=0, description="Total LP token supply")
    locked_percentage: float = Field(default=0.0, description="% locked in known lockers")
    dead_percentage: float = Field(default=0.0, description="% sent to dead addresses")
    unknown_contract_percentage: float = Field(default=0.0, description="% in unknown contracts")
    eoa_controlled_percentage: float = Field(default=0.0, description="% controlled by EOA wallets")
    risk_level: OnChainRiskLevel = Field(default=OnChainRiskLevel.CRITICAL, description="LP safety assessment")
    details: List[str] = Field(default_factory=list, description="Analysis details")

class HolderAnalysisResult(BaseModel):
    """Token holder concentration analysis result"""
    total_holders: int = Field(default=0, description="Total number of holders")
    top_10_concentration: float = Field(default=0.0, description="% held by top 10 EOA wallets")
    top_20_concentration: float = Field(default=0.0, description="% held by top 20 EOA wallets")
    exchange_percentage: float = Field(default=0.0, description="% held by exchanges")
    contract_percentage: float = Field(default=0.0, description="% held by contracts")
    risk_level: OnChainRiskLevel = Field(default=OnChainRiskLevel.MODERATE, description="Concentration risk")
    details: List[str] = Field(default_factory=list, description="Analysis details")

class OnChainAnalysisResult(BaseModel):
    """Complete onchain analysis result"""
    lp_analysis: Optional[LiquidityAnalysisResult] = None
    holder_analysis: Optional[HolderAnalysisResult] = None
    overall_risk: OnChainRiskLevel = Field(default=OnChainRiskLevel.MODERATE)
    recommendation: str = Field(default="PROCEED_WITH_CAUTION")
    analysis_errors: List[str] = Field(default_factory=list)
    
    # Scoring integration
    lp_safety_score: int = Field(default=0, ge=0, le=10, description="LP safety score (0-10)")
    holder_safety_score: int = Field(default=0, ge=0, le=5, description="Holder safety score (0-5)")
    onchain_bonus: int = Field(default=0, ge=0, le=15, description="Total onchain bonus (0-15)")
    
    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    network: str = Field(default="", description="Blockchain network analyzed")
    api_calls_used: int = Field(default=0, description="Number of API calls made")

# === DISCOVERY MODELS ===

class TokenCandidate(BaseModel):
    """Simple token candidate model for testing and discovery"""
    base_token_address: str
    base_token_name: str
    base_token_symbol: str
    quote_token_symbol: str = "WETH"
    price_usd: float
    fdv: float
    liquidity_usd: float
    volume_h24: float
    price_change_m5: float = 0
    price_change_h1: float = 0
    price_change_h6: float = 0
    price_change_h24: float = 0
    chain_id: str
    pair_address: str
    dex: str
    pair_created_at: float  # timestamp
    volume_h1: float = 0
    volume_h6: float = 0
    discovery_score: int = 0

# === EXISTING MODELS ===

class PumpIndicators(BaseModel):
    """
    Pump индикаторы, основанные ТОЛЬКО на доступных данных
    Убраны фантазийные проверки (sterile_deployer, vc_backing)
    """
    
    # === ДАННЫЕ, КОТОРЫЕ МЫ МОЖЕМ ПОЛУЧИТЬ ===
    contract_address: str = Field(..., description="Адрес контракта")
    
    # CoinGecko Demo данные
    narrative_alignment: NarrativeType = Field(default=NarrativeType.UNKNOWN, description="Соответствие тренду")
    market_cap_usd: Optional[float] = Field(None, description="Market cap в USD")
    community_score: Optional[float] = Field(None, description="Community score из CoinGecko")
    developer_score: Optional[float] = Field(None, description="Developer activity score")
    
    # GoPlus Security данные
    is_honeypot: bool = Field(default=True, description="Honeypot проверка")
    is_open_source: bool = Field(default=False, description="Контракт верифицирован")
    has_mint_function: Optional[bool] = Field(None, description="Есть ли функция mint")
    
    # Telegram Social данные  
    social_mentions: int = Field(default=0, description="Упоминания в alpha каналах")
    first_mention_timestamp: Optional[datetime] = Field(None, description="Первое упоминание")
    
    # DexScreener данные
    liquidity_usd: float = Field(default=0, description="Ликвидность в USD")
    volume_24h: float = Field(default=0, description="Объем за 24 часа")
    volume_h1: float = Field(default=0, description="Объем за 1 час")
    volume_h6: float = Field(default=0, description="Объем за 6 часов")
    is_volume_accelerating: bool = Field(default=False, description="Ускоряется ли объем")
    age_hours: float = Field(default=0, description="Возраст токена в часах")
    
    # === OnChain анализ (новое) ===
    onchain_analysis: Optional[OnChainAnalysisResult] = Field(None, description="Результат OnChain анализа")
    
    # === ФИНАЛЬНАЯ ОЦЕНКА ===
    pump_probability_score: int = Field(default=0, ge=0, le=100, description="Вероятность пампа 0-100")
    recommendation: str = Field(default="UNKNOWN", description="STRONG_PUMP/PUMP_BUY/PUMP_WATCH/AVOID")
    
    # === МЕТАДАННЫЕ ===
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    data_completeness_percent: float = Field(default=0, description="Полнота данных %")

class PumpAnalysisReport(BaseModel):
    """Финальный отчет анализа pump потенциала"""
    
    contract_address: str
    base_token_symbol: Optional[str] = None
    base_token_name: Optional[str] = None

    chain_id: Optional[str] = None
    pair_address: Optional[str] = None
    
    # Volume acceleration данные
    volume_h1: float = Field(default=0, description="Объем за 1 час")
    volume_h6: float = Field(default=0, description="Объем за 6 часов")
    is_volume_accelerating: bool = Field(default=False, description="Ускоряется ли объем")
    volume_acceleration_bonus: int = Field(default=0, description="Бонус за ускорение объема")
    
    indicators: PumpIndicators
    
    # Детализация оценки
    narrative_score: int = Field(ge=0, le=40, description="Очки за нарратив")
    security_score: int = Field(ge=0, le=35, description="Очки за безопасность") 
    social_score: int = Field(ge=0, le=25, description="Очки за социальную активность")
    onchain_score: int = Field(default=0, ge=0, le=15, description="Очки за OnChain анализ")
    
    # Обоснование
    reasoning: List[str] = Field(default_factory=list, description="Причины оценки")
    red_flags: List[str] = Field(default_factory=list, description="Красные флаги")
    
    # Источники данных
    data_sources_used: List[str] = Field(default_factory=list, description="Использованные API")
    api_calls_made: int = Field(default=0, description="Количество API вызовов")
    
    # Финальные рекомендации
    final_score: int = Field(ge=0, le=115)  # Увеличено с 100 до 115 из-за onchain_score
    confidence_level: float = Field(ge=0, le=1, description="Уверенность в оценке")
    next_steps: List[str] = Field(default_factory=list, description="Следующие шаги")

class ApiUsageTracker(BaseModel):
    """Отслеживание использования бесплатных API лимитов"""
    
    # CoinGecko Demo (10K calls/месяц)
    coingecko_calls_today: int = 0
    coingecko_daily_limit: int = 323  # 10k/31 день
    
    # GoPlus Free (150K CU/месяц) 
    goplus_cu_today: int = 0
    goplus_daily_limit: int = 5000  # 150k/30 дней
    
    # DexScreener Free (300 calls/минуту)
    dexscreener_calls_minute: int = 0
    dexscreener_minute_limit: int = 300
    
    # Telegram Premium
    telegram_checks_today: int = 0
    
    # OnChain APIs
    etherscan_calls_today: int = 0
    etherscan_daily_limit: int = 100000  # 100k calls/day for free tier
    
    rpc_calls_today: int = 0
    rpc_daily_limit: int = 3000000  # 3M credits/day for Infura free tier
    
    last_reset: datetime = Field(default_factory=datetime.now)
    
    def can_make_coingecko_call(self) -> bool:
        return self.coingecko_calls_today < self.coingecko_daily_limit
    
    def can_make_goplus_call(self) -> bool:
        return self.goplus_cu_today < self.goplus_daily_limit
    
    def can_make_dexscreener_call(self) -> bool:
        return self.dexscreener_calls_minute < self.dexscreener_minute_limit
    
    def can_make_etherscan_call(self) -> bool:
        return self.etherscan_calls_today < self.etherscan_daily_limit
        
    def can_make_rpc_call(self) -> bool:
        return self.rpc_calls_today < self.rpc_daily_limit
