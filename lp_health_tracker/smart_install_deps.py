#!/usr/bin/env python3
"""
Smart Dependencies Installer for Python 3.13
============================================

Handles installation issues with Python 3.13 and pydantic dependencies.

Author: Generated for DeFi-RAG Project
"""

import subprocess
import sys
import platform

def upgrade_pip():
    """Upgrade pip first."""
    print("🔧 Upgrading pip...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True, capture_output=True, text=True)
        print("✅ pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  pip upgrade failed: {e}")
        return False

def install_strategy_1():
    """Try updated requirements with newer versions."""
    print("\n📦 Strategy 1: Installing updated dependencies...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_testing_updated.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ Updated dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Strategy 1 failed: {e}")
        return False

def install_strategy_2():
    """Try installing specific packages individually."""
    print("\n📦 Strategy 2: Installing packages individually...")
    
    packages = [
        "pydantic>=2.10.0",
        "pytest>=8.0.0", 
        "pytest-asyncio>=0.24.0",
        "aiohttp>=3.10.0",
        "requests>=2.32.0",
        "python-dotenv>=1.0.0",
        "APScheduler>=3.10.4",
        "colorlog>=6.8.0"
    ]
    
    failed_packages = []
    
    for package in packages:
        try:
            print(f"   Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True, text=True)
            print(f"   ✅ {package}")
        except subprocess.CalledProcessError:
            print(f"   ❌ {package}")
            failed_packages.append(package)
    
    if not failed_packages:
        print("✅ All packages installed individually!")
        return True
    else:
        print(f"❌ Failed packages: {failed_packages}")
        return False

def install_strategy_3():
    """Try minimal installation for testing."""
    print("\n📦 Strategy 3: Minimal installation...")
    
    minimal_packages = [
        "pytest",
        "pytest-asyncio", 
        "pydantic",
        "requests"
    ]
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install"
        ] + minimal_packages, check=True, capture_output=True, text=True)
        print("✅ Minimal packages installed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Strategy 3 failed: {e}")
        return False

def verify_installation():
    """Verify that key packages are available."""
    print("\n🔍 Verifying installation...")
    
    packages_to_check = [
        ("pytest", "pytest"),
        ("pytest_asyncio", "pytest-asyncio"),
        ("pydantic", "pydantic"),
        ("requests", "requests"),
    ]
    
    all_ok = True
    
    for module, name in packages_to_check:
        try:
            imported = __import__(module)
            if hasattr(imported, '__version__'):
                print(f"   ✅ {name}: {imported.__version__}")
            else:
                print(f"   ✅ {name}: available")
        except ImportError:
            print(f"   ❌ {name}: missing")
            all_ok = False
    
    return all_ok

def main():
    """Try multiple strategies to install dependencies."""
    print("🚀 Smart Dependencies Installer for LP Health Tracker")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print("=" * 60)
    
    # Strategy 0: Upgrade pip
    upgrade_pip()
    
    # Try strategies in order
    strategies = [
        install_strategy_1,
        install_strategy_2, 
        install_strategy_3
    ]
    
    for i, strategy in enumerate(strategies, 1):
        if strategy():
            print(f"\n🎉 Strategy {i} succeeded!")
            break
        print(f"\n⚠️  Strategy {i} failed, trying next...")
    else:
        print("\n❌ All installation strategies failed!")
        print("\n🔧 Manual solutions:")
        print("1. Install Visual Studio Build Tools")
        print("2. Install Rust: https://rustup.rs/")
        print("3. Use Python 3.11 or 3.12 instead of 3.13")
        return 1
    
    # Verify installation
    if verify_installation():
        print("\n🎉 Installation verified - ready for testing!")
        print("\nNext steps:")
        print("  python full_regression_test.py")
        return 0
    else:
        print("\n⚠️  Some packages missing - may still work for basic testing")
        return 1

if __name__ == "__main__":
    exit(main())
