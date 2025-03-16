'use client';

import { Users } from 'lucide-react';
import { AudienceList } from '../../components/AudienceList';

export default function AudiencesPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Users className="h-8 w-8 text-accent-primary" />
          <h1 className="text-2xl font-bold text-foreground">Audience Management</h1>
        </div>
        <p className="text-muted">
          Create and manage audiences to group subreddits together. Audiences help you organize and track related communities,
          making it easier to monitor trends and engagement across similar subreddits.
        </p>
      </div>

      <div className="bg-card-bg border border-card-border rounded-lg">
        <div className="border-b border-card-border p-4">
          <h2 className="text-lg font-semibold text-foreground">Your Audiences</h2>
          <p className="text-sm text-muted mt-1">
            View, create, and manage your custom subreddit audiences.
          </p>
        </div>
        
        <div className="p-4">
          <AudienceList />
        </div>
      </div>

      <div className="mt-8 text-sm text-muted">
        <h3 className="font-medium text-foreground mb-2">Tips:</h3>
        <ul className="list-disc list-inside space-y-1">
          <li>Create audiences based on topics, themes, or monitoring goals</li>
          <li>Add subreddits to multiple audiences if they fit different categories</li>
          <li>Use the edit button to update audience names and descriptions</li>
          <li>Delete audiences that are no longer needed</li>
        </ul>
      </div>
    </div>
  );
} 