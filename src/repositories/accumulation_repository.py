"""
Accumulation Repository - Data persistence for accumulation metrics
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timedelta, UTC
from sqlalchemy import select, desc

from models.database import AccumulationMetric
from models.schemas import AccumulationMetricCreate


class AccumulationRepository(ABC):
    """Abstract repository для accumulation metrics."""
    
    @abstractmethod
    async def save_metric(self, metric: AccumulationMetricCreate) -> int:
        """Save metric, return ID."""
        pass
    
    @abstractmethod
    async def get_latest_score(self, network: str) -> Optional[float]:
        """Get most recent score for network."""
        pass
    
    @abstractmethod
    async def get_trend(
        self, 
        network: str, 
        days: int = 7
    ) -> List[AccumulationMetric]:
        """Get historical scores for trend analysis."""
        pass


class InMemoryAccumulationRepository(AccumulationRepository):
    """In-memory implementation для testing."""
    
    def __init__(self):
        self._metrics: List[dict] = []
        self._next_id = 1
    
    async def save_metric(self, metric: AccumulationMetricCreate) -> int:
        """Save to memory."""
        metric_dict = metric.model_dump()
        metric_dict['id'] = self._next_id
        metric_dict['calculated_at'] = datetime.now(UTC)
        self._metrics.append(metric_dict)
        self._next_id += 1
        return metric_dict['id']
    
    async def get_latest_score(self, network: str) -> Optional[float]:
        """Get latest score from memory."""
        network_metrics = [
            m for m in self._metrics 
            if m['network'] == network
        ]
        if not network_metrics:
            return None
        
        latest = max(network_metrics, key=lambda m: m['calculated_at'])
        return float(latest['score'])
    
    async def get_trend(
        self, 
        network: str, 
        days: int = 7
    ) -> List[dict]:
        """Get trend from memory."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return [
            m for m in self._metrics
            if m['network'] == network and m['calculated_at'] > cutoff
        ]


class SQLAccumulationRepository(AccumulationRepository):
    """SQL implementation для production."""
    
    def __init__(self, session):
        """Initialize with AsyncSession (like SnapshotRepository)."""
        self.session = session
    
    async def save_metric(self, metric: AccumulationMetricCreate) -> int:
        """Save to PostgreSQL."""
        db_metric = AccumulationMetric(**metric.model_dump())
        self.session.add(db_metric)
        await self.session.commit()
        await self.session.refresh(db_metric)
        return db_metric.id
    
    async def get_latest_score(self, network: str) -> Optional[float]:
        """Get latest score from PostgreSQL."""
        stmt = (
            select(AccumulationMetric)
            .where(AccumulationMetric.network == network)
            .order_by(desc(AccumulationMetric.calculated_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        metric = result.scalar_one_or_none()
        return float(metric.score) if metric else None
    
    async def get_trend(
        self, 
        network: str, 
        days: int = 7
    ) -> List[AccumulationMetric]:
        """Get trend from PostgreSQL."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        stmt = (
            select(AccumulationMetric)
            .where(
                AccumulationMetric.network == network,
                AccumulationMetric.calculated_at > cutoff
            )
            .order_by(desc(AccumulationMetric.calculated_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()