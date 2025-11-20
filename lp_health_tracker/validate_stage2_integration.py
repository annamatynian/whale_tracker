#!/usr/bin/env python3
"""
Quick validation test for Stage 2 integration
=============================================

Quick test to verify that the new Stage 2 integration test is properly set up.
"""

import sys
import os
sys.path.append('src')
sys.path.append('tests')

def test_stage2_integration_setup():
    """Test that Stage 2 integration test setup is working."""
    print("🧪 Testing Stage 2 Integration Setup")
    print("=" * 40)
    
    # Test 1: Import the test module
    try:
        import test_integration_stage2
        print("✅ Stage 2 integration test module imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import Stage 2 integration test: {e}")
        return False
    
    # Test 2: Check pytest markers are available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not available")
        return False
    
    # Test 3: Try to import fixtures (basic validation)
    try:
        from conftest import stage2_position_data, live_data_provider
        print("✅ Stage 2 fixtures are available")
    except ImportError as e:
        print(f"⚠️ Some Stage 2 fixtures might not be available: {e}")
    
    # Test 4: Check that key test classes exist
    test_classes = [
        'TestStage2LiveDataProvider',
        'TestStage2DateParsing', 
        'TestStage2MultiPoolManagerLiveData',
        'TestStage2ErrorHandling',
        'TestStage2CompleteWorkflow'
    ]
    
    for class_name in test_classes:
        if hasattr(test_integration_stage2, class_name):
            print(f"✅ {class_name} test class found")
        else:
            print(f"❌ {class_name} test class missing")
            return False
    
    print("\n🎉 Stage 2 Integration Test Setup: ✅ READY")
    return True

def test_basic_fixtures():
    """Test that basic fixtures work."""
    print("\n🔧 Testing Stage 2 Fixtures")
    print("=" * 30)
    
    # Test stage2_position_data fixture logic
    try:
        from datetime import datetime, timedelta
        
        # Simulate the fixture
        entry_date = (datetime.now() - timedelta(days=30)).isoformat()
        position_data = {
            'name': 'WETH-USDC Stage 2 Position',
            'entry_date': entry_date,
            'gas_costs_usd': 75.0,
        }
        
        # Validate entry_date parsing
        parsed_date = datetime.fromisoformat(entry_date.replace('Z', '+00:00'))
        days_held = (datetime.now() - parsed_date).days
        
        assert 29 <= days_held <= 31, f"Days held calculation seems wrong: {days_held}"
        assert 'days_held_mock' not in position_data, "Should not have days_held_mock in Stage 2"
        
        print(f"✅ Stage 2 position data: {days_held} days held (calculated from real date)")
        
    except Exception as e:
        print(f"❌ Stage 2 fixture test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 STAGE 2 INTEGRATION TEST VALIDATION")
    print("=" * 45)
    
    success = True
    
    # Run validation tests
    success &= test_stage2_integration_setup()
    success &= test_basic_fixtures()
    
    print(f"\n📋 VALIDATION RESULT: {'✅ SUCCESS' if success else '❌ NEEDS WORK'}")
    
    if success:
        print("🚀 Ready to run: pytest tests/test_integration_stage2.py -v -m stage2")
    else:
        print("⚠️ Fix the issues above before running Stage 2 tests")
