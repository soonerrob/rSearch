import logging
from math import ceil
from typing import Dict, List

import openai
from app.core.config import get_settings

settings = get_settings()
openai.api_key = settings.OPENAI_API_KEY

async def analyze_posts_for_answer(question: str, posts: List[Dict], max_posts: int = 200) -> str:
    """Analyze posts to generate an answer to a question."""
    # Calculate average post length to determine how many posts to include
    avg_post_length = sum(len(post.get('title', '') + post.get('selftext', '')) for post in posts) / len(posts)
    num_posts = min(len(posts), int(max_posts * (1000 / avg_post_length)))
    
    # Sort posts by engagement and take top N
    sorted_posts = sorted(posts, key=lambda x: x['score'] + x['num_comments'], reverse=True)[:num_posts]
    
    # Prepare prompt
    prompt = f"Based on the following Reddit posts, {question}\n\n"
    for i, post in enumerate(sorted_posts, 1):
        prompt += f"Post {i}:\n"
        prompt += f"Title: {post['title']}\n"
        prompt += f"Content: {post['selftext']}\n"
        prompt += f"Score: {post['score']}, Comments: {post['num_comments']}\n\n"
    
    try:
        # Make async API call
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant analyzing Reddit posts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {str(e)}")
        raise 