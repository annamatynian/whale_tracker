"""
Unit Tests for Simple Whale Watcher
=====================================

Tests for MVP whale monitoring engine.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock
from src.monitors.simple_whale_watcher import SimpleWhaleWatcher
from src.core.web3_manager import Web3Manager
from src.core.whale_config import WhaleConfig, WhaleMetadata, WhaleCategory
from src.analyzers.whale_analyzer import WhaleAnalyzer, AnomalyResult
from src.notifications.telegram_notifier import TelegramNotifier


@pytest.fixture
def mock_web3_manager():
    """Create mock Web3Manager."""
    manager = Mock(spec=Web3Manager)
    manager.get_balance = AsyncMock(return_value=1000.0)
    return manager


@pytest.fixture
def mock_whale_config():
    """Create mock WhaleConfig."""
    config = Mock(spec=WhaleConfig)

    # Mock exchange detection
    config.is_exchange = Mock(return_value=False)

    # Mock metadata
    exchange_metadata = WhaleMetadata(
        address='0xexchange',
        name='Test Exchange',
        category=WhaleCategory.EXCHANGE,
        tags=['exchange']
    )
    config.get_metadata = Mock(return_value=exchange_metadata)

    return config


@pytest.fixture
def mock_analyzer():
    """Create mock WhaleAnalyzer."""
    analyzer = Mock(spec=WhaleAnalyzer)

    # Mock anomaly detection
    anomaly = AnomalyResult(
        is_anomaly=False,
        current_amount=100000.0,
        average_amount=100000.0,
        threshold=130000.0,
        multiplier=1.3,
        confidence=50.0,
        reason="Within normal range"
    )
    analyzer.detect_anomaly = Mock(return_value=anomaly)
    analyzer.add_transaction = Mock()

    return analyzer


@pytest.fixture
def mock_notifier():
    """Create mock TelegramNotifier."""
    notifier = Mock(spec=TelegramNotifier)
    notifier.send_whale_direct_transfer_alert = AsyncMock(return_value=True)
    notifier.send_whale_onehop_alert = AsyncMock(return_value=True)
    return notifier


@pytest.fixture
def mock_settings():
    """Create mock Settings."""
    settings = Mock()
    settings.MIN_AMOUNT_USD = 100000.0
    settings.WHALE_ADDRESSES = ['0xwhale1', '0xwhale2']

    # Mock whale monitoring config
    whale_monitoring = Mock()
    whale_monitoring.intervals = Mock()
    whale_monitoring.intervals.alert_cooldown_minutes = 60
    whale_monitoring.intervals.onehop_check_hours = 2
    settings.whale_monitoring = whale_monitoring

    return settings


@pytest.fixture
def watcher(mock_web3_manager, mock_whale_config, mock_analyzer, mock_notifier, mock_settings):
    """Create SimpleWhaleWatcher with mocked dependencies."""
    return SimpleWhaleWatcher(
        web3_manager=mock_web3_manager,
        whale_config=mock_whale_config,
        analyzer=mock_analyzer,
        notifier=mock_notifier,
        settings=mock_settings
    )


class TestInitialization:
    """Test SimpleWhaleWatcher initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        watcher = SimpleWhaleWatcher()

        assert watcher.web3_manager is not None
        assert watcher.whale_config is not None
        assert watcher.analyzer is not None
        assert watcher.notifier is not None
        assert watcher.settings is not None
        assert len(watcher.last_balances) == 0
        assert len(watcher.last_alerts) == 0

    def test_init_with_custom_components(
        self, mock_web3_manager, mock_whale_config, mock_analyzer, mock_notifier, mock_settings
    ):
        """Test initialization with custom components."""
        watcher = SimpleWhaleWatcher(
            web3_manager=mock_web3_manager,
            whale_config=mock_whale_config,
            analyzer=mock_analyzer,
            notifier=mock_notifier,
            settings=mock_settings
        )

        assert watcher.web3_manager is mock_web3_manager
        assert watcher.whale_config is mock_whale_config
        assert watcher.analyzer is mock_analyzer
        assert watcher.notifier is mock_notifier
        assert watcher.settings is mock_settings


class TestCheckWhale:
    """Test individual whale checking."""

    @pytest.mark.asyncio
    async def test_check_whale_first_time(self, watcher, mock_web3_manager):
        """Test checking whale for the first time (initialization)."""
        whale_address = "0xwhale1"
        mock_web3_manager.get_balance.return_value = 1000.0

        result = await watcher.check_whale(whale_address)

        assert result['status'] == 'initialized'
        assert result['balance'] == 1000.0
        assert whale_address in watcher.last_balances
        assert watcher.last_balances[whale_address] == 1000.0

    @pytest.mark.asyncio
    async def test_check_whale_no_significant_change(self, watcher, mock_web3_manager):
        """Test checking whale with insignificant balance change."""
        whale_address = "0xwhale1"

        # Set initial balance
        watcher.last_balances[whale_address] = 1000.0

        # New balance (small decrease)
        mock_web3_manager.get_balance.return_value = 999.0

        result = await watcher.check_whale(whale_address)

        assert result['status'] == 'no_significant_change'
        assert result['balance_change'] == 1.0

    @pytest.mark.asyncio
    async def test_check_whale_balance_increase(self, watcher, mock_web3_manager):
        """Test checking whale with balance increase (no alert)."""
        whale_address = "0xwhale1"

        # Set initial balance
        watcher.last_balances[whale_address] = 1000.0

        # New balance (increased)
        mock_web3_manager.get_balance.return_value = 1500.0

        result = await watcher.check_whale(whale_address)

        assert result['status'] == 'no_significant_change'
        # Balance change is negative (increased)
        assert result['balance_change'] == -500.0

    @pytest.mark.asyncio
    async def test_check_whale_error_handling(self, watcher, mock_web3_manager):
        """Test error handling when checking whale."""
        whale_address = "0xwhale1"

        # Simulate error
        mock_web3_manager.get_balance.side_effect = Exception("Network error")

        result = await watcher.check_whale(whale_address)

        assert result['status'] == 'error'
        assert 'error' in result
        assert 'Network error' in result['error']


class TestGetRecentTransactions:
    """Test transaction fetching."""

    @pytest.mark.asyncio
    async def test_get_recent_transactions_stub(self, watcher):
        """Test that get_recent_transactions returns empty list (MVP stub)."""
        result = await watcher._get_recent_transactions("0xwhale1", limit=10)

        # MVP implementation returns empty list
        assert result == []


class TestDirectDumpDetection:
    """Test direct dump detection (whale → exchange)."""

    @pytest.mark.asyncio
    async def test_direct_dump_not_to_exchange(self, watcher, mock_whale_config):
        """Test transaction not going to exchange (no alert)."""
        mock_whale_config.is_exchange.return_value = False

        tx = {
            'to': '0xrandom',
            'value': 100 * 1e18,  # 100 ETH
            'hash': '0xabc123'
        }

        result = await watcher._check_direct_dump("0xwhale1", tx)

        assert result is None

    @pytest.mark.asyncio
    async def test_direct_dump_below_threshold(self, watcher, mock_whale_config, mock_settings):
        """Test dump below minimum threshold (no alert)."""
        mock_whale_config.is_exchange.return_value = True
        mock_settings.MIN_AMOUNT_USD = 500000.0  # $500k threshold

        tx = {
            'to': '0xexchange',
            'value': 10 * 1e18,  # 10 ETH = ~$35k (below threshold)
            'hash': '0xabc123'
        }

        result = await watcher._check_direct_dump("0xwhale1", tx)

        assert result is None

    @pytest.mark.asyncio
    async def test_direct_dump_detected(self, watcher, mock_whale_config, mock_notifier):
        """Test successful direct dump detection."""
        mock_whale_config.is_exchange.return_value = True

        tx = {
            'to': '0xexchange',
            'value': 100 * 1e18,  # 100 ETH = ~$350k
            'hash': '0xabc123'
        }

        result = await watcher._check_direct_dump("0xwhale1", tx)

        assert result is not None
        assert result['type'] == 'direct_dump'
        assert result['whale_address'] == "0xwhale1"
        assert result['amount_eth'] == 100.0
        assert result['tx_hash'] == '0xabc123'

        # Verify notification was sent
        assert mock_notifier.send_whale_direct_transfer_alert.called

        # Verify last alert time was updated
        assert "0xwhale1" in watcher.last_alerts

    @pytest.mark.asyncio
    async def test_direct_dump_cooldown(self, watcher, mock_whale_config):
        """Test that cooldown prevents duplicate alerts."""
        mock_whale_config.is_exchange.return_value = True

        # Set last alert time to now
        watcher.last_alerts["0xwhale1"] = datetime.now()

        tx = {
            'to': '0xexchange',
            'value': 100 * 1e18,
            'hash': '0xabc123'
        }

        result = await watcher._check_direct_dump("0xwhale1", tx)

        # Should return None due to cooldown
        assert result is None


class TestSimpleOneHopDetection:
    """Test simple one-hop detection."""

    @pytest.mark.asyncio
    async def test_one_hop_known_destination(self, watcher):
        """Test one-hop with known destination (no alert)."""
        # Mock classify_address to return known address
        watcher.whale_config.is_exchange = Mock(return_value=False)

        tx = {
            'to': '0xknown_defi',
            'value': 100 * 1e18,
            'hash': '0xabc123',
            'timestamp': datetime.now()
        }

        # This should return None because destination is not truly "unknown"
        # (In real code, classify_address would show it's a known DeFi protocol)
        # For MVP, we skip this test as implementation is stubbed

        result = await watcher._check_simple_one_hop("0xwhale1", tx)

        # MVP returns None because get_recent_transactions returns []
        assert result is None

    @pytest.mark.asyncio
    async def test_one_hop_no_intermediate_transactions(self, watcher):
        """Test one-hop when intermediate has no transactions."""
        tx = {
            'to': '0xintermediate',
            'value': 100 * 1e18,
            'hash': '0xabc123',
            'timestamp': datetime.now()
        }

        # Mock to return no intermediate transactions
        watcher._get_recent_transactions = AsyncMock(return_value=[])

        result = await watcher._check_simple_one_hop("0xwhale1", tx)

        assert result is None


class TestAlertCooldown:
    """Test alert cooldown management."""

    def test_can_send_alert_no_previous(self, watcher):
        """Test can send alert when no previous alerts."""
        result = watcher._can_send_alert("0xwhale1")

        assert result is True

    def test_can_send_alert_cooldown_active(self, watcher):
        """Test cannot send alert during cooldown period."""
        # Set last alert to 30 minutes ago (cooldown is 60 min)
        watcher.last_alerts["0xwhale1"] = datetime.now() - timedelta(minutes=30)

        result = watcher._can_send_alert("0xwhale1")

        assert result is False

    def test_can_send_alert_cooldown_expired(self, watcher):
        """Test can send alert after cooldown expires."""
        # Set last alert to 90 minutes ago (cooldown is 60 min)
        watcher.last_alerts["0xwhale1"] = datetime.now() - timedelta(minutes=90)

        result = watcher._can_send_alert("0xwhale1")

        assert result is True


class TestMonitorAllWhales:
    """Test monitoring all configured whales."""

    @pytest.mark.asyncio
    async def test_monitor_all_whales_no_config(self, watcher, mock_settings):
        """Test monitoring when no whales configured."""
        mock_settings.WHALE_ADDRESSES = []

        result = await watcher.monitor_all_whales()

        assert result['status'] == 'no_whales_configured'

    @pytest.mark.asyncio
    async def test_monitor_all_whales_success(self, watcher, mock_web3_manager, mock_settings):
        """Test successful monitoring of multiple whales."""
        mock_settings.WHALE_ADDRESSES = ['0xwhale1', '0xwhale2']
        mock_web3_manager.get_balance.return_value = 1000.0

        result = await watcher.monitor_all_whales()

        assert result['status'] == 'completed'
        assert result['whales_checked'] == 2
        assert 'results' in result
        assert len(result['results']) == 2
        assert 'timestamp' in result


class TestIntegration:
    """Integration tests with real (non-mocked) components."""

    def test_create_watcher_with_real_components(self):
        """Test creating watcher with real components."""
        # This tests that all components can be instantiated together
        watcher = SimpleWhaleWatcher()

        assert watcher.web3_manager is not None
        assert watcher.whale_config is not None
        assert watcher.analyzer is not None
        assert watcher.notifier is not None
        assert watcher.settings is not None
