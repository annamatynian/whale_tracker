# Database Models - Modular Architecture

This directory contains the complete database layer for Whale Tracker, following **modular and abstracted design principles**.

## Architecture Overview

```
models/
├── database.py         # SQLAlchemy ORM models (PostgreSQL/SQLite tables)
├── schemas.py          # Pydantic validation schemas (input/output validation)
├── db_connection.py    # Database connection management (sync + async)
├── __init__.py         # Public exports
└── README.md          # This file
```

## Layer Separation

### 1. SQLAlchemy Models (`database.py`)

**Purpose**: Define database tables and relationships

**Models**:
- `OneHopDetection`: One-hop detection results with multi-signal analysis
- `Transaction`: Ethereum transaction data
- `IntermediateAddress`: Intermediate address profiles
- `WhaleAlert`: Whale alerts sent to users
- `SignalMetrics`: Signal performance tracking

**Usage**:
```python
from models.database import OneHopDetection, Transaction

# Create new detection
detection = OneHopDetection(
    whale_address='0x...',
    intermediate_address='0x...',
    total_confidence=85
)
```

### 2. Pydantic Schemas (`schemas.py`)

**Purpose**: Input validation and API serialization

**Schemas**:
- `*Create`: For creating new records (input validation)
- `*Response`: For API responses (output serialization)
- `*Filter`: For query filtering
- `*Update`: For updating records

**Usage**:
```python
from models.schemas import OneHopDetectionCreate

# Validate input
detection_data = OneHopDetectionCreate(
    whale_address='0x...',
    intermediate_address='0x...',
    total_confidence=85,  # Validated: must be 0-100
    whale_amount_eth=Decimal('10.5')
)
```

### 3. Database Connection (`db_connection.py`)

**Purpose**: Manage database connections (abstraction layer)

**Classes**:
- `DatabaseConfig`: Configuration abstraction
- `DatabaseManager`: Synchronous connection management
- `AsyncDatabaseManager`: Asynchronous connection management

**Usage**:

#### Synchronous Operations
```python
from models.db_connection import create_sync_db_manager, DatabaseConfig
from config.settings import get_settings

# Create manager from settings
settings = get_settings()
db_manager = create_sync_db_manager(settings=settings)

# Use with context manager
with db_manager.session() as session:
    detections = session.query(OneHopDetection).all()
```

#### Asynchronous Operations
```python
from models.db_connection import create_async_db_manager

# Create async manager
async_db = create_async_db_manager(settings=settings)

# Use with async context manager
async with async_db.session() as session:
    result = await session.execute(query)
    detections = result.scalars().all()
```

## Why SQLAlchemy + PostgreSQL?

**Question**: "SQLAlchemy или PostgreSQL?"

**Answer**: **ОБА вместе!**

- **PostgreSQL** = База данных (где данные хранятся на диске)
- **SQLAlchemy** = ORM библиотека (переводит Python → SQL → PostgreSQL)
- **Pydantic** = Валидация (проверяет данные перед сохранением)

**Data Flow**:
```
User Input → Pydantic Schema (validation)
           → SQLAlchemy Model
           → PostgreSQL Database
```

## Configuration

### Environment Variables

```bash
# Database type
DB_TYPE=postgresql  # or sqlite

# PostgreSQL settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=whale_tracker
DB_USER=postgres
DB_PASSWORD=your_password

# Connection pool
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO=false  # Set to true for SQL debugging
```

### From Code

```python
from models.db_connection import DatabaseConfig

# Manual configuration
config = DatabaseConfig(
    host='localhost',
    port=5432,
    database='whale_tracker',
    user='postgres',
    password='secure_password',
    pool_size=5
)

# From settings
from config.settings import get_settings
settings = get_settings()
config = DatabaseConfig.from_env(settings)
```

## Database Migrations

Migrations are managed with **Alembic** (see `alembic/README.md`).

### Create Initial Schema

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### After Model Changes

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Added new field to OneHopDetection"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head
```

## Usage Examples

### Example 1: Save One-Hop Detection

```python
from models.database import OneHopDetection
from models.schemas import OneHopDetectionCreate
from models.db_connection import create_sync_db_manager
from config.settings import get_settings
from decimal import Decimal
from datetime import datetime

# Get database manager
settings = get_settings()
db = create_sync_db_manager(settings=settings)

# Validate input with Pydantic
detection_data = OneHopDetectionCreate(
    whale_address='0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    whale_tx_hash='0x123...',
    intermediate_address='0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B',
    whale_tx_block=18000000,
    whale_tx_timestamp=datetime.utcnow(),
    whale_amount_wei='1000000000000000000',
    whale_amount_eth=Decimal('1.0'),
    time_correlation_score=90,
    gas_correlation_score=95,
    nonce_correlation_score=95,
    total_confidence=93,
    num_signals_used=3,
    detection_method='advanced'
)

# Convert to SQLAlchemy model
detection = OneHopDetection(**detection_data.model_dump())

# Save to database
with db.session() as session:
    session.add(detection)
    session.commit()
    print(f"Detection saved with ID: {detection.id}")
```

### Example 2: Query Detections

```python
from sqlalchemy import select
from models.database import OneHopDetection

with db.session() as session:
    # Get high-confidence detections
    stmt = select(OneHopDetection).where(
        OneHopDetection.total_confidence >= 80
    ).order_by(OneHopDetection.detected_at.desc())

    result = session.execute(stmt)
    detections = result.scalars().all()

    for det in detections:
        print(f"{det.whale_address[:8]}... → "
              f"{det.intermediate_address[:8]}... "
              f"({det.total_confidence}%)")
```

### Example 3: Async Operations

```python
import asyncio
from models.db_connection import create_async_db_manager
from models.database import OneHopDetection

async def get_recent_detections():
    async_db = create_async_db_manager(settings=settings)

    async with async_db.session() as session:
        result = await session.execute(
            select(OneHopDetection)
            .order_by(OneHopDetection.detected_at.desc())
            .limit(10)
        )
        return result.scalars().all()

# Run async function
detections = asyncio.run(get_recent_detections())
```

## Testing

Unit tests for database models (to be created):

```bash
# Test database models
pytest tests/unit/test_database_models.py

# Test Pydantic schemas
pytest tests/unit/test_schemas.py

# Test database connection
pytest tests/unit/test_db_connection.py
```

## Database Tables

### one_hop_detections
- Stores complete one-hop detection results
- Includes all signal scores (time, gas, nonce, amount, address)
- Composite confidence calculation
- Alert tracking

### transactions
- Ethereum transaction data
- Gas information (legacy + EIP-1559)
- Nonce tracking for correlation

### intermediate_addresses
- Address profiles (fresh_burner, professional, etc.)
- Usage statistics
- Confidence scores

### whale_alerts
- Alert history
- Delivery status tracking
- Multi-channel support (Telegram, email, webhook, Discord)

### signal_metrics
- Performance tracking for each detection signal
- Precision and accuracy metrics
- Continuous improvement data

## Integration with Analyzers

Database models are designed to integrate seamlessly with existing analyzers:

```python
from src.analyzers.nonce_tracker import NonceTracker
from src.analyzers.gas_correlator import GasCorrelator
from src.analyzers.address_profiler import AddressProfiler
from models.database import OneHopDetection
from models.db_connection import create_sync_db_manager

# Analyzers produce results
nonce_result = await nonce_tracker.check_nonce_sequence(whale_tx, intermediate_tx)
gas_result = gas_correlator.check_gas_correlation(whale_tx, intermediate_tx)
profile = await address_profiler.profile_address(address, block, timestamp)

# Save to database
detection = OneHopDetection(
    whale_address=whale_address,
    intermediate_address=intermediate_address,
    nonce_correlation_score=nonce_result.confidence,
    gas_correlation_score=gas_result.confidence,
    address_profile_score=profile.overall_confidence,
    total_confidence=(nonce_result.confidence + gas_result.confidence + profile.overall_confidence) // 3
)

with db.session() as session:
    session.add(detection)
    session.commit()
```

## Phase 2 Implementation

This database layer enables **Phase 2** features:

- ✅ **Historical data storage**: All detections, transactions, and profiles
- ✅ **Analytics**: Signal performance tracking
- ✅ **Alert history**: Complete audit trail
- ⏳ **Pattern analysis**: Database ready, analysis logic pending
- ⏳ **Machine learning**: Data collection infrastructure in place

## Best Practices

1. **Always use Pydantic schemas** for input validation
2. **Use context managers** for database sessions
3. **Test on development database** before production
4. **Run migrations** with Alembic, never modify schema directly
5. **Index optimization**: All foreign keys and search fields are indexed
6. **Connection pooling**: Automatically managed by db_connection.py

## Troubleshooting

### "Table doesn't exist"
```bash
# Create tables with migration
alembic upgrade head

# Or programmatically
from models.db_connection import create_sync_db_manager
db = create_sync_db_manager(settings=settings)
db.create_all_tables()
```

### "Connection refused"
- Check PostgreSQL is running: `systemctl status postgresql`
- Verify connection settings in `.env`
- Test connection: `psql -h localhost -U postgres -d whale_tracker`

### "Too many connections"
- Increase `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
- Check for connection leaks (always use context managers)

## Summary

**Модульная архитектура реализована полностью**:

1. ✅ **SQLAlchemy models** - Database tables (database.py)
2. ✅ **Pydantic schemas** - Input validation (schemas.py)
3. ✅ **Connection management** - Abstracted (db_connection.py)
4. ✅ **Migrations** - Alembic setup (alembic/)
5. ✅ **Configuration** - Integrated with config/settings.py
6. ✅ **Documentation** - Complete README + inline docs

**Ready for Phase 2 database implementation!** 🚀
