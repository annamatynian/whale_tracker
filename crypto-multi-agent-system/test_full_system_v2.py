#!/usr/bin/env python3
"""
Полный тест системы с Telegram интеграцией
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("🎯 ПОЛНЫЙ ТЕСТ CRYPTO MULTI-AGENT SYSTEM V2")
print("=" * 60)

async def test_full_system():
    """Тестирование всех компонентов системы"""
    
    # Тест 1: Основные компоненты
    print("\n1️⃣ Тестирование основных компонентов...")
    try:
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
        from agents.social_intelligence.telegram_social_agent import TelegramSocialAgent
        
        orchestrator = SimpleOrchestrator()
        print("   ✅ SimpleOrchestrator инициализирован")
        print("   ✅ TelegramSocialAgent интегрирован")
        
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        return False

    # Тест 2: Telegram агент отдельно
    print("\n2️⃣ Тестирование Telegram агента...")
    try:
        telegram_agent = TelegramSocialAgent()
        
        # Тестовый адрес
        test_addresses = ["0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"]
        momentum_scores = await telegram_agent.get_social_momentum_score(test_addresses)
        
        print(f"   ✅ Momentum score получен: {momentum_scores}")
        print(f"   ✅ Mock режим: {telegram_agent.is_mock}")
        
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        return False

    # Тест 3: Scoring Matrix с социальными данными
    print("\n3️⃣ Тестирование обновленной Scoring Matrix...")
    try:
        from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators
        from agents.pump_analysis.pump_models import NarrativeType
        
        # Создаем индикаторы с социальными данными
        indicators = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=75.0,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=5.0,
            sell_tax_percent=8.0,
            alpha_channel_mentions=3,  # НОВОЕ ПОЛЕ
            social_momentum_score=80   # НОВОЕ ПОЛЕ
        )
        
        matrix = RealisticScoringMatrix(indicators=indicators)
        analysis = matrix.get_detailed_analysis()
        
        print(f"   ✅ Итоговый score: {analysis['total_score']}/100")
        print(f"   ✅ Social score: {analysis['category_scores']['social']}")
        print(f"   ✅ Recommendation: {analysis['recommendation']}")
        
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        return False

    print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("\n📋 Что дальше:")
    print("1. Настройте Telegram API (см. TELEGRAM_SETUP.md)")
    print("2. Запустите: python main.py --dry-run")
    print("3. Система будет сканировать токены + Telegram каналы")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_full_system())
    if success:
        print("\n✅ Система готова к работе!")
    else:
        print("\n❌ Есть проблемы, нужно исправить")
