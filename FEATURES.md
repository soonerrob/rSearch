# Reddit Audience Research Tool - Feature Documentation

## Data Collection Features

### 1. Initial Data Collection
**Location**: `backend/app/services/themes.py` and `backend/app/routers/audiences.py`
**Trigger**: When a new audience is created
**Implementation**:
- Function: `collect_initial_data` (background task)
- Parameters: 
  - Posts per subreddit: 500
  - Time period: 1 year
- Process:
  1. Called automatically when new audience is created
  2. Uses `is_initial_collection=True` flag
  3. Enforces fixed limits regardless of audience settings
  4. Collects posts through RedditService
  5. Analyzes themes after collection

### 2. Hourly Updates
**Location**: `backend/app/main.py`
**Implementation**:
- Function: `update_audience_data` (background thread)
- Process:
  1. Runs in continuous loop while server is active
  2. Gets all audience IDs from database
  3. For each audience:
     - Collects new posts using audience's settings
     - Adds 1-second delay between audiences
  4. Waits 1 hour before next cycle
  5. Prints completion message with timestamp
- Error Handling:
  - Catches and logs exceptions
  - Continues running even if individual updates fail

### 3. Theme Analysis
**Location**: `backend/app/services/themes.py`
**Implementation**:
- Function: `analyze_themes`
- Categories:
  1. Hot Discussions (high engagement posts)
  2. Top Content (highest scoring posts)
  3. Advice Requests (keyword based)
  4. Solution Requests (keyword based)
  5. Pain & Anger (keyword based)
  6. Money Talk (keyword based)
  7. Self-Promotion (keyword based)
  8. News (keyword based)
  9. Ideas (keyword based)
  10. Opportunities (keyword based)
- Process:
  1. Gets recent posts based on audience timeframe
  2. Analyzes posts for each category
  3. Creates theme records with summaries
  4. Associates posts with themes
  5. Calculates relevance scores

### 4. Theme Page Settings
**Location**: Frontend and `backend/app/routers/themes.py`
**Default Settings**:
- Timeframe: "month"
- Posts per subreddit: 100
**Behavior**:
- Settings persist per audience
- Theme analysis updates when settings change

## Database Models

### 1. Audience Model
- Stores audience configuration
- Tracks collection progress
- Maintains subreddit associations
- Stores theme analysis settings

### 2. RedditPost Model
- Stores collected post data
- Tracks post metrics (score, comments)
- Records collection timestamp
- Associates with subreddits

### 3. Theme Model
- Categorizes analyzed content
- Stores theme summaries
- Tracks creation/update times
- Links to relevant posts

### 4. ThemePost Model
- Links posts to themes
- Stores relevance scores
- Enables post filtering by theme

## Background Tasks

### 1. Server Startup Tasks
**Location**: `backend/app/main.py`
**Implementation**:
- Database initialization
- Background thread startup
- CORS configuration
- Router registration

### 2. Error Handling
- Exception catching in background tasks
- Database session management
- Progress tracking and updates
- Graceful degradation on failures

## Performance Features

### 1. Database Optimization
- Session management per operation
- Efficient query patterns
- Bulk operations where possible

### 2. Background Processing
- Non-blocking operations
- Daemon thread for updates
- Progress tracking
- Error resilience

### 3. API Efficiency
- FastAPI's async capabilities
- Proper database session handling
- Controlled update intervals
- Rate limiting considerations

## Future Enhancements (TODOs)
1. AI-powered theme summarization using OpenAI API
2. More sophisticated relevance scoring
3. Enhanced error reporting and monitoring
4. Advanced theme categorization algorithms 