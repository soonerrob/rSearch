# AI Service Documentation

## Overview

The AI service provides intelligent analysis of Reddit content using OpenAI's GPT models. It supports question answering, theme analysis, and content summarization with enhanced features for accuracy and performance.

## Key Features

### 1. Advanced Question Answering
- GPT-4 integration with GPT-3.5-turbo fallback
- Intelligent context preparation with threaded comments
- Confidence scoring based on multiple factors
- Detailed source attribution
- Response caching for performance

### 2. Enhanced Content Analysis
- Threaded comment organization
- Engagement-based sorting
- Theme-specific analysis
- Comprehensive metrics tracking

## Technical Implementation

### Question Analysis Flow

1. **Cache Check**
   ```python
   cache_key = f"qa:{hash(question)}:{hash(str(posts))}"
   cached_response = await cache.get(cache_key)
   ```

2. **Content Preparation**
   - Posts sorted by engagement score
   - Comments organized in threads
   - Context optimized for token limits

3. **AI Model Selection**
   - Primary: GPT-4
   - Fallback: GPT-3.5-turbo
   - Automatic model switching based on availability

4. **Response Structure**
   ```json
   {
     "answer": "Detailed response text",
     "confidence": 0.85,
     "sources": [
       {
         "type": "post",
         "title": "Post title",
         "url": "Reddit URL",
         "score": 100,
         "engagement": 0.95,
         "relevance": "primary"
       }
     ],
     "model": "gpt-4",
     "analyzed_at": "2024-03-16T12:00:00Z"
   }
   ```

### Confidence Scoring

The confidence score (0.0-1.0) is calculated based on multiple factors:

1. **Data Volume and Quality**
   - Number of relevant posts (≥10 posts: +0.1)
   - Comment volume (≥20 comments: +0.1)

2. **Engagement Levels**
   - Average post score (>50: +0.1)

3. **Answer Comprehensiveness**
   - Response word count (>100 words: +0.1)

4. **Question-Content Relevance**
   - Keyword match ratio (proportional boost)

### Comment Threading

Comments are organized in a hierarchical structure:
- Maximum depth: 3 levels
- Maximum children per level: 3
- Sorted by score and engagement

Example thread structure:
```
Top Comment
  ├─ Reply 1
  │   ├─ Sub-reply 1
  │   └─ Sub-reply 2
  └─ Reply 2
      └─ Sub-reply 1
```

### Caching System

- In-memory cache with expiration
- Default TTL: 1 hour
- Automatic cleanup of expired entries
- Thread-safe implementation

## Usage Examples

### Basic Question Analysis
```python
response = await ai_service.analyze_question(
    question="What are common issues discussed?",
    audience_id=123
)
```

### Theme Analysis
```python
analysis = await ai_service.analyze_theme_content(
    theme_posts=posts,
    theme_comments=comments,
    category="Technical Issues"
)
```

## Performance Considerations

1. **Caching Strategy**
   - Frequently asked questions cached
   - High-engagement content prioritized
   - Automatic cache invalidation

2. **Context Optimization**
   - Smart content truncation
   - Relevant comment selection
   - Token limit management

3. **Error Handling**
   - Graceful model fallback
   - Automatic retry logic
   - Comprehensive error logging

## Future Enhancements

1. **Planned Features**
   - Redis cache integration
   - Sentiment analysis integration
   - Multi-model response aggregation
   - Advanced source ranking

2. **Optimization Opportunities**
   - Response streaming
   - Batch processing
   - Distributed caching

## Maintenance

1. **Cache Management**
   - Regular cache cleanup
   - Performance monitoring
   - Usage analytics

2. **Model Updates**
   - Version tracking
   - Performance benchmarking
   - Cost optimization

## Error Handling

1. **Common Issues**
   - API rate limits
   - Token limits
   - Cache misses

2. **Recovery Strategies**
   - Automatic retries
   - Model fallback
   - Cache bypass options

## Best Practices

1. **Question Formatting**
   - Be specific and clear
   - Include context when needed
   - Use consistent terminology

2. **Content Organization**
   - Group related posts
   - Maintain thread context
   - Preserve metadata

3. **Performance Optimization**
   - Use appropriate cache TTLs
   - Monitor response times
   - Implement rate limiting 