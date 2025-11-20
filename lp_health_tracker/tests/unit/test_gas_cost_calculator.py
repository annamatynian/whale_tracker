"""
Tests for Gas Cost Calculator - Gas Cost Analysis
================================================

Unit tests for gas cost calculations and Web3 integration.
These tests verify the correctness of gas cost formulas and blockchain interaction.

Run with: pytest tests/test_gas_cost_calculator.py -v
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from web3 import Web3
from typing import Dict, Any

from src.gas_cost_calculator import GasCostCalculator, GasEstimator
from src.web3_utils import Web3Manager


class TestGasCostCalculatorMath:
    """Test suite for gas cost mathematical calculations."""
    
    def setup_method(self):
        """Setup before each test method."""
        # Create mock Web3Manager to isolate math testing
        self.mock_web3_manager = Mock(spec=Web3Manager)
        self.calculator = GasCostCalculator(self.mock_web3_manager)
    
    def test_wei_to_eth_conversion_accuracy(self):
        """Test that Wei to ETH conversion is mathematically correct."""
        # Arrange
        gas_used = 150000  # typical LP add liquidity
        gas_price_gwei = 20  # 20 Gwei
        
        # Manual calculation for verification
        gas_price_wei = gas_price_gwei * 10**9  # Convert Gwei to Wei
        total_cost_wei = gas_used * gas_price_wei
        expected_cost_eth = total_cost_wei / 10**18  # Convert Wei to ETH
        
        # Act - using Web3.py conversion (what our code uses)
        gas_price_wei_web3 = Web3.to_wei(gas_price_gwei, 'gwei')
        total_cost_wei_web3 = gas_used * gas_price_wei_web3
        actual_cost_eth = float(Web3.from_wei(total_cost_wei_web3, 'ether'))
        
        # Assert
        assert abs(actual_cost_eth - expected_cost_eth) < 1e-18, \
            f"Expected {expected_cost_eth} ETH, got {actual_cost_eth} ETH"
        
        # Verify specific expected value
        expected_eth = 0.003  # 150k gas * 20 Gwei = 0.003 ETH
        assert abs(actual_cost_eth - expected_eth) < 1e-6, \
            f"Expected ~{expected_eth} ETH, got {actual_cost_eth} ETH"
    
    def test_usd_conversion_calculation(self):
        """Test USD conversion with different ETH prices."""
        # Test data: gas costs in ETH and various ETH prices
        test_cases = [
            # (cost_eth, eth_price_usd, expected_cost_usd)
            (0.001, 2000.0, 2.0),      # Simple case
            (0.005, 3500.0, 17.5),     # Higher gas + price
            (0.0001, 1800.0, 0.18),    # Low gas cost
            (0.01, 4000.0, 40.0),      # High gas cost
        ]
        
        for cost_eth, eth_price_usd, expected_cost_usd in test_cases:
            # Act
            actual_cost_usd = cost_eth * eth_price_usd
            
            # Assert
            assert abs(actual_cost_usd - expected_cost_usd) < 0.01, \
                f"ETH {cost_eth} * ${eth_price_usd} should = ${expected_cost_usd}, got ${actual_cost_usd}"
    
    def test_realistic_gas_cost_scenarios(self):
        """Test realistic DeFi transaction scenarios."""
        # Common DeFi operations with realistic gas usage
        scenarios = [
            {
                'name': 'Uniswap V2 Add Liquidity',
                'gas_used': 150000,
                'gas_price_gwei': 25,
                'eth_price_usd': 3200.0,
                'expected_cost_usd': 12.0  # 150k * 25 * 3200 / 10^9 / 10^9
            },
            {
                'name': 'ERC20 Approve',
                'gas_used': 50000,
                'gas_price_gwei': 15,
                'eth_price_usd': 2800.0,
                'expected_cost_usd': 2.1  # 50k * 15 * 2800 / 10^18
            },
            {
                'name': 'Uniswap V2 Remove Liquidity',
                'gas_used': 120000,
                'gas_price_gwei': 30,
                'eth_price_usd': 3500.0,
                'expected_cost_usd': 12.6  # 120k * 30 * 3500 / 10^18
            }
        ]
        
        for scenario in scenarios:
            # Arrange
            gas_used = scenario['gas_used']
            gas_price_gwei = scenario['gas_price_gwei']
            eth_price_usd = scenario['eth_price_usd']
            expected_cost_usd = scenario['expected_cost_usd']
            
            # Act - Manual calculation like our calculator does
            gas_price_wei = Web3.to_wei(gas_price_gwei, 'gwei')
            total_cost_wei = gas_used * gas_price_wei
            cost_eth = float(Web3.from_wei(total_cost_wei, 'ether'))
            actual_cost_usd = cost_eth * eth_price_usd
            
            # Assert (allow small floating point differences)
            assert abs(actual_cost_usd - expected_cost_usd) < 0.1, \
                f"{scenario['name']}: Expected ~${expected_cost_usd}, got ${actual_cost_usd:.2f}"


class TestGasEstimator:
    """Test suite for static gas estimation utilities."""
    
    @pytest.mark.asyncio
    async def test_supported_operations_list(self):
        """Test that we can get list of supported operations."""
        # Act
        operations = GasEstimator.get_supported_operations()
        
        # Assert
        assert isinstance(operations, list)
        assert len(operations) > 0
        assert 'uniswap_v2_add_liquidity' in operations
        assert 'erc20_approve' in operations
    
    @pytest.mark.asyncio
    async def test_operation_cost_estimation(self):
        """Test gas cost estimation for standard operations."""
        # Test cases for common operations
        test_cases = [
            {
                'operation': 'uniswap_v2_add_liquidity',
                'gas_price_gwei': 20.0,
                'eth_price_usd': 3000.0,
                'expected_min_cost': 8.0,   # Should be around $9 (150k gas * 20 gwei * $3000)
                'expected_max_cost': 10.0
            },
            {
                'operation': 'erc20_approve',
                'gas_price_gwei': 15.0,
                'eth_price_usd': 2500.0,
                'expected_min_cost': 1.5,   # Should be around $1.875 (50k gas * 15 gwei * $2500)
                'expected_max_cost': 2.5
            }
        ]
        
        for case in test_cases:
            # Act
            estimated_cost = await GasEstimator.estimate_operation_cost_usd(
                case['operation'],
                case['gas_price_gwei'],
                case['eth_price_usd']
            )
            
            # Assert
            assert estimated_cost is not None, f"Should estimate cost for {case['operation']}"
            assert case['expected_min_cost'] <= estimated_cost <= case['expected_max_cost'], \
                f"{case['operation']}: Expected ${case['expected_min_cost']}-${case['expected_max_cost']}, got ${estimated_cost:.2f}"
    
    @pytest.mark.asyncio
    async def test_unsupported_operation_returns_none(self):
        """Test that unsupported operations return None."""
        # Act
        result = await GasEstimator.estimate_operation_cost_usd(
            'nonexistent_operation',
            20.0,
            3000.0
        )
        
        # Assert
        assert result is None


class TestGasCostCalculatorPositionData:
    """Test suite for position-related gas cost calculations."""
    
    def setup_method(self):
        """Setup before each test method."""
        self.mock_web3_manager = Mock(spec=Web3Manager)
        self.calculator = GasCostCalculator(self.mock_web3_manager)
    
    def test_get_gas_cost_summary_empty_positions(self):
        """Test gas cost summary with empty position list."""
        # Act
        summary = self.calculator.get_gas_cost_summary([])
        
        # Assert
        assert summary['total_positions'] == 0
        assert summary['calculated_positions'] == 0
        assert summary['fallback_positions'] == 0
        assert summary['total_gas_costs_usd'] == 0
        assert summary['average_gas_cost_usd'] == 0
    
    def test_get_gas_cost_summary_mixed_positions(self):
        """Test gas cost summary with mix of calculated and fallback positions."""
        # Arrange
        positions = [
            {
                'name': 'Position 1',
                'gas_costs_usd': 25.0,
                'gas_costs_calculated': True
            },
            {
                'name': 'Position 2', 
                'gas_costs_usd': 15.0,
                'gas_costs_calculated': False  # Fallback value
            },
            {
                'name': 'Position 3',
                'gas_costs_usd': 30.0,
                'gas_costs_calculated': True
            }
        ]
        
        # Act
        summary = self.calculator.get_gas_cost_summary(positions)
        
        # Assert
        assert summary['total_positions'] == 3
        assert summary['calculated_positions'] == 2
        assert summary['fallback_positions'] == 1
        assert summary['total_gas_costs_usd'] == 70.0  # 25 + 15 + 30
        assert summary['calculated_gas_costs_usd'] == 55.0  # 25 + 30
        assert summary['fallback_gas_costs_usd'] == 15.0
        assert abs(summary['calculation_accuracy'] - 0.6667) < 0.001  # 2/3
        assert abs(summary['average_gas_cost_usd'] - 23.333) < 0.001  # 70/3
    
    def test_gas_cost_summary_with_missing_fields(self):
        """Test gas cost summary handles positions with missing gas cost fields."""
        # Arrange
        positions = [
            {
                'name': 'Complete Position',
                'gas_costs_usd': 20.0,
                'gas_costs_calculated': True
            },
            {
                'name': 'Missing gas_costs_calculated',
                'gas_costs_usd': 10.0
                # Missing gas_costs_calculated field
            },
            {
                'name': 'Missing gas_costs_usd',
                'gas_costs_calculated': False
                # Missing gas_costs_usd field
            }
        ]
        
        # Act
        summary = self.calculator.get_gas_cost_summary(positions)
        
        # Assert
        assert summary['total_positions'] == 3
        assert summary['calculated_positions'] == 1  # Only first position
        assert summary['fallback_positions'] == 2    # Second and third positions
        assert summary['total_gas_costs_usd'] == 30.0  # 20 + 10 + 0 (missing defaults to 0)


class TestGasCostCalculatorWeb3Integration:
    """Test suite for Web3Manager integration and blockchain interaction."""
    
    def setup_method(self):
        """Setup before each test method."""
        self.mock_web3_manager = Mock(spec=Web3Manager)
        self.calculator = GasCostCalculator(self.mock_web3_manager)
    
    @pytest.mark.asyncio
    async def test_successful_transaction_receipt_processing(self):
        """Test successful processing of transaction receipt from Web3Manager."""
        # Arrange
        tx_hash = "0xa1b2c3d4e5f6789012345678901234567890abcdef123456789012345678901234"
        eth_price_usd = 3000.0
        
        # Mock transaction receipt (realistic structure)
        mock_receipt = {
            'gasUsed': 150000,
            'effectiveGasPrice': Web3.to_wei(25, 'gwei'),  # 25 Gwei
            'status': 1,
            'blockNumber': 18500000
        }
        
        # Configure mock Web3Manager
        self.mock_web3_manager.get_transaction_receipt = Mock(return_value=mock_receipt)
        
        # Act
        result = await self.calculator.calculate_tx_cost_usd(tx_hash, eth_price_usd)
        
        # Assert
        assert result is not None, "Should return calculated cost"
        
        # Expected calculation: 150000 * 25 Gwei * $3000 = $11.25
        expected_cost = 11.25  # 150k * 25 * 3000 / 10^18
        assert abs(result - expected_cost) < 0.01, f"Expected ~${expected_cost}, got ${result:.2f}"
        
        # Verify Web3Manager was called correctly
        self.mock_web3_manager.get_transaction_receipt.assert_called_once_with(tx_hash)
    
    @pytest.mark.asyncio
    async def test_transaction_receipt_not_found_returns_none(self):
        """Test that missing transaction receipt returns None."""
        # Arrange
        tx_hash = "0xnonexistent1234567890abcdef"
        eth_price_usd = 3000.0
        
        # Configure mock to return None (transaction not found)
        self.mock_web3_manager.get_transaction_receipt = Mock(return_value=None)
        
        # Act
        result = await self.calculator.calculate_tx_cost_usd(tx_hash, eth_price_usd)
        
        # Assert
        assert result is None, "Should return None when transaction not found"
        
        # Verify Web3Manager was called
        self.mock_web3_manager.get_transaction_receipt.assert_called_once_with(tx_hash)
    
    @pytest.mark.asyncio
    async def test_caching_mechanism_prevents_duplicate_web3_calls(self):
        """Test that caching prevents duplicate calls to Web3Manager."""
        # Arrange
        tx_hash = "0xa1b2c3d4e5f6789012345678901234567890abcdef123456789012345678901234"
        eth_price_usd = 3000.0
        
        mock_receipt = {
            'gasUsed': 100000,
            'effectiveGasPrice': Web3.to_wei(20, 'gwei')
        }
        
        # Configure mock Web3Manager
        self.mock_web3_manager.get_transaction_receipt = Mock(return_value=mock_receipt)
        
        # Act - Call twice with same tx_hash
        result1 = await self.calculator.calculate_tx_cost_usd(tx_hash, eth_price_usd)
        result2 = await self.calculator.calculate_tx_cost_usd(tx_hash, eth_price_usd)
        
        # Assert
        assert result1 is not None, "First call should succeed"
        assert result2 is not None, "Second call should succeed"
        assert result1 == result2, "Both calls should return identical results"
        
        # Critical test: Web3Manager should be called only ONCE due to caching
        self.mock_web3_manager.get_transaction_receipt.assert_called_once_with(tx_hash)
        assert self.mock_web3_manager.get_transaction_receipt.call_count == 1, \
            "Web3Manager should be called only once due to caching"
    
    @pytest.mark.asyncio
    async def test_fallback_to_gas_price_when_effective_gas_price_missing(self):
        """Test fallback to gasPrice when effectiveGasPrice is not available."""
        # Arrange
        tx_hash = "0xold_transaction_hash_without_eip1559"
        eth_price_usd = 2500.0
        
        # Mock receipt without effectiveGasPrice (older transaction)
        mock_receipt = {
            'gasUsed': 80000,
            'effectiveGasPrice': None  # Missing for older transactions
        }
        
        # Mock original transaction with gasPrice
        mock_transaction = {
            'gasPrice': Web3.to_wei(18, 'gwei')  # 18 Gwei
        }
        
        # Configure mocks
        self.mock_web3_manager.get_transaction_receipt = Mock(return_value=mock_receipt)
        self.mock_web3_manager.web3 = Mock()
        self.mock_web3_manager.web3.eth = Mock()
        self.mock_web3_manager.web3.eth.get_transaction = Mock(return_value=mock_transaction)
        
        # Act
        result = await self.calculator.calculate_tx_cost_usd(tx_hash, eth_price_usd)
        
        # Assert
        assert result is not None, "Should handle fallback to gasPrice"
        
        # Expected: 80000 * 18 Gwei * $2500 = $3.60
        expected_cost = 3.6  # 80k * 18 * 2500 / 10^18
        assert abs(result - expected_cost) < 0.01, f"Expected ~${expected_cost}, got ${result:.2f}"
        
        # Verify both receipt and transaction were fetched
        self.mock_web3_manager.get_transaction_receipt.assert_called_once_with(tx_hash)
        self.mock_web3_manager.web3.eth.get_transaction.assert_called_once_with(tx_hash)
    
    @pytest.mark.asyncio
    async def test_invalid_gas_data_returns_none(self):
        """Test that invalid gas data (zero values) returns None."""
        # Arrange
        tx_hash = "0xinvalid_gas_data_transaction"
        eth_price_usd = 3000.0
        
        # Mock receipt with invalid gas data
        mock_receipt = {
            'gasUsed': 0,  # Invalid
            'effectiveGasPrice': 0  # Invalid
        }
        
        self.mock_web3_manager.get_transaction_receipt = Mock(return_value=mock_receipt)
        
        # Act
        result = await self.calculator.calculate_tx_cost_usd(tx_hash, eth_price_usd)
        
        # Assert
        assert result is None, "Should return None for invalid gas data"
    
    @pytest.mark.asyncio
    async def test_web3_exception_handling(self):
        """Test proper handling of Web3 exceptions."""
        # Arrange
        tx_hash = "0xerror_causing_transaction"
        eth_price_usd = 3000.0
        
        # Configure mock to raise exception
        self.mock_web3_manager.get_transaction_receipt = Mock(side_effect=Exception("Web3 connection error"))
        
        # Act
        result = await self.calculator.calculate_tx_cost_usd(tx_hash, eth_price_usd)
        
        # Assert
        assert result is None, "Should return None when Web3 exception occurs"
        self.mock_web3_manager.get_transaction_receipt.assert_called_once_with(tx_hash)
    
    def test_cache_clearing_functionality(self):
        """Test that cache can be cleared properly."""
        # Arrange
        # Pre-populate cache
        test_tx_hash = "0xtest123"
        self.calculator._gas_cost_cache[test_tx_hash] = 25.50
        
        # Verify cache has data
        assert len(self.calculator._gas_cost_cache) == 1
        
        # Act
        self.calculator.clear_cache()
        
        # Assert
        assert len(self.calculator._gas_cost_cache) == 0, "Cache should be empty after clearing"


# Test markers for categorization
pytestmark = pytest.mark.gas_calculator
