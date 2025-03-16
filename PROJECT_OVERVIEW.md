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
   - Comment collection framework in place (future feature)

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
   - Users can ask questions about the collected data
   - Questions are processed by OpenAI API
   - Example: "What are the top 3 problems being discussed?"
   - AI analyzes posts/comments to provide relevant answers
   - Question history tracking and persistence
   - Theme-specific question management

## Current Project Status

The project is undergoing a major migration from PRAW to AsyncPRAW. This migration was necessitated by the realization that the original implementation wasn't built on an asynchronous platform, limiting scalability and performance.

### Migration Challenges
- Previous developer initiated migration but left mid-project
- Multiple changes were implemented but not fully documented
- Currently working to stabilize and complete the migration
- Using testing_plan.md and test_results as primary guidelines
- Addressing time_filter validation issues in post collection
- Implementing proper cascade deletion for audiences

## Technical Implementation

### Backend
- FastAPI for API endpoints (port 8001)
  - No automatic port fallback
  - Requires manual port conflict resolution
- AsyncPRAW for Reddit data collection
- PostgreSQL database for data storage
- OpenAI API integration for content analysis
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
  - Comment structure ready for implementation
  - Proper relationship management with audiences

### Frontend
- Next.js/React for the user interface (port 3000)
  - Automatic fallback to port 3001 if 3000 is in use
  - Real-time updates for audience data collection
  - Interactive theme exploration
  - Question-answer interface for AI insights
  - Progress indicators for data collection
  - Error handling and user feedback

### Data Flow
1. User creates audience → Backend initiates post collection
2. Posts are processed and categorized into themes
3. Themes are presented in the UI for exploration
4. User questions trigger AI analysis of collected data
5. Background tasks handle periodic updates

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

### Theme Categorization System Update (March 2024)
1. **Post Analysis Table**
   - Added new `post_analysis` table to store theme matches for each post
   - Each post analysis includes:
     - Matching themes (array of theme categories)
     - Keywords found in the post
     - Analysis timestamp

2. **Theme Generation Process**
   - Changed from manual settings to automated categorization
   - Removed user configuration options (timeframe, posts_per_subreddit)
   - Posts are now analyzed immediately upon collection
   - Theme categories are predefined with specific criteria:
     - Metric-based themes (Hot Discussions, Top Content)
     - Keyword-based themes (Advice Requests, Solution Requests, etc.)

3. **Theme Categories**
   Standardized theme categories with specific criteria:
   - **Metric-based Themes:**
     - Hot Discussions: Posts with score > 10 and comments > 5
     - Top Content: All posts, sorted by score
   - **Keyword-based Themes:**
     - Advice Requests: help, question, how to, beginner, etc.
     - Solution Requests: looking for, recommend, suggestion, etc.
     - Pain & Anger: frustrated, angry, problem, issue, etc.
     - Money Talk: price, cost, budget, deal, etc.
     - Self-Promotion: i made, my project, check out, etc.
     - News: announcement, update, release, etc.
     - Ideas: creative, inspiration, groove, pattern, etc.
     - Opportunities: job, gig, audition, collaboration, etc.

4. **Theme Analysis Flow**
   1. Posts are collected from subreddits
   2. Each post is analyzed for theme matches based on:
      - Content metrics (score, comments)
      - Keyword presence in title and content
   3. Theme matches are stored in post_analysis table
   4. Themes are generated by grouping posts with matching themes
   5. Posts can belong to multiple themes if they match multiple criteria

This update improves consistency in theme categorization and removes the need for manual configuration, while ensuring posts are properly categorized based on both engagement metrics and content analysis. 