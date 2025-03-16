import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from app.core.database import AsyncSessionLocal
from app.models import Subreddit
from sqlalchemy import select


async def restore_subreddits(backup_file: str):
    if not Path(backup_file).exists():
        raise FileNotFoundError(f"Backup file {backup_file} not found")
    
    with open(backup_file, 'r') as f:
        data = json.load(f)
    
    async with AsyncSessionLocal() as session:
        for subreddit_data in data:
            # Convert timezone-aware timestamps to naive UTC timestamps
            for field in ['created_at', 'updated_at', 'last_updated']:
                if subreddit_data.get(field):
                    # Parse the ISO format string to datetime
                    dt = datetime.fromisoformat(subreddit_data[field])
                    # Convert to UTC and remove timezone info
                    subreddit_data[field] = dt.astimezone().replace(tzinfo=None)
            
            subreddit = Subreddit(**subreddit_data)
            session.add(subreddit)
        
        await session.commit()
        print(f"Successfully restored subreddits from {backup_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore_db.py <backup_file>")
        sys.exit(1)
    
    asyncio.run(restore_subreddits(sys.argv[1])) 