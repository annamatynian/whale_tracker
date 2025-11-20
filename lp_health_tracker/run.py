#!/usr/bin/env python3
"""
LP Health Tracker - Main Launcher
================================

This is the main launcher for the LP Health Tracker agent.
Run this file to start monitoring your LP positions.

Usage:
    python run.py                  # Start with default settings
    python run.py --test-config    # Test configuration without starting
    python run.py --add-position   # Add new position interactively

Author: Generated for DeFi-RAG Project
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import LPHealthTracker
from src.position_manager import PositionManager, create_example_position
from config.settings import Settings


def test_configuration():
    """Test and validate configuration."""
    print("🔍 Testing LP Health Tracker Configuration...")
    print("=" * 50)
    
    try:
        # Load settings (validation happens automatically in Pydantic V2)
        settings = Settings()
        print("✅ Configuration is valid!")
        
        # Show configuration summary
        config_summary = settings.to_dict()
        print("\n📋 Configuration Summary:")
        for key, value in config_summary.items():
            print(f"   • {key}: {value}")
        
        print(f"\n🌐 RPC URL: {settings.get_rpc_url()}")
        
        # 🔥 NEW: Test Historical Data Manager
        test_historical_data()
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Please check your .env file and fix the above issues.")
        return False


def test_historical_data():
    """Test Historical Data Manager initialization."""
    print("\n🗄️ Testing Historical Data Manager...")
    try:
        from src.historical_data_manager import HistoricalDataManager
        
        # Initialize manager (this creates the database)
        historical_manager = HistoricalDataManager()
        print("✅ Historical Data Manager initialized")
        
        # Test with mock data
        mock_analysis = {
            'impermanent_loss': {'percentage': -0.01, 'usd_amount': -50.0},
            'hold_strategy': {'current_value_usd': 5000.0},
            'lp_strategy': {'current_value_usd': 4950.0, 'fees_earned_usd': 25.0},
            'better_strategy': 'HOLD'
        }
        
        mock_market = {
            'token_a_price': 2000.0,
            'token_b_price': 1.0,
            'price_ratio': 2000.0
        }
        
        # Test save operation
        success = historical_manager.save_position_snapshot(
            position_name="TEST-Position",
            analysis_data=mock_analysis,
            market_data=mock_market
        )
        
        if success:
            print("✅ Test data saved successfully")
            
            # Test daily summary
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            summary = historical_manager.get_daily_summary(today)
            
            if summary.get('positions_count', 0) > 0:
                print(f"✅ Daily summary generated: {summary['positions_count']} positions")
            else:
                print("📊 Daily summary: No data yet")
        else:
            print("⚠️ Failed to save test data")
            
    except Exception as e:
        print(f"❌ Historical Data Manager Error: {e}")


def add_position_interactive():
    """Interactive position addition."""
    print("➕ Adding New LP Position")
    print("=" * 30)
    
    position = create_example_position()
    
    # Get user input for each field
    position['name'] = input("Position Name (e.g., 'WETH-USDC Uniswap V2'): ").strip()
    position['pair_address'] = input("Pair Contract Address: ").strip()
    position['token_a_symbol'] = input("Token A Symbol (e.g., 'WETH'): ").strip()
    position['token_b_symbol'] = input("Token B Symbol (e.g., 'USDC'): ").strip()
    
    try:
        position['initial_liquidity_a'] = float(input(f"Initial {position['token_a_symbol']} amount: "))
        position['initial_liquidity_b'] = float(input(f"Initial {position['token_b_symbol']} amount: "))
        position['initial_price_a_usd'] = float(input(f"Initial {position['token_a_symbol']} price (USD): "))
        position['initial_price_b_usd'] = float(input(f"Initial {position['token_b_symbol']} price (USD): "))
        position['il_alert_threshold'] = float(input("IL Alert Threshold (e.g., 0.05 for 5%): "))
    except ValueError:
        print("❌ Invalid numeric input. Position not added.")
        return False
    
    position['wallet_address'] = input("Your Wallet Address: ").strip()
    position['network'] = input("Network (ethereum_mainnet/ethereum_sepolia): ").strip() or "ethereum_mainnet"
    position['notes'] = input("Notes (optional): ").strip()
    
    # Save position
    position_manager = PositionManager()
    
    if position_manager.add_position(position):
        print(f"✅ Position '{position['name']}' added successfully!")
        return True
    else:
        print("❌ Failed to add position.")
        return False


def list_positions():
    """List current positions."""
    print("📋 Current LP Positions")
    print("=" * 25)
    
    position_manager = PositionManager()
    positions = position_manager.load_positions()
    
    if not positions:
        print("❌ No positions found.")
        print("💡 Use 'python run.py --add-position' to add your first position.")
        return
    
    for i, position in enumerate(positions, 1):
        name = position.get('name', 'Unknown')
        pair = position.get('pair_address', 'Unknown')
        network = position.get('network', 'Unknown')
        threshold = position.get('il_alert_threshold', 0.05)
        active = "✅" if position.get('active', True) else "❌"
        
        print(f"{i}. {active} {name}")
        print(f"   Pair: {pair}")
        print(f"   Network: {network}")
        print(f"   IL Threshold: {threshold:.1%}")
        print()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LP Health Tracker - DeFi Position Monitor')
    parser.add_argument('--test-config', action='store_true', 
                       help='Test configuration without starting the tracker')
    parser.add_argument('--add-position', action='store_true',
                       help='Add new position interactively')
    parser.add_argument('--list-positions', action='store_true',
                       help='List current positions')
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.test_config:
        if test_configuration():
            print("\n🚀 Configuration is ready! Run 'python run.py' to start monitoring.")
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.add_position:
        if add_position_interactive():
            print("\n🚀 Position added! Run 'python run.py' to start monitoring.")
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.list_positions:
        list_positions()
        sys.exit(0)
    
    else:
        # Normal startup mode
        print("🚀 Starting LP Health Tracker...")
        print("=" * 35)
        
        # Quick config check
        if not test_configuration():
            print("\n❌ Please fix configuration errors before starting.")
            sys.exit(1)
        
        print("\n🎯 Starting monitoring agent...")
        
        # Create and start the tracker
        tracker = LPHealthTracker()
        await tracker.start()


if __name__ == "__main__":
    try:
        # Check if .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            print("⚠️  .env file not found!")
            print("📝 Please copy .env.example to .env and configure your settings.")
            print("\nExample:")
            print("   cp .env.example .env")
            print("   # Then edit .env with your API keys")
            sys.exit(1)
        
        # Run the main function
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n\n👋 LP Health Tracker stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)
