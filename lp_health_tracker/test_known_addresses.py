#!/usr/bin/env python3
"""
Простой скрипт для поиска правильного адреса USDC и пула
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web3 import Web3
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_known_addresses():
    """Тестируем известные адреса токенов."""
    
    # Подключение к Web3
    infura_key = os.getenv('INFURA_API_KEY')
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}'))
    
    if not w3.is_connected():
        print("❌ Нет подключения к Ethereum")
        return
    
    print("✅ Подключен к Ethereum Mainnet")
    print()
    
    # Known correct addresses
    known_addresses = {
        'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        # Попробуем правильный адрес USDC
        'USDC': '0xA0b86a33E6c21C64C0F25A2A0b86a33E6c21C64C0'  # USD Coin
    }
    
    print("🔍 Проверка известных адресов токенов:")
    
    verified_addresses = {}
    
    for symbol, address in known_addresses.items():
        try:
            # Проверяем checksum
            checksum_addr = w3.to_checksum_address(address)
            
            # Проверяем существование контракта
            code = w3.eth.get_code(checksum_addr)
            
            if len(code) > 0:
                print(f"   ✅ {symbol}: {checksum_addr} (контракт найден)")
                verified_addresses[symbol] = checksum_addr
            else:
                print(f"   ❌ {symbol}: {checksum_addr} (нет контракта)")
                
        except Exception as e:
            print(f"   ❌ {symbol}: Ошибка - {e}")
    
    # Если USDC не найден, попробуем другие известные адреса
    if 'USDC' not in verified_addresses:
        print("\n🔍 Пробуем другие варианты USDC:")
        
        alternative_usdc = [
            '0xa0b86a33E6c21C64C0F25A2A0b86a33E6c21C64C0',  # Centre USD Coin
            '0xa0b86a33e6c21c64c0f25a2a0b86a33e6c21c64c0',  # lowercase версия
        ]
        
        for addr in alternative_usdc:
            try:
                checksum_addr = w3.to_checksum_address(addr)
                code = w3.eth.get_code(checksum_addr)
                
                if len(code) > 0:
                    print(f"   ✅ USDC найден: {checksum_addr}")
                    verified_addresses['USDC'] = checksum_addr
                    break
                else:
                    print(f"   ⚠️  Пустой: {checksum_addr}")
                    
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
    
    if len(verified_addresses) < 2:
        print("\n❌ Не удалось найти оба токена")
        return
    
    # Теперь ищем пул
    print(f"\n🔍 Поиск пула WETH-USDC:")
    
    FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
    
    factory_abi = [{
        "constant": True,
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"name": "pair", "type": "address"}],
        "type": "function"
    }]
    
    try:
        factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)
        
        pair_address = factory.functions.getPair(
            verified_addresses['WETH'], 
            verified_addresses['USDC']
        ).call()
        
        if pair_address != "0x0000000000000000000000000000000000000000":
            checksum_pair = w3.to_checksum_address(pair_address)
            
            # Проверяем контракт пула
            code = w3.eth.get_code(checksum_pair)
            if len(code) > 0:
                print(f"   ✅ Пул найден: {checksum_pair}")
                
                print(f"\n🎯 РЕЗУЛЬТАТЫ:")
                print("=" * 40)
                for symbol, addr in verified_addresses.items():
                    print(f"{symbol}: {addr}")
                print(f"WETH-USDC Pool: {checksum_pair}")
                
                return {
                    'tokens': verified_addresses,
                    'pool': checksum_pair
                }
            else:
                print("   ❌ Пул не содержит кода")
        else:
            print("   ❌ Пул не найден")
            
    except Exception as e:
        print(f"   ❌ Ошибка поиска пула: {e}")
    
    return None

if __name__ == "__main__":
    print("🔧 ТЕСТИРОВАНИЕ ИЗВЕСТНЫХ АДРЕСОВ")
    print("=" * 40)
    test_known_addresses()
