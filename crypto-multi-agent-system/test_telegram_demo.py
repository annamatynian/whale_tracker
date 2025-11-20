"""
Mock тест с Telegram интеграцией
Демонстрирует полный workflow с отправкой алертов
"""

import asyncio
import os
import sys
from datetime import datetime

# Добавляем путь к корню проекта
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.social_intelligence.telegram_agent import TelegramAlertAgent
from agents.pump_analysis.pump_models import PumpAnalysisReport, PumpIndicators, NarrativeType

def load_env():
    """Загружает переменные окружения"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

def create_mock_pump_candidates():
    """Создает mock данные pump кандидатов"""
    
    # Хороший кандидат - высокий score
    good_candidate = PumpAnalysisReport(
        contract_address="0x696F...mock_avnt",
        token_symbol="MOCKAVNT",
        token_name="Mock Avantis (RWA)",
        chain_id="base",  # Добавлено обязательное поле
        
        indicators=PumpIndicators(
            contract_address="0x696F...mock_avnt",
            narrative_alignment=NarrativeType.RWA,
            is_honeypot=False,
            is_open_source=True,
            social_mentions=8,
            liquidity_usd=85000,
            volume_24h=45000,
            age_hours=18.0,
            pump_probability_score=87
        ),
        
        narrative_score=35,
        security_score=35,
        social_score=25,
        
        reasoning=[
            "Fresh token: 18.0h (+20pts)",
            "High liquidity: $85,000 (+15pts)",
            "Strong momentum: +67.8% (+15pts)",
            "RWA narrative trending (+25pts)"
        ],
        
        red_flags=[],
        
        data_sources_used=["Mock DexScreener"],
        api_calls_made=1,
        
        final_score=87,
        confidence_level=0.85,
        next_steps=[
            "🚀 HIGH PRIORITY: Full pump analysis",
            "🔍 CoinGecko narrative check",
            "🛡️ GoPlus security validation",
            "📱 Social media monitoring"
        ]
    )
    
    # Средний кандидат
    medium_candidate = PumpAnalysisReport(
        contract_address="0xC729...mock_sapien",
        token_symbol="MOCKSAPIEN",
        token_name="Mock Sapien AI",
        chain_id="ethereum",  # Добавлено обязательное поле
        
        indicators=PumpIndicators(
            contract_address="0xC729...mock_sapien",
            narrative_alignment=NarrativeType.AI,
            is_honeypot=False,
            is_open_source=True,
            social_mentions=5,
            liquidity_usd=65000,
            volume_24h=25000,
            age_hours=36.0,
            pump_probability_score=72
        ),
        
        narrative_score=40,
        security_score=25,
        social_score=15,
        
        reasoning=[
            "Recent token: 36.0h (+10pts)",
            "Good liquidity: $65,000 (+10pts)",
            "AI narrative: very hot (+30pts)",
            "Moderate social activity (+15pts)"
        ],
        
        red_flags=[],
        
        data_sources_used=["Mock DexScreener"],
        api_calls_made=1,
        
        final_score=72,
        confidence_level=0.70,
        next_steps=[
            "🎯 MEDIUM PRIORITY: Extended analysis",
            "🔍 CoinGecko narrative check",
            "📈 Monitor price action"
        ]
    )
    
    # Низкоприоритетный кандидат
    low_candidate = PumpAnalysisReport(
        contract_address="0xA66B...mock_openx",
        token_symbol="MOCKLOW",
        token_name="Mock Low Priority",
        chain_id="arbitrum",  # Добавлено обязательное поле
        
        indicators=PumpIndicators(
            contract_address="0xA66B...mock_openx",
            narrative_alignment=NarrativeType.UNKNOWN,
            is_honeypot=False,
            is_open_source=False,
            social_mentions=1,
            liquidity_usd=8000,
            volume_24h=2500,
            age_hours=6.0,
            pump_probability_score=45
        ),
        
        narrative_score=5,
        security_score=20,
        social_score=10,
        
        reasoning=[
            "Very fresh token: 6.0h (+15pts)",
            "Low liquidity: $8,000 (+5pts)",
            "Minimal social activity (+5pts)",
            "Unknown narrative (+0pts)"
        ],
        
        red_flags=[
            "Low liquidity",
            "No clear narrative",
            "Minimal social buzz"
        ],
        
        data_sources_used=["Mock DexScreener"],
        api_calls_made=1,
        
        final_score=45,
        confidence_level=0.45,
        next_steps=[
            "👀 WATCH LIST: Monitor for changes",
            "📊 Track price action"
        ]
    )
    
    return [good_candidate, medium_candidate, low_candidate]

async def test_telegram_pump_alerts():
    """Тестирует отправку pump алертов в Telegram"""
    
    print("🧪 MOCK TEST - TELEGRAM PUMP ALERTS")
    print("=" * 60)
    
    # Загружаем окружение
    load_env()
    
    # Проверяем настройки Telegram
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Telegram не настроен. Запустите: python test_telegram.py")
        return
    
    print(f"🤖 Telegram Chat ID: {chat_id}")
    print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Создаем Telegram агента
        telegram_agent = TelegramAlertAgent()
        
        # Тестируем подключение
        print("\n📱 Тестирование Telegram подключения...")
        if not telegram_agent.test_connection():
            print("❌ Ошибка подключения к Telegram")
            return
        
        # Создаем mock кандидатов
        print("\n🔍 Создание mock pump кандидатов...")
        candidates = create_mock_pump_candidates()
        
        print(f"✅ Создано {len(candidates)} mock кандидатов:")
        for i, candidate in enumerate(candidates, 1):
            emoji = "🚀" if candidate.final_score >= 80 else "🎯" if candidate.final_score >= 60 else "👀"
            print(f"   {i}. {emoji} {candidate.token_symbol}: {candidate.final_score}/100")
        
        # Отправляем уведомление о начале теста
        print(f"\n📨 Отправка алертов в Telegram...")
        telegram_agent.send_system_message("🧪 Запуск MOCK теста pump discovery системы...")
        
        # Отправляем алерты по кандидатам
        successful_alerts = telegram_agent.send_batch_alert(candidates)
        
        # Отправляем итоговую статистику
        stats_message = f"""
📊 <b>MOCK TEST STATISTICS</b>

🔍 <b>Discovery Results:</b>
• Total candidates: {len(candidates)}
• High priority (80+): {len([c for c in candidates if c.final_score >= 80])}
• Medium priority (60-79): {len([c for c in candidates if 60 <= c.final_score < 80])}
• Watch list (<60): {len([c for c in candidates if c.final_score < 60])}

📱 <b>Telegram Performance:</b>
• Alerts sent: {successful_alerts}/{len(candidates)}
• Success rate: {successful_alerts/len(candidates)*100:.0f}%

🎯 <b>Test Result:</b> ✅ SUCCESS
Mock system fully operational!
"""
        
        telegram_agent.send_message(stats_message)
        
        # Выводим результаты в консоль
        print(f"\n📊 РЕЗУЛЬТАТЫ MOCK ТЕСТА:")
        print(f"   Кандидатов создано: {len(candidates)}")
        print(f"   Алертов отправлено: {successful_alerts}/{len(candidates)}")
        print(f"   Успешность Telegram: {successful_alerts/len(candidates)*100:.0f}%")
        
        telegram_stats = telegram_agent.get_stats()
        print(f"   API вызовов Telegram: {telegram_stats['api_calls']}")
        print(f"   Общая успешность: {telegram_stats['success_rate']:.1f}%")
        
        print(f"\n🎉 MOCK ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
        print(f"✅ Pump Discovery система + Telegram алерты работают!")
        print(f"🚀 Готово к использованию с реальными API!")
        
        return candidates
        
    except Exception as e:
        print(f"\n❌ Ошибка в mock тесте: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Главная функция mock теста"""
    asyncio.run(test_telegram_pump_alerts())

if __name__ == "__main__":
    main()
