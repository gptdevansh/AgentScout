/* ── Pipeline page — kick off and monitor a run ──────────────────────── */

import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  MessageSquare,
  Rocket,
  Search,
  ThumbsUp,
} from 'lucide-react';
import { getPipelineRun, runPipeline } from '../api';
import type { PipelineRequest, PipelineRunOut } from '../types';
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  ErrorBanner,
} from '../components/ui';

const DEFAULT_VALUES: PipelineRequest = {
  problem_description: '',
  product_description: '',
  num_queries: 3,
  max_posts_per_query: 3,
  min_relevance: 0.1,
  platform: 'linkedin',
};

const POLL_INTERVAL_MS = 4000;

export default function PipelinePage() {
  const [form, setForm] = useState<PipelineRequest>(DEFAULT_VALUES);
  const [submitting, setSubmitting] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [runData, setRunData] = useState<PipelineRunOut | null>(null);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const running = submitting || polling;
  const canSubmit = !running && form.problem_description.trim().length >= 10;

  // ── Polling ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!runId || !polling) return;

    const tick = async () => {
      try {
        const data = await getPipelineRun(runId);
        setRunData(data);
        if (data.status === 'completed' || data.status === 'failed') {
          setPolling(false);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setPolling(false);
      }
    };

    tick(); // fetch immediately
    pollRef.current = setInterval(tick, POLL_INTERVAL_MS);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [runId, polling]);

  // ── Submit ───────────────────────────────────────────────────────────
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setRunData(null);
    setRunId(null);

    try {
      const { run_id } = await runPipeline({
        ...form,
        product_description: form.product_description || null,
      });
      setRunId(run_id);
      setPolling(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  function handleChange(key: keyof PipelineRequest, value: string | number) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="flex items-center gap-3 text-2xl font-bold text-gray-900">
          <Rocket className="h-7 w-7 text-blue-600" />
          Run Pipeline
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Describe a problem to discover LinkedIn posts and generate smart comments.
        </p>
      </div>

      {/* Form */}
      <Card className="mb-8">
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Problem description */}
            <div>
              <label
                htmlFor="problem"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Problem Description *
              </label>
              <textarea
                id="problem"
                rows={4}
                required
                minLength={10}
                maxLength={5000}
                placeholder="e.g. People struggling with slow CI/CD pipelines in large monorepos"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm
                           placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500
                           disabled:bg-gray-50 disabled:text-gray-500"
                value={form.problem_description}
                onChange={(e) => handleChange('problem_description', e.target.value)}
                disabled={running}
              />
            </div>

            {/* Product description */}
            <div>
              <label
                htmlFor="product"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Product Description{' '}
                <span className="text-gray-400">(optional)</span>
              </label>
              <textarea
                id="product"
                rows={2}
                maxLength={3000}
                placeholder="e.g. Our tool parallelizes test suites and caches build artifacts"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm
                           placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500
                           disabled:bg-gray-50 disabled:text-gray-500"
                value={form.product_description ?? ''}
                onChange={(e) => handleChange('product_description', e.target.value)}
                disabled={running}
              />
            </div>

            {/* Advanced settings */}
            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-900">
                Advanced Settings
              </summary>
              <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
                <NumberInput
                  label="Queries"
                  value={form.num_queries ?? 3}
                  min={1}
                  max={100}
                  disabled={running}
                  onChange={(v) => handleChange('num_queries', v)}
                />
                <NumberInput
                  label="Posts / Query"
                  value={form.max_posts_per_query ?? 3}
                  min={1}
                  max={50}
                  disabled={running}
                  onChange={(v) => handleChange('max_posts_per_query', v)}
                />
                <NumberInput
                  label="Min Relevance"
                  value={form.min_relevance ?? 0.1}
                  min={0}
                  max={1}
                  step={0.05}
                  disabled={running}
                  onChange={(v) => handleChange('min_relevance', v)}
                />
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Platform
                  </label>
                  <input
                    type="text"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                               focus:border-blue-500 focus:ring-1 focus:ring-blue-500
                               disabled:bg-gray-50"
                    value={form.platform ?? 'linkedin'}
                    onChange={(e) => handleChange('platform', e.target.value)}
                    disabled={running}
                  />
                </div>
              </div>
            </details>

            {/* Submit */}
            <div className="flex items-center gap-3 pt-2">
              <Button type="submit" disabled={!canSubmit} loading={submitting}>
                <Search className="h-4 w-4" />
                {running ? 'Running Pipeline…' : 'Start Pipeline'}
              </Button>
              {running && (
                <span className="text-sm text-gray-500">
                  This may take a few minutes…
                </span>
              )}
            </div>
          </form>
        </CardBody>
      </Card>

      {/* Error */}
      {error && <ErrorBanner message={error} />}

      {/* Progress while polling */}
      {polling && runData && (
        <PipelineProgress data={runData} />
      )}

      {/* Results once complete */}
      {runData && (runData.status === 'completed' || runData.status === 'failed') && (
        <PipelineResults data={runData} />
      )}
    </div>
  );
}

/* ── Live progress card ───────────────────────────────────────────────── */

function PipelineProgress({ data }: { data: PipelineRunOut }) {
  const steps = [
    { key: 'queries', label: 'Generating queries', done: (data.queries?.length ?? 0) > 0 },
    { key: 'scraping', label: 'Scraping posts', done: data.posts_found > 0 },
    { key: 'analysis', label: 'Analysing posts', done: data.posts_analysed > 0 },
    { key: 'debate', label: 'Generating comments', done: data.comments_generated > 0 },
  ];
  const nextIdx = steps.findIndex((s) => !s.done);

  return (
    <Card className="mb-6">
      <CardHeader>
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
          <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
          Pipeline running…
        </h2>
        <p className="text-xs text-gray-400 mt-1">Run ID: {data.id}</p>
      </CardHeader>
      <CardBody>
        <ol className="space-y-3">
          {steps.map((step, i) => {
            const isActive = i === nextIdx;
            return (
              <li key={step.key} className="flex items-center gap-3">
                {step.done ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
                ) : isActive ? (
                  <Loader2 className="h-5 w-5 animate-spin text-blue-400 shrink-0" />
                ) : (
                  <div className="h-5 w-5 rounded-full border-2 border-gray-200 shrink-0" />
                )}
                <span
                  className={`text-sm ${
                    step.done
                      ? 'text-gray-500 line-through'
                      : isActive
                      ? 'font-semibold text-gray-900'
                      : 'text-gray-400'
                  }`}
                >
                  {step.label}
                </span>
              </li>
            );
          })}
        </ol>
      </CardBody>
    </Card>
  );
}

/* ── Final results ────────────────────────────────────────────────────── */

function PipelineResults({ data }: { data: PipelineRunOut }) {
  const hasErrors = data.errors.length > 0;
  const failed = data.status === 'failed';

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Pipeline Results</h2>
          <div className="flex items-center gap-3">
            <Link
              to={`/pipeline/runs/${data.id}`}
              className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              View Run Details
            </Link>
            <Badge variant={failed ? 'danger' : hasErrors ? 'warning' : 'success'}>
              {failed ? 'Failed' : hasErrors ? 'Completed with warnings' : 'Success'}
            </Badge>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <MiniStat label="Queries" value={data.queries?.length ?? 0} />
            <MiniStat label="Posts Found" value={data.posts_found} />
            <MiniStat label="Relevant" value={data.posts_relevant} />
            <MiniStat label="Comments" value={data.comments_generated} />
          </div>
        </CardBody>
      </Card>

      {/* Generated queries */}
      {(data.queries?.length ?? 0) > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-gray-700">
              Generated Queries ({data.queries.length})
            </h3>
          </CardHeader>
          <CardBody>
            <div className="flex flex-wrap gap-2">
              {data.queries.map((q, i) => (
                <Badge key={i} variant="info">
                  {typeof q === 'string' ? q : q.value}
                </Badge>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Posts + generated comments */}
      {data.posts.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-gray-800">
            Posts & Generated Comments ({data.posts.length})
          </h3>
          {data.posts.map((post) => (
            <Card key={post.id}>
              <CardHeader className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {post.author && (
                      <span className="text-sm font-semibold text-gray-900 truncate">
                        {post.author}
                      </span>
                    )}
                    {post.analysis && (
                      <>
                        <Badge
                          variant={
                            post.analysis.relevance_score >= 0.6
                              ? 'success'
                              : post.analysis.relevance_score >= 0.3
                              ? 'warning'
                              : 'default'
                          }
                        >
                          relevance {(post.analysis.relevance_score * 100).toFixed(0)}%
                        </Badge>
                        {post.analysis.intent && (
                          <Badge variant="info">{post.analysis.intent}</Badge>
                        )}
                      </>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-gray-400 line-clamp-1">
                    {post.post_url}
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-400 shrink-0">
                  <span className="flex items-center gap-1">
                    <ThumbsUp className="h-3.5 w-3.5" />
                    {post.likes}
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageSquare className="h-3.5 w-3.5" />
                    {post.comments_count}
                  </span>
                  <a
                    href={post.post_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:text-blue-700"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </div>
              </CardHeader>
              <CardBody className="space-y-3">
                {/* Post content */}
                <p className="text-sm text-gray-700 line-clamp-4 whitespace-pre-line">
                  {post.content}
                </p>

                {/* Generated comments */}
                {post.comment_candidates && post.comment_candidates.length > 0 ? (
                  <div className="mt-3 space-y-2">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Generated Comments ({post.comment_candidates.length})
                    </h4>
                    {post.comment_candidates.map((cc) => (
                      <div
                        key={cc.id}
                        className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2"
                      >
                        <p className="text-sm text-gray-800 whitespace-pre-line">
                          {cc.comment_text}
                        </p>
                        <div className="mt-1 flex items-center gap-2 text-xs text-gray-400">
                          <span>Score: {(cc.score * 100).toFixed(0)}%</span>
                          {cc.critique && (
                            <span className="truncate max-w-xs">· {cc.critique}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  post.analysis && post.analysis.relevance_score < 0.1 && (
                    <p className="text-xs text-gray-400 italic">
                      Post relevance too low — no comment generated.
                    </p>
                  )
                )}

                <div className="pt-1">
                  <Link
                    to={`/posts/${post.id}`}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    View full post →
                  </Link>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Errors */}
      {hasErrors && (
        <Card>
          <CardHeader>
            <h3 className="flex items-center gap-2 text-sm font-semibold text-red-600">
              <AlertTriangle className="h-4 w-4" />
              Errors ({data.errors.length})
            </h3>
          </CardHeader>
          <CardBody className="space-y-2">
            {data.errors.map((err, i) => (
              <p key={i} className="text-sm text-red-700">
                {err}
              </p>
            ))}
          </CardBody>
        </Card>
      )}
    </div>
  );
}

/* ── Helpers ──────────────────────────────────────────────────────────── */

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

function NumberInput({
  label,
  value,
  min,
  max,
  step = 1,
  disabled,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  disabled?: boolean;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">
        {label}
      </label>
      <input
        type="number"
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                   focus:border-blue-500 focus:ring-1 focus:ring-blue-500
                   disabled:bg-gray-50"
        value={value}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}
