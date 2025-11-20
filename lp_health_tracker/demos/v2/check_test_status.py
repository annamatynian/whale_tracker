#!/usr/bin/env python3
"""
Quick Test Status Check - After Fixes
===================================
"""

import subprocess
import sys
import os

def main():
    os.chdir("C:\\Users\\annam\\Documents\\DeFi-RAG-Project\\lp_health_tracker")
    print("🧪 Checking test status after applying fixes...")
    print("=" * 50)
    
    try:
        # Run a quick subset of tests to see current status
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_data_analyzer.py", 
            "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=60)
        
        print("RETURN CODE:", result.returncode)
        print("\nSTDOUT:")
        print(result.stdout[-2000:])  # Last 2000 chars
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr[-1000:])  # Last 1000 chars
            
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
    except Exception as e:
        print(f"❌ Error running tests: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Check completed. Review output above.")

if __name__ == "__main__":
    main()
