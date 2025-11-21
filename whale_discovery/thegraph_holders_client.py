"""
Token Holders Discovery via The Graph
======================================

Автоматическое получение крупных holders ERC20 токенов через The Graph subgraphs.
Использует существующую архитектуру из crypto-multi-agent-system.

Author: Whale Tracker Project
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenHolder:
    """Информация о holder токена"""
    address: str
    balance: float
    balance_raw: str
    percentage: float
    last_updated: Optional[int] = None


class TheGraphTokenHoldersClient:
    """
    Клиент для получения token holders через The Graph.

    Использует различные subgraphs в зависимости от токена:
    - Uniswap tokens: Uniswap subgraph
    - General ERC20: ERC20 subgraph (если доступен)
    """

    # The Graph API endpoint
    GRAPH_API_URL = "https://gateway-arbitrum.network.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"

    # Известные subgraphs для популярных токенов
    KNOWN_SUBGRAPHS = {
        # Uniswap V2
        'UNI': {
            'subgraph_id': '5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV',  # Uniswap V2
            'type': 'uniswap_v2',
            'network': 'ethereum'
        },
        # Uniswap V3
        'UNI_V3': {
            'subgraph_id': '5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV',  # Uniswap V3
            'type': 'uniswap_v3',
            'network': 'ethereum'
        },
        # Для других токенов можно использовать общий ERC20 subgraph
        # Или специфичные subgraphs если известны
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize The Graph client.

        Args:
            api_key: The Graph API key (получить на https://thegraph.com/studio/)
        """
        self.api_key = api_key or "YOUR_GRAPH_API_KEY"
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def build_token_holders_query(
        self,
        token_address: str,
        min_balance: str = "0",
        limit: int = 100,
        skip: int = 0
    ) -> str:
        """
        Построить GraphQL запрос для получения holders.

        Args:
            token_address: Адрес токена
            min_balance: Минимальный баланс (в wei или token units)
            limit: Количество результатов
            skip: Пропустить N результатов

        Returns:
            GraphQL query string
        """
        # NOTE: Точная структура query зависит от конкретного subgraph
        # Для ERC20 tokens обычно есть entity "tokenHolder" или "account"

        query = f"""
        query {{
          tokenHolders(
            where: {{
              token: "{token_address.lower()}",
              balance_gte: "{min_balance}"
            }},
            first: {limit},
            skip: {skip},
            orderBy: balance,
            orderDirection: desc
          ) {{
            id
            address
            balance
            token {{
              id
              symbol
              name
              decimals
              totalSupply
            }}
          }}
        }}
        """

        return query

    async def query_subgraph(
        self,
        subgraph_id: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Выполнить GraphQL запрос к subgraph.

        Args:
            subgraph_id: ID subgraph на The Graph
            query: GraphQL query

        Returns:
            Результат запроса
        """
        if not self.session:
            raise RuntimeError("Use TheGraphTokenHoldersClient as context manager")

        url = self.GRAPH_API_URL.format(
            api_key=self.api_key,
            subgraph_id=subgraph_id
        )

        try:
            async with self.session.post(
                url,
                json={'query': query},
                timeout=30
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if 'errors' in data:
                    self.logger.error(f"GraphQL errors: {data['errors']}")
                    return {'data': {}}

                return data

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout querying subgraph {subgraph_id}")
            return {'data': {}}
        except Exception as e:
            self.logger.error(f"Error querying subgraph: {e}")
            return {'data': {}}

    async def get_token_holders(
        self,
        token_address: str,
        subgraph_id: str,
        min_balance_usd: float = 100000,
        token_price_usd: Optional[float] = None,
        limit: int = 100
    ) -> List[TokenHolder]:
        """
        Получить список holders токена.

        Args:
            token_address: Адрес контракта токена
            subgraph_id: ID subgraph для запроса
            min_balance_usd: Минимальный баланс в USD
            token_price_usd: Цена токена в USD (для фильтрации)
            limit: Максимальное количество holders

        Returns:
            List of TokenHolder objects
        """
        self.logger.info(f"Fetching holders for token {token_address}")

        # Если известна цена токена, конвертируем min_balance_usd в token units
        # Иначе запрашиваем всех и фильтруем после
        min_balance_raw = "0"

        if token_price_usd:
            # Предполагаем 18 decimals (стандарт ERC20)
            # min_balance_raw = (min_balance_usd / token_price_usd) * 10^18
            min_tokens = min_balance_usd / token_price_usd
            min_balance_raw = str(int(min_tokens * 1e18))

        # Построить query
        query = self.build_token_holders_query(
            token_address=token_address,
            min_balance=min_balance_raw,
            limit=limit,
            skip=0
        )

        # Выполнить запрос
        result = await self.query_subgraph(subgraph_id, query)

        # Парсинг результатов
        holders = []

        raw_holders = result.get('data', {}).get('tokenHolders', [])

        if not raw_holders:
            self.logger.warning(f"No holders found for token {token_address}")
            # Возможно schema другая - попробуем альтернативный query
            self.logger.info("Trying alternative schema (accounts)...")
            return await self._try_alternative_schema(token_address, subgraph_id, limit)

        # Получаем total supply для расчета percentage
        total_supply = None
        if raw_holders and 'token' in raw_holders[0]:
            token_info = raw_holders[0]['token']
            total_supply_raw = token_info.get('totalSupply', '0')
            decimals = int(token_info.get('decimals', 18))
            total_supply = float(total_supply_raw) / (10 ** decimals)

        for holder_data in raw_holders:
            try:
                address = holder_data.get('address', holder_data.get('id', ''))
                balance_raw = holder_data.get('balance', '0')

                # Предполагаем 18 decimals
                decimals = 18
                if 'token' in holder_data:
                    decimals = int(holder_data['token'].get('decimals', 18))

                balance = float(balance_raw) / (10 ** decimals)

                # Рассчитываем percentage
                percentage = 0.0
                if total_supply and total_supply > 0:
                    percentage = (balance / total_supply) * 100

                holder = TokenHolder(
                    address=address,
                    balance=balance,
                    balance_raw=balance_raw,
                    percentage=percentage
                )

                holders.append(holder)

            except Exception as e:
                self.logger.error(f"Error parsing holder data: {e}")
                continue

        self.logger.info(f"Found {len(holders)} holders for token {token_address}")
        return holders

    async def _try_alternative_schema(
        self,
        token_address: str,
        subgraph_id: str,
        limit: int = 100
    ) -> List[TokenHolder]:
        """
        Попробовать альтернативную схему (accounts вместо tokenHolders).

        Некоторые subgraphs используют другую структуру данных.
        """
        query = f"""
        query {{
          accounts(
            where: {{
              token_: {{id: "{token_address.lower()}"}}
            }},
            first: {limit},
            orderBy: balance,
            orderDirection: desc
          ) {{
            id
            balance
          }}
        }}
        """

        result = await self.query_subgraph(subgraph_id, query)

        raw_accounts = result.get('data', {}).get('accounts', [])

        if not raw_accounts:
            self.logger.warning("Alternative schema also returned no results")
            return []

        holders = []
        for account_data in raw_accounts:
            try:
                holder = TokenHolder(
                    address=account_data.get('id', ''),
                    balance=float(account_data.get('balance', 0)) / 1e18,
                    balance_raw=account_data.get('balance', '0'),
                    percentage=0.0  # Не можем рассчитать без total supply
                )
                holders.append(holder)
            except Exception as e:
                self.logger.error(f"Error parsing account: {e}")

        return holders

    async def get_holders_for_known_token(
        self,
        token_symbol: str,
        min_balance_usd: float = 100000,
        limit: int = 100
    ) -> List[TokenHolder]:
        """
        Получить holders для известного токена (из KNOWN_SUBGRAPHS).

        Args:
            token_symbol: Символ токена (UNI, LINK, etc.)
            min_balance_usd: Минимальный баланс в USD
            limit: Максимальное количество

        Returns:
            List of TokenHolder objects
        """
        if token_symbol not in self.KNOWN_SUBGRAPHS:
            self.logger.error(f"No known subgraph for token {token_symbol}")
            self.logger.info(f"Available tokens: {list(self.KNOWN_SUBGRAPHS.keys())}")
            return []

        config = self.KNOWN_SUBGRAPHS[token_symbol]
        subgraph_id = config['subgraph_id']

        # Для известных токенов нужен token_address
        # TODO: Добавить маппинг symbol -> address
        self.logger.warning("Token address needed for query - not implemented yet")
        return []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def discover_whale_addresses(
    token_address: str,
    subgraph_id: str,
    graph_api_key: Optional[str] = None,
    min_balance_usd: float = 100000,
    limit: int = 50
) -> List[str]:
    """
    Автоматически найти whale addresses для токена через The Graph.

    Args:
        token_address: Адрес контракта токена
        subgraph_id: ID subgraph на The Graph
        graph_api_key: The Graph API key
        min_balance_usd: Минимальный баланс в USD
        limit: Количество адресов

    Returns:
        List of whale addresses
    """
    async with TheGraphTokenHoldersClient(api_key=graph_api_key) as client:
        holders = await client.get_token_holders(
            token_address=token_address,
            subgraph_id=subgraph_id,
            min_balance_usd=min_balance_usd,
            limit=limit
        )

        # Возвращаем только адреса
        return [holder.address for holder in holders]


# =============================================================================
# CLI EXAMPLE
# =============================================================================

async def main_example():
    """Пример использования"""

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Пример: получить holders для UNI токена
    token_address = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"  # UNI token
    subgraph_id = "EYCKATKGBKLWvSfwvBjzfCBmGwYNdVkduYXVivCsLRFu"  # Uniswap V3 subgraph

    print("\n" + "=" * 80)
    print("🔍 Token Holders Discovery via The Graph")
    print("=" * 80)

    async with TheGraphTokenHoldersClient() as client:
        holders = await client.get_token_holders(
            token_address=token_address,
            subgraph_id=subgraph_id,
            min_balance_usd=100000,
            limit=20
        )

        print(f"\n📊 Найдено {len(holders)} крупных holders:\n")

        for i, holder in enumerate(holders[:10], 1):
            print(f"{i}. {holder.address}")
            print(f"   Balance: {holder.balance:,.2f} tokens ({holder.percentage:.2f}%)")
            print()

        # Экспорт адресов
        addresses = [h.address for h in holders]
        print("\n" + "=" * 80)
        print("📋 Адреса для мониторинга:")
        print("=" * 80)
        print(",".join(addresses))
        print()


if __name__ == "__main__":
    asyncio.run(main_example())
