"""
Address Profiler - Signal #5

Profiles intermediate addresses to determine if they're:
- Fresh (created recently, < 24 hours)
- Empty (had 0 balance before whale transaction)
- Single-use burner (only 2 transactions: receive + send)
- Reused intermediate (used for multiple whale->exchange cycles)

Confidence impact: +70 to +95 depending on profile type
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class AddressProfile:
    """Profile of an intermediate address"""
    address: str
    is_fresh: bool
    fresh_confidence: int
    age_hours: Optional[float]

    was_empty: bool
    empty_confidence: int

    is_single_use: bool
    single_use_confidence: int
    transaction_count: Optional[int]

    is_reused: bool
    reuse_confidence: int
    reuse_cycle_count: Optional[int]

    overall_confidence: int
    profile_type: str  # 'burner', 'fresh_burner', 'professional', 'normal', 'unknown'
    details: str


class AddressProfiler:
    """
    Profiles intermediate addresses to enhance one-hop detection.

    Fresh, empty, single-use addresses are strong signals for burner addresses
    used specifically for this one-hop transfer.
    """

    def __init__(self, web3_manager=None):
        """
        Initialize address profiler.

        Args:
            web3_manager: Web3Manager instance for blockchain queries
        """
        self.logger = logging.getLogger(__name__)
        self.web3_manager = web3_manager

        # Thresholds
        self.FRESH_THRESHOLD_HOURS = 24
        self.VERY_FRESH_THRESHOLD_HOURS = 1

        self.logger.info("AddressProfiler initialized")

    async def profile_address(self,
                             address: str,
                             whale_tx_block: int,
                             whale_tx_timestamp: Optional[datetime] = None) -> AddressProfile:
        """
        Create comprehensive profile of intermediate address.

        Checks multiple signals:
        1. Fresh address (age < 24h)
        2. Empty before whale transaction
        3. Single-use burner pattern
        4. Reused intermediate pattern

        Args:
            address: Address to profile
            whale_tx_block: Block number of whale transaction
            whale_tx_timestamp: Timestamp of whale transaction

        Returns:
            AddressProfile with all signals analyzed
        """
        try:
            # Check each signal
            fresh_result = await self._is_fresh_address(address, whale_tx_timestamp)
            empty_result = await self._was_empty_before(address, whale_tx_block)
            single_use_result = await self._is_single_use(address)
            reuse_result = await self._is_reused_intermediate(address)

            # Determine overall profile type and confidence
            profile_type, overall_confidence = self._determine_profile_type(
                fresh_result, empty_result, single_use_result, reuse_result
            )

            # Build details
            details_parts = []
            if fresh_result['is_fresh']:
                details_parts.append(f"Fresh address ({fresh_result.get('age_hours', 0):.1f}h old)")
            if empty_result['was_empty']:
                details_parts.append("Empty before whale tx")
            if single_use_result['is_single_use']:
                details_parts.append("Single-use burner pattern")
            if reuse_result['is_reused']:
                details_parts.append(f"Reused {reuse_result.get('cycle_count', 0)} times")

            details = "; ".join(details_parts) if details_parts else "Normal address activity"

            return AddressProfile(
                address=address,
                is_fresh=fresh_result['is_fresh'],
                fresh_confidence=fresh_result['confidence'],
                age_hours=fresh_result.get('age_hours'),
                was_empty=empty_result['was_empty'],
                empty_confidence=empty_result['confidence'],
                is_single_use=single_use_result['is_single_use'],
                single_use_confidence=single_use_result['confidence'],
                transaction_count=single_use_result.get('tx_count'),
                is_reused=reuse_result['is_reused'],
                reuse_confidence=reuse_result['confidence'],
                reuse_cycle_count=reuse_result.get('cycle_count'),
                overall_confidence=overall_confidence,
                profile_type=profile_type,
                details=details
            )

        except Exception as e:
            self.logger.error(f"Error profiling address {address}: {e}", exc_info=True)
            return AddressProfile(
                address=address,
                is_fresh=False,
                fresh_confidence=0,
                age_hours=None,
                was_empty=False,
                empty_confidence=0,
                is_single_use=False,
                single_use_confidence=0,
                transaction_count=None,
                is_reused=False,
                reuse_confidence=0,
                reuse_cycle_count=None,
                overall_confidence=0,
                profile_type='error',
                details=f'Error: {str(e)}'
            )

    async def _is_fresh_address(self,
                                address: str,
                                whale_tx_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Check if address was created recently (< 24 hours before whale tx).

        Very fresh addresses (< 1 hour) are strong signal for burner.

        Args:
            address: Address to check
            whale_tx_timestamp: When whale transaction occurred

        Returns:
            Dict with is_fresh, confidence, age_hours
        """
        try:
            if not self.web3_manager:
                return {'is_fresh': False, 'confidence': 0, 'age_hours': None}

            # Get first transaction for this address
            # Note: This is simplified - in production would query Etherscan
            # or maintain database of first seen timestamps

            # For MVP: Use transaction count as proxy
            # If tx count is very low (< 5), likely fresh
            tx_count = self.web3_manager.w3.eth.get_transaction_count(address)

            if tx_count <= 1:
                # Likely brand new (whale tx was first or second)
                return {
                    'is_fresh': True,
                    'confidence': 90,
                    'age_hours': 0.1,  # Estimate very recent
                    'details': 'Very low transaction count - likely fresh'
                }
            elif tx_count <= 5:
                # Very few transactions, possibly fresh
                return {
                    'is_fresh': True,
                    'confidence': 70,
                    'age_hours': 12,  # Estimate
                    'details': 'Low transaction count - possibly fresh'
                }
            else:
                # Established address
                return {
                    'is_fresh': False,
                    'confidence': 0,
                    'age_hours': None,
                    'details': 'Established address with transaction history'
                }

        except Exception as e:
            self.logger.error(f"Error checking if address is fresh: {e}")
            return {'is_fresh': False, 'confidence': 0, 'age_hours': None}

    async def _was_empty_before(self, address: str, whale_tx_block: int) -> Dict[str, Any]:
        """
        Check if address had 0 balance before whale transaction.

        Empty addresses that receive funds then immediately send to exchange
        are strong burner signal.

        Args:
            address: Address to check
            whale_tx_block: Block number of whale transaction

        Returns:
            Dict with was_empty, confidence
        """
        try:
            if not self.web3_manager:
                return {'was_empty': False, 'confidence': 0}

            # Get balance at block before whale transaction
            balance = self.web3_manager.w3.eth.get_balance(
                address,
                block_identifier=whale_tx_block - 1
            )

            if balance == 0:
                return {
                    'was_empty': True,
                    'confidence': 85,
                    'details': 'Address had zero balance before whale transaction'
                }
            elif balance < 0.01 * 10**18:  # Less than 0.01 ETH
                return {
                    'was_empty': True,
                    'confidence': 70,
                    'details': f'Address had minimal balance ({balance / 10**18:.6f} ETH)'
                }
            else:
                return {
                    'was_empty': False,
                    'confidence': 0,
                    'details': f'Address had {balance / 10**18:.4f} ETH balance'
                }

        except Exception as e:
            # Might fail if not archival node
            self.logger.warning(f"Could not check historical balance: {e}")
            return {'was_empty': False, 'confidence': 0}

    async def _is_single_use(self, address: str) -> Dict[str, Any]:
        """
        Check if address follows single-use burner pattern:
        - Exactly 2 transactions: receive from whale, send to exchange
        - Current balance near zero

        Args:
            address: Address to check

        Returns:
            Dict with is_single_use, confidence, tx_count
        """
        try:
            if not self.web3_manager:
                return {'is_single_use': False, 'confidence': 0, 'tx_count': None}

            # Get current transaction count
            tx_count = self.web3_manager.w3.eth.get_transaction_count(address)

            # Get current balance
            balance = self.web3_manager.w3.eth.get_balance(address)

            # Perfect burner pattern: exactly 2 txs, empty now
            if tx_count == 2 and balance < 0.01 * 10**18:
                return {
                    'is_single_use': True,
                    'confidence': 95,
                    'tx_count': tx_count,
                    'details': 'Perfect burner: 2 transactions, now empty'
                }

            # Close burner pattern: 2-3 txs, minimal balance
            if tx_count <= 3 and balance < 0.1 * 10**18:
                return {
                    'is_single_use': True,
                    'confidence': 80,
                    'tx_count': tx_count,
                    'details': f'Likely burner: {tx_count} transactions, minimal balance'
                }

            # Not burner pattern
            return {
                'is_single_use': False,
                'confidence': 0,
                'tx_count': tx_count,
                'details': f'{tx_count} transactions, not burner pattern'
            }

        except Exception as e:
            self.logger.error(f"Error checking single-use pattern: {e}")
            return {'is_single_use': False, 'confidence': 0, 'tx_count': None}

    async def _is_reused_intermediate(self, address: str) -> Dict[str, Any]:
        """
        Check if address is reused intermediate (professional operation).

        Some sophisticated operations reuse same intermediates multiple times.
        Pattern: Multiple whale->intermediate->exchange cycles.

        Note: Full implementation requires transaction history database.
        This is simplified version using transaction count.

        Args:
            address: Address to check

        Returns:
            Dict with is_reused, confidence, cycle_count
        """
        try:
            if not self.web3_manager:
                return {'is_reused': False, 'confidence': 0, 'cycle_count': None}

            # Get transaction count
            tx_count = self.web3_manager.w3.eth.get_transaction_count(address)

            # High transaction count suggests reuse
            # Each cycle = 2 txs (in + out), so N cycles = 2N txs
            if tx_count >= 10:  # 5+ cycles
                estimated_cycles = tx_count // 2
                return {
                    'is_reused': True,
                    'confidence': 75,
                    'cycle_count': estimated_cycles,
                    'details': f'Reused intermediate: {estimated_cycles} estimated cycles'
                }

            return {
                'is_reused': False,
                'confidence': 0,
                'cycle_count': None,
                'details': 'Not enough transactions for reuse pattern'
            }

        except Exception as e:
            self.logger.error(f"Error checking reuse pattern: {e}")
            return {'is_reused': False, 'confidence': 0, 'cycle_count': None}

    def _determine_profile_type(self,
                                fresh_result: Dict,
                                empty_result: Dict,
                                single_use_result: Dict,
                                reuse_result: Dict) -> tuple:
        """
        Determine overall profile type and confidence based on all signals.

        Profile types:
        - fresh_burner: Fresh + empty + single-use (highest confidence)
        - burner: Single-use (high confidence)
        - professional: Reused intermediate (medium-high confidence)
        - fresh: Fresh but not single-use (medium confidence)
        - normal: Established address (low confidence)
        - unknown: Cannot determine (no confidence)

        Returns:
            Tuple of (profile_type, overall_confidence)
        """
        # Fresh burner (strongest signal)
        if (fresh_result['is_fresh'] and
            empty_result['was_empty'] and
            single_use_result['is_single_use']):
            confidence = max(
                fresh_result['confidence'],
                empty_result['confidence'],
                single_use_result['confidence']
            )
            return ('fresh_burner', confidence)

        # Single-use burner
        if single_use_result['is_single_use']:
            return ('burner', single_use_result['confidence'])

        # Professional reused intermediate
        if reuse_result['is_reused']:
            return ('professional', reuse_result['confidence'])

        # Fresh address (moderate signal)
        if fresh_result['is_fresh']:
            return ('fresh', fresh_result['confidence'])

        # Empty address (moderate signal)
        if empty_result['was_empty']:
            return ('empty', empty_result['confidence'])

        # Normal/established address
        return ('normal', 0)
