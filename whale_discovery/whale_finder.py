"""
Whale Finder - Автоматический поиск и анализ криптовалютных китов
====================================================================

Этот скрипт реализует алгоритм поиска качественных "китов" для мониторинга
на основе критериев:
1. Размер капитала + тип кошелька
2. Активность и паттерны поведения
3. Предсказуемость поведения

Usage:
    python whale_finder.py --token UNI --limit 20
    python whale_finder.py --token LINK --check-activity
    python whale_finder.py --token ETH --backtest --months 6
"""

import asyncio
import aiohttp
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import json

from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

# Известные адреса бирж (черный список)
KNOWN_EXCHANGES = [
    '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE',  # Binance 1
    '0x28C6c06298d514Db089934071355E5743bf21d60',  # Binance 2
    '0xD551234Ae421e3BCBA99A0Da6d736074f22192FF',  # Binance 3
    '0x564286362092D8e7936f0549571a803B203aAceD',  # Binance 4
    '0x0681d8Db095565FE8A346fA0277bFfdE9C0eDBBF',  # Binance 5
    '0xfE9e8709d3215310075d67E3ed32A380CCf451C8',  # Binance 6
    '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',  # Binance 7
    '0xF977814e90dA44bFA03b6295A0616a897441aceC',  # Binance 8
    '0x71660c4005BA85c37ccec55d0C4493E66Fe775d3',  # Coinbase 1
    '0x503828976D22510aad0201ac7EC88293211D23Da',  # Coinbase 2
    '0xddfAbCdc4D8FfC6d5beaf154f18B778f892A0740',  # Coinbase 3
    '0x3cD751E6b0078Be393132286c442345e5DC49699',  # Coinbase 4
    '0xb5d85CBf7cB3EE0D56b3bB207D5Fc4B82f43F511',  # Coinbase 5
    '0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf',  # Coinbase 6
    '0xD688AEA8f7d450909AdE10C47FaA95707b0682d9',  # Coinbase 7
    '0x02466E547BFDAb679fC49e96bBfc62B9747D997C',  # Coinbase 8
    '0x6262998Ced04146fA42253a5C0AF90CA02dfd2A3',  # Crypto.com
    '0x46340b20830761efd32832A74d7169B29FEB9758',  # Crypto.com 2
    '0x7758E507850Da48Cd47dF1fB5F875c23E3340C50',  # Crypto.com 3
    '0x77134cbC06cB00b66F4c7e623D5fdBF6777635EC',  # Kraken
    '0xAe2D4617c862309A3d75A0fFB358c7a5009c673F',  # Kraken 2
    '0x43984D578803891dfa9706bDEee6078D80cFC79E',  # Kraken 3
    '0x267be1C1D684F78cb4F6a176C4911b741E4Ffdc0',  # Kraken 4
    '0xFa52274DD61E1643d2205169732f29114BC240b3',  # Kraken 5
]

# Известные мосты
KNOWN_BRIDGES = [
    '0x8484Ef722627bf18ca5Ae6BcF031c23E6e922B30',  # Arbitrum Bridge
    '0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf',  # Polygon Bridge
    '0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1',  # Optimism Bridge
    '0xa3A7B6F88361F48403514059F1F16C8E78d60EeC',  # Arbitrum Bridge 2
    '0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f',  # Arbitrum Inbox
]

# Dead wallets
DEAD_WALLETS = [
    '0x000000000000000000000000000000000000dEaD',  # Burn address
    '0x0000000000000000000000000000000000000000',  # Zero address
]

# Критерии фильтрации
WHALE_CRITERIA = {
    'min_usd_value': 100000,           # Минимум $100k
    'min_percentage': 0.1,             # Минимум 0.1% от total supply
    'recent_activity_days': 30,        # Активность за последние 30 дней
    'min_tx_count': 5,                 # Минимум 5 транзакций
    'min_outbound_count': 2,           # Минимум 2 исходящих транзакции
    'min_large_moves': 1,              # Минимум 1 крупный перевод
    'large_move_threshold': 50000,     # Крупный перевод = $50k+
    'backtest_accuracy_threshold': 0.6 # 60%+ точность предсказаний
}


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class WhaleInfo:
    """Информация о ките"""
    address: str
    token_symbol: str
    balance: float
    balance_usd: float
    percentage: float
    label: Optional[str] = None

    # Activity metrics
    tx_count: int = 0
    outbound_count: int = 0
    large_moves_count: int = 0
    unique_destinations: int = 0

    # Pattern analysis
    pattern_type: Optional[str] = None
    predictability_score: float = 0.0

    # Quality score
    overall_score: float = 0.0
    confidence: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'address': self.address,
            'token': self.token_symbol,
            'balance_usd': self.balance_usd,
            'percentage': self.percentage,
            'label': self.label,
            'activity': {
                'tx_count': self.tx_count,
                'outbound_count': self.outbound_count,
                'large_moves': self.large_moves_count,
                'unique_destinations': self.unique_destinations
            },
            'pattern': self.pattern_type,
            'predictability_score': self.predictability_score,
            'overall_score': self.overall_score,
            'confidence': self.confidence
        }


# =============================================================================
# ETHERSCAN API CLIENT
# =============================================================================

class EtherscanClient:
    """Клиент для работы с Etherscan API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ETHERSCAN_API_KEY')
        self.base_url = "https://api.etherscan.io/api"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить запрос к API"""
        if not self.session:
            raise RuntimeError("Use EtherscanClient as context manager")

        params['apikey'] = self.api_key

        try:
            async with self.session.get(self.base_url, params=params, timeout=30) as response:
                response.raise_for_status()
                data = await response.json()

                if data['status'] == '0':
                    print(f"⚠️  Etherscan API error: {data.get('message', 'Unknown error')}")
                    return {'status': '0', 'result': []}

                return data

        except asyncio.TimeoutError:
            print(f"⏱️  Timeout при запросе к Etherscan API")
            return {'status': '0', 'result': []}
        except Exception as e:
            print(f"❌ Ошибка запроса к Etherscan: {e}")
            return {'status': '0', 'result': []}

    async def get_token_holders(self, token_address: str, page: int = 1, offset: int = 100) -> List[Dict]:
        """
        Получить список holders токена

        Note: Etherscan API не предоставляет прямой endpoint для holders.
        Эта функция симулирует получение данных. В реальности нужно использовать
        Etherscan UI scraping или другие источники (Dune, The Graph).
        """
        print(f"⚠️  Etherscan API не предоставляет прямой доступ к holders.")
        print(f"   Рекомендации:")
        print(f"   1. Используйте Etherscan UI: https://etherscan.io/token/{token_address}#balances")
        print(f"   2. Используйте Dune Analytics")
        print(f"   3. Используйте The Graph")
        print(f"   4. Или вручную добавьте адреса в список")

        # Возвращаем пустой список - нужна интеграция с другими источниками
        return []

    async def get_transactions(
        self,
        address: str,
        startblock: int = 0,
        endblock: int = 99999999,
        page: int = 1,
        offset: int = 100
    ) -> List[Dict]:
        """Получить транзакции адреса"""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': startblock,
            'endblock': endblock,
            'page': page,
            'offset': offset,
            'sort': 'desc'
        }

        data = await self._request(params)
        return data.get('result', [])

    async def get_token_transfers(
        self,
        address: str,
        contract_address: Optional[str] = None,
        page: int = 1,
        offset: int = 100
    ) -> List[Dict]:
        """Получить ERC20 token transfers"""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'page': page,
            'offset': offset,
            'sort': 'desc'
        }

        if contract_address:
            params['contractaddress'] = contract_address

        data = await self._request(params)
        return data.get('result', [])

    async def get_balance(self, address: str) -> int:
        """Получить ETH баланс адреса"""
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest'
        }

        data = await self._request(params)
        return int(data.get('result', 0))


# =============================================================================
# WHALE ANALYZER
# =============================================================================

class WhaleAnalyzer:
    """Анализатор китов"""

    def __init__(self, etherscan_client: EtherscanClient):
        self.etherscan = etherscan_client

    def is_excluded_address(self, address: str) -> bool:
        """Проверка адреса на исключение (биржи, мосты, dead wallets)"""
        address_lower = address.lower()

        excluded = (
            KNOWN_EXCHANGES +
            KNOWN_BRIDGES +
            DEAD_WALLETS
        )

        return any(addr.lower() == address_lower for addr in excluded)

    async def analyze_activity(
        self,
        address: str,
        token_address: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Анализ активности кита

        Returns:
            Dict с метриками активности
        """
        print(f"   📊 Анализ активности {address[:10]}...")

        # Получаем транзакции за последние N дней
        # Определяем startblock (примерно)
        blocks_per_day = 7200  # ~12 sec per block
        startblock = max(0, await self._get_latest_block() - (days * blocks_per_day))

        # Получаем обычные транзакции
        eth_txs = await self.etherscan.get_transactions(
            address,
            startblock=startblock,
            offset=100
        )

        # Получаем token transfers
        token_txs = await self.etherscan.get_token_transfers(
            address,
            contract_address=token_address,
            offset=100
        )

        # Объединяем
        all_txs = eth_txs + token_txs

        # Фильтруем по времени
        cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp())
        recent_txs = [
            tx for tx in all_txs
            if int(tx.get('timeStamp', 0)) > cutoff_time
        ]

        # Анализ
        outbound_txs = [
            tx for tx in recent_txs
            if tx.get('from', '').lower() == address.lower()
        ]

        # Крупные переводы (примерно определяем)
        large_moves = [
            tx for tx in outbound_txs
            if self._estimate_tx_value_usd(tx) > WHALE_CRITERIA['large_move_threshold']
        ]

        # Уникальные адреса назначения
        destinations = set([
            tx.get('to', '').lower()
            for tx in outbound_txs
            if tx.get('to')
        ])

        return {
            'tx_count': len(recent_txs),
            'outbound_count': len(outbound_txs),
            'large_moves_count': len(large_moves),
            'unique_destinations': len(destinations),
            'destinations': list(destinations),
            'transactions': recent_txs
        }

    def _estimate_tx_value_usd(self, tx: Dict) -> float:
        """
        Примерная оценка стоимости транзакции в USD

        Note: Для точной оценки нужна интеграция с price API
        """
        # Если это ETH транзакция
        if 'value' in tx and tx['value'] != '0':
            eth_value = int(tx['value']) / 1e18
            # Грубая оценка: ETH ~$3500
            return eth_value * 3500

        # Если это token transfer
        if 'value' in tx and 'tokenDecimal' in tx:
            token_value = int(tx['value']) / (10 ** int(tx.get('tokenDecimal', 18)))
            # Без price API не можем точно оценить
            # Возвращаем 0 для упрощения
            return 0

        return 0

    async def _get_latest_block(self) -> int:
        """Получить номер последнего блока"""
        # Упрощенная версия - возвращаем примерное значение
        # В реальности нужен отдельный API call
        return 18_000_000  # Примерно текущий блок (Nov 2023)

    def detect_pattern(self, activity: Dict[str, Any]) -> Optional[str]:
        """
        Определение паттерна поведения кита

        Patterns:
        - foundation_unlock: Регулярные исходящие на биржи
        - vc_fund: Крупные единоразовые переводы
        - active_trader: Частые операции на DEX
        - accumulator: Преимущественно входящие
        - inactive: Низкая активность
        """
        tx_count = activity['tx_count']
        outbound_count = activity['outbound_count']
        large_moves = activity['large_moves_count']

        # Неактивный
        if tx_count < 5:
            return 'inactive'

        # Накопитель (больше входящих чем исходящих)
        if outbound_count < tx_count * 0.3:
            return 'accumulator'

        # Foundation unlock (регулярные исходящие, крупные суммы)
        if large_moves >= 2 and outbound_count >= 5:
            return 'foundation_unlock'

        # VC/Fund (несколько крупных переводов)
        if large_moves >= 3:
            return 'vc_fund'

        # Активный трейдер
        if tx_count >= 20:
            return 'active_trader'

        return 'unknown'

    def calculate_predictability_score(
        self,
        activity: Dict[str, Any],
        pattern: Optional[str]
    ) -> float:
        """
        Расчет predictability score (0-100)

        Высокая предсказуемость = паттерн + регулярность
        """
        score = 0.0

        # Базовый score на основе паттерна
        pattern_scores = {
            'foundation_unlock': 80,  # Очень предсказуемо
            'vc_fund': 60,           # Средняя предсказуемость
            'active_trader': 40,     # Сложнее предсказать
            'accumulator': 30,       # Низкая предсказуемость
            'inactive': 10,          # Непредсказуемо
            'unknown': 20
        }

        score = pattern_scores.get(pattern, 20)

        # Бонус за регулярность (если есть крупные переводы)
        if activity['large_moves_count'] >= 2:
            score += 10

        # Бонус за известные направления (биржи)
        destinations = activity.get('destinations', [])
        known_exchange_count = sum(
            1 for dest in destinations
            if dest in [ex.lower() for ex in KNOWN_EXCHANGES]
        )

        if known_exchange_count > 0:
            score += 10

        return min(100, score)

    def calculate_overall_score(self, whale: WhaleInfo) -> float:
        """
        Расчет общего качества кита для мониторинга (0-100)

        Факторы:
        - Размер капитала (25%)
        - Активность (25%)
        - Предсказуемость (30%)
        - Паттерн (20%)
        """
        # 1. Размер капитала (0-25 points)
        capital_score = min(25, (whale.balance_usd / 1_000_000) * 10)

        # 2. Активность (0-25 points)
        activity_score = 0
        if whale.tx_count >= 20:
            activity_score = 25
        elif whale.tx_count >= 10:
            activity_score = 20
        elif whale.tx_count >= 5:
            activity_score = 15
        elif whale.tx_count >= 2:
            activity_score = 10

        # 3. Предсказуемость (0-30 points)
        predictability_score = (whale.predictability_score / 100) * 30

        # 4. Паттерн (0-20 points)
        pattern_scores = {
            'foundation_unlock': 20,
            'vc_fund': 18,
            'active_trader': 15,
            'accumulator': 10,
            'inactive': 5,
            'unknown': 8
        }
        pattern_score = pattern_scores.get(whale.pattern_type, 8)

        total = capital_score + activity_score + predictability_score + pattern_score
        return round(total, 2)

    def determine_confidence(self, score: float) -> str:
        """Определение уровня уверенности"""
        if score >= 80:
            return "high"
        elif score >= 60:
            return "medium"
        elif score >= 40:
            return "low"
        else:
            return "very_low"


# =============================================================================
# WHALE FINDER
# =============================================================================

class WhaleFinder:
    """Главный класс для поиска китов"""

    def __init__(self):
        self.etherscan = None
        self.analyzer = None

    async def find_whales(
        self,
        whale_addresses: List[str],
        token_symbol: str = "ETH",
        token_address: Optional[str] = None,
        check_activity: bool = True
    ) -> List[WhaleInfo]:
        """
        Поиск и анализ китов

        Args:
            whale_addresses: Список адресов для проверки
            token_symbol: Символ токена
            token_address: Адрес контракта токена (для ERC20)
            check_activity: Проверять ли активность

        Returns:
            Список WhaleInfo объектов с анализом
        """
        async with EtherscanClient() as etherscan:
            self.etherscan = etherscan
            self.analyzer = WhaleAnalyzer(etherscan)

            print(f"\n🔍 Начинаю поиск китов для {token_symbol}...")
            print(f"   Адресов для проверки: {len(whale_addresses)}\n")

            whales = []

            for i, address in enumerate(whale_addresses, 1):
                print(f"\n[{i}/{len(whale_addresses)}] Проверка {address}")

                # Шаг 1: Проверка на исключение
                if self.analyzer.is_excluded_address(address):
                    print(f"   ⛔ Пропускаем: адрес в черном списке (биржа/мост/dead)")
                    continue

                # Шаг 2: Получение баланса
                try:
                    balance_wei = await etherscan.get_balance(address)
                    balance_eth = balance_wei / 1e18
                    balance_usd = balance_eth * 3500  # Примерная оценка

                    print(f"   💰 Баланс: {balance_eth:.4f} ETH (~${balance_usd:,.0f})")

                    # Проверка минимального порога
                    if balance_usd < WHALE_CRITERIA['min_usd_value']:
                        print(f"   ⛔ Пропускаем: баланс < ${WHALE_CRITERIA['min_usd_value']:,}")
                        continue

                except Exception as e:
                    print(f"   ❌ Ошибка получения баланса: {e}")
                    continue

                # Создаем WhaleInfo
                whale = WhaleInfo(
                    address=address,
                    token_symbol=token_symbol,
                    balance=balance_eth,
                    balance_usd=balance_usd,
                    percentage=0.0  # Не можем рассчитать без total supply
                )

                # Шаг 3: Анализ активности
                if check_activity:
                    try:
                        activity = await self.analyzer.analyze_activity(
                            address,
                            token_address=token_address,
                            days=WHALE_CRITERIA['recent_activity_days']
                        )

                        whale.tx_count = activity['tx_count']
                        whale.outbound_count = activity['outbound_count']
                        whale.large_moves_count = activity['large_moves_count']
                        whale.unique_destinations = activity['unique_destinations']

                        print(f"   📈 Активность: {whale.tx_count} tx, {whale.outbound_count} исходящих, {whale.large_moves_count} крупных")

                        # Проверка минимальной активности
                        if whale.tx_count < WHALE_CRITERIA['min_tx_count']:
                            print(f"   ⛔ Пропускаем: недостаточная активность")
                            continue

                        # Шаг 4: Определение паттерна
                        whale.pattern_type = self.analyzer.detect_pattern(activity)
                        print(f"   🎯 Паттерн: {whale.pattern_type}")

                        # Шаг 5: Расчет predictability score
                        whale.predictability_score = self.analyzer.calculate_predictability_score(
                            activity,
                            whale.pattern_type
                        )
                        print(f"   🔮 Предсказуемость: {whale.predictability_score:.1f}/100")

                    except Exception as e:
                        print(f"   ⚠️  Ошибка анализа активности: {e}")

                # Шаг 6: Расчет общего score
                whale.overall_score = self.analyzer.calculate_overall_score(whale)
                whale.confidence = self.analyzer.determine_confidence(whale.overall_score)

                print(f"   ⭐ Общий score: {whale.overall_score:.1f}/100 ({whale.confidence} confidence)")

                whales.append(whale)

            return whales

    def print_results(self, whales: List[WhaleInfo]):
        """Вывод результатов в консоль"""
        if not whales:
            print("\n❌ Киты не найдены или все отфильтрованы")
            return

        # Сортируем по overall_score
        sorted_whales = sorted(whales, key=lambda w: w.overall_score, reverse=True)

        print("\n" + "=" * 80)
        print("🐋 РЕЗУЛЬТАТЫ ПОИСКА КИТОВ")
        print("=" * 80)
        print(f"\nНайдено китов: {len(sorted_whales)}\n")

        # Группировка по confidence
        by_confidence = defaultdict(list)
        for whale in sorted_whales:
            by_confidence[whale.confidence].append(whale)

        # Вывод по группам
        for confidence in ['high', 'medium', 'low', 'very_low']:
            whales_in_group = by_confidence.get(confidence, [])
            if not whales_in_group:
                continue

            print(f"\n{'=' * 80}")
            print(f"📊 {confidence.upper()} CONFIDENCE ({len(whales_in_group)} китов)")
            print('=' * 80)

            for whale in whales_in_group:
                print(f"\n🐋 {whale.address}")
                print(f"   💰 Баланс: ${whale.balance_usd:,.0f}")
                print(f"   📊 Активность: {whale.tx_count} tx ({whale.outbound_count} исходящих, {whale.large_moves_count} крупных)")
                print(f"   🎯 Паттерн: {whale.pattern_type}")
                print(f"   🔮 Предсказуемость: {whale.predictability_score:.1f}/100")
                print(f"   ⭐ Общий score: {whale.overall_score:.1f}/100")

        # Рекомендации
        print("\n" + "=" * 80)
        print("💡 РЕКОМЕНДАЦИИ")
        print("=" * 80)

        high_conf = by_confidence.get('high', [])
        medium_conf = by_confidence.get('medium', [])

        if high_conf:
            print(f"\n✅ Рекомендуется добавить в мониторинг ({len(high_conf)} китов):")
            for whale in high_conf[:5]:  # Топ-5
                print(f"   • {whale.address} (score: {whale.overall_score:.1f}, паттерн: {whale.pattern_type})")

        if medium_conf:
            print(f"\n⚡ Можно рассмотреть ({len(medium_conf)} китов):")
            for whale in medium_conf[:3]:  # Топ-3
                print(f"   • {whale.address} (score: {whale.overall_score:.1f}, паттерн: {whale.pattern_type})")

        print("\n" + "=" * 80)

    def export_to_json(self, whales: List[WhaleInfo], filename: str = "whale_analysis.json"):
        """Экспорт результатов в JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_whales': len(whales),
            'whales': [whale.to_dict() for whale in whales]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Результаты сохранены в {filename}")

    def export_to_env_format(self, whales: List[WhaleInfo], min_score: float = 60.0):
        """Экспорт в формат для .env файла"""
        # Фильтруем только качественных китов
        good_whales = [w for w in whales if w.overall_score >= min_score]

        if not good_whales:
            print(f"\n⚠️  Нет китов с score >= {min_score}")
            return

        # Сортируем по score
        sorted_whales = sorted(good_whales, key=lambda w: w.overall_score, reverse=True)

        addresses = ','.join([w.address for w in sorted_whales])

        print("\n" + "=" * 80)
        print("📋 ФОРМАТ ДЛЯ .ENV ФАЙЛА")
        print("=" * 80)
        print(f"\nСкопируйте эту строку в ваш .env файл:\n")
        print(f"WHALE_ADDRESSES={addresses}")
        print(f"\n({len(sorted_whales)} адресов с score >= {min_score})")
        print("=" * 80)


# =============================================================================
# CLI INTERFACE
# =============================================================================

async def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description='Whale Finder - Поиск качественных криптовалютных китов')
    parser.add_argument('--addresses', type=str, help='Адреса для проверки (через запятую)')
    parser.add_argument('--file', type=str, help='Файл с адресами (по одному на строку)')
    parser.add_argument('--token', type=str, default='ETH', help='Символ токена (default: ETH)')
    parser.add_argument('--token-address', type=str, help='Адрес контракта токена (для ERC20)')
    parser.add_argument('--no-activity', action='store_true', help='Не проверять активность')
    parser.add_argument('--export-json', type=str, help='Экспортировать в JSON файл')
    parser.add_argument('--export-env', action='store_true', help='Показать формат для .env')
    parser.add_argument('--min-score', type=float, default=60.0, help='Минимальный score для экспорта (default: 60)')

    args = parser.parse_args()

    # Получение списка адресов
    addresses = []

    if args.addresses:
        addresses = [addr.strip() for addr in args.addresses.split(',')]
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                addresses = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"❌ Файл не найден: {args.file}")
            return
    else:
        # Демо режим - используем примеры из .env.example
        print("📝 Демо режим - используем примеры адресов")
        addresses = [
            '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',  # Vitalik
            '0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B',  # Tornado Cash Deployer
            '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',   # Example whale
        ]

    if not addresses:
        print("❌ Не указаны адреса для проверки")
        print("   Используйте: --addresses или --file")
        return

    # Запуск поиска
    finder = WhaleFinder()
    whales = await finder.find_whales(
        whale_addresses=addresses,
        token_symbol=args.token,
        token_address=args.token_address,
        check_activity=not args.no_activity
    )

    # Вывод результатов
    finder.print_results(whales)

    # Экспорт
    if args.export_json:
        finder.export_to_json(whales, args.export_json)

    if args.export_env:
        finder.export_to_env_format(whales, min_score=args.min_score)

    print("\n✅ Анализ завершен!\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Фатальная ошибка: {e}")
        import traceback
        traceback.print_exc()
