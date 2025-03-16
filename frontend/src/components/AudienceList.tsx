import { Edit, Hourglass, Plus, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { useAudiences } from '../hooks/useAudiences';
import { AudienceDialog } from './AudienceDialog';
import { EditAudienceDialog } from './EditAudienceDialog';

interface AudienceListProps {
  onSelectAudience?: (audienceId: number) => void;
  selectedAudienceId?: number;
  mode?: 'select' | 'manage';
}

export function AudienceList({ 
  onSelectAudience,
  selectedAudienceId,
  mode = 'manage'
}: AudienceListProps) {
  const { audiences, isLoading, error, deleteAudience, refreshAudiences } = useAudiences();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingAudience, setEditingAudience] = useState<typeof audiences[0] | null>(null);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this audience?')) return;
    try {
      await deleteAudience(id);
    } catch (err) {
      console.error('Failed to delete audience:', err);
    }
  };

  const handleEdit = (audience: typeof audiences[0]) => {
    setEditingAudience(audience);
    setIsEditDialogOpen(true);
  };

  if (isLoading) {
    return (
      <div className="p-4 text-center text-muted">
        Loading audiences...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500">
        {error}
      </div>
    );
  }

  if (audiences.length === 0) {
    return (
      <div className="p-4 text-center">
        <p className="text-muted">No audiences created yet</p>
        <p className="text-sm text-muted mt-2">
          Go to the search page to create your first audience by selecting subreddits.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {mode === 'manage' && (
        <div className="flex justify-end">
          <button
            onClick={() => setIsCreateDialogOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-accent-primary text-white rounded-md hover:bg-accent-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Create Audience
          </button>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {audiences.map((audience) => (
          <div
            key={audience.id}
            className={`
              p-4 rounded-lg border border-card-border bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors
              ${mode === 'select' ? 'cursor-pointer hover:border-accent-primary/90' : ''}
              ${selectedAudienceId === audience.id ? 'border-accent-primary ring-1 ring-accent-primary' : ''}
            `}
            onClick={mode === 'select' ? () => onSelectAudience?.(audience.id) : undefined}
          >
            <div className="flex items-start justify-between">
              <div>
                <Link 
                  href={`/audiences/${audience.id}`}
                  className="hover:text-accent-primary"
                >
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-foreground">
                      {audience.name}
                    </h3>
                    {audience.is_collecting && (
                      <div className="flex items-center gap-1">
                        <Hourglass className="h-3 w-3 text-accent-primary animate-spin" />
                        <span className="text-xs text-accent-primary animate-pulse">
                          {audience.collection_progress ? 
                            `${Math.round(audience.collection_progress)}%` :
                            'Collecting data...'
                          }
                        </span>
                      </div>
                    )}
                  </div>
                </Link>
                {audience.description && (
                  <p className="mt-1 text-sm text-muted">
                    {audience.description}
                  </p>
                )}
                {audience.is_collecting && audience.collection_progress > 0 && (
                  <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                    <div 
                      className="bg-accent-primary h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${audience.collection_progress}%` }}
                    />
                  </div>
                )}
              </div>
              {mode === 'manage' && (
                <div className="flex gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(audience);
                    }}
                    className="p-1 text-muted hover:text-accent-primary"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(audience.id);
                    }}
                    className="p-1 text-muted hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
            <div className="mt-3">
              <div className="flex flex-wrap gap-4 text-sm text-muted mb-2">
                <div>
                  {audience.subreddit_names.length} subreddit{audience.subreddit_names.length !== 1 ? 's' : ''}
                </div>
                <div>
                  {audience.post_count.toLocaleString()} post{audience.post_count !== 1 ? 's' : ''}
                </div>
                <div>
                  Created {new Date(audience.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {audience.subreddit_names.slice(0, 3).map((subreddit) => (
                  <span
                    key={subreddit}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-background text-foreground"
                  >
                    r/{subreddit}
                  </span>
                ))}
                {audience.subreddit_names.length > 3 && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-background text-foreground">
                    +{audience.subreddit_names.length - 3} more
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <AudienceDialog
        isOpen={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        selectedSubreddits={[]}
        onSuccess={refreshAudiences}
      />

      {editingAudience && (
        <EditAudienceDialog
          isOpen={isEditDialogOpen}
          onClose={() => {
            setIsEditDialogOpen(false);
            setEditingAudience(null);
          }}
          audience={editingAudience}
          onSuccess={refreshAudiences}
        />
      )}
    </div>
  );
} 