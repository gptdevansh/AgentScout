/* ── Pipeline Runs list page ──────────────────────────────────────────── */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  History,
  Loader2,
  RefreshCw,
  Rocket,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { listPipelineRuns } from '../api';
import { useAsync } from '../hooks';
import type { PipelineRunSummaryOut } from '../types';
import {
  Badge,
  Button,
  Card,
  CardBody,
  EmptyState,
  ErrorBanner,
  Spinner,
} from '../components/ui';

export default function PipelineRunsPage() {
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  const { data, loading, error, reload } = useAsync(
    () => listPipelineRuns({ limit, offset }),
    [limit, offset],
  );

  return (
    <div className="px-6 py-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-2xl font-bold text-gray-900">
            <History className="h-7 w-7 text-blue-600" />
            Pipeline Runs
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {data
              ? `${data.total} run${data.total !== 1 ? 's' : ''} recorded`
              : 'Loading…'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" size="sm" onClick={reload}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Link to="/pipeline">
            <Button size="sm">
              <Rocket className="h-4 w-4" />
              New Run
            </Button>
          </Link>
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
          icon={<History className="h-12 w-12" />}
          title="No pipeline runs yet"
          description="Run the pipeline to start discovering posts."
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
            {data.items.map((run) => (
              <RunCard key={run.id} run={run} />
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

/* ── Single run card ──────────────────────────────────────────────────── */

function RunCard({ run }: { run: PipelineRunSummaryOut }) {
  const hasErrors = run.errors.length > 0;

  const statusConfig: Record<
    string,
    { icon: typeof CheckCircle2; variant: 'success' | 'warning' | 'info'; label: string }
  > = {
    completed: { icon: CheckCircle2, variant: 'success', label: 'Completed' },
    failed: { icon: AlertTriangle, variant: 'warning', label: 'Failed' },
    running: { icon: Loader2, variant: 'info', label: 'Running' },
  };

  const cfg = statusConfig[run.status] ?? statusConfig.running;
  const StatusIcon = cfg.icon;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardBody>
        <Link
          to={`/pipeline/runs/${run.id}`}
          className="block hover:no-underline"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <StatusIcon
                  className={`h-5 w-5 ${
                    run.status === 'completed'
                      ? 'text-green-500'
                      : run.status === 'failed'
                        ? 'text-red-500'
                        : 'text-blue-500 animate-spin'
                  }`}
                />
                <Badge variant={cfg.variant}>{cfg.label}</Badge>
                <Badge variant="info">{run.platform}</Badge>
                {hasErrors && (
                  <Badge variant="warning">
                    {run.errors.length} error{run.errors.length !== 1 ? 's' : ''}
                  </Badge>
                )}
              </div>
              <p className="text-sm font-medium text-gray-900 line-clamp-2">
                {run.problem_description}
              </p>
              {run.product_description && (
                <p className="mt-1 text-xs text-gray-500 line-clamp-1">
                  Product: {run.product_description}
                </p>
              )}
            </div>

            <div className="shrink-0 text-right space-y-1">
              <div className="flex items-center gap-1 text-xs text-gray-400">
                <Clock className="h-3.5 w-3.5" />
                {formatDistanceToNow(new Date(run.created_at), {
                  addSuffix: true,
                })}
              </div>
              <div className="flex gap-4 text-xs text-gray-500">
                <span>
                  <strong>{run.posts_found}</strong> found
                </span>
                <span>
                  <strong>{run.posts_relevant}</strong> relevant
                </span>
                <span>
                  <strong>{run.comments_generated}</strong> comments
                </span>
              </div>
            </div>
          </div>
        </Link>
      </CardBody>
    </Card>
  );
}
