"""
Tier Scoring Matrix - определение tier'а на основе метрик
Заменяет балльную систему на прозрачные критерии

Author: Tier Scoring v1.0
Date: 2025-01-20
"""

from typing import List, Optional, Dict, Set
from .tier_system import (
    TokenTier, TagStatus, TagCategory, TokenTag, TierAnalysisResult,
    TierCriteria, create_tag
)
from .pump_models import NarrativeType, OnChainAnalysisResult, OnChainRiskLevel


class TierScoringMatrix:
    """
    Матрица для определения tier'а токена.
    
    Основные принципы:
    1. Tier определяется по НАЛИЧИЮ критериев, а не по сумме баллов
    2. Один критичный red flag может опустить токен в AVOID
    3. Все метрики видны как теги - полная прозрачность
    """
    
    def __init__(self):
        """Инициализация матрицы"""
        self.tags: List[TokenTag] = []
        self.critical_flags: List[str] = []
        self.criteria_met: Set[str] = set()
    
    # ========================================
    # VOLUME ANALYSIS TAGS
    # ========================================
    
    def analyze_volume_ratio(
        self,
        volume_ratio: float,
        ratio_healthy: bool,
        ratio_overheated: bool,
        ratio_dead: bool
    ) -> TokenTag:
        """
        Анализ Volume Ratio (золотая середина 0.5-3.0).
        
        GREEN: 0.5 < ratio < 3.0 (здоровая активность)
        YELLOW: ratio > 3.0 (перегрев, возможны манипуляции)
        RED: ratio < 0.5 (мёртвый токен)
        """
        if ratio_dead:
            self.critical_flags.append("Dead token - no real trading activity")
            return create_tag(
                name="DEAD_TOKEN",
                category=TagCategory.VOLUME,
                status=TagStatus.RED,
                value=volume_ratio,
                threshold="< 0.5",
                reasoning=f"Ratio {volume_ratio:.3f} < 0.5 - token is dead",
                weight=1.0
            )
        
        elif ratio_overheated:
            return create_tag(
                name="OVERHEATED_RATIO",
                category=TagCategory.VOLUME,
                status=TagStatus.YELLOW,
                value=volume_ratio,
                threshold="0.5-3.0",
                reasoning=f"Ratio {volume_ratio:.3f} > 3.0 - possible wash trading",
                weight=0.7
            )
        
        elif ratio_healthy:
            self.criteria_met.add("healthy_volume_ratio")
            return create_tag(
                name="HEALTHY_VOLUME_RATIO",
                category=TagCategory.VOLUME,
                status=TagStatus.GREEN,
                value=volume_ratio,
                threshold="0.5-3.0",
                reasoning=f"Ratio {volume_ratio:.3f} in golden range",
                weight=0.9
            )
        
        else:
            # Edge case: ratio == 0 или нет данных
            return create_tag(
                name="VOLUME_RATIO_UNKNOWN",
                category=TagCategory.VOLUME,
                status=TagStatus.YELLOW,
                value=volume_ratio,
                threshold="0.5-3.0",
                reasoning="No volume ratio data available",
                weight=0.3
            )
    
    def analyze_volume_acceleration(
        self,
        is_accelerating: bool,
        acceleration_factor: float,
        volume_h1: float = 0
    ) -> TokenTag:
        """
        Анализ ускорения объёма.
        
        GREEN: acceleration >= 2.0x (сильный импульс)
        GREEN: 1.5x <= acceleration < 2.0x (умеренный импульс)
        YELLOW: acceleration < 1.5x но > 1.0x (слабый рост)
        RED: acceleration <= 1.0x (нет роста)
        """
        if not is_accelerating or acceleration_factor < 1.5:
            if acceleration_factor <= 1.0:
                self.critical_flags.append("No volume acceleration - token not gaining momentum")
                return create_tag(
                    name="NO_ACCELERATION",
                    category=TagCategory.VOLUME,
                    status=TagStatus.RED,
                    value=acceleration_factor,
                    threshold=">= 1.5x",
                    reasoning=f"Factor {acceleration_factor:.2f}x <= 1.0x - no growth",
                    weight=0.9
                )
            else:
                return create_tag(
                    name="WEAK_ACCELERATION",
                    category=TagCategory.VOLUME,
                    status=TagStatus.YELLOW,
                    value=acceleration_factor,
                    threshold=">= 1.5x",
                    reasoning=f"Factor {acceleration_factor:.2f}x < 1.5x - weak growth",
                    weight=0.6
                )
        
        # Acceleration detected
        if acceleration_factor >= 2.0 and volume_h1 >= 10000:
            self.criteria_met.add("volume_acceleration_2x")
            self.criteria_met.add("volume_acceleration")  # Для STRONG tier
            return create_tag(
                name="STRONG_ACCELERATION",
                category=TagCategory.VOLUME,
                status=TagStatus.GREEN,
                value=acceleration_factor,
                threshold=">= 2.0x",
                reasoning=f"Factor {acceleration_factor:.2f}x - strong momentum",
                weight=1.0
            )
        else:
            self.criteria_met.add("volume_acceleration")  # Для STRONG tier
            return create_tag(
                name="MODERATE_ACCELERATION",
                category=TagCategory.VOLUME,
                status=TagStatus.GREEN,
                value=acceleration_factor,
                threshold=">= 1.5x",
                reasoning=f"Factor {acceleration_factor:.2f}x - moderate momentum",
                weight=0.8
            )
    
    # ========================================
    # SECURITY TAGS
    # ========================================
    
    def analyze_honeypot(self, is_honeypot: bool) -> TokenTag:
        """
        Проверка honeypot.
        
        GREEN: не honeypot
        RED: honeypot (критичный флаг)
        """
        if is_honeypot:
            self.critical_flags.append("HONEYPOT detected - SCAM")
            return create_tag(
                name="HONEYPOT",
                category=TagCategory.SECURITY,
                status=TagStatus.RED,
                value=True,
                threshold="False",
                reasoning="Token is a honeypot - cannot sell",
                weight=1.0
            )
        else:
            self.criteria_met.add("not_honeypot")
            return create_tag(
                name="NOT_HONEYPOT",
                category=TagCategory.SECURITY,
                status=TagStatus.GREEN,
                value=False,
                threshold="False",
                reasoning="Safe to trade - not a honeypot",
                weight=1.0
            )
    
    def analyze_contract_verification(self, is_open_source: bool) -> TokenTag:
        """
        Проверка верификации контракта.
        
        GREEN: верифицирован
        YELLOW: не верифицирован
        """
        if is_open_source:
            self.criteria_met.add("verified_contract")
            return create_tag(
                name="VERIFIED_CONTRACT",
                category=TagCategory.SECURITY,
                status=TagStatus.GREEN,
                value=True,
                threshold="True",
                reasoning="Contract is verified and open source",
                weight=0.8
            )
        else:
            return create_tag(
                name="UNVERIFIED_CONTRACT",
                category=TagCategory.SECURITY,
                status=TagStatus.YELLOW,
                value=False,
                threshold="True",
                reasoning="Contract not verified - higher risk",
                weight=0.6
            )
    
    def analyze_taxes(self, buy_tax: float, sell_tax: float) -> TokenTag:
        """
        Анализ налогов.
        
        GREEN: Buy <= 5%, Sell <= 10% (низкие)
        YELLOW: Buy <= 10%, Sell <= 15% (умеренные)
        YELLOW: Buy <= 20%, Sell <= 20% (высокие)
        RED: > 20% (экстремальные, возможен скам)
        """
        if buy_tax > 50 or sell_tax > 50:
            self.critical_flags.append(f"Extreme taxes - likely scam (Buy: {buy_tax}%, Sell: {sell_tax}%)")
            return create_tag(
                name="EXTREME_TAXES",
                category=TagCategory.SECURITY,
                status=TagStatus.RED,
                value={"buy": buy_tax, "sell": sell_tax},
                threshold="< 20%",
                reasoning=f"Buy {buy_tax}% / Sell {sell_tax}% - likely scam",
                weight=1.0
            )
        
        elif buy_tax <= 5 and sell_tax <= 10:
            self.criteria_met.add("low_taxes")
            return create_tag(
                name="LOW_TAXES",
                category=TagCategory.SECURITY,
                status=TagStatus.GREEN,
                value={"buy": buy_tax, "sell": sell_tax},
                threshold="Buy <= 5%, Sell <= 10%",
                reasoning=f"Buy {buy_tax}% / Sell {sell_tax}% - reasonable",
                weight=0.8
            )
        
        elif buy_tax <= 10 and sell_tax <= 15:
            self.criteria_met.add("moderate_taxes")
            return create_tag(
                name="MODERATE_TAXES",
                category=TagCategory.SECURITY,
                status=TagStatus.YELLOW,
                value={"buy": buy_tax, "sell": sell_tax},
                threshold="Buy <= 10%, Sell <= 15%",
                reasoning=f"Buy {buy_tax}% / Sell {sell_tax}% - moderate",
                weight=0.6
            )
        
        else:
            return create_tag(
                name="HIGH_TAXES",
                category=TagCategory.SECURITY,
                status=TagStatus.YELLOW,
                value={"buy": buy_tax, "sell": sell_tax},
                threshold="< 20%",
                reasoning=f"Buy {buy_tax}% / Sell {sell_tax}% - high but acceptable",
                weight=0.4
            )
    
    # ========================================
    # ONCHAIN TAGS
    # ========================================
    
    def analyze_lp_lock(self, onchain: Optional[OnChainAnalysisResult]) -> TokenTag:
        """
        Анализ блокировки ликвидности.
        
        GREEN: >= 90% locked (безопасно)
        YELLOW: 50-90% locked (частичная защита)
        YELLOW: 20-50% locked (минимальная защита)
        RED: < 20% locked (критичный риск rug pull)
        """
        if not onchain or not onchain.lp_analysis:
            return create_tag(
                name="LP_LOCK_UNKNOWN",
                category=TagCategory.LIQUIDITY,
                status=TagStatus.YELLOW,
                value=None,
                threshold=">= 50%",
                reasoning="No LP lock data available",
                weight=0.5
            )
        
        lp = onchain.lp_analysis
        locked_pct = lp.locked_percentage
        
        if lp.risk_level == OnChainRiskLevel.CRITICAL or locked_pct < 20:
            self.critical_flags.append(f"LP NOT locked ({locked_pct:.1f}%) - HIGH RUG PULL RISK")
            return create_tag(
                name="LP_NOT_LOCKED",
                category=TagCategory.LIQUIDITY,
                status=TagStatus.RED,
                value=locked_pct,
                threshold=">= 20%",
                reasoning=f"Only {locked_pct:.1f}% locked - extreme risk",
                weight=1.0
            )
        
        elif locked_pct >= 90:
            self.criteria_met.add("lp_locked_90plus")
            self.criteria_met.add("lp_locked_50plus")  # Для STRONG tier
            return create_tag(
                name="LP_LOCKED_90%+",
                category=TagCategory.LIQUIDITY,
                status=TagStatus.GREEN,
                value=locked_pct,
                threshold=">= 90%",
                reasoning=f"{locked_pct:.1f}% locked - safely secured",
                weight=1.0
            )
        
        elif locked_pct >= 50:
            self.criteria_met.add("lp_locked_50plus")
            return create_tag(
                name="LP_LOCKED_50%+",
                category=TagCategory.LIQUIDITY,
                status=TagStatus.YELLOW,
                value=locked_pct,
                threshold=">= 50%",
                reasoning=f"{locked_pct:.1f}% locked - partial protection",
                weight=0.7
            )
        
        else:
            return create_tag(
                name="LP_PARTIALLY_LOCKED",
                category=TagCategory.LIQUIDITY,
                status=TagStatus.YELLOW,
                value=locked_pct,
                threshold=">= 50%",
                reasoning=f"{locked_pct:.1f}% locked - minimal protection",
                weight=0.5
            )
    
    def analyze_holder_concentration(self, onchain: Optional[OnChainAnalysisResult]) -> TokenTag:
        """
        Анализ концентрации держателей.
        
        GREEN: Top-10 < 20% (здоровое распределение)
        YELLOW: Top-10 20-40% (умеренная концентрация)
        YELLOW: Top-10 40-60% (высокая концентрация)
        RED: Top-10 > 60% (критичная концентрация)
        """
        if not onchain or not onchain.holder_analysis:
            return create_tag(
                name="CONCENTRATION_UNKNOWN",
                category=TagCategory.ONCHAIN,
                status=TagStatus.YELLOW,
                value=None,
                threshold="< 40%",
                reasoning="No holder data available",
                weight=0.5
            )
        
        holder = onchain.holder_analysis
        concentration = holder.top_10_concentration
        
        if concentration > 60:
            self.critical_flags.append(f"Critical concentration ({concentration:.1f}% in top-10) - extreme dump risk")
            return create_tag(
                name="CRITICAL_CONCENTRATION",
                category=TagCategory.ONCHAIN,
                status=TagStatus.RED,
                value=concentration,
                threshold="< 60%",
                reasoning=f"{concentration:.1f}% in top-10 - extreme dump risk",
                weight=1.0
            )
        
        elif concentration < 20:
            self.criteria_met.add("low_holder_concentration")
            return create_tag(
                name="LOW_CONCENTRATION",
                category=TagCategory.ONCHAIN,
                status=TagStatus.GREEN,
                value=concentration,
                threshold="< 20%",
                reasoning=f"{concentration:.1f}% in top-10 - healthy distribution",
                weight=0.9
            )
        
        elif concentration < 40:
            self.criteria_met.add("moderate_concentration")
            return create_tag(
                name="MODERATE_CONCENTRATION",
                category=TagCategory.ONCHAIN,
                status=TagStatus.YELLOW,
                value=concentration,
                threshold="< 40%",
                reasoning=f"{concentration:.1f}% in top-10 - moderate risk",
                weight=0.6
            )
        
        else:
            return create_tag(
                name="HIGH_CONCENTRATION",
                category=TagCategory.ONCHAIN,
                status=TagStatus.YELLOW,
                value=concentration,
                threshold="< 40%",
                reasoning=f"{concentration:.1f}% in top-10 - high dump risk",
                weight=0.4
            )
    
    # ========================================
    # TIER DETERMINATION
    # ========================================
    
    def determine_tier(self) -> TokenTier:
        """
        Определить tier на основе собранных критериев.
        
        Логика:
        1. AVOID: хотя бы один критичный red flag
        2. PREMIUM: все required критерии выполнены
        3. STRONG: минимум 5 из 7 критериев
        4. SPECULATIVE: всё остальное
        """
        # Проверка критичных флагов
        if self.critical_flags:
            return TokenTier.AVOID
        
        # Проверка PREMIUM
        if TierCriteria.PREMIUM_REQUIRED.issubset(self.criteria_met):
            return TokenTier.PREMIUM
        
        # Проверка STRONG
        strong_count = len(TierCriteria.STRONG_CRITERIA & self.criteria_met)
        if strong_count >= TierCriteria.STRONG_MIN_COUNT:
            return TokenTier.STRONG
        
        # По умолчанию SPECULATIVE
        return TokenTier.SPECULATIVE
    
    def calculate_confidence(self, data_completeness: float) -> float:
        """
        Рассчитать уверенность в определении tier'а.
        
        Зависит от:
        - Полноты данных
        - Количества критичных флагов (снижает confidence)
        - Согласованности сигналов
        """
        # Базовая confidence = полнота данных
        confidence = data_completeness
        
        # Снижаем за критичные флаги (но AVOID всегда уверенный)
        if self.critical_flags and len(self.tags) > 0:
            red_count = len([t for t in self.tags if t.status == TagStatus.RED])
            penalty = (red_count / len(self.tags)) * 0.2
            confidence = max(0.5, confidence - penalty)
        
        # Повышаем за много зелёных тегов
        if len(self.tags) > 0:
            green_count = len([t for t in self.tags if t.status == TagStatus.GREEN])
            bonus = (green_count / len(self.tags)) * 0.1
            confidence = min(1.0, confidence + bonus)
        
        return confidence
    
    # ========================================
    # MAIN ANALYSIS METHOD
    # ========================================
    
    def analyze(
        self,
        # Volume data
        volume_ratio: float = 0,
        ratio_healthy: bool = False,
        ratio_overheated: bool = False,
        ratio_dead: bool = False,
        is_accelerating: bool = False,
        acceleration_factor: float = 0,
        volume_h1: float = 0,
        
        # Security data
        is_honeypot: bool = False,
        is_open_source: bool = False,
        buy_tax: float = 5.0,
        sell_tax: float = 5.0,
        
        # OnChain data
        onchain_analysis: Optional[OnChainAnalysisResult] = None,
        
        # Metadata
        data_completeness: float = 0.0,
        token_address: Optional[str] = None,
        token_symbol: Optional[str] = None,
        chain: Optional[str] = None
        
    ) -> TierAnalysisResult:
        """
        Главный метод анализа - определяет tier и создаёт все теги.
        
        Returns:
            TierAnalysisResult с полной информацией
        """
        # Сбросить состояние
        self.tags = []
        self.critical_flags = []
        self.criteria_met = set()
        
        # Создать теги для всех метрик
        
        # Volume
        self.tags.append(self.analyze_volume_ratio(volume_ratio, ratio_healthy, ratio_overheated, ratio_dead))
        self.tags.append(self.analyze_volume_acceleration(is_accelerating, acceleration_factor, volume_h1))
        
        # Security
        self.tags.append(self.analyze_honeypot(is_honeypot))
        self.tags.append(self.analyze_contract_verification(is_open_source))
        self.tags.append(self.analyze_taxes(buy_tax, sell_tax))
        
        # OnChain
        self.tags.append(self.analyze_lp_lock(onchain_analysis))
        self.tags.append(self.analyze_holder_concentration(onchain_analysis))
        
        # Определить tier
        tier = self.determine_tier()
        
        # Рассчитать confidence
        confidence = self.calculate_confidence(data_completeness)
        
        # Создать результат
        return TierAnalysisResult(
            tier=tier,
            tags=self.tags,
            critical_flags=self.critical_flags,
            confidence=confidence,
            data_completeness=data_completeness,
            token_address=token_address,
            token_symbol=token_symbol,
            chain=chain
        )


# === TESTING ===

def test_tier_scoring():
    """Тест определения tier'ов"""
    from .pump_models import OnChainAnalysisResult, LiquidityAnalysisResult, HolderAnalysisResult
    
    print("=" * 70)
    print("TIER SCORING MATRIX - TEST")
    print("=" * 70)
    
    matrix = TierScoringMatrix()
    
    # Test 1: PREMIUM token
    print("\n" + "─" * 70)
    print("TEST 1: PREMIUM Token")
    print("─" * 70)
    
    perfect_lp = LiquidityAnalysisResult(
        locked_percentage=95.0,
        risk_level=OnChainRiskLevel.SAFE,
        details=["LP locked in Unicrypt"]
    )
    
    perfect_holders = HolderAnalysisResult(
        top_10_concentration=15.0,
        risk_level=OnChainRiskLevel.LOW,
        details=["Healthy distribution"]
    )
    
    perfect_onchain = OnChainAnalysisResult(
        lp_analysis=perfect_lp,
        holder_analysis=perfect_holders,
        overall_risk=OnChainRiskLevel.SAFE,
        lp_safety_score=10,
        holder_safety_score=5,
        onchain_bonus=15
    )
    
    result1 = matrix.analyze(
        volume_ratio=2.0,
        ratio_healthy=True,
        is_accelerating=True,
        acceleration_factor=2.5,
        volume_h1=50000,
        is_honeypot=False,
        is_open_source=True,
        buy_tax=2.0,
        sell_tax=5.0,
        onchain_analysis=perfect_onchain,
        data_completeness=0.95,
        token_symbol="PREMIUM",
        token_address="0x1234...5678"
    )
    
    print(result1.get_detailed_report())
    assert result1.tier == TokenTier.PREMIUM, "Should be PREMIUM"
    print("\n✅ Test 1 PASSED")
    
    # Test 2: AVOID token (dead)
    print("\n" + "─" * 70)
    print("TEST 2: AVOID Token (Dead)")
    print("─" * 70)
    
    matrix2 = TierScoringMatrix()
    result2 = matrix2.analyze(
        volume_ratio=0.2,
        ratio_dead=True,
        is_accelerating=True,
        acceleration_factor=2.0,
        is_honeypot=False,
        data_completeness=0.8,
        token_symbol="DEAD",
        token_address="0xdead...beef"
    )
    
    print(result2.get_detailed_report())
    assert result2.tier == TokenTier.AVOID, "Should be AVOID"
    print("\n✅ Test 2 PASSED")
    
    print("\n" + "=" * 70)
    print("✅ ALL TIER SCORING TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    test_tier_scoring()
