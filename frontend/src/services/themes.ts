import type { Theme } from '../types/theme';
import { apiClient } from './apiClient';

export interface CreateThemeRequest {
  audience_id: number;
  name: string;
  description: string;
}

export interface UpdateThemeRequest {
  name?: string;
  description?: string;
}

export const themesService = {
  async createTheme(data: CreateThemeRequest): Promise<Theme> {
    return apiClient.post<Theme>('/api/themes', data);
  },

  async getThemesByAudience(audienceId: number): Promise<Theme[]> {
    return apiClient.get<Theme[]>(`/api/themes/audience/${audienceId}`);
  },

  async getTheme(themeId: number): Promise<Theme> {
    return apiClient.get<Theme>(`/api/themes/${themeId}`);
  },

  async updateTheme(themeId: number, data: UpdateThemeRequest): Promise<Theme> {
    return apiClient.patch<Theme>(`/api/themes/${themeId}`, data);
  },

  async deleteTheme(themeId: number): Promise<void> {
    return apiClient.delete(`/api/themes/${themeId}`);
  },

  async requestThemeRefresh(themeId: number): Promise<void> {
    return apiClient.post(`/api/themes/${themeId}/refresh`);
  },

  async refreshAudienceThemes(audienceId: number): Promise<Theme[]> {
    return apiClient.post<Theme[]>(`/api/themes/audience/${audienceId}/refresh`);
  }
}; 