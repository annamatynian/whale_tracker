"""
Gas Cost Calculator - Real-time Gas Cost Analysis
================================================

This module handles:
- Real gas cost calculation from transaction receipts
- USD conversion of gas costs
- Position gas cost management with caching
- Integration with Web3Manager for blockchain data

Author: Generated for DeFi-RAG Project - Phase 1.2
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from web3 import Web3

from src.web3_utils import Web3Manager


class GasCostCalculator:
    """
    Calculates real gas costs from blockchain transactions.
    
    Features:
    - Real transaction cost calculation from tx receipts
    - USD conversion using current ETH price
    - Caching to avoid redundant RPC calls
    - Fallback to manual gas_costs_usd values
    """
    
    def __init__(self, web3_manager: Web3Manager):
        """
        Initialize Gas Cost Calculator.
        
        Args:
            web3_manager: Web3Manager instance for blockchain interactions
        """
        self.logger = logging.getLogger(__name__)
        self.web3_manager = web3_manager
        
        # Simple in-memory cache for gas costs
        # _gas_cost_cache Это "краткосрочная память" или кэш. 
        # Калькулятор сохраняет сюда уже вычисленные результаты, 
        # чтобы не делать одну и ту же работу дважды. 
        # Это экономит время и ресурсы.
        self._gas_cost_cache = {}
    
    async def calculate_tx_cost_usd(
        self, 
        tx_hash: str, 
        eth_price_usd: float
    ) -> Optional[float]:
        """
        Calculate real transaction cost in USD from tx receipt.
        
        Args:
            tx_hash: Transaction hash
            eth_price_usd: ETH price in USD (required)
            
        Returns:
            Optional[float]: Transaction cost in USD, None if error
        """
        try:
            # Check cache first
            if tx_hash in self._gas_cost_cache:
                cached_result = self._gas_cost_cache[tx_hash]
                self.logger.debug(f"Using cached gas cost for {tx_hash[:10]}...")
                return cached_result
            
            # Get transaction receipt from blockchain
            receipt = self.web3_manager.get_transaction_receipt(tx_hash)
            if not receipt:
                self.logger.error(f"Could not get receipt for tx {tx_hash}")
                return None
            
            # Extract gas data from receipt
            gas_used = receipt.get('gasUsed', 0)
            effective_gas_price = receipt.get('effectiveGasPrice')
            
            # Fallback to gasPrice if effectiveGasPrice not available (older txs)
            if effective_gas_price is None:
                # Get original transaction for gasPrice
                tx = self.web3_manager.web3.eth.get_transaction(tx_hash)
                effective_gas_price = tx.get('gasPrice', 0)
            
            if gas_used == 0 or effective_gas_price == 0:
                self.logger.error(f"Invalid gas data: used={gas_used}, price={effective_gas_price}")
                return None
            
            # Calculate cost in ETH
            total_cost_wei = gas_used * effective_gas_price
            total_cost_eth = Web3.from_wei(total_cost_wei, 'ether')
            
            # Convert to USD using provided ETH price
            total_cost_usd = float(total_cost_eth) * eth_price_usd
            
            # Cache result
            self._gas_cost_cache[tx_hash] = total_cost_usd
            
            self.logger.info(
                f"Gas cost calculated: {gas_used:,} gas × {Web3.from_wei(effective_gas_price, 'gwei'):.1f} gwei "
                f"= {total_cost_eth:.6f} ETH = ${total_cost_usd:.2f}"
            )
            
            return total_cost_usd
            
        except Exception as e:
            self.logger.error(f"Error calculating gas cost for tx {tx_hash}: {e}")
            return None
    
    async def update_position_gas_costs(
        self, 
        position: Dict[str, Any], 
        eth_price_usd: float
    ) -> Dict[str, Any]:
        """
        Update gas costs for a single position.
        
        Args:
            position: Position data dictionary
            eth_price_usd: Current ETH price in USD
            
        Returns:
            Dict: Updated position with real gas costs
        """
        try:
            position_name = position.get('name', 'Unknown')
            
            # Check if already calculated
            if position.get('gas_costs_calculated', False):
                self.logger.debug(f"Gas costs already calculated for {position_name}")
                return position
            
            # Get entry transaction hash
            entry_tx_hash = position.get('entry_tx_hash')
            if not entry_tx_hash:
                self.logger.warning(f"No entry_tx_hash for position {position_name}, using fallback")
                return position
            
            # Calculate real gas cost using provided ETH price
            real_gas_cost = await self.calculate_tx_cost_usd(entry_tx_hash, eth_price_usd)
            
            if real_gas_cost is not None:
                # Update position with real cost
                position['gas_costs_usd'] = real_gas_cost
                position['gas_costs_calculated'] = True
                position['gas_calculation_date'] = datetime.now().isoformat()
                
                self.logger.info(
                    f"Updated gas costs for {position_name}: ${real_gas_cost:.2f}"
                )
            else:
                # Keep fallback value, but log the attempt
                self.logger.warning(
                    f"Could not calculate real gas cost for {position_name}, "
                    f"keeping fallback: ${position.get('gas_costs_usd', 0):.2f}"
                )
            
            return position
            
        except Exception as e:
            self.logger.error(f"Error updating gas costs for position: {e}")
            return position
    
    async def update_all_positions_gas_costs(
        self, 
        positions: list[Dict[str, Any]],
        eth_price_usd: float
    ) -> list[Dict[str, Any]]:
        """
        Update gas costs for all positions.
        
        Args:
            positions: List of position dictionaries
            eth_price_usd: Current ETH price in USD
            
        Returns:
            List[Dict]: Updated positions with real gas costs
        """
        try:
            self.logger.info(f"Updating gas costs for {len(positions)} positions...")
            
            # Process all positions
            updated_positions = []
            for position in positions:
                updated_position = await self.update_position_gas_costs(position, eth_price_usd)
                updated_positions.append(updated_position)
            
            # Calculate summary
            calculated_count = sum(1 for p in updated_positions if p.get('gas_costs_calculated', False))
            total_gas_costs = sum(p.get('gas_costs_usd', 0) for p in updated_positions)
            
            self.logger.info(
                f"Gas cost update complete: {calculated_count}/{len(positions)} calculated, "
                f"total gas costs: ${total_gas_costs:.2f}"
            )
            
            return updated_positions
            
        except Exception as e:
            self.logger.error(f"Error updating all positions gas costs: {e}")
            return positions
    

    
    def get_gas_cost_summary(self, positions: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate gas cost summary for all positions.
        
        Args:
            positions: List of positions
            
        Returns:
            Dict: Gas cost summary statistics
        """
        try:
            calculated_positions = [p for p in positions if p.get('gas_costs_calculated', False)]
            fallback_positions = [p for p in positions if not p.get('gas_costs_calculated', False)]
            
            total_gas_costs = sum(p.get('gas_costs_usd', 0) for p in positions)
            calculated_gas_costs = sum(p.get('gas_costs_usd', 0) for p in calculated_positions)
            fallback_gas_costs = sum(p.get('gas_costs_usd', 0) for p in fallback_positions)
            
            return {
                'total_positions': len(positions),
                'calculated_positions': len(calculated_positions),
                'fallback_positions': len(fallback_positions),
                'total_gas_costs_usd': total_gas_costs,
                'calculated_gas_costs_usd': calculated_gas_costs,
                'fallback_gas_costs_usd': fallback_gas_costs,
                'calculation_accuracy': len(calculated_positions) / len(positions) if positions else 0,
                'average_gas_cost_usd': total_gas_costs / len(positions) if positions else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error generating gas cost summary: {e}")
            return {}
    
    def clear_cache(self):
        """Clear gas cost cache."""
        self._gas_cost_cache.clear()
        self.logger.info("Gas cost cache cleared")


# Utility functions for gas cost estimation
class GasEstimator:
    """
    Estimates gas costs for common DeFi operations.
    """
    
    # Typical gas usage for common operations
    OPERATION_GAS_ESTIMATES = {
        'uniswap_v2_add_liquidity': 150000,
        'uniswap_v2_remove_liquidity': 120000,
        'uniswap_v2_swap': 100000,
        'erc20_approve': 50000,
        'erc20_transfer': 21000,
        'eth_transfer': 21000
    }
    
    @classmethod
    async def estimate_operation_cost_usd(
        cls, 
        operation: str, 
        gas_price_gwei: float, 
        eth_price_usd: float
    ) -> Optional[float]:
        """
        Estimate USD cost for a DeFi operation.
        
        Args:
            operation: Operation type (key from OPERATION_GAS_ESTIMATES)
            gas_price_gwei: Gas price in Gwei
            eth_price_usd: ETH price in USD
            
        Returns:
            Optional[float]: Estimated cost in USD
        """
        try:
            gas_limit = cls.OPERATION_GAS_ESTIMATES.get(operation)
            if gas_limit is None:
                return None
            
            # Calculate cost in ETH
            gas_price_wei = Web3.to_wei(gas_price_gwei, 'gwei')
            cost_wei = gas_limit * gas_price_wei
            cost_eth = Web3.from_wei(cost_wei, 'ether')
            
            # Convert to USD
            cost_usd = float(cost_eth) * eth_price_usd
            
            return cost_usd
            
        except Exception:
            return None
    
    @classmethod
    def get_supported_operations(cls) -> list[str]:
        """Get list of supported operations for gas estimation."""
        return list(cls.OPERATION_GAS_ESTIMATES.keys())
