#!/usr/bin/env python3
"""
Быстрая проверка обновленных настроек
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import Settings, CONTRACT_ADDRESSES

def check_settings():
    """Проверить что настройки обновились."""
    print("⚙️  ПРОВЕРКА ОБНОВЛЕННЫХ НАСТРОЕК")
    print("=" * 40)
    
    settings = Settings()
    
    # Проверяем рабочий адрес пула
    expected_pool = "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"
    
    print("📋 Адреса пулов в настройках:")
    ethereum_pairs = CONTRACT_ADDRESSES.get('ethereum_mainnet', {}).get('pairs', {})
    
    for name, address in ethereum_pairs.items():
        status = "✅" if address == expected_pool else "⚠️"
        print(f"   {status} {name}: {address}")
    
    if ethereum_pairs.get('WETH_USDC_V2') == expected_pool:
        print(f"\n✅ WETH_USDC_V2 адрес обновлен корректно!")
        print(f"   Рабочий адрес: {expected_pool}")
    else:
        print(f"\n❌ WETH_USDC_V2 адрес не обновлен")
        print(f"   Ожидался: {expected_pool}")
        print(f"   Получен: {ethereum_pairs.get('WETH_USDC_V2', 'НЕ НАЙДЕН')}")
    
    print(f"\n🔧 Валидация настроек:")
    errors = settings.validate()
    if errors:
        print("   ❌ Найдены ошибки в настройках:")
        for error in errors:
            print(f"     • {error}")
    else:
        print("   ✅ Настройки валидны")
    
    print(f"\n📡 RPC подключение:")
    rpc_url = settings.get_rpc_url()
    print(f"   URL: {rpc_url}")

if __name__ == "__main__":
    check_settings()
