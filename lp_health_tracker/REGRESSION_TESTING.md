# 🧪 Regression Testing Guide

После интеграции Pydantic models необходимо провести регрессионное тестирование.

## ⚠️ Python 3.13 Notice

Если у вас Python 3.13, могут быть проблемы с установкой зависимостей из-за компиляции Rust компонентов.

## 🚀 Быстрый запуск

### Вариант 1: Проверка существующих зависимостей
```bash
# Проверить что уже установлено
python check_deps.py

# Если достаточно - запустить базовые тесты
python regression_test.py
```

### Вариант 2: Умная установка зависимостей  
```bash
# Попробует несколько стратегий установки
python smart_install_deps.py

# После успешной установки
python full_regression_test.py
```

### Вариант 3: Ручная установка
```bash
# Для Python 3.13 - используйте обновленные версии
pip install -r requirements_testing_updated.txt

# Если не работает - установите по одному:
pip install pytest>=8.0.0
pip install pytest-asyncio>=0.24.0  
pip install pydantic>=2.10.0
pip install requests aiohttp python-dotenv
```

## 📋 Что тестируется

### Custom Regression Tests (regression_test.py)
- ✅ Импорт всех модулей
- ✅ Создание Pydantic моделей  
- ✅ Валидация данных
- ✅ PositionManager функциональность
- ✅ Совместимость с существующими данными

### Pytest Test Suite (full_regression_test.py)
- ✅ Unit тесты (математика IL, расчеты)
- ✅ Integration тесты (компоненты)
- ✅ Regression тесты (фиксы багов)

## 🎯 Recommended Testing Order

1. **python check_deps.py** - проверить что доступно
2. **python regression_test.py** - базовые Pydantic тесты  
3. **python smart_install_deps.py** - установить недостающее
4. **python full_regression_test.py** - полное тестирование

## ⚠️ Troubleshooting

### "pydantic-core compilation failed" (Python 3.13)
```bash
# Solution 1: Use updated versions
python smart_install_deps.py

# Solution 2: Install Rust
# https://rustup.rs/

# Solution 3: Use Python 3.11/3.12
```

### "pytest-asyncio missing"
```bash
pip install pytest-asyncio>=0.24.0
```

### "Module not found"
Убедитесь, что вы в правильной директории:
```bash
cd C:\Users\annam\Documents\DeFi-RAG-Project\lp_health_tracker
python check_deps.py
```

### "Validation errors"  
Проверьте, что в data/positions.json используются валидные Ethereum адреса (42 символа, начинающиеся с 0x).

## 📊 Expected Results

✅ **Success**: Все тесты проходят - можно продолжать разработку
❌ **Failure**: Есть регрессии - нужно исправить перед продолжением

## 🔧 Files Created

- `check_deps.py` - проверка существующих зависимостей
- `smart_install_deps.py` - умная установка с несколькими стратегиями  
- `requirements_testing_updated.txt` - обновленные версии для Python 3.13
- `regression_test.py` - основные тесты Pydantic интеграции
- `full_regression_test.py` - полное тестирование
