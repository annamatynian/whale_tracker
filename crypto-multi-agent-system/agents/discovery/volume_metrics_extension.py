"""
Volume Metrics Extension - добавляет pairDayData запросы к существующей системе
Минимально инвазивное расширение для получения исторических данных

Author: Phase 1 Volume Acceleration implementation
Version: 1.0
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


def build_token_day_data_query() -> str:
    """
    Построить GraphQL запрос для получения tokenDayData за последние 30 дней.
    
    Returns:
        GraphQL query string для получения дневных данных токена
    """
    return '''
    query GetTokenDayData($tokenId: String!, $startDate: Int!, $first: Int!) {
      tokenDayDatas(
        where: {
          token: $tokenId,
          date_gte: $startDate
        }
        first: $first
        orderBy: date
        orderDirection: desc
      ) {
        date
        dailyVolumeUSD
        totalLiquidityUSD
      }
    }
    '''


def calculate_volume_metrics_from_daily_data(
    token_day_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Рассчитать метрики ускорения объема из дневных данных.
    
    Метрики:
    - avg_volume_last_7_days: средний объем за последние 7 дней
    - avg_volume_last_30_days: средний объем за последние 30 дней  
    - is_accelerating: True если avg_7d > avg_30d * 1.5
    - acceleration_factor: во сколько раз avg_7d больше avg_30d
    - volume_ratio: volume_h24 / liquidity (если данные за последний день есть)
    
    Args:
        pair_day_data: список дневных данных (от новых к старым)
        
    Returns:
        Dict с рассчитанными метриками
    """
    if not token_day_data or len(token_day_data) < 7:
        return {
            'avg_volume_last_7_days': 0.0,
            'avg_volume_last_30_days': 0.0,
            'is_accelerating': False,
            'acceleration_factor': 0.0,
            'volume_ratio': 0.0,
            'volume_ratio_healthy': False,
            'data_points_count': len(token_day_data) if token_day_data else 0,
            'error': 'Insufficient data (need at least 7 days)'
        }
    
    # Сортируем по дате (самые свежие первые)
    sorted_data = sorted(token_day_data, key=lambda x: x['date'], reverse=True)
    
    # Получаем последние 7 дней
    last_7_days = sorted_data[:7]
    volumes_7d = [float(day.get('dailyVolumeUSD', 0)) for day in last_7_days]
    avg_7d = sum(volumes_7d) / len(volumes_7d) if volumes_7d else 0.0
    
    # Получаем последние 30 дней (или сколько есть)
    last_30_days = sorted_data[:min(30, len(sorted_data))]
    volumes_30d = [float(day.get('dailyVolumeUSD', 0)) for day in last_30_days]
    avg_30d = sum(volumes_30d) / len(volumes_30d) if volumes_30d else 0.0
    
    # Рассчитываем acceleration
    acceleration_factor = avg_7d / avg_30d if avg_30d > 0 else 0.0
    is_accelerating = acceleration_factor > 1.5  # Порог 1.5x
    
    # Volume ratio (если есть данные за последний день)
    volume_ratio = 0.0
    volume_ratio_healthy = False
    volume_ratio_overheated = False
    volume_ratio_dead = False
    
    if sorted_data:
        latest_day = sorted_data[0]
        latest_volume = float(latest_day.get('dailyVolumeUSD', 0))
        latest_liquidity = float(latest_day.get('totalLiquidityUSD', 1))  # Избегаем деления на 0
        
        if latest_liquidity > 0:
            volume_ratio = latest_volume / latest_liquidity
            
            # Классификация по "здоровью" ratio
            if volume_ratio < 0.5:
                volume_ratio_dead = True
                volume_ratio_healthy = False
            elif 0.5 <= volume_ratio <= 3.0:
                volume_ratio_healthy = True
                volume_ratio_dead = False
            else:  # ratio > 3.0
                volume_ratio_overheated = True
                volume_ratio_healthy = False
    
    return {
        'avg_volume_last_7_days': avg_7d,
        'avg_volume_last_30_days': avg_30d,
        'is_accelerating': is_accelerating,
        'acceleration_factor': acceleration_factor,
        'volume_ratio': volume_ratio,
        'volume_ratio_healthy': volume_ratio_healthy,
        'volume_ratio_overheated': volume_ratio_overheated,
        'volume_ratio_dead': volume_ratio_dead,
        'data_points_count': len(sorted_data),
        'volumes_7d': volumes_7d,  # Для дебага
        'volumes_30d': volumes_30d  # Для дебага
    }


def apply_volume_filters(metrics: Dict[str, Any]) -> tuple[bool, str]:
    """
    Применить фильтры на основе volume metrics согласно "Liquidity and volume corrected.docx".
    
    Логика "золотой середины" для Volume Ratio:
    - ✅ 0.5 < ratio < 3.0: Здоровая активность (+5 баллов)
    - ⚠️ ratio > 3.0: Перегрев (не штрафуем, но и не добавляем баллы)
    - ❌ ratio < 0.5: Мертвый токен (исключаем)
    
    Args:
        metrics: результат от calculate_volume_metrics_from_daily_data
        
    Returns:
        (should_pass: bool, reason: str)
    """
    # Проверка 0: Недостаточно данных
    if metrics.get('error'):
        return False, f"Insufficient data: {metrics['error']}"
    
    # Проверка 1: Volume ratio < 0.5 → КРИТИЧЕСКИЙ RED FLAG
    if metrics.get('volume_ratio_dead', False):
        return False, f"❌ Dead token (volume ratio {metrics['volume_ratio']:.3f} < 0.5)"
    
    # Проверка 2: Нет ускорения объема → не соответствует стратегии
    if not metrics['is_accelerating']:
        return False, f"No volume acceleration (factor {metrics['acceleration_factor']:.2f}x < 1.5x)"
    
    # Проверка 3: Volume ratio в "золотой середине" → GREEN FLAG
    if metrics.get('volume_ratio_healthy', False):
        return True, f"✅ Healthy activity (acceleration {metrics['acceleration_factor']:.2f}x, ratio {metrics['volume_ratio']:.3f})"
    
    # Проверка 4: Volume ratio > 3.0 → YELLOW FLAG (перегрев, но не отбрасываем)
    if metrics.get('volume_ratio_overheated', False):
        return True, f"⚠️ Overheated (acceleration {metrics['acceleration_factor']:.2f}x, ratio {metrics['volume_ratio']:.3f} > 3.0)"
    
    # Fallback: если ratio == 0 (нет данных по ликвидности), но есть ускорение
    return True, f"Passed filters (acceleration {metrics['acceleration_factor']:.2f}x, ratio data unavailable)"


# === ИНТЕГРАЦИОННЫЕ УТИЛИТЫ ===

def prepare_day_data_variables(token_address: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Подготовить переменные для GraphQL запроса tokenDayData.
    
    Args:
        token_address: адрес токена (lowercase)
        days_back: сколько дней назад запрашивать (по умолчанию 30)
        
    Returns:
        Dict с переменными для GraphQL
    """
    now = datetime.now()
    start_date = now - timedelta(days=days_back)
    start_timestamp = int(start_date.timestamp())
    
    return {
        'tokenId': token_address.lower(),
        'startDate': start_timestamp,
        'first': days_back  # Запросим ровно столько, сколько нужно
    }


# === ТЕСТОВАЯ ФУНКЦИЯ ===

def test_volume_metrics():
    """Тестовая функция для проверки расчета метрик."""
    
    print("=" * 60)
    print("TEST: Volume Metrics Calculation")
    print("=" * 60)
    
    # Тест 1: "Золотая середина" - Здоровый ratio (0.5 < r < 3.0) + Ускорение
    print("\nTest 1: ✅ HEALTHY RATIO (Golden Middle) - Should PASS")
    # Объем 100k, ликвидность 50k → ratio = 2.0 (в золотой середине)
    mock_data_healthy = [
        {'date': 30 - i, 'dailyVolumeUSD': 100000 if i < 7 else 50000, 'totalLiquidityUSD': 50000}
        for i in range(30)
    ]
    
    metrics1 = calculate_volume_metrics_from_daily_data(mock_data_healthy)
    print(f"   avg_7d: ${metrics1['avg_volume_last_7_days']:,.0f}")
    print(f"   avg_30d: ${metrics1['avg_volume_last_30_days']:,.0f}")
    print(f"   acceleration: {metrics1['acceleration_factor']:.2f}x")
    print(f"   is_accelerating: {metrics1['is_accelerating']}")
    print(f"   volume_ratio: {metrics1['volume_ratio']:.3f}")
    print(f"   ratio_healthy: {metrics1['volume_ratio_healthy']}")
    print(f"   ratio_overheated: {metrics1['volume_ratio_overheated']}")
    print(f"   ratio_dead: {metrics1['volume_ratio_dead']}")
    
    passed, reason = apply_volume_filters(metrics1)
    print(f"   Filter result: {'✓ PASS' if passed else '✗ FAIL'}")
    print(f"   Reason: {reason}")
    
    # Тест 2: Перегрев - ratio > 3.0 (проходит с предупреждением)
    print("\nTest 2: ⚠️ OVERHEATED RATIO (ratio > 3.0) - Should PASS with warning")
    # Объем 200k, ликвидность 50k → ratio = 4.0 (перегрев)
    mock_data_overheated = [
        {'date': 30 - i, 'dailyVolumeUSD': 200000 if i < 7 else 100000, 'totalLiquidityUSD': 50000}
        for i in range(30)
    ]
    
    metrics2 = calculate_volume_metrics_from_daily_data(mock_data_overheated)
    print(f"   volume_ratio: {metrics2['volume_ratio']:.3f}")
    print(f"   ratio_healthy: {metrics2['volume_ratio_healthy']}")
    print(f"   ratio_overheated: {metrics2['volume_ratio_overheated']}")
    print(f"   acceleration: {metrics2['acceleration_factor']:.2f}x")
    
    passed, reason = apply_volume_filters(metrics2)
    print(f"   Filter result: {'✓ PASS' if passed else '✗ FAIL'}")
    print(f"   Reason: {reason}")
    
    # Тест 3: Мертвый токен - ratio < 0.5
    print("\nTest 3: ❌ DEAD TOKEN (ratio < 0.5) - Should FAIL")
    # Объем 10k, ликвидность 50k → ratio = 0.2 (мертвый)
    mock_data_dead = [
        {'date': 30 - i, 'dailyVolumeUSD': 10000 if i < 7 else 5000, 'totalLiquidityUSD': 50000}
        for i in range(30)
    ]
    
    metrics3 = calculate_volume_metrics_from_daily_data(mock_data_dead)
    print(f"   volume_ratio: {metrics3['volume_ratio']:.3f}")
    print(f"   ratio_dead: {metrics3['volume_ratio_dead']}")
    print(f"   acceleration: {metrics3['acceleration_factor']:.2f}x")
    
    passed, reason = apply_volume_filters(metrics3)
    print(f"   Filter result: {'✓ PASS' if passed else '✗ FAIL'}")
    print(f"   Reason: {reason}")
    
    # Тест 4: Нет ускорения (но ratio здоровый)
    print("\nTest 4: NO ACCELERATION (healthy ratio but flat volume) - Should FAIL")
    # Объем 50k всегда, ликвидность 50k → ratio = 1.0 (здоровый)
    mock_data_no_accel = [
        {'date': 30 - i, 'dailyVolumeUSD': 50000, 'totalLiquidityUSD': 50000}
        for i in range(30)
    ]
    
    metrics4 = calculate_volume_metrics_from_daily_data(mock_data_no_accel)
    print(f"   volume_ratio: {metrics4['volume_ratio']:.3f}")
    print(f"   ratio_healthy: {metrics4['volume_ratio_healthy']}")
    print(f"   acceleration: {metrics4['acceleration_factor']:.2f}x")
    print(f"   is_accelerating: {metrics4['is_accelerating']}")
    
    passed, reason = apply_volume_filters(metrics4)
    print(f"   Filter result: {'✓ PASS' if passed else '✗ FAIL'}")
    print(f"   Reason: {reason}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Запустить тесты
    test_volume_metrics()
    
    # Показать пример GraphQL запроса
    print("\n" + "=" * 60)
    print("Example GraphQL Query:")
    print("=" * 60)
    print(build_token_day_data_query())
    
    # Показать пример переменных
    print("\n" + "=" * 60)
    print("Example Query Variables:")
    print("=" * 60)
    example_vars = prepare_day_data_variables("0x1234567890abcdef1234567890abcdef12345678")
    print(f"tokenId: {example_vars['tokenId']}")
    print(f"startDate: {example_vars['startDate']}")
    print(f"first: {example_vars['first']}")
