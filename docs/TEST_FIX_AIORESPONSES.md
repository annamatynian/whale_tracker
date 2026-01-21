# Test Fix: aioresponses Request Counting

## Issue
Tests were failing with:
```
AssertionError: assert 1 == 2
```

## Root Cause
`aioresponses.requests` is a dictionary that **groups requests by URL**.

- `len(m.requests)` returns number of **unique URLs** (always 1 in our case)
- But we need to count **total API calls** (can be multiple to same URL)

## Example
```python
# Two calls to same URL
m.get(url, payload=...)  # Call 1
m.get(url, payload=...)  # Call 2

# aioresponses structure:
m.requests = {
    ('GET', URL(...)): [
        RequestCall(...),  # First call
        RequestCall(...)   # Second call
    ]
}

len(m.requests) == 1           # ❌ WRONG - counts unique URLs
len(m.requests[url_key]) == 2  # ✅ CORRECT - counts actual calls
```

## Fix Applied
Changed from:
```python
assert len(m.requests) == 2  # ❌ Wrong
```

To:
```python
# ✅ Correct - sum all RequestCall objects across all URLs
total_calls = sum(len(calls) for calls in m.requests.values())
assert total_calls == 2
```

## Tests Fixed
1. `test_get_steth_eth_rate_cached` - expects 1 call
2. `test_get_steth_eth_rate_cache_expiry` - expects 2 calls
3. `test_multiple_concurrent_calls_use_cache` - expects 1 call

## Verification
All tests should now pass:
```bash
pytest tests/unit/test_price_provider_steth.py -v
# Expected: 12/12 PASSED ✅
```
