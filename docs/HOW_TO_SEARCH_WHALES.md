Критерии отбора "китов" (по приоритету)

1. Размер капитала + тип кошелька

Базовый фильтр:

python

whale_criteria = {

'min_token_balance': '0.1%_of_total_supply',  # Минимум 0.1% от общего предложения

'min_usd_value': 100000,  # Минимум $100k

'wallet_type': 'private',  # Исключаем биржи

'exclude_types': ['exchange', 'bridge', 'dead_wallet']

}

Где искать:

Etherscan → Holders tab → сортировка по балансу

DeFiLlama → Token page → Top holders

Dune Analytics → готовые дашборды по holders

2. Активность и паттерны поведения

Качественные фильтры:

python

activity_filters = {

'recent_activity': 'last_30_days',        # Активность за месяц

'transaction_frequency': 'weekly_or_more', # Регулярные операции

'transaction_variety': 'not_just_receives', # Не только получает

'outbound_destinations': 'to_known_addresses' # Переводит на известные адреса

}

Конкретные паттерны из видео:

Foundation wallets - линейный unlock schedule

VC/Fund wallets - крупные переводы в определенные периоды

Team wallets - активность вокруг важных событий (листинги, обновления)

3. Предсказуемость поведения

Самый важный критерий:

python

predictability_score = {

'unlock_schedule': 'known',      # Известный график разблокировки

'historical_pattern': 'consistent', # Последовательное поведение

'destination_preference': 'same_exchanges', # Предпочитает те же биржи

'timing_pattern': 'after_events'  # Активность после событий

}

🔍 Практический алгоритм поиска

Шаг 1: Найти топ-100 holders

Для начала - возьмите любой крупный токен (ETH, LINK, UNI):

python

# Пример поиска через Etherscan API

async def find_top_holders(token_address, limit=100):

# Получаем топ holders

holders = await etherscan_api.get_token_holders(token_address)

# Фильтруем по размеру

significant_holders = [

h for h in holders

if h['balance_usd'] > 100000 and h['balance_percentage'] > 0.1

]

return significant_holders

Шаг 2: Исключить очевидные "плохие" адреса

Черный список (всегда исключаем):

python

exclude_patterns = {

'known_exchanges': [

'0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE',  # Binance

'0x28C6c06298d514Db089934071355E5743bf21d60',  # Binance 2

# ... другие биржи

],

'known_bridges': [

'0x8484Ef722627bf18ca5Ae6BcF031c23E6e922B30',  # Arbitrum Bridge

# ... другие мосты

],

'dead_wallets': [

'0x000000000000000000000000000000000000dEaD'  # Burn address

]

}

Шаг 3: Проверить активность за последний месяц

python

async def check_whale_activity(address):

transactions = await get_recent_transactions(address, days=30)

activity_score = {

'tx_count': len(transactions),

'outbound_count': len([tx for tx in transactions if tx['from'] == address]),

'large_moves': len([tx for tx in transactions if tx['value_usd'] > 50000]),

'unique_destinations': len(set([tx['to'] for tx in transactions]))

}

# Хороший кит: 5+ транзакций, есть исходящие, есть крупные переводы

is_good_whale = (

activity_score['tx_count'] >= 5 and

activity_score['outbound_count'] >= 2 and

activity_score['large_moves'] >= 1

)

return is_good_whale, activity_score

📊 Конкретные примеры "хороших китов"

Foundation/Team wallets:

Признаки:

Регулярные исходящие транзакции (unlock schedule)

Переводы на одни и те же адреса

Активность вокруг определенных дат

Пример поиска:

python

# Ищем адреса с patterns как в видео

foundation_patterns = {

'regular_outflows': True,        # Регулярные исходящие

'same_amounts': True,           # Примерно одинаковые суммы

'monthly_frequency': True,      # Ежемесячные операции

'to_known_exchanges': True      # На известные биржи

}

VC/Fund wallets:

Признаки:

Крупные единоразовые переводы

Активность после unlock dates

Переводы на OTC/institutional адреса

Insider trading wallets:

Признаки:

Активность перед анонсами

Необычные паттерны накопления

Связь с team/advisor адресами

🛠️ Минимальный стартовый набор

Для начала - возьмите 5-10 адресов:

Критерии для первого списка:

Размер: >$500k в одном токене

Активность: 10+ транзакций за месяц

Известность: Есть информация о принадлежности (team/VC)

Паттерн: Уже видели переводы на биржи

Пример стартового списка (гипотетический):

json

{

"whales_to_monitor": [

{

"address": "0x123...",

"label": "Optimism Foundation Unlock",

"token": "OP",

"balance_usd": 2500000,

"pattern": "monthly_unlock_to_coinbase",

"confidence": "high"

},

{

"address": "0x456...",

"label": "Large Uniswap Holder",

"token": "UNI",

"balance_usd": 1200000,

"pattern": "irregular_large_moves",

"confidence": "medium"

}

]

}

✅ Как проверить качество выбранных китов

Backtest на исторических данных:

python

def validate_whale_quality(whale_address, token_symbol):

# Берем последние 6 месяцев транзакций

historical_txs = get_historical_transactions(whale_address, months=6)

dump_predictions = []

for tx in historical_txs:

if tx['to'] in known_exchange_addresses:

# Проверяем изменение цены после транзакции

price_change = get_price_change_after_tx(token_symbol, tx['timestamp'])

dump_predictions.append({

'predicted_dump': True,

'actual_price_change': price_change,

'correct_prediction': price_change < -2  # 2%+ падение

})

# Считаем точность предсказаний

accuracy = sum(p['correct_prediction'] for p in dump_predictions) / len(dump_predictions)

return accuracy > 0.6  # 60%+ точность = хороший кит

🎯 Практические первые шаги

На эту неделю:

Выберите 1 токен (например, UNI или LINK)

Найдите топ-20 holders через Etherscan

Исключите биржи (очевидные адреса)

Проверьте активность 5-10 адресов за месяц

Выберите 2-3 самых активных для первого теста

Результат: У вас будет мини-список для начала мониторинга без сложной автоматизации.
