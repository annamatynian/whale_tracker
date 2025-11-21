# 📥 Установка Whale Discovery модуля

Инструкции по получению **только папки whale_discovery** без скачивания всего проекта.

---

## 🎯 Цель

Получить только модуль поиска китов (`whale_discovery/`) на ваш компьютер без необходимости клонировать весь проект Whale Tracker.

---

## ✅ Метод 1: Sparse Checkout (рекомендуется)

Git sparse checkout позволяет скачать только нужную папку.

### Шаг 1: Инициализация репозитория

```bash
# Создайте новую папку для проекта
mkdir whale_tracker
cd whale_tracker

# Инициализируйте git репозиторий
git init

# Добавьте remote
git remote add origin https://github.com/annamatynian/whale_tracker.git
```

### Шаг 2: Настройка Sparse Checkout

```bash
# Включите sparse checkout
git config core.sparseCheckout true

# Укажите какую папку скачать
echo "whale_discovery/*" >> .git/info/sparse-checkout

# Опционально: также скачать .env.example
echo ".env.example" >> .git/info/sparse-checkout
```

### Шаг 3: Получение файлов

```bash
# Получите нужную ветку
git fetch origin claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk

# Checkout на эту ветку
git checkout claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk

# Или просто:
git pull origin claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk
```

### Результат

```
whale_tracker/
├── .git/
├── .env.example          # Если добавили в sparse-checkout
└── whale_discovery/
    ├── README.md
    ├── INSTALL_INSTRUCTIONS.md
    ├── whale_finder.py
    ├── whale_finder_auto.py
    ├── thegraph_holders_client.py
    ├── eth_whale_discovery.py
    ├── example_whale_addresses.txt
    ├── WHALE_FINDER_GUIDE.md
    ├── THEGRAPH_AUTO_DISCOVERY.md
    └── ETH_WHALE_DISCOVERY.md
```

---

## ✅ Метод 2: Прямое скачивание (альтернатива)

Если не хотите использовать git:

### Вариант A: GitHub UI (если репозиторий публичный)

1. Откройте https://github.com/annamatynian/whale_tracker
2. Перейдите в ветку `claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk`
3. Зайдите в папку `whale_discovery/`
4. Нажмите "Download ZIP" или скачайте каждый файл отдельно

### Вариант B: curl/wget (для каждого файла)

```bash
# Создайте папку
mkdir -p whale_discovery
cd whale_discovery

# URL pattern для raw файлов
BASE_URL="https://raw.githubusercontent.com/annamatynian/whale_tracker/claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk/whale_discovery"

# Скачайте каждый файл
curl -O "$BASE_URL/README.md"
curl -O "$BASE_URL/whale_finder.py"
curl -O "$BASE_URL/whale_finder_auto.py"
curl -O "$BASE_URL/thegraph_holders_client.py"
curl -O "$BASE_URL/eth_whale_discovery.py"
curl -O "$BASE_URL/example_whale_addresses.txt"
curl -O "$BASE_URL/WHALE_FINDER_GUIDE.md"
curl -O "$BASE_URL/THEGRAPH_AUTO_DISCOVERY.md"
curl -O "$BASE_URL/ETH_WHALE_DISCOVERY.md"
```

---

## ✅ Метод 3: Клонирование всего репозитория (если нужен весь проект)

Если в итоге вам понадобится весь Whale Tracker:

```bash
# Клонировать репозиторий
git clone https://github.com/annamatynian/whale_tracker.git

# Перейти в папку
cd whale_tracker

# Checkout нужную ветку
git checkout claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk

# Whale Discovery будет в папке whale_discovery/
cd whale_discovery
```

---

## 📋 После установки

### 1. Установите зависимости

```bash
pip install aiohttp python-dotenv
```

### 2. Создайте .env файл

```bash
# Скопируйте пример (если скачали .env.example)
cp .env.example .env

# Или создайте новый
cat > .env <<EOF
# Обязательно
ETHERSCAN_API_KEY=ваш_ключ_здесь

# Опционально
THEGRAPH_API_KEY=
EOF
```

### 3. Получите API ключи

**Etherscan (обязательно):**
1. Откройте https://etherscan.io/apis
2. Зарегистрируйтесь
3. Создайте API key
4. Добавьте в .env: `ETHERSCAN_API_KEY=ваш_ключ`

**The Graph (опционально):**
1. Откройте https://thegraph.com/studio/
2. Подключите кошелек
3. Создайте API key
4. Добавьте в .env: `THEGRAPH_API_KEY=ваш_ключ`

### 4. Тестовый запуск

```bash
# Демо режим (без API ключей)
python whale_discovery/whale_finder.py

# С автопоиском (нужен The Graph key)
python whale_discovery/whale_finder_auto.py --preset UNI --limit 10

# ETH киты
python whale_discovery/eth_whale_discovery.py
```

---

## 🔄 Обновление модуля

Если нужно получить обновления:

### Метод 1 (Sparse Checkout):

```bash
cd whale_tracker
git pull origin claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk
```

### Метод 2 (Прямое скачивание):

Повторите команды curl/wget

---

## 🛠️ Проверка установки

Проверьте что все файлы на месте:

```bash
ls -la whale_discovery/

# Должно быть:
# README.md
# INSTALL_INSTRUCTIONS.md
# whale_finder.py
# whale_finder_auto.py
# thegraph_holders_client.py
# eth_whale_discovery.py
# example_whale_addresses.txt
# WHALE_FINDER_GUIDE.md
# THEGRAPH_AUTO_DISCOVERY.md
# ETH_WHALE_DISCOVERY.md
```

Проверьте что скрипты работают:

```bash
# Проверка синтаксиса
python -m py_compile whale_discovery/whale_finder.py
python -m py_compile whale_discovery/whale_finder_auto.py
python -m py_compile whale_discovery/eth_whale_discovery.py
python -m py_compile whale_discovery/thegraph_holders_client.py

# Если нет ошибок - все ОК!
```

---

## ❓ Troubleshooting

### Ошибка: "fatal: not a git repository"

**Решение:** Вы не в git репозитории. Выполните Шаг 1.

### Ошибка: "couldn't find remote ref"

**Решение:** Неверное имя ветки или репозитория. Проверьте:
```bash
git remote -v
git fetch origin
git branch -r  # Список удаленных веток
```

### Sparse checkout не работает

**Решение:** Используйте Метод 2 (прямое скачивание)

### "Permission denied" при git clone

**Решение:**
1. Проверьте доступ к репозиторию
2. Для приватного репозитория настройте SSH ключи
3. Или используйте HTTPS с токеном

---

## 📞 Дополнительная помощь

**Документация:**
- Sparse Checkout: https://git-scm.com/docs/git-sparse-checkout
- Git Remote: https://git-scm.com/docs/git-remote

**После установки читайте:**
- `whale_discovery/README.md` - Общий обзор
- `whale_discovery/WHALE_FINDER_GUIDE.md` - Подробное руководство

---

## 🎯 Быстрая команда (все в одном)

**Linux/Mac:**

```bash
mkdir -p whale_tracker && cd whale_tracker && \
git init && \
git remote add origin https://github.com/annamatynian/whale_tracker.git && \
git config core.sparseCheckout true && \
echo "whale_discovery/*" >> .git/info/sparse-checkout && \
echo ".env.example" >> .git/info/sparse-checkout && \
git pull origin claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk && \
pip install aiohttp python-dotenv && \
echo "✅ Установка завершена! Папка: $(pwd)/whale_discovery"
```

**Windows (PowerShell):**

```powershell
mkdir whale_tracker; cd whale_tracker
git init
git remote add origin https://github.com/annamatynian/whale_tracker.git
git config core.sparseCheckout true
"whale_discovery/*" | Out-File -Encoding ASCII .git/info/sparse-checkout
".env.example" | Out-File -Encoding ASCII -Append .git/info/sparse-checkout
git pull origin claude/telegram-api-testing-013883JrfLBPpHUWkbYTtAMk
pip install aiohttp python-dotenv
Write-Host "✅ Установка завершена! Папка: $PWD\whale_discovery"
```

---

**Версия:** 1.0
**Дата:** 2025-11-21
**Для:** Whale Tracker Project
