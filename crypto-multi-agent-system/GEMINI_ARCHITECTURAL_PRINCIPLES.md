# 🏛️ Дополнительные архитектурные принципы от Gemini
## Критически важные принципы для профессиональной ML/AI системы

*Данные принципы дополняют основной план проекта и обеспечивают production-ready качество системы*

---

## 🔄 **ПРИНЦИП #7: ВОСПРОИЗВОДИМОСТЬ И ВЕРСИОНИРОВАНИЕ (MLOps)**

### **Суть принципа:**
> *"Любое решение, принятое системой, должно быть полностью воспроизводимым. Мы должны иметь возможность вернуться назад во времени и понять, почему был дан именно такой результат."*

### **Почему это критично:**
✅ **Отладка моделей:** Если модель дала неверный прогноз, нам нужно точно знать, на каких данных и какой версией модели он был сделан.

✅ **Анализ эффективности:** Чтобы понять, почему старая версия модели работала лучше или хуже, нужно уметь воспроизводить ее результаты.

✅ **Аудит и доверие:** Вы должны быть в состоянии доказать (в первую очередь себе), почему система порекомендовала купить тот или иной токен.

✅ **Защита от "сломалось после обновления":** Гарантирует, что вы всегда можете откатиться к предыдущей рабочей версии не только кода, но и моделей/данных.

### **Как применяется в нашей системе:**

#### **1. Версионирование моделей и данных**
Использовать инструменты, такие как **DVC (Data Version Control)**, для версионирования:
- Датасетов, на которых обучаются ML-модели
- Самих файлов моделей
- Конфигураций обучения

#### **2. Логирование версий**
Расширить центральное состояние `CryptoAnalysisState` для записи версий ключевых компонентов, использованных при анализе.

**Пример кода для CryptoAnalysisState:**

```python
# Дополненная модель CryptoAnalysisState
class CryptoAnalysisState(BaseModel):
    # ... все предыдущие поля ...

    # === ДАННЫЕ ДЛЯ ВОСПРОИЗВОДИМОСТИ ===
    # Словарь, хранящий версии моделей, использованных в этом анализе
    model_versions: Dict[str, str] = Field(
        default_factory=dict, 
        description="Версии ML моделей (e.g., {'success_predictor': 'v1.2.0'})"
    )
    # Хеш коммита git, на котором был запущен анализ
    git_commit_hash: Optional[str] = Field(
        None, 
        description="Git commit hash для воспроизводимости кода"
    )
    # Версия данных, на которых была обучена модель
    training_data_version: Optional[str] = Field(
        None,
        description="Версия обучающих данных"
    )
    # Timestamp анализа для временной привязки
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Точное время проведения анализа"
    )
```

**Пример использования в агенте:**

```python
# Дополненный RiskAssessmentAgent
class RiskAssessmentAgent:
    def __init__(self):
        # Версия модели загружается из конфига или файла
        self.model_version = "v1.2.0" 
        self.success_predictor = load_model(f'token_success_predictor_{self.model_version}.pkl')
        
    def assess(self, state: CryptoAnalysisState) -> CryptoAnalysisState:
        # ... логика оценки ...
        
        # ЗАПИСЫВАЕМ ВЕРСИЮ ИСПОЛЬЗОВАННОЙ МОДЕЛИ В СОСТОЯНИЕ
        state.model_versions['success_predictor'] = self.model_version
        state.git_commit_hash = get_current_git_hash()  # Утилитарная функция
        state.training_data_version = "scam_patterns_v2.1.0"
        
        state.risk_assessment = RiskAssessmentReport(...)
        return state
```

#### **3. Утилитарные функции для версионирования**

```python
import subprocess
from typing import Dict, Any

def get_current_git_hash() -> str:
    """Получить хеш текущего git коммита"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"

def get_model_metadata(model_path: str) -> Dict[str, Any]:
    """Получить метаданные модели"""
    return {
        'model_path': model_path,
        'created_at': os.path.getctime(model_path),
        'size_bytes': os.path.getsize(model_path),
        'checksum': calculate_file_hash(model_path)
    }

def save_analysis_snapshot(state: CryptoAnalysisState, output_dir: str):
    """Сохранить полный снимок анализа для воспроизводимости"""
    snapshot_data = {
        'state': state.dict(),
        'environment': {
            'python_version': sys.version,
            'packages': get_installed_packages(),
            'os_info': platform.platform()
        }
    }
    
    snapshot_file = f"{output_dir}/analysis_snapshot_{state.analysis_timestamp}.json"
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot_data, f, indent=2, default=str)
```

---

## 💰 **ПРИНЦИП #8: УПРАВЛЕНИЕ ЗАТРАТАМИ И БЕЗОПАСНОСТЬ**

### **Суть принципа:**
> *"Система должна быть защищена от непредвиденных расходов и внешних атак. Мы должны контролировать затраты и обезопасить наши API-ключи."*

### **Почему это критично:**
✅ **Финансовая безопасность:** Ошибка в коде не должна приводить к тысячам запросов к платному API и огромным счетам.

✅ **Защита от злоупотреблений:** Если система будет иметь внешний интерфейс, ее нужно защитить от DoS-атак.

✅ **Безопасность ключей:** Компрометация API-ключей может привести к финансовым и репутационным потерям.

✅ **Прогнозируемость расходов:** Вы всегда должны знать, сколько стоит работа вашей системы.

### **Как применяется в нашей системе:**

#### **1. Централизованное управление секретами**
- **Стартовый уровень:** `.env` файлы с четким разделением dev/prod окружений
- **Production уровень:** Doppler, HashiCorp Vault или секреты от облачного провайдера

#### **2. Бюджетный менеджер**
Создать сервис, который отслеживает количество вызовов к платным API и может остановить систему при превышении лимитов.

**Пример кода для Бюджетного Менеджера:**

```python
from collections import Counter
from datetime import datetime, timedelta
import logging

# Простой сервис для контроля затрат
class CostTracker:
    def __init__(self, daily_budget_usd: float = 5.0):
        self.daily_budget = daily_budget_usd
        self.costs = Counter()
        self.call_history = []
        self.api_prices = {
            'openai_gpt4': 0.03 / 1000,  # Цена за 1000 токенов
            'openai_gpt3.5': 0.002 / 1000,
            'goplus_pro': 0.005,  # Цена за вызов (условно)
            'twitter_api': 0.001,  # Цена за запрос
            'coingecko_pro': 0.0001  # Очень дешево
        }
        self.daily_limits = {
            'openai_gpt4': 100,  # Максимум вызовов в день
            'twitter_api': 1000,
            'total_usd': daily_budget_usd
        }
    
    def record_call(self, api_name: str, tokens: int = 0, metadata: dict = None):
        """Записать вызов API с расчетом стоимости"""
        cost = 0
        if api_name in self.api_prices:
            cost = self.api_prices[api_name] * (tokens or 1)
            self.costs[api_name] += cost
            
        # Записать в историю для детального анализа
        self.call_history.append({
            'timestamp': datetime.now(),
            'api_name': api_name,
            'tokens': tokens,
            'cost_usd': cost,
            'metadata': metadata or {}
        })
        
        # Логирование для мониторинга
        logging.info(f"API Call: {api_name}, Cost: ${cost:.4f}, Total today: ${self.get_daily_cost():.2f}")
        
    def get_total_cost(self) -> float:
        """Общая стоимость за все время"""
        return sum(self.costs.values())
        
    def get_daily_cost(self) -> float:
        """Стоимость за сегодня"""
        today = datetime.now().date()
        daily_cost = sum(
            call['cost_usd'] for call in self.call_history 
            if call['timestamp'].date() == today
        )
        return daily_cost
    
    def is_budget_exceeded(self) -> bool:
        """Проверка превышения дневного бюджета"""
        return self.get_daily_cost() > self.daily_budget
        
    def is_api_limit_exceeded(self, api_name: str) -> bool:
        """Проверка превышения лимита для конкретного API"""
        if api_name not in self.daily_limits:
            return False
            
        today = datetime.now().date()
        daily_calls = len([
            call for call in self.call_history 
            if call['timestamp'].date() == today and call['api_name'] == api_name
        ])
        
        return daily_calls >= self.daily_limits[api_name]
    
    def get_remaining_budget(self) -> float:
        """Оставшийся бюджет на сегодня"""
        return max(0, self.daily_budget - self.get_daily_cost())
    
    def generate_cost_report(self) -> dict:
        """Генерация отчета по затратам"""
        return {
            'total_cost': self.get_total_cost(),
            'daily_cost': self.get_daily_cost(),
            'remaining_budget': self.get_remaining_budget(),
            'costs_by_api': dict(self.costs),
            'budget_utilization': (self.get_daily_cost() / self.daily_budget) * 100
        }

# Глобальный экземпляр
cost_tracker = CostTracker()

# Декоратор для автоматического отслеживания затрат
def track_api_cost(api_name: str, tokens_field: str = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Проверяем лимиты перед вызовом
            if cost_tracker.is_budget_exceeded():
                raise Exception(f"Daily budget exceeded: ${cost_tracker.daily_budget}")
                
            if cost_tracker.is_api_limit_exceeded(api_name):
                raise Exception(f"Daily limit exceeded for {api_name}")
            
            # Выполняем функцию
            result = func(*args, **kwargs)
            
            # Записываем стоимость
            tokens = 0
            if tokens_field and hasattr(result, tokens_field):
                tokens = getattr(result, tokens_field)
            elif tokens_field and isinstance(result, dict):
                tokens = result.get(tokens_field, 0)
                
            cost_tracker.record_call(api_name, tokens)
            
            return result
        return wrapper
    return decorator

# Использование в агенте
@track_api_cost('openai_gpt4', 'usage.total_tokens')
def some_expensive_analysis(text: str) -> str:
    """Пример дорогого анализа с автоматическим трекингом затрат"""
    # ... делаем дорогой вызов к OpenAI ...
    response = call_openai_api(text)
    return response.choices[0].message.content

# Альтернативный подход - manual tracking
def manual_expensive_analysis(text: str) -> str:
    if cost_tracker.is_budget_exceeded():
        # Если бюджет превышен, используем fallback или останавливаемся
        logging.warning("Budget exceeded. Using fallback summary.")
        return "Budget exceeded. Using fallback summary."
    
    if cost_tracker.is_api_limit_exceeded('openai_gpt4'):
        logging.warning("API limit exceeded for OpenAI GPT-4")
        return "API limit exceeded. Try again tomorrow."
    
    # ... делаем дорогой вызов к OpenAI ...
    response = call_openai_api(text)
    
    # Записываем стоимость вызова
    cost_tracker.record_call('openai_gpt4', tokens=response.usage.total_tokens)
    
    return response.choices[0].message.content
```

#### **3. Throttling и Rate Limiting**
Реализовать ограничение на частоту вызовов как к внешним API, так и к собственным эндпоинтам.

```python
import time
from functools import wraps
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self):
        self.calls = defaultdict(deque)
        self.limits = {
            'coingecko': (50, 60),  # 50 вызовов в минуту
            'twitter': (100, 900),   # 100 вызовов в 15 минут
            'goplus': (1000, 86400), # 1000 вызовов в день
        }
    
    def is_allowed(self, api_name: str) -> bool:
        if api_name not in self.limits:
            return True
            
        max_calls, time_window = self.limits[api_name]
        now = time.time()
        
        # Удаляем старые записи
        while (self.calls[api_name] and 
               now - self.calls[api_name][0] > time_window):
            self.calls[api_name].popleft()
        
        # Проверяем лимит
        if len(self.calls[api_name]) >= max_calls:
            return False
            
        # Записываем новый вызов
        self.calls[api_name].append(now)
        return True
    
    def wait_time(self, api_name: str) -> float:
        """Время ожидания до следующего разрешенного вызова"""
        if api_name not in self.limits:
            return 0
            
        max_calls, time_window = self.limits[api_name]
        if len(self.calls[api_name]) < max_calls:
            return 0
            
        oldest_call = self.calls[api_name][0]
        return time_window - (time.time() - oldest_call)

rate_limiter = RateLimiter()

def rate_limit(api_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not rate_limiter.is_allowed(api_name):
                wait_time = rate_limiter.wait_time(api_name)
                logging.warning(f"Rate limit hit for {api_name}. Waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

#### **4. Управление секретами - практическая реализация**

```python
import os
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class APICredentials:
    """Структура для хранения API credentials"""
    api_key: str
    base_url: Optional[str] = None
    rate_limit: Optional[int] = None
    daily_quota: Optional[int] = None

class SecretManager:
    """Централизованное управление секретами"""
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self._secrets: Dict[str, APICredentials] = {}
        self._load_secrets()
    
    def _load_secrets(self):
        """Загрузка секретов в зависимости от окружения"""
        if self.environment == 'development':
            self._load_from_env()
        elif self.environment == 'production':
            self._load_from_vault()  # В будущем
        
    def _load_from_env(self):
        """Загрузка из .env файла"""
        self._secrets = {
            'coingecko': APICredentials(
                api_key=os.getenv('COINGECKO_API_KEY', ''),
                base_url='https://api.coingecko.com/api/v3',
                rate_limit=50,
                daily_quota=10000
            ),
            'twitter': APICredentials(
                api_key=os.getenv('TWITTER_API_KEY', ''),
                base_url='https://api.twitter.com/2',
                rate_limit=100,
                daily_quota=500000
            ),
            'openai': APICredentials(
                api_key=os.getenv('OPENAI_API_KEY', ''),
                base_url='https://api.openai.com/v1',
                daily_quota=1000  # В токенах
            )
        }
    
    def get_credentials(self, service: str) -> APICredentials:
        """Получить credentials для сервиса"""
        if service not in self._secrets:
            raise ValueError(f"No credentials found for service: {service}")
        
        creds = self._secrets[service]
        if not creds.api_key:
            raise ValueError(f"API key not configured for service: {service}")
            
        return creds
    
    def is_service_available(self, service: str) -> bool:
        """Проверить доступность сервиса"""
        try:
            creds = self.get_credentials(service)
            return bool(creds.api_key)
        except ValueError:
            return False

# Глобальный менеджер секретов
secret_manager = SecretManager()
```

---

## 💡 **СТОИМОСТЬ СЕРВИСОВ УПРАВЛЕНИЯ СЕКРЕТАМИ**

### **Doppler** 
**Рекомендуется для старта**

- ✅ **Полностью бесплатный план** для индивидуальных разработчиков
- ✅ **До 5 пользователей** бесплатно 
- ✅ **Неограниченные проекты и секреты**
- ✅ **Простота настройки** - 15 минут на интеграцию
- 💰 **Платить нужно только:** при росте команды до 6+ человек

### **HashiCorp Vault**

**Два варианта:**

1. **HCP Vault (облачная версия):**
   - ✅ **Бесплатный план** для разработки
   - ✅ **Управляемый сервис** - не нужно настраивать

2. **Vault Open Source (самостоятельная установка):**
   - ✅ **Полностью бесплатный** софт
   - 💰 **Стоимость:** только аренда сервера ($5-6/месяц)
   - ⚠️ **Требует:** технические навыки для настройки

### **Рекомендация:**
Начинайте с **Doppler** - он решает 99% задач по управлению секретами для индивидуального проекта совершенно бесплатно.

---

## 🎯 **ЗАКЛЮЧЕНИЕ**

Эти два принципа критически важны для создания профессиональной системы:

1. **Принцип #7 (Воспроизводимость)** обеспечивает возможность анализа и улучшения системы
2. **Принцип #8 (Управление затратами)** защищает от непредвиденных расходов и уязвимостей

Без них система может работать, но будет непрофессиональной и рискованной для продуктивного использования. Интеграция этих принципов превращает любительский проект в enterprise-ready решение.

---

*Документ создан на основе рекомендаций Gemini*  
*Дата: 1 августа 2025*  
*Статус: Готов к интеграции в основной план проекта*
