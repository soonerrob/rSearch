# Reddit Audience Research Tool - Project Overview

## Core Functionality

This site is an audience research tool designed to gather insights about buyer intent, problem-solution research, and general market research using Reddit data. The tool enables users to:

1. **Audience Creation**
   - Search for and discover relevant subreddits from the home page
   - Select multiple subreddits to create custom "audiences"
   - Configure audience settings (e.g., post collection timeframe)
   - Real-time collection status tracking with progress indicators

2. **Data Collection**
   - Automatically collects posts from each subreddit in an audience
   - Flexible timeframe options: hour, day, week, month, year
   - Configurable posts per subreddit (default 500, max 500)
   - Collection process starts immediately upon audience creation
   - Real-time progress tracking during collection
   - Background task scheduling with hourly updates
   - Comment collection with threading support
   - Engagement scoring and quality filtering

3. **Content Analysis**
   - Organizes posts into themed categories on the audience details page
   - Structured theme categorization system with:
     - Category classification
     - Theme summaries
     - Timestamp tracking (created_at, updated_at)
   - Identifies different types of conversations:
     - Buyer intent signals
     - Problem-solution discussions
     - General trends and patterns
   
4. **AI-Powered Insights**
   - Enhanced question answering using GPT-4/3.5
   - Intelligent context preparation with threaded comments
   - Confidence scoring based on multiple factors:
     - Data volume and quality
     - Engagement levels
     - Answer comprehensiveness
     - Question-content relevance
   - Detailed source attribution
   - Response caching for performance
   - Theme-specific analysis
   - Question history tracking and persistence

## Technical Implementation

### Backend
- FastAPI for API endpoints (port 8001)
  - No automatic port fallback
  - Requires manual port conflict resolution
- AsyncPRAW for Reddit data collection
- PostgreSQL database for data storage
- OpenAI API integration with:
  - GPT-4 primary model
  - GPT-3.5-turbo fallback
  - Intelligent context preparation
  - Response caching
- SQLAlchemy for database operations with:
  - Proper transaction management
  - Cascade deletions
  - Foreign key constraints
  - Relationship management

### Database Schema
- Audiences: Core table for audience management
  - Configurable settings (timeframe, posts_per_subreddit)
  - Collection status tracking (is_collecting, collection_progress)
  - Metadata (created_at, updated_at)
- Theme System:
  - Themes table with categories and summaries
  - Theme posts for content organization
  - Theme questions for tracking AI interactions
- Posts and Comments:
  - Reddit posts with full metadata
  - Threaded comment structure
  - Engagement scoring
  - Proper relationship management with audiences

### Frontend
- Next.js/React for the user interface (port 3000)
  - Automatic fallback to port 3001 if 3000 is in use
  - Real-time updates for audience data collection
  - Interactive theme exploration
  - Enhanced question-answer interface
  - Progress indicators for data collection
  - Error handling and user feedback

### Data Flow
1. User creates audience → Backend initiates post collection
2. Posts and comments are collected with threading
3. Content is analyzed and categorized into themes
4. Themes are presented in the UI for exploration
5. User questions trigger enhanced AI analysis
6. Cached responses improve performance
7. Background tasks handle periodic updates

## Future Plans
- Implement comment collection for deeper insights
- Enhance theme categorization
- Add more analysis features
- Improve AI-powered insights
- Implement retry mechanisms for failed collections
- Optimize batch processing operations

## Development Guidelines
- Follow testing_plan.md for feature verification
- Maintain asynchronous architecture
- Ensure proper error handling
- Document all major changes
- Implement proper validation for all user inputs
- Maintain transaction integrity in database operations
- Follow server management best practices:
  - Kill existing processes before starting servers
  - Verify port availability
  - Start backend before frontend
  - Monitor for port conflicts

## Recent Changes

### AI Analysis Enhancement (March 2024)
1. **Model Upgrades**
   - Added GPT-4 support
   - Automatic fallback to GPT-3.5-turbo
   - Improved context preparation

2. **Comment Threading**
   - Hierarchical comment organization
   - Depth-based relevance scoring
   - Engagement-based filtering

3. **Performance Optimization**
   - In-memory response caching
   - Smart context truncation
   - Automatic cache cleanup

4. **Enhanced Response Quality**
   - Multi-factor confidence scoring
   - Detailed source attribution
   - Structured response format

For detailed information about the AI service, see [AI_SERVICE.md](docs/AI_SERVICE.md). 