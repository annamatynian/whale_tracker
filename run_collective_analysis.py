"""
Collective Whale Analysis - Main Entry Point (With LST Correction)

Run collective whale analysis with LST correction, smart tags, and anomaly detection.

Usage:
    python run_collective_analysis.py
"""

import asyncio
import logging
import sys
from datetime import datetime

from src.core.web3_manager import Web3Manager
from src.data.multicall_client import MulticallClient
from src.data.whale_list_provider import WhaleListProvider
from src.providers.coingecko_provider import CoinGeckoProvider
from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator
from data_quality_validator import DataQualityValidator, HealthStatus

# Telegram notifications
try:
    from config.notification_config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        ENABLE_TELEGRAM
    )
    from src.notifications.telegram_notifier import TelegramNotifier
    
    if ENABLE_TELEGRAM:
        telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    else:
        telegram = None
except ImportError:
    telegram = None
    logger.warning("⚠️  Telegram notifications disabled (config not found)")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class DataQualityException(Exception):
    """Raised when data quality is too poor to proceed."""
    pass


async def run_analysis():
    """Run collective whale analysis end-to-end."""
    
    logger.info("=" * 70)
    logger.info("🐋 COLLECTIVE WHALE ANALYSIS - STARTING")
    logger.info("=" * 70)
    
    try:
        # Step 1: Initialize Database (using init_postgres approach)
        logger.info("\n📊 Step 1: Initializing database...")
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        import os
        
        # Get database URL from environment
        # Use asyncpg for async support (not psycopg2)
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'whale_tracker')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'Jayaasiri2185')
        
        db_url = f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        
        engine = create_async_engine(db_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Create session
        async with async_session() as session:
            logger.info("✅ Database connected")
            
            # ========================================
            # STEP 0: DATA QUALITY GATE (CIRCUIT BREAKER)
            # ========================================
            logger.info("\n" + "=" * 70)
            logger.info("🔒 STEP 0: Data Quality Validation (Circuit Breaker)")
            logger.info("=" * 70)
            
            validator = DataQualityValidator(session)
            report = await validator.run_all_checks()
            
            validation_status = HealthStatus(report["overall_status"])
            validation_score = report["overall_score"]
            
            # Print report summary
            logger.info(f"\n📋 Quality Report:")
            logger.info(f"  Overall Status: {validation_status.value.upper()}")
            logger.info(f"  Quality Score: {validation_score:.1f}/100")
            logger.info(f"  Critical Issues: {report['summary']['critical_issues']}")
            logger.info(f"  Warnings: {report['summary']['warnings']}")
            
            # CIRCUIT BREAKER LOGIC
            if validation_status == HealthStatus.CRITICAL:
                logger.error("\n" + "⚠" * 35)
                logger.error("🚨 CIRCUIT BREAKER ACTIVATED - CRITICAL DATA QUALITY")
                logger.error("⚠" * 35)
                logger.error(f"\nCritical Issues Found: {report['summary']['critical_issues']}")
                
                # Print detailed issues
                for check in report["checks"]:
                    if check["status"] == "critical":
                        logger.error(f"\n[{check['check_name'].upper()}]")
                        for issue in check["issues"]:
                            logger.error(f"  ❌ {issue}")
                
                logger.error("\n💡 Recommended Actions:")
                logger.error("  1. Review logs/whale_tracker.log for RPC errors")
                logger.error("  2. Verify SnapshotJob is running (check APScheduler)")
                logger.error("  3. Check database: SELECT COUNT(*) FROM whale_balance_snapshots WHERE snapshot_timestamp >= NOW() - INTERVAL '24 hours';")
                logger.error("  4. Re-run manual snapshot: python run_manual_snapshot.py")
                logger.error("\n⚠️  ANALYSIS ABORTED - Fix data quality issues first")
                logger.error("=" * 70)
                
                # Send Telegram alert
                if telegram:
                    alert_msg = (
                        "🚨 <b>CIRCUIT BREAKER ACTIVATED</b>\\n\\n"
                        f"📊 Quality Score: {validation_score:.1f}/100\\n"
                        f"❌ Critical Issues: {report['summary']['critical_issues']}\\n\\n"
                        "<b>Action Required:</b>\\n"
                        "Run: <code>python run_manual_snapshot.py</code>"
                    )
                    await telegram.send_alert(alert_msg)
                
                # STOP EXECUTION
                raise DataQualityException(
                    f"Circuit breaker OPEN - Data quality CRITICAL\n"
                    f"Score: {validation_score:.1f}/100\n"
                    f"Issues: {report['summary']['critical_issues']}"
                )
            
            elif validation_status == HealthStatus.DEGRADED:
                logger.warning("\n" + "⚠" * 35)
                logger.warning("⚠️  DEGRADED DATA QUALITY - Proceeding with caution")
                logger.warning("⚠" * 35)
                logger.warning("\n📋 Warnings:")
                for check in report["checks"]:
                    if check["status"] == "degraded" and check["issues"]:
                        logger.warning(f"\n[{check['check_name'].upper()}]")
                        for issue in check["issues"]:
                            logger.warning(f"  ⚠️  {issue}")
                logger.warning("\n💡 Analysis will continue but ALL metrics will be marked as anomalies")
                force_anomaly_flag = True
            else:
                logger.info("\n✅ Data quality HEALTHY - Proceeding normally")
                force_anomaly_flag = False
            
            # Step 2: Initialize Web3
            logger.info("\n🌐 Step 2: Initializing Web3 connection...")
            web3_manager = Web3Manager(mock_mode=False)
            success = await web3_manager.initialize()
            if not success:
                raise Exception("Failed to initialize Web3Manager")
            logger.info("✅ Web3 connected")
            
            # Step 3: Initialize MulticallClient
            logger.info("\n🔗 Step 3: Initializing MulticallClient...")
            multicall_client = MulticallClient(web3_manager)
            logger.info("✅ MulticallClient ready")
            
            # Step 4: Initialize WhaleListProvider
            logger.info("\n🐳 Step 4: Initializing WhaleListProvider...")
            whale_provider = WhaleListProvider(
                multicall_client=multicall_client,
                min_balance_eth=1000  # 1000 ETH minimum
            )
            logger.info("✅ WhaleListProvider ready")
            
            # Step 5: Initialize Repositories
            logger.info("\n💾 Step 5: Initializing Repositories...")
            from src.repositories.accumulation_repository import SQLAccumulationRepository
            from src.repositories.snapshot_repository import SnapshotRepository
            
            # Create concrete implementations
            repository = SQLAccumulationRepository(session)
            snapshot_repo = SnapshotRepository(session)  # Already concrete
            logger.info("✅ Repositories ready")
            
            # Step 6: Initialize PriceProvider
            logger.info("\n💰 Step 6: Initializing PriceProvider...")
            price_provider = CoinGeckoProvider(network="ethereum")
            logger.info("✅ PriceProvider ready")
            
            # Step 7: Initialize Calculator
            logger.info("\n🧮 Step 7: Initializing AccumulationScoreCalculator...")
            calculator = AccumulationScoreCalculator(
                whale_provider=whale_provider,
                multicall_client=multicall_client,
                repository=repository,
                snapshot_repo=snapshot_repo,
                price_provider=price_provider,
                lookback_hours=24
            )
            logger.info("✅ Calculator ready (LST correction enabled)")
            
            # Step 8: Run Analysis
            logger.info("\n" + "=" * 70)
            logger.info("🚀 Step 8: RUNNING COLLECTIVE ANALYSIS")
            logger.info("=" * 70)
            
            metric = await calculator.calculate_accumulation_score(
                token_symbol="ETH",
                whale_limit=20,  # MVP: analyze top 20 whales only
                network="ethereum"
            )
            
            # Step 9: Apply Data Quality Flag (Circuit Breaker Effect)
            # If data quality was DEGRADED, force is_anomaly and add tag
            if force_anomaly_flag:
                metric.is_anomaly = True
                if "[Data Quality Warning]" not in metric.tags:
                    metric.tags.append("[Data Quality Warning]")
                metric.num_signals_excluded = report["summary"]["warnings"]
                logger.warning(f"\n⚠️  Metric flagged as anomaly due to DEGRADED data quality")
            
            # Store validation metrics
            metric.num_signals_used = report["summary"]["checks_passed"]
            
            # Step 10: Display Results
            logger.info("\n" + "=" * 70)
            logger.info("📊 ANALYSIS RESULTS")
            logger.info("=" * 70)
            
            print(f"\n🐋 Whales Analyzed: {metric.whale_count}")
            print(f"📈 Accumulation Score (Native ETH): {metric.accumulation_score:+.2f}%")
            
            if metric.lst_adjusted_score:
                print(f"🔄 LST-Adjusted Score (ETH+WETH+stETH): {metric.lst_adjusted_score:+.2f}%")
            
            print(f"💰 Total Balance Change: {metric.total_balance_change_eth:+,.2f} ETH")
            print(f"📊 Current Total: {metric.total_balance_current_eth:,.2f} ETH")
            print(f"📊 Historical Total: {metric.total_balance_historical_eth:,.2f} ETH")
            
            if metric.total_weth_balance_eth or metric.total_steth_balance_eth:
                print(f"\n🔄 LST Holdings:")
                if metric.total_weth_balance_eth:
                    print(f"  WETH: {metric.total_weth_balance_eth:,.2f} ETH")
                if metric.total_steth_balance_eth:
                    print(f"  stETH: {metric.total_steth_balance_eth:,.2f} ETH (rate: {metric.steth_eth_rate:.4f})")
            
            print(f"\n👥 Whale Behavior:")
            print(f"  ⬆️  Accumulating: {metric.accumulators_count}")
            print(f"  ⬇️  Distributing: {metric.distributors_count}")
            print(f"  ➡️  Neutral: {metric.neutral_count}")
            
            if metric.concentration_gini:
                print(f"\n📊 Statistical Quality:")
                print(f"  Gini Coefficient: {metric.concentration_gini:.4f} (0=equal, 1=concentrated)")
                if metric.is_anomaly:
                    print(f"  ⚠️  ANOMALY DETECTED: {metric.top_anomaly_driver[:10]}...")
            
            if metric.lst_migration_count > 0:
                print(f"\n🔄 LST Migrations Detected: {metric.lst_migration_count}")
            
            if metric.price_change_48h_pct:
                print(f"\n📉 Price Context (48h):")
                print(f"  Change: {metric.price_change_48h_pct:+.2f}%")
            
            if metric.tags:
                print(f"\n🏷️  Smart Tags: {', '.join(f'[{tag}]' for tag in metric.tags)}")
            
            print(f"\n🔢 Block Range:")
            print(f"  Current: {metric.current_block_number:,}")
            print(f"  Historical: {metric.historical_block_number:,}")
            print(f"  Lookback: {metric.lookback_hours}h")
            
            # Data Quality Context
            print(f"\n🛡️  Data Quality:")
            print(f"  Status: {validation_status.value.upper()}")
            print(f"  Score: {validation_score:.1f}/100")
            print(f"  Checks Passed: {report['summary']['checks_passed']}/5")
            
            if validation_status == HealthStatus.DEGRADED:
                print(f"  ⚠️  WARNING: Results may contain noise due to:")
                for check in report["checks"]:
                    if check["status"] == "degraded" and check["issues"]:
                        for issue in check["issues"][:2]:  # Show first 2
                            print(f"    • {issue[:80]}...")
            
            # Interpretation
            print(f"\n💡 Interpretation:")
            if metric.accumulation_score > 2:
                print("  🟢 STRONG ACCUMULATION - Whales are buying aggressively")
            elif metric.accumulation_score > 0.5:
                print("  🟢 ACCUMULATION - Whales are net buyers")
            elif metric.accumulation_score > -0.5:
                print("  🟡 NEUTRAL - No significant whale movement")
            elif metric.accumulation_score > -2:
                print("  🔴 DISTRIBUTION - Whales are net sellers")
            else:
                print("  🔴 STRONG DISTRIBUTION - Whales are selling aggressively")
            
            # Add data quality disclaimer if needed
            if validation_status == HealthStatus.DEGRADED:
                print(f"\n🚨 DATA QUALITY ISSUE DETECTED:")
                print(f"  ⚠️  Manual verification required before posting")
                print(f"  ⚠️  Review validation report above for specific issues")
                print(f"  ⚠️  Consider re-running analysis after fixing data quality")
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ ANALYSIS COMPLETE")
            logger.info("=" * 70)
        
        return metric
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(run_analysis())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)
