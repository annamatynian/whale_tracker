"""
Debug RPC Connection Issues
"""
import asyncio
import os
import logging
from dotenv import load_dotenv

# Load .env
load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_rpc():
    """Debug RPC connection step by step"""

    print("\n" + "="*80)
    print("🔍 DEBUGGING RPC CONNECTION")
    print("="*80)

    # Step 1: Check environment variables
    print("\n1️⃣ Checking environment variables:")
    print("-" * 80)

    infura_url = os.getenv('INFURA_URL')
    infura_key = os.getenv('INFURA_API_KEY')
    alchemy_url = os.getenv('ALCHEMY_URL')
    alchemy_key = os.getenv('ALCHEMY_API_KEY')
    ankr_url = os.getenv('ANKR_URL')

    print(f"INFURA_URL: {'✅ SET' if infura_url else '❌ NOT SET'}")
    if infura_url:
        print(f"  Value: {infura_url[:50]}...")

    print(f"INFURA_API_KEY: {'✅ SET' if infura_key else '❌ NOT SET'}")
    if infura_key:
        print(f"  Value: {infura_key[:10]}...{infura_key[-4:]}")

    print(f"ALCHEMY_URL: {'✅ SET' if alchemy_url else '❌ NOT SET'}")
    if alchemy_url:
        print(f"  Value: {alchemy_url[:50]}...")

    print(f"ALCHEMY_API_KEY: {'✅ SET' if alchemy_key else '❌ NOT SET'}")
    if alchemy_key:
        print(f"  Value: {alchemy_key[:10]}...{alchemy_key[-4:]}")

    print(f"ANKR_URL: {'✅ SET' if ankr_url else '❌ NOT SET'}")
    if ankr_url:
        print(f"  Value: {ankr_url}")

    # Step 2: Test Web3Manager initialization
    print("\n2️⃣ Testing Web3Manager initialization:")
    print("-" * 80)

    try:
        from src.core.web3_manager import Web3Manager

        web3_manager = Web3Manager(mock_mode=False)
        print("✅ Web3Manager created successfully")

        # Check what RPC URL it selected
        print(f"\nSelected network: {web3_manager.network}")
        network_config = web3_manager.networks.get(web3_manager.network)
        if network_config:
            print(f"RPC URL: {network_config['rpc_url']}")

    except Exception as e:
        print(f"❌ FAILED to create Web3Manager: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Test initialization
    print("\n3️⃣ Testing Web3 connection initialization:")
    print("-" * 80)

    try:
        result = await web3_manager.initialize()
        if result:
            print("✅ Web3 initialized successfully")
            print(f"   Connected: {web3_manager.web3.is_connected()}")
            if web3_manager.web3:
                chain_id = web3_manager.web3.eth.chain_id
                print(f"   Chain ID: {chain_id}")
        else:
            print("❌ Web3 initialization returned False")
    except Exception as e:
        print(f"❌ FAILED to initialize: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Test gas price
    print("\n4️⃣ Testing get_current_gas_price():")
    print("-" * 80)

    try:
        gas_price = await web3_manager.get_current_gas_price()
        if gas_price:
            print(f"✅ Gas price retrieved: {gas_price / 1e9:.2f} Gwei")
        else:
            print("❌ get_current_gas_price() returned None")
    except Exception as e:
        print(f"❌ FAILED to get gas price: {e}")
        import traceback
        traceback.print_exc()

    # Step 5: Alternative RPC test
    print("\n5️⃣ Testing alternative RPC endpoints:")
    print("-" * 80)

    from web3 import Web3

    test_rpcs = [
        ('Infura', f'https://mainnet.infura.io/v3/{infura_key}' if infura_key else None),
        ('Alchemy', alchemy_url if alchemy_url else None),
        ('Ankr Public', 'https://rpc.ankr.com/eth'),
        ('Cloudflare', 'https://cloudflare-eth.com'),
    ]

    for name, rpc_url in test_rpcs:
        if not rpc_url:
            print(f"⏭️  {name}: Skipped (not configured)")
            continue

        try:
            print(f"\nTesting {name}: {rpc_url[:50]}...")
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))

            if w3.is_connected():
                chain_id = w3.eth.chain_id
                gas_price = w3.eth.gas_price
                print(f"  ✅ Connected!")
                print(f"     Chain ID: {chain_id}")
                print(f"     Gas Price: {gas_price / 1e9:.2f} Gwei")
            else:
                print(f"  ❌ Not connected")

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")

    print("\n" + "="*80)
    print("🏁 DIAGNOSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(debug_rpc())
