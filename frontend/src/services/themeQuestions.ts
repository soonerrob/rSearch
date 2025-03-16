import { API_BASE_URL } from '@/config';

export interface ThemeQuestion {
  id: number;
  theme_id: number;
  question: string;
  answer: string | null;
  created_at: string;
  updated_at: string;
  last_recalculated_at: string | null;
}

export interface CreateThemeQuestionRequest {
  theme_id: number;
  question: string;
}

export const createThemeQuestion = async (data: CreateThemeQuestionRequest): Promise<ThemeQuestion> => {
  const response = await fetch(`${API_BASE_URL}/theme-questions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to create theme question');
  }

  return response.json();
};

export const getThemeQuestions = async (themeId: number): Promise<ThemeQuestion[]> => {
  const response = await fetch(`${API_BASE_URL}/theme-questions/theme/${themeId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch theme questions');
  }

  return response.json();
};

export const recalculateThemeQuestion = async (questionId: number): Promise<ThemeQuestion> => {
  const response = await fetch(`${API_BASE_URL}/theme-questions/${questionId}/recalculate`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to recalculate theme question');
  }

  return response.json();
};

export const deleteThemeQuestion = async (questionId: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/theme-questions/${questionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete theme question');
  }
}; 