import { Button } from '@/components/ui/button';
import { useAudiences } from '@/hooks/useAudiences';
import { Plus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { AudienceDialog } from './AudienceDialog';

interface AddToAudienceButtonProps {
  selectedSubreddits: string[];
}

export function AddToAudienceButton({ selectedSubreddits }: AddToAudienceButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { audiences, refreshAudiences } = useAudiences();

  useEffect(() => {
    if (isOpen) {
      refreshAudiences();
    }
  }, [isOpen, refreshAudiences]);

  const handleSuccess = async () => {
    await refreshAudiences();
    setIsOpen(false);
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        disabled={selectedSubreddits.length === 0}
      >
        <Plus className="h-4 w-4 mr-2" />
        Add to Audience
      </Button>

      <AudienceDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        selectedSubreddits={selectedSubreddits}
        existingAudiences={audiences}
        onSuccess={handleSuccess}
      />
    </>
  );
} 