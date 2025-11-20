#!/usr/bin/env python3
"""
Install Testing Dependencies
===========================

Install all required dependencies for testing.

Author: Generated for DeFi-RAG Project
"""

import subprocess
import sys

def main():
    """Install testing dependencies."""
    print("📦 Installing testing dependencies...")
    print("=" * 50)
    
    try:
        # Install requirements_testing.txt
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_testing.txt"
        ], check=True)
        
        print("✅ Dependencies installed successfully!")
        
        # Verify key packages
        print("\n🔍 Verifying installations...")
        
        packages_to_check = [
            ("pytest", "pytest"),
            ("pytest_asyncio", "pytest-asyncio"),
            ("pydantic", "pydantic"),
        ]
        
        for module, name in packages_to_check:
            try:
                imported = __import__(module)
                if hasattr(imported, '__version__'):
                    print(f"   ✅ {name}: {imported.__version__}")
                else:
                    print(f"   ✅ {name}: available")
            except ImportError:
                print(f"   ❌ {name}: missing")
        
        print("\n🎉 Ready to run regression tests!")
        print("Run: python full_regression_test.py")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return 1
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
