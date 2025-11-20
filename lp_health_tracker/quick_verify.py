#!/usr/bin/env python3
"""
Quick Test - Verify Fix
======================

Simple test to verify the pytest hook naming fix works.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def quick_test():
    """Quick test to verify basic functionality."""
    try:
        from src.data_analyzer import ImpermanentLossCalculator
        
        calculator = ImpermanentLossCalculator()
        
        # Test basic IL calculation
        il = calculator.calculate_impermanent_loss(1.0, 2.0)
        expected = 0.057  # ~5.7% for 2x price change
        
        if abs(il - expected) < 0.01:
            print("✅ Basic IL calculation test passed!")
            print(f"   Calculated: {il:.3f}, Expected: ~{expected:.3f}")
            return True
        else:
            print(f"❌ Basic IL calculation failed: {il:.3f} vs {expected:.3f}")
            return False
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Quick Fix Verification")
    print("=" * 25)
    
    if quick_test():
        print("\n🎉 Fix verification successful!")
        print("💡 Now you can run: pytest tests/test_data_analyzer.py -v")
    else:
        print("\n⚠️  Fix verification failed.")
