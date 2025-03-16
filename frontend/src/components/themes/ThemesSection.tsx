import { Card, CardContent } from '@/components/ui/card';
import { Theme, ThemeState, ThemeTab } from '@/types/themes';
import { useState } from 'react';
import ThemePanel from './ThemePanel';

const mockThemes: Theme[] = [
  {
    id: '1',
    category: 'Hot Discussions',
    title: 'Most Engaged Topics This Week',
    summary: 'Top discussions from the community this week...',
    postCount: 156,
    lastUpdated: new Date().toISOString(),
  },
  {
    id: '2',
    category: 'Advice Requests',
    title: 'Common Questions & Guidance',
    summary: 'Popular advice requests from the community...',
    postCount: 89,
    lastUpdated: new Date().toISOString(),
  },
  // Add more mock themes as needed
];

export default function ThemesSection() {
  const [state, setState] = useState<ThemeState>({
    selectedTheme: null,
    selectedTab: 'browse',
    isOpen: false,
    questions: [],
    recentQuestions: [],
  });

  const handleThemeClick = (theme: Theme) => {
    setState(prev => ({
      ...prev,
      selectedTheme: theme,
      isOpen: true,
      selectedTab: 'browse',
    }));
  };

  const handleClose = () => {
    setState(prev => ({
      ...prev,
      isOpen: false,
    }));
  };

  const handleTabChange = (tab: ThemeTab) => {
    setState(prev => ({
      ...prev,
      selectedTab: tab,
    }));
  };

  return (
    <div className="w-full p-6 space-y-6">
      <h2 className="text-2xl font-bold tracking-tight">Themes</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockThemes.map((theme) => (
          <Card 
            key={theme.id}
            className="cursor-pointer hover:bg-slate-50 transition-colors"
            onClick={() => handleThemeClick(theme)}
          >
            <CardContent className="p-6">
              <h3 className="font-semibold text-lg mb-2">{theme.category}</h3>
              <p className="text-sm text-slate-600 mb-4">{theme.title}</p>
              <div className="flex justify-between text-xs text-slate-500">
                <span>{theme.postCount} posts</span>
                <span>Updated {new Date(theme.lastUpdated).toLocaleDateString()}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {state.selectedTheme && (
        <ThemePanel
          theme={state.selectedTheme}
          isOpen={state.isOpen}
          selectedTab={state.selectedTab}
          onClose={handleClose}
          onTabChange={handleTabChange}
          questions={state.questions}
          recentQuestions={state.recentQuestions}
        />
      )}
    </div>
  );
} 