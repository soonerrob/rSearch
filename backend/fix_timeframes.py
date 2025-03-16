import asyncio

from app.core.database import AsyncSessionLocal
from app.models.audience import Audience
from sqlmodel import select, update


async def fix_timeframes():
    """Fix invalid timeframe values in audiences table"""
    async with AsyncSessionLocal() as session:
        # Get all audiences
        result = await session.execute(select(Audience))
        audiences = result.scalars().all()
        
        # Valid timeframes
        valid_timeframes = {'hour', 'day', 'week', 'month', 'year', 'all'}
        
        # Check and fix invalid timeframes
        fixed_count = 0
        for audience in audiences:
            if audience.timeframe not in valid_timeframes:
                print(f"Found invalid timeframe '{audience.timeframe}' for audience {audience.id} ({audience.name})")
                # Set to default of 'year'
                audience.timeframe = 'year'
                fixed_count += 1
        
        if fixed_count > 0:
            print(f"\nFixing {fixed_count} audiences with invalid timeframes...")
            await session.commit()
            print("Done!")
        else:
            print("\nNo invalid timeframes found!")

if __name__ == "__main__":
    asyncio.run(fix_timeframes()) 