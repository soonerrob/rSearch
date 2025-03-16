import { cn } from '@/lib/utils';
import { Search, X } from 'lucide-react';
import { useEffect, useState } from 'react';

interface KeywordSuggestion {
  keyword: string;
  score: number;
  subreddit_count: number;
}

interface SearchBarProps {
  onSearch: (query: string) => void;
  className?: string;
  placeholder?: string;
  debounceMs?: number;
}

export function SearchBar({
  onSearch,
  className,
  placeholder = "Search subreddits to create an audience...",
  debounceMs = 300
}: SearchBarProps) {
  const [value, setValue] = useState('');
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<KeywordSuggestion[]>([]);

  // Fetch suggestions
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!value.trim()) {
        setSuggestions([]);
        return;
      }

      try {
        const response = await fetch(`http://localhost:8001/subreddits/suggest-keywords?query=${encodeURIComponent(value)}`);
        if (!response.ok) throw new Error('Failed to fetch suggestions');
        const data = await response.json();
        setSuggestions(data);
      } catch (error) {
        console.error('Error fetching suggestions:', error);
        setSuggestions([]);
      }
    };

    const timer = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(timer);
  }, [value]);

  // Handle search
  useEffect(() => {
    const timer = setTimeout(() => {
      const searchQuery = [...selectedKeywords, value].filter(Boolean).join(' ');
      onSearch(searchQuery);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [value, selectedKeywords, onSearch, debounceMs]);

  const handleRemoveKeyword = (keyword: string) => {
    setSelectedKeywords(selectedKeywords.filter(k => k !== keyword));
  };

  const handleSelectSuggestion = (suggestion: KeywordSuggestion) => {
    if (!selectedKeywords.includes(suggestion.keyword)) {
      setSelectedKeywords([...selectedKeywords, suggestion.keyword]);
      setSuggestions([]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className={cn(
        "relative flex items-center",
        className
      )}>
        <Search className="absolute left-3 h-4 w-4 text-gray-500" />
        <input
          type="text"
          value={value}
          onChange={handleInputChange}
          placeholder={selectedKeywords.length ? "" : placeholder}
          className="w-full rounded-md bg-gray-800 py-3 pl-9 pr-4 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary"
        />
      </div>

      {/* Selected Keywords */}
      <div className="flex flex-wrap gap-2">
        {selectedKeywords.map((keyword) => (
          <button
            key={keyword}
            onClick={() => handleRemoveKeyword(keyword)}
            className="group flex items-center gap-1 rounded-full bg-accent-primary/10 px-3 py-1 text-sm font-medium text-accent-primary hover:bg-accent-primary/20"
          >
            {keyword}
            <X className="h-3 w-3 text-accent-primary/50 group-hover:text-accent-primary" />
          </button>
        ))}
      </div>

      {/* Suggested Keywords as + Buttons */}
      {suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.keyword}
              onClick={() => handleSelectSuggestion(suggestion)}
              className="flex items-center gap-1 rounded-full bg-accent-primary px-3 py-1 text-sm text-white hover:bg-accent-primary/90"
            >
              <span>+</span>
              {suggestion.keyword}
            </button>
          ))}
        </div>
      )}
    </div>
  );
} 