import { themesService } from '@/services/themes';
import { Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

interface Theme {
  id: number;
  name: string;
  description: string;
  category: string;
  created_at: string;
  updated_at: string;
  audience_id: number;
  is_ai_based: boolean;
  status: string;
}

interface ThemesSectionProps {
  audienceId: number;
  onThemeSelected?: (theme: Theme) => void;
}

export function ThemesSection({ audienceId, onThemeSelected }: ThemesSectionProps) {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTheme, setSelectedTheme] = useState<Theme | null>(null);

  const fetchThemes = async () => {
    try {
      const data = await themesService.getThemesByAudience(audienceId);
      setThemes(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch themes';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThemes();
  }, [audienceId]);

  const handleThemeClick = (theme: Theme) => {
    setSelectedTheme(theme);
    onThemeSelected?.(theme);
  };

  const handleRefreshTheme = async (themeId: number) => {
    try {
      await themesService.requestThemeRefresh(themeId);
      toast.success('Theme refresh requested');
      fetchThemes(); // Refresh the themes list
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to refresh theme';
      toast.error(message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-accent-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg">
        {error}
      </div>
    );
  }

  const basicThemes = themes.filter(theme => !theme.is_ai_based);
  const aiThemes = themes.filter(theme => theme.is_ai_based);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4">Basic Themes</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {basicThemes.map(theme => (
            <div
              key={theme.id}
              className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                selectedTheme?.id === theme.id
                  ? 'border-accent-primary bg-accent-primary/5'
                  : 'border-gray-200 dark:border-gray-700 hover:border-accent-primary/50'
              }`}
              onClick={() => handleThemeClick(theme)}
            >
              <h3 className="font-medium mb-2">{theme.name}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{theme.description}</p>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-xs text-gray-500 dark:text-gray-500">
                  {new Date(theme.updated_at).toLocaleDateString()}
                </span>
                <span className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800">
                  {theme.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">AI-Based Themes</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {aiThemes.map(theme => (
            <div
              key={theme.id}
              className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                selectedTheme?.id === theme.id
                  ? 'border-accent-primary bg-accent-primary/5'
                  : 'border-gray-200 dark:border-gray-700 hover:border-accent-primary/50'
              }`}
              onClick={() => handleThemeClick(theme)}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{theme.name}</h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRefreshTheme(theme.id);
                  }}
                  className="text-xs px-2 py-1 rounded-full bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20"
                >
                  Refresh
                </button>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">{theme.description}</p>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-xs text-gray-500 dark:text-gray-500">
                  {new Date(theme.updated_at).toLocaleDateString()}
                </span>
                <span className="text-xs px-2 py-1 rounded-full bg-accent-primary/10 text-accent-primary">
                  AI Generated
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 