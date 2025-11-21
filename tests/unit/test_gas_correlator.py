"""
Unit tests for GasCorrelator (Signal #2)
"""

import pytest
from src.analyzers.gas_correlator import GasCorrelator, GasCorrelationResult


class TestGasCorrelatorInitialization:
    """Test GasCorrelator initialization"""

    def test_init(self):
        """Test initialization"""
        correlator = GasCorrelator()
        assert correlator.EXACT_MATCH_TOLERANCE == 0
        assert correlator.CLOSE_MATCH_THRESHOLD_GWEI == 0.1


class TestGasCorrelation:
    """Test gas price correlation detection"""

    def test_exact_match_strongest_signal(self):
        """Test exact gas price match - 95% confidence"""
        correlator = GasCorrelator()

        whale_tx = {'gasPrice': 50000000000}  # 50 Gwei
        intermediate_tx = {'gasPrice': 50000000000}  # 50 Gwei

        result = correlator.check_gas_correlation(whale_tx, intermediate_tx)

        assert result.match is True
        assert result.confidence == 95
        assert result.correlation_type == 'exact'
        assert result.gas_diff_gwei == 0.0
        assert 'same entity' in result.details.lower()

    def test_close_match(self):
        """Test close gas price match (within 0.1 Gwei) - 80% confidence"""
        correlator = GasCorrelator()

        whale_tx = {'gasPrice': 50000000000}  # 50.0 Gwei
        intermediate_tx = {'gasPrice': 50050000000}  # 50.05 Gwei

        result = correlator.check_gas_correlation(whale_tx, intermediate_tx)

        assert result.match is True
        assert result.confidence == 80
        assert result.correlation_type == 'close'
        assert result.gas_diff_gwei == pytest.approx(0.05, abs=0.001)

    def test_close_match_edge_case(self):
        """Test close match at exact threshold"""
        correlator = GasCorrelator()

        whale_tx = {'gasPrice': 50000000000}  # 50.0 Gwei
        intermediate_tx = {'gasPrice': 50100000000}  # 50.1 Gwei (exactly at threshold)

        result = correlator.check_gas_correlation(whale_tx, intermediate_tx)

        assert result.match is True
        assert result.confidence == 80
        assert result.correlation_type == 'close'

    def test_priority_fee_match(self):
        """Test EIP-1559 priority fee match - 70% confidence"""
        correlator = GasCorrelator()

        whale_tx = {
            'gasPrice': 50000000000,
            'maxFeePerGas': 60000000000,
            'maxPriorityFeePerGas': 2000000000  # Same priority fee
        }
        intermediate_tx = {
            'gasPrice': 55000000000,  # Different base gas
            'maxFeePerGas': 65000000000,
            'maxPriorityFeePerGas': 2000000000  # Same priority fee
        }

        result = correlator.check_gas_correlation(whale_tx, intermediate_tx)

        assert result.match is True
        assert result.confidence == 70
        assert result.correlation_type == 'strategy'
        assert 'same wallet' in result.details.lower()

    def test_no_correlation(self):
        """Test no gas correlation"""
        correlator = GasCorrelator()

        whale_tx = {'gasPrice': 50000000000}  # 50 Gwei
        intermediate_tx = {'gasPrice': 70000000000}  # 70 Gwei

        result = correlator.check_gas_correlation(whale_tx, intermediate_tx)

        assert result.match is False
        assert result.confidence == 0
        assert result.correlation_type == 'none'
        assert result.gas_diff_gwei == 20.0

    def test_missing_gas_price(self):
        """Test handling missing gas price"""
        correlator = GasCorrelator()

        whale_tx = {}
        intermediate_tx = {'gasPrice': 50000000000}

        result = correlator.check_gas_correlation(whale_tx, intermediate_tx)

        assert result.match is False
        assert result.confidence == 0
        assert 'Missing gas price' in result.details


class TestGasPriceExtraction:
    """Test gas price extraction from transactions"""

    def test_extract_legacy_gas_price_int(self):
        """Test extracting legacy gasPrice (int)"""
        correlator = GasCorrelator()

        tx = {'gasPrice': 50000000000}
        gas = correlator._extract_gas_price(tx)

        assert gas == 50000000000

    def test_extract_legacy_gas_price_hex(self):
        """Test extracting legacy gasPrice (hex string)"""
        correlator = GasCorrelator()

        tx = {'gasPrice': '0xba43b7400'}  # 50000000000 in hex
        gas = correlator._extract_gas_price(tx)

        assert gas == 50000000000

    def test_extract_legacy_gas_price_string(self):
        """Test extracting legacy gasPrice (decimal string)"""
        correlator = GasCorrelator()

        tx = {'gasPrice': '50000000000'}
        gas = correlator._extract_gas_price(tx)

        assert gas == 50000000000

    def test_extract_eip1559_gas_price_int(self):
        """Test extracting EIP-1559 maxFeePerGas (int)"""
        correlator = GasCorrelator()

        tx = {'maxFeePerGas': 60000000000}
        gas = correlator._extract_gas_price(tx)

        assert gas == 60000000000

    def test_extract_eip1559_gas_price_hex(self):
        """Test extracting EIP-1559 maxFeePerGas (hex)"""
        correlator = GasCorrelator()

        tx = {'maxFeePerGas': '0xdf8475800'}  # 60000000000 in hex
        gas = correlator._extract_gas_price(tx)

        assert gas == 60000000000

    def test_extract_missing_gas_price(self):
        """Test extracting when no gas price present"""
        correlator = GasCorrelator()

        tx = {'nonce': 5}  # No gas fields
        gas = correlator._extract_gas_price(tx)

        assert gas is None

    def test_extract_none_gas_price(self):
        """Test extracting when gasPrice is None"""
        correlator = GasCorrelator()

        tx = {'gasPrice': None}
        gas = correlator._extract_gas_price(tx)

        assert gas is None


class TestPriorityFeeMatching:
    """Test EIP-1559 priority fee matching"""

    def test_priority_fee_exact_match_int(self):
        """Test exact priority fee match (int)"""
        correlator = GasCorrelator()

        whale_tx = {'maxPriorityFeePerGas': 2000000000}
        intermediate_tx = {'maxPriorityFeePerGas': 2000000000}

        match = correlator._check_priority_fee_match(whale_tx, intermediate_tx)

        assert match is True

    def test_priority_fee_exact_match_hex(self):
        """Test exact priority fee match (hex)"""
        correlator = GasCorrelator()

        whale_tx = {'maxPriorityFeePerGas': '0x77359400'}  # 2000000000
        intermediate_tx = {'maxPriorityFeePerGas': '0x77359400'}

        match = correlator._check_priority_fee_match(whale_tx, intermediate_tx)

        assert match is True

    def test_priority_fee_no_match(self):
        """Test no priority fee match"""
        correlator = GasCorrelator()

        whale_tx = {'maxPriorityFeePerGas': 2000000000}
        intermediate_tx = {'maxPriorityFeePerGas': 3000000000}

        match = correlator._check_priority_fee_match(whale_tx, intermediate_tx)

        assert match is False

    def test_priority_fee_missing(self):
        """Test when priority fee is missing"""
        correlator = GasCorrelator()

        whale_tx = {'gasPrice': 50000000000}  # No priority fee
        intermediate_tx = {'maxPriorityFeePerGas': 2000000000}

        match = correlator._check_priority_fee_match(whale_tx, intermediate_tx)

        assert match is False

    def test_priority_fee_both_missing(self):
        """Test when both priority fees are missing"""
        correlator = GasCorrelator()

        whale_tx = {'gasPrice': 50000000000}
        intermediate_tx = {'gasPrice': 50000000000}

        match = correlator._check_priority_fee_match(whale_tx, intermediate_tx)

        assert match is False


class TestGasPriceFormatting:
    """Test gas price formatting utilities"""

    def test_format_gas_price_gwei(self):
        """Test converting Wei to Gwei"""
        correlator = GasCorrelator()

        gwei = correlator.format_gas_price_gwei(50000000000)
        assert gwei == 50.0

        gwei = correlator.format_gas_price_gwei(1000000000)
        assert gwei == 1.0

        gwei = correlator.format_gas_price_gwei(100000000000)
        assert gwei == 100.0


class TestConfidenceFromDifference:
    """Test confidence calculation from gas difference"""

    def test_confidence_exact_match(self):
        """Test confidence for exact match"""
        correlator = GasCorrelator()
        confidence = correlator.calculate_confidence_from_diff(0.0)
        assert confidence == 95

    def test_confidence_very_close(self):
        """Test confidence for very close (0.05 Gwei)"""
        correlator = GasCorrelator()
        confidence = correlator.calculate_confidence_from_diff(0.05)
        assert confidence == 80

    def test_confidence_close(self):
        """Test confidence for close (0.3 Gwei)"""
        correlator = GasCorrelator()
        confidence = correlator.calculate_confidence_from_diff(0.3)
        assert confidence == 60

    def test_confidence_somewhat_close(self):
        """Test confidence for somewhat close (0.8 Gwei)"""
        correlator = GasCorrelator()
        confidence = correlator.calculate_confidence_from_diff(0.8)
        assert confidence == 40

    def test_confidence_far(self):
        """Test confidence for far (5 Gwei)"""
        correlator = GasCorrelator()
        confidence = correlator.calculate_confidence_from_diff(5.0)
        assert confidence == 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_zero_gas_price(self):
        """Test zero gas price (shouldn't happen but handle it)"""
        correlator = GasCorrelator()

        whale_tx = {'gasPrice': 0}
        intermediate_tx = {'gasPrice': 0}

        result = correlator.check_gas_correlation(whale_tx, intermediate_tx)

        # Zero gas prices are exact match
        assert result.match is True
        assert result.confidence == 95

    def test_exception_handling(self):
        """Test exception handling in check_gas_correlation"""
        correlator = GasCorrelator()

        # Invalid transaction (will cause exception in processing)
        whale_tx = {'gasPrice': 'invalid'}
        intermediate_tx = {'gasPrice': 50000000000}

        # Should not raise exception, should return error result
        result = correlator.check_gas_correlation(whale_tx, intermediate_tx)

        assert result.match is False
        assert result.correlation_type == 'error'
        assert 'Error' in result.details
