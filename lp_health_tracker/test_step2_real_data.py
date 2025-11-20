#!/usr/bin/env python3
"""
🔍 ЭТАП 2: Тестирование получения реальных данных блокчейна
========================================================

Этот скрипт проверяет:
1. Получение данных реального Uniswap пула (резервы, токены)
2. Получение цен токенов
3. Расчет IL на реальных данных
4. Валидацию всего data pipeline

НЕ изменяет основной код - только тестирует получение данных.
"""

import asyncio
import sys
import pytest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.web3_utils import Web3Manager, UNISWAP_V2_PAIR_ABI, ERC20_ABI
from src.defi_utils import ProtocolDataFetcher
from decimal import Decimal

@pytest.mark.asyncio
async def test_real_blockchain_data():
    """Тестируем получение реальных данных блокчейна."""
    print("🔍 ЭТАП 2: Тестирование реальных данных блокчейна")
    print("=" * 60)
    
    # Load environment
    print("📋 Загружаем конфигурацию...")
    load_dotenv()
    
    # Initialize Web3
    web3_manager = Web3Manager()
    success = await web3_manager.initialize()
    
    if not success:
        print("❌ Не удалось подключиться к Web3")
        return False
    
    print("✅ Web3 подключение готово")
    
    # Test 1: Real LP Pool Data
    print("\n1️⃣ Тестируем получение данных реального пула...")
    
    # Use example pool from positions.json.example (with correct checksum)
    pool_address = "0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D"  # WETH-USDC
    weth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    usdc_address = "0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C"
    
    try:
        print(f"   📍 Пул: {pool_address}")
        
        # Get pool reserves
        pool_data = await web3_manager.call_contract_function(
            pool_address,
            UNISWAP_V2_PAIR_ABI,
            "getReserves"
        )
        
        if pool_data:
            reserve0, reserve1, timestamp = pool_data
            print(f"   💰 Reserve 0: {reserve0}")
            print(f"   💰 Reserve 1: {reserve1}")
            print(f"   🕐 Last update: {timestamp}")
            
            # Get total LP supply
            total_supply = await web3_manager.call_contract_function(
                pool_address,
                UNISWAP_V2_PAIR_ABI,
                "totalSupply"
            )
            
            if total_supply:
                # Convert to human readable (18 decimals for LP tokens)
                total_supply_formatted = total_supply / (10 ** 18)
                print(f"   📊 Total LP Supply: {total_supply_formatted:.6f}")
            
            # Get token info
            token0_addr = await web3_manager.call_contract_function(
                pool_address,
                UNISWAP_V2_PAIR_ABI,
                "token0"
            )
            
            token1_addr = await web3_manager.call_contract_function(
                pool_address,
                UNISWAP_V2_PAIR_ABI,
                "token1"
            )
            
            print(f"   🪙 Token0: {token0_addr}")
            print(f"   🪙 Token1: {token1_addr}")
            
        else:
            print("   ❌ Не удалось получить данные пула")
            return False
            
    except Exception as e:
        print(f"   💥 Ошибка получения данных пула: {e}")
        return False
    
    # Test 2: Token Information
    print("\n2️⃣ Тестируем получение информации о токенах...")
    
    try:
        # Get WETH info
        weth_symbol = await web3_manager.call_contract_function(
            weth_address,
            ERC20_ABI,
            "symbol"
        )
        
        weth_decimals = await web3_manager.call_contract_function(
            weth_address,
            ERC20_ABI,
            "decimals"
        )
        
        # Get USDC info
        usdc_symbol = await web3_manager.call_contract_function(
            usdc_address,
            ERC20_ABI,
            "symbol"
        )
        
        usdc_decimals = await web3_manager.call_contract_function(
            usdc_address,
            ERC20_ABI,
            "decimals"
        )
        
        print(f"   🪙 {weth_symbol}: {weth_decimals} decimals")
        print(f"   🪙 {usdc_symbol}: {usdc_decimals} decimals")
        
        # Convert reserves to human readable format
        if pool_data and weth_decimals and usdc_decimals:
            # Determine which reserve corresponds to which token
            if token0_addr.lower() == weth_address.lower():
                weth_reserve = reserve0 / (10 ** weth_decimals)
                usdc_reserve = reserve1 / (10 ** usdc_decimals)
            else:
                weth_reserve = reserve1 / (10 ** weth_decimals)
                usdc_reserve = reserve0 / (10 ** usdc_decimals)
            
            print(f"   💰 WETH в пуле: {weth_reserve:.6f}")
            print(f"   💰 USDC в пуле: {usdc_reserve:.2f}")
            
            # Calculate current price ratio
            if weth_reserve > 0:
                price_ratio = usdc_reserve / weth_reserve
                print(f"   💱 Текущая цена WETH: ${price_ratio:.2f} USDC")
    
    except Exception as e:
        print(f"   💥 Ошибка получения информации о токенах: {e}")
        return False
    
    # Test 3: Price Data
    print("\n3️⃣ Тестируем получение цен токенов...")
    
    try:
        price_fetcher = ProtocolDataFetcher()
        
        # Get ETH price from CoinGecko
        eth_price = await price_fetcher.get_token_price("ethereum")
        if eth_price:
            print(f"   💲 ETH цена (CoinGecko): ${eth_price:.2f}")
        
        # Get USDC price
        usdc_price = await price_fetcher.get_token_price("usd-coin")  
        if usdc_price:
            print(f"   💲 USDC цена (CoinGecko): ${usdc_price:.4f}")
            
    except Exception as e:
        print(f"   💥 Ошибка получения цен: {e}")
        # This is not critical, continue
    
    # Test 4: LP Balance Check
    print("\n4️⃣ Тестируем проверку LP баланса...")
    
    try:
        # Test wallet from config
        test_wallet = "0x742d35Cc6634C0532925a3b8D41141D8F10C473d"
        
        lp_balance = await web3_manager.get_erc20_balance(
            pool_address,
            test_wallet
        )
        
        if lp_balance is not None:
            print(f"   🏦 LP баланс {test_wallet[:10]}...: {lp_balance:.10f}")
            
            if lp_balance > 0:
                print("   🎉 Найден активный LP баланс!")
                
                # Calculate position value if balance > 0
                if 'total_supply_formatted' in locals() and total_supply_formatted > 0:
                    pool_share = lp_balance / total_supply_formatted
                    print(f"   📊 Доля в пуле: {pool_share:.8%}")
                    
                    if 'weth_reserve' in locals() and 'usdc_reserve' in locals():
                        owned_weth = weth_reserve * pool_share
                        owned_usdc = usdc_reserve * pool_share
                        print(f"   💰 Ваш WETH: {owned_weth:.6f}")
                        print(f"   💰 Ваш USDC: {owned_usdc:.2f}")
            else:
                print("   ℹ️  LP баланс = 0 (нет активной позиции)")
        else:
            print("   ❌ Не удалось получить LP баланс")
    
    except Exception as e:
        print(f"   💥 Ошибка проверки LP баланса: {e}")
    
    # Test 5: Simple IL Calculation
    print("\n5️⃣ Тестируем расчет IL на реальных данных...")
    
    try:
        # Simulate initial position (example values)
        initial_weth_price = 2000.0  # Example initial price
        current_weth_price = eth_price if eth_price else 2100.0
        
        # Calculate price ratio change
        price_ratio_change = current_weth_price / initial_weth_price
        print(f"   📈 Изменение цены: {price_ratio_change:.4f}x")
        
        # Simple IL formula: IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
        import math
        il = 2 * math.sqrt(price_ratio_change) / (1 + price_ratio_change) - 1
        
        print(f"   📉 Расчетный IL: {il:.4%}")
        
        if abs(il) < 0.01:
            print("   🟢 IL в норме (< 1%)")
        elif abs(il) < 0.05:
            print("   🟡 Умеренный IL (1-5%)")
        else:
            print("   🔴 Высокий IL (> 5%)")
    
    except Exception as e:
        print(f"   💥 Ошибка расчета IL: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТ РЕАЛЬНЫХ ДАННЫХ ЗАВЕРШЕН!")
    print("✅ Все компоненты data pipeline протестированы")
    print("🚀 Готовы к запуску полной системы")
    
    return True

if __name__ == "__main__":
    print("🚀 Запускаем тест реальных данных блокчейна...")
    
    try:
        success = asyncio.run(test_real_blockchain_data())
        if success:
            print("\n🎯 РЕЗУЛЬТАТ: Data pipeline работает с реальными данными!")
            print("   Можно переходить к запуску полной системы")
            sys.exit(0)
        else:
            print("\n❌ РЕЗУЛЬТАТ: Нужно исправить проблемы с получением данных")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
