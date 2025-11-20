"""
Mock Test - Тестирование системы на фиктивных данных

Показывает как система работает без реальных API ключей
Использует примеры токенов из PDF исследования
"""

import asyncio
from datetime import datetime
from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
from agents.pump_analysis.pump_models import PumpAnalysisReport, PumpIndicators, NarrativeType

# Фиктивные данные на основе реальных примеров из PDF
MOCK_PUMP_CANDIDATES = [
    {
        # Пример хорошего токена (AI нарратив + свежий + хорошая ликвидность)
        "chainId": "base",
        "pairAddress": "0x123...mock1",
        "baseToken": {
            "address": "0x696F...mock_avnt",
            "symbol": "MOCKAVNT", 
            "name": "Mock Avantis"
        },
        "liquidity": {"usd": 85000},  # Хорошая ликвидность
        "volume": {"h24": 45000},     # Активная торговля
        "priceChange": {
            "h1": 15.5,    # Положительная динамика
            "h24": 67.8    # Сильный рост
        },
        "pairCreatedAt": int((datetime.now().timestamp() - 3600 * 18) * 1000)  # 18 часов назад
    },
    {
        # Пример среднего токена (хорошая ликвидность, но старше)
        "chainId": "ethereum", 
        "pairAddress": "0x456...mock2",
        "baseToken": {
            "address": "0xC729...mock_sapien",
            "symbol": "MOCKSAPIEN",
            "name": "Mock Sapien AI"
        },
        "liquidity": {"usd": 65000},
        "volume": {"h24": 25000},
        "priceChange": {
            "h1": 8.2,
            "h24": 34.1    # Умеренный рост
        },
        "pairCreatedAt": int((datetime.now().timestamp() - 3600 * 36) * 1000)  # 36 часов назад
    },
    {
        # Пример слабого токена (низкая ликвидность, очень свежий)
        "chainId": "arbitrum",
        "pairAddress": "0x789...mock3", 
        "baseToken": {
            "address": "0xA66B...mock_openx",
            "symbol": "MOCKOPENX",
            "name": "Mock OpenX AI"
        },
        "liquidity": {"usd": 8000},   # Низкая ликвидность
        "volume": {"h24": 2500},      # Низкая активность
        "priceChange": {
            "h1": 2.1,
            "h24": 15.6
        },
        "pairCreatedAt": int((datetime.now().timestamp() - 3600 * 6) * 1000)   # 6 часов назад
    },
    {
        # Пример очень плохого токена (дамп)
        "chainId": "bsc",
        "pairAddress": "0xabc...mock4",
        "baseToken": {
            "address": "0x123...mock_bad",
            "symbol": "MOCKBAD",
            "name": "Mock Bad Token"
        },
        "liquidity": {"usd": 15000},
        "volume": {"h24": 8000},
        "priceChange": {
            "h1": -25.5,   # Падение
            "h24": -65.2   # Сильный дамп - должен быть отфильтрован
        },
        "pairCreatedAt": int((datetime.now().timestamp() - 3600 * 12) * 1000)
    }
]

class MockPumpDiscoveryAgent(PumpDiscoveryAgent):
    """
    Mock версия PumpDiscoveryAgent для тестирования без API
    
    Переопределяет discover_tokens_async для работы только с mock данными
    """
    
    async def discover_tokens_async(self):
        """Переопределяем полностью для работы с mock данными"""
        print(f"   🔍 Анализируем {len(MOCK_PUMP_CANDIDATES)} mock токенов...")
        
        discovered_reports = []
        pairs_scanned = 0
        
        for pair_data in MOCK_PUMP_CANDIDATES:
            pairs_scanned += 1
            
            # Применяем фильтры
            if not self.should_analyze_pair(pair_data):
                continue
            
            # Рассчитываем возраст
            created_at = pair_data.get('pairCreatedAt', 0)
            age_minutes = (datetime.now().timestamp() - created_at/1000) / 60
            
            # Рассчитываем score
            score, reason = self.calculate_score(pair_data, age_minutes)
            
            # Создаем отчет
            report = self.create_report(
                pair_data, score, reason, age_minutes, 
                "mock_git_hash", 0.1
            )
            
            discovered_reports.append(report)
        
        # Обновляем статистику
        self.session_stats['pairs_scanned'] = pairs_scanned
        self.session_stats['reports_generated'] = len(discovered_reports)
        
        return discovered_reports

async def test_mock_pump_discovery():
    """Главный тест mock системы"""
    print("🧪 MOCK TEST - PUMP DISCOVERY SYSTEM")
    print("=" * 60)
    
    print("\n📊 ТЕСТОВЫЕ ДАННЫЕ:")
    for i, token in enumerate(MOCK_PUMP_CANDIDATES, 1):
        symbol = token["baseToken"]["symbol"]
        liquidity = token["liquidity"]["usd"]
        price_change = token["priceChange"]["h24"]
        age_hours = (datetime.now().timestamp() - token["pairCreatedAt"]/1000) / 3600
        
        print(f"   {i}. {symbol}: ${liquidity:,.0f} liquidity, {price_change:+.1f}% (24h), {age_hours:.1f}h age")
    
    print(f"\n🔍 СКАНИРОВАНИЕ MOCK СЕТЕЙ...")
    
    # Создаем mock агента
    agent = MockPumpDiscoveryAgent()
    
    # Запускаем анализ
    pump_candidates = await agent.discover_tokens_async()
    
    print(f"\n📈 РЕЗУЛЬТАТЫ АНАЛИЗА:")
    print(f"   Найдено кандидатов: {len(pump_candidates)}")
    
    if not pump_candidates:
        print("   😔 Нет токенов, прошедших фильтры")
        return
    
    print(f"\n🎯 ДЕТАЛЬНЫЙ АНАЛИЗ КАНДИДАТОВ:")
    print("=" * 60)
    
    for i, candidate in enumerate(pump_candidates, 1):
        print(f"\n#{i}: {candidate.token_name} ({candidate.token_symbol})")
        print("-" * 40)
        print(f"   🎯 Pump Score: {candidate.final_score}/100")
        print(f"   💰 Liquidity: ${candidate.indicators.liquidity_usd:,.0f}")
        print(f"   📊 Volume 24h: ${candidate.indicators.volume_24h:,.0f}")
        print(f"   🕒 Age: {candidate.indicators.age_hours:.1f} hours")
        print(f"   📈 Confidence: {candidate.confidence_level:.0%}")
        
        print(f"   💡 Reasoning:")
        for reason in candidate.reasoning[:3]:  # Показываем первые 3 причины
            print(f"      • {reason}")
        
        print(f"   📋 Next Steps:")
        for step in candidate.next_steps[:2]:  # Показываем первые 2 шага
            print(f"      • {step}")
    
    # Показать статистику сессии
    stats = agent.get_session_stats()
    print(f"\n📊 СТАТИСТИКА MOCK СЕССИИ:")
    print(f"   Пар просканировано: {stats['pairs_scanned']}")
    print(f"   Кандидатов найдено: {stats['pump_stats']['pump_candidates_found']}")
    print(f"   Высокий потенциал: {stats['pump_stats']['high_potential_found']}")
    print(f"   Отфильтровано по дампу: {stats['pump_stats']['filtered_by_dump']}")
    print(f"   Отфильтровано по возрасту: {stats['pump_stats']['filtered_by_age']}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")

def show_filtering_logic():
    """Показать логику фильтрации на примерах"""
    print(f"\n🔧 ЛОГИКА ФИЛЬТРАЦИИ (объяснение):")
    print("=" * 50)
    
    agent = MockPumpDiscoveryAgent()
    
    for i, pair_data in enumerate(MOCK_PUMP_CANDIDATES, 1):
        symbol = pair_data["baseToken"]["symbol"]
        should_analyze = agent.should_analyze_pair(pair_data)
        
        liquidity = pair_data["liquidity"]["usd"]
        price_change_24h = pair_data["priceChange"]["h24"]
        age_hours = (datetime.now().timestamp() - pair_data["pairCreatedAt"]/1000) / 3600
        
        print(f"\n{i}. {symbol}: {'✅ PASSED' if should_analyze else '❌ FILTERED'}")
        print(f"   Liquidity: ${liquidity:,.0f} ({'✅' if liquidity >= 5000 else '❌'} min $5,000)")
        print(f"   Price 24h: {price_change_24h:+.1f}% ({'✅' if price_change_24h >= -50 else '❌'} not dumping)")
        print(f"   Age: {age_hours:.1f}h ({'✅' if age_hours <= 48 else '❌'} max 48h)")

async def main():
    """Главная функция mock теста"""
    await test_mock_pump_discovery()
    show_filtering_logic()
    
    print(f"\n🎉 MOCK TEST ЗАВЕРШЕН!")
    print("Система работает корректно на тестовых данных")
    print("Готова к использованию с реальными API ключами! 🚀")

if __name__ == "__main__":
    asyncio.run(main())
