"""
Pump Scoring Matrix - Точная реализация из PDF исследования (стр. 12-13)
Оценочная карта вероятности пампа с весами из исследования

Author: Based on "Анатомия спекулятивного пампа" research
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, List

class PumpRecommendation(str, Enum):
    """Рекомендации на основе итогового score"""
    STRONG_PUMP = "STRONG_PUMP"     # 25-31 баллов
    PUMP_BUY = "PUMP_BUY"          # 18-24 балла
    PUMP_WATCH = "PUMP_WATCH"       # 12-17 баллов
    LOW_PRIORITY = "LOW_PRIORITY"   # <12 баллов

class PumpScoringMatrix(BaseModel):
    """
    Взвешенная оценочная карта из исследования (стр. 12-13)
    
    КРИТИЧНЫЕ НАХОДКИ ИЗ ИССЛЕДОВАНИЯ:
    - ВСЕ пампы имели float <30%
    - 90% имели поддержку Tier-1 VC
    - 95% запускались листингом на крупной CEX
    - 100% соответствовали трендовому нарративу
    """
    
    # === ОНЧЕЙН ИНДИКАТОРЫ (максимум 10 баллов) ===
    sterile_deployer: bool = Field(default=False, description="Стерильный деплоер (85% случаев)")
    low_float: bool = Field(default=False, description="Низкий флот <30% (100% случаев)") 
    high_insider_concentration: bool = Field(default=False, description="Высокая концентрация инсайдеров")
    
    # === ТОКЕНОМИКА (максимум 3 балла) ===
    long_vesting: bool = Field(default=False, description="Длительные блокировки >6 мес")
    
    # === РЫНОЧНЫЕ КАТАЛИЗАТОРЫ (максимум 13 баллов) ===
    tier1_cex_listing: bool = Field(default=False, description="Подтвержденный листинг Tier-1 CEX")
    strategic_airdrop: bool = Field(default=False, description="Недавний стратегический аирдроп")
    strong_vc_support: bool = Field(default=False, description="Сильная поддержка VC")
    narrative_alignment: bool = Field(default=False, description="Соответствие актуальному нарративу")
    kol_endorsement: bool = Field(default=False, description="Громкая поддержка")
    
    def calculate_total_score(self) -> int:
        """
        Расчет итогового score по точным весам из исследования
        
        Returns:
            int: Общий score (0-31 баллов)
        """
        score = 0
        
        # Ончейн индикаторы (веса из таблицы стр. 13)
        if self.sterile_deployer: score += 2
        if self.low_float: score += 3           # Максимальный вес - критический фактор
        if self.high_insider_concentration: score += 2
        
        # Токеномика
        if self.long_vesting: score += 3
        
        # Рыночные катализаторы (веса из таблицы стр. 13)
        if self.tier1_cex_listing: score += 5  # Максимальный вес - главный триггер
        if self.strategic_airdrop: score += 4
        if self.strong_vc_support: score += 4
        if self.narrative_alignment: score += 3
        if self.kol_endorsement: score += 5     # Максимальный вес
        
        return score
    
    def get_recommendation(self) -> PumpRecommendation:
        """
        Получить рекомендацию на основе score
        
        Пороги основаны на исследовании:
        - Все токены >25 баллов показали памп >200%
        - Токены 18-24 показали умеренный рост
        """
        score = self.calculate_total_score()
        
        if score >= 25:
            return PumpRecommendation.STRONG_PUMP
        elif score >= 18:
            return PumpRecommendation.PUMP_BUY
        elif score >= 12:
            return PumpRecommendation.PUMP_WATCH
        else:
            return PumpRecommendation.LOW_PRIORITY
    
    def get_detailed_analysis(self) -> Dict[str, any]:
        """
        Детальный анализ с обоснованием score
        """
        score = self.calculate_total_score()
        recommendation = self.get_recommendation()
        
        # Анализ по категориям
        onchain_score = (
            (2 if self.sterile_deployer else 0) +
            (3 if self.low_float else 0) +
            (2 if self.high_insider_concentration else 0)
        )
        
        tokenomics_score = 3 if self.long_vesting else 0
        
        market_score = (
            (5 if self.tier1_cex_listing else 0) +
            (4 if self.strategic_airdrop else 0) +
            (4 if self.strong_vc_support else 0) +
            (3 if self.narrative_alignment else 0) +
            (5 if self.kol_endorsement else 0)
        )
        
        # Формируем reasons
        reasons = []
        if self.low_float:
            reasons.append("✅ КРИТИЧНО: Низкий флот (<30%) - в 100% пампов")
        if self.tier1_cex_listing:
            reasons.append("🚀 ГЛАВНЫЙ ТРИГГЕР: Листинг на Tier-1 CEX")
        if self.strong_vc_support:
            reasons.append("💰 VC поддержка - в 90% пампов")
        if self.narrative_alignment:
            reasons.append("📈 Соответствует трендовому нарративу")
        if self.kol_endorsement:
            reasons.append("🔥 Громкая поддержка - мощный катализатор")
        
        # Red flags
        red_flags = []
        if not self.low_float:
            red_flags.append("❌ КРИТИЧНО: Нет данных о флоте")
        if not self.narrative_alignment:
            red_flags.append("⚠️ Нет соответствия трендам")
        if score < 12:
            red_flags.append("📉 Низкий общий score")
        
        return {
            'total_score': score,
            'max_possible': 31,
            'recommendation': recommendation.value,
            'category_scores': {
                'onchain': onchain_score,
                'tokenomics': tokenomics_score,
                'market_catalysts': market_score
            },
            'positive_signals': reasons,
            'red_flags': red_flags,
            'confidence_level': min(score / 31, 1.0)
        }

# === ИСТОРИЧЕСКИЕ ПРИМЕРЫ ИЗ ИССЛЕДОВАНИЯ ===

HISTORICAL_EXAMPLES = {
    'AVNT': PumpScoringMatrix(
        low_float=True,           # 25.8% в обращении
        strong_vc_support=True,   # Pantera Capital, Founders Fund  
        tier1_cex_listing=True,   # Coinbase, Bybit
        narrative_alignment=True, # RWA + L2 нарратив
        strategic_airdrop=True    # Binance аирдроп
    ),
    'SAPIEN': PumpScoringMatrix(
        low_float=True,           # 25% в обращении  
        strong_vc_support=True,   # $15.5M от топ VC
        tier1_cex_listing=True,   # Множественные листинги
        narrative_alignment=True, # AI нарратив
        strategic_airdrop=True    # 5% аирдроп
    ),
    'OPENX': PumpScoringMatrix(
        low_float=True,           # 10% в обращении
        tier1_cex_listing=True,   # LBank
        narrative_alignment=True, # AI нарратив
        kol_endorsement=True      # CEO Coinbase
    )
}

def validate_historical_examples():
    """Валидация на исторических примерах из исследования"""
    print("🧪 ВАЛИДАЦИЯ НА ИСТОРИЧЕСКИХ ПРИМЕРАХ")
    print("=" * 50)
    
    for token_name, matrix in HISTORICAL_EXAMPLES.items():
        analysis = matrix.get_detailed_analysis()
        
        print(f"\n📊 {token_name}:")
        print(f"   Score: {analysis['total_score']}/31")
        print(f"   Recommendation: {analysis['recommendation']}")
        print(f"   Confidence: {analysis['confidence_level']:.2f}")
        
        # Показать ключевые сигналы
        if analysis['positive_signals']:
            print(f"   Signals: {analysis['positive_signals'][0]}")

if __name__ == "__main__":
    validate_historical_examples()
