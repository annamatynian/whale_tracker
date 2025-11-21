"""
ETH Whale Discovery - Поиск крупных ETH holders
================================================

Для нативного ETH (не ERC20) используются альтернативные методы:
1. Известные whale адреса из публичных источников
2. Etherscan UI scraping (опционально)
3. Dune Analytics queries (рекомендуется для production)

Author: Whale Tracker Project
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ETHHolder:
    """Информация о ETH holder"""
    address: str
    balance_eth: float
    balance_usd: float
    rank: Optional[int] = None
    label: Optional[str] = None


# =============================================================================
# ИЗВЕСТНЫЕ ETH КИТЫ
# =============================================================================

KNOWN_ETH_WHALES = [
    {
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'label': 'Vitalik Buterin',
        'category': 'founder'
    },
    {
        'address': '0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B',
        'label': 'Tornado Cash: Deployer',
        'category': 'protocol'
    },
    {
        'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0',
        'label': 'Wrapped Ether',
        'category': 'contract'
    },
    {
        'address': '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',
        'label': 'Binance 7',
        'category': 'exchange'
    },
    # Добавьте больше известных китов здесь
    # Источники:
    # - https://etherscan.io/accounts
    # - https://whale-alert.io/
    # - https://nansen.ai/
]


# =============================================================================
# ПУБЛИЧНЫЕ ИСТОЧНИКИ TOP HOLDERS
# =============================================================================

# Топ-50 ETH адресов (по состоянию на Nov 2023)
# Источник: Etherscan Top Accounts
# ВАЖНО: Исключает биржи и контракты
TOP_ETH_HOLDERS = [
    '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',  # Vitalik
    '0x220866B1A2219f40e72f5c628B65D54268cA3A9D',  # Large holder 1
    '0x2FAF487A4414Fe77e2327F0bf4AE2a264a776AD2',  # Large holder 2
    # ... добавьте больше адресов из публичных источников
]


# =============================================================================
# ETH WHALE DISCOVERY CLIENT
# =============================================================================

class ETHWhaleDiscoveryClient:
    """
    Клиент для поиска ETH китов.

    Методы:
    1. Использование известных адресов
    2. Etherscan API (для проверки балансов)
    3. Опционально: Dune Analytics API
    """

    def __init__(self, etherscan_api_key: Optional[str] = None):
        """Initialize ETH whale discovery client."""
        self.etherscan_api_key = etherscan_api_key
        self.etherscan_base_url = "https://api.etherscan.io/api"

    async def get_eth_balance(self, address: str) -> float:
        """
        Получить ETH баланс адреса через Etherscan API.

        Args:
            address: Ethereum address

        Returns:
            Balance in ETH
        """
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest',
            'apikey': self.etherscan_api_key or ''
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.etherscan_base_url,
                    params=params,
                    timeout=10
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if data.get('status') == '1':
                        balance_wei = int(data.get('result', 0))
                        balance_eth = balance_wei / 1e18
                        return balance_eth
                    else:
                        print(f"⚠️  Etherscan API error: {data.get('message')}")
                        return 0.0

        except Exception as e:
            print(f"❌ Error getting balance for {address}: {e}")
            return 0.0

    async def get_known_whales(
        self,
        min_balance_eth: float = 1000,
        eth_price_usd: float = 3500
    ) -> List[ETHHolder]:
        """
        Получить список известных ETH китов с их балансами.

        Args:
            min_balance_eth: Минимальный баланс в ETH
            eth_price_usd: Цена ETH в USD

        Returns:
            List of ETHHolder objects
        """
        print(f"\n🔍 Получение балансов известных ETH китов...")
        print(f"   Минимальный баланс: {min_balance_eth:,.0f} ETH (${min_balance_eth * eth_price_usd:,.0f})")

        holders = []

        for i, whale_info in enumerate(KNOWN_ETH_WHALES, 1):
            address = whale_info['address']
            label = whale_info.get('label', 'Unknown')
            category = whale_info.get('category', 'unknown')

            print(f"\n[{i}/{len(KNOWN_ETH_WHALES)}] Проверка {label}")
            print(f"   Address: {address}")

            # Пропускаем биржи и контракты
            if category in ['exchange', 'contract']:
                print(f"   ⛔ Пропускаем: {category}")
                continue

            # Получаем баланс
            balance_eth = await self.get_eth_balance(address)

            if balance_eth < min_balance_eth:
                print(f"   ⛔ Баланс слишком мал: {balance_eth:,.2f} ETH")
                continue

            balance_usd = balance_eth * eth_price_usd

            print(f"   ✅ Баланс: {balance_eth:,.2f} ETH (~${balance_usd:,.0f})")

            holder = ETHHolder(
                address=address,
                balance_eth=balance_eth,
                balance_usd=balance_usd,
                rank=i,
                label=label
            )

            holders.append(holder)

            # Rate limiting
            await asyncio.sleep(0.2)

        print(f"\n✅ Найдено {len(holders)} ETH китов")
        return holders

    async def discover_from_list(
        self,
        addresses: List[str],
        min_balance_eth: float = 1000,
        eth_price_usd: float = 3500
    ) -> List[ETHHolder]:
        """
        Проверить список адресов и вернуть тех, кто соответствует критериям.

        Args:
            addresses: List of Ethereum addresses
            min_balance_eth: Минимальный баланс в ETH
            eth_price_usd: Цена ETH в USD

        Returns:
            List of ETHHolder objects
        """
        print(f"\n🔍 Проверка {len(addresses)} адресов...")

        holders = []

        for i, address in enumerate(addresses, 1):
            print(f"\n[{i}/{len(addresses)}] {address}")

            balance_eth = await self.get_eth_balance(address)

            if balance_eth < min_balance_eth:
                print(f"   ⛔ Баланс: {balance_eth:,.2f} ETH (меньше порога)")
                continue

            balance_usd = balance_eth * eth_price_usd
            print(f"   ✅ Баланс: {balance_eth:,.2f} ETH (~${balance_usd:,.0f})")

            holder = ETHHolder(
                address=address,
                balance_eth=balance_eth,
                balance_usd=balance_usd,
                rank=i
            )

            holders.append(holder)

            # Rate limiting
            await asyncio.sleep(0.2)

        return holders


# =============================================================================
# ИНТЕГРАЦИЯ С DUNE ANALYTICS (опционально)
# =============================================================================

class DuneAnalyticsETHWhales:
    """
    Получение ETH китов через Dune Analytics.

    Требует Dune API key (платный).
    https://dune.com/docs/api/
    """

    def __init__(self, dune_api_key: str):
        """Initialize Dune Analytics client."""
        self.api_key = dune_api_key
        self.base_url = "https://api.dune.com/api/v1"

    async def get_top_eth_holders(
        self,
        limit: int = 100,
        exclude_contracts: bool = True
    ) -> List[Dict]:
        """
        Получить топ ETH holders через Dune Analytics.

        Args:
            limit: Количество holders
            exclude_contracts: Исключить контракты

        Returns:
            List of holder data
        """
        # SQL query для Dune Analytics
        query = f"""
        SELECT
            address,
            balance / 1e18 as balance_eth,
            rank() OVER (ORDER BY balance DESC) as rank
        FROM ethereum.balances
        WHERE balance > 1000 * 1e18  -- минимум 1000 ETH
        {'AND is_contract = false' if exclude_contracts else ''}
        ORDER BY balance DESC
        LIMIT {limit}
        """

        print("⚠️  Dune Analytics интеграция требует API key")
        print("   Получить на: https://dune.com/settings/api")

        # TODO: Реализовать Dune API call
        return []


# =============================================================================
# CLI EXAMPLE
# =============================================================================

async def main():
    """Пример использования"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("\n" + "=" * 80)
    print("🐋 ETH WHALE DISCOVERY")
    print("=" * 80)

    etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')

    if not etherscan_api_key:
        print("\n⚠️  ETHERSCAN_API_KEY не найден в .env")
        print("   Получите бесплатный ключ на: https://etherscan.io/apis")
        print("   Продолжаю без ключа (лимит 5 запросов/сек)...\n")

    client = ETHWhaleDiscoveryClient(etherscan_api_key=etherscan_api_key)

    # Метод 1: Известные киты
    print("\n" + "=" * 80)
    print("МЕТОД 1: Известные ETH киты")
    print("=" * 80)

    holders = await client.get_known_whales(
        min_balance_eth=100,  # Минимум 100 ETH
        eth_price_usd=3500    # ~$3500/ETH
    )

    print("\n📊 РЕЗУЛЬТАТЫ:")
    print("=" * 80)

    for holder in holders:
        print(f"\n{holder.rank}. {holder.label or 'Unknown'}")
        print(f"   Address: {holder.address}")
        print(f"   Balance: {holder.balance_eth:,.2f} ETH (${holder.balance_usd:,.0f})")

    # Экспорт адресов
    if holders:
        addresses = [h.address for h in holders]
        print("\n" + "=" * 80)
        print("📋 АДРЕСА ДЛЯ МОНИТОРИНГА")
        print("=" * 80)
        print("\nДобавьте в .env файл:\n")
        print(f"WHALE_ADDRESSES={','.join(addresses)}")
        print()

    # Метод 2: Пользовательский список
    print("\n" + "=" * 80)
    print("МЕТОД 2: Проверка пользовательского списка")
    print("=" * 80)
    print("\nДля проверки своего списка адресов:")
    print("custom_addresses = ['0x...', '0x...']")
    print("holders = await client.discover_from_list(custom_addresses)")


if __name__ == "__main__":
    asyncio.run(main())
