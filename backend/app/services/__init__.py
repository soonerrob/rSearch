from sqlalchemy.ext.asyncio import AsyncSession

from .reddit import RedditService


# Factory functions for services
def create_reddit_service(db: AsyncSession) -> RedditService:
    """Create a new instance of RedditService with the provided database session"""
    return RedditService(db=db)

# Export service classes for direct use in tests
__all__ = ['RedditService', 'create_reddit_service'] 
