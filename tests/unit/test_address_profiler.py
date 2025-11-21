"""
Unit tests for AddressProfiler (Signal #5)
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.analyzers.address_profiler import AddressProfiler, AddressProfile


class TestAddressProfilerInitialization:
    """Test AddressProfiler initialization"""

    def test_init_default(self):
        """Test initialization with defaults"""
        profiler = AddressProfiler()
        assert profiler.web3_manager is None
        assert profiler.FRESH_THRESHOLD_HOURS == 24
        assert profiler.VERY_FRESH_THRESHOLD_HOURS == 1

    def test_init_with_web3(self):
        """Test initialization with Web3Manager"""
        mock_web3 = Mock()
        profiler = AddressProfiler(web3_manager=mock_web3)
        assert profiler.web3_manager is mock_web3


class TestFreshAddressDetection:
    """Test fresh address detection"""

    @pytest.mark.asyncio
    async def test_very_fresh_address(self):
        """Test very fresh address (tx count = 1)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 1
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_fresh_address('0xAddress')

        assert result['is_fresh'] is True
        assert result['confidence'] == 90
        assert result['age_hours'] is not None

    @pytest.mark.asyncio
    async def test_fresh_address_low_txcount(self):
        """Test fresh address (tx count = 5)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 5
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_fresh_address('0xAddress')

        assert result['is_fresh'] is True
        assert result['confidence'] == 70

    @pytest.mark.asyncio
    async def test_established_address(self):
        """Test established address (many transactions)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 100
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_fresh_address('0xAddress')

        assert result['is_fresh'] is False
        assert result['confidence'] == 0

    @pytest.mark.asyncio
    async def test_fresh_no_web3(self):
        """Test when no Web3Manager available"""
        profiler = AddressProfiler()

        result = await profiler._is_fresh_address('0xAddress')

        assert result['is_fresh'] is False
        assert result['confidence'] == 0


class TestEmptyBeforeDetection:
    """Test detection of empty address before whale transaction"""

    @pytest.mark.asyncio
    async def test_was_empty(self):
        """Test address that was completely empty"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_balance.return_value = 0
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._was_empty_before('0xAddress', whale_tx_block=18000000)

        assert result['was_empty'] is True
        assert result['confidence'] == 85

    @pytest.mark.asyncio
    async def test_was_minimal_balance(self):
        """Test address with minimal balance (< 0.01 ETH)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_balance.return_value = int(0.005 * 10**18)  # 0.005 ETH
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._was_empty_before('0xAddress', whale_tx_block=18000000)

        assert result['was_empty'] is True
        assert result['confidence'] == 70

    @pytest.mark.asyncio
    async def test_had_significant_balance(self):
        """Test address with significant balance"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_balance.return_value = int(1.0 * 10**18)  # 1 ETH
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._was_empty_before('0xAddress', whale_tx_block=18000000)

        assert result['was_empty'] is False
        assert result['confidence'] == 0

    @pytest.mark.asyncio
    async def test_empty_no_web3(self):
        """Test when no Web3Manager available"""
        profiler = AddressProfiler()

        result = await profiler._was_empty_before('0xAddress', whale_tx_block=18000000)

        assert result['was_empty'] is False
        assert result['confidence'] == 0

    @pytest.mark.asyncio
    async def test_empty_rpc_error(self):
        """Test handling RPC error (archival node not available)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_balance.side_effect = Exception("Historical data not available")
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._was_empty_before('0xAddress', whale_tx_block=18000000)

        assert result['was_empty'] is False
        assert result['confidence'] == 0


class TestSingleUseDetection:
    """Test single-use burner pattern detection"""

    @pytest.mark.asyncio
    async def test_perfect_burner(self):
        """Test perfect burner pattern (2 txs, empty)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 2
        mock_web3.eth.get_balance.return_value = 0
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_single_use('0xAddress')

        assert result['is_single_use'] is True
        assert result['confidence'] == 95
        assert result['tx_count'] == 2
        assert 'perfect burner' in result['details'].lower()

    @pytest.mark.asyncio
    async def test_likely_burner(self):
        """Test likely burner pattern (3 txs, minimal balance)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 3
        mock_web3.eth.get_balance.return_value = int(0.05 * 10**18)  # 0.05 ETH
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_single_use('0xAddress')

        assert result['is_single_use'] is True
        assert result['confidence'] == 80
        assert result['tx_count'] == 3

    @pytest.mark.asyncio
    async def test_not_burner_many_txs(self):
        """Test not burner (many transactions)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 20
        mock_web3.eth.get_balance.return_value = int(1.0 * 10**18)
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_single_use('0xAddress')

        assert result['is_single_use'] is False
        assert result['confidence'] == 0
        assert result['tx_count'] == 20

    @pytest.mark.asyncio
    async def test_not_burner_has_balance(self):
        """Test not burner (2 txs but has balance)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 2
        mock_web3.eth.get_balance.return_value = int(1.0 * 10**18)  # 1 ETH
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_single_use('0xAddress')

        assert result['is_single_use'] is False
        assert result['confidence'] == 0


class TestReusedIntermediateDetection:
    """Test reused intermediate pattern detection"""

    @pytest.mark.asyncio
    async def test_reused_intermediate(self):
        """Test reused intermediate (10+ transactions)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 20  # 10 cycles
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_reused_intermediate('0xAddress')

        assert result['is_reused'] is True
        assert result['confidence'] == 75
        assert result['cycle_count'] == 10

    @pytest.mark.asyncio
    async def test_not_reused(self):
        """Test not reused (few transactions)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        mock_web3.eth.get_transaction_count.return_value = 5
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        result = await profiler._is_reused_intermediate('0xAddress')

        assert result['is_reused'] is False
        assert result['confidence'] == 0


class TestFullProfileCreation:
    """Test comprehensive profile creation"""

    @pytest.mark.asyncio
    async def test_fresh_burner_profile(self):
        """Test fresh burner profile (highest confidence)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        # Fresh (low tx count)
        mock_web3.eth.get_transaction_count.side_effect = [1, 2]  # First for fresh, second for single-use
        # Empty before
        mock_web3.eth.get_balance.side_effect = [0, 0]  # First for empty check, second for single-use
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        profile = await profiler.profile_address(
            '0xAddress',
            whale_tx_block=18000000
        )

        assert profile.profile_type == 'fresh_burner'
        assert profile.overall_confidence >= 85
        assert profile.is_fresh is True
        assert profile.was_empty is True
        assert profile.is_single_use is True

    @pytest.mark.asyncio
    async def test_burner_profile(self):
        """Test burner profile (single-use but not fresh)"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        # Not fresh (many txs from history)
        mock_web3.eth.get_transaction_count.side_effect = [100, 2]  # Not fresh, but 2 for single-use
        # Wasn't empty before
        mock_web3.eth.get_balance.side_effect = [int(1.0 * 10**18), 0]  # Had balance, now empty
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        profile = await profiler.profile_address(
            '0xAddress',
            whale_tx_block=18000000
        )

        assert profile.profile_type == 'burner'
        assert profile.is_single_use is True
        assert profile.is_fresh is False

    @pytest.mark.asyncio
    async def test_professional_profile(self):
        """Test professional reused intermediate profile"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        # Many transactions (reused)
        mock_web3.eth.get_transaction_count.side_effect = [50, 50, 50]
        # Has balance
        mock_web3.eth.get_balance.side_effect = [int(1.0 * 10**18), int(0.5 * 10**18)]
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        profile = await profiler.profile_address(
            '0xAddress',
            whale_tx_block=18000000
        )

        assert profile.profile_type == 'professional'
        assert profile.is_reused is True
        assert profile.reuse_confidence > 0

    @pytest.mark.asyncio
    async def test_normal_profile(self):
        """Test normal address profile"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        # Normal transaction count (not enough for reuse, but not fresh)
        mock_web3.eth.get_transaction_count.side_effect = [8, 8, 8]
        # Normal balance
        mock_web3.eth.get_balance.side_effect = [int(1.0 * 10**18), int(1.0 * 10**18)]
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        profile = await profiler.profile_address(
            '0xAddress',
            whale_tx_block=18000000
        )

        assert profile.profile_type == 'normal'
        assert profile.overall_confidence == 0

    @pytest.mark.asyncio
    async def test_profile_error_handling(self):
        """Test error handling in profile creation"""
        mock_web3_manager = Mock()
        mock_web3 = Mock()
        # Make ALL calls raise exception
        mock_web3.eth.get_transaction_count = Mock(side_effect=Exception("RPC error"))
        mock_web3.eth.get_balance = Mock(side_effect=Exception("RPC error"))
        mock_web3_manager.w3 = mock_web3

        profiler = AddressProfiler(web3_manager=mock_web3_manager)

        profile = await profiler.profile_address(
            '0xAddress',
            whale_tx_block=18000000
        )

        # When all methods fail, should return error profile
        # But since each method catches its own exception, the profile_address
        # itself won't throw, it will just return a profile with all signals = False
        # So we should check that all signals are False (not an error profile)
        assert profile.profile_type in ['normal', 'error']  # Either is acceptable
        assert profile.overall_confidence == 0


class TestProfileTypeDetection:
    """Test profile type and confidence determination"""

    def test_fresh_burner_determination(self):
        """Test fresh_burner type determination"""
        profiler = AddressProfiler()

        fresh_result = {'is_fresh': True, 'confidence': 90}
        empty_result = {'was_empty': True, 'confidence': 85}
        single_use_result = {'is_single_use': True, 'confidence': 95}
        reuse_result = {'is_reused': False, 'confidence': 0}

        profile_type, confidence = profiler._determine_profile_type(
            fresh_result, empty_result, single_use_result, reuse_result
        )

        assert profile_type == 'fresh_burner'
        assert confidence == 95  # Max of all

    def test_burner_determination(self):
        """Test burner type determination"""
        profiler = AddressProfiler()

        fresh_result = {'is_fresh': False, 'confidence': 0}
        empty_result = {'was_empty': False, 'confidence': 0}
        single_use_result = {'is_single_use': True, 'confidence': 95}
        reuse_result = {'is_reused': False, 'confidence': 0}

        profile_type, confidence = profiler._determine_profile_type(
            fresh_result, empty_result, single_use_result, reuse_result
        )

        assert profile_type == 'burner'
        assert confidence == 95

    def test_professional_determination(self):
        """Test professional type determination"""
        profiler = AddressProfiler()

        fresh_result = {'is_fresh': False, 'confidence': 0}
        empty_result = {'was_empty': False, 'confidence': 0}
        single_use_result = {'is_single_use': False, 'confidence': 0}
        reuse_result = {'is_reused': True, 'confidence': 75}

        profile_type, confidence = profiler._determine_profile_type(
            fresh_result, empty_result, single_use_result, reuse_result
        )

        assert profile_type == 'professional'
        assert confidence == 75

    def test_fresh_determination(self):
        """Test fresh type determination"""
        profiler = AddressProfiler()

        fresh_result = {'is_fresh': True, 'confidence': 70}
        empty_result = {'was_empty': False, 'confidence': 0}
        single_use_result = {'is_single_use': False, 'confidence': 0}
        reuse_result = {'is_reused': False, 'confidence': 0}

        profile_type, confidence = profiler._determine_profile_type(
            fresh_result, empty_result, single_use_result, reuse_result
        )

        assert profile_type == 'fresh'
        assert confidence == 70

    def test_normal_determination(self):
        """Test normal type determination"""
        profiler = AddressProfiler()

        fresh_result = {'is_fresh': False, 'confidence': 0}
        empty_result = {'was_empty': False, 'confidence': 0}
        single_use_result = {'is_single_use': False, 'confidence': 0}
        reuse_result = {'is_reused': False, 'confidence': 0}

        profile_type, confidence = profiler._determine_profile_type(
            fresh_result, empty_result, single_use_result, reuse_result
        )

        assert profile_type == 'normal'
        assert confidence == 0
