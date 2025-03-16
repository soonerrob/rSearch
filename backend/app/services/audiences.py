from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audience import Audience
from ..schemas.audience import AudienceCreate, AudienceUpdate


class AudienceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_audience(self, audience: AudienceCreate) -> Audience:
        db_audience = Audience(
            name=audience.name,
            description=audience.description,
            subreddit_names=audience.subreddits
        )
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