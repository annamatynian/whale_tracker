#!/usr/bin/env python3
"""
🔍 ЭТАП 1: Базовый тест подключения к blockchain
============================================

Этот скрипт проверяет:
1. Подключение к Infura/Sepolia
2. Получение базовой информации о сети
3. Подключение к Telegram боту

НЕ изменяет основной код - только тестирует компоненты.
"""

import asyncio
import sys
import pytest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.web3_utils import Web3Manager
from src.notification_manager import TelegramNotifier

@pytest.mark.asyncio
async def test_basic_connections():
    """Тестируем базовые подключения."""
    print("🔍 ЭТАП 1: Базовый тест подключений")
    print("=" * 50)
    
    # Load environment
    print("📋 Загружаем конфигурацию...")
    load_dotenv()
    
    # Test 1: Web3 Connection
    print("\n1️⃣ Тестируем Web3 подключение...")
    try:
        web3_manager = Web3Manager()
        success = await web3_manager.initialize()
        
        if success:
            print("   ✅ Web3 подключение успешно!")
            
            # Get basic network info using existing Web3 object
            if web3_manager.web3:
                # Get latest block number directly from web3 object
                latest_block = web3_manager.web3.eth.get_block('latest')['number']
                print(f"   📊 Последний блок: {latest_block}")
                
                # Use existing gas price method
                gas_price = await web3_manager.get_current_gas_price()
                if gas_price:
                    # Convert to Gwei for readability
                    from web3 import Web3
                    gas_price_gwei = Web3.from_wei(gas_price, 'gwei')
                    print(f"   ⛽ Текущая цена газа: {gas_price_gwei:.2f} Gwei")
        else:
            print("   ❌ Web3 подключение не удалось")
            return False
            
    except Exception as e:
        print(f"   💥 Ошибка Web3: {e}")
        return False
    
    # Test 2: Telegram Connection  
    print("\n2️⃣ Тестируем Telegram подключение...")
    try:
        notifier = TelegramNotifier()
        success = await notifier.test_connection()
        
        if success:
            print("   ✅ Telegram подключение успешно!")
            
            # Send test message
            test_message = (
                "Тест подключения LP Health Tracker\n"
                "Этап 1: Базовые подключения работают!\n"
                f"Blockchain: Подключен к Sepolia\n" 
                f"Telegram: Бот отвечает"
            )
            
            await notifier.send_message(test_message, parse_mode=None)
            print("   📨 Тестовое сообщение отправлено!")
        else:
            print("   ❌ Telegram подключение не удалось")
            return False
            
    except Exception as e:
        print(f"   💥 Ошибка Telegram: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ВСЕ БАЗОВЫЕ ПОДКЛЮЧЕНИЯ РАБОТАЮТ!")
    print("✅ Готовы к следующему этапу")
    
    return True

if __name__ == "__main__":
    print("🚀 Запускаем базовый тест подключений...")
    
    try:
        success = asyncio.run(test_basic_connections())
        if success:
            print("\n🎯 РЕЗУЛЬТАТ: Система готова для активации real-data pipeline")
            sys.exit(0)
        else:
            print("\n❌ РЕЗУЛЬТАТ: Нужно исправить подключения перед продолжением")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
