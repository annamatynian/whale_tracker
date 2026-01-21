# tests/unit/test_accumulation_repository.py

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta, UTC
from models.schemas import AccumulationMetricCreate
from src.repositories.accumulation_repository import InMemoryAccumulationRepository

class TestAccumulationRepository:
    
    @pytest.mark.asyncio
    async def test_save_metric(self):
        """Тест сохранения метрики."""
        repo = InMemoryAccumulationRepository()
        
        metric = AccumulationMetricCreate(
            network="ethereum",
            score=0.75,
            addresses_analyzed=100,
            total_balance_change=Decimal("1234.56"),
            measurement_period_days=30
        )
        
        metric_id = await repo.save_metric(metric)
        
        assert metric_id == 1
        assert len(repo._metrics) == 1
    
    @pytest.mark.asyncio
    async def test_get_latest_score(self):
        """Тест получения последнего score."""
        repo = InMemoryAccumulationRepository()
        
        # Сохраняем две метрики
        metric1 = AccumulationMetricCreate(
            network="ethereum", score=0.5,
            addresses_analyzed=100,
            total_balance_change=Decimal("100")
        )
        metric2 = AccumulationMetricCreate(
            network="ethereum", score=0.8,
            addresses_analyzed=100,
            total_balance_change=Decimal("200")
        )
        
        await repo.save_metric(metric1)
        await asyncio.sleep(0.1)  # Разница по времени
        await repo.save_metric(metric2)
        
        latest = await repo.get_latest_score("ethereum")
        
        assert latest == 0.8  # Последний score
    
    @pytest.mark.asyncio
    async def test_get_latest_score_nonexistent(self):
        """Тест для несуществующей сети."""
        repo = InMemoryAccumulationRepository()
        
        latest = await repo.get_latest_score("bitcoin")
        
        assert latest is None
    
    @pytest.mark.asyncio
    async def test_get_trend(self):
        """Тест получения исторических данных."""
        repo = InMemoryAccumulationRepository()
        
        # Создаем метрики за последние 3 дня
        for i in range(3):
            metric = AccumulationMetricCreate(
                network="ethereum",
                score=0.5 + (i * 0.1),
                addresses_analyzed=100,
                total_balance_change=Decimal("100")
            )
            await repo.save_metric(metric)
            await asyncio.sleep(0.1)
        
        trend = await repo.get_trend("ethereum", days=7)
        
        assert len(trend) == 3
        # Проверяем что все за последние 7 дней
        cutoff = datetime.now(UTC) - timedelta(days=7)
        assert all(m['calculated_at'] > cutoff for m in trend)