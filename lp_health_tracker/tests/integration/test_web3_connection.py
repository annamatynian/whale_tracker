#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИКА: Проверка подключения и контракта
==============================================

Простая диагностика для выяснения проблемы с получением данных контракта.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.web3_utils import Web3Manager

async def diagnose_connection():
    """Диагностика подключения и контракта."""
    print("🔍 ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ")
    print("=" * 40)
    
    # Load environment
    load_dotenv()
    
    # Initialize Web3
    web3_manager = Web3Manager()
    success = await web3_manager.initialize()
    
    if not success:
        print("❌ Web3 инициализация не удалась")
        return
    
    # Check network info
    print("📡 Информация о сети:")
    network_info = web3_manager.get_network_info()
    print(f"   Сеть: {network_info.get('name', 'Unknown')}")
    print(f"   Chain ID: {network_info.get('chain_id', 'Unknown')}")
    print(f"   RPC URL: {network_info.get('rpc_url', 'Unknown')}")
    
    # Check actual connection
    if web3_manager.web3:
        try:
            # Get current chain ID to verify we're on the right network
            current_chain_id = web3_manager.web3.eth.chain_id
            print(f"   Реальный Chain ID: {current_chain_id}")
            
            # Get latest block
            latest_block = web3_manager.web3.eth.get_block('latest')
            print(f"   Последний блок: {latest_block['number']}")
            
            # Verify this is mainnet (chain_id = 1)
            if current_chain_id == 1:
                print("✅ Подключены к Ethereum Mainnet")
            elif current_chain_id == 11155111:
                print("⚠️  Подключены к Sepolia (нужен Mainnet)")
                return
            else:
                print(f"⚠️  Подключены к неизвестной сети: {current_chain_id}")
                return
                
        except Exception as e:
            print(f"❌ Ошибка получения информации о сети: {e}")
            return
    
    # Test contract existence
    print("\n🏗️ Проверка контракта:")
    pool_address_raw = "0xb4e16d0168e52d35cacd2b6464f00d6eb9002c6d"  # Попробуем известный адрес
    print(f"   Тестируем адрес 1: {pool_address_raw}")
    
    # Также попробуем другие известные WETH-USDC адреса
    known_addresses = [
        "0xb4e16d0168e52d35cacd2b6464f00d6eb9002c6d",  # Один из вариантов
        "0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D",  # Другой вариант  
        "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0",  # USDC-WETH (обратный порядок)
    ]
    
    found_working_address = None
    
    for addr in known_addresses:
        try:
            # Let Web3 create proper checksum
            from web3 import Web3
            pool_address = Web3.to_checksum_address(addr)
            print(f"\n   Проверяем: {pool_address}")
            
            # Check if contract exists (has code)
            contract_code = web3_manager.web3.eth.get_code(pool_address)
            
            if len(contract_code) > 2:  # More than '0x'
                print(f"   ✅ Контракт найден! Размер кода: {len(contract_code)} bytes")
                found_working_address = pool_address
                break
            else:
                print(f"   ❌ Контракт не найден (нет кода)")
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки {addr}: {e}")
            continue
    
    if not found_working_address:
        print("\n❌ Не найден ни один рабочий адрес пула")
        return
    
    pool_address = found_working_address
    
    # Test simple contract call - get total supply (simpler than getReserves)
    print("\n🔧 Тест простого вызова контракта:")
    
    # Minimal ERC20 ABI for totalSupply
    simple_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        }
    ]
    
    try:
        # Create contract instance directly
        from web3 import Web3
        pool_address_checksum = Web3.to_checksum_address(pool_address)
        contract = web3_manager.web3.eth.contract(
            address=pool_address_checksum,
            abi=simple_abi
        )
        
        # Call totalSupply
        total_supply = contract.functions.totalSupply().call()
        print(f"✅ totalSupply вызов успешен: {total_supply}")
        
        # Convert to human readable
        total_supply_readable = total_supply / (10 ** 18)
        print(f"   В читаемом виде: {total_supply_readable:.6f}")
        
    except Exception as e:
        print(f"❌ Ошибка вызова totalSupply: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return
    
    # Test getReserves call
    print("\n💰 Тест вызова getReserves:")
    
    # Uniswap V2 ABI for getReserves
    uniswap_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"name": "_reserve0", "type": "uint112"},
                {"name": "_reserve1", "type": "uint112"},
                {"name": "_blockTimestampLast", "type": "uint32"}
            ],
            "type": "function"
        }
    ]
    
    try:
        # Create contract instance
        contract = web3_manager.web3.eth.contract(
            address=pool_address_checksum,
            abi=uniswap_abi
        )
        
        # Call getReserves
        reserves = contract.functions.getReserves().call()
        print(f"✅ getReserves вызов успешен:")
        print(f"   Reserve0: {reserves[0]}")
        print(f"   Reserve1: {reserves[1]}")
        print(f"   Timestamp: {reserves[2]}")
        
    except Exception as e:
        print(f"❌ Ошибка вызова getReserves: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return
    
    print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    print("🚀 Контракт работает, можно продолжать")

if __name__ == "__main__":
    asyncio.run(diagnose_connection())
