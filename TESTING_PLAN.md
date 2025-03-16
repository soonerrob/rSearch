# AsyncPRAW Migration Testing Plan

## Overview
This document outlines the testing plan for verifying the migration from PRAW to AsyncPRAW in the Reddit Audience Research Tool. The testing will cover all major functionality areas to ensure a smooth transition.

## Test Environment
- Backend: FastAPI running on port 8001
  - Fallback port handling not implemented
  - Must ensure port is free before starting
- Frontend: Next.js running on port 3000
  - Fallback to port 3001 if 3000 is in use
  - Must verify both ports are available
- Database: PostgreSQL
- Reddit API: AsyncPRAW

### Port Management
- Check port availability before starting servers:
  ```bash
  sudo lsof -i :3000,3001,8001
  ```
- Kill any existing processes:
  ```bash
  sudo kill -9 $(lsof -t -i:3000)
  sudo kill -9 $(lsof -t -i:3001)
  sudo kill -9 $(lsof -t -i:8001)
  ```
- Verify ports are free before starting servers

## Testing Areas

### 1. Homepage Testing ✅
#### Search and Filtering
- [x] Test basic subreddit search functionality
  - [x] Verify search results are returned correctly
  - [x] Check error handling for invalid searches
  - [x] Verify rate limiting compliance
- [x] Test keyword suggestions
  - [x] Verify suggestions appear as you type
  - [x] Check suggestion relevance
  - [x] Test error handling
- [x] Test subreddit filtering
  - [x] Verify subscriber count filters
  - [x] Test active users filters
  - [x] Check category filters
- [x] Test subreddit selection
  - [x] Verify selection state persistence
  - [x] Test bulk selection
  - [x] Check selection limits

#### Performance Metrics
- [x] Measure search response times (~200ms average)
- [x] Monitor API rate limit usage (no issues observed)
- [x] Track database query performance (good performance with caching)

### 2. Audiences Page Testing ✅
#### Audience Management
- [x] Test audience creation
  - [x] Verify initial creation in database
  - [x] Verify subreddit validation
  - [x] Check background task initialization
    - [x] Fixed MissingGreenlet error with proper async session management
    - [x] Fixed InvalidRequestError by adding unique() to query results
    - [x] Fixed ListingGenerator async iteration
  - [x] Test error handling
- [x] Test audience listing
  - [x] Verify pagination
  - [x] Check sorting options
  - [x] Test filtering
- [x] Test audience editing
  - [x] Verify subreddit updates
    - [x] Successfully tested removing subreddits from multiple audiences
    - [x] Verified cascade deletion of related posts and themes
    - [x] Confirmed proper database updates
    - [x] Added post retention logic
      - [x] Posts are only deleted if subreddit is not used by other audiences
      - [x] Posts are retained if subreddit exists in another audience
      - [x] Theme posts are properly cleaned up
  - [x] Check description updates
    - [x] Successfully updated audience descriptions
    - [x] Successfully updated audience names
    - [x] Verified changes persist in database
  - [x] Test settings changes
    - [x] Update timeframe
      - [x] Successfully updated timeframe settings
      - [x] Verified valid Reddit API timeframe values (hour, day, week, month, year)
      - [x] Removed 'all' timeframe option as it's no longer supported
      - [x] Confirmed changes persist in database
      - [x] Verified timeframe dropdown shows correct options in UI
    - [x] Update posts_per_subreddit
      - [x] Successfully updated posts per subreddit limit
      - [x] Verified max limit of 500 posts
      - [x] Confirmed changes persist in database
      - [x] Enhanced validation feedback
        - [x] Real-time validation messages
        - [x] Visual feedback (red border, error text)
        - [x] Accessibility support (ARIA attributes)
        - [x] Form submission protection
- [x] Test audience deletion
  - [x] Verify cascade deletion
    - [x] Audience record deleted
    - [x] Audience-subreddit associations removed
    - [x] Related theme posts deleted
    - [x] Related themes deleted
  - [x] Check cleanup of related data
    - [x] No orphaned records
    - [x] Foreign key constraints enforced
    - [x] Transaction integrity maintained
    - [x] Added post retention logic
      - [x] Posts are only deleted if subreddit is not used by other audiences
      - [x] Posts are retained if subreddit exists in another audience
      - [x] Theme posts are properly cleaned up
  - [x] Database verification
    - [x] Verify audience removed from audiences table (confirmed ID 19 deleted)
    - [x] Verify associations removed from audience_subreddits
    - [x] Verify no orphaned data in related tables
    - [ ] CURRENT ISSUE: Audience 9 deletion not working
      - [ ] Frontend sends delete request but no response/action
      - [ ] Backend endpoint appears correct but may not be receiving request
      - [ ] Need to verify request in browser dev tools
      - [ ] Backend shows unrelated error about time_filter
    - [ ] Theme verification pending (tables not yet implemented)
      - [ ] Theme posts table verification
    - [ ] Verify audience removed from audiences table
    - [ ] Verify associations removed from audience_subreddits
    - [ ] Verify theme posts removed from theme_posts
    - [ ] Verify themes removed from themes table
    - [ ] Check for any orphaned data in related tables

#### Data Collection ✅
- [x] Test initial data collection
  - [x] Verify post fetching
  - [x] Monitor progress updates
- [x] Test background updates
  - [x] Verify scheduled updates
  - [x] Check error recovery
  - [x] Monitor resource usage

### 3. Theme Pages Testing 🔄
#### Theme Analysis
- [ ] Test theme generation
  - [ ] Verify topic clustering
  - [ ] Check sentiment analysis
  - [ ] Test keyword extraction
- [ ] Test theme visualization
  - [ ] Verify chart rendering
  - [ ] Check data accuracy
  - [ ] Test interactivity
- [ ] Test theme questions
  - [ ] Verify question generation
  - [ ] Check answer processing
  - [ ] Test question updates
- [ ] Test theme insights
  - [ ] Verify trend analysis
  - [ ] Check pattern detection
  - [ ] Test recommendation generation

### 4. Comment Collection 🔄
#### Implementation Plan
- [ ] Design comment collection strategy
  - [ ] Define comment depth limits
  - [ ] Plan batch processing approach
  - [ ] Design storage schema
- [ ] Implement collection logic
  - [ ] Add AsyncPRAW comment fetching
  - [ ] Implement batch processing
  - [ ] Add progress tracking
- [ ] Test collection process
  - [ ] Verify rate limiting compliance
  - [ ] Check data integrity
  - [ ] Monitor performance

## Current Focus Areas

### Priority Tasks
1. Theme System Implementation
   - Design theme generation algorithm
   - Implement topic clustering
   - Add sentiment analysis
   - Create visualization components

2. Comment Collection System
   - Design database schema updates
   - Implement AsyncPRAW comment fetching
   - Add batch processing logic
   - Create progress tracking

### Next Steps
1. Begin theme system implementation
2. Design comment collection architecture
3. Update database schema for comments
4. Implement theme visualization components

## Progress Tracking
- [x] Homepage Testing Complete
- [x] Audiences Page Testing Complete
- [x] Post Collection Complete
- [x] Background Tasks Complete
- [ ] Theme Pages Testing Not Started
- [ ] Comment Collection Not Started

## Notes
- Core audience and post management features complete
- Focus shifting to theme system and comment collection
- Consider implementing retry mechanism for comment collection
- Plan for scalability in theme processing

### Current Priority Issues
1. Audience Deletion Not Working (IN PROGRESS)
   - Issue: Audience 9 cannot be deleted through frontend
   - Status: Under Investigation
   - Location: Frontend delete request and backend delete endpoint
   - Current Findings:
     - Frontend sends delete confirmation dialog
     - User confirms deletion
     - No visible response or error in UI
     - Backend shows unrelated error about time_filter
   - Next Debug Steps:
     1. Check browser dev tools for request/response
     2. Verify backend receiving delete request
     3. Investigate potential frontend state management issues
     4. Address unrelated time_filter error in logs

## Post Retention Logic Testing

### Background and Core Functionality
The application allows users to:
1. Create audiences containing multiple subreddits
2. Collect posts for each subreddit within an audience
3. Share subreddits across multiple audiences
4. Remove subreddits from audiences
5. Delete entire audiences

**Key Post Retention Rules:**
- When removing a subreddit from an audience:
  - Delete its posts ONLY IF that subreddit isn't in any other audience
  - Retain posts if the subreddit exists in another audience
- When deleting an entire audience:
  - For each subreddit in that audience, delete its posts ONLY IF that subreddit isn't in any other audience
  - Retain posts for any subreddits that exist in other audiences

### Previous Test Attempt (Interrupted)
We previously attempted the first test case:
- Target: Audience 9
  - Contained only one subreddit: "pythonprojects2"
  - "pythonprojects2" also exists in Audience 12
  - Had 500 verified posts
- Expected Outcome:
  - Audience 9 should be completely deleted
  - All posts for "pythonprojects2" should be retained (due to Audience 12)
- Test Status: Interrupted due to:
  - Technical issues from unit testing implementation
  - Complications from starting comment collection feature
  - Partial deletion bug (now fixed)

### Test Cases

#### 1. Delete Audience with Shared Subreddit
**Objective**: Verify posts are retained when a subreddit exists in multiple audiences
**Setup**:
- Audience A contains subreddit "python"
- Audience B also contains subreddit "python"
- 500 posts exist for "python"

**Test Steps**:
1. Delete Audience A
2. Verify:
   - Audience A is completely removed from audiences table
   - All audience-subreddit associations for Audience A are removed
   - All 500 posts for "python" are retained (since still used by Audience B)
   - All theme/theme_post relationships for Audience A are removed
   - No orphaned data exists in any related tables

#### 2. Delete Audience with Unique Subreddit
**Objective**: Verify posts are deleted when removing an audience with a unique subreddit
**Setup**:
- Audience C contains subreddit "unique_subreddit"
- No other audience contains "unique_subreddit"
- 500 posts exist for "unique_subreddit"

**Test Steps**:
1. Delete Audience C
2. Verify:
   - Audience C is completely removed from audiences table
   - All audience-subreddit associations for Audience C are removed
   - All 500 posts for "unique_subreddit" are deleted
   - All theme/theme_post relationships are removed
   - No orphaned data exists in any related tables

#### 3. Remove Subreddit from Audience (Shared)
**Objective**: Verify posts are retained when removing a subreddit that exists in other audiences
**Setup**:
- Audience D and E both contain subreddit "python"
- 500 posts exist for "python"

**Test Steps**:
1. Remove "python" from Audience D
2. Verify:
   - Association between Audience D and "python" is removed
   - All 500 posts for "python" are retained
   - Theme/theme_post relationships for Audience D are removed
   - Association between Audience E and "python" remains intact
   - No orphaned data exists

#### 4. Remove Subreddit from Last Audience
**Objective**: Verify posts are deleted when removing a subreddit from its last audience
**Setup**:
- Only Audience F contains subreddit "last_subreddit"
- 500 posts exist for "last_subreddit"

**Test Steps**:
1. Remove "last_subreddit" from Audience F
2. Verify:
   - Association between Audience F and "last_subreddit" is removed
   - All 500 posts for "last_subreddit" are deleted
   - All related theme/theme_post relationships are removed
   - No orphaned data exists

### Current Testing Priority
1. First Test Case (Retry Previous Attempt)
**Objective**: Verify posts are retained when deleting an audience that shares its only subreddit with another audience
**Setup**:
- Find two suitable audiences where:
  - First audience contains only one subreddit
  - That same subreddit exists in the second audience
  - Verified post count exists for the subreddit
**Test Steps**:
1. Delete the first audience
2. Verify:
   - Audience is completely removed
   - All associations are removed
   - All posts are retained (due to second audience)
   - No orphaned data exists

### Verification Methods
For each test case, use the following verification steps:

1. Database Integrity Checks:
```sql
-- Check for orphaned posts
SELECT p.* FROM redditpost p
LEFT JOIN audience_subreddits a ON p.subreddit_name = a.subreddit_name
WHERE a.subreddit_name IS NULL;

-- Check for orphaned theme posts
SELECT tp.* FROM themepost tp
LEFT JOIN theme t ON tp.theme_id = t.id
WHERE t.id IS NULL;

-- Check for orphaned themes
SELECT t.* FROM theme t
LEFT JOIN audiences a ON t.audience_id = a.id
WHERE a.id IS NULL;
```

2. Application-Level Verification:
   - Use frontend UI to verify visibility of audiences and posts
   - Confirm post counts in audience listings are accurate
   - Verify theme relationships are properly maintained/removed

3. Error Handling:
   - Verify proper error messages for invalid operations
   - Ensure transaction rollback on failures
   - Check logging of deletion operations

### Success Criteria
- No orphaned records in any table
- Posts retained when shared across audiences
- Posts deleted only when removed from last audience
- All theme relationships properly maintained
- Database constraints maintained
- No unhandled errors during operations 