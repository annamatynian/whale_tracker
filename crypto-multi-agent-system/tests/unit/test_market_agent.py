"""
Unit Tests for Market Conditions Agent

Tests the core logic in isolation using mocks.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import os

# Add the agents directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agents', 'market_conditions'))

from market_agent import analyze_market_conditions, fetch_coingecko_global_data, MarketConditionsReport


class TestMarketConditionsLogic:
    """Test the core business logic of market conditions analysis."""
    
    def test_aggressive_market_regime(self):
        """Test that USDT dominance < 4.5% returns AGGRESSIVE regime."""
        # Arrange
        mock_api_response = {
            'data': {
                'market_cap_percentage': {
                    'usdt': 3.2  # Below 4.5% threshold
                }
            }
        }
        
        # Act
        with patch('market_agent.fetch_coingecko_global_data', return_value=(mock_api_response, 150.0)):
            with patch('market_agent.get_current_git_hash', return_value='abc123'):
                result = analyze_market_conditions()
        
        # Assert
        assert result.market_regime == "AGGRESSIVE"
        assert result.usdt_dominance_percentage == 3.2
        assert result.data_source == "CoinGecko"
        assert result.git_commit_hash == "abc123"
        assert result.api_response_time_ms == 150.0
        assert result.processing_time_ms is not None
    
    def test_conservative_market_regime(self):
        """Test that USDT dominance > 4.5% returns CONSERVATIVE regime."""
        # Arrange
        mock_api_response = {
            'data': {
                'market_cap_percentage': {
                    'usdt': 5.8  # Above 4.5% threshold
                }
            }
        }
        
        # Act
        with patch('market_agent.fetch_coingecko_global_data', return_value=(mock_api_response, 200.0)):
            with patch('market_agent.get_current_git_hash', return_value='def456'):
                result = analyze_market_conditions()
        
        # Assert
        assert result.market_regime == "CONSERVATIVE"
        assert result.usdt_dominance_percentage == 5.8
        assert result.git_commit_hash == "def456"
        assert result.api_response_time_ms == 200.0
    
    def test_boundary_value_exactly_threshold(self):
        """Test behavior when USDT dominance is exactly 4.5%."""
        # Arrange
        mock_api_response = {
            'data': {
                'market_cap_percentage': {
                    'usdt': 4.5  # Exactly at threshold
                }
            }
        }
        
        # Act
        with patch('market_agent.fetch_coingecko_global_data', return_value=(mock_api_response, 120.0)):
            with patch('market_agent.get_current_git_hash', return_value='ghi789'):
                result = analyze_market_conditions()
        
        # Assert
        # Since 4.5 is NOT < 4.5, it should be CONSERVATIVE
        assert result.market_regime == "CONSERVATIVE"
        assert result.usdt_dominance_percentage == 4.5
    
    def test_api_failure_returns_unknown(self):
        """Test that API failure returns UNKNOWN state without crashing."""
        # Arrange - simulate API failure
        with patch('market_agent.fetch_coingecko_global_data', return_value=(None, None)):
            with patch('market_agent.get_current_git_hash', return_value='fail123'):
                result = analyze_market_conditions()
        
        # Assert
        assert result.market_regime == "UNKNOWN"
        assert result.usdt_dominance_percentage == 0.0
        assert result.git_commit_hash == "fail123"
        assert result.api_response_time_ms is None
        assert result.processing_time_ms is not None
    
    def test_malformed_api_response_missing_field(self):
        """Test handling of API response missing required fields."""
        # Arrange - API response missing 'market_cap_percentage'
        mock_api_response = {
            'data': {
                'some_other_field': 'value'
                # Missing 'market_cap_percentage'
            }
        }
        
        # Act
        with patch('market_agent.fetch_coingecko_global_data', return_value=(mock_api_response, 300.0)):
            with patch('market_agent.get_current_git_hash', return_value='error123'):
                result = analyze_market_conditions()
        
        # Assert
        assert result.market_regime == "UNKNOWN"
        assert result.usdt_dominance_percentage == 0.0
        assert result.api_response_time_ms == 300.0
    
    def test_malformed_api_response_missing_usdt_field(self):
        """Test handling of API response missing USDT field specifically."""
        # Arrange - API response missing 'usdt' in market_cap_percentage
        mock_api_response = {
            'data': {
                'market_cap_percentage': {
                    'btc': 45.2,
                    'eth': 18.3
                    # Missing 'usdt'
                }
            }
        }
        
        # Act
        with patch('market_agent.fetch_coingecko_global_data', return_value=(mock_api_response, 180.0)):
            with patch('market_agent.get_current_git_hash', return_value='usdt_error'):
                result = analyze_market_conditions()
        
        # Assert
        assert result.market_regime == "UNKNOWN"
        assert result.usdt_dominance_percentage == 0.0


class TestPydanticValidation:
    """Test that Pydantic validation works correctly."""
    
    def test_valid_report_creation(self):
        """Test creating a valid MarketConditionsReport."""
        # Arrange & Act
        report = MarketConditionsReport(
            market_regime="AGGRESSIVE",
            usdt_dominance_percentage=3.5,
            git_commit_hash="abc123",
            api_response_time_ms=150.0,
            processing_time_ms=200.0
        )
        
        # Assert
        assert report.market_regime == "AGGRESSIVE"
        assert report.usdt_dominance_percentage == 3.5
        assert report.data_source == "CoinGecko"  # Default value
        assert isinstance(report.analysis_timestamp, datetime)
    
    def test_invalid_market_regime_validation(self):
        """Test that invalid market regime values are rejected."""
        with pytest.raises(ValueError):
            MarketConditionsReport(
                market_regime="INVALID_REGIME",  # Should only accept AGGRESSIVE, CONSERVATIVE, UNKNOWN
                usdt_dominance_percentage=3.5
            )
    
    def test_invalid_dominance_percentage_validation(self):
        """Test that invalid dominance percentages are rejected."""
        # Test negative value
        with pytest.raises(ValueError):
            MarketConditionsReport(
                market_regime="AGGRESSIVE",
                usdt_dominance_percentage=-1.0  # Should be >= 0
            )
        
        # Test value over 100
        with pytest.raises(ValueError):
            MarketConditionsReport(
                market_regime="CONSERVATIVE",
                usdt_dominance_percentage=150.0  # Should be <= 100
            )
    
    def test_json_serialization(self):
        """Test that the report can be serialized to JSON."""
        # Arrange
        report = MarketConditionsReport(
            market_regime="CONSERVATIVE",
            usdt_dominance_percentage=5.2,
            git_commit_hash="json_test"
        )
        
        # Act
        json_str = report.model_dump_json()
        
        # Assert
        assert isinstance(json_str, str)
        assert "CONSERVATIVE" in json_str
        assert "5.2" in json_str
        assert "json_test" in json_str


class TestUtilityFunctions:
    """Test utility functions in isolation."""
    
    @patch('subprocess.check_output')
    def test_git_hash_success(self, mock_subprocess):
        """Test successful git hash retrieval."""
        from market_agent import get_current_git_hash
        
        # Arrange
        mock_subprocess.return_value = b'abc123\n'
        
        # Act
        result = get_current_git_hash()
        
        # Assert
        assert result == "abc123"
        mock_subprocess.assert_called_once()
    
    @patch('subprocess.check_output')
    def test_git_hash_failure(self, mock_subprocess):
        """Test git hash retrieval when git is not available."""
        from market_agent import get_current_git_hash
        
        # Arrange
        mock_subprocess.side_effect = FileNotFoundError("git not found")
        
        # Act
        result = get_current_git_hash()
        
        # Assert
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
