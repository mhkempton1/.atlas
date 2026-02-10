import asyncio
from core.app import app
import sys

async def test_lifespan():
    print("Testing lifespan startup...")
    try:
        # Triggering lifespan startup
        async with app.router.lifespan_context(app) as ctx:
            print("Lifespan startup complete and yielded.")
            await asyncio.sleep(1) # Let it run for a bit
            print("Finished waiting in lifespan context.")
    except Exception as e:
        print(f"Lifespan failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lifespan())
