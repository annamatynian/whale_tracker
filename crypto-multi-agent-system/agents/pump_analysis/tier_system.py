"""
Tier + Tags Scoring System - замена балльной системы
Обеспечивает полную прозрачность всех метрик без искажения через баллы

Author: Tier System v1.0
Date: 2025-01-20
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class TokenTier(str, Enum):
    """
    Иерархия качества токенов.
    Tier определяется по наличию критериев, а не по сумме баллов.
    """
    PREMIUM = "PREMIUM"           # 🏆 Все зелёные флаги
    STRONG = "STRONG"             # 💪 Большинство зелёных, мало жёлтых
    SPECULATIVE = "SPECULATIVE"   # ⚡ Есть потенциал, но высокие риски
    AVOID = "AVOID"               # 🚫 Критичные red flags


class TagStatus(str, Enum):
    """Статус конкретной метрики"""
    GREEN = "✅"      # Позитивный сигнал
    YELLOW = "⚠️"    # Предупреждение
    RED = "❌"       # Критический риск


class TagCategory(str, Enum):
    """Категория тега для группировки"""
    LIQUIDITY = "LIQUIDITY"         # LP lock, liquidity amount
    VOLUME = "VOLUME"               # Volume metrics, acceleration
    SECURITY = "SECURITY"           # Honeypot, taxes, contract
    ONCHAIN = "ONCHAIN"            # Holder concentration, deployer
    NARRATIVE = "NARRATIVE"        # Market narrative, sentiment
    PRICE = "PRICE"                # Price action, stability


class TokenTag(BaseModel):
    """
    Один тег - одна метрика с полным контекстом.
    Вся информация для принятия решения.
    """
    name: str = Field(..., description="Имя тега, например LP_LOCKED_90%")
    category: TagCategory = Field(..., description="Категория для группировки")
    status: TagStatus = Field(..., description="Статус: GREEN/YELLOW/RED")
    value: Any = Field(..., description="Фактическое значение метрики")
    threshold: str = Field(..., description="Порог для понимания статуса")
    reasoning: str = Field(..., description="Человекочитаемое объяснение")
    weight: float = Field(default=1.0, ge=0, le=1.0, description="Важность (0-1)")
    
    def __str__(self) -> str:
        """Компактное строковое представление"""
        return f"{self.status.value} {self.name:30s} ({self.reasoning})"
    
    def to_dict(self) -> Dict:
        """Для JSON сериализации"""
        return {
            "name": self.name,
            "category": self.category.value,
            "status": self.status.value,
            "value": self.value,
            "threshold": self.threshold,
            "reasoning": self.reasoning,
            "weight": self.weight
        }


class TierAnalysisResult(BaseModel):
    """
    Результат tier-анализа токена.
    Содержит все данные для принятия решения.
    """
    tier: TokenTier = Field(..., description="Итоговый tier")
    tags: List[TokenTag] = Field(default_factory=list, description="Все теги с деталями")
    critical_flags: List[str] = Field(default_factory=list, description="Критичные причины downgrade")
    confidence: float = Field(default=0.0, ge=0, le=1.0, description="Уверенность в tier (0-1)")
    data_completeness: float = Field(default=0.0, ge=0, le=1.0, description="Полнота данных (0-1)")
    
    # Metadata
    token_address: Optional[str] = None
    token_symbol: Optional[str] = None
    chain: Optional[str] = None
    
    def get_tags_by_category(self, category: TagCategory) -> List[TokenTag]:
        """Получить теги по категории"""
        return [tag for tag in self.tags if tag.category == category]
    
    def get_tags_by_status(self, status: TagStatus) -> List[TokenTag]:
        """Получить теги по статусу"""
        return [tag for tag in self.tags if tag.status == status]
    
    def count_by_status(self) -> Dict[str, int]:
        """Подсчёт тегов по статусам"""
        return {
            "green": len([t for t in self.tags if t.status == TagStatus.GREEN]),
            "yellow": len([t for t in self.tags if t.status == TagStatus.YELLOW]),
            "red": len([t for t in self.tags if t.status == TagStatus.RED])
        }
    
    def get_summary(self) -> Dict:
        """Компактное представление для алертов"""
        counts = self.count_by_status()
        
        return {
            "tier": self.tier.value,
            "confidence": round(self.confidence, 2),
            "green_count": counts["green"],
            "yellow_count": counts["yellow"],
            "red_count": counts["red"],
            "critical_flags": self.critical_flags,
            "data_completeness": round(self.data_completeness, 2)
        }
    
    def get_detailed_report(self) -> str:
        """
        Детальный текстовый отчёт для Telegram/консоли.
        Группирует теги по категориям.
        """
        lines = []
        
        # Header
        tier_emoji = {
            TokenTier.PREMIUM: "🏆",
            TokenTier.STRONG: "💪",
            TokenTier.SPECULATIVE: "⚡",
            TokenTier.AVOID: "🚫"
        }
        
        lines.append("━" * 60)
        lines.append(f"{tier_emoji[self.tier]} TIER: {self.tier.value}")
        lines.append("━" * 60)
        
        if self.token_symbol:
            lines.append(f"Token: {self.token_symbol} ({self.token_address[:10]}...)")
            lines.append("")
        
        # Группировка по категориям
        for category in TagCategory:
            category_tags = self.get_tags_by_category(category)
            if category_tags:
                lines.append(f"\n📊 {category.value}:")
                lines.append("─" * 60)
                for tag in category_tags:
                    lines.append(f"  {tag}")
        
        # Critical flags
        if self.critical_flags:
            lines.append("\n⚠️ CRITICAL FLAGS:")
            lines.append("─" * 60)
            for flag in self.critical_flags:
                lines.append(f"  ❌ {flag}")
        
        # Summary
        counts = self.count_by_status()
        lines.append("\n📈 SUMMARY:")
        lines.append("─" * 60)
        lines.append(f"  Tags: {counts['green']}✅ {counts['yellow']}⚠️ {counts['red']}❌")
        lines.append(f"  Confidence: {self.confidence:.0%}")
        lines.append(f"  Data completeness: {self.data_completeness:.0%}")
        
        # Action
        lines.append("\n🎯 RECOMMENDED ACTION:")
        lines.append("─" * 60)
        if self.tier == TokenTier.PREMIUM:
            lines.append("  🚀 IMMEDIATE WATCH - High priority monitoring")
        elif self.tier == TokenTier.STRONG:
            lines.append("  👀 MONITOR - Medium priority, verify details")
        elif self.tier == TokenTier.SPECULATIVE:
            lines.append("  ⚠️ CAUTION - High risk, experts only")
        else:
            lines.append("  🚫 EXCLUDE - Do not trade")
        
        lines.append("━" * 60)
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """Для JSON сериализации"""
        return {
            "tier": self.tier.value,
            "tags": [tag.to_dict() for tag in self.tags],
            "critical_flags": self.critical_flags,
            "confidence": self.confidence,
            "data_completeness": self.data_completeness,
            "summary": self.get_summary(),
            "token_address": self.token_address,
            "token_symbol": self.token_symbol,
            "chain": self.chain
        }


# === TIER CRITERIA DEFINITIONS ===

class TierCriteria:
    """
    Определения критериев для каждого tier.
    Используются для автоматического определения tier'а.
    """
    
    # PREMIUM: ВСЕ критерии должны быть выполнены
    PREMIUM_REQUIRED = {
        "lp_locked_90plus",
        "healthy_volume_ratio",
        "volume_acceleration_2x",
        "not_honeypot",
        "low_holder_concentration",
        "verified_contract",
        "low_taxes"
    }
    
    # STRONG: минимум 5 из 7 критериев
    STRONG_CRITERIA = {
        "lp_locked_50plus",
        "healthy_volume_ratio",
        "volume_acceleration",
        "not_honeypot",
        "moderate_concentration",
        "verified_contract",
        "moderate_taxes"
    }
    STRONG_MIN_COUNT = 5
    
    # AVOID: хотя бы один критичный red flag
    AVOID_CRITICAL_FLAGS = {
        "dead_token",
        "honeypot",
        "lp_not_locked",
        "critical_concentration",
        "no_acceleration",
        "extreme_taxes"
    }


# === HELPER FUNCTIONS ===

def create_tag(
    name: str,
    category: TagCategory,
    status: TagStatus,
    value: Any,
    threshold: str,
    reasoning: str,
    weight: float = 1.0
) -> TokenTag:
    """Удобная функция для создания тегов"""
    return TokenTag(
        name=name,
        category=category,
        status=status,
        value=value,
        threshold=threshold,
        reasoning=reasoning,
        weight=weight
    )


# === TESTING ===

def test_tier_models():
    """Тест базовых моделей"""
    print("=" * 70)
    print("TIER SYSTEM MODELS - TEST")
    print("=" * 70)
    
    # Создаём пример тегов
    tags = [
        create_tag(
            "LP_LOCKED_95%",
            TagCategory.LIQUIDITY,
            TagStatus.GREEN,
            95.0,
            "> 90%",
            "Liquidity safely locked",
            weight=1.0
        ),
        create_tag(
            "HEALTHY_RATIO",
            TagCategory.VOLUME,
            TagStatus.GREEN,
            2.0,
            "0.5-3.0",
            "Volume ratio in golden range",
            weight=0.8
        ),
        create_tag(
            "HIGH_CONCENTRATION",
            TagCategory.ONCHAIN,
            TagStatus.YELLOW,
            45.0,
            "< 40%",
            "Top-10 hold 45% - moderate risk",
            weight=0.9
        )
    ]
    
    # Создаём результат анализа
    result = TierAnalysisResult(
        tier=TokenTier.STRONG,
        tags=tags,
        critical_flags=[],
        confidence=0.85,
        data_completeness=0.90,
        token_symbol="TEST",
        token_address="0x1234...5678"
    )
    
    # Тестируем методы
    print("\n1. Summary:")
    print(result.get_summary())
    
    print("\n2. Status counts:")
    print(result.count_by_status())
    
    print("\n3. Tags by category (VOLUME):")
    volume_tags = result.get_tags_by_category(TagCategory.VOLUME)
    for tag in volume_tags:
        print(f"   {tag}")
    
    print("\n4. Detailed report:")
    print(result.get_detailed_report())
    
    print("\n5. JSON export:")
    import json
    print(json.dumps(result.to_dict(), indent=2))
    
    print("\n" + "=" * 70)
    print("✅ All model tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    test_tier_models()
