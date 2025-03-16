import { audiencesService } from '@/services/audiences';
import { X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

interface Audience {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  subreddit_names: string[];
  timeframe: string;
  posts_per_subreddit: number;
  is_collecting: boolean;
  collection_progress: number;
  post_count: number;
}

interface AudienceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  selectedSubreddits: string[];
  existingAudiences?: Audience[];
  onSuccess?: () => void;
}

export function AudienceDialog({ 
  isOpen, 
  onClose, 
  selectedSubreddits,
  existingAudiences = [],
  onSuccess
}: AudienceDialogProps) {
  const [mode, setMode] = useState<'new' | 'existing'>('new');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedAudienceId, setSelectedAudienceId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setMode('new');
      setName('');
      setDescription('');
      setSelectedAudienceId(null);
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      let response;
      const isNewAudience = mode === 'new';
      
      if (isNewAudience) {
        // Create new audience
        response = await audiencesService.createAudience({
          name,
          description: description || null,
          subreddit_names: selectedSubreddits,
          timeframe: "year",  // Default to year timeframe
          posts_per_subreddit: 500  // Default to 500 posts per subreddit
        });
      } else {
        // Get existing audience
        if (!selectedAudienceId) {
          throw new Error('No audience selected');
        }
        const existingAudience = existingAudiences.find(a => a.id === selectedAudienceId);
        if (!existingAudience) {
          throw new Error('Selected audience not found');
        }

        // Create a Set to remove duplicates
        const uniqueSubreddits = new Set([
          ...existingAudience.subreddit_names,
          ...selectedSubreddits
        ]);

        // Add to existing audience
        response = await audiencesService.updateAudience(selectedAudienceId, {
          name: existingAudience.name,
          description: existingAudience.description,
          subreddit_names: Array.from(uniqueSubreddits)
        });
      }
      
      // Show success toast
      toast.success(
        isNewAudience 
          ? `Created audience "${response.name}" with ${response.subreddit_names.length} subreddits`
          : `Added ${selectedSubreddits.length} subreddits to "${response.name}"`
      );

      // Call onSuccess callback and close modal immediately
      onSuccess?.();
      onClose();
    } catch (err) {
      console.error('Error:', err);
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      toast.error(errorMessage);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {mode === 'new' ? 'Create New Audience' : 'Add to Existing Audience'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4 bg-white dark:bg-gray-800">
          <div className="flex gap-4 mb-4">
            <button
              type="button"
              onClick={() => setMode('new')}
              className={`flex-1 py-2 px-4 rounded-md transition-colors ${
                mode === 'new'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600'
              }`}
            >
              Create New
            </button>
            <button
              type="button"
              onClick={() => setMode('existing')}
              className={`flex-1 py-2 px-4 rounded-md transition-colors ${
                mode === 'existing'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600'
              }`}
              disabled={existingAudiences.length === 0}
            >
              Add to Existing
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {mode === 'new' ? (
              <>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                      Audience Name
                    </label>
                    <input
                      type="text"
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                      Description (Optional)
                    </label>
                    <textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      rows={3}
                    />
                  </div>
                </div>
              </>
            ) : (
              <div>
                <label htmlFor="audience" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                  Select Audience
                </label>
                <select
                  id="audience"
                  value={selectedAudienceId || ''}
                  onChange={(e) => setSelectedAudienceId(Number(e.target.value))}
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required
                >
                  <option value="">Select an audience...</option>
                  {existingAudiences.map((audience) => (
                    <option key={audience.id} value={audience.id}>
                      {audience.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {error && (
              <div className="mt-4 text-sm text-red-500">
                {error}
              </div>
            )}

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={mode === 'existing' && !selectedAudienceId}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {mode === 'new' ? 'Create Audience' : 'Add to Audience'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
} 