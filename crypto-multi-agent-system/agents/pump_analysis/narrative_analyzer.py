"""
Narrative Analyzer - "Умный переводчик" нарративов

Определяет соответствие трендовому нарративу на основе "грязных"
категорий от API, используя словарь синонимов.

Это делает систему устойчивой к изменениям в API CoinGecko.
"""

from typing import List, Optional, Dict
from .pump_models import NarrativeType

# === СЛОВАРЬ СИНОНИМОВ ДЛЯ НАРРАТИВОВ ===
# Ключ: Наш внутренний, стандартизированный тип (Enum)
# Значение: Список возможных строк, которые может вернуть API
NARRATIVE_ALIASES: Dict[NarrativeType, List[str]] = {
    NarrativeType.AI: [
        "ai", 
        "artificial-intelligence",
        "ai-big-data"
    ],
    NarrativeType.LAYER2: [
        "layer-2",
        "l2",
        "layer-2-scaling"
    ],
    NarrativeType.RWA: [
        "rwa",
        "real-world-assets",
        "tokenized-assets"
    ],
    NarrativeType.DEFI: [
        "defi",
        "decentralized-finance"
    ],
    NarrativeType.GAMING: [
        "gaming",
        "gamefi",
        "play-to-earn"
    ]
}

def find_narrative_in_categories(categories: List[str]) -> Optional[NarrativeType]:
    """
    Ищет соответствие трендовому нарративу в списке категорий от API.

    Args:
        categories: Список строк-категорий от CoinGecko API.

    Returns:
        Optional[NarrativeType]: Найденный стандартизированный нарратив или None.
    """
    if not categories:
        return None

    # Приводим все категории от API к нижнему регистру для надежного сравнения
    normalized_categories = {cat.lower() for cat in categories}

    # Итерируемся по нашему словарю синонимов
    for narrative, aliases in NARRATIVE_ALIASES.items():
        # Итерируемся по каждому синониму для данного нарратива
        for alias in aliases:
            # Если находим точное совпадение синонима с одной из категорий,
            # возвращаем НАШ внутренний, стандартизированный тип.
            if alias in normalized_categories:
                return narrative
    
    # Если ничего не найдено
    return None

# === Тестирование "Переводчика" ===
def test_narrative_analyzer():
    print('🧪 ТЕСТ "УМНОГО ПЕРЕВОДЧИКА" НАРРАТИВОВ')
    print("=" * 50)
    
    # Пример 1: Классический случай
    test_case_1 = ["Decentralized Exchange (DEX)", "ai"]
    result_1 = find_narrative_in_categories(test_case_1)
    print(f"Вход: {test_case_1} -> Результат: {result_1.value if result_1 else 'None'}")
    assert result_1 == NarrativeType.AI

    # Пример 2: API вернул длинное название
    test_case_2 = ["Artificial-Intelligence", "Another Category"]
    result_2 = find_narrative_in_categories(test_case_2)
    print(f"Вход: {test_case_2} -> Результат: {result_2.value if result_2 else 'None'}")
    assert result_2 == NarrativeType.AI

    # Пример 3: Ложное срабатывание (проверка на подстроку)
    test_case_3 = ["train-game", "some-other"]
    result_3 = find_narrative_in_categories(test_case_3)
    print(f"Вход: {test_case_3} -> Результат: {result_3.value if result_3 else 'None'}")
    assert result_3 is None

    # Пример 4: Пустой список
    test_case_4 = []
    result_4 = find_narrative_in_categories(test_case_4)
    print(f"Вход: {test_case_4} -> Результат: {result_4.value if result_4 else 'None'}")
    assert result_4 is None
    
    print('🧪 ТЕСТИРОВАНИЕ "УМНОГО ПЕРЕВОДЧИКА" НАРРАТИВОВ')

if __name__ == "__main__":
    test_narrative_analyzer()
