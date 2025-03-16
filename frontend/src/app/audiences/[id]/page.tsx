'use client';

import { ThemesList } from '@/components/ThemesList';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { audienceApi, themesApi } from '@/lib/api';
import { Audience } from '@/types/audience';
import { Hourglass, RefreshCw, Settings, Users } from 'lucide-react';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

const timeframeOptions = [
  { value: 'hour', label: 'Last Hour' },
  { value: 'day', label: 'Last 24 Hours' },
  { value: 'week', label: 'Last Week' },
  { value: 'month', label: 'Last Month' },
  { value: 'year', label: 'Last Year' }
];

export default function AudienceDetailPage() {
  const params = useParams();
  const [audience, setAudience] = useState<Audience | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [tempSettings, setTempSettings] = useState({
    timeframe: '',
    posts_per_subreddit: 0
  });

  const audienceId = params?.id ? parseInt(params.id as string, 10) : null;

  useEffect(() => {
    const fetchAudience = async () => {
      if (!audienceId) return;
      
      try {
        setIsLoading(true);
        setError(null);
        const data = await audienceApi.getAudience(audienceId);
        setAudience(data);
        setTempSettings({
          timeframe: data.timeframe,
          posts_per_subreddit: data.posts_per_subreddit
        });
      } catch (err) {
        console.error('Error fetching audience:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch audience');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAudience();
  }, [audienceId]);

  const handleRefreshThemes = async () => {
    if (!audienceId || !audience) return;
    
    try {
      setIsRefreshing(true);
      // First update the settings
      const updatedAudience = await audienceApi.updateAudience(audienceId, {
        ...audience,
        timeframe: tempSettings.timeframe,
        posts_per_subreddit: tempSettings.posts_per_subreddit
      });
      setAudience(updatedAudience);
      // Then refresh themes
      await themesApi.refreshAudienceThemes(audienceId);
      // Close settings after successful refresh
      setShowSettings(false);
    } catch (err) {
      console.error('Error refreshing themes:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!audienceId) {
    return <div>Error: No audience ID provided</div>;
  }

  if (isLoading) {
    return <div>Loading audience details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!audience) {
    return <div>No audience found</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Users className="h-8 w-8 text-accent-primary" />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-primary">{audience.name}</h1>
                {audience.is_collecting && (
                  <div className="flex items-center gap-1">
                    <Hourglass className="h-5 w-5 text-blue-500 dark:text-blue-400 animate-spin" />
                    <span className="text-sm text-blue-500 dark:text-blue-400 animate-pulse">
                      Collecting data...
                    </span>
                  </div>
                )}
              </div>
              {audience.description && (
                <p className="text-muted">{audience.description}</p>
              )}
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {showSettings && (
        <Card className="p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Theme Collection Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Time Period</label>
              <Select
                value={tempSettings.timeframe}
                onValueChange={(value) => setTempSettings(prev => ({ ...prev, timeframe: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {timeframeOptions.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Posts per Subreddit</label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  value={tempSettings.posts_per_subreddit}
                  min={1}
                  max={1000}
                  onChange={(e) => {
                    const value = parseInt(e.target.value, 10);
                    if (!isNaN(value) && value >= 1 && value <= 1000) {
                      setTempSettings(prev => ({ ...prev, posts_per_subreddit: value }));
                    }
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Number of posts to collect from each subreddit (1-1000)
              </p>
            </div>
            <div className="flex gap-2 pt-2">
              <Button 
                onClick={handleRefreshThemes} 
                disabled={isRefreshing}
                className="flex-1"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Applying Settings & Refreshing...' : 'Apply Settings & Refresh Themes'}
              </Button>
              <Button 
                onClick={() => {
                  // Reset temp settings to current values when canceling
                  setTempSettings({
                    timeframe: audience.timeframe,
                    posts_per_subreddit: audience.posts_per_subreddit
                  });
                  setShowSettings(false);
                }}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Click "Apply Settings & Refresh" to update collection settings and gather new posts
            </p>
          </div>
        </Card>
      )}

      <div className="space-y-8">
        <div className="bg-card-bg border border-card-border rounded-lg p-6">
          <ThemesList audienceId={audienceId} refreshing={isRefreshing} />
        </div>
      </div>
    </div>
  );
} 