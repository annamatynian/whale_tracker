#!/usr/bin/env python3
"""
Поиск правильного адреса WETH-USDC пула через Uniswap V2 Factory

Этот скрипт найдет актуальный адрес пула через Factory контракт
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web3 import Web3
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def find_uniswap_pool():
    """Найти правильный адрес WETH-USDC пула."""
    
    # Подключение к Web3
    infura_key = os.getenv('INFURA_API_KEY')
    if not infura_key:
        print("❌ INFURA_API_KEY не найден в .env файле")
        return
    
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}'))
    
    if not w3.is_connected():
        print("❌ Не удалось подключиться к Ethereum")
        return
    
    print("✅ Подключен к Ethereum Mainnet")
    
    # Адреса контрактов
    FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"  # Uniswap V2 Factory
    WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"   # WETH
    USDC_ADDRESS = "0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C"   # USDC
    
    # ABI для factory contract
    factory_abi = [
        {
            "constant": True,
            "inputs": [
                {"name": "tokenA", "type": "address"},
                {"name": "tokenB", "type": "address"}
            ],
            "name": "getPair",
            "outputs": [{"name": "pair", "type": "address"}],
            "type": "function"
        }
    ]
    
    try:
        # Создаем контракт factory
        factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)
        
        # Получаем адрес пула
        pair_address = factory.functions.getPair(WETH_ADDRESS, USDC_ADDRESS).call()
        
        print(f"🔍 Поиск пула WETH-USDC:")
        print(f"   WETH: {WETH_ADDRESS}")
        print(f"   USDC: {USDC_ADDRESS}")
        print(f"   Factory: {FACTORY_ADDRESS}")
        print()
        
        if pair_address == "0x0000000000000000000000000000000000000000":
            print("❌ Пул WETH-USDC не найден")
            return
        
        print(f"✅ Найден пул WETH-USDC: {pair_address}")
        
        # Проверяем что контракт существует
        code = w3.eth.get_code(pair_address)
        if len(code) > 0:
            print(f"✅ Контракт подтвержден (размер кода: {len(code)} байт)")
        else:
            print("❌ Контракт не содержит кода")
            return
        
        # Правильный checksum адрес
        checksum_address = w3.to_checksum_address(pair_address)
        print(f"📋 Правильный checksum адрес: {checksum_address}")
        
        return checksum_address
        
    except Exception as e:
        print(f"❌ Ошибка при поиске пула: {e}")
        return None

if __name__ == "__main__":
    print("🔍 ПОИСК ПРАВИЛЬНОГО АДРЕСА WETH-USDC ПУЛА")
    print("=" * 50)
    
    correct_address = find_uniswap_pool()
    
    if correct_address:
        print()
        print("🎯 РЕЗУЛЬТАТ:")
        print(f"Используйте этот адрес в ваших настройках: {correct_address}")
        print()
        print("📝 Обновите файлы:")
        print("   - config/settings.py")
        print("   - data/positions.json.example")
    else:
        print("❌ Не удалось найти правильный адрес пула")
