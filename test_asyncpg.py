"""Quick test: Verify asyncpg is working"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    url = "postgresql+asyncpg://postgres:Jayaasiri2185@localhost:5432/whale_tracker"
    try:
        engine = create_async_engine(url, echo=True)
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("✅ asyncpg works!")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
