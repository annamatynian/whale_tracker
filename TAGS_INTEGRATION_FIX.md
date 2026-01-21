# Tags Integration - Required Fixes

## 1. [High Conviction] - Fix MAD Threshold Logic

**CURRENT (BROKEN):**
```python
# [High Conviction]
if (metric.lst_adjusted_score and metric.lst_adjusted_score > Decimal('0.5') and
    not metric.is_anomaly):
    tags.append("High Conviction")
```

**PROBLEM:** 
- `lst_adjusted_score` is ABSOLUTE balance (in ETH), not percentage!
- `0.5` means 500K ETH - nonsense threshold
- Should use `3×MAD` for statistical significance

**FIX:**
```python
# [High Conviction]
if (metric.lst_adjusted_score and 
    metric.mad_threshold and 
    metric.lst_adjusted_score > (metric.mad_threshold * Decimal('3')) and
    not metric.is_anomaly):
    tags.append("High Conviction")
    self.logger.debug(
        f"Tag: [High Conviction] - Score {metric.lst_adjusted_score:.4f} ETH "
        f"exceeds 3×MAD threshold ({metric.mad_threshold * 3:.4f} ETH), no anomaly"
    )
```

**WHY:** Статистическая значимость требует превышения 3 стандартных отклонений (3σ = 3×MAD).

---

## 2. [Depeg Risk] - Add Missing Tag

**MISSING:** Critical tag for stETH depeg detection

**ADD:**
```python
# [Depeg Risk] - CRITICAL for Aave liquidation cascade
if metric.steth_eth_rate and metric.steth_eth_rate < Decimal('0.98'):
    tags.append("Depeg Risk")
    self.logger.warning(
        f"Tag: [Depeg Risk] - stETH trading at {metric.steth_eth_rate:.4f} ETH "
        f"(< 0.98 threshold, liquidation risk in lending protocols)"
    )
```

**WHY:** 
- stETH < 0.98 ETH triggers cascade liquidations in Aave/Compound
- Historical precedent: June 2022 depeg to 0.92 caused \$300M+ liquidations
- GEMINI research confirms 0.98 as critical threshold

---

## 3. [Bullish Divergence] - Fix Score Interpretation

**CURRENT (AMBIGUOUS):**
```python
# [Bullish Divergence]
if (metric.price_change_48h_pct and 
    metric.price_change_48h_pct < Decimal('-2.0') and
    metric.lst_adjusted_score and metric.lst_adjusted_score > Decimal('0.2')):
```

**PROBLEM:**
- `lst_adjusted_score` is ABSOLUTE balance (ETH), not %
- Comparing `0.2 ETH` to price change `-2%` - WRONG UNITS!

**FIX:**
```python
# [Bullish Divergence]
if (metric.price_change_48h_pct and 
    metric.price_change_48h_pct < Decimal('-2.0') and
    metric.accumulation_score and metric.accumulation_score > Decimal('0.2')):
    # ^^^^^^^^^^^^^^^^^^^^^^^ USE PERCENTAGE SCORE, NOT ABSOLUTE BALANCE!
    tags.append("Bullish Divergence")
    self.logger.debug(
        f"Tag: [Bullish Divergence] - Accumulation +{metric.accumulation_score:.2f}% "
        f"while price dropped {metric.price_change_48h_pct:.2f}% (alpha signal)"
    )
```

**WHY:** 
- Bullish Divergence = whales buying (%) during price drop (%)
- Must compare LIKE UNITS: percentage vs percentage
- `accumulation_score` is the correct metric (percentage change)

---

## 4. Code Location

File: `src/analyzers/accumulation_score_calculator.py`
Method: `_assign_tags(self, metric: AccumulationMetricCreate, whale_count: int)`

Insert fixes starting at line ~450 (current tag assignment section).

---

## 5. Testing After Fix

```python
# Test case 1: High Conviction
metric.lst_adjusted_score = 1000000.0  # 1M ETH absolute change
metric.mad_threshold = 250000.0        # MAD = 250K ETH
metric.is_anomaly = False
# Expected: Tag activated (1M > 3×250K = 750K)

# Test case 2: Depeg Risk
metric.steth_eth_rate = 0.97  # Below 0.98 threshold
# Expected: Tag activated + WARNING log

# Test case 3: Bullish Divergence
metric.accumulation_score = 2.5       # +2.5% accumulation
metric.price_change_48h_pct = -3.2    # -3.2% price drop
# Expected: Tag activated (buying during panic)
```

---

## 6. Priority

1. **HIGH**: Fix [High Conviction] - wrong threshold logic
2. **CRITICAL**: Add [Depeg Risk] - missing safety feature
3. **MEDIUM**: Fix [Bullish Divergence] - wrong units
