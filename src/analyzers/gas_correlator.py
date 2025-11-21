"""
Gas Price Correlator - Signal #2

Correlates gas prices between whale and intermediate transactions.
Same gas price = likely same entity (same wallet software, same strategy).

Probability of exact gas match by chance: ~0.1%
Exact match = 95% confidence same entity.

Confidence impact: +70 to +95
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GasCorrelationResult:
    """Result of gas price correlation analysis"""
    match: bool
    confidence: int
    correlation_type: str  # 'exact', 'close', 'strategy', 'none'
    whale_gas_price: Optional[int] = None
    intermediate_gas_price: Optional[int] = None
    gas_diff_gwei: Optional[float] = None
    details: Optional[str] = None


class GasCorrelator:
    """
    Analyzes gas price correlation between transactions.

    If whale transaction and intermediate->exchange transaction have
    same/similar gas price, it's strong evidence they're controlled
    by same entity.
    """

    def __init__(self):
        """Initialize gas correlator"""
        self.logger = logging.getLogger(__name__)

        # Thresholds
        self.EXACT_MATCH_TOLERANCE = 0  # Must be exactly same for "exact"
        self.CLOSE_MATCH_THRESHOLD_GWEI = 0.1  # Within 0.1 Gwei for "close"

        self.logger.info("GasCorrelator initialized")

    def check_gas_correlation(self,
                              whale_tx: Dict[str, Any],
                              intermediate_tx: Dict[str, Any]) -> GasCorrelationResult:
        """
        Check if gas prices correlate between transactions.

        Correlation types:
        - Exact: Same gas price (95% confidence) - probability by chance ~0.1%
        - Close: Within 0.1 Gwei (80% confidence)
        - Strategy: Same priority fee strategy (70% confidence)
        - None: No correlation (0% confidence)

        Args:
            whale_tx: Transaction from whale to intermediate
                Fields: gasPrice (or maxFeePerGas/maxPriorityFeePerGas for EIP-1559)
            intermediate_tx: Transaction from intermediate to exchange
                Fields: same as whale_tx

        Returns:
            GasCorrelationResult with match status and confidence
        """
        try:
            # Extract gas prices
            whale_gas = self._extract_gas_price(whale_tx)
            intermediate_gas = self._extract_gas_price(intermediate_tx)

            if whale_gas is None or intermediate_gas is None:
                self.logger.warning("Missing gas price data")
                return GasCorrelationResult(
                    match=False,
                    confidence=0,
                    correlation_type='none',
                    whale_gas_price=whale_gas,
                    intermediate_gas_price=intermediate_gas,
                    details='Missing gas price fields'
                )

            # Calculate difference
            gas_diff_wei = abs(whale_gas - intermediate_gas)
            gas_diff_gwei = gas_diff_wei / 1e9

            # Check exact match
            if gas_diff_wei == self.EXACT_MATCH_TOLERANCE:
                return GasCorrelationResult(
                    match=True,
                    confidence=95,
                    correlation_type='exact',
                    whale_gas_price=whale_gas,
                    intermediate_gas_price=intermediate_gas,
                    gas_diff_gwei=0.0,
                    details='Exact gas price match - very strong signal of same entity'
                )

            # Check close match (within 0.1 Gwei)
            if gas_diff_gwei <= self.CLOSE_MATCH_THRESHOLD_GWEI:
                return GasCorrelationResult(
                    match=True,
                    confidence=80,
                    correlation_type='close',
                    whale_gas_price=whale_gas,
                    intermediate_gas_price=intermediate_gas,
                    gas_diff_gwei=gas_diff_gwei,
                    details=f'Close gas price match ({gas_diff_gwei:.4f} Gwei difference)'
                )

            # Check if both used same priority fee strategy (EIP-1559)
            priority_match = self._check_priority_fee_match(whale_tx, intermediate_tx)
            if priority_match:
                return GasCorrelationResult(
                    match=True,
                    confidence=70,
                    correlation_type='strategy',
                    whale_gas_price=whale_gas,
                    intermediate_gas_price=intermediate_gas,
                    gas_diff_gwei=gas_diff_gwei,
                    details='Same priority fee strategy - likely same wallet software'
                )

            # No correlation
            return GasCorrelationResult(
                match=False,
                confidence=0,
                correlation_type='none',
                whale_gas_price=whale_gas,
                intermediate_gas_price=intermediate_gas,
                gas_diff_gwei=gas_diff_gwei,
                details=f'No gas correlation ({gas_diff_gwei:.2f} Gwei difference)'
            )

        except Exception as e:
            self.logger.error(f"Error checking gas correlation: {e}", exc_info=True)
            return GasCorrelationResult(
                match=False,
                confidence=0,
                correlation_type='error',
                details=f'Error: {str(e)}'
            )

    def _extract_gas_price(self, tx: Dict[str, Any]) -> Optional[int]:
        """
        Extract gas price from transaction.

        Handles both legacy (gasPrice) and EIP-1559 (maxFeePerGas) transactions.

        Args:
            tx: Transaction dict

        Returns:
            Gas price in Wei, or None if not found
        """
        # Legacy transaction (pre-EIP-1559)
        if 'gasPrice' in tx and tx['gasPrice'] is not None:
            gas_price = tx['gasPrice']
            # Convert hex to int if needed
            if isinstance(gas_price, str):
                return int(gas_price, 16) if gas_price.startswith('0x') else int(gas_price)
            return int(gas_price)

        # EIP-1559 transaction
        if 'maxFeePerGas' in tx and tx['maxFeePerGas'] is not None:
            max_fee = tx['maxFeePerGas']
            if isinstance(max_fee, str):
                return int(max_fee, 16) if max_fee.startswith('0x') else int(max_fee)
            return int(max_fee)

        self.logger.warning(f"No gas price found in transaction: {tx.get('hash', 'unknown')}")
        return None

    def _check_priority_fee_match(self,
                                  whale_tx: Dict[str, Any],
                                  intermediate_tx: Dict[str, Any]) -> bool:
        """
        Check if both transactions used same priority fee (EIP-1559).

        If maxPriorityFeePerGas is exactly the same, it indicates:
        - Same wallet software
        - Same gas estimation strategy
        - Likely same entity

        Args:
            whale_tx: Whale transaction
            intermediate_tx: Intermediate transaction

        Returns:
            True if priority fees match exactly
        """
        try:
            whale_priority = whale_tx.get('maxPriorityFeePerGas')
            intermediate_priority = intermediate_tx.get('maxPriorityFeePerGas')

            if whale_priority is None or intermediate_priority is None:
                return False

            # Convert to int if needed
            if isinstance(whale_priority, str):
                whale_priority = int(whale_priority, 16) if whale_priority.startswith('0x') else int(whale_priority)
            if isinstance(intermediate_priority, str):
                intermediate_priority = int(intermediate_priority, 16) if intermediate_priority.startswith('0x') else int(intermediate_priority)

            # Exact match
            return whale_priority == intermediate_priority

        except Exception as e:
            self.logger.error(f"Error checking priority fee: {e}")
            return False

    def format_gas_price_gwei(self, gas_price_wei: int) -> float:
        """
        Convert gas price from Wei to Gwei for display.

        Args:
            gas_price_wei: Gas price in Wei

        Returns:
            Gas price in Gwei
        """
        return gas_price_wei / 1e9

    def calculate_confidence_from_diff(self, gas_diff_gwei: float) -> int:
        """
        Calculate confidence score based on gas price difference.

        Args:
            gas_diff_gwei: Gas price difference in Gwei

        Returns:
            Confidence score (0-95)
        """
        if gas_diff_gwei == 0:
            return 95  # Exact match
        elif gas_diff_gwei <= 0.1:
            return 80  # Very close
        elif gas_diff_gwei <= 0.5:
            return 60  # Close
        elif gas_diff_gwei <= 1.0:
            return 40  # Somewhat close
        else:
            return 0   # Too different
