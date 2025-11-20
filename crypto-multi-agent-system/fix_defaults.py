"""
Патч для исправления defaults в RealisticPumpIndicators
Делает CoinGecko и GoPlus факультативными
"""

CURRENT_DEFAULTS = """
    is_honeypot: bool = Field(default=True, description="Honeypot проверка")
    is_open_source: bool = Field(default=False, description="Контракт верифицирован")
    buy_tax_percent: float = Field(default=100, ge=0, le=100, description="Налог на покупку %")
    sell_tax_percent: float = Field(default=100, ge=0, le=100, description="Налог на продажу %")
"""

FIXED_DEFAULTS = """
    # ФАКУЛЬТАТИВНО: если GoPlus недоступен, используем нейтральные defaults
    is_honeypot: bool = Field(default=False, description="Honeypot проверка")
    is_open_source: bool = Field(default=True, description="Контракт верифицирован")
    buy_tax_percent: float = Field(default=5.0, ge=0, le=100, description="Налог на покупку %")
    sell_tax_percent: float = Field(default=5.0, ge=0, le=100, description="Налог на продажу %")
"""

print("🔧 ИСПРАВЛЕНИЯ ДЛЯ ФАКУЛЬТАТИВНЫХ СИГНАЛОВ:")
print("\n❌ Текущие defaults (убивают новые токены):")
print(CURRENT_DEFAULTS)
print("\n✅ Исправленные defaults (нейтральные):")
print(FIXED_DEFAULTS)
print("\n📝 Нужно заменить в файле: agents/pump_analysis/realistic_scoring.py")
print("Строки примерно 28-31")
