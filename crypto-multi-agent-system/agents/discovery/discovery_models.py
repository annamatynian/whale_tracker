"""
Discovery Models - Актуальные модели для Token Discovery
Центральное место для всех моделей discovery системы

Author: Production Discovery Models  
Version: 2.0 - Clean Architecture
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TokenDiscoveryReport(BaseModel):
    """
    Стандартный формат отчета о найденном токене.
    
    Используется всеми discovery агентами для единообразия данных.
    Совместим с оркестратором и базой данных.
    """
    
    # === ИДЕНТИФИКАТОРЫ ===
    pair_address: str = Field(..., description="Адрес торговой пары на DEX")
    chain_id: str = Field(..., description="ID сети (ethereum, bsc, arbitrum, etc)")
    base_token_address: str = Field(..., description="Адрес базового токена")
    base_token_symbol: str = Field(..., description="Символ базового токена")
    base_token_name: str = Field(..., description="Имя базового токена")
    
    # === ЛИКВИДНОСТЬ И ОБЪЕМЫ ===
    liquidity_usd: float = Field(..., ge=0, description="Ликвидность в USD")
    volume_h24: float = Field(..., ge=0, description="Объем торгов за 24 часа в USD")
    volume_h6: float = Field(default=0, ge=0, description="Объем торгов за 6 часов в USD")
    volume_h1: float = Field(default=0, ge=0, description="Объем торгов за 1 час в USD")
    
    # === ЦЕНА И ИЗМЕНЕНИЯ ===
    price_usd: float = Field(..., description="Текущая цена в USD")
    price_change_m5: float = Field(default=0, description="Изменение цены за 5 минут в %")
    price_change_h1: float = Field(default=0, description="Изменение цены за 1 час в %")
    price_change_h6: float = Field(default=0, description="Изменение цены за 6 часов в %")
    price_change_h24: float = Field(default=0, description="Изменение цены за 24 часа в %")
    
    # === MARKET DATA ===
    fdv: float = Field(default=0, ge=0, description="Fully Diluted Valuation")
    quote_token_symbol: str = Field(default="WETH", description="Символ квотируемого токена")
    dex: str = Field(default="unknown", description="DEX название (uniswap-v2, sushiswap, etc)")
    
    # === ВРЕМЕННЫЕ МЕТРИКИ ===
    pair_created_at: datetime = Field(..., description="Время создания пары")
    age_minutes: float = Field(default=0, ge=0, description="Возраст пары в минутах")
    
    # === DISCOVERY ОЦЕНКА ===
    discovery_score: int = Field(..., ge=0, le=100, description="Оценка перспективности (0-100)")
    discovery_reason: str = Field(..., description="Обоснование оценки")
    
    # === МЕТАДАННЫЕ ===
    data_source: str = Field(default="TheGraph", description="Источник данных")
    discovery_timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="Время обнаружения"
    )
    git_commit_hash: Optional[str] = Field(None, description="Git commit hash для версионирования")
    
    # === PERFORMANCE МЕТРИКИ ===
    api_response_time_ms: Optional[float] = Field(None, description="Время ответа API в мс")
    processing_time_ms: Optional[float] = Field(None, description="Время обработки в мс")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
