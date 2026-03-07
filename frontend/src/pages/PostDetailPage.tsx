/* ── Post detail page — full post, analysis, and comment management ──── */

import { useCallback, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  ClipboardCopy,
  ExternalLink,
  Heart,
  MessageCircle,
  Star,
  XCircle,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { getPost, updateCommentStatus } from '../api';
import { useAsync } from '../hooks';
import type { CommentOut, CommentStatus } from '../types';
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
} from '../components/ui';

export default function PostDetailPage() {
  const { postId } = useParams<{ postId: string }>();
  const { data: post, loading, error, reload } = useAsync(
    () => getPost(postId!),
    [postId],
  );

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size={32} className="text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-6 py-8">
        <ErrorBanner message={error} onRetry={reload} />
      </div>
    );
  }

  if (!post) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {/* Back link */}
      <Link
        to="/posts"
        className="mb-4 inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to posts
      </Link>

      {/* ── Post card ──────────────────────────────────────────────────── */}
      <Card className="mb-6">
        <CardBody>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                {post.author ?? 'Unknown Author'}
              </h1>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-400">
                <Badge variant="info">{post.platform}</Badge>
                {post.post_timestamp && (
                  <span>
                    Posted{' '}
                    {formatDistanceToNow(new Date(post.post_timestamp), {
                      addSuffix: true,
                    })}
                  </span>
                )}
                {post.source_query && (
                  <span className="text-gray-300">
                    via &ldquo;{post.source_query}&rdquo;
                  </span>
                )}
                {post.pipeline_run_id && (
                  <Link
                    to={`/pipeline/runs/${post.pipeline_run_id}`}
                    className="text-blue-500 hover:text-blue-700"
                  >
                    View Pipeline Run
                  </Link>
                )}
              </div>
            </div>
            <a
              href={post.post_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800"
            >
              <ExternalLink className="h-4 w-4" />
              Original
            </a>
          </div>

          {/* Full content */}
          <div className="mt-4 whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
            {post.content}
          </div>

          {/* Engagement */}
          <div className="mt-4 flex items-center gap-5 border-t border-gray-100 pt-3 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Heart className="h-4 w-4" />
              {post.likes} likes
            </span>
            <span className="flex items-center gap-1">
              <MessageCircle className="h-4 w-4" />
              {post.comments_count} comments
            </span>
          </div>
        </CardBody>
      </Card>

      {/* ── Analysis ───────────────────────────────────────────────────── */}
      {post.analysis && (
        <Card className="mb-6">
          <CardHeader>
            <h2 className="text-sm font-semibold text-gray-700">
              AI Analysis
            </h2>
          </CardHeader>
          <CardBody>
            <div className="grid gap-4 sm:grid-cols-2">
              <ScoreBar
                value={post.analysis.relevance_score}
                label="Relevance Score"
              />
              <ScoreBar
                value={post.analysis.opportunity_score}
                label="Opportunity Score"
              />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {post.analysis.intent && (
                <Badge>Intent: {post.analysis.intent}</Badge>
              )}
              {post.analysis.emotion && (
                <Badge>Emotion: {post.analysis.emotion}</Badge>
              )}
            </div>
            {post.analysis.reasoning && (
              <p className="mt-3 text-sm text-gray-600 leading-relaxed">
                {post.analysis.reasoning}
              </p>
            )}
          </CardBody>
        </Card>
      )}

      {/* ── Comments ───────────────────────────────────────────────────── */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          Comment Candidates ({post.comment_candidates.length})
        </h2>

        {post.comment_candidates.length === 0 ? (
          <EmptyState
            icon={<MessageCircle className="h-10 w-10" />}
            title="No comments generated yet"
            description="Run the pipeline to generate comment candidates."
          />
        ) : (
          <div className="space-y-4">
            {post.comment_candidates
              .sort((a, b) => b.score - a.score)
              .map((comment) => (
                <CommentCard
                  key={comment.id}
                  comment={comment}
                  onStatusChange={reload}
                />
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Comment card with actions ────────────────────────────────────────── */

function CommentCard({
  comment,
  onStatusChange,
}: {
  comment: CommentOut;
  onStatusChange: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleStatus = useCallback(
    async (status: CommentStatus) => {
      setBusy(true);
      try {
        await updateCommentStatus(comment.id, status);
        onStatusChange();
      } catch {
        // toast would be nice — for now just reload
        onStatusChange();
      } finally {
        setBusy(false);
      }
    },
    [comment.id, onStatusChange],
  );

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(comment.comment_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [comment.comment_text]);

  return (
    <Card
      className={
        comment.status === 'selected'
          ? 'ring-2 ring-green-500/30'
          : comment.status === 'rejected'
            ? 'opacity-60'
            : ''
      }
    >
      <CardBody>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <Badge variant={comment.status}>{comment.status}</Badge>
            <span className="text-xs text-gray-400">v{comment.version}</span>
            {comment.score > 0 && (
              <span className="flex items-center gap-1 text-xs text-amber-600">
                <Star className="h-3.5 w-3.5 fill-current" />
                {(comment.score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <span className="text-xs text-gray-400">
            {format(new Date(comment.created_at), 'MMM d, yyyy HH:mm')}
          </span>
        </div>

        {/* Comment text */}
        <div className="mt-3 rounded-lg bg-gray-50 p-4 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
          {comment.comment_text}
        </div>

        {/* Critique (if any) */}
        {comment.critique && (
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700">
              View Critique
            </summary>
            <pre className="mt-1 rounded bg-gray-50 p-3 text-xs text-gray-600 whitespace-pre-wrap">
              {comment.critique}
            </pre>
          </details>
        )}

        {/* Actions */}
        <div className="mt-3 flex items-center gap-2 border-t border-gray-100 pt-3">
          {comment.status !== 'selected' && (
            <Button
              variant="primary"
              size="sm"
              loading={busy}
              onClick={() => handleStatus('selected')}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Select
            </Button>
          )}
          {comment.status !== 'rejected' && (
            <Button
              variant="danger"
              size="sm"
              loading={busy}
              onClick={() => handleStatus('rejected')}
            >
              <XCircle className="h-3.5 w-3.5" />
              Reject
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
          >
            <ClipboardCopy className="h-3.5 w-3.5" />
            {copied ? 'Copied!' : 'Copy'}
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}
