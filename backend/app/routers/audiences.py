from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import joinedload
from sqlmodel import delete, func, select

from ..core.config import get_settings
from ..dependencies import get_db_session
from ..models import (Audience, AudienceSubreddit, RedditPost, Subreddit,
                      Theme, ThemePost, ThemeQuestion)
from ..schemas.audience import (AudienceCreate, AudienceResponse,
                                AudienceUpdate, AudienceWithSubreddits)
from ..services.themes import ThemeService

router = APIRouter(prefix="/api/audiences", tags=["audiences"])

# Create a new async session maker for background tasks
settings = get_settings()
background_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=True,
    pool_pre_ping=True
)
BackgroundSessionLocal = async_sessionmaker(
    background_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def collect_initial_data(audience_id: int) -> None:
    """Background task to collect initial data for a new audience."""
    async with BackgroundSessionLocal() as session:
        try:
            # Get the audience
            stmt = select(Audience).where(Audience.id == audience_id)
            result = await session.execute(stmt)
            audience = result.scalar_one_or_none()
            
            if not audience:
                print(f"Audience {audience_id} not found")
                return
            
            try:
                # Set collecting flag
                audience.is_collecting = True
                await session.commit()
                
                # Create theme service with the background session
                theme_service = ThemeService(session)
                
                # These methods are already async, so we don't need run_in_threadpool
                await theme_service.collect_posts_for_audience(audience_id, is_initial_collection=True)
                await theme_service.analyze_themes(audience_id)
                
            finally:
                # Always update the collecting status, even if there's an error
                stmt = select(Audience).where(Audience.id == audience_id)
                result = await session.execute(stmt)
                audience = result.scalar_one_or_none()
                if audience:
                    audience.is_collecting = False
                    await session.commit()
                
        except Exception as e:
            print(f"Error in collect_initial_data for audience {audience_id}: {str(e)}")
            # Ensure we reset the collecting flag even if there's an error
            try:
                stmt = select(Audience).where(Audience.id == audience_id)
                result = await session.execute(stmt)
                audience = result.scalar_one_or_none()
                if audience:
                    audience.is_collecting = False
                    await session.commit()
            except Exception as inner_e:
                print(f"Error resetting collecting flag: {str(inner_e)}")
            raise

@router.post("", response_model=AudienceWithSubreddits)
async def create_audience(
    audience: AudienceCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
) -> AudienceWithSubreddits:
    """Create a new audience."""
    try:
        db_audience = Audience(
            name=audience.name,
            description=audience.description,
            timeframe=audience.timeframe,
            posts_per_subreddit=audience.posts_per_subreddit,
            is_collecting=True
        )
        
        # Add subreddits to the audience
        subreddit_names = []
        for subreddit_name in audience.subreddit_names:
            subreddit_name = subreddit_name.lower()
            subreddit_names.append(subreddit_name)
            
            # Get or create subreddit
            stmt = select(Subreddit).where(Subreddit.name == subreddit_name)
            result = await session.execute(stmt)
            db_subreddit = result.scalar_one_or_none()
            
            if not db_subreddit:
                db_subreddit = Subreddit(
                    name=subreddit_name,
                    display_name=subreddit_name
                )
                session.add(db_subreddit)
                try:
                    await session.flush()
                except Exception as e:
                    await session.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error creating subreddit {subreddit_name}: {str(e)}"
                    )
            
            audience_subreddit = AudienceSubreddit(subreddit_name=subreddit_name)
            db_audience.subreddits.append(audience_subreddit)
        
        session.add(db_audience)
        await session.commit()
        
        # Refresh the audience with eager loading of subreddits
        stmt = (
            select(Audience)
            .options(joinedload(Audience.subreddits))
            .where(Audience.id == db_audience.id)
        )
        result = await session.execute(stmt)
        db_audience = result.unique().scalar_one()
        
        # Start background task after successful commit
        background_tasks.add_task(collect_initial_data, db_audience.id)
        
        return AudienceWithSubreddits(
            id=db_audience.id,
            name=db_audience.name,
            description=db_audience.description,
            created_at=db_audience.created_at,
            updated_at=db_audience.updated_at,
            timeframe=db_audience.timeframe,
            posts_per_subreddit=db_audience.posts_per_subreddit,
            is_collecting=db_audience.is_collecting,
            subreddit_names=subreddit_names
        )
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error creating audience: {str(e)}"
        )

@router.get("", response_model=List[AudienceWithSubreddits])
async def get_audiences(
    session: AsyncSession = Depends(get_db_session)
) -> List[AudienceWithSubreddits]:
    """Get all audiences."""
    # Query audiences with their post counts and eagerly load subreddits
    stmt = (
        select(
            Audience,
            func.count(RedditPost.id).label('post_count')
        )
        .outerjoin(AudienceSubreddit, Audience.id == AudienceSubreddit.audience_id)
        .outerjoin(RedditPost, AudienceSubreddit.subreddit_name == RedditPost.subreddit_name)
        .options(joinedload(Audience.subreddits))
        .group_by(Audience.id)
        .order_by(Audience.created_at.desc())  # Sort by creation date, newest first
    )
    
    result = await session.execute(stmt)
    audiences_with_counts = result.unique().all()
    
    return [
        AudienceWithSubreddits(
            id=audience.id,
            name=audience.name,
            description=audience.description,
            created_at=audience.created_at,
            updated_at=audience.updated_at,
            timeframe=audience.timeframe,
            posts_per_subreddit=audience.posts_per_subreddit,
            is_collecting=audience.is_collecting,
            post_count=post_count or 0,
            subreddit_names=[s.subreddit_name for s in audience.subreddits]
        )
        for audience, post_count in audiences_with_counts
    ]

@router.get("/{audience_id}", response_model=AudienceWithSubreddits)
async def get_audience(
    audience_id: int,
    session: AsyncSession = Depends(get_db_session)
) -> AudienceWithSubreddits:
    """Get an audience by ID with its subreddits."""
    stmt = (
        select(
            Audience,
            func.count(RedditPost.id).label('post_count')
        )
        .outerjoin(AudienceSubreddit, Audience.id == AudienceSubreddit.audience_id)
        .outerjoin(RedditPost, AudienceSubreddit.subreddit_name == RedditPost.subreddit_name)
        .options(joinedload(Audience.subreddits))
        .where(Audience.id == audience_id)
        .group_by(Audience.id)
    )
    
    result = await session.execute(stmt)
    result = result.unique().first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Audience not found")
    
    audience, post_count = result
    return AudienceWithSubreddits(
        id=audience.id,
        name=audience.name,
        description=audience.description,
        created_at=audience.created_at,
        updated_at=audience.updated_at,
        timeframe=audience.timeframe,
        posts_per_subreddit=audience.posts_per_subreddit,
        is_collecting=audience.is_collecting,
        post_count=post_count or 0,
        subreddit_names=[s.subreddit_name for s in audience.subreddits]
    )

@router.patch("/{audience_id}", response_model=AudienceWithSubreddits)
async def update_audience(
    audience_id: int,
    update: AudienceUpdate,
    session: AsyncSession = Depends(get_db_session)
) -> AudienceWithSubreddits:
    """Update an audience."""
    # Load audience with subreddits in a single query
    stmt = (
        select(Audience)
        .options(joinedload(Audience.subreddits))
        .where(Audience.id == audience_id)
    )
    result = await session.execute(stmt)
    audience = result.unique().scalar_one_or_none()
    
    if not audience:
        raise HTTPException(status_code=404, detail="Audience not found")
    
    # Update basic fields
    if update.name is not None:
        audience.name = update.name
    if update.description is not None:
        audience.description = update.description
    if update.timeframe is not None:
        audience.timeframe = update.timeframe
    if update.posts_per_subreddit is not None:
        audience.posts_per_subreddit = update.posts_per_subreddit
    
    # Update subreddits if provided
    if update.subreddit_names is not None:
        # Get current subreddit names before update
        current_subreddit_names = {s.subreddit_name for s in audience.subreddits}
        # Get new subreddit names as a set
        new_subreddit_names = set(update.subreddit_names)
        
        # Find subreddits that were removed
        removed_subreddit_names = current_subreddit_names - new_subreddit_names
        
        # Delete posts from removed subreddits
        if removed_subreddit_names:
            try:
                # For each removed subreddit, check if it's used by other audiences
                for subreddit_name in removed_subreddit_names:
                    # Check if subreddit is used by other audiences
                    result = await session.execute(
                        select(AudienceSubreddit)
                        .where(
                            (AudienceSubreddit.subreddit_name == subreddit_name) &
                            (AudienceSubreddit.audience_id != audience_id)
                        )
                    )
                    other_audience_uses = result.first() is not None
                    
                    # Only delete posts if subreddit is not used by other audiences
                    if not other_audience_uses:
                        # Get posts from this subreddit
                        result = await session.execute(
                            select(RedditPost.id).where(RedditPost.subreddit_name == subreddit_name)
                        )
                        post_ids = [post_id for post_id, in result.all()]
                        
                        if post_ids:
                            # Delete theme_posts entries that reference these posts
                            await session.execute(
                                delete(ThemePost).where(ThemePost.post_id.in_(post_ids))
                            )
                            
                            # Then delete the posts themselves
                            await session.execute(
                                delete(RedditPost).where(RedditPost.id.in_(post_ids))
                            )
                
                # Get all theme IDs for this audience
                result = await session.execute(
                    select(Theme.id).where(Theme.audience_id == audience_id)
                )
                theme_ids = [theme_id for theme_id, in result.all()]
                
                if theme_ids:
                    # First delete theme questions
                    await session.execute(
                        delete(ThemeQuestion).where(ThemeQuestion.theme_id.in_(theme_ids))
                    )
                    
                    # Then delete theme posts
                    await session.execute(
                        delete(ThemePost).where(ThemePost.theme_id.in_(theme_ids))
                    )
                    
                    # Finally delete the themes
                    await session.execute(
                        delete(Theme).where(Theme.id.in_(theme_ids))
                    )
                
                # Commit the deletions
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Error deleting posts and related data: {str(e)}"
                )
        
        # Remove existing audience-subreddit associations
        await session.execute(
            delete(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience_id)
        )
        
        # Add new subreddits
        for subreddit_name in update.subreddit_names:
            # Ensure subreddit name is lowercase
            subreddit_name = subreddit_name.lower()
            
            # Get or create subreddit
            result = await session.execute(
                select(Subreddit).where(Subreddit.name == subreddit_name)
            )
            db_subreddit = result.scalar_one_or_none()
            
            if not db_subreddit:
                # Create a new subreddit with minimal information
                db_subreddit = Subreddit(
                    name=subreddit_name,
                    display_name=subreddit_name  # Use name as display_name initially
                )
                session.add(db_subreddit)
                await session.flush()
            
            audience_subreddit = AudienceSubreddit(
                audience_id=audience_id,
                subreddit_name=subreddit_name
            )
            session.add(audience_subreddit)
    
    # Update the timestamp
    audience.updated_at = datetime.utcnow()
    
    # Commit the changes
    await session.commit()
    
    # Refresh audience with subreddits
    stmt = (
        select(Audience)
        .options(joinedload(Audience.subreddits))
        .where(Audience.id == audience_id)
    )
    result = await session.execute(stmt)
    audience = result.unique().scalar_one_or_none()
    
    return AudienceWithSubreddits(
        id=audience.id,
        name=audience.name,
        description=audience.description,
        created_at=audience.created_at,
        updated_at=audience.updated_at,
        timeframe=audience.timeframe,
        posts_per_subreddit=audience.posts_per_subreddit,
        is_collecting=audience.is_collecting,
        collection_progress=audience.collection_progress,
        subreddit_names=[s.subreddit_name for s in audience.subreddits]
    )

@router.delete("/{audience_id}")
async def delete_audience(
    audience_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Delete an audience."""
    try:
        # Start a transaction
        async with session.begin():
            # Get the audience with its subreddits
            result = await session.execute(
                select(Audience)
                .options(joinedload(Audience.subreddits))
                .where(Audience.id == audience_id)
            )
            audience = result.unique().scalar_one_or_none()
            
            if not audience:
                raise HTTPException(status_code=404, detail="Audience not found")
            
            # Get all subreddit names for this audience
            subreddit_names = [s.subreddit_name for s in audience.subreddits]
            
            # Step 1: Delete all theme-related data
            # First get all theme IDs for this audience
            result = await session.execute(
                select(Theme.id).where(Theme.audience_id == audience_id)
            )
            theme_ids = [theme_id for theme_id, in result.all()]
            
            if theme_ids:
                # Delete theme_posts and theme_questions first (they reference themes)
                await session.execute(
                    delete(ThemePost).where(ThemePost.theme_id.in_(theme_ids))
                )
                await session.execute(
                    delete(ThemeQuestion).where(ThemeQuestion.theme_id.in_(theme_ids))
                )
                # Then delete the themes
                await session.execute(
                    delete(Theme).where(Theme.id.in_(theme_ids))
                )
            
            # Step 2: For each subreddit, check if we should delete its posts
            for subreddit_name in subreddit_names:
                # Check if subreddit is used by other audiences
                result = await session.execute(
                    select(AudienceSubreddit)
                    .where(
                        (AudienceSubreddit.subreddit_name == subreddit_name) &
                        (AudienceSubreddit.audience_id != audience_id)
                    )
                )
                other_audience_uses = result.first() is not None
                
                # Only delete posts if subreddit is not used by other audiences
                if not other_audience_uses:
                    # Get posts from this subreddit
                    result = await session.execute(
                        select(RedditPost.id).where(RedditPost.subreddit_name == subreddit_name)
                    )
                    post_ids = [post_id for post_id, in result.all()]
                    
                    if post_ids:
                        # Delete theme_posts entries that reference these posts first
                        await session.execute(
                            delete(ThemePost).where(ThemePost.post_id.in_(post_ids))
                        )
                        # Then delete the posts themselves
                        await session.execute(
                            delete(RedditPost).where(RedditPost.id.in_(post_ids))
                        )
            
            # Step 3: Delete audience_subreddits associations
            # This needs to happen before deleting the audience due to foreign key constraints
            await session.execute(
                delete(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience_id)
            )
            
            # Step 4: Finally delete the audience itself
            await session.delete(audience)
            
            # The transaction will be automatically committed here if no errors occurred
            
        return {"status": "success", "message": "Audience deleted successfully"}
        
    except Exception as e:
        # The transaction will be automatically rolled back on error
        raise HTTPException(status_code=500, detail=str(e)) 