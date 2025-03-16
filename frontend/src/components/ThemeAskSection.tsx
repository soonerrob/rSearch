import { ErrorMessage } from '@/components/ui/error-message';
import { themeQuestionsService } from '@/services/themeQuestions';
import { Loader2 } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

interface ThemeAskSectionProps {
  themeId: number;
  onQuestionCreated?: () => void;
}

export function ThemeAskSection({ themeId, onQuestionCreated }: ThemeAskSectionProps) {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setError(null);
    setIsLoading(true);
    try {
      await themeQuestionsService.createQuestion({
        theme_id: themeId,
        question: question.trim()
      });
      
      setQuestion('');
      toast.success('Question submitted successfully');
      onQuestionCreated?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit question';
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Ask a Question</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Your Question
          </label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              setError(null);
            }}
            placeholder="What would you like to know about this theme?"
            className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-primary"
            rows={3}
            required
          />
        </div>

        {error && (
          <ErrorMessage message={error} />
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading || !question.trim()}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-accent-primary rounded-md hover:bg-accent-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Question'
            )}
          </button>
        </div>
      </form>
    </div>
  );
} 