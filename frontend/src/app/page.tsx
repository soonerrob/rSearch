'use client';

import { AddToAudienceButton } from '@/components/AddToAudienceButton';
import { SearchBar } from '@/components/SearchBar';
import { SearchFilters, type SearchFilters as SearchFiltersType } from '@/components/SearchFilters';
import { SubredditListItem } from '@/components/SubredditCard';
import { subredditApi } from '@/lib/api';
import { Subreddit } from '@/types/subreddit';
import { useCallback, useState } from 'react';

export default function Home() {
  const [subreddits, setSubreddits] = useState<Subreddit[]>([]);
  const [selectedSubreddits, setSelectedSubreddits] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [currentFilters, setCurrentFilters] = useState<SearchFiltersType>({});

  const handleSearch = useCallback(async (query: string) => {
    if (query.trim()) {
      setIsSearching(true);
      setError(null);

      try {
        console.log('Searching with query:', query, 'and filters:', currentFilters);
        const data = await subredditApi.searchSubreddits(query, currentFilters);
        console.log('Search API response:', data);
        setSubreddits(data);
      } catch (err) {
        console.error('Search error:', err);
        setError(err instanceof Error ? err.message : 'Failed to search subreddits');
      } finally {
        setIsSearching(false);
      }
    } else {
      setSubreddits([]);
    }
  }, [currentFilters]);

  const handleFiltersChange = useCallback((filters: SearchFiltersType) => {
    console.log('Filters changed:', filters);
    setCurrentFilters(filters);
    // Trigger a new search with the current query and new filters
    const searchInput = document.querySelector('input[type="text"]') as HTMLInputElement;
    if (searchInput && searchInput.value.trim()) {
      handleSearch(searchInput.value.trim());
    }
  }, [handleSearch]);

  const applyFilters = useCallback((data: Subreddit[], shouldSort: boolean) => {
    console.log('Applying filters to data:', { dataLength: data.length, filters: currentFilters, shouldSort });
    const filtered = data
      .filter(sub => {
        // Basic validation
        if (!sub.display_name || !sub.name) return false;
        
        // Subscriber range filter
        if (currentFilters.minSubscribers !== undefined) {
          const minSubs = Number(currentFilters.minSubscribers);
          if (sub.subscribers === null || sub.subscribers < minSubs) {
            console.debug('Filtering out due to min subscribers:', { 
              subreddit: sub.name, 
              subscribers: sub.subscribers, 
              minRequired: minSubs 
            });
            return false;
          }
        }
        if (currentFilters.maxSubscribers !== undefined) {
          const maxSubs = Number(currentFilters.maxSubscribers);
          if (sub.subscribers === null || sub.subscribers > maxSubs) {
            console.debug('Filtering out due to max subscribers:', { 
              subreddit: sub.name, 
              subscribers: sub.subscribers, 
              maxAllowed: maxSubs 
            });
            return false;
          }
        }

        // Active users range filter
        if (currentFilters.minActiveUsers !== undefined) {
          const minActive = Number(currentFilters.minActiveUsers);
          if (sub.active_users === null || sub.active_users < minActive) {
            return false;
          }
        }
        if (currentFilters.maxActiveUsers !== undefined) {
          const maxActive = Number(currentFilters.maxActiveUsers);
          if (sub.active_users === null || sub.active_users > maxActive) {
            return false;
          }
        }

        // Category filter
        if (currentFilters.category && currentFilters.category !== 'All') {
          // This is a simple category check. You might want to implement more sophisticated
          // category detection based on subreddit metadata, description, or tags
          return sub.display_name.toLowerCase().includes(currentFilters.category.toLowerCase()) ||
                 (sub.description && sub.description.toLowerCase().includes(currentFilters.category.toLowerCase()));
        }

        return true;
      });

    // Only sort trending results, preserve search order
    if (shouldSort) {
      filtered.sort((a, b) => {
        // If both have subscribers, sort by that
        if (a.subscribers !== null && b.subscribers !== null) {
          return b.subscribers - a.subscribers;
        }
        // If only one has subscribers, put it first
        if (a.subscribers !== null) return -1;
        if (b.subscribers !== null) return 1;
        // If neither has subscribers, sort by active users
        if (a.active_users !== null && b.active_users !== null) {
          return b.active_users - a.active_users;
        }
        return 0;
      });
    }
    
    console.log('Filtered results:', { filteredLength: filtered.length });
    return filtered;
  }, [currentFilters]);

  const handleSubredditSelect = useCallback((subreddit: Subreddit) => {
    setSelectedSubreddits(prev => {
      const next = new Set(prev);
      if (next.has(subreddit.name)) {
        next.delete(subreddit.name);
      } else {
        next.add(subreddit.name);
      }
      return next;
    });
  }, []);

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8 space-y-4">
        <h1 className="text-4xl font-bold">Reddit Audience Research</h1>
        <div className="flex items-stretch gap-4">
          <div className="flex-1">
            <SearchBar 
              onSearch={handleSearch}
            />
          </div>
          <SearchFilters 
            onFiltersChange={handleFiltersChange}
            isLoading={isSearching}
            currentFilters={currentFilters}
          />
        </div>
      </div>

      {selectedSubreddits.size > 0 && (
        <div className="mb-4 flex items-center justify-between bg-accent-primary/5 px-4 py-3 rounded-lg">
          <div className="flex items-center gap-4">
            <span className="text-sm text-accent-primary">
              {selectedSubreddits.size} subreddit{selectedSubreddits.size === 1 ? '' : 's'} selected
            </span>
            <AddToAudienceButton
              selectedSubreddits={Array.from(selectedSubreddits)}
            />
          </div>
          <button
            onClick={() => setSelectedSubreddits(new Set())}
            className="text-sm text-accent-primary hover:text-accent-primary/80"
          >
            Clear selection
          </button>
        </div>
      )}
      
      {isSearching && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-100 p-4 text-red-700">
          {error}
        </div>
      )}

      {!isSearching && subreddits.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No subreddits found
        </div>
      )}

      <div className="space-y-4">
        {subreddits.map((subreddit) => (
          <SubredditListItem 
            key={subreddit.name}
            subreddit={subreddit}
            isSelected={selectedSubreddits.has(subreddit.name)}
            onSelect={handleSubredditSelect}
          />
        ))}
      </div>
    </main>
  );
}
