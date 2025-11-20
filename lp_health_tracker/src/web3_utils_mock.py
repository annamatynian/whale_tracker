# Mock version for testing without web3
# ====================================

class MockWeb3Manager:
    """Mock Web3Manager for testing without blockchain dependencies."""
    
    def __init__(self):
        self.network = "ethereum_mainnet"  # Mock network
        self.web3 = None
        
    async def initialize(self):
        """Mock initialization."""
        print("[MOCK] Web3Manager initialized (no real connection)")
        return True
    
    def is_connected(self):
        """Mock connection check.""" 
        return False  # Always return False since it's mock
    
    def get_current_gas_price(self):
        """Mock gas price."""
        return 20000000000  # 20 gwei
