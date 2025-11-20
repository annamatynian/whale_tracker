"""
LP Health Tracker Test Suite
============================

Comprehensive test suite for LP Health Tracker project.

Test Structure:
- test_data_analyzer.py: MVP tests for mathematical calculations (Phase 1)
- test_extensions.py: Extended tests for future iterations (Phase 2)
- fixtures/: Test data and mock responses
- conftest.py: Shared fixtures and configuration

Usage:
    # Run all MVP tests
    pytest tests/test_data_analyzer.py -v
    
    # Run specific test
    pytest tests/test_data_analyzer.py::test_no_price_change_zero_il -v
    
    # Run with coverage
    pytest tests/ --cov=src --cov-report=html
    
    # Run only fast tests (exclude slow/performance)
    pytest tests/ -m "not slow"

Markers:
    @pytest.mark.unit - Fast, isolated unit tests
    @pytest.mark.integration - Tests requiring external APIs
    @pytest.mark.slow - Tests that may take several seconds
    @pytest.mark.performance - Performance benchmark tests
"""

__version__ = "1.0.0"
__author__ = "LP Health Tracker Team"
