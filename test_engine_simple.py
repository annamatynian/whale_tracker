"""Test SQLAlchemy async engine creation"""
import asyncio
import os

async def test():
    print("\n" + "="*70)
    print("Testing SQLAlchemy Async Engine")
    print("="*70)
    
    # Import AFTER function definition
    from sqlalchemy.ext.asyncio import create_async_engine
    
    db_user = "postgres"
    db_password = "Jayaasiri2185"
    db_host = "localhost"
    db_port = "5432"
    db_name = "whale_tracker"
    
    url = f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    print(f"\nDatabase URL: {url.replace(db_password, '***')}")
    
    try:
        print("\n1. Creating async engine...")
        engine = create_async_engine(url, echo=False)
        print("   ✅ Engine created")
        
        print("\n2. Testing connection...")
        from sqlalchemy import text
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"   ✅ Connected!")
            print(f"   PostgreSQL: {version.split(',')[0]}")
        
        print("\n3. Disposing engine...")
        await engine.dispose()
        print("   ✅ Done")
        
        print("\n" + "="*70)
        print("✅ TEST PASSED - asyncpg is working correctly")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
