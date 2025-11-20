"""
Патч: Добавить метод calculate_discovery_score в RealisticScoringMatrix

Нужно добавить в файл realistic_scoring.py в класс RealisticScoringMatrix:
"""

DISCOVERY_METHOD = '''
    def calculate_discovery_score(self) -> int:
        """Оценка Discovery данных (максимум 40 баллов)"""
        score = 0
        
        # Главный источник баллов - качество Discovery анализа
        if self.indicators.discovery_score >= 80:
            score += 35  # Отличный Discovery score
        elif self.indicators.discovery_score >= 60:
            score += 25  # Хороший Discovery score  
        elif self.indicators.discovery_score >= 40:
            score += 15  # Средний Discovery score
        elif self.indicators.discovery_score >= 20:
            score += 5   # Низкий но приемлемый
        
        # Бонус за очень высокое качество
        if self.indicators.discovery_score >= 90:
            score += 5
        
        return min(score, 40)
'''

GET_DETAILED_ANALYSIS_UPDATE = '''
Также нужно обновить метод get_detailed_analysis():

Найти строку:
    narrative_score = self.calculate_narrative_score()

Заменить на:
    # narrative_score = self.calculate_narrative_score()  # Временно отключен
    discovery_score = self.calculate_discovery_score()   # Используем Discovery вместо narrative

И обновить:
    total_score = discovery_score + security_score + volume_score + onchain_score

И в category_scores:
    'discovery': discovery_score,  # Вместо narrative
    'security': security_score,
    'volume': volume_score,
    'onchain': onchain_score
'''

print("🔧 ПАТЧ ДЛЯ DISCOVERY SCORING:")
print("\n1. Добавить метод в RealisticScoringMatrix:")
print(DISCOVERY_METHOD)
print("\n2. Обновления в get_detailed_analysis:")
print(GET_DETAILED_ANALYSIS_UPDATE)
