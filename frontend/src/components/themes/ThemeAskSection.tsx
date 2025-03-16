import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';
import { createThemeQuestion, deleteThemeQuestion, recalculateThemeQuestion } from '@/services/themeQuestions';
import { Theme } from '@/types/theme';
import { ThemeQuestion } from '@/types/themes';
import { Clock, MessageCircle, RefreshCw, X } from 'lucide-react';
import { useState } from 'react';

interface ThemeAskSectionProps {
  theme: Theme;
  questions: ThemeQuestion[];
  onQuestionsChange: () => void;
}

export default function ThemeAskSection({
  theme,
  questions,
  onQuestionsChange,
}: ThemeAskSectionProps) {
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [processingQuestionId, setProcessingQuestionId] = useState<number | null>(null);
  const [newQuestionId, setNewQuestionId] = useState<number | null>(null);
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null);
  const { toast } = useToast();

  const handleSubmitQuestion = async () => {
    if (!currentQuestion.trim()) return;
    
    setIsSubmitting(true);
    toast({
      title: "Question submitted",
      description: "Your question is being processed. This may take a few moments.",
    });
    
    try {
      const response = await createThemeQuestion({
        theme_id: theme.id,
        question: currentQuestion.trim()
      });
      setNewQuestionId(response.id);
      setExpandedQuestionId(response.id.toString());
      onQuestionsChange();
    } catch {
      toast({
        title: "Error",
        description: "Failed to submit question. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
      setCurrentQuestion('');
    }
  };

  const handleRecalculate = async (question: ThemeQuestion) => {
    setProcessingQuestionId(question.id);
    try {
      await recalculateThemeQuestion(question.id);
      onQuestionsChange();
      toast({
        title: "Answer recalculated",
        description: "The answer has been updated based on the latest data.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to recalculate answer. Please try again.",
        variant: "destructive",
      });
    } finally {
      setProcessingQuestionId(null);
    }
  };

  const handleDeleteQuestion = async (questionId: number) => {
    try {
      await deleteThemeQuestion(questionId);
      onQuestionsChange();
      toast({
        title: "Question deleted",
        description: "The question has been removed.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to delete question. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <div className="relative flex-1">
            {isSubmitting ? (
              <RefreshCw className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white animate-spin" />
            ) : (
              <MessageCircle className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white" />
            )}
            <Input
              placeholder={`Ask a question about ${theme.category} in this audience...`}
              value={currentQuestion}
              onChange={(e) => setCurrentQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmitQuestion()}
              disabled={isSubmitting}
              className="w-full rounded-md bg-gray-800 h-12 pl-9 pr-4 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary border-0"
            />
          </div>
          <Button 
            onClick={handleSubmitQuestion}
            disabled={!currentQuestion.trim() || isSubmitting}
            className="h-12"
          >
            Ask
          </Button>
        </div>

        <div className="flex justify-center">
          <div className="w-full max-w-[740px]">
            <div className="h-px bg-gray-500" />
            <div className="text-sm text-gray-500 mt-4 mb-2">Recent Questions</div>
            <Accordion 
              type="single" 
              collapsible 
              className="w-full space-y-2"
              value={expandedQuestionId}
              onValueChange={setExpandedQuestionId}
            >
              {questions.map((q) => (
                <AccordionItem 
                  key={q.id} 
                  value={q.id.toString()}
                  className="border-none [&[data-state=open]]:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-start justify-between py-1 px-4 rounded-lg bg-transparent hover:bg-gray-800 transition-colors border-2 border-gray-800">
                    <AccordionTrigger className="hover:no-underline flex-1 flex items-start pt-2">
                      <div className="flex-shrink-0">
                        <Clock className="h-4 w-4 text-gray-500" />
                      </div>
                      <span className="font-medium text-left flex-1 -ml-1">{q.question}</span>
                    </AccordionTrigger>
                    <div className="flex items-center gap-1 ml-2 pt-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRecalculate(q);
                        }}
                        disabled={processingQuestionId === q.id}
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${processingQuestionId === q.id ? 'animate-spin' : ''}`} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteQuestion(q.id);
                        }}
                        disabled={processingQuestionId === q.id}
                      >
                        <X className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                  <AccordionContent className="px-4 pb-4">
                    {!q.answer ? (
                      <p className="text-sm text-slate-500">Processing your question...</p>
                    ) : (
                      <>
                        <p className="text-sm whitespace-pre-wrap">{q.answer}</p>
                        <p className="text-xs text-slate-400 mt-2">
                          Last updated: {new Date(q.updated_at).toLocaleString()}
                        </p>
                      </>
                    )}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </div>
      </div>
    </div>
  );
} 