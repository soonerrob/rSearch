# Migration Plan: Converting to Async Operations

## Overview
This document outlines the step-by-step process for converting the application from synchronous to asynchronous operations. The main focus is on:
1. Converting the Reddit API client from PRAW to AsyncPRAW
2. Converting database operations to use async SQLAlchemy
3. Updating all services and routes to be async-compatible
4. Ensuring proper error handling and cancellation support

## Important Guidelines
1. **Feature Preservation**
   - Do not modify or change any existing features
   - Only convert synchronous operations to async
   - Maintain all current functionality and behavior
   - Keep all existing API endpoints and their responses unchanged

2. **Server Management**
   - Backend runs on port 8001
   - Frontend runs on port 3000
   - Always kill existing processes before starting new ones
   - Backend: `pkill -f "uvicorn main:app" && pkill -f "next"`
   - Frontend: `pkill -f "next"`
   - If processes persist, use: `pkill -9 -f "uvicorn" && pkill -9 -f "next"`
   - Always verify processes are killed: `ps aux | grep -E "python|uvicorn|next"`
   - Wait at least 2 seconds after killing before starting new servers

3. **Server Start Commands**
   - Backend (port 8001): `cd backend && uvicorn app.main:app --reload --port 8001 --log-level debug`
   - Frontend (port 3000): `cd frontend && npm run dev`

4. **Health Checks**
   - Verify backend is not running on port 8001: `ps aux | grep -E "python|uvicorn"`
   - Verify frontend is not running on port 3000: `ps aux | grep next`
   - Check ports 3000 (frontend) and 8001 (backend) are free
   - Check for zombie processes: `ps aux | grep defunct`

## Current Architecture
- FastAPI backend with synchronous PRAW client
- SQLModel/SQLAlchemy with synchronous database operations
- Background tasks using threading
- Multiple services with synchronous operations

## Migration Phases

### Phase 1: Database Migration
1. Update database configuration
   - Convert to async SQLAlchemy engine
   - Update session management
   - Update models to support async operations

2. Update database dependencies
   - Convert session factory to async
   - Update dependency injection

3. Update database operations
   - Convert all direct database operations to async
   - Update transaction management

### Phase 2: Reddit Service Migration
1. Replace PRAW with AsyncPRAW
   - Update service initialization
   - Convert all API calls to async
   - Implement proper rate limiting

2. Update service methods
   - Convert all methods to async
   - Implement proper error handling
   - Add cancellation support

3. Update service dependencies
   - Convert service factory to async
   - Update dependency injection

### Phase 3: Theme Service Migration
1. Convert to async operations
   - Update all methods to async
   - Implement proper progress tracking
   - Add cancellation support

2. Update background tasks
   - Convert to async background tasks
   - Implement proper task management
   - Add task cancellation

### Phase 4: Route Updates
1. Update route handlers
   - Convert to async operations
   - Implement proper error handling
   - Add request cancellation

2. Update response handling
   - Implement streaming responses
   - Add proper error responses
   - Update progress tracking

### Phase 5: Testing and Validation
1. Update tests
   - Convert to async tests
   - Add proper mocking
   - Test cancellation

2. Performance testing
   - Test concurrent operations
   - Validate response times
   - Check resource usage

## Detailed Steps

### Phase 1: Database Migration

#### Step 1.1: Update Database Configuration
```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Update dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

#### Step 1.2: Update Models
- No changes needed to model definitions
- Update any direct database operations in models to be async

#### Step 1.3: Update Database Operations
```python
# Example of converting sync to async operations
# Before:
result = session.execute(statement)
existing = result.scalar_one_or_none()

# After:
result = await session.execute(statement)
existing = result.scalar_one_or_none()
```

### Phase 2: Reddit Service Migration

#### Step 2.1: Replace PRAW with AsyncPRAW
```python
# backend/app/services/reddit.py
import asyncpraw

class RedditService:
    def __init__(self):
        settings = get_settings()
        self.reddit = asyncpraw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
            read_only=True
        )
```

#### Step 2.2: Convert Service Methods
```python
# Example of converting sync to async method
# Before:
def get_subreddit_posts(self, subreddit_name: str, limit: int = 500):
    subreddit = self.reddit.subreddit(subreddit_name)
    posts = subreddit.top(time_filter="year", limit=limit)
    return list(posts)

# After:
async def get_subreddit_posts(self, subreddit_name: str, limit: int = 500):
    subreddit = await self.reddit.subreddit(subreddit_name)
    posts = await subreddit.top(time_filter="year", limit=limit)
    return await posts.to_list()
```

### Phase 3: Theme Service Migration

#### Step 3.1: Convert to Async Operations
```python
# backend/app/services/themes.py
class ThemeService:
    async def collect_posts_for_audience(self, audience_id: int):
        audience = await self.db.get(Audience, audience_id)
        for subreddit_link in audience.subreddits:
            posts = await self.reddit_service.get_subreddit_posts(
                subreddit_link.subreddit_name
            )
            # Process posts asynchronously
```

### Phase 4: Route Updates

#### Step 4.1: Update Route Handlers
```python
# Example of converting sync to async route
# Before:
@router.get("/subreddits/trending")
def get_trending_subreddits():
    subreddits = reddit_service.get_trending_subreddits()
    return subreddits

# After:
@router.get("/subreddits/trending")
async def get_trending_subreddits():
    subreddits = await reddit_service.get_trending_subreddits()
    return subreddits
```

## Testing Strategy

### Unit Tests
1. Test each async service method independently
2. Mock external dependencies (Reddit API, database)
3. Test error handling and cancellation

### Integration Tests
1. Test full request/response cycles
2. Test concurrent operations
3. Test background tasks

### Performance Tests
1. Measure response times
2. Test under load
3. Monitor resource usage

## Rollback Plan
1. Keep old code in separate branches
2. Maintain database compatibility
3. Document all changes
4. Test rollback procedures

## Implementation Order
1. Start with database migration
2. Move to Reddit service
3. Update theme service
4. Convert routes
5. Update tests
6. Deploy in stages

## Notes
- Keep old code until new code is fully tested
- Test each phase thoroughly before moving to next
- Monitor performance metrics throughout
- Document all changes and decisions 