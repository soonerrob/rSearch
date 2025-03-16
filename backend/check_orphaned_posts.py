import asyncio

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def check_orphaned_data():
    """Check for orphaned data in the database"""
    async with AsyncSessionLocal() as session:
        # Check for posts whose subreddits aren't in any audience
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
        orphaned_posts = result.all()
        
        print("\nOrphaned Posts (posts with no associated audience):")
        print("------------------------------------------------")
        if orphaned_posts:
            for row in orphaned_posts:
                print(f"Subreddit: {row.subreddit_name}, Posts: {row.post_count}")
        else:
            print("No orphaned posts found!")
            
        # Check for theme posts without themes
        result = await session.execute(
            text("""
                SELECT COUNT(*) as count
                FROM themepost tp
                LEFT JOIN theme t ON tp.theme_id = t.id
                WHERE t.id IS NULL
            """)
        )
        orphaned_theme_posts = result.scalar()
        
        print("\nOrphaned Theme Posts:")
        print("--------------------")
        if orphaned_theme_posts > 0:
            print(f"Found {orphaned_theme_posts} theme posts without associated themes")
        else:
            print("No orphaned theme posts found!")
            
        # Check for themes without audiences
        result = await session.execute(
            text("""
                SELECT COUNT(*) as count
                FROM theme t
                LEFT JOIN audiences a ON t.audience_id = a.id
                WHERE a.id IS NULL
            """)
        )
        orphaned_themes = result.scalar()
        
        print("\nOrphaned Themes:")
        print("--------------")
        if orphaned_themes > 0:
            print(f"Found {orphaned_themes} themes without associated audiences")
        else:
            print("No orphaned themes found!")

if __name__ == "__main__":
    asyncio.run(check_orphaned_data()) 