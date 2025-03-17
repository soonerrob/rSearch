import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import uvicorn
from app.core.database import AsyncSessionLocal, init_db
from app.models import Audience
from app.routers.audiences import router as audience_router
from app.routers.subreddits import router as subreddit_router
from app.routers.theme_questions import router as theme_questions_router
from app.routers.themes import router as theme_router
from app.services.themes import ThemeService
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

# Get the absolute path to the backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Create logs directory if it doesn't exist
logs_dir = BACKEND_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure logging
log_file = logs_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
print(f"Setting up logging to file: {log_file}")  # Debug print

# Create file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Remove all existing handlers from the root logger
root_logger = logging.getLogger()
root_logger.handlers = []

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler],
    force=True
)

# Configure specific loggers without adding duplicate handlers
for logger_name in ['asyncpraw', 'asyncprawcore', 'urllib3', 'app']:
    module_logger = logging.getLogger(logger_name)
    module_logger.setLevel(logging.DEBUG)
    module_logger.propagate = False  # Prevent propagation to parent loggers
    module_logger.handlers = [file_handler, console_handler]  # Set handlers directly

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Prevent propagation to parent loggers

# Log startup messages
logger.info(f"Starting application... Log file: {log_file}")
logger.info(f"Logs directory: {logs_dir}")
logger.info("Logging configuration complete")

# Global variable to control the background task
should_continue_background_tasks = True

async def update_audience_data():
    """Background task to systematically collect new Reddit posts for all audiences."""
    while should_continue_background_tasks:
        try:
            async with AsyncSessionLocal() as db:
                # Get all audience IDs using async session
                result = await db.execute(
                    select(Audience).where(
                        (Audience.is_collecting == False) &  # Only collect for non-collecting audiences
                        (
                            (Audience.last_collection_time == None) |  # Never collected
                            (datetime.now(timezone.utc) - Audience.last_collection_time > timedelta(hours=1))  # Or collected over 1 hour ago
                        )
                    )
                )
                audience_ids = [a.id for a in result.scalars().all()]
            
                # Process audiences one at a time
                for audience_id in audience_ids:
                    theme_service = ThemeService(db)
                    # Only collect new posts, don't analyze themes
                    await theme_service.collect_posts_for_audience(audience_id)
                    # Small delay between processing each audience to prevent overload
                    await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in background task: {str(e)}")
        
        # Wait for 1 hour before next update
        logger.info(f"Completed data collection cycle at {datetime.now(timezone.utc)}, waiting 1 hour before next update")
        await asyncio.sleep(3600)  # 3600 seconds = 1 hour

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    
    # Start background task
    background_task = asyncio.create_task(update_audience_data())
    
    yield
    
    # Stop background task
    global should_continue_background_tasks
    should_continue_background_tasks = False
    await background_task

app = FastAPI(
    title="Reddit Audience Research Tool",
    description="A specialized tool for Reddit audience research and analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(subreddit_router)
app.include_router(audience_router)
app.include_router(theme_router)
app.include_router(theme_questions_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Reddit Audience Research Tool API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True) 