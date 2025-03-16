'use client';

import { useToast } from '@/components/ui/use-toast';
import { getThemeQuestions } from '@/services/themeQuestions';
import { themesService } from '@/services/themes';
import { Theme } from '@/types/theme';
import { ThemeState, ThemeTab } from '@/types/themes';
import {
    DollarSign,
    Flame,
    Frown,
    HelpCircle,
    Lightbulb,
    LucideIcon,
    Megaphone,
    Newspaper,
    Target,
    Trophy,
    Wrench
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import ThemePanel from './themes/ThemePanel';

interface ThemesListProps {
  audienceId: number;
}

const THEME_ICONS: Record<string, LucideIcon> = {
  'Hot Discussions': Flame,
  'Top Content': Trophy,
  'Advice Requests': HelpCircle,
  'Solution Requests': Wrench,
  'Pain & Anger': Frown,
  'Money Talk': DollarSign,
  'Self-Promotion': Megaphone,
  'News': Newspaper,
  'Ideas': Lightbulb,
  'Opportunities': Target
};

export function ThemesList({ audienceId }: ThemesListProps) {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCollecting, setIsCollecting] = useState(false);
  const [themeState, setThemeState] = useState<ThemeState>({
    selectedTheme: null,
    selectedTab: 'browse',
    isOpen: false,
    questions: [],
  });
  const { toast } = useToast();

  const fetchQuestions = async (themeId: number) => {
    try {
      const questions = await getThemeQuestions(themeId);
      setThemeState(prev => ({
        ...prev,
        questions,
      }));
    } catch {
      toast({
        title: "Error",
        description: "Failed to fetch questions. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleThemeClick = (theme: Theme) => {
    setThemeState(prev => ({
      ...prev,
      selectedTheme: theme,
      isOpen: true,
      selectedTab: 'browse',
    }));
    fetchQuestions(theme.id);
  };

  const handleClose = () => {
    setThemeState(prev => ({
      ...prev,
      isOpen: false,
    }));
  };

  const handleTabChange = (tab: ThemeTab) => {
    setThemeState(prev => ({
      ...prev,
      selectedTab: tab,
    }));
    if (tab === 'ask' && themeState.selectedTheme) {
      fetchQuestions(themeState.selectedTheme.id);
    }
  };

  const fetchThemes = async () => {
    try {
      setLoading(true);
      setError(null);
      setIsCollecting(false);
      const data = await themesService.getThemesByAudience(audienceId);
      
      // Deduplicate themes by category
      const uniqueThemes = Object.values(
        data.reduce((acc: Record<string, Theme>, theme: Theme) => {
          // Only keep the most recent theme for each category
          if (!acc[theme.category] || theme.updated_at > acc[theme.category].updated_at) {
            acc[theme.category] = theme;
          }
          return acc;
        }, {})
      ) as Theme[];
      
      setThemes(uniqueThemes);
    } catch (err) {
      if (err instanceof Error && err.message.includes('202')) {
        setIsCollecting(true);
        setError('Initial data collection is in progress. Please wait.');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to fetch themes');
      }
    } finally {
      setLoading(false);
    }
  };

  // Combined effect for initial fetch and refreshing
  useEffect(() => {
    fetchThemes();
    
    // If collecting, poll every 5 seconds
    let interval: NodeJS.Timeout;
    if (isCollecting) {
      interval = setInterval(fetchThemes, 5000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [audienceId, isCollecting]);

  if (error) {
    return (
      <div className="p-4 text-center">
        <div className="flex items-center justify-center gap-2 text-accent-primary">
          {isCollecting && (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-accent-primary border-t-transparent" />
              <span>Collecting data...</span>
            </>
          )}
        </div>
        <div className={isCollecting ? "text-muted mt-2" : "text-red-500"}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Themes</h2>
      </div>

      {(loading || isCollecting) && <div className="text-center p-4">Loading themes...</div>}

      {/* Scoring-based themes section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Scoring-based themes</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {themes
            .filter(theme => ['Hot Discussions', 'Top Content'].includes(theme.category))
            .map((theme) => (
              <div 
                key={theme.id} 
                className="px-4 py-3 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                onClick={() => handleThemeClick(theme)}
              >
                <h3 className="font-medium mb-2 text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  {THEME_ICONS[theme.category] && React.createElement(THEME_ICONS[theme.category], { className: 'h-4 w-4' })}
                  {theme.category}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{theme.summary}</p>
                {theme.posts && theme.posts.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Top Posts:</h4>
                    <ul className="space-y-1">
                      {theme.posts.slice(0, 3).map((post) => (
                        <li key={post.id} className="text-sm">
                          <a 
                            href={post.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-accent-primary hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {post.title}
                          </a>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {post.score} points • {post.num_comments} comments
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
        </div>

        {/* AI-based themes section */}
        <h3 className="text-lg font-semibold mb-4">AI-based themes</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {themes
            .filter(theme => !['Hot Discussions', 'Top Content'].includes(theme.category))
            .map((theme) => (
              <div 
                key={theme.id} 
                className="px-4 py-3 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                onClick={() => handleThemeClick(theme)}
              >
                <h3 className="font-medium mb-2 text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  {THEME_ICONS[theme.category] && React.createElement(THEME_ICONS[theme.category], { className: 'h-4 w-4' })}
                  {theme.category}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{theme.summary}</p>
                {theme.posts && theme.posts.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Top Posts:</h4>
                    <ul className="space-y-1">
                      {theme.posts.slice(0, 3).map((post) => (
                        <li key={post.id} className="text-sm">
                          <a 
                            href={post.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-accent-primary hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {post.title}
                          </a>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {post.score} points • {post.num_comments} comments
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
        </div>
      </div>

      {themeState.selectedTheme && (
        <ThemePanel
          theme={themeState.selectedTheme}
          isOpen={themeState.isOpen}
          selectedTab={themeState.selectedTab}
          onClose={handleClose}
          onTabChange={handleTabChange}
          questions={themeState.questions}
          onQuestionsChange={() => themeState.selectedTheme && fetchQuestions(themeState.selectedTheme.id)}
        />
      )}
    </div>
  );
} 