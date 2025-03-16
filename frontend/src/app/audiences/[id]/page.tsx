'use client';

import { ThemesList } from '@/components/ThemesList';
import { audienceApi } from '@/lib/api';
import { Audience } from '@/types/audience';
import { Hourglass, Users } from 'lucide-react';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function AudienceDetailPage() {
  const params = useParams();
  const [audience, setAudience] = useState<Audience | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const audienceId = params?.id ? parseInt(params.id as string, 10) : null;

  useEffect(() => {
    const fetchAudience = async () => {
      if (!audienceId) return;
      
      try {
        setIsLoading(true);
        setError(null);
        const data = await audienceApi.getAudience(audienceId);
        setAudience(data);
      } catch (err) {
        console.error('Error fetching audience:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch audience');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAudience();
  }, [audienceId]);

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
      </div>

      <div className="space-y-8">
        <div className="bg-card-bg border border-card-border rounded-lg p-6">
          <ThemesList audienceId={audienceId} />
        </div>
      </div>
    </div>
  );
} 