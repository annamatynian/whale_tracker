"""
Unit tests for NonceTracker (Signal #3)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import aiohttp

from src.analyzers.nonce_tracker import NonceTracker, NonceCorrelationResult


class TestNonceTrackerInitialization:
    """Test NonceTracker initialization"""

    def test_init_default(self):
        """Test initialization with defaults"""
        tracker = NonceTracker()
        assert tracker.web3_manager is None
        assert tracker.etherscan_api_key is None
        assert tracker.use_etherscan is False

    def test_init_with_etherscan(self):
        """Test initialization with Etherscan API key"""
        tracker = NonceTracker(etherscan_api_key='test_key')
        assert tracker.etherscan_api_key == 'test_key'
        assert tracker.use_etherscan is True

    def test_init_with_web3(self):
        """Test initialization with Web3Manager"""
        mock_web3 = Mock()
        tracker = NonceTracker(web3_manager=mock_web3)
        assert tracker.web3_manager is mock_web3


class TestNonceSequenceChecking:
    """Test nonce sequence detection"""

    @pytest.mark.asyncio
    async def test_nonce_gap_1_strongest_signal(self):
        """Test nonce gap of 1 - STRONGEST signal (95% confidence)"""
        tracker = NonceTracker()
        tracker._get_nonce_at_block = AsyncMock(return_value=5)

        whale_tx = {
            'blockNumber': 18000000,
            'to': '0xIntermediate',
            'nonce': 100
        }

        intermediate_tx = {
            'nonce': 6,  # Gap = 6 - 5 = 1
            'from': '0xIntermediate'
        }

        result = await tracker.check_nonce_sequence(whale_tx, intermediate_tx)

        assert result.match is True
        assert result.confidence == 95
        assert result.nonce_gap == 1
        assert result.signal_strength == 'STRONGEST'
        assert 'immediate' in result.details.lower()

    @pytest.mark.asyncio
    async def test_nonce_gap_2_strong_signal(self):
        """Test nonce gap of 2-3 - STRONG signal (75% confidence)"""
        tracker = NonceTracker()
        tracker._get_nonce_at_block = AsyncMock(return_value=10)

        whale_tx = {
            'blockNumber': 18000000,
            'to': '0xIntermediate'
        }

        intermediate_tx = {
            'nonce': 12,  # Gap = 12 - 10 = 2
            'from': '0xIntermediate'
        }

        result = await tracker.check_nonce_sequence(whale_tx, intermediate_tx)

        assert result.match is True
        assert result.confidence == 75
        assert result.nonce_gap == 2
        assert result.signal_strength == 'STRONG'

    @pytest.mark.asyncio
    async def test_nonce_gap_3_strong_signal(self):
        """Test nonce gap of 3 - still STRONG signal"""
        tracker = NonceTracker()
        tracker._get_nonce_at_block = AsyncMock(return_value=10)

        whale_tx = {
            'blockNumber': 18000000,
            'to': '0xIntermediate'
        }

        intermediate_tx = {
            'nonce': 13,  # Gap = 13 - 10 = 3
            'from': '0xIntermediate'
        }

        result = await tracker.check_nonce_sequence(whale_tx, intermediate_tx)

        assert result.match is True
        assert result.confidence == 75
        assert result.nonce_gap == 3
        assert result.signal_strength == 'STRONG'

    @pytest.mark.asyncio
    async def test_nonce_gap_5_weak_signal(self):
        """Test nonce gap of 5 - WEAK signal (40% confidence)"""
        tracker = NonceTracker()
        tracker._get_nonce_at_block = AsyncMock(return_value=10)

        whale_tx = {
            'blockNumber': 18000000,
            'to': '0xIntermediate'
        }

        intermediate_tx = {
            'nonce': 15,  # Gap = 15 - 10 = 5
            'from': '0xIntermediate'
        }

        result = await tracker.check_nonce_sequence(whale_tx, intermediate_tx)

        assert result.match is True
        assert result.confidence == 40
        assert result.nonce_gap == 5
        assert result.signal_strength == 'WEAK'

    @pytest.mark.asyncio
    async def test_nonce_gap_large_no_match(self):
        """Test large nonce gap - NO match"""
        tracker = NonceTracker()
        tracker._get_nonce_at_block = AsyncMock(return_value=10)

        whale_tx = {
            'blockNumber': 18000000,
            'to': '0xIntermediate'
        }

        intermediate_tx = {
            'nonce': 25,  # Gap = 25 - 10 = 15 (too large)
            'from': '0xIntermediate'
        }

        result = await tracker.check_nonce_sequence(whale_tx, intermediate_tx)

        assert result.match is False
        assert result.confidence == 0
        assert result.nonce_gap == 15
        assert result.signal_strength == 'NONE'

    @pytest.mark.asyncio
    async def test_missing_whale_tx_fields(self):
        """Test handling of missing whale_tx fields"""
        tracker = NonceTracker()

        whale_tx = {}  # Missing 'to' and 'blockNumber'
        intermediate_tx = {'nonce': 5}

        result = await tracker.check_nonce_sequence(whale_tx, intermediate_tx)

        assert result.match is False
        assert result.confidence == 0
        assert 'Missing whale_tx fields' in result.details

    @pytest.mark.asyncio
    async def test_missing_intermediate_nonce(self):
        """Test handling of missing intermediate nonce"""
        tracker = NonceTracker()
        tracker._get_nonce_at_block = AsyncMock(return_value=5)

        whale_tx = {
            'blockNumber': 18000000,
            'to': '0xIntermediate'
        }

        intermediate_tx = {}  # Missing 'nonce'

        result = await tracker.check_nonce_sequence(whale_tx, intermediate_tx)

        assert result.match is False
        assert result.confidence == 0
        assert 'missing nonce' in result.details.lower()

    @pytest.mark.asyncio
    async def test_nonce_retrieval_failure(self):
        """Test handling when nonce cannot be retrieved"""
        tracker = NonceTracker()
        tracker._get_nonce_at_block = AsyncMock(return_value=None)

        whale_tx = {
            'blockNumber': 18000000,
            'to': '0xIntermediate'
        }

        intermediate_tx = {'nonce': 5}

        result = await tracker.check_nonce_sequence(whale_tx, intermediate_tx)

        assert result.match is False
        assert result.confidence == 0


class TestEtherscanNonceRetrieval:
    """Test nonce retrieval via Etherscan API"""

    @pytest.mark.asyncio
    async def test_etherscan_success(self):
        """Test successful nonce retrieval from Etherscan"""
        tracker = NonceTracker(etherscan_api_key='test_key')

        # Mock aiohttp response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'status': '1',
            'result': '0x5'  # Nonce = 5
        })

        mock_get = AsyncMock()
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_session = Mock()
        mock_session.get = Mock(return_value=mock_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            nonce = await tracker._get_nonce_via_etherscan('0xAddress', 18000000)

        assert nonce == 5

    @pytest.mark.asyncio
    async def test_etherscan_api_error(self):
        """Test Etherscan API error handling"""
        tracker = NonceTracker(etherscan_api_key='test_key')

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'status': '0',
            'message': 'NOTOK',
            'result': 'Error message'
        })

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            nonce = await tracker._get_nonce_via_etherscan('0xAddress', 18000000)

        assert nonce is None

    @pytest.mark.asyncio
    async def test_etherscan_http_error(self):
        """Test Etherscan HTTP error"""
        tracker = NonceTracker(etherscan_api_key='test_key')

        mock_response = AsyncMock()
        mock_response.status = 500

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            nonce = await tracker._get_nonce_via_etherscan('0xAddress', 18000000)

        assert nonce is None

    @pytest.mark.asyncio
    async def test_etherscan_timeout(self):
        """Test Etherscan timeout handling"""
        tracker = NonceTracker(etherscan_api_key='test_key')

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = aiohttp.ClientError()

            nonce = await tracker._get_nonce_via_etherscan('0xAddress', 18000000)

        assert nonce is None


class TestRPCNonceRetrieval:
    """Test nonce retrieval via RPC"""

    @pytest.mark.asyncio
    async def test_rpc_success(self):
        """Test successful nonce retrieval via RPC"""
        test_address = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'  # Valid Ethereum address

        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 5
        mock_web3_manager.w3 = mock_web3

        tracker = NonceTracker(web3_manager=mock_web3_manager)

        nonce = await tracker._get_nonce_via_rpc(test_address, 18000000)

        assert nonce == 5
        mock_web3.eth.get_transaction_count.assert_called_once()

    @pytest.mark.asyncio
    async def test_rpc_no_web3_manager(self):
        """Test RPC when no Web3Manager available"""
        tracker = NonceTracker()

        nonce = await tracker._get_nonce_via_rpc('0xAddress', 18000000)

        assert nonce is None

    @pytest.mark.asyncio
    async def test_rpc_error(self):
        """Test RPC error handling"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.side_effect = Exception("RPC error")
        mock_web3_manager.w3 = mock_web3

        tracker = NonceTracker(web3_manager=mock_web3_manager)

        nonce = await tracker._get_nonce_via_rpc('0xAddress', 18000000)

        assert nonce is None


class TestNonceFallback:
    """Test fallback between Etherscan and RPC"""

    @pytest.mark.asyncio
    async def test_etherscan_primary_success(self):
        """Test Etherscan as primary source"""
        mock_web3_manager = Mock()
        tracker = NonceTracker(
            web3_manager=mock_web3_manager,
            etherscan_api_key='test_key'
        )

        tracker._get_nonce_via_etherscan = AsyncMock(return_value=5)
        tracker._get_nonce_via_rpc = AsyncMock(return_value=5)

        nonce = await tracker._get_nonce_at_block('0xAddress', 18000000)

        assert nonce == 5
        # Should use Etherscan, not call RPC
        tracker._get_nonce_via_etherscan.assert_called_once()
        tracker._get_nonce_via_rpc.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_to_rpc(self):
        """Test fallback to RPC when Etherscan fails"""
        mock_web3_manager = Mock()
        tracker = NonceTracker(
            web3_manager=mock_web3_manager,
            etherscan_api_key='test_key'
        )

        tracker._get_nonce_via_etherscan = AsyncMock(return_value=None)
        tracker._get_nonce_via_rpc = AsyncMock(return_value=5)

        nonce = await tracker._get_nonce_at_block('0xAddress', 18000000)

        assert nonce == 5
        tracker._get_nonce_via_etherscan.assert_called_once()
        tracker._get_nonce_via_rpc.assert_called_once()

    @pytest.mark.asyncio
    async def test_both_methods_fail(self):
        """Test when both Etherscan and RPC fail"""
        mock_web3_manager = Mock()
        tracker = NonceTracker(
            web3_manager=mock_web3_manager,
            etherscan_api_key='test_key'
        )

        tracker._get_nonce_via_etherscan = AsyncMock(return_value=None)
        tracker._get_nonce_via_rpc = AsyncMock(return_value=None)

        nonce = await tracker._get_nonce_at_block('0xAddress', 18000000)

        assert nonce is None


class TestConfidenceCalculation:
    """Test confidence score calculation"""

    def test_confidence_gap_1(self):
        """Test confidence for gap = 1"""
        tracker = NonceTracker()
        assert tracker.calculate_confidence_from_gap(1) == 95

    def test_confidence_gap_2(self):
        """Test confidence for gap = 2"""
        tracker = NonceTracker()
        assert tracker.calculate_confidence_from_gap(2) == 75

    def test_confidence_gap_3(self):
        """Test confidence for gap = 3"""
        tracker = NonceTracker()
        assert tracker.calculate_confidence_from_gap(3) == 75

    def test_confidence_gap_5(self):
        """Test confidence for gap = 5"""
        tracker = NonceTracker()
        assert tracker.calculate_confidence_from_gap(5) == 40

    def test_confidence_gap_10(self):
        """Test confidence for gap = 10"""
        tracker = NonceTracker()
        assert tracker.calculate_confidence_from_gap(10) == 40

    def test_confidence_gap_large(self):
        """Test confidence for large gap"""
        tracker = NonceTracker()
        assert tracker.calculate_confidence_from_gap(15) == 0
        assert tracker.calculate_confidence_from_gap(100) == 0
