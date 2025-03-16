import { cn } from '@/lib/utils';
import { Filter, Loader2, MessageSquare, SlidersHorizontal, Users, X } from 'lucide-react';
import { useEffect, useState } from 'react';

export interface SearchFilters {
  minSubscribers?: number;
  maxSubscribers?: number;
  minActiveUsers?: number;
  maxActiveUsers?: number;
  category?: string;
}

interface SearchFiltersProps {
  onFiltersChange: (filters: SearchFilters) => void;
  className?: string;
  isLoading?: boolean;
  currentFilters?: SearchFilters;
}

const CATEGORIES = [
  'All',
  'Technology',
  'Gaming',
  'Entertainment',
  'Science',
  'Sports',
  'News',
  'Art',
  'Music',
  'Education',
  'Business',
] as const;

export function SearchFilters({ onFiltersChange, className, isLoading = false, currentFilters = {} }: SearchFiltersProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>(currentFilters);

  // Update internal filters when currentFilters prop changes
  useEffect(() => {
    setFilters(currentFilters);
  }, [currentFilters]);

  const handleFilterChange = (key: keyof SearchFilters, value: number | string | undefined) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearFilters = () => {
    const emptyFilters = {};
    setFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  const activeFilterCount = Object.keys(filters).filter(key => 
    filters[key as keyof SearchFilters] !== undefined && 
    filters[key as keyof SearchFilters] !== 'All'
  ).length;

  return (
    <div className={cn("relative", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <SlidersHorizontal className="h-4 w-4" />
        <span>Filters</span>
        {activeFilterCount > 0 && (
          <span className="flex items-center justify-center w-5 h-5 text-xs font-medium rounded-full bg-accent-primary text-white">
            {activeFilterCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-64 rounded-lg border bg-card text-card-foreground p-3 shadow-lg z-50">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium">Filters</h3>
              {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            </div>
            <div className="flex items-center gap-2">
              {activeFilterCount > 0 && (
                <button
                  onClick={clearFilters}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear all
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          <div className="space-y-3">
            {/* Subscriber Range */}
            <div>
              <label className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                <Users className="h-3.5 w-3.5" />
                Subscriber Range
              </label>
              <div className="mt-1 grid grid-cols-2 gap-1.5">
                <input
                  type="number"
                  placeholder="Min"
                  className="rounded-md border bg-background text-foreground px-2 py-1 text-xs"
                  value={filters.minSubscribers || ''}
                  onChange={(e) => handleFilterChange('minSubscribers', e.target.value ? Number(e.target.value) : undefined)}
                />
                <input
                  type="number"
                  placeholder="Max"
                  className="rounded-md border bg-background text-foreground px-2 py-1 text-xs"
                  value={filters.maxSubscribers || ''}
                  onChange={(e) => handleFilterChange('maxSubscribers', e.target.value ? Number(e.target.value) : undefined)}
                />
              </div>
            </div>

            {/* Active Users Range */}
            <div>
              <label className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                <MessageSquare className="h-3.5 w-3.5" />
                Active Users Range
              </label>
              <div className="mt-1 grid grid-cols-2 gap-1.5">
                <input
                  type="number"
                  placeholder="Min"
                  className="rounded-md border bg-background text-foreground px-2 py-1 text-xs"
                  value={filters.minActiveUsers || ''}
                  onChange={(e) => handleFilterChange('minActiveUsers', e.target.value ? Number(e.target.value) : undefined)}
                />
                <input
                  type="number"
                  placeholder="Max"
                  className="rounded-md border bg-background text-foreground px-2 py-1 text-xs"
                  value={filters.maxActiveUsers || ''}
                  onChange={(e) => handleFilterChange('maxActiveUsers', e.target.value ? Number(e.target.value) : undefined)}
                />
              </div>
            </div>

            {/* Categories */}
            <div>
              <label className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                <Filter className="h-3.5 w-3.5" />
                Category
              </label>
              <select
                className="mt-1 w-full rounded-md border bg-background text-foreground px-2 py-1 text-xs"
                onChange={(e) => handleFilterChange('category', e.target.value)}
                value={filters.category || 'All'}
              >
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 