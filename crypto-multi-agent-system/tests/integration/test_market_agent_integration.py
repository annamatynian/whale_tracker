"""
Integration Tests for Market Conditions Agent

Tests real API interactions and architectural principles.
"""

import pytest
import sys
import os
import time
import json
import requests
from unittest.mock import patch

# Add the agents directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agents', 'market_conditions'))

from market_agent import analyze_market_conditions, fetch_coingecko_global_data, MarketConditionsReport


class TestRealAPIIntegration:
    """Test integration with real CoinGecko API."""
    
    @pytest.mark.integration
    def test_real_api_call_success(self):
        """Test that we can successfully call the real CoinGecko API."""
        # Act
        api_data, response_time = fetch_coingecko_global_data()
        
        # Assert
        assert api_data is not None, "API should return data"
        assert isinstance(api_data, dict), "API should return a dictionary"
        assert 'data' in api_data, "API response should have 'data' field"
        assert 'market_cap_percentage' in api_data['data'], "Should have market_cap_percentage"
        assert 'usdt' in api_data['data']['market_cap_percentage'], "Should have USDT dominance"
        
        # Check response time is reasonable (less than 5 seconds)
        assert response_time is not None
        assert response_time < 5000, f"API response too slow: {response_time}ms"
        
        # Check USDT dominance is a reasonable number
        usdt_dominance = api_data['data']['market_cap_percentage']['usdt']
        assert isinstance(usdt_dominance, (int, float)), "USDT dominance should be numeric"
        assert 0 <= usdt_dominance <= 100, f"USDT dominance should be 0-100%, got {usdt_dominance}"
    
    @pytest.mark.integration
    def test_full_analysis_with_real_api(self):
        """Test complete analysis flow with real API."""
        # Act
        result = analyze_market_conditions()
        
        # Assert basic structure
        assert isinstance(result, MarketConditionsReport)
        assert result.market_regime in ["AGGRESSIVE", "CONSERVATIVE", "UNKNOWN"]
        assert 0 <= result.usdt_dominance_percentage <= 100
        assert result.data_source == "CoinGecko"
        
        # Assert timing metrics are present
        assert result.processing_time_ms is not None
        assert result.processing_time_ms > 0
        
        # If API call succeeded, we should have API response time
        if result.market_regime != "UNKNOWN":
            assert result.api_response_time_ms is not None
            assert result.api_response_time_ms > 0
    
    @pytest.mark.integration
    def test_pydantic_validation_with_real_data(self):
        """Test that real API data passes Pydantic validation."""
        # Act
        result = analyze_market_conditions()
        
        # Assert we can serialize to JSON without errors
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)
        
        # Assert we can parse it back
        data = json.loads(json_str)
        assert data['market_regime'] in ['AGGRESSIVE', 'CONSERVATIVE', 'UNKNOWN']
        assert isinstance(data['usdt_dominance_percentage'], (int, float))
        assert data['data_source'] == 'CoinGecko'
        
        # Validate the Pydantic model can be reconstructed
        reconstructed = MarketConditionsReport(**data)
        assert reconstructed.market_regime == result.market_regime
        assert reconstructed.usdt_dominance_percentage == result.usdt_dominance_percentage


class TestArchitecturalPrinciples:
    """Test adherence to architectural principles."""
    
    def test_principle_4_fault_tolerance_bad_url(self):
        """Test Principle #4: Fault tolerance with bad URL."""
        # Arrange - patch the URL to something invalid
        with patch('market_agent.fetch_coingecko_global_data') as mock_fetch:
            # Simulate network failure
            mock_fetch.return_value = (None, None)
            
            # Act
            result = analyze_market_conditions()
            
            # Assert - should not crash, should return UNKNOWN gracefully
            assert result.market_regime == "UNKNOWN"
            assert result.usdt_dominance_percentage == 0.0
            assert result.processing_time_ms is not None
    
    def test_principle_4_fault_tolerance_network_error(self):
        """Test Principle #4: Fault tolerance with network timeout."""
        # Arrange - patch requests to raise timeout
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
            
            # Act - should not crash due to retry mechanism
            api_data, response_time = fetch_coingecko_global_data()
            
            # Assert
            assert api_data is None
            assert response_time is None
    
    def test_principle_6_observability_logging(self, caplog):
        """Test Principle #6: Observability through logging."""
        import logging
        
        # Arrange
        caplog.set_level(logging.INFO)
        
        # Act
        with patch('market_agent.fetch_coingecko_global_data', return_value=({
            'data': {'market_cap_percentage': {'usdt': 4.0}}
        }, 100.0)):
            result = analyze_market_conditions()
        
        # Assert logging messages are present
        log_messages = [record.message for record in caplog.records]
        
        # Should have start message
        start_messages = [msg for msg in log_messages if "Starting market conditions analysis" in msg]
        assert len(start_messages) > 0, "Should log analysis start"
        
        # Should have completion message with results
        completion_messages = [msg for msg in log_messages if "Analysis complete" in msg]
        assert len(completion_messages) > 0, "Should log analysis completion"
        
        # Completion message should include key metrics
        completion_msg = completion_messages[0]
        assert "USDT Dominance:" in completion_msg
        assert "Market Regime:" in completion_msg
        assert "API:" in completion_msg  # Performance metrics
        assert "Total:" in completion_msg
    
    def test_principle_7_reproducibility_git_hash(self):
        """Test Principle #7: Reproducibility with git hash."""
        # Act
        result = analyze_market_conditions()
        
        # Assert
        # Git hash should either be a string or None
        assert result.git_commit_hash is None or isinstance(result.git_commit_hash, str)
        
        # If git is available, hash should be non-empty
        if result.git_commit_hash is not None:
            assert len(result.git_commit_hash) > 0
            assert result.git_commit_hash.strip() == result.git_commit_hash  # No whitespace
    
    def test_principle_8_security_no_hardcoded_secrets(self):
        """Test Principle #8: No hardcoded secrets in code."""
        # Read the source file and check for common secret patterns
        agent_file = os.path.join(
            os.path.dirname(__file__), '..', '..', 
            'agents', 'market_conditions', 'market_agent.py'
        )
        
        with open(agent_file, 'r') as f:
            source_code = f.read()
        
        # Assert no common secret patterns
        forbidden_patterns = [
            'api_key = "',
            'api_key="',
            'secret = "',
            'secret="',
            'token = "',
            'token="',
            'password = "',
            'password="'
        ]
        
        for pattern in forbidden_patterns:
            assert pattern.lower() not in source_code.lower(), \
                f"Found potential hardcoded secret pattern: {pattern}"


class TestPerformanceBaseline:
    """Establish performance baselines for monitoring."""
    
    @pytest.mark.integration
    def test_performance_baseline(self):
        """Establish baseline performance metrics."""
        # Run analysis multiple times to get average
        results = []
        for _ in range(3):
            result = analyze_market_conditions()
            if result.api_response_time_ms is not None:
                results.append({
                    'api_time': result.api_response_time_ms,
                    'total_time': result.processing_time_ms
                })
            time.sleep(1)  # Be nice to the API
        
        if results:
            avg_api_time = sum(r['api_time'] for r in results) / len(results)
            avg_total_time = sum(r['total_time'] for r in results) / len(results)
            
            print(f"\n📊 Performance Baseline:")
            print(f"   Average API Response: {avg_api_time:.1f}ms")
            print(f"   Average Total Time: {avg_total_time:.1f}ms")
            
            # Basic performance assertions
            assert avg_api_time < 2000, f"API too slow: {avg_api_time}ms (baseline: <2000ms)"
            assert avg_total_time < 2500, f"Total processing too slow: {avg_total_time}ms (baseline: <2500ms)"


class TestRetryMechanism:
    """Test the retry mechanism functionality."""
    
    def test_retry_mechanism_recovers_from_transient_failure(self):
        """Test that retry mechanism recovers from temporary failures."""
        call_count = 0
        
        def mock_requests_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:  # Fail first 2 attempts
                raise requests.exceptions.ConnectionError("Temporary failure")
            else:  # Succeed on 3rd attempt
                mock_response = type('MockResponse', (), {})()
                mock_response.status_code = 200
                mock_response.raise_for_status = lambda: None
                mock_response.json = lambda: {
                    'data': {'market_cap_percentage': {'usdt': 4.2}}
                }
                return mock_response
        
        # Act
        with patch('requests.get', side_effect=mock_requests_get):
            api_data, response_time = fetch_coingecko_global_data()
        
        # Assert
        assert call_count == 3, "Should have retried 3 times total"
        assert api_data is not None, "Should eventually succeed"
        assert api_data['data']['market_cap_percentage']['usdt'] == 4.2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
