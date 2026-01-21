"""
Example: Integrating Data Quality Validator into Main Monitoring Loop

This script shows how to integrate periodic data quality checks
into your existing Whale Tracker monitoring system.

WHY: Automated validation prevents corrupted data from triggering
     false alerts to traders.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Import validator
from data_quality_validator import DataQualityValidator, HealthStatus

# Import existing infrastructure
from models.db_connection import get_session
from src.notifications.telegram_notifier import TelegramNotifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class MonitoringOrchestrator:
    """
    Main monitoring orchestrator with integrated data quality checks.
    
    Combines:
    - Whale balance monitoring (hourly)
    - Accumulation score calculation (every 6h)
    - Data quality validation (every 6h)
    - Alert delivery (real-time)
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.telegram = TelegramNotifier()
        self.last_validation_status = HealthStatus.HEALTHY
        
    async def start(self):
        """Start all monitoring jobs"""
        logger.info("🚀 Starting Whale Tracker Monitoring System...")
        
        # Schedule data quality validation (every 6 hours)
        self.scheduler.add_job(
            self.validate_data_quality,
            'interval',
            hours=6,
            id='data_quality_check',
            next_run_time=datetime.now(timezone.utc)  # Run immediately on startup
        )
        
        # Schedule accumulation analysis (every 6 hours, offset by 30min)
        self.scheduler.add_job(
            self.analyze_whale_accumulation,
            'interval',
            hours=6,
            id='accumulation_analysis',
            next_run_time=datetime.now(timezone.utc)
        )
        
        self.scheduler.start()
        logger.info("✅ All monitoring jobs scheduled")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Shutting down gracefully...")
            self.scheduler.shutdown()
    
    async def validate_data_quality(self):
        """
        Run data quality validation and alert if issues detected.
        
        This job runs BEFORE accumulation analysis to ensure we're
        not calculating scores on corrupted data.
        """
        logger.info("🔍 Running scheduled data quality validation...")
        
        try:
            async with get_session() as session:
                validator = DataQualityValidator(session)
                report = await validator.run_all_checks()
                
                current_status = HealthStatus(report["overall_status"])
                score = report["overall_score"]
                
                # Log results
                logger.info(
                    f"Data Quality: {current_status.value.upper()} "
                    f"(Score: {score:.1f}/100)"
                )
                
                # Alert on status change
                if current_status != self.last_validation_status:
                    await self._send_status_change_alert(
                        old_status=self.last_validation_status,
                        new_status=current_status,
                        report=report
                    )
                    self.last_validation_status = current_status
                
                # Always alert on CRITICAL
                elif current_status == HealthStatus.CRITICAL:
                    await self._send_critical_data_alert(report)
                
                # Store report for dashboard
                await self._store_validation_report(report)
                
        except Exception as e:
            logger.error(f"❌ Data quality validation failed: {e}")
            await self.telegram.send_admin_alert(
                f"🚨 DATA VALIDATION CRASHED\n\nError: {str(e)}"
            )
    
    async def analyze_whale_accumulation(self):
        """
        Run whale accumulation analysis (only if data quality OK).
        
        This job is GATED by data quality status - if data is CRITICAL,
        we skip analysis to prevent false signals.
        """
        logger.info("🐋 Running whale accumulation analysis...")
        
        # GATE: Only run if data quality is acceptable
        if self.last_validation_status == HealthStatus.CRITICAL:
            logger.warning(
                "⚠️  SKIPPING accumulation analysis - data quality CRITICAL"
            )
            await self.telegram.send_admin_alert(
                "⚠️ Accumulation analysis SKIPPED\n"
                "Reason: Data quality in CRITICAL state\n"
                "Action: Fix data issues before resuming analysis"
            )
            return
        
        # TODO: Your existing accumulation analysis logic here
        # from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator
        # calculator = AccumulationScoreCalculator(...)
        # result = await calculator.calculate_collective_score()
        
        logger.info("✅ Accumulation analysis complete")
    
    async def _send_status_change_alert(
        self,
        old_status: HealthStatus,
        new_status: HealthStatus,
        report: dict
    ):
        """Send Telegram alert when data quality status changes"""
        
        # Emoji mapping
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.CRITICAL: "🚨"
        }
        
        message = (
            f"{status_emoji[new_status]} DATA QUALITY STATUS CHANGE\n\n"
            f"Previous: {old_status.value.upper()}\n"
            f"Current: {new_status.value.upper()}\n"
            f"Score: {report['overall_score']:.1f}/100\n\n"
            f"Issues Detected: {report['summary']['total_issues']}\n"
            f"Critical: {report['summary']['critical_issues']}\n"
            f"Warnings: {report['summary']['warnings']}\n\n"
        )
        
        # Add top issues
        if report['summary']['total_issues'] > 0:
            message += "Top Issues:\n"
            issue_count = 0
            for check in report['checks']:
                if check['issues']:
                    for issue in check['issues'][:2]:  # First 2 issues per check
                        message += f"• {issue}\n"
                        issue_count += 1
                        if issue_count >= 5:  # Max 5 total
                            break
                    if issue_count >= 5:
                        break
        
        await self.telegram.send_admin_alert(message)
    
    async def _send_critical_data_alert(self, report: dict):
        """Send urgent alert for CRITICAL data quality issues"""
        
        message = (
            "🚨 CRITICAL DATA QUALITY ALERT 🚨\n\n"
            f"Score: {report['overall_score']:.1f}/100\n"
            f"Critical Issues: {report['summary']['critical_issues']}\n\n"
            "⚠️  ACCUMULATION ANALYSIS SUSPENDED\n\n"
            "Action Required:\n"
            "1. Review data_quality.log\n"
            "2. Check RPC provider health\n"
            "3. Verify database integrity\n"
            "4. Re-run snapshots if needed\n"
        )
        
        await self.telegram.send_admin_alert(message, priority="high")
    
    async def _store_validation_report(self, report: dict):
        """
        Store validation report for historical tracking.
        
        This allows dashboard visualization of data quality trends.
        """
        # TODO: Implement storage logic
        # Options:
        # 1. JSON file: logs/data_quality_reports/YYYY-MM-DD_HH-MM.json
        # 2. Database table: CREATE TABLE data_quality_reports (...)
        # 3. Time-series DB: InfluxDB, Prometheus, etc.
        
        import json
        from pathlib import Path
        
        # Simple file storage for now
        report_dir = Path("logs/data_quality_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Validation report saved: {report_path}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    """
    Main entry point for Whale Tracker monitoring system.
    
    Usage:
        python integration_example.py
    """
    orchestrator = MonitoringOrchestrator()
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
