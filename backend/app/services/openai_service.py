import logging
from datetime import datetime, timedelta
from functools import lru_cache
from math import ceil
from typing import Dict, List, Optional

import openai
from app.core.cache import get_cache
from app.core.config import get_settings

settings = get_settings()
openai.api_key = settings.OPENAI_API_KEY
cache = get_cache()

logger = logging.getLogger(__name__)

async def analyze_posts_for_answer(
    question: str,
    posts: List[Dict],
    comments: Optional[List[Dict]] = None,
    max_tokens: int = 1000,
    max_context_length: int = 4000
) -> Dict[str, str]:
    """
    Analyze posts and comments to generate an answer to a question.
    
    Args:
        question: The user's question
        posts: List of posts to analyze
        comments: Optional list of comments to include in analysis
        max_tokens: Maximum tokens for response
        max_context_length: Maximum context length to send to API
        
    Returns:
        Dict containing answer, confidence level, and sources
    """
    try:
        # Check cache first
        cache_key = f"qa:{hash(question)}:{hash(str(posts))}"
        cached_response = await cache.get(cache_key)
        if cached_response:
            return cached_response

        # Sort posts by engagement score
        sorted_posts = sorted(
            posts,
            key=lambda x: (x.get('score', 0) + x.get('num_comments', 0)) * x.get('engagement_score', 1.0),
            reverse=True
        )

        # Prepare context with posts and comments
        context = _prepare_context(sorted_posts, comments, max_context_length)
        
        # Get appropriate system message
        system_message = _get_system_message(question)
        
        # Make API call with GPT-4 if available, fallback to GPT-3.5-turbo
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
        except openai.error.InvalidRequestError:
            # Fallback to GPT-3.5-turbo if GPT-4 is not available
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
        
        # Calculate confidence based on multiple factors
        confidence = _calculate_confidence(
            question=question,
            posts=sorted_posts,
            comments=comments,
            response_content=response.choices[0].message.content
        )
        
        # Extract sources with detailed attribution
        sources = _extract_sources(sorted_posts[:5], comments)
        
        result = {
            "answer": response.choices[0].message.content.strip(),
            "confidence": confidence,
            "sources": sources,
            "model": response.model,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        # Cache the response for 1 hour
        await cache.set(cache_key, result, expire=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise

def _prepare_context(
    posts: List[Dict],
    comments: Optional[List[Dict]],
    max_length: int
) -> str:
    """Prepare context from posts and comments for AI analysis."""
    context = "Based on the following Reddit content:\n\n"
    current_length = len(context)
    
    # Process posts first
    for i, post in enumerate(posts, 1):
        post_text = f"Post {i}:\n"
        post_text += f"Title: {post.get('title', '')}\n"
        post_text += f"Content: {post.get('content', '')}\n"
        post_text += f"Score: {post.get('score', 0)}, Comments: {post.get('num_comments', 0)}\n"
        post_text += f"Engagement Score: {post.get('engagement_score', 0):.2f}\n"
        
        # Add post comments if available
        if comments:
            post_comments = _organize_comments_thread(
                [c for c in comments if c.get('post_id') == post.get('id')]
            )
            if post_comments:
                post_text += "Discussion Threads:\n"
                post_text += _format_comment_threads(post_comments)
        
        post_text += "\n"
        
        # Check if adding this post would exceed max length
        if current_length + len(post_text) > max_length:
            break
            
        context += post_text
        current_length += len(post_text)
    
    return context

def _organize_comments_thread(comments: List[Dict]) -> List[Dict]:
    """Organize comments into a threaded structure."""
    # Sort by score and engagement
    sorted_comments = sorted(
        comments,
        key=lambda x: (x.get('score', 0) * x.get('engagement_score', 1.0)),
        reverse=True
    )
    
    # Create lookup of parent to children
    children = {}
    for comment in sorted_comments:
        parent_id = comment.get('parent_comment_id')
        if parent_id not in children:
            children[parent_id] = []
        children[parent_id].append(comment)
    
    # Get top-level comments
    top_comments = children.get(None, [])[:3]  # Limit to top 3 threads
    
    # Build threads recursively
    def build_thread(comment, depth=0):
        thread = {
            'comment': comment,
            'depth': depth,
            'children': []
        }
        # Add up to 3 best child comments, up to depth 3
        if depth < 3 and comment.get('id') in children:
            thread['children'] = [
                build_thread(child, depth + 1)
                for child in children[comment.get('id')][:3]
            ]
        return thread
    
    return [build_thread(comment) for comment in top_comments]

def _format_comment_threads(threads: List[Dict], indent: str = "") -> str:
    """Format threaded comments for context."""
    result = ""
    for thread in threads:
        comment = thread['comment']
        result += f"{indent}{'  ' * thread['depth']}- {comment.get('content', '')} "
        result += f"(Score: {comment.get('score', 0)})\n"
        if thread['children']:
            result += _format_comment_threads(thread['children'], indent + "  ")
    return result

def _calculate_confidence(
    question: str,
    posts: List[Dict],
    comments: Optional[List[Dict]],
    response_content: str
) -> float:
    """Calculate confidence score based on multiple factors."""
    confidence = 0.5  # Base confidence
    
    # Factor 1: Data volume and quality
    if len(posts) >= 10:
        confidence += 0.1
    if comments and len(comments) >= 20:
        confidence += 0.1
    
    # Factor 2: Engagement levels
    avg_score = sum(p.get('score', 0) for p in posts) / len(posts) if posts else 0
    if avg_score > 50:
        confidence += 0.1
    
    # Factor 3: Answer comprehensiveness
    word_count = len(response_content.split())
    if word_count > 100:
        confidence += 0.1
    
    # Factor 4: Question-content relevance
    question_keywords = set(question.lower().split())
    content_text = ' '.join(p.get('title', '') + ' ' + p.get('content', '') for p in posts).lower()
    matching_keywords = question_keywords.intersection(set(content_text.split()))
    keyword_match_ratio = len(matching_keywords) / len(question_keywords)
    confidence += keyword_match_ratio * 0.1
    
    return min(1.0, confidence)

def _extract_sources(posts: List[Dict], comments: Optional[List[Dict]] = None) -> List[Dict]:
    """Extract detailed source information."""
    sources = []
    for post in posts:
        source = {
            "type": "post",
            "title": post.get('title'),
            "url": f"https://reddit.com{post.get('reddit_id')}",
            "score": post.get('score'),
            "engagement": post.get('engagement_score'),
            "timestamp": post.get('created_at'),
            "relevance": "primary"
        }
        sources.append(source)
        
        # Add top comment if available
        if comments:
            post_comments = [c for c in comments if c.get('post_id') == post.get('id')]
            if post_comments:
                best_comment = max(post_comments, key=lambda x: x.get('score', 0))
                sources.append({
                    "type": "comment",
                    "content_preview": best_comment.get('content', '')[:100],
                    "score": best_comment.get('score'),
                    "url": f"https://reddit.com{post.get('reddit_id')}",
                    "relevance": "supporting"
                })
    
    return sources

def _get_system_message(question: str) -> str:
    """Generate system message based on question type."""
    base_message = (
        "You are an expert analyst processing Reddit content. "
        "Analyze the provided posts and comments to answer the user's question. "
        "Consider both post content and comment discussions in your analysis. "
        "Focus on extracting insights that are supported by the data. "
        "\n\nProvide your response in the following format:\n"
        "1. Direct Answer: A clear, concise answer to the question\n"
        "2. Supporting Evidence: Key points from the posts/comments that support your answer\n"
        "3. Additional Context: Any relevant nuances or caveats\n"
        "4. Confidence Explanation: Why you believe this answer is reliable (or any uncertainties)\n"
    )
    
    # Add specific instructions based on question type
    if any(word in question.lower() for word in ['problem', 'issue', 'challenge']):
        base_message += (
            "\nFocus on:\n"
            "- Frequency and severity of reported problems\n"
            "- Common patterns in user frustrations\n"
            "- Any mentioned solutions or workarounds\n"
            "- Impact on users and their experiences"
        )
    elif any(word in question.lower() for word in ['trend', 'pattern', 'common']):
        base_message += (
            "\nFocus on:\n"
            "- Recurring themes across multiple posts\n"
            "- Changes in sentiment over time\n"
            "- Popular topics and discussions\n"
            "- User behavior patterns"
        )
    elif any(word in question.lower() for word in ['suggest', 'recommend', 'advice']):
        base_message += (
            "\nFocus on:\n"
            "- Most upvoted suggestions\n"
            "- Consensus among experienced users\n"
            "- Practical implementation details\n"
            "- Success stories and outcomes"
        )
    
    return base_message

async def analyze_theme_content(
    theme_posts: List[Dict],
    theme_comments: List[Dict],
    category: str
) -> Dict[str, str]:
    """
    Generate AI-powered analysis of a theme's content.
    
    Args:
        theme_posts: List of posts in the theme
        theme_comments: List of comments for the theme's posts
        category: Theme category name
    
    Returns:
        Dict containing summary and key insights
    """
    try:
        # Prepare context focusing on theme-specific content
        context = _prepare_theme_context(theme_posts, theme_comments, category)
        
        # Generate theme analysis prompt
        system_message = (
            f"You are analyzing content from the '{category}' theme in a Reddit community. "
            "Provide a comprehensive analysis including:\n"
            "1. A concise summary of the main discussion points\n"
            "2. Key insights and patterns\n"
            "3. Notable user sentiments and opinions\n"
            "4. Emerging trends or recurring topics"
        )
        
        # Make API call
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": context}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return {
            "summary": response.choices[0].message.content.strip(),
            "category": category,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing theme content: {str(e)}")
        raise

def _prepare_theme_context(
    posts: List[Dict],
    comments: List[Dict],
    category: str
) -> str:
    """Prepare theme-specific context for AI analysis."""
    context = f"Analyzing content from the '{category}' theme:\n\n"
    
    # Add high-level metrics
    total_score = sum(p.get('score', 0) for p in posts)
    total_comments = sum(p.get('num_comments', 0) for p in posts)
    avg_engagement = sum(p.get('engagement_score', 0) for p in posts) / len(posts) if posts else 0
    
    context += f"Overview:\n"
    context += f"- Total Posts: {len(posts)}\n"
    context += f"- Total Score: {total_score}\n"
    context += f"- Total Comments: {total_comments}\n"
    context += f"- Average Engagement: {avg_engagement:.2f}\n\n"
    
    # Add top posts with their best comments
    sorted_posts = sorted(posts, key=lambda x: x.get('engagement_score', 0), reverse=True)
    for i, post in enumerate(sorted_posts[:5], 1):
        context += f"Top Post {i}:\n"
        context += f"Title: {post.get('title', '')}\n"
        context += f"Content: {post.get('content', '')}\n"
        context += f"Score: {post.get('score', 0)}, Comments: {post.get('num_comments', 0)}\n"
        
        # Add top comments for this post
        post_comments = [c for c in comments if c.get('post_id') == post.get('id')]
        if post_comments:
            sorted_comments = sorted(post_comments, key=lambda x: x.get('engagement_score', 0), reverse=True)
            context += "Best Comments:\n"
            for j, comment in enumerate(sorted_comments[:3], 1):
                context += f"  {j}. {comment.get('content', '')}\n"
        
        context += "\n"
    
    return context 