# 🧪 Testing Roadmap для LP Health Tracker

## 🎯 **MVP Тесты (Week 1) - ПРИОРИТЕТ**

**Цель:** Покрыть критические риски за минимальное время

### ✅ **Тест 1: Основной расчет IL**
```python
def test_il_calculation_basic():
    """Цена удвоилась → IL = -5.72%"""
    il = calculate_impermanent_loss(1.0, 2.0) 
    assert abs(il - (-0.0572)) < 0.001
```

### ✅ **Тест 2: Защита от деления на ноль**
```python
def test_zero_division_protection():
    """total_supply = 0 не должно крашить систему"""
    result = calculate_lp_position_value(lp_tokens=10, total_supply=0, ...)
    assert result['total_value_usd'] == 0.0
```

### ✅ **Тест 3: Пороги алертов**
```python
def test_alert_threshold_basic():
    """IL -6% при пороге 5% → алерт должен сработать"""
    should_alert = check_il_threshold(current_il=-0.06, threshold=0.05)
    assert should_alert == True
```

**Время на реализацию:** ~30-45 минут
**Покрытие рисков:** ~80% критических случаев

---

## 🔄 **Расширенные тесты (Phase 2) - БУДУЩЕЕ**

*Источник: предложения от Gemini AI*

### 📊 **Расширение тестов IL calculation:**

```python
def test_il_no_price_change():
    """price_ratio = 1.0 → IL должен быть 0%"""
    il = calculate_impermanent_loss(1.0, 1.0)
    assert il == 0.0

def test_il_price_halved():
    """price_ratio = 0.5 → IL = -5.72% (симметрично удвоению)"""
    il = calculate_impermanent_loss(1.0, 0.5)
    assert abs(il - (-0.0572)) < 0.001

def test_il_price_to_zero():
    """price_ratio = 0.0 → IL = -100%"""
    il = calculate_impermanent_loss(1.0, 0.0) 
    assert abs(il - (-1.0)) < 0.001

def test_il_extreme_price_changes():
    """Очень большие изменения цены"""
    # 10x рост
    il_10x = calculate_impermanent_loss(1.0, 10.0)
    assert il_10x < -0.1  # Больше -10% IL
    
    # 90% падение  
    il_90_drop = calculate_impermanent_loss(1.0, 0.1)
    assert il_90_drop < -0.1
```

### 🛡️ **Расширение edge cases:**

```python
def test_negative_lp_tokens():
    """Отрицательные LP токены → должна быть ошибка валидации"""
    with pytest.raises(ValueError):
        calculate_lp_position_value(lp_tokens=-10, total_supply=1000, ...)

def test_empty_pool_reserves():
    """Резервы пула = 0 → позиция должна быть 0"""
    result = calculate_lp_position_value(
        lp_tokens=10, total_supply=1000,
        reserve_a=0, reserve_b=0, ...
    )
    assert result['total_value_usd'] == 0.0
```

### 🚨 **Расширение alert logic:**

```python
def test_alert_threshold_not_triggered():
    """IL -4% при пороге 5% → алерт НЕ должен сработать"""
    should_alert = check_il_threshold(current_il=-0.04, threshold=0.05)
    assert should_alert == False

def test_alert_threshold_boundary():
    """Пороговое значение: IL -5% при пороге 5%"""
    should_alert = check_il_threshold(current_il=-0.05, threshold=0.05)
    # TODO: Определить поведение - >= или > ?
    # assert should_alert == True  # если >=
    # assert should_alert == False # если >
```

### 📈 **Дополнительные тесты производительности:**

```python
def test_calculation_performance():
    """Расчеты должны выполняться быстро"""
    import time
    
    start = time.time()
    for i in range(1000):
        calculate_impermanent_loss(1.0, 2.0)
    duration = time.time() - start
    
    assert duration < 1.0  # Меньше 1 секунды на 1000 расчетов
```

---

## 📅 **Планирование по фазам:**

### **Phase 1 (MVP)** - Week 1
- [x] 3 базовых теста  
- [x] Настройка pytest
- [x] CI/CD интеграция (опционально)

### **Phase 2 (Extension)** - Month 2-3
- [ ] Расширенные тесты IL (6 дополнительных)
- [ ] Edge cases (4 дополнительных)  
- [ ] Performance тесты
- [ ] Integration тесты с API

### **Phase 3 (Advanced)** - Month 6+
- [ ] Stress тесты
- [ ] Security тесты
- [ ] End-to-end тесты
- [ ] Мониторинг тесты

---

## 🎯 **Критерии готовности:**

### **MVP Ready:**
- ✅ Основные математические расчеты протестированы
- ✅ Критические edge cases покрыты
- ✅ Alert логика проверена
- ✅ CI проходит без ошибок

### **Production Ready:**
- ✅ MVP тесты +
- ✅ Все расширенные тесты Phase 2
- ✅ Test coverage > 85%
- ✅ Performance benchmarks

---

## 💡 **Заметки для команды:**

### **Приоритизация:**
1. **Критично:** Математика (деньги на кону)
2. **Важно:** Edge cases (система не должна крашиться)  
3. **Полезно:** Performance, мониторинг
4. **Nice to have:** UI, логирование

### **Когда переходить к Phase 2:**
- [ ] MVP тесты стабильно проходят 2+ недели
- [ ] Основной функционал работает в production
- [ ] Есть время на расширение (не в спринте)
- [ ] Команда готова поддерживать больше тестов

### **Технические заметки:**
- **pytest-cov** для покрытия кода
- **pytest-benchmark** для performance тестов
- **hypothesis** для property-based тестирования (Phase 3)
- **docker** для изолированного тестирования

---

## 📁 **Организация файлов тестов:**

```
tests/
├── __init__.py                 # Python package
├── conftest.py                 # Общие настройки pytest  
├── test_data_analyzer.py       # ✅ MVP тесты (готово)
├── test_extensions.py          # 🔄 Расширенные тесты (Phase 2)
├── test_integrations.py        # 🔄 API и Web3 тесты (Phase 2)
├── test_performance.py         # 🔄 Performance тесты (Phase 3)
└── fixtures/                   # Тестовые данные
    ├── sample_positions.json
    ├── sample_prices.json
    └── mock_responses.json
```

---

## 🚀 **Быстрый старт для новых тестов:**

### **1. Запуск MVP тестов:**
```bash
# Все MVP тесты
pytest tests/test_data_analyzer.py -v

# Один конкретный тест
pytest tests/test_data_analyzer.py::test_no_price_change_zero_il -v
```

### **2. Добавление нового теста:**
```python
# В test_data_analyzer.py или test_extensions.py
def test_my_new_scenario(self):
    """Описание что тестируем"""
    # Arrange - подготовка данных
    # Act - выполнение функции  
    # Assert - проверка результата
    pass
```

### **3. Запуск с покрытием:**
```bash
pytest tests/ --cov=src --cov-report=html
```

---

*Документ создан: 2025-01-01*
*Версия: 1.0*
*Автор: LP Health Tracker Team*