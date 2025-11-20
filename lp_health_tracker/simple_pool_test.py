#!/usr/bin/env python3
"""
Упрощенная диагностика с правильными адресами
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

def simple_test():
    """Простая проверка с известными правильными адресами."""
    
    infura_key = os.getenv('INFURA_API_KEY')
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}'))
    
    if not w3.is_connected():
        print("❌ Нет подключения")
        return
    
    print("✅ Подключен к Ethereum Mainnet")
    
    # Попробуем самый простой тест - проверим известные популярные пулы
    known_pools = {
        'WETH-USDC Uniswap V2': '0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D',  # Популярный пул
        'WETH-USDT Uniswap V2': '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852',  # Другой популярный пул
    }
    
    print("\n🔍 Проверка известных пулов Uniswap V2:")
    
    for pool_name, address in known_pools.items():
        try:
            checksum_addr = w3.to_checksum_address(address)
            code = w3.eth.get_code(checksum_addr)
            
            if len(code) > 0:
                print(f"   ✅ {pool_name}: {checksum_addr}")
                print(f"      Размер кода: {len(code)} байт")
                return checksum_addr  # Возвращаем первый найденный
            else:
                print(f"   ❌ {pool_name}: {checksum_addr} (пустой)")
                
        except Exception as e:
            print(f"   ❌ {pool_name}: Ошибка - {e}")
    
    print("\n❌ Известные пулы не найдены")
    return None

if __name__ == "__main__":
    print("🧪 ПРОСТАЯ ПРОВЕРКА ИЗВЕСТНЫХ ПУЛОВ")
    print("=" * 40)
    
    result = simple_test()
    
    if result:
        print(f"\n🎯 НАЙДЕН РАБОЧИЙ ПУЛ: {result}")
        print("\n📝 Используйте этот адрес для тестов")
    else:
        print("\n❌ Ни один пул не найден")
        print("💡 Возможно, проблема с RPC подключением")
