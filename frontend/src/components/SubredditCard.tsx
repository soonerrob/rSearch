import { formatNumber } from '@/lib/utils';
import { Subreddit } from '@/types/subreddit';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { Check, Users } from 'lucide-react';

interface SubredditListItemProps {
  subreddit: Subreddit;
  isSelected: boolean;
  onSelect: (subreddit: Subreddit) => void;
}

export function SubredditListItem({ subreddit, isSelected, onSelect }: SubredditListItemProps) {
  console.log('Subreddit data:', {
    name: subreddit.name,
    created_at: subreddit.created_at,
  });

  // Format the creation date if available
  let createdText = '';
  if (subreddit.created_at) {
    try {
      createdText = `Created ${formatDistanceToNow(parseISO(subreddit.created_at))} ago`;
      console.log('Formatted date:', createdText);
    } catch (error) {
      console.error('Error formatting date:', error);
      createdText = `Created ${new Date(subreddit.created_at).toLocaleDateString()}`;
    }
  }
  
  // Format posts per day if available
  const postsPerDay = subreddit.posts_per_day 
    ? `${subreddit.posts_per_day.toFixed(1)} posts/day` 
    : '';
  
  // Combine stats with bullet separator if both exist
  const stats = [createdText, postsPerDay].filter(Boolean).join(' • ');

  return (
    <div 
      onClick={() => onSelect(subreddit)}
      className={`flex items-center gap-4 px-4 py-3 rounded-lg mb-2 cursor-pointer transition-colors bg-gray-50 dark:bg-gray-800 ${
        isSelected 
          ? 'bg-accent-primary/10 dark:bg-accent-primary/20' 
          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
      }`}
    >
      {/* Selection indicator */}
      <div className={`flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center ${
        isSelected 
          ? 'border-accent-primary bg-accent-primary text-white' 
          : 'border-gray-300 dark:border-gray-600'
      }`}>
        {isSelected && <Check className="w-3 h-3" />}
      </div>

      {/* Subreddit info */}
      <div className="flex flex-grow items-start justify-between min-w-0">
        <div className="flex flex-col min-w-0">
          <div className="flex items-baseline gap-2">
            <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 truncate">
              r/{subreddit.name}
            </h3>
          </div>
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Users className="w-3 h-3" />
            <span>{formatNumber(subreddit.subscribers || 0)} subscribers</span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1">
          {/* Always show stats container even if empty */}
          <div className="text-xs text-gray-500">
            {stats || 'No stats available'}
          </div>
          {subreddit.active_users && (
            <div className="text-xs font-medium text-emerald-600">
              {formatNumber(subreddit.active_users)} active now
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 