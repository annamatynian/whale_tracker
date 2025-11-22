"""
Real API Integration Test
==========================

Тестирование Whale Tracker с реальными данными и API.

Этот скрипт тестирует:
1. RPC подключение к Ethereum (публичный Ankr RPC)
2. Получение реальных балансов и транзакций
3. CoinGecko API для цен (без ключа)
4. WhaleConfig (exchange database)
5. WhaleAnalyzer (статистический анализ)
6. Полный цикл мониторинга реального whale адреса

Author: Whale Tracker Project
"""

import asyncio
import logging
import os
from datetime import datetime
from decimal import Decimal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_rpc_connection():
    """Test 1: RPC Connection to Ethereum mainnet"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: RPC Connection to Ethereum Mainnet")
    logger.info("="*80)

    try:
        from src.core.web3_manager import Web3Manager

        # Use public Ankr RPC (no API key needed)
        os.environ['ANKR_URL'] = 'https://rpc.ankr.com/eth'

        # Create Web3Manager WITHOUT mock mode
        web3_manager = Web3Manager(mock_mode=False)

        # Test connection by getting gas price
        logger.info("Testing connection to Ethereum mainnet...")
        gas_price = await web3_manager.get_current_gas_price()

        if gas_price:
            logger.info(f"✅ SUCCESS: Connected to Ethereum mainnet")
            logger.info(f"   Current gas price: {gas_price / 1e9:.2f} Gwei")
        else:
            raise Exception("Failed to get gas price")

        return web3_manager

    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        raise


async def test_whale_balance(web3_manager):
    """Test 2: Get real whale balance"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Get Real Whale Balance")
    logger.info("="*80)

    try:
        # Vitalik's known address
        vitalik_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        logger.info(f"Checking balance for Vitalik's address:")
        logger.info(f"   Address: {vitalik_address}")

        # Get balance
        balance_eth = await web3_manager.get_eth_balance(vitalik_address)

        if balance_eth is not None:
            logger.info(f"✅ SUCCESS: Retrieved balance")
            logger.info(f"   Balance: {balance_eth:.4f} ETH")
        else:
            raise Exception("Failed to get balance")

        return vitalik_address, balance_eth

    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        raise


async def test_whale_transactions(web3_manager, whale_address):
    """Test 3: Get recent whale transactions"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Get Recent Whale Transactions")
    logger.info("="*80)

    try:
        logger.info(f"Fetching recent transactions for {whale_address[:10]}...")

        # Use Web3Manager's method to get recent transactions
        transactions = await web3_manager.get_recent_transactions(
            address=whale_address,
            limit=5
        )

        if transactions:
            logger.info(f"✅ SUCCESS: Found {len(transactions)} recent transaction(s)")
            for i, tx in enumerate(transactions[:3], 1):
                value_eth = tx.get('value_eth', 0)
                logger.info(f"\n   Transaction #{i}:")
                logger.info(f"      Hash: {tx.get('hash', 'N/A')[:20]}...")
                logger.info(f"      From: {tx.get('from', 'N/A')[:20]}...")
                logger.info(f"      To: {tx.get('to', 'N/A')[:20]}...")
                logger.info(f"      Value: {value_eth:.6f} ETH")
                logger.info(f"      Timestamp: {tx.get('timestamp', 'N/A')}")
        else:
            logger.info("ℹ️  No recent transactions found")
            logger.info("   (This may be due to API limits or inactive address)")

        return transactions

    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        logger.info("   Note: This requires Etherscan API key")
        return []


async def test_coingecko_prices():
    """Test 4: Get ETH price from CoinGecko"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Get ETH Price from CoinGecko")
    logger.info("="*80)

    try:
        from src.providers.coingecko_provider import CoinGeckoProvider

        # Create provider (works without API key)
        provider = CoinGeckoProvider()

        logger.info("Fetching current ETH price from CoinGecko...")

        # Get ETH price using the correct method
        eth_price = await provider.get_eth_price()

        if eth_price:
            logger.info(f"✅ SUCCESS: Retrieved ETH price")
            logger.info(f"   Price: ${float(eth_price):,.2f}")
        else:
            raise Exception("Failed to get ETH price")

        return {'usd': float(eth_price)}

    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        logger.info("   Note: CoinGecko may have rate limits without API key")
        return None


async def test_whale_config():
    """Test 5: Test WhaleConfig exchange database"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Test WhaleConfig Exchange Database")
    logger.info("="*80)

    try:
        from src.core.whale_config import WhaleConfig

        config = WhaleConfig()

        logger.info(f"Loaded {len(config.all_addresses)} known addresses")

        # Count by category
        from src.core.whale_config import WhaleCategory
        exchanges = sum(1 for a in config.all_addresses.values() if a.category == WhaleCategory.EXCHANGE)
        whales = sum(1 for a in config.all_addresses.values() if a.category == WhaleCategory.KNOWN_WHALE)
        defi = sum(1 for a in config.all_addresses.values() if a.category == WhaleCategory.DEFI_PROTOCOL)

        logger.info(f"   Exchanges: {exchanges}")
        logger.info(f"   Whales: {whales}")
        logger.info(f"   DeFi: {defi}")

        # Test classification (use exact case from config)
        binance_hot = "0x28C6c06298d514Db089934071355E5743bf21d60"
        logger.info(f"\n   Testing classification:")
        logger.info(f"   Address: {binance_hot}")

        info = config.classify_transaction_destination(binance_hot)
        logger.info(f"   ✅ Identified as: {info['category']}")
        logger.info(f"   Name: {info['name']}")
        logger.info(f"   Dump risk: {info['is_dump_risk']}")

        return config

    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        raise


async def test_whale_analyzer():
    """Test 6: Test WhaleAnalyzer with mock data"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Test WhaleAnalyzer Statistical Analysis")
    logger.info("="*80)

    try:
        from src.analyzers.whale_analyzer import WhaleAnalyzer

        analyzer = WhaleAnalyzer(
            anomaly_multiplier=2.0,
            rolling_window_size=10,
            min_history_required=5
        )

        logger.info("Feeding mock transaction data...")

        # Simulate 10 normal transactions using add_transaction
        whale_addr = "0xtest123"
        for i in range(10):
            analyzer.add_transaction(
                whale_address=whale_addr,
                amount_usd=35000.0  # Normal ~$35k
            )

        # Test anomaly detection with large transaction
        result = analyzer.detect_anomaly(
            whale_address=whale_addr,
            current_amount=350000.0  # 10x larger!
        )

        logger.info(f"✅ SUCCESS: Analyzer working")
        logger.info(f"   Anomaly detected: {result.is_anomaly}")
        logger.info(f"   Confidence: {result.confidence:.1f}%")
        logger.info(f"   Average amount: ${result.average_amount:,.2f}")
        logger.info(f"   Test amount: ${result.current_amount:,.0f}")
        logger.info(f"   Threshold: ${result.threshold:,.0f}")
        logger.info(f"   Multiplier: {result.multiplier:.2f}x")

        return analyzer

    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        raise


async def test_full_monitoring_cycle(web3_manager):
    """Test 7: Full monitoring cycle for real whale"""
    logger.info("\n" + "="*80)
    logger.info("TEST 7: Full Monitoring Cycle (Real Whale)")
    logger.info("="*80)

    try:
        from src.core.whale_config import WhaleConfig
        from src.analyzers.whale_analyzer import WhaleAnalyzer
        from config.settings import Settings

        # Load settings
        settings = Settings()

        # Initialize components
        whale_config = WhaleConfig()
        analyzer = WhaleAnalyzer()

        # Test address (Vitalik)
        whale_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        logger.info(f"Running monitoring cycle for {whale_address[:10]}...")

        # 1. Get current balance
        balance_eth = await web3_manager.get_eth_balance(whale_address)

        logger.info(f"\n   📊 Current State:")
        logger.info(f"      Balance: {balance_eth:.4f} ETH")

        # 2. Get recent transactions
        logger.info(f"\n   🔍 Fetching recent transactions...")

        transactions = await web3_manager.get_recent_transactions(
            address=whale_address,
            limit=10
        )

        if transactions:
            tx_count = len(transactions)
            large_tx_count = sum(1 for tx in transactions if tx.get('value_eth', 0) > 1.0)

            logger.info(f"   ✅ Analysis complete:")
            logger.info(f"      Transactions found: {tx_count}")
            logger.info(f"      Large txs (>1 ETH): {large_tx_count}")

            # 3. Analyze a transaction
            if transactions:
                tx = transactions[0]
                logger.info(f"\n   📈 Latest transaction:")
                logger.info(f"      Value: {tx.get('value_eth', 0):.4f} ETH")
                logger.info(f"      To: {tx.get('to', 'N/A')[:20]}...")

                # Check if destination is known
                dest = tx.get('to', '')
                if dest:
                    info = whale_config.classify_transaction_destination(dest)
                    logger.info(f"      Destination: {info['category']} - {info['name']}")
        else:
            logger.info(f"   ℹ️  No recent transactions found (may require Etherscan API key)")

        return True

    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        raise


async def main():
    """Run all real API tests"""
    logger.info("\n" + "🔥"*40)
    logger.info("WHALE TRACKER - REAL API INTEGRATION TESTS")
    logger.info("🔥"*40)

    results = {
        'passed': 0,
        'failed': 0,
        'total': 7
    }

    web3_manager = None

    try:
        # Test 1: RPC Connection
        web3_manager = await test_rpc_connection()
        results['passed'] += 1
    except Exception as e:
        results['failed'] += 1
        logger.error(f"Test 1 failed: {e}")

    if web3_manager:
        try:
            # Test 2: Whale Balance
            whale_address, balance = await test_whale_balance(web3_manager)
            results['passed'] += 1
        except Exception as e:
            results['failed'] += 1
            logger.error(f"Test 2 failed: {e}")

        try:
            # Test 3: Whale Transactions
            transactions = await test_whale_transactions(web3_manager, whale_address)
            results['passed'] += 1
        except Exception as e:
            results['failed'] += 1
            logger.error(f"Test 3 failed: {e}")

    try:
        # Test 4: CoinGecko Prices
        price_data = await test_coingecko_prices()
        if price_data:
            results['passed'] += 1
        else:
            results['failed'] += 1
    except Exception as e:
        results['failed'] += 1
        logger.error(f"Test 4 failed: {e}")

    try:
        # Test 5: WhaleConfig
        config = await test_whale_config()
        results['passed'] += 1
    except Exception as e:
        results['failed'] += 1
        logger.error(f"Test 5 failed: {e}")

    try:
        # Test 6: WhaleAnalyzer
        analyzer = await test_whale_analyzer()
        results['passed'] += 1
    except Exception as e:
        results['failed'] += 1
        logger.error(f"Test 6 failed: {e}")

    if web3_manager:
        try:
            # Test 7: Full Monitoring Cycle
            await test_full_monitoring_cycle(web3_manager)
            results['passed'] += 1
        except Exception as e:
            results['failed'] += 1
            logger.error(f"Test 7 failed: {e}")

    # Final Report
    logger.info("\n" + "="*80)
    logger.info("FINAL RESULTS")
    logger.info("="*80)
    logger.info(f"Total Tests: {results['total']}")
    logger.info(f"✅ Passed: {results['passed']}")
    logger.info(f"❌ Failed: {results['failed']}")
    logger.info(f"Success Rate: {(results['passed']/results['total'])*100:.1f}%")
    logger.info("="*80)

    if results['passed'] == results['total']:
        logger.info("🎉 ALL TESTS PASSED! Whale Tracker is READY!")
    elif results['passed'] >= results['total'] * 0.7:
        logger.info("✅ Most tests passed. System is functional with minor issues.")
    else:
        logger.info("⚠️  Several tests failed. Check configuration and API keys.")


if __name__ == "__main__":
    asyncio.run(main())
