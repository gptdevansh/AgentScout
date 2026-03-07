/* ── Pipeline Run Detail page ──────────────────────────────────────────── */

import { Link, useParams } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  Heart,
  Loader2,
  MessageCircle,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getPipelineRun } from '../api';
import { useAsync } from '../hooks';
import type { PipelineRunPostOut } from '../types';
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  ErrorBanner,
  ScoreBar,
  Spinner,
} from '../components/ui';

export default function PipelineRunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const { data: run, loading, error } = useAsync(
    () => getPipelineRun(runId!),
    [runId],
  );

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner size={32} className="text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-6 py-8">
        <ErrorBanner message={error} />
      </div>
    );
  }

  if (!run) return null;

  const hasErrors = run.errors.length > 0;

  const statusConfig: Record<
    string,
    { icon: typeof CheckCircle2; color: string; label: string }
  > = {
    completed: { icon: CheckCircle2, color: 'text-green-500', label: 'Completed' },
    failed: { icon: AlertTriangle, color: 'text-red-500', label: 'Failed' },
    running: { icon: Loader2, color: 'text-blue-500 animate-spin', label: 'Running' },
  };
  const cfg = statusConfig[run.status] ?? statusConfig.running;
  const StatusIcon = cfg.icon;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {/* Back link */}
      <Link
        to="/pipeline/runs"
        className="mb-6 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" />
        All Runs
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <StatusIcon className={`h-6 w-6 ${cfg.color}`} />
          <h1 className="text-2xl font-bold text-gray-900">Pipeline Run</h1>
          <Badge variant={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'warning' : 'info'}>
            {cfg.label}
          </Badge>
          <Badge variant="info">{run.platform}</Badge>
        </div>
        <p className="text-sm text-gray-600">{run.problem_description}</p>
        {run.product_description && (
          <p className="mt-1 text-xs text-gray-400">
            Product: {run.product_description}
          </p>
        )}
        <p className="mt-1 text-xs text-gray-400">
          {formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}
          {' · '}
          Run ID: {run.id}
        </p>
      </div>

      {/* Metrics */}
      <Card className="mb-6">
        <CardBody>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            <MiniStat label="Posts Found" value={run.posts_found} />
            <MiniStat label="Analysed" value={run.posts_analysed} />
            <MiniStat label="Relevant" value={run.posts_relevant} />
            <MiniStat label="Debates" value={run.debates_run} />
            <MiniStat label="Comments" value={run.comments_generated} />
          </div>
        </CardBody>
      </Card>

      {/* Queries */}
      {run.queries.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <h3 className="text-sm font-semibold text-gray-700">
              Generated Queries ({run.queries.length})
            </h3>
          </CardHeader>
          <CardBody>
            <div className="flex flex-wrap gap-2">
              {run.queries.map((q, i) => (
                <Badge key={i} variant="info">
                  {q}
                </Badge>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Errors */}
      {hasErrors && (
        <Card className="mb-6">
          <CardHeader>
            <h3 className="flex items-center gap-2 text-sm font-semibold text-red-600">
              <AlertTriangle className="h-4 w-4" />
              Errors ({run.errors.length})
            </h3>
          </CardHeader>
          <CardBody className="space-y-2">
            {run.errors.map((err, i) => (
              <p key={i} className="text-sm text-red-700">
                {err}
              </p>
            ))}
          </CardBody>
        </Card>
      )}

      {/* Posts discovered in this run */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">
            Posts Discovered ({run.posts.length})
          </h2>
        </CardHeader>
        <CardBody>
          {run.posts.length === 0 ? (
            <EmptyState
              icon={<MessageCircle className="h-10 w-10" />}
              title="No posts in this run"
              description="This run did not discover any posts."
            />
          ) : (
            <div className="divide-y divide-gray-100">
              {run.posts.map((post) => (
                <RunPostRow key={post.id} post={post} />
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

/* ── Helper components ────────────────────────────────────────────────── */

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

function RunPostRow({ post }: { post: PipelineRunPostOut }) {
  return (
    <div className="flex items-center gap-4 py-3 -mx-6 px-6 hover:bg-gray-50 transition-colors">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Link
            to={`/posts/${post.id}`}
            className="text-sm font-medium text-gray-900 hover:text-blue-600 truncate"
          >
            {post.author ?? 'Unknown Author'}
          </Link>
          <a
            href={post.post_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-blue-600 shrink-0"
            title="Open original post"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
        <p className="text-xs text-gray-500 truncate mt-0.5">{post.content.slice(0, 120)}</p>
        <div className="mt-1 flex items-center gap-3 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <Heart className="h-3 w-3" />
            {post.likes}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle className="h-3 w-3" />
            {post.comments_count}
          </span>
          {post.source_query && (
            <span className="truncate">Query: {post.source_query}</span>
          )}
        </div>
      </div>
      {post.analysis && (
        <div className="w-28 shrink-0">
          <ScoreBar value={post.analysis.relevance_score} label="Relevance" />
        </div>
      )}
    </div>
  );
}
