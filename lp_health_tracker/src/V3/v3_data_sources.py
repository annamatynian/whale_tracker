
"""
V3 Data Sources Integration
==========================
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import logging

# Настройка логгера
logger = logging.getLogger(__name__)


class V3GraphQLClient:
    """The Graph V3 Subgraph integration with a persistent session."""

    def __init__(self, subgraph_url: str = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"):
        self.subgraph_url = subgraph_url
        # Сессия создается один раз для всего жизненного цикла объекта
        self._session = aiohttp.ClientSession()

    async def query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Универсальный метод для выполнения любого GraphQL запроса.
        Возвращает данные или вызывает исключение в случае ошибки.
        """
        payload = {"query": query, "variables": variables or {}}
        try:
            async with self._session.post(
                self.subgraph_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                response.raise_for_status()  # Вызовет ошибку для статусов 4xx/5xx
                data = await response.json()
                return data.get('data', {})
        except asyncio.TimeoutError:
            logger.error("GraphQL query timed out.")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"GraphQL query failed with a client error: {e}")
            raise

    async def close(self):
        """Метод для корректного закрытия сессии при завершении работы."""
        await self._session.close()

class V3DataProvider:
    """Unified V3 data provider with fallback logic."""

    def __init__(self):
        self.graph_client = V3GraphQLClient()

    async def get_position_data(self, wallet_address: str) -> List[Dict]:
        """Get V3 position data using the universal GraphQL client."""
        # --- ИЗМЕНЕНИЕ: GraphQL-запрос остается тот же, но вызывается через универсальный метод ---
        query = """
        query GetV3Positions($wallet: String!) {
            positions(where: {owner: $wallet}) {
                id
                tickLower
                tickUpper
                liquidity
                depositedToken0
                depositedToken1
                withdrawnToken0
                withdrawnToken1
                collectedFeesToken0
                collectedFeesToken1
                pool {
                    id
                    token0 { symbol decimals }
                    token1 { symbol decimals }
                    tick
                    sqrtPrice
                    feeTier
                }
            }
        }
        """
        variables = {"wallet": wallet_address.lower()}
        
        try:
            data = await self.graph_client.query(query, variables)
            positions = data.get('positions', [])
        except Exception:
            # Если произошла любая ошибка на уровне клиента, возвращаем пустой список
            return []

        # Process and validate positions
        processed = []
        for pos in positions:
            if self._is_valid_position(pos):
                processed.append(self._format_position(pos))
        
        return processed

    def _is_valid_position(self, position: Dict) -> bool:
        """Validate position data."""
        required_fields = ['id', 'liquidity', 'pool']
        # Проверяем, что ликвидность больше нуля, чтобы отсеять закрытые позиции
        return all(field in position for field in required_fields) and int(position.get('liquidity', 0)) > 0

    def _format_position(self, position: Dict) -> Dict:
        """Format position for internal use."""
        pool = position.get('pool', {})
        token0 = pool.get('token0', {})
        token1 = pool.get('token1', {})

        return {
            'token_id': int(position['id']),
            'liquidity': int(position['liquidity']),
            'tick_lower': int(position.get('tickLower', 0)),
            'tick_upper': int(position.get('tickUpper', 0)),
            'pool_address': pool.get('id'),
            'token0_symbol': token0.get('symbol'),
            'token1_symbol': token1.get('symbol'),
            'token0_decimals': token0.get('decimals'),
            'token1_decimals': token1.get('decimals'),
            'fee_tier': int(pool.get('feeTier', 0)),
            'current_tick': int(pool.get('tick', 0)),
            'collected_fees_0': float(position.get('collectedFeesToken0', 0)),
            'collected_fees_1': float(position.get('collectedFeesToken1', 0))
        }

    async def close_connections(self):
        """Gracefully close the underlying client session."""
        await self.graph_client.close()

