import type { Subreddit } from '../types/subreddit';
import { apiClient } from './apiClient';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface SearchSubredditsResponse {
  subreddits: Subreddit[];
}

export interface SearchFilters {
  minSubscribers?: number;
  maxSubscribers?: number;
  minActiveUsers?: number;
  maxActiveUsers?: number;
  category?: string;
}

export interface GetSubredditPostsResponse {
  posts: Array<{
    id: string;
    title: string;
    content: string;
    url: string;
    score: number;
    created_at: string;
    author: string;
    permalink: string;
    num_comments: number;
    subreddit: string;
    thumbnail: string | null;
    is_self: boolean;
  }>;
}

export const subredditsService = {
  async searchSubreddits(query: string, filters?: SearchFilters, limit: number = 10): Promise<Subreddit[]> {
    const params = new URLSearchParams({
      query: query,
      limit: limit.toString(),
      ...(filters?.minSubscribers && { min_subscribers: filters.minSubscribers.toString() }),
      ...(filters?.maxSubscribers && { max_subscribers: filters.maxSubscribers.toString() }),
      ...(filters?.minActiveUsers && { min_active_users: filters.minActiveUsers.toString() }),
      ...(filters?.maxActiveUsers && { max_active_users: filters.maxActiveUsers.toString() }),
      ...(filters?.category && { category: filters.category }),
    });
    const response = await apiClient.get<Subreddit[]>(`/subreddits/search?${params.toString()}`);
    return response;
  },

  async getSubredditInfo(subredditName: string): Promise<Subreddit> {
    const response = await apiClient.get<Subreddit>(`/subreddits/${subredditName}`);
    return response;
  },

  async getSubredditPosts(subredditName: string, limit: number = 10): Promise<GetSubredditPostsResponse> {
    const response = await apiClient.get<GetSubredditPostsResponse>(`/subreddits/${subredditName}/posts?limit=${limit}`);
    return response;
  }
};

export const searchSubreddits = async (query: string, filters?: SearchFilters): Promise<Subreddit[]> => {
  try {
    const params = new URLSearchParams({
      query,
      limit: '10', // Set a default limit of 10
      ...(filters?.minSubscribers && { min_subscribers: filters.minSubscribers.toString() }),
      ...(filters?.maxSubscribers && { max_subscribers: filters.maxSubscribers.toString() }),
      ...(filters?.minActiveUsers && { min_active_users: filters.minActiveUsers.toString() }),
      ...(filters?.maxActiveUsers && { max_active_users: filters.maxActiveUsers.toString() }),
      ...(filters?.category && { category: filters.category })
    });

    const response = await fetch(`${API_BASE_URL}/subreddits/search?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch subreddits');
    }
    return await response.json();
  } catch (error) {
    console.error('Error searching subreddits:', error);
    throw error;
  }
}; 