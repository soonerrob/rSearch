import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db_session, get_reddit_service
from ..models import Subreddit
from ..schemas.subreddit import KeywordSuggestionResponse, SubredditResponse
from ..services.reddit import RedditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subreddits", tags=["subreddits"])

@router.get("/trending", response_model=List[SubredditResponse])
async def get_trending_subreddits(
    limit: int = 20,
    reddit_service: RedditService = Depends(get_reddit_service),
    session: AsyncSession = Depends(get_db_session)
) -> List[SubredditResponse]:
    """Get trending subreddits."""
    try:
        logger.info("Fetching trending subreddits")
        subreddits = await reddit_service.get_trending_subreddits(limit=limit)
        
        # Sync each subreddit to the database
        for subreddit in subreddits:
            try:
                await reddit_service.sync_subreddit_to_db(subreddit, session)
            except Exception as e:
                logger.error(f"Error syncing subreddit to database: {str(e)}")
                # Continue with other subreddits even if one fails
                continue
        
        # Convert models to response schema using model_validate
        responses = []
        for subreddit in subreddits:
            try:
                response = SubredditResponse.model_validate(subreddit)
                responses.append(response)
            except Exception as e:
                logger.error(f"Error serializing subreddit {subreddit.name}: {str(e)}")
                continue
                
        return responses
    except Exception as e:
        logger.error(f"Error in get_trending_subreddits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending subreddits: {str(e)}")

@router.get("/search", response_model=List[SubredditResponse])
async def search_subreddits(
    query: str,
    limit: int = 100,
    min_subscribers: Optional[int] = None,
    max_subscribers: Optional[int] = None,
    min_active_users: Optional[int] = None,
    max_active_users: Optional[int] = None,
    reddit_service: RedditService = Depends(get_reddit_service),
    session: AsyncSession = Depends(get_db_session)
) -> List[SubredditResponse]:
    """Search for subreddits."""
    try:
        logger.info(f"Searching subreddits with query: {query}, filters: min_subscribers={min_subscribers}, max_subscribers={max_subscribers}, min_active_users={min_active_users}, max_active_users={max_active_users}")
        subreddits = await reddit_service.search_subreddits(
            query, 
            limit=limit,
            min_subscribers=min_subscribers,
            max_subscribers=max_subscribers,
            min_active_users=min_active_users,
            max_active_users=max_active_users
        )
        
        # Sync each subreddit to the database
        for subreddit in subreddits:
            try:
                await reddit_service.sync_subreddit_to_db(subreddit, session)
            except Exception as e:
                logger.error(f"Error syncing subreddit to database: {str(e)}")
                continue
        
        # Convert models to response schema and ensure proper JSON serialization
        responses = []
        for subreddit in subreddits:
            try:
                json_data = jsonable_encoder(subreddit)
                response = SubredditResponse(**json_data)
                responses.append(response)
            except Exception as e:
                logger.error(f"Error serializing subreddit {subreddit.name}: {str(e)}")
                continue
                
        return responses
    except Exception as e:
        logger.error(f"Error in search_subreddits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search subreddits: {str(e)}")

@router.get("/suggest-keywords", response_model=List[KeywordSuggestionResponse])
async def get_keyword_suggestions(
    query: str,
    limit: int = 5,
    reddit_service: RedditService = Depends(get_reddit_service)
) -> List[KeywordSuggestionResponse]:
    """Get keyword suggestions based on a partial search query."""
    try:
        logger.info(f"Getting keyword suggestions for query: {query}")
        suggestions = await reddit_service.get_keyword_suggestions(query, limit=limit)
        return suggestions
    except Exception as e:
        logger.error(f"Error in get_keyword_suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get keyword suggestions: {str(e)}")

@router.get("/{subreddit_name}", response_model=SubredditResponse)
async def get_subreddit_info(
    subreddit_name: str,
    reddit_service: RedditService = Depends(get_reddit_service),
    session: AsyncSession = Depends(get_db_session)
) -> SubredditResponse:
    """Get information about a specific subreddit."""
    try:
        logger.info(f"Getting info for subreddit: {subreddit_name}")
        subreddit = await reddit_service.get_subreddit_info(subreddit_name)
        
        # Sync the subreddit to the database
        try:
            await reddit_service.sync_subreddit_to_db(subreddit, session)
        except Exception as e:
            logger.error(f"Error syncing subreddit to database: {str(e)}")
        
        # Convert model to response schema and ensure proper JSON serialization
        json_data = jsonable_encoder(subreddit)
        response = SubredditResponse(**json_data)
        return response
    except Exception as e:
        logger.error(f"Error in get_subreddit_info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get subreddit info: {str(e)}") 