#!/usr/bin/env python3
"""
Quick validation script for LP Health Tracker system
====================================================

This script validates basic imports. For comprehensive testing,
use the pytest test suite in tests/ directory.

Usage: python quick_check.py
"""

import sys
import os

def main():
    """Quick validation that basic imports work."""
    print("🧪 LP Health Tracker - Quick Import Check")
    print("=" * 50)
    
    try:
        # Test basic imports
        project_path = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(project_path)
        
        from src.simple_multi_pool import SimpleMultiPoolManager
        from src.data_analyzer import ImpermanentLossCalculator
        
        print("✅ All imports successful")
        print("✅ System ready for use")
        print("✅ Run 'pytest tests/' for comprehensive testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    main()
