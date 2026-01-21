"""
Unit Tests for MulticallClient

Tests batch balance queries, chunking, error handling, and historical balances.

Run: pytest tests/unit/test_multicall_client.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from web3 import Web3

from src.data.multicall_client import MulticallClient, MULTICALL3_ABI, WETH_ADDRESS, STETH_ADDRESS, ERC20_ABI


@pytest.fixture
def mock_web3():
    """Create mock Web3 instance."""
    mock_w3 = Mock()
    mock_w3.eth = Mock()
    mock_w3.eth.block_number = 24000000
    mock_w3.eth.get_balance = Mock(return_value=1000000000000000000)  # 1 ETH in Wei
    mock_w3.eth.contract = Mock()
    return mock_w3


@pytest.fixture
def mock_web3_manager(mock_web3):
    """Create mock Web3Manager."""
    manager = Mock()
    manager.web3 = mock_web3
    return manager


@pytest.fixture
def multicall_client(mock_web3_manager):
    """Create MulticallClient instance with mocked dependencies."""
    return MulticallClient(mock_web3_manager)


class TestMulticallClientInitialization:
    """Test MulticallClient initialization."""
    
    def test_init_success(self, mock_web3_manager):
        """Test successful initialization."""
        client = MulticallClient(mock_web3_manager)
        
        assert client.web3_manager == mock_web3_manager
        assert client.w3 == mock_web3_manager.web3
        assert client.MULTICALL3_ADDRESS == "0xcA11bde05977b3631167028862bE2a173976CA11"
    
    def test_init_without_web3_raises_error(self):
        """Test initialization fails without Web3 connection."""
        manager = Mock()
        manager.web3 = None
        
        with pytest.raises(ValueError, match="Web3Manager must be initialized"):
            MulticallClient(manager)


class TestGetLatestBlock:
    """Test get_latest_block method."""
    
    @pytest.mark.asyncio
    async def test_get_latest_block_success(self, multicall_client, mock_web3):
        """Test getting latest block number."""
        mock_web3.eth.block_number = 24266373
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = 24266373
            
            block = await multicall_client.get_latest_block()
            
            assert block == 24266373
    
    @pytest.mark.asyncio
    async def test_get_latest_block_error(self, multicall_client, mock_web3):
        """Test error handling when RPC fails."""
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("RPC connection failed")
            
            with pytest.raises(Exception, match="RPC connection failed"):
                await multicall_client.get_latest_block()


class TestGetBalancesBatch:
    """Test get_balances_batch method."""
    
    @pytest.mark.asyncio
    async def test_get_balances_empty_list(self, multicall_client):
        """Test with empty address list."""
        result = await multicall_client.get_balances_batch([])
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_balances_single_address(self, multicall_client, mock_web3):
        """Test with single address using Multicall3.aggregate3()."""
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        expected_balance = 33111613082018243614  # Vitalik's balance from real test
        
        # Mock Multicall3.aggregate3() response
        mock_results = [(True, expected_balance.to_bytes(32, 'big'))]
        
        mock_aggregate = Mock()
        mock_call = Mock()
        mock_call.call = Mock(return_value=mock_results)
        mock_aggregate.return_value = mock_call
        
        with patch.object(multicall_client.multicall_contract.functions, 'aggregate3', mock_aggregate):
            with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = mock_results
                
                result = await multicall_client.get_balances_batch([address])
                
                assert len(result) == 1
                assert result[address] == expected_balance
    
    @pytest.mark.asyncio
    async def test_get_balances_multiple_addresses(self, multicall_client):
        """Test with multiple addresses using Multicall3.aggregate3()."""
        addresses = [
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
            "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",  # Tornado Cash
            "0x00000000219ab540356cBB839Cbe05303d7705Fa",  # ETH2 Deposit
        ]
        
        balances = [33111613082018243614, 993033772614273069, 77938775857974546172899779]
        
        # Mock Multicall3.aggregate3() response with 3 results
        mock_results = [
            (True, balances[0].to_bytes(32, 'big')),
            (True, balances[1].to_bytes(32, 'big')),
            (True, balances[2].to_bytes(32, 'big')),
        ]
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            result = await multicall_client.get_balances_batch(addresses)
            
            assert len(result) == 3
            assert result[addresses[0]] == balances[0]
            assert result[addresses[1]] == balances[1]
            assert result[addresses[2]] == balances[2]
    
    @pytest.mark.asyncio
    async def test_get_balances_chunking(self, multicall_client):
        """Test chunking with many addresses - should use 2 Multicall3 calls."""
        # Create 750 VALID addresses (should split into 2 chunks: 500 + 250)
        # Use addresses that are valid checksummed Ethereum addresses
        addresses = [f"0x{'0' * (39 - len(hex(i)[2:]))}{hex(i)[2:]}0" for i in range(750)]
        balance = 1000000000000000000  # 1 ETH
        
        # Mock will be called twice (once per chunk)
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            # First chunk: 500 addresses
            chunk1_results = [(True, balance.to_bytes(32, 'big')) for _ in range(500)]
            # Second chunk: 250 addresses
            chunk2_results = [(True, balance.to_bytes(32, 'big')) for _ in range(250)]
            
            mock_thread.side_effect = [chunk1_results, chunk2_results]
            
            result = await multicall_client.get_balances_batch(addresses, chunk_size=500)
            
            # Should process all addresses
            assert len(result) == 750
            # Should be called 2 times (2 chunks)
            assert mock_thread.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_balances_error_handling(self, multicall_client):
        """Test graceful error handling when Multicall3 calls fail."""
        # Use VALID Ethereum addresses
        addresses = [
            "0x0000000000000000000000000000000000000001",  # Good address 1
            "0x0000000000000000000000000000000000000002",  # Bad address (will fail)
            "0x0000000000000000000000000000000000000003",  # Good address 2
        ]
        
        # Mock results: first succeeds, second fails, third succeeds
        mock_results = [
            (True, (1000000000000000000).to_bytes(32, 'big')),   # Success
            (False, b''),  # Failure - RPC error
            (True, (1000000000000000000).to_bytes(32, 'big')),   # Success
        ]
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            result = await multicall_client.get_balances_batch(addresses)
            
            # Should have 3 results
            assert len(result) == 3
            assert result[addresses[0]] == 1000000000000000000
            assert result[addresses[1]] is None  # CRITICAL: RPC error -> None (not 0!)
            assert result[addresses[2]] == 1000000000000000000
    
    @pytest.mark.asyncio
    async def test_none_balance_handling(self, multicall_client):
        """Test that None balances are returned for RPC errors (not 0)."""
        addresses = ["0x0000000000000000000000000000000000000001"]
        
        # Mock RPC failure
        mock_results = [(False, b'')]  # success=False -> RPC error
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            result = await multicall_client.get_balances_batch(addresses)
            
            # CRITICAL: RPC error must return None, not 0
            assert result[addresses[0]] is None
    
    @pytest.mark.asyncio
    async def test_zero_balance_logged(self, multicall_client, caplog):
        """Test that zero balances are logged with warning."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        addresses = ["0x0000000000000000000000000000000000000001"]
        
        # Mock zero balance (valid, not error)
        mock_results = [(True, (0).to_bytes(32, 'big'))]  # success=True, balance=0
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            result = await multicall_client.get_balances_batch(addresses)
            
            # Should return 0 (valid empty wallet)
            assert result[addresses[0]] == 0
            
            # Should log warning about zero balance
            assert "⚠️ Zero balance" in caplog.text
    
    @pytest.mark.asyncio
    async def test_chunk_error_returns_none(self, multicall_client):
        """Test that entire chunk errors return None for all addresses."""
        addresses = [
            "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002",
        ]
        
        # Mock chunk exception
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = Exception("RPC timeout")
            
            result = await multicall_client.get_balances_batch(addresses)
            
            # All addresses in failed chunk should be None
            assert result[addresses[0]] is None
            assert result[addresses[1]] is None



class TestGetHistoricalBalances:
    """Test get_historical_balances method."""
    
    @pytest.mark.asyncio
    async def test_historical_balances_recent_block(self, multicall_client, mock_web3):
        """Test historical balances for recent block (within archive limit)."""
        current_block = 24266373
        historical_block = current_block - 50  # Within 128 block limit
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        expected_balance = 33000000000000000000
        
        with patch.object(multicall_client, 'get_latest_block', new_callable=AsyncMock) as mock_latest:
            mock_latest.return_value = current_block
            
            with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                mock_to_thread.return_value = expected_balance
                
                result = await multicall_client.get_historical_balances([address], historical_block)
                
                assert len(result) == 1
                assert result[address] == expected_balance
    
    @pytest.mark.asyncio
    async def test_historical_balances_old_block_mvp_mode(self, multicall_client, mock_web3):
        """Test MVP mode for old blocks (beyond archive limit)."""
        current_block = 24266373
        old_block = current_block - 200  # Beyond 128 block limit
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        current_balance = 33111613082018243614
        
        with patch.object(multicall_client, 'get_latest_block', new_callable=AsyncMock) as mock_latest:
            mock_latest.return_value = current_block
            
            with patch.object(multicall_client, 'get_balances_batch', new_callable=AsyncMock) as mock_batch:
                mock_batch.return_value = {address: current_balance}
                
                result = await multicall_client.get_historical_balances([address], old_block)
                
                # Should call get_balances_batch (MVP fallback)
                mock_batch.assert_called_once()
                assert result[address] == current_balance


class TestHealthCheck:
    """Test health_check method."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, multicall_client):
        """Test successful health check."""
        with patch.object(multicall_client, 'get_latest_block', new_callable=AsyncMock) as mock_block:
            mock_block.return_value = 24266373
            
            with patch.object(multicall_client, 'get_balances_batch', new_callable=AsyncMock) as mock_batch:
                mock_batch.return_value = {"0x0000000000000000000000000000000000000000": 0}
                
                health = await multicall_client.health_check()
                
                assert health["status"] == "healthy"
                assert health["latest_block"] == 24266373
                assert health["test_balance_query"] == "success"
                assert health["multicall_address"] == "0xcA11bde05977b3631167028862bE2a173976CA11"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, multicall_client):
        """Test health check failure."""
        with patch.object(multicall_client, 'get_latest_block', new_callable=AsyncMock) as mock_block:
            mock_block.side_effect = Exception("RPC connection failed")
            
            health = await multicall_client.health_check()
            
            assert health["status"] == "unhealthy"
            assert "error" in health


class TestCreateBalanceCall:
    """Test _create_balance_call helper method."""
    
    def test_create_balance_call(self, multicall_client):
        """Test creating balance call structure for Multicall3.getEthBalance."""
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        
        # Mock the contract's functions.getEthBalance()._encode_transaction_data()
        mock_encode = Mock(return_value=b'\x12\x34\x56\x78')  # Mock encoded data
        mock_get_balance = Mock()
        mock_get_balance._encode_transaction_data = mock_encode
        
        with patch.object(
            multicall_client.multicall_contract.functions,
            'getEthBalance',
            return_value=mock_get_balance
        ):
            call = multicall_client._create_balance_call(address)
            
            # Should target Multicall3 contract itself
            assert call["target"] == Web3.to_checksum_address(multicall_client.MULTICALL3_ADDRESS)
            assert call["allowFailure"] is True
            assert call["callData"] == b'\x12\x34\x56\x78'  # Encoded getEthBalance call


class TestERC20BalanceMethods:
    """Test ERC20 balance fetching methods (WETH/stETH)."""
    
    def test_create_erc20_balance_call(self, multicall_client):
        """
        Test creating ERC20 balanceOf call structure.
        
        WHY: ERC20 calls target token contract (not Multicall3)
        """
        token_address = WETH_ADDRESS
        holder_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        
        # Mock ERC20 contract and balanceOf encoding
        mock_encode = Mock(return_value=b'\x70\xa0\x82\x31')  # balanceOf signature
        mock_balance_of = Mock()
        mock_balance_of._encode_transaction_data = mock_encode
        
        mock_contract = Mock()
        mock_contract.functions.balanceOf = Mock(return_value=mock_balance_of)
        
        with patch.object(multicall_client.w3.eth, 'contract', return_value=mock_contract):
            call = multicall_client._create_erc20_balance_call(token_address, holder_address)
            
            # Should target token contract (not Multicall3)
            assert call["target"] == Web3.to_checksum_address(token_address)
            assert call["allowFailure"] is True
            assert call["callData"] == b'\x70\xa0\x82\x31'
    
    @pytest.mark.asyncio
    async def test_get_erc20_balances_weth_single_address(self, multicall_client):
        """
        Test WETH balance for single address.
        
        WHY: Validates WETH token name detection in logs
        """
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        expected_weth_balance = 5000000000000000000  # 5 WETH
        
        # Mock Multicall3.aggregate3() response
        mock_results = [(True, expected_weth_balance.to_bytes(32, 'big'))]
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            result = await multicall_client.get_erc20_balances_batch(
                addresses=[address],
                token_address=WETH_ADDRESS
            )
            
            assert len(result) == 1
            assert result[address] == expected_weth_balance
    
    @pytest.mark.asyncio
    async def test_get_erc20_balances_steth_multiple_addresses(self, multicall_client):
        """
        Test stETH balances for multiple addresses.
        
        WHY: stETH is critical for LST migration detection
        """
        addresses = [
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",
        ]
        
        steth_balances = [
            12500000000000000000,  # 12.5 stETH
            8300000000000000000,   # 8.3 stETH
        ]
        
        # Mock Multicall3.aggregate3() response
        mock_results = [
            (True, steth_balances[0].to_bytes(32, 'big')),
            (True, steth_balances[1].to_bytes(32, 'big')),
        ]
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            result = await multicall_client.get_erc20_balances_batch(
                addresses=addresses,
                token_address=STETH_ADDRESS
            )
            
            assert len(result) == 2
            assert result[addresses[0]] == steth_balances[0]
            assert result[addresses[1]] == steth_balances[1]
    
    @pytest.mark.asyncio
    async def test_get_erc20_balances_empty_list(self, multicall_client):
        """Test ERC20 balance query with empty address list."""
        result = await multicall_client.get_erc20_balances_batch(
            addresses=[],
            token_address=WETH_ADDRESS
        )
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_erc20_balances_zero_balance(self, multicall_client, caplog):
        """
        Test ERC20 zero balance logging.
        
        WHY: Distinguish between "0 WETH" and "RPC error"
        """
        import logging
        caplog.set_level(logging.DEBUG)
        
        address = "0x0000000000000000000000000000000000000001"
        
        # Mock zero WETH balance (valid)
        mock_results = [(True, (0).to_bytes(32, 'big'))]
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            result = await multicall_client.get_erc20_balances_batch(
                addresses=[address],
                token_address=WETH_ADDRESS
            )
            
            # Should return 0 (valid zero WETH)
            assert result[address] == 0
            
            # Should log with token name
            assert "Zero WETH balance" in caplog.text
    
    @pytest.mark.asyncio
    async def test_get_erc20_balances_rpc_failure(self, multicall_client):
        """
        Test ERC20 RPC failure returns None (not 0).
        
        WHY: Critical for LST migration detection - don't confuse error with empty wallet
        """
        addresses = [
            "0x0000000000000000000000000000000000000001",  # Good
            "0x0000000000000000000000000000000000000002",  # RPC error
        ]
        
        # Mock results: first succeeds, second fails
        mock_results = [
            (True, (1000000000000000000).to_bytes(32, 'big')),  # 1 WETH
            (False, b''),  # RPC error
        ]
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            result = await multicall_client.get_erc20_balances_batch(
                addresses=addresses,
                token_address=WETH_ADDRESS
            )
            
            assert result[addresses[0]] == 1000000000000000000
            assert result[addresses[1]] is None  # CRITICAL: None, not 0!
    
    @pytest.mark.asyncio
    async def test_get_erc20_balances_chunking(self, multicall_client):
        """
        Test ERC20 chunking with 750 addresses.
        
        WHY: Same efficiency as native ETH (2 RPC calls for 750 addresses)
        """
        # Create 750 valid addresses
        addresses = [f"0x{'0' * (39 - len(hex(i)[2:]))}{hex(i)[2:]}0" for i in range(750)]
        steth_balance = 10000000000000000000  # 10 stETH per address
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            # First chunk: 500 addresses
            chunk1_results = [(True, steth_balance.to_bytes(32, 'big')) for _ in range(500)]
            # Second chunk: 250 addresses
            chunk2_results = [(True, steth_balance.to_bytes(32, 'big')) for _ in range(250)]
            
            mock_thread.side_effect = [chunk1_results, chunk2_results]
            
            result = await multicall_client.get_erc20_balances_batch(
                addresses=addresses,
                token_address=STETH_ADDRESS,
                chunk_size=500
            )
            
            # Should process all addresses
            assert len(result) == 750
            # Should be called 2 times (2 chunks)
            assert mock_thread.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_erc20_balances_chunk_error(self, multicall_client):
        """
        Test ERC20 chunk error handling.
        
        WHY: One failed chunk shouldn't break entire batch
        """
        addresses = [
            "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002",
        ]
        
        # Mock chunk exception
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = Exception("RPC timeout")
            
            result = await multicall_client.get_erc20_balances_batch(
                addresses=addresses,
                token_address=WETH_ADDRESS
            )
            
            # All addresses in failed chunk should be None
            assert result[addresses[0]] is None
            assert result[addresses[1]] is None
    
    @pytest.mark.asyncio
    async def test_get_erc20_balances_token_name_detection(self, multicall_client, caplog):
        """
        Test token name detection in logs.
        
        WHY: Helps debugging - "Fetching WETH balances" vs "Fetching stETH balances"
        """
        import logging
        caplog.set_level(logging.INFO)
        
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        mock_results = [(True, (1000000000000000000).to_bytes(32, 'big'))]
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_results
            
            # Test WETH
            await multicall_client.get_erc20_balances_batch(
                addresses=[address],
                token_address=WETH_ADDRESS
            )
            assert "Fetching WETH balances" in caplog.text
            
            # Test stETH
            caplog.clear()
            await multicall_client.get_erc20_balances_batch(
                addresses=[address],
                token_address=STETH_ADDRESS
            )
            assert "Fetching stETH balances" in caplog.text
            
            # Test generic ERC20
            caplog.clear()
            custom_token = "0x1234567890123456789012345678901234567890"
            await multicall_client.get_erc20_balances_batch(
                addresses=[address],
                token_address=custom_token
            )
            assert "Fetching ERC20 balances" in caplog.text


# ============================================
# INTEGRATION-STYLE TESTS (require real RPC)
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_multicall_integration():
    """
    Integration test with real blockchain (requires RPC connection).
    
    Run with: pytest tests/unit/test_multicall_client.py -v -m integration
    """
    from src.core.web3_manager import Web3Manager
    from config.settings import Settings
    
    # Initialize real Web3Manager
    settings = Settings()
    web3_manager = Web3Manager(mock_mode=False)
    success = await web3_manager.initialize()
    
    assert success, "Failed to initialize Web3Manager"
    
    # Create MulticallClient
    client = MulticallClient(web3_manager)
    
    # Test with real addresses
    addresses = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
    ]
    
    balances = await client.get_balances_batch(addresses)
    
    # Should have balance > 0
    assert len(balances) == 1
    assert balances[addresses[0]] > 0
    
    print(f"✅ Real balance: {Web3.from_wei(balances[addresses[0]], 'ether')} ETH")
