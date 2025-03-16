export interface Subreddit {
  name: string;
  display_name: string;
  description: string | null;
  subscribers: number | null;
  active_users: number | null;
  posts_per_day: number | null;
  comments_per_day: number | null;
  growth_rate: number | null;
  relevance_score: number | null;
  created_at: string | null;
  updated_at: string | null;
  last_updated: string | null;
}

export interface SubredditResponse {
  data: Subreddit[];
  status: number;
  message?: string;
} 