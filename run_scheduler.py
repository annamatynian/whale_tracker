"""
Automated Schedulers - Data Quality Monitor & Whale Analysis

Two independent processes:
1. Data Quality Monitor - Hourly health checks
2. Whale Analysis - 6-hour market signals (only if data healthy)
"""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env

from data_quality_validator import DataQualityValidator, HealthStatus
from src.notifications.telegram_notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Telegram from env
ENABLE_TELEGRAM = os.getenv('ENABLE_TELEGRAM', 'False').lower() == 'true'
if ENABLE_TELEGRAM:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
else:
    telegram = None

# Database setup
db_url = (
    f"postgresql+asyncpg://"
    f"{os.getenv('DB_USER', 'postgres')}:"
    f"{os.getenv('DB_PASSWORD', 'Jayaasiri2185')}@"
    f"{os.getenv('DB_HOST', 'localhost')}:"
    f"{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'whale_tracker')}"
)
engine = create_async_engine(db_url, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ========================================
# JOB 1: DATA QUALITY MONITOR (Hourly)
# ========================================

async def data_quality_check():
    """
    Hourly data quality monitoring.
    
    Sends Telegram alert ONLY if:
    - CRITICAL: Immediate alert with actionable steps
    - DEGRADED: Warning with issue count
    - HEALTHY: Silent (no spam)
    """
    logger.info("=" * 60)
    logger.info("🛡️  DATA QUALITY CHECK - STARTING")
    logger.info("=" * 60)
    
    try:
        async with async_session_factory() as session:
            validator = DataQualityValidator(session)
            report = await validator.run_all_checks()
            
            status = HealthStatus(report["overall_status"])
            score = report["overall_score"]
            
            logger.info(f"Status: {status.value.upper()} | Score: {score:.1f}/100")
            
            # Send alert if NOT healthy
            if status == HealthStatus.CRITICAL and telegram:
                # Find primary issue
                primary_issue = "Unknown"
                for check in report["checks"]:
                    if check["status"] == "critical" and check["issues"]:
                        primary_issue = check["issues"][0][:100]
                        break
                
                alert = (
                    "🚨 <b>DATA QUALITY ALERT</b>\\n\\n"
                    f"📊 Score: {score:.1f}/100\\n"
                    f"❌ Issues: {report['summary']['critical_issues']}\\n\\n"
                    f"<b>Primary:</b>\\n{primary_issue}\\n\\n"
                    "<b>Action:</b>\\n"
                    "<code>python run_manual_snapshot.py</code>"
                )
                await telegram.send_alert(alert)
                logger.warning("⚠️  Alert sent to Telegram")
                
            elif status == HealthStatus.DEGRADED and telegram:
                alert = (
                    "⚠️ <b>DATA QUALITY WARNING</b>\\n\\n"
                    f"📊 Score: {score:.1f}/100\\n"
                    f"⚠️ Warnings: {report['summary']['warnings']}\\n\\n"
                    "Analysis will continue with reduced confidence."
                )
                await telegram.send_alert(alert)
                logger.warning("⚠️  Warning sent to Telegram")
            
            else:
                logger.info("✅ Data quality HEALTHY - no alert needed")
                
    except Exception as e:
        logger.error(f"❌ Quality check failed: {e}", exc_info=True)
        if telegram:
            await telegram.send_alert(
                f"🚨 <b>QUALITY CHECK CRASHED</b>\\n\\nError: {str(e)[:200]}"
            )


# ========================================
# JOB 2: WHALE ANALYSIS (Every 6 hours)
# ========================================

async def whale_analysis():
    """
    Run collective whale analysis every 6 hours.
    
    Only executes if data quality is HEALTHY.
    Sends market signal summary to Telegram.
    """
    logger.info("=" * 60)
    logger.info("🐋 WHALE ANALYSIS - STARTING")
    logger.info("=" * 60)
    
    try:
        async with async_session_factory() as session:
            # Step 0: Quality gate
            validator = DataQualityValidator(session)
            report = await validator.run_all_checks()
            
            status = HealthStatus(report["overall_status"])
            
            if status == HealthStatus.CRITICAL:
                logger.error("⛔ Analysis SKIPPED - Data quality CRITICAL")
                return
            
            # Step 1: Run analysis
            from run_collective_analysis import run_analysis
            metric = await run_analysis()
            
            if not metric:
                logger.error("❌ Analysis returned None")
                return
            
            # Step 2: Send summary
            if telegram:
                # Determine signal
                if metric.accumulation_score > 2:
                    signal = "🟢 STRONG ACCUMULATION"
                    emoji = "📈"
                elif metric.accumulation_score > 0.5:
                    signal = "🟢 ACCUMULATION"
                    emoji = "📊"
                elif metric.accumulation_score > -0.5:
                    signal = "🟡 NEUTRAL"
                    emoji = "➡️"
                elif metric.accumulation_score > -2:
                    signal = "🔴 DISTRIBUTION"
                    emoji = "📉"
                else:
                    signal = "🔴 STRONG DISTRIBUTION"
                    emoji = "⚠️"
                
                alert = (
                    f"{emoji} <b>WHALE ANALYSIS UPDATE</b>\\n\\n"
                    f"<b>Signal:</b> {signal}\\n"
                    f"📊 Score: {metric.accumulation_score:+.2f}%\\n"
                    f"🐋 Whales: {metric.whale_count}\\n\\n"
                    f"⬆️ Accumulating: {metric.accumulators_count}\\n"
                    f"⬇️ Distributing: {metric.distributors_count}\\n"
                    f"➡️ Neutral: {metric.neutral_count}\\n\\n"
                )
                
                # Add LST-adjusted if available
                if metric.lst_adjusted_score:
                    alert += f"🔄 LST-Adjusted: {metric.lst_adjusted_score:+.2f}%\\n"
                
                # Add tags if any
                if metric.tags:
                    alert += f"\\n🏷️ Tags: {', '.join(metric.tags)}"
                
                await telegram.send_alert(alert)
                logger.info("✅ Analysis summary sent to Telegram")
            
            logger.info(f"✅ Analysis complete: {metric.accumulation_score:+.2f}%")
            
    except Exception as e:
        logger.error(f"❌ Whale analysis failed: {e}", exc_info=True)
        if telegram:
            await telegram.send_alert(
                f"🚨 <b>WHALE ANALYSIS CRASHED</b>\\n\\nError: {str(e)[:200]}"
            )


# ========================================
# SCHEDULER SETUP
# ========================================

def start_scheduler():
    """Start both scheduled jobs"""
    scheduler = AsyncIOScheduler()
    
    # Get intervals from env (default: 1h and 6h)
    quality_interval = int(os.getenv('QUALITY_CHECK_INTERVAL', '1'))
    analysis_interval = int(os.getenv('WHALE_ANALYSIS_INTERVAL', '6'))
    
    # Job 1: Data Quality Monitor
    scheduler.add_job(
        data_quality_check,
        trigger=IntervalTrigger(hours=quality_interval),
        id='data_quality_monitor',
        name='Data Quality Monitor',
        replace_existing=True
    )
    
    # Job 2: Whale Analysis
    scheduler.add_job(
        whale_analysis,
        trigger=IntervalTrigger(hours=analysis_interval),
        id='whale_analysis',
        name='Whale Analysis',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("=" * 60)
    logger.info("🚀 SCHEDULER STARTED")
    logger.info("=" * 60)
    logger.info(f"📅 Data Quality Monitor: Every {quality_interval} hour(s)")
    logger.info(f"📅 Whale Analysis: Every {analysis_interval} hour(s)")
    logger.info("=" * 60)
    
    return scheduler


# ========================================
# MAIN
# ========================================

async def main():
    """Run scheduler in background"""
    scheduler = start_scheduler()
    
    # Run first checks immediately
    logger.info("🔥 Running initial checks...")
    await data_quality_check()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep 1 hour
    except KeyboardInterrupt:
        logger.info("⚠️  Shutting down scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
