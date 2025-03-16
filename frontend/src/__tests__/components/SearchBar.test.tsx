import { SearchBar } from '@/components/SearchBar';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('SearchBar', () => {
  const mockOnSearch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();
  });

  it('renders with default placeholder', () => {
    render(<SearchBar onSearch={mockOnSearch} />);
    expect(screen.getByPlaceholderText('Search subreddits to create an audience...')).toBeInTheDocument();
  });

  it('renders with custom placeholder', () => {
    render(<SearchBar onSearch={mockOnSearch} placeholder="Custom placeholder" />);
    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument();
  });

  it('handles input changes', async () => {
    render(<SearchBar onSearch={mockOnSearch} />);
    const input = screen.getByRole('textbox');
    
    fireEvent.change(input, { target: { value: 'test' } });
    expect(input).toHaveValue('test');

    // Should trigger search after debounce
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('test');
    });
  });

  it('fetches and displays suggestions', async () => {
    const mockSuggestions = [
      { keyword: 'dogs', score: 0.8, subreddit_count: 100 },
      { keyword: 'puppies', score: 0.7, subreddit_count: 50 }
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSuggestions
    });

    render(<SearchBar onSearch={mockOnSearch} />);
    const input = screen.getByRole('textbox');
    
    fireEvent.change(input, { target: { value: 'dog' } });

    // Wait for suggestions to appear
    await waitFor(() => {
      expect(screen.getByText('+ dogs')).toBeInTheDocument();
      expect(screen.getByText('+ puppies')).toBeInTheDocument();
    });

    // Verify fetch was called correctly
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8001/subreddits/suggest-keywords?query=dog'
    );
  });

  it('handles suggestion selection', async () => {
    const mockSuggestions = [
      { keyword: 'dogs', score: 0.8, subreddit_count: 100 }
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSuggestions
    });

    render(<SearchBar onSearch={mockOnSearch} />);
    const input = screen.getByRole('textbox');
    
    fireEvent.change(input, { target: { value: 'dog' } });

    // Wait for and click suggestion
    await waitFor(() => {
      const suggestion = screen.getByText('+ dogs');
      fireEvent.click(suggestion);
    });

    // Selected keyword should appear as a pill
    expect(screen.getByText('dogs')).toBeInTheDocument();
    
    // Search should be triggered with selected keyword
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('dogs');
    });
  });

  it('handles keyword removal', async () => {
    const mockSuggestions = [
      { keyword: 'dogs', score: 0.8, subreddit_count: 100 }
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSuggestions
    });

    render(<SearchBar onSearch={mockOnSearch} />);
    
    // Add a keyword
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'dog' } });
    await waitFor(() => {
      const suggestion = screen.getByText('+ dogs');
      fireEvent.click(suggestion);
    });

    // Remove the keyword
    const removeButton = screen.getByText('dogs');
    fireEvent.click(removeButton);

    // Keyword should be removed
    expect(screen.queryByText('dogs')).not.toBeInTheDocument();

    // Search should be triggered without the keyword
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('');
    });
  });

  it('handles fetch errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    render(<SearchBar onSearch={mockOnSearch} />);
    const input = screen.getByRole('textbox');
    
    fireEvent.change(input, { target: { value: 'test' } });

    // No suggestions should appear
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /\+/i })).not.toBeInTheDocument();
    });
  });
}); 