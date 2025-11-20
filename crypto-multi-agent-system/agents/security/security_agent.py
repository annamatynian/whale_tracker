"""
Security Agent - Crypto Multi-Agent System

Проверяет безопасность токенов через GoPlus Security API.
Выявляет honeypots, высокие налоги, неверифицированные контракты и другие
красные флаги для защиты от скама.

Author: Generated for Crypto Multi-Agent System
"""

import requests
import logging
import subprocess
import time
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError

from tenacity import retry, stop_after_attempt, wait_fixed

# --- 1. Configuration Constants ---
# Risk scoring thresholds
HONEYPOT_RISK_SCORE = 90
HIGH_TAX_THRESHOLD = 0.15  # 15%
MEDIUM_TAX_THRESHOLD = 0.05  # 5%
HIGH_TAX_RISK_SCORE = 40
MEDIUM_TAX_RISK_SCORE = 20
UNVERIFIED_CONTRACT_RISK = 25
NO_LOCKED_LIQUIDITY_RISK = 15

# Risk categories thresholds
SAFE_THRESHOLD = 20
CAUTION_THRESHOLD = 40
HIGH_RISK_THRESHOLD = 70

# --- 2. Pydantic Model (Data Contract) ---
class SecurityReport(BaseModel):
    contract_address: str = Field(..., description="Адрес контракта токена")
    is_honeypot: Optional[bool] = Field(None, description="Является ли honeypot")
    is_verified: bool = Field(False, description="Верифицирован ли контракт")
    buy_tax: Optional[float] = Field(None, ge=0, le=1, description="Налог на покупку (0-1)")
    sell_tax: Optional[float] = Field(None, ge=0, le=1, description="Налог на продажу (0-1)")
    liquidity_locked: Optional[bool] = Field(None, description="Заблокирована ли ликвидность")
    owner_address: Optional[str] = Field(None, description="Адрес владельца контракта")
    
    risk_score: int = Field(..., ge=0, le=100, description="Общий риск-скор 0-100")
    risk_category: str = Field(..., description="SAFE/CAUTION/HIGH_RISK/SCAM")
    red_flags: List[str] = Field(default_factory=list, description="Список красных флагов")
    
    # Standard fields for consistency
    data_source: str = Field("GoPlus", description="Источник данных")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Время проведения анализа")
    git_commit_hash: Optional[str] = Field(None, description="Git commit hash для воспроизводимости кода")
    api_response_time_ms: Optional[float] = Field(None, description="Время ответа API в миллисекундах")
    processing_time_ms: Optional[float] = Field(None, description="Общее время обработки в миллисекундах")

# --- 3. Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# --- 4. Placeholder Tools (for Cost Management & Rate Limiting) ---
# In a real project, these would be imported from a shared `tools` module.
def track_api_cost(api_name: str, cost_units: int = 1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"[CostTracker] Recording {cost_units} unit(s) for {api_name} API.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(api_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"[RateLimiter] Checking rate limit for {api_name}.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# --- 5. Utility & Core Functions ---
def get_current_git_hash() -> Optional[str]:
    """Gets the short hash of the current git commit."""
    try:
        result = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL)
        return result.decode('ascii').strip()
    except Exception as e:
        logger.warning(f"Could not get git hash: {e}")
        return None

@rate_limit('goplus')
@track_api_cost('goplus', cost_units=1)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_goplus_security_data(contract_address: str, chain_id: str = '1') -> tuple[Optional[Dict[str, Any]], Optional[float]]:
    """Fetches token security data from the GoPlus Labs API."""
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={contract_address}"
    headers = {'User-Agent': 'crypto-multi-agent-system/1.0'}
    
    try:
        logger.debug(f"Fetching security data for {contract_address} on chain {chain_id}")
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        response_time = (time.time() - start_time) * 1000
        
        # GoPlus returns a result object, even for errors. We need to check the code.
        if data.get('code') != 1:
             logger.error(f"GoPlus API returned error: {data.get('message')}")
             return None, response_time

        # Extract the specific contract data from the nested response
        contract_data = data.get('result', {}).get(contract_address.lower())
        return contract_data, response_time
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from GoPlus for {contract_address}: {e}")
        return None, None
    except ValueError as e:
        logger.error(f"Error parsing JSON from GoPlus for {contract_address}: {e}")
        return None, None

def calculate_security_risk(security_data: Dict[str, Any]) -> tuple[int, List[str], str]:
    """Calculates a security risk score and category based on GoPlus data."""
    score = 0
    red_flags = []

    # Honeypot check (critical)
    if security_data.get('is_honeypot') == '1':
        score += HONEYPOT_RISK_SCORE
        red_flags.append("HONEYPOT_DETECTED")

    # Tax check
    try:
        buy_tax = float(security_data.get('buy_tax', '0'))
        sell_tax = float(security_data.get('sell_tax', '0'))
        if buy_tax > HIGH_TAX_THRESHOLD or sell_tax > HIGH_TAX_THRESHOLD:
            score += HIGH_TAX_RISK_SCORE
            red_flags.append(f"HIGH_TAX_RATE (Buy: {buy_tax:.0%}, Sell: {sell_tax:.0%})")
        elif buy_tax > MEDIUM_TAX_THRESHOLD or sell_tax > MEDIUM_TAX_THRESHOLD:
            score += MEDIUM_TAX_RISK_SCORE
            red_flags.append(f"MEDIUM_TAX_RATE (Buy: {buy_tax:.0%}, Sell: {sell_tax:.0%})")
    except (ValueError, TypeError):
        red_flags.append("TAX_INFO_INVALID")

    # Contract verification check
    if security_data.get('is_open_source') == '0':
        score += UNVERIFIED_CONTRACT_RISK
        red_flags.append("CONTRACT_NOT_VERIFIED")

    # Liquidity lock check (simplified: check if LP holder is a known locker)
    # A full implementation would check the percentage and duration of lock.
    has_lock = any('lock' in str(holder.get('address', '')) for holder in security_data.get('lp_holders', []))
    if not has_lock:
        score += NO_LOCKED_LIQUIDITY_RISK
        red_flags.append("NO_LOCKED_LIQUIDITY_DETECTED")

    # Determine risk category
    final_score = min(score, 100)
    if final_score >= HIGH_RISK_THRESHOLD:
        category = "SCAM" if "HONEYPOT" in str(red_flags) else "HIGH_RISK"
    elif final_score >= CAUTION_THRESHOLD:
        category = "CAUTION"
    else:
        category = "SAFE"
        
    return final_score, red_flags, category

# --- 6. Core Agent Logic (Sync & Async) ---
def analyze_token_security(contract_address: str) -> Optional[SecurityReport]:
    """Core synchronous function for security analysis."""
    start_processing = time.time()
    logger.info(f"🛡️ Starting security analysis for {contract_address}...")
    git_hash = get_current_git_hash()
    
    api_data, api_time = fetch_goplus_security_data(contract_address)

    # Handle API/data errors according to the specified strategy
    if api_data is None:
        risk_score, flags, category = 50, ["API_UNAVAILABLE"], "HIGH_RISK"
    elif not api_data: # Empty dict means contract not found in GoPlus
        risk_score, flags, category = 80, ["CONTRACT_NOT_FOUND"], "HIGH_RISK"
    else:
        try:
            risk_score, flags, category = calculate_security_risk(api_data)
        except Exception:
            risk_score, flags, category = 60, ["DATA_PARSING_ERROR"], "HIGH_RISK"
            
    try:
        report = SecurityReport(
            contract_address=contract_address,
            is_honeypot=api_data.get('is_honeypot') == '1' if api_data else None,
            is_verified=api_data.get('is_open_source') == '1' if api_data else False,
            buy_tax=float(api_data.get('buy_tax', '0')) if api_data else None,
            sell_tax=float(api_data.get('sell_tax', '0')) if api_data else None,
            liquidity_locked=any('lock' in str(h.get('address', '')) for h in api_data.get('lp_holders', [])) if api_data else None,
            owner_address=api_data.get('owner_address') if api_data else None,
            risk_score=risk_score,
            risk_category=category,
            red_flags=flags,
            git_commit_hash=git_hash,
            api_response_time_ms=api_time,
            processing_time_ms=(time.time() - start_processing) * 1000,
        )
        logger.info(f"✅ Security analysis complete for {contract_address}. Risk Score: {report.risk_score} ({report.risk_category})")
        return report
    except ValidationError as e:
        logger.error(f"❌ Failed to create SecurityReport for {contract_address}: {e}")
        return None

async def analyze_token_security_async(contract_address: str) -> Optional[SecurityReport]:
    """Async wrapper for the core security analysis logic."""
    logger.info(f"Running sync security analysis for {contract_address} in executor...")
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, analyze_token_security, contract_address)

# --- 7. Example Usage & Testing ---
async def main():
    """Main async function for testing the Security Agent."""
    print("🛡️ Security Agent - Testing Mode")
    print("=" * 50)
    
    test_cases = {
        "SAFE (USDC)": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", # Corrected USDC address
        "HIGH_TAX_TOKEN": "0x74c1E4B8CAE49272212d25243181f2142B28415a", # Example of a token with tax
        "SUSPICIOUS": "0x163f8C2467924be0ae7B5347228CABF260318753", # Example of a risky token
        "INVALID_ADDRESS": "0x0000000000000000000000000000000000000000"
    }

    for name, address in test_cases.items():
        print(f"\n--- Testing: {name} ({address}) ---")
        report = await analyze_token_security_async(address)
        
        if report:
            print(f"   📊 Risk Score: {report.risk_score}/100")
            print(f"   🏷️ Category: {report.risk_category}")
            print(f"    Verified: {report.is_verified}")
            print(f"   Honeypot: {report.is_honeypot}")
            if report.buy_tax is not None:
                print(f"   Tax (Buy/Sell): {report.buy_tax:.1%} / {report.sell_tax:.1%}")
            if report.red_flags:
                print(f"   🚩 Red Flags: {', '.join(report.red_flags)}")
        else:
            print("   ❌ Failed to generate report.")
        print("-" * 30)

if __name__ == "__main__":
    # Note: On Windows, you might see a "RuntimeError: Event loop is closed"
    # which is often a benign warning. Using asyncio.run() is the modern way.
    asyncio.run(main())