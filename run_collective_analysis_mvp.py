"""
Collective Whale Analysis - MVP Demo (No Database)

Quick demo: get top whales and calculate accumulation manually.

Usage:
    python run_collective_analysis_mvp.py
"""

import asyncio
import logging
from decimal import Decimal

from src.core.web3_manager import Web3Manager
from src.data.multicall_client import MulticallClient
from src.data.whale_list_provider import WhaleListProvider


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def run_mvp_analysis():
    """Run simplified collective whale analysis (no database)."""
    
    logger.info("=" * 70)
    logger.info("🐋 COLLECTIVE WHALE ANALYSIS - MVP DEMO")
    logger.info("=" * 70)
    
    try:
        # Step 1: Initialize Web3
        logger.info("\n🌐 Step 1: Initializing Web3...")
        web3_manager = Web3Manager(mock_mode=False)
        success = await web3_manager.initialize()
        if not success:
            raise Exception("Failed to initialize Web3")
        logger.info("✅ Web3 connected")
        
        # Step 2: Initialize MulticallClient
        logger.info("\n🔗 Step 2: Initializing MulticallClient...")
        multicall_client = MulticallClient(web3_manager)
        logger.info("✅ MulticallClient ready")
        
        # Step 3: Initialize WhaleListProvider
        logger.info("\n🐳 Step 3: Initializing WhaleListProvider...")
        whale_provider = WhaleListProvider(
            multicall_client=multicall_client,
            min_balance_eth=1000
        )
        logger.info("✅ WhaleListProvider ready")
        
        # Step 4: Get Current Whales
        logger.info("\n" + "=" * 70)
        logger.info("🚀 Step 4: FETCHING TOP 10 WHALES")
        logger.info("=" * 70)
        
        whales = await whale_provider.get_top_whales(limit=10)
        
        logger.info(f"\n✅ Found {len(whales)} whales\n")
        
        # Calculate current total
        total_current_wei = sum(w['balance_wei'] for w in whales)
        total_current_eth = Decimal(str(total_current_wei)) / Decimal('1e18')
        
        # Step 5: Get Historical Balances
        logger.info("=" * 70)
        logger.info("📊 Step 5: FETCHING HISTORICAL BALANCES (24h ago)")
        logger.info("=" * 70)
        
        current_block = await multicall_client.get_latest_block()
        historical_block = current_block - (24 * 300)  # 24h ago
        
        addresses = [w['address'] for w in whales]
        historical_balances = await multicall_client.get_historical_balances(
            addresses=addresses,
            block_number=historical_block
        )
        
        # Calculate historical total
        total_historical_wei = sum(historical_balances.values())
        total_historical_eth = Decimal(str(total_historical_wei)) / Decimal('1e18')
        
        # Step 6: Calculate Metrics
        logger.info("\n" + "=" * 70)
        logger.info("🧮 Step 6: CALCULATING ACCUMULATION SCORE")
        logger.info("=" * 70)
        
        total_change_wei = total_current_wei - total_historical_wei
        total_change_eth = total_current_eth - total_historical_eth
        
        if total_historical_wei > 0:
            accumulation_score = (Decimal(str(total_change_wei)) / Decimal(str(total_historical_wei))) * 100
        else:
            accumulation_score = Decimal('0')
        
        # Count accumulators vs distributors
        accumulators = 0
        distributors = 0
        neutral = 0
        
        for whale in whales:
            current = whale['balance_wei']
            historical = historical_balances.get(whale['address'], 0)
            
            if current > historical:
                accumulators += 1
            elif current < historical:
                distributors += 1
            else:
                neutral += 1
        
        # Step 7: Display Results
        logger.info("\n" + "=" * 70)
        logger.info("📊 ANALYSIS RESULTS")
        logger.info("=" * 70)
        
        print(f"\n🐋 Whales Analyzed: {len(whales)}")
        print(f"📈 Accumulation Score: {accumulation_score:+.4f}%")
        print(f"💰 Total Balance Change: {total_change_eth:+,.2f} ETH")
        print(f"📊 Current Total: {total_current_eth:,.2f} ETH")
        print(f"📊 Historical Total: {total_historical_eth:,.2f} ETH")
        print(f"\n👥 Whale Behavior:")
        print(f"  ⬆️  Accumulating: {accumulators}")
        print(f"  ⬇️  Distributing: {distributors}")
        print(f"  ➡️  Neutral: {neutral}")
        print(f"\n🔢 Block Range:")
        print(f"  Current: {current_block:,}")
        print(f"  Historical: {historical_block:,}")
        print(f"  Lookback: 24h")
        
        # Interpretation
        print(f"\n💡 Interpretation:")
        if accumulation_score > 2:
            print("  🟢 STRONG ACCUMULATION - Whales are buying aggressively")
        elif accumulation_score > 0.5:
            print("  🟢 ACCUMULATION - Whales are net buyers")
        elif accumulation_score > -0.5:
            print("  🟡 NEUTRAL - No significant whale movement")
        elif accumulation_score > -2:
            print("  🔴 DISTRIBUTION - Whales are net sellers")
        else:
            print("  🔴 STRONG DISTRIBUTION - Whales are selling aggressively")
        
        print("\n" + "=" * 70)
        print("✅ MVP ANALYSIS COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(run_mvp_analysis())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Analysis interrupted")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
