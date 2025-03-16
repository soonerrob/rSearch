import { audiencesService, type Audience } from '@/services/audiences';
import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';

interface UseAudiencesReturn {
  audiences: Audience[];
  isLoading: boolean;
  error: string | null;
  refreshAudiences: () => Promise<void>;
  deleteAudience: (id: number) => Promise<void>;
}

export function useAudiences(): UseAudiencesReturn {
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAudiences = async () => {
    try {
      const data = await audiencesService.getAudiences();
      setAudiences(data);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch audiences';
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshAudiences = useCallback(async () => {
    setIsLoading(true);
    await fetchAudiences();
  }, []);

  const deleteAudience = useCallback(async (id: number) => {
    try {
      const audience = audiences.find(a => a.id === id);
      await audiencesService.deleteAudience(id);
      
      // Optimistically update the UI
      setAudiences(prev => prev.filter(a => a.id !== id));
      toast.success(`Deleted audience "${audience?.name || 'Unknown'}"`);
      
      // Refresh to ensure we're in sync with the server
      await refreshAudiences();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete audience';
      toast.error(message);
      throw err; // Re-throw to let the component handle the error if needed
    }
  }, [audiences, refreshAudiences]);

  useEffect(() => {
    fetchAudiences();
  }, []);

  return {
    audiences,
    isLoading,
    error,
    refreshAudiences,
    deleteAudience,
  };
} 