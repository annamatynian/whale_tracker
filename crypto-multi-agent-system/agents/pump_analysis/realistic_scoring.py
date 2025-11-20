"""
РЕАЛИСТИЧНАЯ Pump Scoring Matrix - MVP версия с OnChain анализом
Основана ТОЛЬКО на данных, доступных через бесплатные API

Author: MVP Version with OnChain integration
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, List, Optional

# Импортируем NarrativeType и OnChain модели из pump_models
from .pump_models import NarrativeType, OnChainAnalysisResult, OnChainRiskLevel

class PumpRecommendationMVP(str, Enum):
    """MVP рекомендации на основе реалистичного scoring (максимум 105 баллов с OnChain)"""
    HIGH_POTENTIAL = "HIGH_POTENTIAL"     # 85-105 баллов  
    MEDIUM_POTENTIAL = "MEDIUM_POTENTIAL" # 60-84 балла  
    LOW_POTENTIAL = "LOW_POTENTIAL"       # 35-59 баллов
    NO_POTENTIAL = "NO_POTENTIAL"         # <35 баллов

class RealisticPumpIndicators(BaseModel):
    """
    РЕАЛИСТИЧНЫЕ индикаторы на основе доступных API
    
    ✅ ЧТО МЫ МОЖЕМ ПОЛУЧИТЬ:
    - Narrative alignment (CoinGecko Demo)
    - Security checks (GoPlus Free)  
    - Basic metrics (DexScreener Free)
    - OnChain analysis (Etherscan + RPC)
    """
    
    # === DISCOVERY DATA (40 баллов максимум) ===
    discovery_score: float = Field(default=0, ge=0, le=100, description="Discovery score из PumpDiscoveryAgent")
    
    # === ДАННЫЕ ИЗ COINGECKO (ВРЕМЕННО ОТКЛЮЧЕНЫ - 40 баллов) ===
    narrative_type: NarrativeType = Field(default=NarrativeType.UNKNOWN, description="Тип нарратива")
    has_trending_narrative: bool = Field(default=False, description="Соответствует ли трендовому нарративу")
    coingecko_score: Optional[float] = Field(None, ge=0, le=100, description="Community score из CoinGecko")
    
    # === ДАННЫЕ ИЗ GOPLUS (35 баллов максимум) ===
    is_honeypot: bool = Field(default=False, description="Honeypot проверка")
    is_open_source: bool = Field(default=False, description="Контракт верифицирован")
    has_mint_function: Optional[bool] = Field(None, description="Есть ли функция mint")
    buy_tax_percent: float = Field(default=5.0, ge=0, le=100, description="Налог на покупку %")
    sell_tax_percent: float = Field(default=5.0, ge=0, le=100, description="Налог на продажу %")
    
    # === VOLUME ACCELERATION (15 баллов максимум) ===
    volume_h1: float = Field(default=0, description="Объем за 1 час")
    volume_h6: float = Field(default=0, description="Объем за 6 часов")
    is_volume_accelerating: bool = Field(default=False, description="Ускоряется ли объем")
    volume_ratio_healthy: bool = Field(default=False, description="Здоровый volume ratio (0.5-3.0)")
    price_h1: float = Field(default=0, description="Изменение цены за 1 час")
    price_h6: float = Field(default=0, description="Изменение цены за 6 часов")
    
    # === ONCHAIN ANALYSIS (15 баллов максимум) ===
    onchain_analysis: Optional[OnChainAnalysisResult] = Field(None, description="Результат OnChain анализа")
    
    # === МЕТАДАННЫЕ ===
    data_completeness_percent: float = Field(default=0, ge=0, le=100, description="Полнота данных")
    api_calls_used: int = Field(default=0, description="Потрачено API calls")

class RealisticScoringMatrix(BaseModel):
    """
    MVP Scoring Matrix с OnChain анализом
    
    Веса:
    - Narrative (40 баллов) - самый сильный автоматизируемый сигнал
    - Security (35 баллов) - критично для отсева скама
    - Volume (15 баллов) - подтверждение активности
    - OnChain (15 баллов) - структурная безопасность
    
    Максимум: 105 баллов
    """
    
    indicators: RealisticPumpIndicators
    
    def calculate_narrative_score(self) -> int:
        """Оценка нарратива (максимум 40 баллов)"""
        score = 0
        
        # === ОСНОВА: DISCOVERY SCORE ===
        # Discovery score от TheGraph - это базовая оценка потенциала
        if self.indicators.discovery_score > 80:
            score += 25  # Отличный discovery score
        elif self.indicators.discovery_score > 60:
            score += 20  # Хороший discovery score
        elif self.indicators.discovery_score > 40:
            score += 15  # Средний discovery score
        elif self.indicators.discovery_score > 20:
            score += 10  # Низкий discovery score
        # < 20 = 0 баллов
        
        # === БОНУСЫ: НАРРАТИВ И COMMUNITY ===
        # Главный бонус за трендовый нарратив
        if self.indicators.has_trending_narrative:
            if self.indicators.narrative_type in [NarrativeType.AI, NarrativeType.LAYER2]:
                score += 10  # Самые горячие нарративы
            elif self.indicators.narrative_type == NarrativeType.RWA:
                score += 8   # Актуальный нарратив
            else:
                score += 5   # Другие нарративы
        
        # Бонус за community score
        if self.indicators.coingecko_score and self.indicators.coingecko_score > 50:
            score += 5
        elif self.indicators.coingecko_score and self.indicators.coingecko_score > 30:
            score += 3
            
        return min(score, 40)
    
    def calculate_volume_score(self) -> int:
        """Оценка Volume Acceleration (максимум 15 баллов)"""
        score = 0
        
        # Проверяем, что объем ускоряется прямо сейчас
        if self.indicators.is_volume_accelerating and self.indicators.volume_h1 > 10000:
            score += 10  # Сильный сигнал ускорения
        elif self.indicators.is_volume_accelerating:
            score += 5   # Ускорение есть, но объем небольшой
            
        # "Золотая середина" - активность без перегрева
        if self.indicators.volume_ratio_healthy:
            score += 5   # Здоровый volume ratio (0.5-3.0)
            
        return min(score, 15)
    
    def calculate_security_score(self) -> int:
        """Оценка безопасности (максимум 35 баллов)"""
        score = 0
        
        # Жесткое правило 1: Honeypot = автоматический 0
        if self.indicators.is_honeypot:
            return 0  # Honeypot = автоматический 0
        
        # Жесткое правило 2: Очень высокие налоги = скам
        if self.indicators.buy_tax_percent > 50 or self.indicators.sell_tax_percent > 50:
            return 0  # Налоги >50% = почти всегда скам
            
        # Базовая безопасность - критично
        score += 20  # Не honeypot и нормальные налоги - основа основ
            
        # Открытый код
        if self.indicators.is_open_source:
            score += 10  # Верифицированный контракт
            
        # Разумные налоги (дополнительные бонусы)
        if self.indicators.buy_tax_percent <= 5 and self.indicators.sell_tax_percent <= 10:
            score += 5   # Низкие налоги
        elif self.indicators.buy_tax_percent <= 10 and self.indicators.sell_tax_percent <= 15:
            score += 2   # Умеренные налоги
            
        return score
    
    def calculate_onchain_score(self) -> int:
        """Оценка OnChain анализа (максимум 15 баллов)"""
        if not self.indicators.onchain_analysis:
            return 0  # Нет OnChain данных
        
        score = 0
        onchain = self.indicators.onchain_analysis
        
        # LP Safety Score (0-10 баллов)
        if onchain.lp_analysis:
            if onchain.lp_analysis.risk_level == OnChainRiskLevel.SAFE:
                score += 10  # Ликвидность заблокирована безопасно
            elif onchain.lp_analysis.risk_level == OnChainRiskLevel.MODERATE:
                score += 5   # Частичная блокировка
            elif onchain.lp_analysis.risk_level == OnChainRiskLevel.HIGH:
                score += 2   # Минимальная защита
            # CRITICAL = 0 баллов
        
        # Holder Concentration Score (0-5 баллов)
        if onchain.holder_analysis:
            if onchain.holder_analysis.risk_level == OnChainRiskLevel.LOW:
                score += 5   # Низкая концентрация - здоровое распределение
            elif onchain.holder_analysis.risk_level == OnChainRiskLevel.MODERATE:
                score += 3   # Умеренная концентрация
            elif onchain.holder_analysis.risk_level == OnChainRiskLevel.HIGH:
                score += 1   # Высокая концентрация - риск дампа
            # CRITICAL = 0 баллов
        
        return min(score, 15)
    
    def calculate_total_score(self) -> int:
        """Итоговый MVP score (максимум 105 баллов)"""
        
        # ЖЕСТКОЕ ПРАВИЛО: Honeypot = 0 баллов ИТОГО
        if self.indicators.is_honeypot:
            return 0  # Независимо от нарратива!
        
        # ЖЕСТКОЕ ПРАВИЛО: Очень высокие налоги = 0 баллов
        if self.indicators.buy_tax_percent > 50 or self.indicators.sell_tax_percent > 50:
            return 0  # Налоги >50% = почти всегда скам
        
        # ЖЕСТКОЕ ПРАВИЛО: Критический OnChain риск = максимум 50% от возможного
        onchain = self.indicators.onchain_analysis
        if (onchain and onchain.lp_analysis and 
            onchain.lp_analysis.risk_level == OnChainRiskLevel.CRITICAL):
            # Если высокий риск rug pull, ограничиваем максимальный балл
            max_allowed = 52  # 50% от 105
        else:
            max_allowed = 105
        
        # Обычный расчет для чистых токенов
        narrative_score = self.calculate_narrative_score()
        security_score = self.calculate_security_score()
        volume_score = self.calculate_volume_score()
        onchain_score = self.calculate_onchain_score()
        
        total = narrative_score + security_score + volume_score + onchain_score
        return min(total, max_allowed)
    
    def get_recommendation(self) -> PumpRecommendationMVP:
        """MVP рекомендация на основе реалистичного scoring (максимум 105 баллов)"""
        score = self.calculate_total_score()
        
        if score >= 85:
            return PumpRecommendationMVP.HIGH_POTENTIAL
        elif score >= 60:
            return PumpRecommendationMVP.MEDIUM_POTENTIAL
        elif score >= 35:
            return PumpRecommendationMVP.LOW_POTENTIAL
        else:
            return PumpRecommendationMVP.NO_POTENTIAL
    
    def get_detailed_analysis(self) -> Dict[str, any]:
        """Детальный анализ с реалистичным обоснованием"""
        narrative_score = self.calculate_narrative_score()
        security_score = self.calculate_security_score()
        volume_score = self.calculate_volume_score()
        onchain_score = self.calculate_onchain_score()
        total_score = self.calculate_total_score()
        
        reasons = []
        red_flags = []
        
        # Позитивные сигналы
        if self.indicators.has_trending_narrative:
            reasons.append(f"Trending narrative: {self.indicators.narrative_type.value}")
        if not self.indicators.is_honeypot:
            reasons.append("Not honeypot - safe to trade")
        if self.indicators.is_open_source:
            reasons.append("Verified contract")
        
        # Volume acceleration сигналы
        if self.indicators.is_volume_accelerating:
            reasons.append("Volume accelerating now")
        if self.indicators.volume_ratio_healthy:
            reasons.append("Healthy trading activity")
        
        # OnChain сигналы
        onchain = self.indicators.onchain_analysis
        if onchain:
            if onchain.lp_analysis and onchain.lp_analysis.risk_level == OnChainRiskLevel.SAFE:
                reasons.append("Liquidity safely locked")
            if onchain.holder_analysis and onchain.holder_analysis.risk_level == OnChainRiskLevel.LOW:
                reasons.append("Low holder concentration")
            
        # Красные флаги
        if self.indicators.is_honeypot:
            red_flags.append("HONEYPOT - avoid")
        if self.indicators.buy_tax_percent > 10:
            red_flags.append(f"High buy tax: {self.indicators.buy_tax_percent}%")
        if self.indicators.narrative_type == NarrativeType.UNKNOWN:
            red_flags.append("Unknown narrative")
        
        # OnChain красные флаги
        if onchain:
            if onchain.lp_analysis and onchain.lp_analysis.risk_level == OnChainRiskLevel.CRITICAL:
                red_flags.append("HIGH RUG PULL RISK - LP not locked")
            if onchain.holder_analysis and onchain.holder_analysis.risk_level == OnChainRiskLevel.HIGH:
                red_flags.append("High whale concentration - dump risk")
            
        return {
            'total_score': total_score,
            'max_possible': 105,
            'recommendation': self.get_recommendation().value,
            'category_scores': {
                'narrative': narrative_score,
                'security': security_score,
                'volume': volume_score,
                'onchain': onchain_score
            },
            'positive_signals': reasons,
            'red_flags': red_flags,
            'confidence_level': min(total_score / 105, 1.0),
            'data_completeness': self.indicators.data_completeness_percent
        }

# === UPDATED WEIGHTS ===
MVP_SCORING_WEIGHTS = {
    'narrative_alignment': 40,  # Самый сильный автоматизируемый сигнал
    'security_checks': 35,      # Критично для отсева скама
    'volume_acceleration': 15,  # Подтверждение объемов
    'onchain_analysis': 15      # Структурная безопасность
    # Максимум: 40 + 35 + 15 + 15 = 105 баллов
}

def should_spend_api_calls(basic_score: int, available_calls: int) -> bool:
    """
    Определить, стоит ли тратить API calls на токен
    
    Args:
        basic_score: Базовый score из DexScreener
        available_calls: Оставшиеся API calls
        
    Returns:
        bool: Стоит ли анализировать дальше
    """
    # Если calls на исходе, только топ токены
    if available_calls < 10:
        return basic_score > 80
    elif available_calls < 50:
        return basic_score > 60
    else:
        return basic_score > 40

def should_run_onchain_analysis(enriched_score: int, available_onchain_calls: int) -> bool:
    """
    Определить, стоит ли запускать дорогой OnChain анализ
    
    Args:
        enriched_score: Score после обогащения данных (CoinGecko + GoPlus)
        available_onchain_calls: Оставшиеся OnChain API calls
        
    Returns:
        bool: Стоит ли тратить OnChain ресурсы
    """
    # OnChain анализ только для высокопотенциальных токенов
    if available_onchain_calls < 5:
        return enriched_score > 80  # Только лучшие при нехватке calls
    elif available_onchain_calls < 20:
        return enriched_score > 70  # Строже при ограниченных ресурсах
    else:
        return enriched_score > 60  # Стандартный порог

# === ТЕСТИРОВАНИЕ ===

def test_realistic_scoring():
    """Тест с реалистичными данными включая OnChain"""
    print("ТЕСТ РЕАЛИСТИЧНОГО SCORING С ONCHAIN")
    print("=" * 50)
    
    # Пример 1: Идеальный токен с OnChain анализом
    from .pump_models import OnChainAnalysisResult, LiquidityAnalysisResult, HolderAnalysisResult
    
    perfect_lp = LiquidityAnalysisResult(
        locked_percentage=95.0,
        risk_level=OnChainRiskLevel.SAFE,
        details=["LP safely locked in Unicrypt"]
    )
    
    perfect_holders = HolderAnalysisResult(
        top_10_concentration=15.0,
        risk_level=OnChainRiskLevel.LOW,
        details=["Healthy distribution among many holders"]
    )
    
    perfect_onchain = OnChainAnalysisResult(
        lp_analysis=perfect_lp,
        holder_analysis=perfect_holders,
        overall_risk=OnChainRiskLevel.SAFE,
        lp_safety_score=10,
        holder_safety_score=5,
        onchain_bonus=15
    )
    
    perfect_indicators = RealisticPumpIndicators(
        narrative_type=NarrativeType.AI,
        has_trending_narrative=True,
        coingecko_score=85.0,
        is_honeypot=False,
        is_open_source=True,
        buy_tax_percent=2.0,
        sell_tax_percent=5.0,
        is_volume_accelerating=True,
        volume_h1=50000,
        volume_ratio_healthy=True,
        onchain_analysis=perfect_onchain,
        data_completeness_percent=95.0
    )
    
    perfect_matrix = RealisticScoringMatrix(indicators=perfect_indicators)
    perfect_analysis = perfect_matrix.get_detailed_analysis()
    
    print(f"PERFECT TOKEN:")
    print(f"   Score: {perfect_analysis['total_score']}/105")
    print(f"   Recommendation: {perfect_analysis['recommendation']}")
    print(f"   Category scores: {perfect_analysis['category_scores']}")

if __name__ == "__main__":
    test_realistic_scoring()
