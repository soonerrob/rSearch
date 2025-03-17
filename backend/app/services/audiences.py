from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audience import Audience, AudienceSubreddit
from ..models.subreddit import Subreddit
from ..schemas.audience import AudienceCreate, AudienceUpdate


class AudienceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_audience(self, audience: AudienceCreate) -> Audience:
        db_audience = Audience(
            name=audience.name,
            description=audience.description,
            timeframe=audience.timeframe,
            posts_per_subreddit=audience.posts_per_subreddit,
            is_collecting=False,
            collection_progress=0.0
        )
        
        # Add subreddits to the audience
        for subreddit_name in audience.subreddit_names:
            subreddit_name = subreddit_name.lower()
            
            # Get or create subreddit
            stmt = select(Subreddit).where(Subreddit.name == subreddit_name)
            result = await self.db.execute(stmt)
            db_subreddit = result.scalar_one_or_none()
            
            if not db_subreddit:
                db_subreddit = Subreddit(
                    name=subreddit_name,
                    display_name=subreddit_name,
                    subscribers=0,
                    active_users=0,
                    last_updated=datetime.utcnow()
                )
                self.db.add(db_subreddit)
                await self.db.flush()
            
            audience_subreddit = AudienceSubreddit(subreddit_name=subreddit_name)
            db_audience.subreddits.append(audience_subreddit)
        
        self.db.add(db_audience)
        await self.db.commit()
        await self.db.refresh(db_audience)
        return db_audience

    async def get_audience(self, audience_id: int) -> Optional[Audience]:
        result = await self.db.execute(
            select(Audience).where(Audience.id == audience_id)
        )
        return result.scalar_one_or_none()

    async def get_audiences(self) -> List[Audience]:
        result = await self.db.execute(select(Audience))
        return list(result.scalars().all())

    async def update_audience(self, audience_id: int, audience: AudienceUpdate) -> Optional[Audience]:
        db_audience = await self.get_audience(audience_id)
        if not db_audience:
            return None

        if audience.subreddits is not None:
            db_audience.subreddit_names = audience.subreddits

        await self.db.commit()
        await self.db.refresh(db_audience)
        return db_audience

    async def delete_audience(self, audience_id: int) -> bool:
        db_audience = await self.get_audience(audience_id)
        if not db_audience:
            return False

        await self.db.delete(db_audience)
        await self.db.commit()
        return True 