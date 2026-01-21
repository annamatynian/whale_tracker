"""
Test for Empty Delta Attack Fix (GEMINI FIX #6)

Validates that LST migrations are detected even when ETH delta = 0
(e.g., stETH ↔ WETH swaps from wallets with 0 native ETH)
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator


@pytest.fixture
def calculator():
    """Create AccumulationScoreCalculator with mocked dependencies."""
    return AccumulationScoreCalculator(
        whale_provider=AsyncMock(),
        multicall_client=AsyncMock(),
        repository=AsyncMock(),
        snapshot_repo=AsyncMock(),
        price_provider=AsyncMock(),
        lookback_hours=24
    )


class TestEmptyDeltaAttackFix:
    """Test that LST migration detection works for wallets with 0 ETH."""
    
    @pytest.mark.asyncio
    async def test_steth_to_weth_swap_detected_zero_eth(self, calculator):
        """
        GEMINI FIX #6: Detect stETH → WETH migration even when ETH = 0.
        
        Scenario: Whale has 0 native ETH, swaps 100 stETH → 100 WETH
        OLD: eth_delta=0 fails condition, NOT detected
        NEW: abs(total_delta)≈0 condition catches it
        """
        # Arrange: Empty wallet swaps stETH → WETH
        addresses = ["0x1234567890123456789012345678901234567890"]
        
        # Historical: 0 ETH, 0 WETH, 100 stETH
        eth_historical = {addresses[0]: 0}
        weth_historical = {addresses[0]: 0}
        steth_historical = {addresses[0]: int(Decimal("100") * Decimal("1e18"))}
        
        # Current: 0 ETH, 100 WETH, 0 stETH (swapped!)
        eth_current = {addresses[0]: 0}
        weth_current = {addresses[0]: int(Decimal("100") * Decimal("1e18"))}
        steth_current = {addresses[0]: 0}
        
        steth_rate = Decimal("1.0")
        
        # Act
        migration_count = await calculator._detect_lst_migration(
            addresses=addresses,
            eth_current=eth_current,
            eth_historical=eth_historical,
            weth_current=weth_current,
            steth_current=steth_current,
            weth_historical=weth_historical,
            steth_historical=steth_historical,
            steth_rate=steth_rate
        )
        
        # Assert: Migration MUST be detected
        assert migration_count == 1, "stETH→WETH swap should be detected even with 0 ETH"
    
    @pytest.mark.asyncio
    async def test_weth_to_steth_swap_detected_zero_eth(self, calculator):
        """Detect WETH → stETH migration when ETH = 0."""
        # Arrange: Empty wallet swaps WETH → stETH
        addresses = ["0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"]
        
        # Historical: 0 ETH, 50 WETH, 0 stETH
        eth_historical = {addresses[0]: 0}
        weth_historical = {addresses[0]: int(Decimal("50") * Decimal("1e18"))}
        steth_historical = {addresses[0]: 0}
        
        # Current: 0 ETH, 0 WETH, 50 stETH (swapped!)
        eth_current = {addresses[0]: 0}
        weth_current = {addresses[0]: 0}
        steth_current = {addresses[0]: int(Decimal("50") * Decimal("1e18"))}
        
        steth_rate = Decimal("1.0")
        
        # Act
        migration_count = await calculator._detect_lst_migration(
            addresses=addresses,
            eth_current=eth_current,
            eth_historical=eth_historical,
            weth_current=weth_current,
            steth_current=steth_current,
            weth_historical=weth_historical,
            steth_historical=steth_historical,
            steth_rate=steth_rate
        )
        
        # Assert
        assert migration_count == 1, "WETH→stETH swap should be detected even with 0 ETH"
    
    @pytest.mark.asyncio
    async def test_classic_eth_to_steth_still_detected(self, calculator):
        """Verify classic ETH → stETH migration still works (backward compatibility)."""
        # Arrange: Classic migration (100 ETH → 100 stETH)
        addresses = ["0x9999999999999999999999999999999999999999"]
        
        # Historical: 100 ETH, 0 WETH, 0 stETH
        eth_historical = {addresses[0]: int(Decimal("100") * Decimal("1e18"))}
        weth_historical = {addresses[0]: 0}
        steth_historical = {addresses[0]: 0}
        
        # Current: 0 ETH, 0 WETH, 100 stETH
        eth_current = {addresses[0]: 0}
        weth_current = {addresses[0]: 0}
        steth_current = {addresses[0]: int(Decimal("100") * Decimal("1e18"))}
        
        steth_rate = Decimal("1.0")
        
        # Act
        migration_count = await calculator._detect_lst_migration(
            addresses=addresses,
            eth_current=eth_current,
            eth_historical=eth_historical,
            weth_current=weth_current,
            steth_current=steth_current,
            weth_historical=weth_historical,
            steth_historical=steth_historical,
            steth_rate=steth_rate
        )
        
        # Assert: Classic migration still detected
        assert migration_count == 1, "Classic ETH→stETH migration should still work"
    
    @pytest.mark.asyncio
    async def test_real_accumulation_not_flagged_as_migration(self, calculator):
        """Ensure real WETH accumulation is NOT flagged as migration (net wealth increased)."""
        # Arrange: Real accumulation (bought 50 WETH, net +50 ETH wealth)
        addresses = ["0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]
        
        # Historical: 0 ETH, 0 WETH, 0 stETH
        eth_historical = {addresses[0]: 0}
        weth_historical = {addresses[0]: 0}
        steth_historical = {addresses[0]: 0}
        
        # Current: 0 ETH, 50 WETH, 0 stETH (bought WETH!)
        eth_current = {addresses[0]: 0}
        weth_current = {addresses[0]: int(Decimal("50") * Decimal("1e18"))}
        steth_current = {addresses[0]: 0}
        
        steth_rate = Decimal("1.0")
        
        # Act
        migration_count = await calculator._detect_lst_migration(
            addresses=addresses,
            eth_current=eth_current,
            eth_historical=eth_historical,
            weth_current=weth_current,
            steth_current=steth_current,
            weth_historical=weth_historical,
            steth_historical=steth_historical,
            steth_rate=steth_rate
        )
        
        # Assert: NOT a migration (net wealth increased by 50 ETH)
        assert migration_count == 0, "Real WETH accumulation should NOT be flagged as migration"
    
    @pytest.mark.asyncio
    async def test_partial_swap_within_tolerance(self, calculator):
        """Detect partial LST swap (50 stETH → 49.995 WETH, within gas tolerance)."""
        # Arrange: Partial swap with small loss (gas fees)
        addresses = ["0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"]
        
        # Historical: 0 ETH, 0 WETH, 50 stETH
        eth_historical = {addresses[0]: 0}
        weth_historical = {addresses[0]: 0}
        steth_historical = {addresses[0]: int(Decimal("50") * Decimal("1e18"))}
        
        # Current: 0 ETH, 49.995 WETH, 0 stETH (swapped with 0.005 ETH loss - gas)
        # ✅ 0.005 ETH < 0.01 ETH tolerance
        eth_current = {addresses[0]: 0}
        weth_current = {addresses[0]: int(Decimal("49.995") * Decimal("1e18"))}
        steth_current = {addresses[0]: 0}
        
        steth_rate = Decimal("1.0")
        
        # Act
        migration_count = await calculator._detect_lst_migration(
            addresses=addresses,
            eth_current=eth_current,
            eth_historical=eth_historical,
            weth_current=weth_current,
            steth_current=steth_current,
            weth_historical=weth_historical,
            steth_historical=steth_historical,
            steth_rate=steth_rate
        )
        
        # Assert: Within 0.01 ETH tolerance
        assert migration_count == 1, "Partial swap within gas tolerance should be detected"
    
    @pytest.mark.asyncio
    async def test_complex_three_way_shuffle(self, calculator):
        """Detect complex 3-way LST shuffle (ETH → WETH + stETH)."""
        # Arrange: Complex shuffle (100 ETH → 30 WETH + 70 stETH)
        addresses = ["0xcccccccccccccccccccccccccccccccccccccccc"]
        
        # Historical: 100 ETH, 0 WETH, 0 stETH
        eth_historical = {addresses[0]: int(Decimal("100") * Decimal("1e18"))}
        weth_historical = {addresses[0]: 0}
        steth_historical = {addresses[0]: 0}
        
        # Current: 0 ETH, 30 WETH, 70 stETH (net ≈ 100 ETH)
        eth_current = {addresses[0]: 0}
        weth_current = {addresses[0]: int(Decimal("30") * Decimal("1e18"))}
        steth_current = {addresses[0]: int(Decimal("70") * Decimal("1e18"))}
        
        steth_rate = Decimal("1.0")
        
        # Act
        migration_count = await calculator._detect_lst_migration(
            addresses=addresses,
            eth_current=eth_current,
            eth_historical=eth_historical,
            weth_current=weth_current,
            steth_current=steth_current,
            weth_historical=weth_historical,
            steth_historical=steth_historical,
            steth_rate=steth_rate
        )
        
        # Assert: 3-way shuffle detected
        assert migration_count == 1, "Complex 3-way LST shuffle should be detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
