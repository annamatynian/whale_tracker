"""
Whale Finder AUTO - Полностью автоматический поиск китов через The Graph
==========================================================================

Использует The Graph для автоматического получения holders,
затем анализирует их через whale_finder алгоритм.

Usage:
    python whale_finder_auto.py --token-address 0x1f9840... --subgraph-id ABC123
    python whale_finder_auto.py --preset UNI --limit 50
"""

import asyncio
import os
import sys
from typing import List, Optional

from dotenv import load_dotenv

# Импорт наших модулей
from thegraph_holders_client import TheGraphTokenHoldersClient, discover_whale_addresses
from whale_finder import WhaleFinder, WhaleInfo

load_dotenv()


# =============================================================================
# ПРЕСЕТЫ ДЛЯ ПОПУЛЯРНЫХ ТОКЕНОВ
# =============================================================================

TOKEN_PRESETS = {
    'UNI': {
        'name': 'Uniswap',
        'token_address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
        'subgraph_id': 'EYCKATKGBKLWvSfwvBjzfCBmGwYNdVkduYXVivCsLRFu',  # Uniswap V3
        'decimals': 18
    },
    'LINK': {
        'name': 'Chainlink',
        'token_address': '0x514910771AF9Ca656af840dff83E8264EcF986CA',
        'subgraph_id': 'EYCKATKGBKLWvSfwvBjzfCBmGwYNdVkduYXVivCsLRFu',  # Может потребоваться другой
        'decimals': 18
    },
    'AAVE': {
        'name': 'Aave',
        'token_address': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',
        'subgraph_id': 'EYCKATKGBKLWvSfwvBjzfCBmGwYNdVkduYXVivCsLRFu',
        'decimals': 18
    },
}


# =============================================================================
# АВТОМАТИЧЕСКИЙ ПОИСК
# =============================================================================

class AutoWhaleFinderIntegrated:
    """
    Интегрированный поиск китов:
    1. The Graph → получение holders
    2. Whale Finder → анализ качества
    3. Экспорт лучших адресов
    """

    def __init__(self, graph_api_key: Optional[str] = None):
        """
        Initialize автоматического whale finder.

        Args:
            graph_api_key: The Graph API key (опционально)
        """
        self.graph_api_key = graph_api_key or os.getenv('THEGRAPH_API_KEY')
        self.whale_finder = WhaleFinder()

    async def discover_and_analyze(
        self,
        token_address: str,
        subgraph_id: str,
        token_symbol: str = "TOKEN",
        min_balance_usd: float = 100000,
        limit: int = 100,
        check_activity: bool = True
    ) -> List[WhaleInfo]:
        """
        Полный цикл: поиск holders через The Graph + анализ.

        Args:
            token_address: Адрес контракта токена
            subgraph_id: The Graph subgraph ID
            token_symbol: Символ токена (для отображения)
            min_balance_usd: Минимальный баланс для поиска
            limit: Количество holders для анализа
            check_activity: Проверять активность через Etherscan

        Returns:
            List of analyzed WhaleInfo objects
        """
        print("\n" + "=" * 80)
        print(f"🤖 АВТОМАТИЧЕСКИЙ ПОИСК КИТОВ ДЛЯ {token_symbol}")
        print("=" * 80)

        # Шаг 1: Получение holders через The Graph
        print(f"\n📡 ШАГ 1: Получение holders через The Graph")
        print(f"   Token: {token_address}")
        print(f"   Subgraph: {subgraph_id}")
        print(f"   Минимальный баланс: ${min_balance_usd:,}")
        print(f"   Лимит: {limit} holders\n")

        async with TheGraphTokenHoldersClient(api_key=self.graph_api_key) as graph_client:
            holders = await graph_client.get_token_holders(
                token_address=token_address,
                subgraph_id=subgraph_id,
                min_balance_usd=min_balance_usd,
                limit=limit
            )

            if not holders:
                print("❌ Не удалось получить holders через The Graph")
                print("\n💡 Возможные причины:")
                print("   1. Неверный subgraph_id")
                print("   2. Subgraph не содержит tokenHolders entity")
                print("   3. Неверный token_address")
                print("\n💡 Попробуйте:")
                print("   1. Проверить subgraph на https://thegraph.com/explorer")
                print("   2. Использовать ручной режим: --addresses или --file")
                return []

            print(f"✅ Получено {len(holders)} holders")
            print(f"\nТоп-5 крупнейших holders:")
            for i, holder in enumerate(holders[:5], 1):
                print(f"   {i}. {holder.address[:10]}...{holder.address[-8:]}")
                print(f"      Balance: {holder.balance:,.2f} tokens ({holder.percentage:.2f}%)")

        # Шаг 2: Анализ качества через Whale Finder
        print(f"\n🔍 ШАГ 2: Анализ качества китов")
        print(f"   Проверка активности: {'ДА' if check_activity else 'НЕТ'}\n")

        whale_addresses = [holder.address for holder in holders]

        whales = await self.whale_finder.find_whales(
            whale_addresses=whale_addresses,
            token_symbol=token_symbol,
            token_address=token_address,
            check_activity=check_activity
        )

        # Шаг 3: Вывод результатов
        print(f"\n✅ ШАГ 3: Анализ завершен")
        print(f"   Проанализировано: {len(whale_addresses)} адресов")
        print(f"   Прошли фильтры: {len(whales)} китов")

        return whales

    async def discover_from_preset(
        self,
        preset_name: str,
        min_balance_usd: float = 100000,
        limit: int = 50,
        check_activity: bool = True
    ) -> List[WhaleInfo]:
        """
        Поиск китов для известного токена (пресет).

        Args:
            preset_name: Имя пресета (UNI, LINK, AAVE, etc.)
            min_balance_usd: Минимальный баланс
            limit: Количество holders
            check_activity: Проверять активность

        Returns:
            List of WhaleInfo objects
        """
        if preset_name not in TOKEN_PRESETS:
            print(f"❌ Неизвестный пресет: {preset_name}")
            print(f"\n📋 Доступные пресеты: {', '.join(TOKEN_PRESETS.keys())}")
            return []

        preset = TOKEN_PRESETS[preset_name]

        print(f"\n🎯 Используется пресет: {preset_name} ({preset['name']})")

        return await self.discover_and_analyze(
            token_address=preset['token_address'],
            subgraph_id=preset['subgraph_id'],
            token_symbol=preset_name,
            min_balance_usd=min_balance_usd,
            limit=limit,
            check_activity=check_activity
        )


# =============================================================================
# CLI INTERFACE
# =============================================================================

async def main():
    """Главная функция CLI"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Whale Finder AUTO - Автоматический поиск китов через The Graph'
    )

    # Режим работы
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--preset',
        type=str,
        choices=list(TOKEN_PRESETS.keys()),
        help='Использовать пресет для известного токена'
    )
    mode_group.add_argument(
        '--token-address',
        type=str,
        help='Адрес контракта токена (требуется --subgraph-id)'
    )

    # Дополнительные параметры
    parser.add_argument(
        '--subgraph-id',
        type=str,
        help='The Graph subgraph ID (обязательно с --token-address)'
    )
    parser.add_argument(
        '--token-symbol',
        type=str,
        default='TOKEN',
        help='Символ токена для отображения (default: TOKEN)'
    )
    parser.add_argument(
        '--min-balance',
        type=float,
        default=100000,
        help='Минимальный баланс в USD (default: 100000)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Количество holders для анализа (default: 50)'
    )
    parser.add_argument(
        '--no-activity',
        action='store_true',
        help='Не проверять активность (быстрее, но менее точно)'
    )
    parser.add_argument(
        '--export-json',
        type=str,
        help='Экспортировать результаты в JSON'
    )
    parser.add_argument(
        '--export-env',
        action='store_true',
        help='Показать формат для .env'
    )
    parser.add_argument(
        '--min-score',
        type=float,
        default=60.0,
        help='Минимальный score для экспорта (default: 60)'
    )

    args = parser.parse_args()

    # Проверка параметров
    if args.token_address and not args.subgraph_id:
        print("❌ Ошибка: --token-address требует --subgraph-id")
        return

    # Создание finder
    finder = AutoWhaleFinderIntegrated()

    # Выполнение поиска
    if args.preset:
        # Режим пресета
        whales = await finder.discover_from_preset(
            preset_name=args.preset,
            min_balance_usd=args.min_balance,
            limit=args.limit,
            check_activity=not args.no_activity
        )
    else:
        # Ручной режим
        whales = await finder.discover_and_analyze(
            token_address=args.token_address,
            subgraph_id=args.subgraph_id,
            token_symbol=args.token_symbol,
            min_balance_usd=args.min_balance,
            limit=args.limit,
            check_activity=not args.no_activity
        )

    # Вывод результатов
    finder.whale_finder.print_results(whales)

    # Экспорт
    if args.export_json:
        finder.whale_finder.export_to_json(whales, args.export_json)

    if args.export_env:
        finder.whale_finder.export_to_env_format(whales, min_score=args.min_score)

    print("\n✅ Автоматический поиск завершен!\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Фатальная ошибка: {e}")
        import traceback
        traceback.print_exc()
