import asyncio
import logging
from datetime import datetime
from typing import List, Tuple

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'cleanup_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def get_orphaned_posts() -> List[Tuple[str, int]]:
    """Get list of orphaned posts grouped by subreddit"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT p.subreddit_name, COUNT(*) as post_count
                FROM redditpost p
                LEFT JOIN audience_subreddits a ON p.subreddit_name = a.subreddit_name
                WHERE a.subreddit_name IS NULL
                GROUP BY p.subreddit_name
                ORDER BY post_count DESC
            """)
        )
        return [(row.subreddit_name, row.post_count) for row in result.all()]

async def delete_orphaned_posts(subreddit_name: str) -> int:
    """Delete orphaned posts for a specific subreddit"""
    async with AsyncSessionLocal() as session:
        # Double check this subreddit is truly orphaned
        result = await session.execute(
            text("""
                SELECT COUNT(*) 
                FROM audience_subreddits 
                WHERE subreddit_name = :subreddit
            """),
            {"subreddit": subreddit_name}
        )
        if result.scalar() > 0:
            logger.warning(f"Subreddit {subreddit_name} is not orphaned! Skipping deletion.")
            return 0
        
        # Delete the orphaned posts
        result = await session.execute(
            text("""
                DELETE FROM redditpost 
                WHERE subreddit_name = :subreddit
                AND NOT EXISTS (
                    SELECT 1 FROM audience_subreddits 
                    WHERE subreddit_name = redditpost.subreddit_name
                )
                RETURNING id
            """),
            {"subreddit": subreddit_name}
        )
        deleted_count = len(result.all())
        await session.commit()
        return deleted_count

async def main():
    try:
        logger.info("Starting orphaned posts cleanup")
        
        # Get list of orphaned posts
        orphaned_posts = await get_orphaned_posts()
        if not orphaned_posts:
            logger.info("No orphaned posts found!")
            return
        
        logger.info(f"Found orphaned posts in {len(orphaned_posts)} subreddits:")
        for subreddit, count in orphaned_posts:
            logger.info(f"- {subreddit}: {count} posts")
        
        # Confirm before deletion
        total_posts = sum(count for _, count in orphaned_posts)
        print(f"\nWARNING: This will delete {total_posts} posts from {len(orphaned_posts)} subreddits.")
        confirm = input("Type 'yes' to confirm deletion: ")
        
        if confirm.lower() != 'yes':
            logger.info("Cleanup cancelled by user")
            return
        
        # Perform deletion
        total_deleted = 0
        for subreddit, expected_count in orphaned_posts:
            logger.info(f"Cleaning up {subreddit}...")
            deleted = await delete_orphaned_posts(subreddit)
            total_deleted += deleted
            logger.info(f"Deleted {deleted} posts from {subreddit}")
        
        logger.info(f"Cleanup completed. Total posts deleted: {total_deleted}")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main()) 