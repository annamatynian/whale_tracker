"""
Расширенный тест DatabaseManager
Имитирует реальный workflow системы
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.database_manager import DatabaseManager

def test_full_workflow():
    """Тест полного workflow - имитация реального pipeline."""
    print("🔄 Тестируем полный workflow DatabaseManager...")
    
    db_manager = DatabaseManager()
    
    # Шаг 1: Создание сессии анализа
    print("\n📊 Создаем сессию анализа...")
    session_id = db_manager.create_analysis_session(cycle_number=1)
    if session_id > 0:
        print(f"✅ Сессия создана с ID={session_id}")
    else:
        print("❌ Ошибка создания сессии")
        return
    
    # Шаг 2: Сохранение токена
    print("\n🪙 Сохраняем информацию о токене...")
    token_data = {
        'token_address': '0x1234567890abcdef1234567890abcdef12345678',
        'symbol': 'TEST',
        'name': 'Test Token',
        'chain_id': 'ethereum',
        'dex': 'Uniswap',
        'pair_address': '0xabcdef1234567890abcdef1234567890abcdef12'
    }
    
    if db_manager.save_or_update_token(token_data):
        print(f"✅ Токен {token_data['symbol']} сохранен")
    else:
        print("❌ Ошибка сохранения токена")
        return
    
    # Шаг 3: Сохранение анализа
    print("\n🔍 Сохраняем результат анализа...")
    analysis_result = {
        'discovery_score': 45,
        'final_score': 72,
        'recommendation': 'MEDIUM_POTENTIAL',
        'category_scores': {
            'narrative': 25,
            'security': 30,
            'onchain': 17
        }
    }
    
    token_data_with_market = {**token_data, **{
        'price_usd': 0.00123,
        'liquidity_usd': 15000,
        'volume_h24': 8500
    }}
    
    analysis_id = db_manager.save_token_analysis(session_id, token_data_with_market, analysis_result)
    if analysis_id > 0:
        print(f"✅ Анализ сохранен с ID={analysis_id}")
    else:
        print("❌ Ошибка сохранения анализа")
        return
    
    # Шаг 4: Создание алерта
    print("\n🚨 Создаем алерт...")
    alert_data = {
        'token_address': token_data['token_address'],
        'token_symbol': token_data['symbol'],
        'recommendation': analysis_result['recommendation'],
        'final_score': analysis_result['final_score'],
        'confidence_level': 0.78,
        'price_usd': token_data_with_market['price_usd'],
        'liquidity_usd': token_data_with_market['liquidity_usd'],
        'volume_24h': token_data_with_market['volume_h24']
    }
    
    alert_id = db_manager.save_alert(session_id, analysis_id, alert_data)
    if alert_id > 0:
        print(f"✅ Алерт создан с ID={alert_id}")
    else:
        print("❌ Ошибка создания алерта")
        return
    
    print("\n🎉 Полный workflow успешно протестирован!")
    print(f"📈 Создано: Сессия={session_id}, Анализ={analysis_id}, Алерт={alert_id}")

if __name__ == "__main__":
    test_full_workflow()
