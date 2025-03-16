import { audiencesService } from '@/services/audiences';
import { X } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

interface Audience {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  subreddit_names: string[];
  timeframe: string;
  posts_per_subreddit: number;
  is_collecting: boolean;
  collection_progress: number;
}

interface EditAudienceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  audience: Audience;
  onSuccess?: () => void;
}

export function EditAudienceDialog({ 
  isOpen, 
  onClose, 
  audience,
  onSuccess
}: EditAudienceDialogProps) {
  const [name, setName] = useState(audience.name);
  const [description, setDescription] = useState(audience.description || '');
  const [selectedSubreddits, setSelectedSubreddits] = useState<Set<string>>(
    new Set(audience.subreddit_names)
  );
  const [timeframe, setTimeframe] = useState(audience.timeframe);
  const [postsPerSubreddit, setPostsPerSubreddit] = useState(audience.posts_per_subreddit);
  const [postsInputError, setPostsInputError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRemoveSubreddit = (subreddit: string) => {
    const newSubreddits = new Set(selectedSubreddits);
    newSubreddits.delete(subreddit);
    setSelectedSubreddits(newSubreddits);
  };

  const handlePostsPerSubredditChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value);
    setPostsPerSubreddit(value);
    
    // Validate the input
    if (value < 1) {
      setPostsInputError('Must collect at least 1 post per subreddit');
    } else if (value > 500) {
      setPostsInputError('Maximum 500 posts per subreddit allowed');
    } else {
      setPostsInputError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    // Validate posts per subreddit before submission
    if (postsPerSubreddit < 1 || postsPerSubreddit > 500) {
      setError('Invalid number of posts per subreddit');
      return;
    }
    
    setIsLoading(true);

    try {
      const data = await audiencesService.updateAudience(audience.id, {
        name,
        description: description || null,
        subreddit_names: Array.from(selectedSubreddits),
        timeframe,
        posts_per_subreddit: postsPerSubreddit
      });

      toast.success(`Updated audience "${data.name}"`);
      onSuccess?.();
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-2xl w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Audience
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="timeframe" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                  Timeframe
                </label>
                <select
                  id="timeframe"
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="hour">Last Hour</option>
                  <option value="day">Last 24 Hours</option>
                  <option value="week">Last Week</option>
                  <option value="month">Last Month</option>
                  <option value="year">Last Year</option>
                </select>
              </div>

              <div>
                <label htmlFor="postsPerSubreddit" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                  Posts per Subreddit
                  <span className="ml-1 text-xs text-gray-500">(Max: 500)</span>
                </label>
                <input
                  type="number"
                  id="postsPerSubreddit"
                  value={postsPerSubreddit}
                  onChange={handlePostsPerSubredditChange}
                  min={1}
                  max={500}
                  className={`w-full rounded-md border ${
                    postsInputError 
                      ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
                      : 'border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-blue-500'
                  } bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-1`}
                  aria-invalid={!!postsInputError}
                  aria-describedby={postsInputError ? "posts-error" : undefined}
                />
                {postsInputError && (
                  <p id="posts-error" className="mt-1 text-sm text-red-500">
                    {postsInputError}
                  </p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                Subreddits ({selectedSubreddits.size})
              </label>
              <div className="border border-gray-200 dark:border-gray-700 rounded-md p-4 max-h-64 overflow-y-auto">
                {selectedSubreddits.size === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    No subreddits in this audience
                  </p>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {Array.from(selectedSubreddits).map((subreddit) => (
                      <div
                        key={subreddit}
                        className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded px-3 py-2"
                      >
                        <span className="text-sm text-gray-900 dark:text-gray-100 truncate">
                          r/{subreddit}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveSubreddit(subreddit)}
                          className="ml-2 text-gray-400 hover:text-red-500 dark:text-gray-500 dark:hover:text-red-400"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

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
              disabled={isLoading || selectedSubreddits.size === 0}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 