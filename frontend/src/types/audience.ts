export interface Audience {
  id: number;
  name: string;
  description?: string;
  created_at?: string;
  subreddits?: string[];
  timeframe: string;
  posts_per_subreddit: number;
  is_collecting: boolean;
  collection_progress: number;
  subreddit_names: string[];
  post_count: number;
} 