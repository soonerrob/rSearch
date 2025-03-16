export interface Theme {
  id: number;
  category: string;
  summary: string;
  created_at: string;
  updated_at: string;
  audience_id: number;
  post_count?: number;
  posts?: {
    id: number;
    title: string;
    url: string;
    score: number;
    num_comments: number;
    created_utc: string;
  }[];
} 