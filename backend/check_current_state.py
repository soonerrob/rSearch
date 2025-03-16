import asyncio
import os
import sys
from pathlib import Path

# Add debug logging
print("Current working directory:", os.getcwd())
print("Python path:", sys.path)

# Add the parent directory (where app/ is) to sys.path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from app.core.database import get_session
    from app.models.audience import Audience
    from app.models.post import Post
    from app.models.subreddit import Subreddit
    from sqlalchemy import func, select
    from sqlalchemy.orm import joinedload
    print("Successfully imported all modules")
except Exception as e:
    print("Error importing modules:", str(e))
    sys.exit(1)

async def check_current_state():
    try:
        print("Starting database check...")
        async for session in get_session():
            print("Got database session")
            # Query for audiences with their subreddits
            stmt = select(Audience).options(joinedload(Audience.subreddits))
            result = await session.execute(stmt)
            audiences = result.unique().scalars().all()

            print("\n=== Current Database State ===\n")
            
            if not audiences:
                print("No audiences found in the database.")
                return

            for audience in audiences:
                print(f"Audience: {audience.name} (ID: {audience.id})")
                print(f"Description: {audience.description}")
                print(f"Timeframe: {audience.timeframe}")
                print(f"Number of subreddits: {len(audience.subreddits)}")
                
                if audience.subreddits:
                    print("\nSubreddits:")
                    for subreddit in audience.subreddits:
                        # Count posts for this subreddit
                        post_count = await session.scalar(
                            select(func.count()).select_from(Post).where(Post.subreddit_id == subreddit.id)
                        )
                        print(f"- {subreddit.name} (ID: {subreddit.id}, Posts: {post_count})")
                print("\n" + "-"*50 + "\n")
            break  # We only need one session
    except Exception as e:
        print("Error during database check:", str(e))
        raise

if __name__ == "__main__":
    try:
        asyncio.run(check_current_state())
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print("Script failed:", str(e)) 