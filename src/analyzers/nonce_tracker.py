"""
Nonce Tracker - Signal #3 (STRONGEST SIGNAL)

Tracks transaction nonce sequences to detect immediate transfers.
Nonce gap = 1 means intermediate address sent to exchange IMMEDIATELY after
receiving from whale - strongest possible signal for one-hop detection.

Confidence impact: +40 to +95 (highest of all signals)
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
import aiohttp
import asyncio
from web3 import Web3


@dataclass
class NonceCorrelationResult:
    """Result of nonce correlation analysis"""
    match: bool
    confidence: int
    nonce_gap: Optional[int]
    signal_strength: str
    whale_tx_nonce: Optional[int] = None
    intermediate_nonce_at_whale_block: Optional[int] = None
    exchange_tx_nonce: Optional[int] = None
    details: Optional[str] = None


class NonceTracker:
    """
    Tracks nonce sequences to detect one-hop patterns.

    Sequential nonces (gap = 1) = STRONGEST signal that intermediate
    immediately forwarded funds to exchange.
    """

    def __init__(self,
                 web3_manager=None,
                 etherscan_api_key: Optional[str] = None,
                 use_etherscan: bool = True):
        """
        Initialize nonce tracker.

        Args:
            web3_manager: Web3Manager instance for RPC calls
            etherscan_api_key: Etherscan API key (optional but recommended)
            use_etherscan: Whether to use Etherscan API (faster, more reliable)
        """
        self.logger = logging.getLogger(__name__)
        self.web3_manager = web3_manager
        self.etherscan_api_key = etherscan_api_key
        self.use_etherscan = use_etherscan and etherscan_api_key is not None

        # Rate limiting
        self.last_etherscan_call = 0
        self.etherscan_rate_limit = 0.2  # 5 calls/sec = 0.2s between calls

        self.logger.info(f"NonceTracker initialized (Etherscan: {self.use_etherscan})")

    async def check_nonce_sequence(self,
                                   whale_tx: Dict[str, Any],
                                   intermediate_tx: Dict[str, Any]) -> NonceCorrelationResult:
        """
        Check if intermediate address had sequential nonces.

        This is the STRONGEST signal for one-hop detection:
        - Gap = 1: Intermediate IMMEDIATELY sent to exchange (95% confidence)
        - Gap = 2-3: Very likely related (75% confidence)
        - Gap = 4-10: Possibly related (40% confidence)
        - Gap > 10: Unlikely related (0% confidence)

        Args:
            whale_tx: Transaction from whale to intermediate
                Required fields: blockNumber, to (intermediate address)
            intermediate_tx: Transaction from intermediate to exchange
                Required fields: nonce, from (intermediate address)

        Returns:
            NonceCorrelationResult with match status and confidence
        """
        try:
            intermediate_addr = whale_tx.get('to')
            whale_block = whale_tx.get('blockNumber')

            if not intermediate_addr or not whale_block:
                self.logger.warning("Missing required fields in whale_tx")
                return NonceCorrelationResult(
                    match=False,
                    confidence=0,
                    nonce_gap=None,
                    signal_strength='NONE',
                    details='Missing whale_tx fields'
                )

            # Get intermediate's nonce at the time of whale transaction
            nonce_at_whale_block = await self._get_nonce_at_block(
                intermediate_addr,
                whale_block
            )

            if nonce_at_whale_block is None:
                self.logger.warning(f"Could not get nonce for {intermediate_addr} at block {whale_block}")
                return NonceCorrelationResult(
                    match=False,
                    confidence=0,
                    nonce_gap=None,
                    signal_strength='NONE',
                    details='Could not retrieve nonce'
                )

            # Get intermediate's nonce for exchange transaction
            exchange_tx_nonce = intermediate_tx.get('nonce')

            if exchange_tx_nonce is None:
                self.logger.warning("Exchange transaction missing nonce field")
                return NonceCorrelationResult(
                    match=False,
                    confidence=0,
                    nonce_gap=None,
                    signal_strength='NONE',
                    details='Exchange tx missing nonce'
                )

            # Calculate nonce gap
            nonce_gap = exchange_tx_nonce - nonce_at_whale_block

            # Determine confidence based on gap
            if nonce_gap == 1:
                # STRONGEST SIGNAL
                # Intermediate received from whale, IMMEDIATELY sent to exchange
                # No other transactions in between
                return NonceCorrelationResult(
                    match=True,
                    confidence=95,
                    nonce_gap=1,
                    signal_strength='STRONGEST',
                    whale_tx_nonce=whale_tx.get('nonce'),
                    intermediate_nonce_at_whale_block=nonce_at_whale_block,
                    exchange_tx_nonce=exchange_tx_nonce,
                    details='Sequential nonces - immediate transfer detected'
                )

            elif nonce_gap <= 3:
                # Very few transactions in between
                # Still very strong signal
                return NonceCorrelationResult(
                    match=True,
                    confidence=75,
                    nonce_gap=nonce_gap,
                    signal_strength='STRONG',
                    whale_tx_nonce=whale_tx.get('nonce'),
                    intermediate_nonce_at_whale_block=nonce_at_whale_block,
                    exchange_tx_nonce=exchange_tx_nonce,
                    details=f'Small nonce gap ({nonce_gap}) - likely related'
                )

            elif nonce_gap <= 10:
                # Some activity in between, but still possible
                return NonceCorrelationResult(
                    match=True,
                    confidence=40,
                    nonce_gap=nonce_gap,
                    signal_strength='WEAK',
                    whale_tx_nonce=whale_tx.get('nonce'),
                    intermediate_nonce_at_whale_block=nonce_at_whale_block,
                    exchange_tx_nonce=exchange_tx_nonce,
                    details=f'Moderate nonce gap ({nonce_gap}) - possibly related'
                )

            else:
                # Too many transactions in between
                # Unlikely to be immediate one-hop
                return NonceCorrelationResult(
                    match=False,
                    confidence=0,
                    nonce_gap=nonce_gap,
                    signal_strength='NONE',
                    whale_tx_nonce=whale_tx.get('nonce'),
                    intermediate_nonce_at_whale_block=nonce_at_whale_block,
                    exchange_tx_nonce=exchange_tx_nonce,
                    details=f'Large nonce gap ({nonce_gap}) - unlikely related'
                )

        except Exception as e:
            self.logger.error(f"Error checking nonce sequence: {e}", exc_info=True)
            return NonceCorrelationResult(
                match=False,
                confidence=0,
                nonce_gap=None,
                signal_strength='ERROR',
                details=f'Error: {str(e)}'
            )

    async def _get_nonce_at_block(self, address: str, block_number: int) -> Optional[int]:
        """
        Get transaction count (nonce) for address at specific block.

        Tries multiple methods:
        1. Etherscan API (fastest, most reliable)
        2. RPC eth_getTransactionCount (requires archival node)

        Args:
            address: Ethereum address
            block_number: Block number

        Returns:
            Nonce at that block, or None if unable to retrieve
        """
        # Try Etherscan first if available
        if self.use_etherscan:
            nonce = await self._get_nonce_via_etherscan(address, block_number)
            if nonce is not None:
                return nonce
            self.logger.warning(f"Etherscan failed, falling back to RPC")

        # Fallback to RPC
        if self.web3_manager:
            nonce = await self._get_nonce_via_rpc(address, block_number)
            if nonce is not None:
                return nonce

        self.logger.error(f"All methods failed to get nonce for {address} at block {block_number}")
        return None

    async def _get_nonce_via_etherscan(self, address: str, block_number: int) -> Optional[int]:
        """
        Get nonce using Etherscan API.

        Endpoint: eth_getTransactionCount via proxy module
        Rate limit: 5 calls/sec (free tier)
        """
        try:
            # Rate limiting
            current_time = asyncio.get_event_loop().time()
            time_since_last_call = current_time - self.last_etherscan_call
            if time_since_last_call < self.etherscan_rate_limit:
                await asyncio.sleep(self.etherscan_rate_limit - time_since_last_call)

            url = (
                f"https://api.etherscan.io/api"
                f"?module=proxy"
                f"&action=eth_getTransactionCount"
                f"&address={address}"
                f"&tag={hex(block_number)}"
                f"&apikey={self.etherscan_api_key}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    self.last_etherscan_call = asyncio.get_event_loop().time()

                    if response.status != 200:
                        self.logger.error(f"Etherscan API error: HTTP {response.status}")
                        return None

                    data = await response.json()

                    if data.get('status') == '1' and 'result' in data:
                        # Result is hex string
                        nonce = int(data['result'], 16)
                        self.logger.debug(f"Etherscan nonce for {address} at block {block_number}: {nonce}")
                        return nonce
                    else:
                        error_msg = data.get('message', 'Unknown error')
                        self.logger.error(f"Etherscan API error: {error_msg}")
                        return None

        except asyncio.TimeoutError:
            self.logger.error("Etherscan API timeout")
            return None
        except Exception as e:
            self.logger.error(f"Error calling Etherscan API: {e}")
            return None

    async def _get_nonce_via_rpc(self, address: str, block_number: int) -> Optional[int]:
        """
        Get nonce using RPC eth_getTransactionCount.

        Note: Requires archival node for historical blocks.
        Regular nodes only support recent blocks (~128 blocks back).
        """
        try:
            if not self.web3_manager or not self.web3_manager.w3:
                self.logger.error("Web3Manager not available")
                return None

            # Convert to checksum address
            checksum_address = Web3.to_checksum_address(address)

            # Get nonce at specific block
            nonce = self.web3_manager.w3.eth.get_transaction_count(
                checksum_address,
                block_identifier=block_number
            )

            self.logger.debug(f"RPC nonce for {address} at block {block_number}: {nonce}")
            return nonce

        except Exception as e:
            self.logger.error(f"Error getting nonce via RPC: {e}")
            return None

    def calculate_confidence_from_gap(self, nonce_gap: int) -> int:
        """
        Calculate confidence score based on nonce gap.

        Args:
            nonce_gap: Number of transactions between whale tx and exchange tx

        Returns:
            Confidence score (0-95)
        """
        if nonce_gap == 1:
            return 95  # STRONGEST
        elif nonce_gap <= 3:
            return 75  # STRONG
        elif nonce_gap <= 10:
            return 40  # WEAK
        else:
            return 0   # NONE
