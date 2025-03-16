import { apiClient } from './apiClient';

export interface Audience {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  subreddit_names: string[];
  timeframe: string;
  posts_per_subreddit: number;
  is_collecting: boolean;
  collection_progress: number;
  post_count: number;
}

export interface CreateAudienceRequest {
  name: string;
  description?: string | null;
  subreddit_names: string[];
  timeframe: string;
  posts_per_subreddit: number;
}

export interface UpdateAudienceRequest {
  name?: string;
  description?: string | null;
  subreddit_names?: string[];
  timeframe?: string;
  posts_per_subreddit?: number;
}

export const audiencesService = {
  async createAudience(data: CreateAudienceRequest): Promise<Audience> {
    return apiClient.post<Audience>('/api/audiences', data);
  },

  async getAudiences(): Promise<Audience[]> {
    return apiClient.get<Audience[]>('/api/audiences');
  },

  async getAudience(audienceId: number): Promise<Audience> {
    return apiClient.get<Audience>(`/api/audiences/${audienceId}`);
  },

  async updateAudience(audienceId: number, data: UpdateAudienceRequest): Promise<Audience> {
    return apiClient.patch<Audience>(`/api/audiences/${audienceId}`, data);
  },

  async deleteAudience(audienceId: number): Promise<void> {
    return apiClient.delete(`/api/audiences/${audienceId}`);
  },

  async collectInitialData(audienceId: number): Promise<void> {
    return apiClient.post(`/api/audiences/${audienceId}/collect-initial-data`);
  }
};