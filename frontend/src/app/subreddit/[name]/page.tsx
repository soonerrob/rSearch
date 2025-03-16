'use client';

import { subredditApi } from '@/lib/api';
import { Subreddit } from '@/types/subreddit';
import { ArrowLeft, Clock, MessageSquare, TrendingUp, Users } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function SubredditPage() {
  const params = useParams();
  const subredditName = params.name as string;
  
  const [subreddit, setSubreddit] = useState<Subreddit | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSubredditDetails = async () => {
      try {
        const data = await subredditApi.getSubredditDetails(subredditName);
        setSubreddit(data);
      } catch (err) {
        setError('Failed to fetch subreddit details');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubredditDetails();
  }, [subredditName]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error || !subreddit) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Link
          href="/"
          className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to search
        </Link>
        <div className="rounded-lg bg-red-100 p-4 text-red-700">
          {error || 'Subreddit not found'}
        </div>
      </div>
    );
  }

  return (
    <main className="container mx-auto px-4 py-8">
      {/* Back Button */}
      <Link
        href="/"
        className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to search
      </Link>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold">r/{subreddit.display_name}</h1>
        <p className="mt-2 text-gray-600">{subreddit.description}</p>
      </div>

      {/* Stats Grid */}
      <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Subscribers */}
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-500" />
            <h3 className="font-medium text-gray-900">Subscribers</h3>
          </div>
          <p className="mt-2 text-3xl font-bold">
            {subreddit.subscribers?.toLocaleString() ?? 'N/A'}
          </p>
        </div>

        {/* Active Users */}
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-green-500" />
            <h3 className="font-medium text-gray-900">Active Users</h3>
          </div>
          <p className="mt-2 text-3xl font-bold">
            {subreddit.active_users?.toLocaleString() ?? 'N/A'}
          </p>
        </div>

        {/* Posts per Day */}
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-purple-500" />
            <h3 className="font-medium text-gray-900">Posts per Day</h3>
          </div>
          <p className="mt-2 text-3xl font-bold">
            {subreddit.posts_per_day?.toLocaleString() ?? 'N/A'}
          </p>
        </div>

        {/* Comments per Day */}
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-orange-500" />
            <h3 className="font-medium text-gray-900">Comments per Day</h3>
          </div>
          <p className="mt-2 text-3xl font-bold">
            {subreddit.comments_per_day?.toLocaleString() ?? 'N/A'}
          </p>
        </div>
      </div>

      {/* Additional Sections - To be implemented */}
      <div className="space-y-8">
        {/* Growth Trends Section */}
        <section className="rounded-lg border bg-white p-6">
          <h2 className="text-2xl font-bold">Growth Trends</h2>
          <p className="mt-2 text-gray-600">Coming soon: Growth trend visualization</p>
        </section>

        {/* Recent Posts Section */}
        <section className="rounded-lg border bg-white p-6">
          <h2 className="text-2xl font-bold">Recent Posts</h2>
          <p className="mt-2 text-gray-600">Coming soon: List of recent popular posts</p>
        </section>

        {/* Similar Subreddits Section */}
        <section className="rounded-lg border bg-white p-6">
          <h2 className="text-2xl font-bold">Similar Subreddits</h2>
          <p className="mt-2 text-gray-600">Coming soon: Related subreddit recommendations</p>
        </section>
      </div>
    </main>
  );
} 