import { Theme } from './theme';

export type ThemeTab = 'browse' | 'patterns' | 'ask';

export interface ThemeQuestion {
  id: number;
  theme_id: number;
  question: string;
  answer: string | null;
  created_at: string;
  updated_at: string;
  last_recalculated_at: string | null;
}

export interface ThemeState {
  selectedTheme: Theme | null;
  selectedTab: ThemeTab;
  isOpen: boolean;
  questions: ThemeQuestion[];
} 