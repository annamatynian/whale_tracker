"""
Unit Tests for Main Orchestrator
==================================

Tests for the main entry point and orchestrator.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from main import WhaleTrackerOrchestrator, setup_logging
from config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock Settings."""
    settings = Mock(spec=Settings)
    settings.LOG_LEVEL = "INFO"
    settings.LOG_TO_FILE = False
    settings.WHALE_ADDRESSES = ['0xwhale1', '0xwhale2']
    settings.CHECK_INTERVAL_MINUTES = 15
    settings.MIN_AMOUNT_USD = 100000.0

    # Mock development settings
    settings.development = Mock()
    settings.development.mock_data = False

    # Mock whale monitoring
    settings.whale_monitoring = Mock()
    settings.whale_monitoring.thresholds = Mock()
    settings.whale_monitoring.thresholds.anomaly_multiplier = 1.3

    return settings


class TestSetupLogging:
    """Test logging configuration."""

    def test_setup_logging_basic(self, mock_settings):
        """Test basic logging setup."""
        # Should not raise exception
        setup_logging(mock_settings)

    def test_setup_logging_with_file(self, mock_settings):
        """Test logging setup with file logging enabled."""
        mock_settings.LOG_TO_FILE = True

        # Should not raise exception (actual file creation is tested in integration)
        setup_logging(mock_settings)


class TestOrchestratorInitialization:
    """Test orchestrator initialization."""

    def test_init_default(self):
        """Test initialization with default settings."""
        orchestrator = WhaleTrackerOrchestrator()

        assert orchestrator.settings is not None
        assert orchestrator.web3_manager is None  # Not initialized yet
        assert orchestrator.watcher is None
        assert orchestrator.scheduler is None
        assert orchestrator.shutdown_requested == False

    def test_init_custom_settings(self, mock_settings):
        """Test initialization with custom settings."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        assert orchestrator.settings is mock_settings


class TestComponentSetup:
    """Test component initialization."""

    @patch('main.TelegramNotifier')
    @patch('main.WhaleAnalyzer')
    @patch('main.WhaleConfig')
    @patch('main.Web3Manager')
    @patch('main.SimpleWhaleWatcher')
    def test_setup_success(
        self,
        mock_watcher_class,
        mock_web3_class,
        mock_config_class,
        mock_analyzer_class,
        mock_notifier_class,
        mock_settings
    ):
        """Test successful component setup."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Mock component instances
        mock_web3 = Mock()
        mock_config = Mock()
        mock_config.all_addresses = {'0x123': 'Test'}
        mock_analyzer = Mock()
        mock_notifier = Mock()
        mock_watcher = Mock()

        mock_web3_class.return_value = mock_web3
        mock_config_class.return_value = mock_config
        mock_analyzer_class.return_value = mock_analyzer
        mock_notifier_class.return_value = mock_notifier
        mock_watcher_class.return_value = mock_watcher

        # Run setup
        orchestrator.setup()

        # Verify components created
        assert orchestrator.web3_manager is mock_web3
        assert orchestrator.whale_config is mock_config
        assert orchestrator.analyzer is mock_analyzer
        assert orchestrator.notifier is mock_notifier
        assert orchestrator.watcher is mock_watcher

        # Verify constructors called
        mock_web3_class.assert_called_once()
        mock_config_class.assert_called_once()
        mock_analyzer_class.assert_called_once()
        mock_notifier_class.assert_called_once()
        mock_watcher_class.assert_called_once()

    @patch('main.Web3Manager')
    def test_setup_error_handling(self, mock_web3_class, mock_settings):
        """Test error handling during setup."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Simulate error
        mock_web3_class.side_effect = Exception("Connection error")

        # Should raise exception
        with pytest.raises(Exception, match="Connection error"):
            orchestrator.setup()


class TestMonitoringCycle:
    """Test monitoring cycle execution."""

    @pytest.mark.asyncio
    async def test_run_monitoring_cycle_no_watcher(self, mock_settings):
        """Test monitoring cycle when watcher not initialized."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Run without setup (watcher is None)
        await orchestrator.run_monitoring_cycle()

        # Should log error but not crash

    @pytest.mark.asyncio
    async def test_run_monitoring_cycle_no_whales(self, mock_settings):
        """Test monitoring cycle with no whales configured."""
        mock_settings.WHALE_ADDRESSES = []

        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)
        orchestrator.watcher = Mock()

        await orchestrator.run_monitoring_cycle()

        # Should log warning but not crash
        # Watcher should not be called
        assert not orchestrator.watcher.monitor_all_whales.called

    @pytest.mark.asyncio
    async def test_run_monitoring_cycle_success(self, mock_settings):
        """Test successful monitoring cycle."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Mock watcher
        mock_watcher = Mock()
        mock_watcher.monitor_all_whales = AsyncMock(return_value={
            'status': 'completed',
            'whales_checked': 2,
            'total_alerts': 1,
            'results': []
        })
        orchestrator.watcher = mock_watcher

        await orchestrator.run_monitoring_cycle()

        # Verify watcher was called
        mock_watcher.monitor_all_whales.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_monitoring_cycle_error_handling(self, mock_settings):
        """Test error handling in monitoring cycle."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Mock watcher that raises error
        mock_watcher = Mock()
        mock_watcher.monitor_all_whales = AsyncMock(side_effect=Exception("API error"))
        orchestrator.watcher = mock_watcher

        # Should not crash, just log error
        await orchestrator.run_monitoring_cycle()


class TestScheduler:
    """Test scheduler setup and management."""

    @patch('main.AsyncIOScheduler')
    def test_setup_scheduler(self, mock_scheduler_class, mock_settings):
        """Test scheduler setup."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler

        orchestrator.setup_scheduler()

        # Verify scheduler created
        assert orchestrator.scheduler is mock_scheduler

        # Verify job added
        mock_scheduler.add_job.assert_called_once()

        # Check job configuration
        call_args = mock_scheduler.add_job.call_args
        assert call_args.kwargs['id'] == 'whale_monitoring'
        assert call_args.kwargs['max_instances'] == 1

    @patch('main.AsyncIOScheduler')
    def test_setup_scheduler_error(self, mock_scheduler_class, mock_settings):
        """Test scheduler setup error handling."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Simulate error
        mock_scheduler_class.side_effect = Exception("Scheduler error")

        with pytest.raises(Exception, match="Scheduler error"):
            orchestrator.setup_scheduler()

    def test_start_scheduler_not_initialized(self, mock_settings):
        """Test starting scheduler before initialization."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Scheduler is None
        with pytest.raises(RuntimeError, match="not initialized"):
            orchestrator.start()

    def test_start_scheduler_success(self, mock_settings):
        """Test successful scheduler start."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Mock scheduler
        mock_scheduler = Mock()
        orchestrator.scheduler = mock_scheduler

        orchestrator.start()

        # Verify scheduler started
        mock_scheduler.start.assert_called_once()

    def test_stop_scheduler(self, mock_settings):
        """Test stopping scheduler."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Mock running scheduler
        mock_scheduler = Mock()
        mock_scheduler.running = True
        orchestrator.scheduler = mock_scheduler

        orchestrator.stop()

        # Verify scheduler shutdown
        mock_scheduler.shutdown.assert_called_once_with(wait=True)
        assert orchestrator.shutdown_requested == True

    def test_stop_no_scheduler(self, mock_settings):
        """Test stopping when no scheduler exists."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Should not crash
        orchestrator.stop()

        assert orchestrator.shutdown_requested == True


class TestRunOnce:
    """Test single run functionality."""

    @pytest.mark.asyncio
    async def test_run_once(self, mock_settings):
        """Test running single monitoring cycle."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Mock run_monitoring_cycle
        orchestrator.run_monitoring_cycle = AsyncMock()

        await orchestrator.run_once()

        # Verify monitoring cycle was called
        orchestrator.run_monitoring_cycle.assert_called_once()


class TestSignalHandling:
    """Test signal handling."""

    def test_signal_handler(self, mock_settings):
        """Test signal handler calls stop."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Mock stop method
        orchestrator.stop = Mock()

        # Simulate signal
        import signal
        orchestrator.signal_handler(signal.SIGINT, None)

        # Verify stop was called
        orchestrator.stop.assert_called_once()


class TestIntegration:
    """Integration tests with real components."""

    @patch('main.SimpleWhaleWatcher')
    @patch('main.TelegramNotifier')
    @patch('main.WhaleAnalyzer')
    @patch('main.WhaleConfig')
    @patch('main.Web3Manager')
    def test_full_setup_flow(
        self,
        mock_web3,
        mock_config,
        mock_analyzer,
        mock_notifier,
        mock_watcher,
        mock_settings
    ):
        """Test full setup and initialization flow."""
        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Setup components
        orchestrator.setup()

        # Verify all components initialized
        assert orchestrator.web3_manager is not None
        assert orchestrator.whale_config is not None
        assert orchestrator.analyzer is not None
        assert orchestrator.notifier is not None
        assert orchestrator.watcher is not None
