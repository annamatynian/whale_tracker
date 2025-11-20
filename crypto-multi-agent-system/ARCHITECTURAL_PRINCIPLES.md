# 🏗️ Архитектурные принципы мультиагентной системы
## Рациональный подход к построению AI агентов

*Дата создания: 31 июля 2025*  
*Версия: 1.0*  
*Связанный документ: Multi-Agent_Crypto_Analysis_System.md*

---

## 📋 **ВВЕДЕНИЕ**

Этот документ содержит **критически важные архитектурные принципы** для построения мультиагентной криптоаналитической системы. Принципы основаны на практическом опыте разработчиков и направлены на **предотвращение "ада отладки"** и создание **масштабируемой, поддерживаемой системы**.

### **🎯 Цель документа:**
- Обеспечить четкое понимание архитектурных решений
- Предотвратить типичные ошибки в мультиагентных системах
- Создать reference guide для принятия технических решений
- Гарантировать консистентность подхода на всех этапах разработки

---

## 🧠 **ФИЛОСОФИЯ АРХИТЕКТУРЫ**

### **Основная идея: "Правильный инструмент для правильной задачи"**

**Проблема:** Многие разработчики либо используют слишком простые инструменты для сложных задач, либо применяют сложные фреймворки там, где достаточно простых решений.

**Наше решение:** Гибридный подход с четкими критериями выбора:

```python
# Матрица принятия архитектурных решений
TOOL_SELECTION_MATRIX = {
    'simple_linear_task': {
        'example': 'API call → parse → validate → return',
        'solution': 'Pure Python function + Pydantic',
        'avoid': 'Langchain для простого API вызова',
        'reason': 'Overhead фреймворка больше пользы'
    },
    'complex_coordination': {
        'example': 'Multi-agent workflow с условной логикой',
        'solution': 'LangGraph для оркестрации',
        'avoid': 'Самописный orchestrator',
        'reason': 'Проверенные паттерны координации'
    },
    'rapid_prototyping': {
        'example': 'MVP за 3 недели',
        'solution': 'CrewAI для быстрой сборки',
        'avoid': 'Custom implementation с нуля',
        'reason': 'Скорость важнее идеальной архитектуры'
    }
}
```

---

## 🎯 **ПРИНЦИП #1: МИНИМИЗАЦИЯ СЛОЖНОСТИ**

### **Суть принципа:**
**"Каждый компонент должен быть максимально простым для решения своей конкретной задачи"**

### **Почему это критично:**
- ✅ **Отладка:** Проблемы легко локализуются и исправляются
- ✅ **Тестирование:** Простые функции легко покрываются тестами
- ✅ **Понимание:** Код читается и поддерживается командой
- ✅ **Рефакторинг:** Изменения не ломают другие компоненты

### **Как применяется в нашей системе:**

#### **✅ ПРАВИЛЬНО: Агент как простая функция**
```python
def security_agent_node(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """
    Агент реализован как простая, изолированная функция.
    Принцип: одна функция = одна ответственность.
    """
    try:
        # 1. Читаем входные данные из состояния
        contract_address = state.contract_address
        
        # 2. Выполняем работу через простые функции
        security_data = check_contract_security(contract_address)
        risk_score = calculate_security_risk(security_data)
        
        # 3. Создаем типизированный результат
        security_report = SecurityReport(
            contract_address=contract_address,
            is_honeypot=security_data.get('is_honeypot', False),
            risk_score=risk_score,
            red_flags=security_data.get('red_flags', [])
        )
        
        # 4. Записываем результат в состояние
        state.security_report = security_report
        state.processing_stage = "SECURITY_COMPLETE"
        
        return state
        
    except Exception as e:
        # 5. Обрабатываем ошибки gracefully
        state.errors.append(f"SecurityAgent error: {str(e)}")
        state.processing_stage = "SECURITY_ERROR"
        return state

def check_contract_security(contract_address: str) -> dict:
    """
    Вспомогательная функция - тоже максимально простая.
    Делает ОДНО дело: запрос к GoPlus API.
    """
    url = f"https://api.gopluslabs.io/api/v1/token_security/{contract_address}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

#### **❌ НЕПРАВИЛЬНО: Излишние абстракции**
```python
# ИЗБЕГАЕМ ТАКОГО ПОДХОДА!
class SecurityAgentBase(ABC):
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.validator = SecurityValidator(config.validation_rules)
        self.reporter = SecurityReporter(config.report_format)
    
    @abstractmethod
    def analyze(self, token_data: TokenAnalysisRequest) -> SecurityAnalysisResponse:
        pass

class GoPlus SecurityAgent(SecurityAgentBase):
    def __init__(self, config: SecurityConfig):
        super().__init__(config)
        self.api_client = GoPlusAPIClient(config.api_key)
        self.response_parser = GoPlusResponseParser(config.parsing_rules)
    
    def analyze(self, token_data: TokenAnalysisRequest) -> SecurityAnalysisResponse:
        # 10+ строк кода для того же API вызова...
```

**Проблемы сложного подхода:**
- 🚫 **Отладка:** Проблема может быть в любом из 5+ классов
- 🚫 **Тестирование:** Нужно мокать множество зависимостей
- 🚫 **Понимание:** Нужно изучить всю иерархию классов
- 🚫 **Изменения:** Модификация одного класса может сломать другие

---

## 🔒 **ПРИНЦИП #2: КОНТРАКТНО-ОРИЕНТИРОВАННАЯ АРХИТЕКТУРА**

### **Суть принципа:**
**"Каждый интерфейс между компонентами должен иметь строгий, валидируемый контракт данных"**

### **Почему это критично:**
- ✅ **Раннее обнаружение ошибок:** Pydantic ловит проблемы во время выполнения
- ✅ **Автодокументирование:** Схемы данных служат документацией
- ✅ **Безопасный рефакторинг:** Изменения схем сразу выявляют breaking changes
- ✅ **IDE поддержка:** Автокомплит и проверка типов

### **Архитектура состояния системы:**

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ProcessingStage(str, Enum):
    """Стадии обработки токена в системе"""
    PENDING = "PENDING"
    MARKET_ANALYSIS = "MARKET_ANALYSIS"
    DISCOVERY = "DISCOVERY"
    SECURITY_CHECK = "SECURITY_CHECK"
    SOCIAL_ANALYSIS = "SOCIAL_ANALYSIS"
    TECHNICAL_ANALYSIS = "TECHNICAL_ANALYSIS"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    DECISION_MAKING = "DECISION_MAKING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

class CryptoAnalysisState(BaseModel):
    """
    ЦЕНТРАЛЬНОЕ СОСТОЯНИЕ всей мультиагентной системы.
    
    Это единственный объект, который передается между всеми агентами.
    Каждый агент читает нужные ему поля и записывает свой результат.
    
    КРИТИЧЕСКИ ВАЖНО: 
    - Все поля Optional кроме входных данных
    - Каждый агент добавляет свой строго типизированный отчет
    - Состояние полностью валидируется Pydantic
    """
    
    # === ВХОДНЫЕ ДАННЫЕ ===
    contract_address: str = Field(..., description="Адрес контракта токена")
    token_symbol: Optional[str] = Field(None, description="Символ токена")
    initial_source: Optional[str] = Field(None, description="Источник обнаружения")
    
    # === ОТЧЕТЫ ОТ АГЕНТОВ ===
    market_conditions: Optional['MarketConditionsReport'] = None
    discovery_report: Optional['DiscoveryReport'] = None
    security_report: Optional['SecurityReport'] = None
    social_analysis: Optional['SocialAnalysisReport'] = None
    technical_analysis: Optional['TechnicalAnalysisReport'] = None
    risk_assessment: Optional['RiskAssessmentReport'] = None
    final_decision: Optional['FinalDecision'] = None
    
    # === МЕТАДАННЫЕ ===
    processing_stage: ProcessingStage = ProcessingStage.PENDING
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # === СЛУЖЕБНЫЕ ПОЛЯ ===
    should_stop: bool = Field(False, description="Флаг для остановки обработки")
    stop_reason: Optional[str] = Field(None, description="Причина остановки")
    
    def add_error(self, agent_name: str, error_message: str):
        """Добавить ошибку с указанием источника"""
        self.errors.append(f"{agent_name}: {error_message}")
        self.updated_at = datetime.now()
    
    def add_warning(self, agent_name: str, warning_message: str):
        """Добавить предупреждение с указанием источника"""
        self.warnings.append(f"{agent_name}: {warning_message}")
        self.updated_at = datetime.now()
    
    def mark_stage_complete(self, stage: ProcessingStage):
        """Отметить завершение стадии обработки"""
        self.processing_stage = stage
        self.updated_at = datetime.now()
```

### **Контракты данных для каждого агента:**

```python
class SecurityReport(BaseModel):
    """
    Строгий контракт для результатов Security Agent.
    
    Любые изменения в этой модели будут автоматически обнаружены
    во всех местах использования благодаря Pydantic валидации.
    """
    contract_address: str
    is_honeypot: bool
    is_verified: bool
    buy_tax: Optional[float] = Field(None, ge=0, le=1)
    sell_tax: Optional[float] = Field(None, ge=0, le=1)
    liquidity_locked: Optional[bool] = None
    owner_address: Optional[str] = None
    risk_score: int = Field(..., ge=0, le=100, description="Общий риск-скор от 0 до 100")
    red_flags: List[str] = Field(default_factory=list)
    security_analysis_timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('contract_address')
    def validate_contract_address(cls, v):
        """Валидация формата адреса контракта"""
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid contract address format')
        return v.lower()

class SocialAnalysisReport(BaseModel):
    """Контракт для результатов Social Intelligence Agent"""
    contract_address: str
    twitter_mentions: int = Field(ge=0)
    twitter_sentiment: float = Field(ge=-1, le=1)
    telegram_mentions: int = Field(ge=0)
    discord_mentions: int = Field(ge=0)
    influencer_mentions: List[str] = Field(default_factory=list)
    coordinated_shilling_detected: bool = False
    community_strength_score: int = Field(ge=0, le=100)
    social_red_flags: List[str] = Field(default_factory=list)
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

class RiskAssessmentReport(BaseModel):
    """Контракт для результатов Risk Assessment Agent"""
    contract_address: str
    success_probability: float = Field(ge=0, le=1)
    expected_roi: float
    recommended_position_size_usd: float = Field(ge=0)
    max_loss_scenario: float = Field(le=0)
    kelly_fraction: float = Field(ge=0, le=1)
    confidence_interval: tuple[float, float]
    risk_category: str = Field(regex=r'^(VERY_LOW|LOW|MEDIUM|HIGH|VERY_HIGH)$')
    assessment_timestamp: datetime = Field(default_factory=datetime.now)

class FinalDecision(BaseModel):
    """Контракт для финального решения системы"""
    contract_address: str
    decision: str = Field(regex=r'^(STRONG_BUY|BUY|WATCH|AVOID|SCAM)$')
    confidence: float = Field(ge=0, le=1)
    recommended_action: str
    position_size_usd: float = Field(ge=0)
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    reasoning: List[str] = Field(default_factory=list)
    decision_timestamp: datetime = Field(default_factory=datetime.now)
```

### **Преимущества такого подхода:**

```python
# ПРИМЕР: Автоматическое обнаружение ошибок
def process_security_report(state: CryptoAnalysisState):
    """
    Если Security Agent изменит структуру своего отчета,
    эта функция НЕМЕДЛЕННО сломается с понятной ошибкой Pydantic,
    а не будет молча работать неправильно.
    """
    if state.security_report is None:
        raise ValueError("Security report not available")
    
    # Если поле переименуется, получим ошибку валидации
    risk_score = state.security_report.risk_score  # автокомплит работает!
    
    # Если тип изменится, получим ошибку типизации
    if risk_score > 80:  # IDE знает, что это int
        return "HIGH_RISK"
    
    return "ACCEPTABLE_RISK"
```

---

## 🎭 **ПРИНЦИП #3: СЛОИСТАЯ АРХИТЕКТУРА С LANGGRAPH**

### **Суть принципа:**
**"LangGraph отвечает ТОЛЬКО за координацию, агенты содержат ТОЛЬКО бизнес-логику"**

### **Почему это важно:**
- ✅ **Четкое разделение ответственности:** Координация отделена от логики
- ✅ **Тестируемость:** Агенты можно тестировать независимо от LangGraph
- ✅ **Переносимость:** Агенты можно использовать с другими orchestrator'ами
- ✅ **Отладка:** Проблемы либо в координации, либо в логике агента

### **Архитектура разделения:**

```python
# УРОВЕНЬ 1: Координация (LangGraph)
from langgraph.graph import StateGraph, END

def build_crypto_analysis_workflow():
    """
    LangGraph workflow содержит ТОЛЬКО логику координации.
    Никакой бизнес-логики здесь нет!
    """
    workflow = StateGraph(CryptoAnalysisState)
    
    # Добавляем узлы (каждый узел = простая функция)
    workflow.add_node("market_check", market_conditions_node)
    workflow.add_node("discovery", discovery_node)
    workflow.add_node("security", security_node)
    workflow.add_node("social", social_analysis_node)
    workflow.add_node("technical", technical_analysis_node)
    workflow.add_node("risk", risk_assessment_node)
    workflow.add_node("decision", decision_node)
    
    # ТОЛЬКО логика переходов - никакой бизнес-логики!
    workflow.set_entry_point("market_check")
    workflow.add_edge("market_check", "discovery")
    workflow.add_edge("discovery", "security")
    
    # Условные переходы на основе результатов агентов
    workflow.add_conditional_edges(
        "security",
        should_continue_after_security,  # Простая функция-предикат
        {
            "continue": "social",
            "stop_scam": END,
            "stop_error": END
        }
    )
    
    workflow.add_edge("social", "technical")
    workflow.add_edge("technical", "risk")
    workflow.add_edge("risk", "decision")
    workflow.add_edge("decision", END)
    
    return workflow.compile()

def should_continue_after_security(state: CryptoAnalysisState) -> str:
    """
    Простая функция-предикат для условных переходов.
    
    Содержит ТОЛЬКО логику принятия решения о переходе,
    не содержит бизнес-логику анализа.
    """
    if state.should_stop:
        return "stop_error"
    
    if state.security_report is None:
        return "stop_error"
    
    if state.security_report.risk_score > 80:
        return "stop_scam"
    
    return "continue"
```

```python
# УРОВЕНЬ 2: Бизнес-логика агентов (Pure Python)
def security_node(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """
    Узел LangGraph - простая функция-обертка.
    Вся бизнес-логика вынесена в отдельные функции.
    """
    try:
        # Обновляем стадию обработки
        state.mark_stage_complete(ProcessingStage.SECURITY_CHECK)
        
        # Вызываем бизнес-логику (отдельные функции)
        security_report = analyze_token_security(
            contract_address=state.contract_address,
            token_symbol=state.token_symbol
        )
        
        # Записываем результат в состояние
        state.security_report = security_report
        
        return state
        
    except Exception as e:
        state.add_error("SecurityAgent", str(e))
        state.should_stop = True
        state.stop_reason = f"Security analysis failed: {str(e)}"
        return state

def analyze_token_security(contract_address: str, token_symbol: Optional[str] = None) -> SecurityReport:
    """
    ЧИСТАЯ бизнес-логика Security Agent.
    
    Эта функция:
    - Не знает про LangGraph
    - Не знает про состояние системы
    - Просто принимает входные данные и возвращает результат
    - Легко тестируется изолированно
    """
    # Получаем данные из внешних источников
    goplus_data = fetch_goplus_security_data(contract_address)
    etherscan_data = fetch_etherscan_verification(contract_address)
    
    # Анализируем полученные данные
    risk_score = calculate_security_risk_score(goplus_data, etherscan_data)
    red_flags = identify_security_red_flags(goplus_data, etherscan_data)
    
    # Возвращаем строго типизированный результат
    return SecurityReport(
        contract_address=contract_address,
        is_honeypot=goplus_data.get('is_honeypot', False),
        is_verified=etherscan_data.get('is_verified', False),
        buy_tax=goplus_data.get('buy_tax'),
        sell_tax=goplus_data.get('sell_tax'),
        risk_score=risk_score,
        red_flags=red_flags
    )

# УРОВЕНЬ 3: Утилитарные функции (самый простой уровень)
def fetch_goplus_security_data(contract_address: str) -> dict:
    """
    Максимально простая функция для API вызова.
    Никаких классов, никаких абстракций - просто запрос и ответ.
    """
    url = f"https://api.gopluslabs.io/api/v1/token_security/{contract_address}"
    
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    return data.get('result', {}).get(contract_address, {})

def calculate_security_risk_score(goplus_data: dict, etherscan_data: dict) -> int:
    """
    Простая функция расчета риск-скора.
    Четкие входные и выходные данные, легко тестируется.
    """
    score = 0
    
    # Проверки на основе GoPlus данных
    if goplus_data.get('is_honeypot') == '1':
        score += 50
    
    if goplus_data.get('is_blacklisted') == '1':
        score += 30
        
    if not etherscan_data.get('is_verified', False):
        score += 20
    
    # Ограничиваем скор максимумом 100
    return min(score, 100)
```

### **Преимущества слоистой архитектуры:**

```python
# ТЕСТИРОВАНИЕ: Каждый слой тестируется независимо

# Тест бизнес-логики (без LangGraph)
def test_security_analysis():
    mock_goplus = {'is_honeypot': '0', 'is_blacklisted': '0'}
    mock_etherscan = {'is_verified': True}
    
    # Тестируем ТОЛЬКО бизнес-логику
    result = analyze_token_security('0x123...')
    
    assert isinstance(result, SecurityReport)
    assert result.risk_score >= 0

# Тест координации (с моками агентов)  
def test_workflow_stops_on_high_risk():
    initial_state = CryptoAnalysisState(contract_address='0x123...')
    
    # Мокаем результат Security Agent
    initial_state.security_report = SecurityReport(
        risk_score=90,  # Высокий риск
        # ... другие поля
    )
    
    # Тестируем ТОЛЬКО логику координации
    result = should_continue_after_security(initial_state)
    
    assert result == "stop_scam"
```

---

## 🔄 **ПРИНЦИП #4: ИЗОЛЯЦИЯ И ОТКАЗОУСТОЙЧИВОСТЬ**

### **Суть принципа:**
**"Каждый компонент должен работать независимо и gracefully обрабатывать сбои других компонентов"**

### **Почему это критично:**
- ✅ **Отладка:** Проблема локализуется в конкретном компоненте
- ✅ **Надежность:** Сбой одного агента не ломает всю систему
- ✅ **Разработка:** Команда может работать над разными агентами параллельно
- ✅ **Тестирование:** Каждый компонент тестируется изолированно

### **Паттерны изоляции:**

```python
# ПАТТЕРН 1: Изолированный агент с fallback значениями
def social_analysis_node(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """
    Агент работает независимо от других агентов.
    Если что-то не так с внешними зависимостями - возвращает fallback.
    """
    try:
        # Пытаемся выполнить основную работу
        social_report = analyze_social_signals(
            contract_address=state.contract_address,
            token_symbol=state.token_symbol
        )
        
        state.social_analysis = social_report
        state.mark_stage_complete(ProcessingStage.SOCIAL_ANALYSIS)
        
    except TwitterAPIError as e:
        # Специфичная обработка проблем с Twitter API
        state.add_warning("SocialAgent", f"Twitter API unavailable: {str(e)}")
        
        # Создаем fallback отчет с ограниченными данными
        state.social_analysis = SocialAnalysisReport(
            contract_address=state.contract_address,
            twitter_mentions=0,  # Fallback значения
            twitter_sentiment=0.0,
            community_strength_score=50,  # Нейтральная оценка
            social_red_flags=["Twitter data unavailable"]
        )
        
    except Exception as e:
        # Общая обработка неожиданных ошибок
        state.add_error("SocialAgent", f"Unexpected error: {str(e)}")
        
        # Устанавливаем минимальный fallback
        state.social_analysis = SocialAnalysisReport(
            contract_address=state.contract_address,
            twitter_mentions=0,
            twitter_sentiment=0.0,
            community_strength_score=0,  # Неизвестно = худший случай
            social_red_flags=["Social analysis failed"]
        )
    
    finally:
        # Агент ВСЕГДА возвращает валидное состояние
        return state

# ПАТТЕРН 2: Standalone mode для разработки и тестирования
def analyze_social_signals(
    contract_address: str,
    token_symbol: Optional[str] = None,
    standalone_mode: bool = False
) -> SocialAnalysisReport:
    """
    Функция может работать как часть системы или автономно.
    Standalone mode полезен для разработки и отладки.
    """
    if standalone_mode:
        # В автономном режиме используем mock данные
        return SocialAnalysisReport(
            contract_address=contract_address,
            twitter_mentions=42,
            twitter_sentiment=0.3,
            community_strength_score=65,
            social_red_flags=[]
        )
    
    # Обычная логика анализа
    twitter_data = fetch_twitter_mentions(contract_address, token_symbol)
    telegram_data = fetch_telegram_mentions(contract_address)
    
    return SocialAnalysisReport(
        contract_address=contract_address,
        twitter_mentions=len(twitter_data),
        twitter_sentiment=calculate_sentiment(twitter_data),
        community_strength_score=assess_community_strength(twitter_data, telegram_data),
        social_red_flags=identify_social_red_flags(twitter_data, telegram_data)
    )

# ПАТТЕРН 3: Circuit Breaker для внешних API
class APICircuitBreaker:
    """
    Защита от каскадных сбоев внешних API.
    
    Если API недоступен больше N попыток подряд,
    переключаемся в fallback режим на определенное время.
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def call_api(self, api_function, *args, **kwargs):
        """Обертка для API вызовов с circuit breaker логикой"""
        
        # Проверяем, можно ли попробовать API снова
        if self.is_open:
            if self._should_attempt_reset():
                self.is_open = False
                self.failure_count = 0
            else:
                raise CircuitBreakerOpenError("API circuit breaker is open")
        
        try:
            result = api_function(*args, **kwargs)
            # Успешный вызов - сбрасываем счетчик
            self.failure_count = 0
            return result
            
        except Exception as e:
            # Неудачный вызов - увеличиваем счетчик
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Проверяем, прошло ли достаточно времени для попытки сброса"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time > self.recovery_timeout

# Использование Circuit Breaker
goplus_circuit_breaker = APICircuitBreaker()

def fetch_goplus_security_data_with_protection(contract_address: str) -> dict:
    """API вызов с защитой от каскадных сбоев"""
    try:
        return goplus_circuit_breaker.call_api(
            fetch_goplus_security_data_raw,
            contract_address
        )
    except CircuitBreakerOpenError:
        # API недоступен - возвращаем безопасные fallback значения
        return {
            'is_honeypot': '0',  # Предполагаем безопасность
            'buy_tax': '0',
            'sell_tax': '0',
            '_fallback_reason': 'GoPlus API circuit breaker open'
        }
```

### **Паттерны graceful degradation:**

```python
# ПРИМЕР: Decision Agent работает даже при отсутствии данных от других агентов
def decision_node(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """
    Decision Agent принимает решение на основе доступных данных.
    Если какие-то агенты не сработали - работает с тем, что есть.
    """
    try:
        # Собираем все доступные данные
        available_reports = {}
        
        if state.security_report:
            available_reports['security'] = state.security_report
        if state.social_analysis:
            available_reports['social'] = state.social_analysis
        if state.risk_assessment:
            available_reports['risk'] = state.risk_assessment
            
        # Принимаем решение на основе доступных данных
        if len(available_reports) == 0:
            # Критическая ситуация - нет данных вообще
            decision = FinalDecision(
                contract_address=state.contract_address,
                decision="AVOID",
                confidence=0.0,
                recommended_action="Insufficient data for analysis",
                position_size_usd=0,
                reasoning=["No analysis data available"]
            )
        
        elif 'security' in available_reports and available_reports['security'].risk_score > 70:
            # Есть данные безопасности и они показывают высокий риск
            decision = FinalDecision(
                contract_address=state.contract_address,
                decision="SCAM",
                confidence=0.9,
                recommended_action="Avoid due to security risks",
                position_size_usd=0,
                reasoning=[f"High security risk: {available_reports['security'].risk_score}"]
            )
            
        else:
            # Принимаем решение на основе доступных данных
            decision = make_decision_with_partial_data(available_reports)
        
        state.final_decision = decision
        state.mark_stage_complete(ProcessingStage.COMPLETE)
        
    except Exception as e:
        state.add_error("DecisionAgent", str(e))
        # Даже при ошибке возвращаем консервативное решение
        state.final_decision = FinalDecision(
            contract_address=state.contract_address,
            decision="AVOID",
            confidence=0.0,
            recommended_action="Decision making failed",
            position_size_usd=0,
            reasoning=[f"Decision error: {str(e)}"]
        )
    
    return state
```

---

## 📋 **ПРИНЦИП #5: ПОЭТАПНАЯ РАЗРАБОТКА И СТАБИЛЬНЫЕ ТОЧКИ**

### **Суть принципа:**
**"Каждый этап разработки должен заканчиваться working software с возможностью rollback"**

### **Почему это критично:**
- ✅ **Избежание ада отладки:** Всегда есть рабочая версия для отката
- ✅ **Демонстрируемый прогресс:** Можно показать результат на любом этапе
- ✅ **Минимизация рисков:** Проблемы выявляются на раннем этапе
- ✅ **Командная работа:** Четкие milestone'ы для координации

### **Git workflow как архитектурный принцип:**

```bash
# СТРУКТУРА ВЕТОК
main                    # Всегда рабочая версия для демо
├── feature/market-agent    # Разработка Market Conditions Agent
├── feature/discovery-agent # Разработка Discovery Agent  
├── feature/security-agent  # Разработка Security Agent
└── feature/integration     # Интеграция агентов

# ОБЯЗАТЕЛЬНЫЕ ТЕГИ СТАБИЛЬНОСТИ
v1.0-market-agent      # Market Agent работает изолированно
v1.0-data-pipeline     # Discovery + Security работают изолированно
v1.0-mvp              # Полный MVP pipeline работает end-to-end
v1.0-social-intel     # Добавлен Social Intelligence Agent
v1.0-production       # Production-ready система

# ПРАВИЛО ЗОЛОТОЙ ВЕТКИ
# main branch ВСЕГДА содержит демонстрируемую версию
# Merge только после полного тестирования
# При проблемах: git checkout v1.0-market-agent = мгновенный rollback
```

### **Definition of Done для каждого этапа:**

```python
# WEEK 1: Market Conditions Agent
WEEK_1_DEFINITION_OF_DONE = {
    'functional_requirements': [
        'Получает USDT dominance данные из CoinGecko API',
        'Определяет market regime (AGGRESSIVE/CONSERVATIVE)',
        'Логирует все операции без ошибок',
        'Обрабатывает API failures gracefully'
    ],
    'technical_requirements': [
        'Unit тесты покрывают 80%+ кода',
        'Pydantic модели для всех входных/выходных данных',
        'Structured logging настроен',
        'Error handling для всех API вызовов'
    ],
    'integration_requirements': [
        'Агент можно запустить изолированно',
        'Интерфейс готов для интеграции с orchestrator',
        'Docker контейнер собирается и запускается',
        'Configuration через environment variables'
    ],
    'documentation_requirements': [
        'API агента задокументирован',
        'Примеры использования созданы',
        'README обновлен',
        'Architecture Decision Records (ADR) записаны'
    ]
}

# WEEK 2: Data Pipeline Agents  
WEEK_2_DEFINITION_OF_DONE = {
    'functional_requirements': [
        'Discovery Agent находит 10-50 новых токенов в день',
        'Security Agent оценивает риски с точностью 80%+',
        'Оба агента работают независимо от Market Agent',
        'Rate limiting и retry logic реализованы'
    ],
    'technical_requirements': [
        'Каждый агент можно запустить в изоляции',
        'Integration тесты между агентами',
        'Performance benchmarks установлены',
        'Monitoring и alerting настроены'
    ],
    'quality_requirements': [
        'Code review прошел',
        'Security audit базовых функций',
        'Load testing с реальными API',
        'Error scenarios протестированы'
    ]
}

# WEEK 3: MVP Integration
WEEK_3_DEFINITION_OF_DONE = {
    'system_requirements': [
        'End-to-end pipeline работает без участия человека',
        'Telegram получает 3-8 качественных алертов в день',
        'Система работает стабильно 95% времени',
        'Все компоненты логируют операции'
    ],
    'production_readiness': [
        'Health check endpoints работают',
        'Graceful shutdown реализован',
        'Configuration validation проходит при старте',
        'Backup и recovery процедуры задокументированы'
    ],
    'user_acceptance': [
        'Telegram bot отвечает на команды',
        'Алерты содержат всю необходимую информацию',
        'False positive rate < 25%',
        'Response time < 2 минут от обнаружения до алерта'
    ]
}
```

### **Архитектура для поэтапной разработки:**

```python
# ПАТТЕРН: Агенты с режимами работы
class AgentMode(str, Enum):
    DEVELOPMENT = "development"    # Mock данные, быстрая отладка
    TESTING = "testing"           # Real API, но с ограничениями
    PRODUCTION = "production"      # Full functionality
    STANDALONE = "standalone"      # Изолированная работа для demo

def security_agent_node(
    state: CryptoAnalysisState,
    mode: AgentMode = AgentMode.PRODUCTION
) -> CryptoAnalysisState:
    """
    Агент поддерживает разные режимы работы для поэтапной разработки.
    """
    if mode == AgentMode.DEVELOPMENT:
        # В режиме разработки возвращаем предсказуемые данные
        state.security_report = SecurityReport(
            contract_address=state.contract_address,
            is_honeypot=False,
            is_verified=True,
            risk_score=25,  # Безопасный тестовый токен
            red_flags=[]
        )
        return state
    
    elif mode == AgentMode.STANDALONE:
        # В standalone режиме работаем независимо от других агентов
        # Полезно для демонстрации конкретного агента
        return run_security_analysis_standalone(state)
    
    else:
        # Обычная production логика
        return run_security_analysis_production(state)

# ПАТТЕРН: Конфигурируемые источники данных
class DataSourceConfig(BaseModel):
    """Конфигурация источников данных для разных этапов разработки"""
    use_mock_data: bool = False
    api_rate_limit: Optional[int] = None
    fallback_to_cache: bool = True
    enable_circuit_breaker: bool = True
    
def fetch_token_data(
    contract_address: str,
    config: DataSourceConfig = DataSourceConfig()
) -> dict:
    """
    Функция адаптируется к этапу разработки через конфигурацию.
    """
    if config.use_mock_data:
        # Этап 1: Разработка с mock данными
        return generate_mock_token_data(contract_address)
    
    elif config.fallback_to_cache:
        # Этап 2: Тестирование с кешем как fallback
        try:
            return fetch_from_api_with_cache(contract_address)
        except APIError:
            return load_from_cache(contract_address)
    
    else:
        # Этап 3: Production без fallback
        return fetch_from_api(contract_address)
```

---

## 🔍 **ПРИНЦИП #6: НАБЛЮДАЕМОСТЬ И ДИАГНОСТИКА**

### **Суть принципа:**
**"Система должна предоставлять полную видимость своего состояния и операций"**

### **Почему это критично:**
- ✅ **Быстрая диагностика:** Проблемы обнаруживаются и локализуются быстро
- ✅ **Оптимизация производительности:** Метрики показывают узкие места
- ✅ **Бизнес-инсайты:** Данные о работе системы помогают улучшать алгоритмы
- ✅ **SLA мониторинг:** Отслеживание соответствия требованиям

### **Архитектура логирования:**

```python
import structlog
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class EventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    API_CALL = "api_call"
    API_ERROR = "api_error"
    DECISION_MADE = "decision_made"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"

@dataclass
class LogEvent:
    """Структурированное событие для логирования"""
    event_type: EventType
    agent_name: Optional[str]
    contract_address: Optional[str]
    duration_ms: Optional[int]
    success: bool
    metadata: Dict[str, Any]
    error_message: Optional[str] = None

# Настройка структурированного логирования
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def log_agent_operation(
    agent_name: str,
    operation: str,
    contract_address: str,
    success: bool,
    duration_ms: int,
    metadata: Dict[str, Any] = None,
    error: Optional[str] = None
):
    """Стандартизированное логирование операций агентов"""
    
    event = LogEvent(
        event_type=EventType.AGENT_COMPLETE if success else EventType.AGENT_ERROR,
        agent_name=agent_name,
        contract_address=contract_address,
        duration_ms=duration_ms,
        success=success,
        metadata=metadata or {},
        error_message=error
    )
    
    log_level = LogLevel.INFO if success else LogLevel.ERROR
    
    logger.bind(
        event_type=event.event_type.value,
        agent_name=event.agent_name,
        contract_address=event.contract_address,
        duration_ms=event.duration_ms,
        success=event.success,
        metadata=event.metadata,
        error_message=event.error_message
    ).log(log_level.value, f"{agent_name} {operation} {'completed' if success else 'failed'}")

# Декоратор для автоматического логирования агентов
def log_agent_execution(agent_name: str):
    """Декоратор для автоматического логирования выполнения агентов"""
    def decorator(func):
        def wrapper(state: CryptoAnalysisState, *args, **kwargs):
            start_time = time.time()
            
            try:
                logger.bind(
                    event_type=EventType.AGENT_START.value,
                    agent_name=agent_name,
                    contract_address=state.contract_address
                ).info(f"{agent_name} started")
                
                result = func(state, *args, **kwargs)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                log_agent_operation(
                    agent_name=agent_name,
                    operation="analysis",
                    contract_address=state.contract_address,
                    success=True,
                    duration_ms=duration_ms,
                    metadata={
                        'processing_stage': result.processing_stage.value,
                        'errors_count': len(result.errors),
                        'warnings_count': len(result.warnings)
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                
                log_agent_operation(
                    agent_name=agent_name,
                    operation="analysis",
                    contract_address=state.contract_address,
                    success=False,
                    duration_ms=duration_ms,
                    error=str(e)
                )
                
                # Не останавливаем выполнение, добавляем ошибку в состояние
                state.add_error(agent_name, str(e))
                return state
                
        return wrapper
    return decorator

# Использование декоратора
@log_agent_execution("SecurityAgent")
def security_node(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """Агент автоматически логирует свою работу"""
    # Бизнес-логика агента
    # Логирование происходит автоматически
    pass
```

### **Метрики и мониторинг:**

```python
from dataclasses import dataclass
from typing import Counter
import time

@dataclass
class SystemMetrics:
    """Ключевые метрики работы системы"""
    
    # Производительность
    avg_processing_time_ms: float
    tokens_processed_per_hour: int
    api_success_rate: float
    
    # Качество
    decisions_made: int
    high_confidence_decisions: int
    scam_tokens_detected: int
    
    # Надежность  
    agents_success_rate: Dict[str, float]
    api_errors_per_hour: int
    system_uptime_percentage: float

class MetricsCollector:
    """Сборщик метрик работы системы"""
    
    def __init__(self):
        self.metrics = {
            'processing_times': [],
            'api_calls': Counter(),
            'api_errors': Counter(), 
            'agent_successes': Counter(),
            'agent_errors': Counter(),
            'decisions': Counter(),
            'start_time': time.time()
        }
    
    def record_processing_time(self, contract_address: str, duration_ms: int):
        """Записать время обработки токена"""
        self.metrics['processing_times'].append({
            'contract_address': contract_address,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })
    
    def record_api_call(self, api_name: str, success: bool):
        """Записать API вызов"""
        if success:
            self.metrics['api_calls'][api_name] += 1
        else:
            self.metrics['api_errors'][api_name] += 1
    
    def record_agent_execution(self, agent_name: str, success: bool):
        """Записать выполнение агента"""
        if success:
            self.metrics['agent_successes'][agent_name] += 1
        else:
            self.metrics['agent_errors'][agent_name] += 1
    
    def record_decision(self, decision: str, confidence: float):
        """Записать принятое решение"""
        self.metrics['decisions'][decision] += 1
        if confidence > 0.7:
            self.metrics['decisions']['high_confidence'] += 1
    
    def get_current_metrics(self) -> SystemMetrics:
        """Получить текущие метрики системы"""
        
        # Рассчитываем производительность
        processing_times = [p['duration_ms'] for p in self.metrics['processing_times']]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Рассчитываем надежность API
        total_api_calls = sum(self.metrics['api_calls'].values())
        total_api_errors = sum(self.metrics['api_errors'].values())
        api_success_rate = total_api_calls / (total_api_calls + total_api_errors) if (total_api_calls + total_api_errors) > 0 else 1.0
        
        # Рассчитываем надежность агентов
        agents_success_rate = {}
        for agent_name in set(list(self.metrics['agent_successes'].keys()) + list(self.metrics['agent_errors'].keys())):
            successes = self.metrics['agent_successes'][agent_name]
            errors = self.metrics['agent_errors'][agent_name] 
            total = successes + errors
            agents_success_rate[agent_name] = successes / total if total > 0 else 1.0
        
        # Рассчитываем uptime
        uptime_seconds = time.time() - self.metrics['start_time']
        uptime_percentage = 100.0  # Упрощенно, в реальности нужно отслеживать downtime
        
        return SystemMetrics(
            avg_processing_time_ms=avg_processing_time,
            tokens_processed_per_hour=len(processing_times),  # Упрощенно
            api_success_rate=api_success_rate,
            decisions_made=sum(self.metrics['decisions'].values()),
            high_confidence_decisions=self.metrics['decisions']['high_confidence'],
            scam_tokens_detected=self.metrics['decisions']['SCAM'],
            agents_success_rate=agents_success_rate,
            api_errors_per_hour=sum(self.metrics['api_errors'].values()),  # Упрощенно
            system_uptime_percentage=uptime_percentage
        )

# Глобальный экземпляр сборщика метрик
metrics_collector = MetricsCollector()

# Health check endpoint
def get_system_health() -> Dict[str, Any]:
    """Endpoint для проверки здоровья системы"""
    metrics = metrics_collector.get_current_metrics()
    
    # Определяем статус системы на основе метрик
    status = "healthy"
    issues = []
    
    if metrics.api_success_rate < 0.95:
        status = "degraded" 
        issues.append(f"Low API success rate: {metrics.api_success_rate:.2%}")
    
    if metrics.avg_processing_time_ms > 30000:  # 30 секунд
        status = "degraded"
        issues.append(f"High processing time: {metrics.avg_processing_time_ms}ms")
    
    for agent_name, success_rate in metrics.agents_success_rate.items():
        if success_rate < 0.90:
            status = "degraded"
            issues.append(f"Agent {agent_name} success rate: {success_rate:.2%}")
    
    return {
        "status": status,
        "timestamp": time.time(),
        "metrics": metrics.__dict__,
        "issues": issues
    }
```

---

## 🔄 **ПРИНЦИП #7: ВОСПРОИЗВОДИМОСТЬ И ВЕРСИОНИРОВАНИЕ (MLOps)**

### **Суть принципа:**
**"Любое решение, принятое системой, должно быть полностью воспроизводимым. Мы должны иметь возможность вернуться назад во времени и понять, почему был дан именно такой результат."**

### **Почему это критично:**
- ✅ **Отладка моделей:** Если модель дала неверный прогноз, нам нужно точно знать, на каких данных и какой версией модели он был сделан
- ✅ **Анализ эффективности:** Чтобы понять, почему старая версия модели работала лучше или хуже, нужно уметь воспроизводить ее результаты
- ✅ **Аудит и доверие:** Вы должны быть в состоянии доказать (в первую очередь себе), почему система порекомендовала купить тот или иной токен
- ✅ **Защита от "сломалось после обновления":** Гарантирует, что вы всегда можете откатиться к предыдущей рабочей версии не только кода, но и моделей/данных

### **Как применяется в нашей системе:**

#### **Версионирование моделей и данных:**
```python
# Использование DVC (Data Version Control) для версионирования
# dvc.yaml конфигурация
stages:
  train_success_predictor:
    cmd: python train_model.py
    deps:
    - data/training_set.csv
    - src/models/success_predictor.py
    outs:
    - models/success_predictor_v1.2.0.pkl
    metrics:
    - metrics/accuracy.json
```

#### **Расширенное состояние для воспроизводимости:**
```python
# Дополненная модель CryptoAnalysisState
class CryptoAnalysisState(BaseModel):
    # ... все предыдущие поля ...
    
    # === ДАННЫЕ ДЛЯ ВОСПРОИЗВОДИМОСТИ ===
    model_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Версии ML моделей (e.g., {'success_predictor': 'v1.2.0'})"
    )
    git_commit_hash: Optional[str] = Field(
        None,
        description="Git commit hash для воспроизводимости кода"
    )
    data_snapshot_id: Optional[str] = Field(
        None,
        description="ID снимка данных для воспроизводимости"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Точное время анализа"
    )
    environment_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Информация об окружении (версии библиотек и т.д.)"
    )
```

#### **Пример использования в агенте:**
```python
# Дополненный Risk Assessment Agent
class RiskAssessmentAgent:
    def __init__(self):
        # Версия модели загружается из конфига или файла
        self.model_version = "v1.2.0"
        self.success_predictor = load_model(f'models/token_success_predictor_{self.model_version}.pkl')
        
    def assess(self, state: CryptoAnalysisState) -> CryptoAnalysisState:
        """Оценка рисков с полным логированием для воспроизводимости"""
        
        # ЗАПИСЫВАЕМ ВЕРСИИ ИСПОЛЬЗОВАННЫХ КОМПОНЕНТОВ
        state.model_versions['success_predictor'] = self.model_version
        state.git_commit_hash = get_current_git_hash()  # Утилитарная функция
        state.environment_info = {
            'python_version': sys.version,
            'sklearn_version': sklearn.__version__,
            'model_file_hash': get_file_hash(f'models/token_success_predictor_{self.model_version}.pkl')
        }
        
        # Выполняем анализ
        features = extract_features(state)
        risk_prediction = self.success_predictor.predict_proba(features)
        
        # Сохраняем ВХОДНЫЕ ДАННЫЕ для модели (для воспроизводимости)
        state.risk_assessment = RiskAssessmentReport(
            contract_address=state.contract_address,
            success_probability=risk_prediction[1],
            model_version=self.model_version,
            input_features=features.to_dict(),  # Сохраняем входные данные
            feature_importance=get_feature_importance(self.success_predictor),
            assessment_timestamp=datetime.now()
        )
        
        return state

def get_current_git_hash() -> str:
    """Получить хеш текущего git коммита"""
    try:
        import subprocess
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                               capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "unknown"

def get_file_hash(filepath: str) -> str:
    """Получить хеш файла для проверки целостности"""
    import hashlib
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
```

#### **Система воспроизводимости:**
```python
class ReproducibilityManager:
    """Менеджер для воспроизведения результатов анализа"""
    
    def save_analysis_snapshot(self, state: CryptoAnalysisState):
        """Сохранить полный снимок анализа для последующего воспроизведения"""
        snapshot = {
            'state': state.dict(),
            'models': {name: self._copy_model_file(name, version) 
                      for name, version in state.model_versions.items()},
            'environment': state.environment_info,
            'timestamp': state.analysis_timestamp.isoformat()
        }
        
        snapshot_id = f"analysis_{state.contract_address}_{int(state.analysis_timestamp.timestamp())}"
        
        # Сохраняем в архив для долгосрочного хранения
        with open(f"data/analysis_snapshots/{snapshot_id}.json", 'w') as f:
            json.dump(snapshot, f, indent=2)
            
        return snapshot_id
    
    def reproduce_analysis(self, snapshot_id: str) -> CryptoAnalysisState:
        """Воспроизвести анализ на основе сохраненного снимка"""
        with open(f"data/analysis_snapshots/{snapshot_id}.json", 'r') as f:
            snapshot = json.load(f)
        
        # Восстанавливаем состояние
        state = CryptoAnalysisState(**snapshot['state'])
        
        # Проверяем совместимость моделей
        for model_name, version in state.model_versions.items():
            current_model_path = f"models/{model_name}_{version}.pkl"
            if not os.path.exists(current_model_path):
                raise ReproducibilityError(f"Model {model_name} v{version} not found")
        
        return state
```

---

## 💸 **ПРИНЦИП #8: УПРАВЛЕНИЕ ЗАТРАТАМИ И БЕЗОПАСНОСТЬ**

### **Суть принципа:**
**"Система должна быть защищена от непредвиденных расходов и внешних атак. Мы должны контролировать затраты и обезопасить наши API-ключи."**

### **Почему это критично:**
- ✅ **Финансовая безопасность:** Ошибка в коде не должна приводить к тысячам запросов к платному API и огромным счетам
- ✅ **Защита от злоупотреблений:** Если система будет иметь внешний интерфейс, ее нужно защитить от DoS-атак
- ✅ **Безопасность ключей:** Компрометация API-ключей может привести к финансовым и репутационным потерям
- ✅ **Прогнозируемость расходов:** Вы всегда должны знать, сколько стоит работа вашей системы

### **Как применяется в нашей системе:**

#### **Централизованное управление секретами:**
```python
# config/secrets_manager.py
from cryptography.fernet import Fernet
import os
from typing import Dict, Optional

class SecretsManager:
    """Безопасное управление API ключами и секретами"""
    
    def __init__(self):
        # В production используем внешние сервисы (Vault, AWS Secrets Manager)
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            raise SecurityError("ENCRYPTION_KEY must be set")
        
        self.fernet = Fernet(self.encryption_key.encode())
        self._secrets_cache = {}
    
    def get_api_key(self, service_name: str) -> str:
        """Получить API ключ для сервиса"""
        if service_name in self._secrets_cache:
            return self._secrets_cache[service_name]
        
        # В development читаем из .env
        if os.getenv('ENV') == 'development':
            key = os.getenv(f'{service_name.upper()}_API_KEY')
            if not key:
                raise SecurityError(f"API key for {service_name} not found")
            return key
        
        # В production загружаем из зашифрованного хранилища
        encrypted_key = self._load_encrypted_secret(service_name)
        decrypted_key = self.fernet.decrypt(encrypted_key.encode()).decode()
        
        self._secrets_cache[service_name] = decrypted_key
        return decrypted_key
    
    def rotate_api_key(self, service_name: str, new_key: str):
        """Ротация API ключей"""
        encrypted_key = self.fernet.encrypt(new_key.encode())
        self._save_encrypted_secret(service_name, encrypted_key.decode())
        
        # Инвалидируем кеш
        if service_name in self._secrets_cache:
            del self._secrets_cache[service_name]

# Глобальный менеджер секретов
secrets_manager = SecretsManager()
```

#### **Система контроля затрат:**
```python
# monitoring/cost_tracker.py
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

class CostTracker:
    """Система отслеживания и контроля затрат на API вызовы"""
    
    def __init__(self, daily_budget_usd: float = 50.0):
        self.daily_budget = daily_budget_usd
        self.monthly_budget = daily_budget_usd * 30
        
        # Отслеживание затрат по дням
        self.daily_costs = defaultdict(Counter)
        self.monthly_costs = Counter()
        
        # Цены API (в USD)
        self.api_prices = {
            'openai_gpt4': 0.03 / 1000,  # За 1000 токенов
            'openai_gpt35': 0.002 / 1000,
            'coingecko_pro': 0.01,  # За вызов
            'dexscreener_pro': 0.005,
            'goplus_pro': 0.002,
            'etherscan_api': 0.0,  # Бесплатный
            'telegram_bot': 0.0
        }
        
        # Лимиты по API (вызовов в час)
        self.rate_limits = {
            'openai_gpt4': 200,
            'coingecko_pro': 1000,
            'etherscan_api': 5000
        }
        
        self.hourly_calls = defaultdict(lambda: defaultdict(int))
        self.logger = logging.getLogger(__name__)
    
    def record_api_call(self, api_name: str, cost_units: int = 1, 
                       metadata: Dict[str, Any] = None) -> bool:
        """Записать API вызов и проверить лимиты"""
        current_time = datetime.now()
        today = current_time.date()
        current_hour = current_time.hour
        
        # Проверяем rate limits
        if self._is_rate_limited(api_name, current_hour):
            self.logger.warning(f"Rate limit exceeded for {api_name}")
            return False
        
        # Рассчитываем стоимость
        if api_name in self.api_prices:
            cost = self.api_prices[api_name] * cost_units
            
            # Проверяем бюджет
            if self._would_exceed_budget(cost, today):
                self.logger.error(f"Budget would be exceeded for {api_name} call")
                return False
            
            # Записываем затраты
            self.daily_costs[today][api_name] += cost
            self.monthly_costs[api_name] += cost
            
            # Записываем метрики для rate limiting
            self.hourly_calls[current_hour][api_name] += 1
            
            # Логируем
            self.logger.info(f"API call recorded: {api_name}, cost: ${cost:.4f}, units: {cost_units}")
            
            return True
        else:
            self.logger.warning(f"Unknown API: {api_name}")
            return False
    
    def _is_rate_limited(self, api_name: str, current_hour: int) -> bool:
        """Проверить превышение rate limits"""
        if api_name not in self.rate_limits:
            return False
        
        current_calls = self.hourly_calls[current_hour][api_name]
        return current_calls >= self.rate_limits[api_name]
    
    def _would_exceed_budget(self, additional_cost: float, today) -> bool:
        """Проверить превышение бюджета"""
        daily_total = sum(self.daily_costs[today].values())
        return (daily_total + additional_cost) > self.daily_budget
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Получить сводку по затратам"""
        today = datetime.now().date()
        daily_total = sum(self.daily_costs[today].values())
        monthly_total = sum(self.monthly_costs.values())
        
        return {
            'daily_spent': daily_total,
            'daily_budget': self.daily_budget,
            'daily_remaining': self.daily_budget - daily_total,
            'monthly_spent': monthly_total,
            'monthly_budget': self.monthly_budget,
            'breakdown_by_api': dict(self.daily_costs[today]),
            'budget_utilization_percent': (daily_total / self.daily_budget) * 100
        }
    
    def is_budget_healthy(self) -> tuple[bool, str]:
        """Проверить состояние бюджета"""
        today = datetime.now().date()
        daily_spent = sum(self.daily_costs[today].values())
        utilization = (daily_spent / self.daily_budget) * 100
        
        if utilization > 90:
            return False, f"CRITICAL: {utilization:.1f}% budget used"
        elif utilization > 70:
            return True, f"WARNING: {utilization:.1f}% budget used"
        else:
            return True, f"HEALTHY: {utilization:.1f}% budget used"

# Глобальный трекер затрат
cost_tracker = CostTracker()
```

#### **Декораторы для защищенных API вызовов:**
```python
# tools/api_protection.py
from functools import wraps
from typing import Callable, Any
import time

def protected_api_call(api_name: str, cost_units: int = 1):
    """Декоратор для защиты API вызовов от превышения бюджета"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Проверяем бюджет и rate limits
            if not cost_tracker.record_api_call(api_name, cost_units):
                # Если превышен лимит - возвращаем fallback или кешированный результат
                fallback_result = get_fallback_result(api_name, args, kwargs)
                if fallback_result is not None:
                    return fallback_result
                else:
                    raise BudgetExceededError(f"Cannot call {api_name}: budget or rate limit exceeded")
            
            # Выполняем реальный API вызов
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Логируем успешный вызов
                logging.getLogger(__name__).info(
                    f"API call successful: {api_name}, duration: {duration:.2f}s"
                )
                
                # Кешируем результат для возможного fallback
                cache_api_result(api_name, args, kwargs, result)
                
                return result
                
            except Exception as e:
                logging.getLogger(__name__).error(
                    f"API call failed: {api_name}, error: {str(e)}"
                )
                raise
                
        return wrapper
    return decorator

# Пример использования
@protected_api_call('coingecko_pro', cost_units=1)
def fetch_token_price(token_id: str) -> float:
    """Защищенный вызов API CoinGecko"""
    api_key = secrets_manager.get_api_key('coingecko')
    # ... реальный API вызов ...
    return price

@protected_api_call('openai_gpt4', cost_units=1500)  # Примерное количество токенов
def analyze_project_whitepaper(whitepaper_text: str) -> str:
    """Защищенный анализ whitepaper через GPT-4"""
    api_key = secrets_manager.get_api_key('openai')
    # ... вызов OpenAI API ...
    return analysis
```

#### **Мониторинг безопасности:**
```python
# monitoring/security_monitor.py
class SecurityMonitor:
    """Мониторинг безопасности системы"""
    
    def __init__(self):
        self.failed_auth_attempts = Counter()
        self.suspicious_activities = []
        self.api_usage_anomalies = []
    
    def detect_anomalies(self):
        """Детекция аномалий в использовании системы"""
        
        # Детекция аномального использования API
        cost_summary = cost_tracker.get_cost_summary()
        
        if cost_summary['budget_utilization_percent'] > 150:  # Превышение на 50%
            self.api_usage_anomalies.append({
                'timestamp': datetime.now(),
                'type': 'budget_exceeded',
                'details': cost_summary
            })
            
            # Отправляем экстренное уведомление
            self._send_security_alert(
                "Budget significantly exceeded",
                f"Current utilization: {cost_summary['budget_utilization_percent']:.1f}%"
            )
    
    def _send_security_alert(self, title: str, message: str):
        """Отправить уведомление о проблеме безопасности"""
        # Отправляем через Telegram или email
        pass
```

---

## 📚 **ЗАКЛЮЧЕНИЕ: ПРАКТИЧЕСКОЕ ПРИМЕНЕНИЕ ПРИНЦИПОВ**

### **Чек-лист архитектурных решений:**

При принятии любого архитектурного решения в проекте, задавайте себе эти вопросы:

```python
ARCHITECTURE_CHECKLIST = {
    'complexity_assessment': [
        "Это самое простое решение для данной задачи?",
        "Можно ли решить проблему без дополнительных абстракций?", 
        "Будет ли это понятно через 6 месяцев?"
    ],
    'isolation_verification': [
        "Можно ли этот компонент протестировать изолированно?",
        "Что произойдет, если этот компонент сломается?",
        "Есть ли fallback сценарий?"
    ],
    'contract_validation': [
        "Есть ли Pydantic модели для всех входных/выходных данных?",
        "Будет ли breaking change обнаружен автоматически?",
        "Четко ли определены ответственности компонентов?"
    ],
    'observability_check': [
        "Логируется ли важная информация структурированно?",
        "Есть ли метрики для мониторинга производительности?",
        "Можно ли диагностировать проблемы по логам?"
    ],
    'rollback_safety': [
        "Есть ли стабильная версия для отката?",
        "Сохранится ли работоспособность при откате?",
        "Задокументированы ли шаги для rollback?"
    ]
}
```

### **Архитектурные Anti-паттерны (чего избегать):**

```python
ANTI_PATTERNS_TO_AVOID = {
    'god_object': {
        'description': 'Один класс/функция делает слишком много',
        'example': 'Класс CryptoAnalyzer с 50 методами',
        'solution': 'Разбить на специализированные агенты'
    },
    'hidden_dependencies': {
        'description': 'Компоненты неявно зависят друг от друга',
        'example': 'SecurityAgent читает данные из глобальной переменной',
        'solution': 'Явные параметры функций, Pydantic модели'
    },
    'silent_failures': {
        'description': 'Ошибки не логируются или игнорируются',
        'example': 'try-catch с pass в обработчике',
        'solution': 'Структурированное логирование всех ошибок'
    },
    'configuration_hell': {
        'description': 'Слишком много настроек в разных местах',
        'example': 'Константы разбросаны по всему коду',
        'solution': 'Централизованная конфигурация через Settings'
    },
    'testing_afterthought': {
        'description': 'Тесты пишутся после кода',
        'example': 'Код нельзя протестировать изолированно',
        'solution': 'TDD или минимум testable design'
    }
}
```

### **Эволюция архитектуры:**

```python
EVOLUTION_ROADMAP = {
    'phase_1_mvp': {
        'focus': 'Работающий прототип',
        'compromises_allowed': ['Некоторое дублирование кода', 'Простые алгоритмы'],
        'non_negotiable': ['Pydantic контракты', 'Структурированное логирование']
    },
    'phase_2_optimization': {
        'focus': 'Производительность и качество',
        'improvements': ['Оптимизация API вызовов', 'Advanced ML модели'],
        'maintain': ['Архитектурные принципы', 'Обратная совместимость']
    },
    'phase_3_scale': {
        'focus': 'Масштабирование и надежность',
        'additions': ['Horizontal scaling', 'Advanced monitoring'],
        'preserve': ['Простота отдельных компонентов', 'Изоляция агентов']
    }
}
```

---

**🎯 Главное правило:** 

> **"Архитектура должна упрощать разработку, а не усложнять ее.  
> Если архитектурное решение требует объяснения на двух страницах,  
> вероятно, оно слишком сложное."**

Эти принципы - не догма, а инструменты. Используйте их для создания **понятной, надежной и масштабируемой** системы, которая будет служить основой для достижения бизнес-целей проекта.

---

*Документ создан: 31 июля 2025*  
*Статус: ARCHITECTURAL FOUNDATION*  
*Применимость: Все этапы разработки мультиагентной системы*  
*Next: Практическое применение в коде* 🚀