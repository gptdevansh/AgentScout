/* ── Posts list page ──────────────────────────────────────────────────── */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ExternalLink,
  Filter,
  Heart,
  MessageCircle,
  Newspaper,
  RefreshCw,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { listPosts } from '../api';
import { useAsync } from '../hooks';
import type { PostDetailOut } from '../types';
import {
  Badge,
  Button,
  Card,
  CardBody,
  EmptyState,
  ErrorBanner,
  ScoreBar,
  Spinner,
} from '../components/ui';

export default function PostsPage() {
  const [minRelevance, setMinRelevance] = useState<number | undefined>(undefined);
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  const { data, loading, error, reload } = useAsync(
    () => listPosts({ min_relevance: minRelevance, limit, offset }),
    [minRelevance, limit, offset],
  );

  return (
    <div className="px-6 py-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-2xl font-bold text-gray-900">
            <Newspaper className="h-7 w-7 text-blue-600" />
            Discovered Posts
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {data ? `${data.total} post${data.total !== 1 ? 's' : ''} found` : 'Loading…'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Relevance filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              value={minRelevance ?? ''}
              onChange={(e) => {
                setMinRelevance(e.target.value ? Number(e.target.value) : undefined);
                setOffset(0);
              }}
            >
              <option value="">All relevance</option>
              <option value="0.3">≥ 30%</option>
              <option value="0.5">≥ 50%</option>
              <option value="0.7">≥ 70%</option>
              <option value="0.9">≥ 90%</option>
            </select>
          </div>
          <Button variant="secondary" size="sm" onClick={reload}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Content */}
      {loading && (
        <div className="flex justify-center py-16">
          <Spinner size={32} className="text-blue-600" />
        </div>
      )}

      {error && <ErrorBanner message={error} onRetry={reload} />}

      {!loading && data && data.items.length === 0 && (
        <EmptyState
          icon={<Newspaper className="h-12 w-12" />}
          title="No posts found"
          description="Run the pipeline to discover posts, or relax the relevance filter."
          action={
            <Link to="/pipeline">
              <Button>Run Pipeline</Button>
            </Link>
          }
        />
      )}

      {!loading && data && data.items.length > 0 && (
        <>
          <div className="space-y-4">
            {data.items.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>

          {/* Pagination */}
          {data.total > limit && (
            <div className="mt-6 flex items-center justify-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - limit))}
              >
                Previous
              </Button>
              <span className="text-sm text-gray-500">
                Page {Math.floor(offset / limit) + 1} of{' '}
                {Math.ceil(data.total / limit)}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={offset + limit >= data.total}
                onClick={() => setOffset(offset + limit)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ── Single post card ─────────────────────────────────────────────────── */

function PostCard({ post }: { post: PostDetailOut }) {
  const selectedCount = post.comment_candidates.filter(
    (c) => c.status === 'selected',
  ).length;
  const totalComments = post.comment_candidates.length;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardBody>
        <div className="flex gap-4">
          {/* Main content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-3">
              <div>
                <Link
                  to={`/posts/${post.id}`}
                  className="text-base font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                >
                  {post.author ?? 'Unknown Author'}
                </Link>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-400">
                  <Badge variant="info">{post.platform}</Badge>
                  {post.created_at && (
                    <span>
                      {formatDistanceToNow(new Date(post.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  )}
                </div>
              </div>
              <a
                href={post.post_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-blue-600 transition-colors shrink-0"
                title="Open original post"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>

            {/* Content preview */}
            <p className="mt-2 text-sm text-gray-600 line-clamp-3">
              {post.content}
            </p>

            {/* Bottom row */}
            <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Heart className="h-3.5 w-3.5" />
                {post.likes}
              </span>
              <span className="flex items-center gap-1">
                <MessageCircle className="h-3.5 w-3.5" />
                {post.comments_count}
              </span>
              {totalComments > 0 && (
                <span>
                  {selectedCount}/{totalComments} comments selected
                </span>
              )}
              {post.pipeline_run_id && (
                <Link
                  to={`/pipeline/runs/${post.pipeline_run_id}`}
                  className="text-blue-500 hover:text-blue-700"
                  onClick={(e) => e.stopPropagation()}
                >
                  View Run
                </Link>
              )}
            </div>
          </div>

          {/* Score sidebar */}
          {post.analysis && (
            <div className="w-36 shrink-0 space-y-2">
              <ScoreBar
                value={post.analysis.relevance_score}
                label="Relevance"
              />
              <ScoreBar
                value={post.analysis.opportunity_score}
                label="Opportunity"
              />
              {post.analysis.intent && (
                <div className="text-xs text-gray-500">
                  Intent: <Badge variant="default">{post.analysis.intent}</Badge>
                </div>
              )}
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
