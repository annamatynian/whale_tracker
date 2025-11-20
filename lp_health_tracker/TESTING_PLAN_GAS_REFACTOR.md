# ПЛАН ТЕСТИРОВАНИЯ - Dependency Injection Рефакторинг

## 🎯 ТЕСТЫ, КОТОРЫЕ НУЖНО ЗАПУСТИТЬ

### **🚨 КРИТИЧЕСКИЕ ТЕСТЫ (обязательные):**

1. **test_dependency_injection.py** 
   ```bash
   python test_dependency_injection.py
   ```
   ✅ Проверяет что dependency injection работает правильно

2. **test_gas_integration.py**
   ```bash
   python test_gas_integration.py
   ```
   ✅ Проверяет интеграцию с main.py

3. **Регрессионные тесты**
   ```bash
   python regression_test.py
   ```
   ✅ Убеждается что основная функциональность не сломана

### **🔧 UNIT ТЕСТЫ:**

4. **Существующие unit тесты для GasCostCalculator**
   ```bash
   pytest tests/unit/test_gas_cost_calculator.py -v
   ```
   ⚠️ Может потребовать обновления для нового API

5. **Быстрые тесты газа**
   ```bash
   pytest tests/unit/test_gas_quick.py -v
   python tests/unit/test_gas_quick.py
   ```

6. **Простые тесты газа**
   ```bash
   pytest tests/unit/test_gas_simple.py -v
   ```

### **🔗 INTEGRATION ТЕСТЫ:**

7. **Интеграционные тесты**
   ```bash
   pytest tests/integration/test_integration_stage1.py -v
   pytest tests/integration/test_integration_stage2.py -v
   ```

8. **YAML совместимость**
   ```bash
   pytest tests/integration/test_yaml_compatibility.py -v
   ```

### **🌐 E2E ТЕСТЫ:**

9. **Основная функциональность**
   ```bash
   pytest tests/e2e/test_core_functionality.py -v
   ```

### **🎬 КОМПЛЕКСНЫЙ ТЕСТ:**

10. **Запустить все сразу**
    ```bash
    python test_comprehensive_gas_refactor.py
    ```
    🏆 Автоматически запускает все тесты и генерирует отчет

## 🔄 ПОРЯДОК ВЫПОЛНЕНИЯ:

### **Вариант 1: Быстрая проверка**
```bash
# 1. Проверить dependency injection
python test_dependency_injection.py

# 2. Проверить интеграцию
python test_gas_integration.py

# 3. Проверить что ничего не сломано
python regression_test.py
```

### **Вариант 2: Полная проверка**
```bash
# Запустить комплексный тест
python test_comprehensive_gas_refactor.py
```

### **Вариант 3: Пошаговая проверка**
```bash
# 1. Dependency injection
python test_dependency_injection.py

# 2. Unit тесты
pytest tests/unit/test_gas_cost_calculator.py -v
pytest tests/unit/test_gas_quick.py -v

# 3. Integration тесты
pytest tests/integration/ -v

# 4. Регрессия
python regression_test.py

# 5. E2E
pytest tests/e2e/ -v
```

## ⚠️ ОЖИДАЕМЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ:

### **Если unit тесты падают:**
- **Причина:** API изменился (eth_price_usd теперь обязательный)
- **Решение:** Обновить тесты, добавив параметр eth_price_usd

### **Если integration тесты падают:**
- **Причина:** main.py изменился
- **Решение:** Проверить что ETH цена правильно передается

### **Если regression тесты падают:**
- **Причина:** Нарушена обратная совместимость
- **Решение:** Проверить что все старые API еще работают

## 🎯 КРИТЕРИИ УСПЕХА:

✅ **Dependency injection тесты PASS**
✅ **Integration тесты PASS**  
✅ **Regression тесты PASS**
✅ **>80% всех тестов PASS**

## 🚀 ЗАПУСК:

```bash
# Быстрая проверка (5 минут)
python test_dependency_injection.py && python test_gas_integration.py && python regression_test.py

# Полная проверка (15-20 минут)
python test_comprehensive_gas_refactor.py
```
