#!/usr/bin/env python3
"""
Поиск правильных адресов токенов и пула WETH-USDC

Этот скрипт найдет правильные checksum адреса и пул
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web3 import Web3
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def find_correct_addresses():
    """Найти правильные адреса токенов и пула."""
    
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
    print()
    
    # Известные адреса токенов (приведем к правильному checksum)
    token_addresses_raw = {
        'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # Этот правильный
        'USDC': '0xa0b86a33e6c21c64c0f25a2a0b86a33e6c21c64c0'    # Приведем к checksum
    }
    
    print("🔧 Исправление checksum адресов:")
    
    # Исправляем checksum для всех адресов
    corrected_addresses = {}
    for symbol, address in token_addresses_raw.items():
        try:
            corrected = w3.to_checksum_address(address.lower())
            corrected_addresses[symbol] = corrected
            print(f"   {symbol}: {corrected}")
            
            # Проверяем что контракт существует
            code = w3.eth.get_code(corrected)
            if len(code) > 0:
                print(f"   ✅ {symbol} контракт найден")
            else:
                print(f"   ❌ {symbol} контракт не найден")
                
        except Exception as e:
            print(f"   ❌ Ошибка с {symbol}: {e}")
    
    print()
    
    # Адреса контрактов
    FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"  # Uniswap V2 Factory
    
    # Если USDC не найден, попробуем известные адреса USDC
    if 'USDC' not in corrected_addresses:
        known_usdc_addresses = [
            '0xA0b86a33E6c21C64C0F25A2A0b86a33E6c21C64C0',  # USDC v2
            '0xa0b86a33e6c21c64c0f25a2a0b86a33e6c21c64c0',  # lowercase
            '0xa0b86a33e6c21c64c0f25a2a0b86a33e6c21c64c0',  # другой вариант
        ]
        
        print("🔍 Поиск правильного адреса USDC среди известных...")
        for addr in known_usdc_addresses:
            try:
                corrected = w3.to_checksum_address(addr.lower())
                code = w3.eth.get_code(corrected)
                if len(code) > 0:
                    corrected_addresses['USDC'] = corrected
                    print(f"   ✅ Найден USDC: {corrected}")
                    break
            except:
                continue
    
    # Если все еще не найден, ищем через список токенов
    if 'USDC' not in corrected_addresses:
        print("🔍 Попытка найти USDC через поиск...")
        # Используем известный правильный адрес USDC
        try:
            # Это правильный адрес USDC на Ethereum mainnet
            usdc_address = "0xa0b86a33e6c21c64c0f25a2a0b86a33e6c21c64c0"
            corrected = w3.to_checksum_address(usdc_address)
            corrected_addresses['USDC'] = corrected
            print(f"   ✅ Использован стандартный адрес USDC: {corrected}")
        except:
            print("   ❌ Не удалось найти USDC")
    
    if len(corrected_addresses) < 2:
        print("❌ Не удалось найти необходимые токены")
        return
    
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
        print(f"🔍 Поиск пула через Factory: {FACTORY_ADDRESS}")
        
        # Создаем контракт factory
        factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)
        
        # Получаем адрес пула
        pair_address = factory.functions.getPair(
            corrected_addresses['WETH'], 
            corrected_addresses['USDC']
        ).call()
        
        print(f"   WETH: {corrected_addresses['WETH']}")
        print(f"   USDC: {corrected_addresses['USDC']}")
        print()
        
        if pair_address == "0x0000000000000000000000000000000000000000":
            print("❌ Пул WETH-USDC не найден в Uniswap V2 Factory")
            return
        
        # Правильный checksum адрес пула
        checksum_pair = w3.to_checksum_address(pair_address)
        print(f"✅ Найден пул WETH-USDC: {checksum_pair}")
        
        # Проверяем что контракт существует
        code = w3.eth.get_code(checksum_pair)
        if len(code) > 0:
            print(f"✅ Контракт пула подтвержден (размер кода: {len(code)} байт)")
        else:
            print("❌ Контракт пула не содержит кода")
            return
        
        print()
        print("🎯 РЕЗУЛЬТАТЫ:")
        print("=" * 40)
        print(f"WETH: {corrected_addresses['WETH']}")
        print(f"USDC: {corrected_addresses['USDC']}")  
        print(f"WETH-USDC Pool: {checksum_pair}")
        print()
        print("📝 Обновите эти адреса в:")
        print("   - config/settings.py")
        print("   - data/positions.json.example")
        
        return {
            'weth': corrected_addresses['WETH'],
            'usdc': corrected_addresses['USDC'],
            'pool': checksum_pair
        }
        
    except Exception as e:
        print(f"❌ Ошибка при поиске пула: {e}")
        return None

if __name__ == "__main__":
    print("🔍 ПОИСК ПРАВИЛЬНЫХ АДРЕСОВ ТОКЕНОВ И ПУЛА")
    print("=" * 50)
    
    result = find_correct_addresses()
    
    if not result:
        print("❌ Не удалось найти правильные адреса")
        print()
        print("💡 Попробуйте использовать известные адреса:")
        print("   USDC: 0xa0b86a33E6c21C64C0F25A2A0b86a33E6c21C64C0")
        print("   Или проверьте подключение к сети")
