"""
Market Conditions Agent - Crypto Multi-Agent System

This agent analyzes current market conditions based on USDT dominance.
It determines whether the market is in AGGRESSIVE or CONSERVATIVE mode.

Author: Generated for Crypto Multi-Agent System
"""

import requests
import logging
import subprocess
import time
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed

# --- 1. Pydantic Model (Data Contract) ---
class MarketConditionsReport(BaseModel):
    """
    Строгий контракт для результатов Market Conditions Agent.
    """
    market_regime: str = Field(
        ..., 
        pattern=r'^(AGGRESSIVE|CONSERVATIVE|UNKNOWN)$',
        description="Текущий режим рынка"
    )
    usdt_dominance_percentage: float = Field(
        ..., 
        ge=0, 
        le=100, 
        description="Процент доминации USDT"
    )
    data_source: str = Field(
        "CoinGecko", 
        description="Источник данных"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Время проведения анализа"
    )
    
    # Поле для Принципа #7: Воспроизводимость
    git_commit_hash: Optional[str] = Field(
        None, 
        description="Git commit hash для воспроизводимости кода"
    )
    
    # Метрики производительности для наблюдаемости
    api_response_time_ms: Optional[float] = Field(
        None,
        description="Время ответа API в миллисекундах"
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Общее время обработки в миллисекундах"
    )

# --- 2. Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# --- 3. Utility Functions ---
def get_current_git_hash() -> Optional[str]:
    """
    Gets the short hash of the current git commit.
    
    Returns:
        Optional[str]: Short git commit hash or None if git is not available
    """
    try:
        result = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=None,
            stderr=subprocess.DEVNULL
        )
        return result.decode('ascii').strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        logger.warning(f"Could not get git hash: {e}")
        return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_coingecko_global_data() -> tuple[Optional[dict], Optional[float]]:
    """
    Fetches global market data from CoinGecko API with retry mechanism.
    
    Returns:
        tuple: (API response data or None, response time in ms or None)
    """
    url = "https://api.coingecko.com/api/v3/global"
    headers = {
        'User-Agent': 'crypto-multi-agent-system/1.0',
        'Accept': 'application/json'
    }
    
    try:
        logger.debug(f"Making request to {url}")
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.debug(f"Successfully fetched data from CoinGecko in {response_time:.1f}ms")
        return data, response_time
        
    except requests.exceptions.Timeout:
        logger.error("Request to CoinGecko API timed out")
        return None, None
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to CoinGecko API")
        return None, None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from CoinGecko API: {e}")
        return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from CoinGecko: {e}")
        return None, None
    except ValueError as e:
        logger.error(f"Error parsing JSON response from CoinGecko: {e}")
        return None, None

# --- 4. Core Agent Logic ---
def analyze_market_conditions() -> MarketConditionsReport:
    """
    Analyzes the market conditions based on USDT dominance.
    This is the core function of the Market Conditions Agent.
    
    Logic:
    - USDT dominance < 4.5% → AGGRESSIVE market (money flowing into risky assets)
    - USDT dominance >= 4.5% → CONSERVATIVE market (money flowing to stablecoins)
    
    Returns:
        MarketConditionsReport: Structured report with market analysis
    """
    start_processing = time.time()
    logger.info("🚀 Starting market conditions analysis...")
    
    # Get git hash for reproducibility
    git_hash = get_current_git_hash()
    
    # Fetch market data with performance metrics
    api_data, api_response_time = fetch_coingecko_global_data()

    if not api_data:
        processing_time = (time.time() - start_processing) * 1000
        logger.error("❌ Failed to get data from API. Returning UNKNOWN state.")
        return MarketConditionsReport(
            market_regime="UNKNOWN",
            usdt_dominance_percentage=0.0,
            git_commit_hash=git_hash,
            api_response_time_ms=api_response_time,
            processing_time_ms=processing_time
        )

    try:
        # Extract USDT dominance from API response
        usdt_dominance = api_data['data']['market_cap_percentage']['usdt']
        
        # Determine market regime based on 4.5% threshold
        market_regime = "AGGRESSIVE" if usdt_dominance < 4.5 else "CONSERVATIVE"
        
        # Calculate processing metrics
        processing_time = (time.time() - start_processing) * 1000
        
        # Log successful analysis with performance metrics
        logger.info(
            f"✅ Analysis complete. "
            f"USDT Dominance: {usdt_dominance:.2f}%, "
            f"Market Regime: {market_regime} "
            f"(API: {api_response_time:.1f}ms, Total: {processing_time:.1f}ms)"
        )
        
        return MarketConditionsReport(
            market_regime=market_regime,
            usdt_dominance_percentage=usdt_dominance,
            git_commit_hash=git_hash,
            api_response_time_ms=api_response_time,
            processing_time_ms=processing_time
        )
        
    except KeyError as e:
        processing_time = (time.time() - start_processing) * 1000
        logger.error(f"❌ Missing expected field in API response: {e}")
        logger.debug(f"API response structure: {list(api_data.keys()) if api_data else 'None'}")
        return MarketConditionsReport(
            market_regime="UNKNOWN",
            usdt_dominance_percentage=0.0,
            git_commit_hash=git_hash,
            api_response_time_ms=api_response_time,
            processing_time_ms=processing_time
        )
    except (TypeError, ValueError) as e:
        processing_time = (time.time() - start_processing) * 1000
        logger.error(f"❌ Error parsing API response: {e}")
        logger.debug(f"API data type: {type(api_data)}")
        return MarketConditionsReport(
            market_regime="UNKNOWN",
            usdt_dominance_percentage=0.0,
            git_commit_hash=git_hash,
            api_response_time_ms=api_response_time,
            processing_time_ms=processing_time
        )

# --- 5. Example Usage & Testing ---
def main():
    """Main function for testing the Market Conditions Agent."""
    print("🔍 Market Conditions Agent - Testing Mode")
    print("=" * 50)
    
    try:
        # Run analysis
        report = analyze_market_conditions()
        
        # Display results
        print("\n📊 Market Conditions Report:")
        print("-" * 30)
        print(report.model_dump_json(indent=2))
        print("-" * 30)
        
        # Human-readable summary
        print(f"\n📈 Summary:")
        print(f"   Market Regime: {report.market_regime}")
        print(f"   USDT Dominance: {report.usdt_dominance_percentage:.2f}%")
        print(f"   Analysis Time: {report.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Code Version: {report.git_commit_hash or 'Unknown'}")
        print(f"   Data Source: {report.data_source}")
        
        # Performance metrics
        if report.api_response_time_ms:
            print(f"\n⚡ Performance:")
            print(f"   API Response: {report.api_response_time_ms:.1f}ms")
            print(f"   Total Processing: {report.processing_time_ms:.1f}ms")
        
        # Market interpretation
        if report.market_regime == "AGGRESSIVE":
            print(f"\n🚀 Market Interpretation:")
            print(f"   Money is flowing INTO risky assets (altcoins, memecoins)")
            print(f"   Suitable for high-risk strategies")
        elif report.market_regime == "CONSERVATIVE":
            print(f"\n🛡️  Market Interpretation:")
            print(f"   Money is flowing INTO stablecoins (USDT)")
            print(f"   Suitable for conservative DeFi strategies")
        else:
            print(f"\n⚠️  Unable to determine market conditions")
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in main(): {e}")
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    main()
