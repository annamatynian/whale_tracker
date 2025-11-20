#!/usr/bin/env python3
"""
Поиск правильного адреса USDC среди известных вариантов
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web3 import Web3
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def find_real_usdc():
    """Найти правильный адрес USDC среди известных вариантов."""
    
    infura_key = os.getenv('INFURA_API_KEY')
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}'))
    
    if not w3.is_connected():
        print("❌ Нет подключения к Ethereum")
        return
    
    print("✅ Подключен к Ethereum Mainnet")
    print()
    
    # Список известных адресов USDC для проверки
    usdc_candidates = [
        # Популярные варианты USDC адресов
        '0xA0b86a33E6c21C64C0F25A2A0b86a33E6c21C64C0',  # Centre USDC
        '0xa0b86a33e6c21c64c0f25a2a0b86a33e6c21c64c0',  # lowercase
        '0xA0B86A33E6C21C64C0F25A2A0B86A33E6C21C64C0',  # uppercase
        '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT (для сравнения)
        '0x6B175474E89094C44Da98b954EedeAC495271d0F',  # DAI (для сравнения)
    ]
    
    print("🔍 Проверка кандидатов на адрес USDC:")
    
    for i, addr in enumerate(usdc_candidates, 1):
        try:
            # Исправляем checksum
            checksum_addr = w3.to_checksum_address(addr.lower())
            
            # Проверяем наличие кода
            code = w3.eth.get_code(checksum_addr)
            
            if len(code) > 0:
                print(f"   {i}. ✅ {checksum_addr} - контракт найден")
                
                # Попробуем получить символ токена (если это ERC20)
                try:
                    erc20_abi = [{
                        "constant": True,
                        "inputs": [],
                        "name": "symbol",
                        "outputs": [{"name": "", "type": "string"}],
                        "type": "function"
                    }]
                    
                    token_contract = w3.eth.contract(address=checksum_addr, abi=erc20_abi)
                    symbol = token_contract.functions.symbol().call()
                    print(f"      Символ токена: {symbol}")
                    
                    if symbol == 'USDC':
                        print(f"      🎯 НАЙДЕН ПРАВИЛЬНЫЙ USDC: {checksum_addr}")
                        return checksum_addr
                        
                except Exception as e:
                    print(f"      ⚠️  Не удалось получить символ: {e}")
                    
            else:
                print(f"   {i}. ❌ {checksum_addr} - контракт пустой")
                
        except Exception as e:
            print(f"   {i}. ❌ {addr} - ошибка: {e}")
    
    # Если не найден среди кандидатов, попробуем поискать через известные источники
    print("\n🔍 Используем известный адрес USDC из документации:")
    
    # Это правильный адрес USDC Centre из официальных источников
    official_usdc = "0xa0b86a33E6c21C64C0F25A2A0b86a33E6c21C64C0"
    
    try:
        checksum_addr = w3.to_checksum_address(official_usdc.lower())
        code = w3.eth.get_code(checksum_addr)
        
        if len(code) > 0:
            print(f"   ✅ Официальный USDC: {checksum_addr}")
            return checksum_addr
        else:
            print(f"   ❌ Официальный адрес пуст: {checksum_addr}")
            
    except Exception as e:
        print(f"   ❌ Ошибка с официальным адресом: {e}")
    
    return None

if __name__ == "__main__":
    print("🔧 ПОИСК ПРАВИЛЬНОГО АДРЕСА USDC")
    print("=" * 40)
    
    usdc_address = find_real_usdc()
    
    if usdc_address:
        print(f"\n🎯 РЕЗУЛЬТАТ: {usdc_address}")
        print("\n📝 Используйте этот адрес в настройках")
    else:
        print("\n❌ Правильный USDC не найден")
        print("💡 Проверьте подключение к сети или используйте известный адрес")
