/* ── Dashboard page — overview stats + recent activity ────────────────── */

import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  Inbox,
  MessageSquareText,
  Newspaper,
  Rocket,
  TrendingUp,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getHealth, listPosts } from '../api';
import { useAsync } from '../hooks';
import type { PostDetailOut } from '../types';
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  ErrorBanner,
  ScoreBar,
  Spinner,
  StatCard,
} from '../components/ui';

export default function DashboardPage() {
  const { data: health, loading: healthLoading } = useAsync(
    () => getHealth(),
    [],
  );
  const {
    data: postsData,
    loading: postsLoading,
    error,
    reload,
  } = useAsync(() => listPosts({ limit: 200 }), []);

  const loading = healthLoading || postsLoading;

  const posts = postsData?.items ?? [];
  const totalPosts = posts.length;
  const analysedPosts = posts.filter((p) => p.analysis !== null).length;
  const totalComments = posts.reduce(
    (sum, p) => sum + p.comment_candidates.length,
    0,
  );
  const selectedComments = posts.reduce(
    (sum, p) =>
      sum + p.comment_candidates.filter((c) => c.status === 'selected').length,
    0,
  );
  const avgRelevance =
    analysedPosts > 0
      ? posts
          .filter((p) => p.analysis)
          .reduce((sum, p) => sum + (p.analysis?.relevance_score ?? 0), 0) /
        analysedPosts
      : 0;

  // Top 5 most relevant posts
  const topPosts = [...posts]
    .filter((p) => p.analysis)
    .sort(
      (a, b) =>
        (b.analysis?.relevance_score ?? 0) -
        (a.analysis?.relevance_score ?? 0),
    )
    .slice(0, 5);

  return (
    <div className="px-6 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            {health
              ? `${health.app} v${health.version} — Status: ${health.status}`
              : 'Connecting…'}
          </p>
        </div>
        <Link to="/pipeline">
          <Button>
            <Rocket className="h-4 w-4" />
            New Pipeline Run
          </Button>
        </Link>
      </div>

      {error && <ErrorBanner message={error} onRetry={reload} />}

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner size={32} className="text-blue-600" />
        </div>
      ) : (
        <>
          {/* Stat cards */}
          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Total Posts"
              value={totalPosts}
              icon={<Newspaper className="h-6 w-6" />}
            />
            <StatCard
              label="Comments Generated"
              value={totalComments}
              icon={<MessageSquareText className="h-6 w-6" />}
            />
            <StatCard
              label="Comments Selected"
              value={selectedComments}
              icon={<CheckCircle2 className="h-6 w-6" />}
            />
            <StatCard
              label="Avg Relevance"
              value={`${(avgRelevance * 100).toFixed(0)}%`}
              icon={<TrendingUp className="h-6 w-6" />}
            />
          </div>

          {/* Top posts */}
          <Card>
            <CardHeader className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-700">
                Top Relevant Posts
              </h2>
              <Link
                to="/posts"
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                View all →
              </Link>
            </CardHeader>
            <CardBody>
              {topPosts.length === 0 ? (
                <EmptyState
                  icon={<Inbox className="h-10 w-10" />}
                  title="No posts yet"
                  description="Run the pipeline to discover and analyse posts."
                  action={
                    <Link to="/pipeline">
                      <Button size="sm">Run Pipeline</Button>
                    </Link>
                  }
                />
              ) : (
                <div className="divide-y divide-gray-100">
                  {topPosts.map((post) => (
                    <TopPostRow key={post.id} post={post} />
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}

/* ── Row component for top posts ──────────────────────────────────────── */

function TopPostRow({ post }: { post: PostDetailOut }) {
  const selectedCount = post.comment_candidates.filter(
    (c) => c.status === 'selected',
  ).length;

  return (
    <Link
      to={`/posts/${post.id}`}
      className="flex items-center gap-4 py-3 hover:bg-gray-50 -mx-6 px-6 transition-colors"
    >
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {post.author ?? 'Unknown'}
        </p>
        <p className="text-xs text-gray-500 truncate">{post.content.slice(0, 100)}</p>
      </div>
      <div className="w-28 shrink-0">
        <ScoreBar value={post.analysis?.relevance_score ?? 0} />
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {post.analysis?.intent && (
          <Badge variant="default">{post.analysis.intent}</Badge>
        )}
        {selectedCount > 0 && (
          <Badge variant="success">{selectedCount} selected</Badge>
        )}
        {post.created_at && (
          <span className="text-xs text-gray-400">
            {formatDistanceToNow(new Date(post.created_at), {
              addSuffix: true,
            })}
          </span>
        )}
      </div>
    </Link>
  );
}
