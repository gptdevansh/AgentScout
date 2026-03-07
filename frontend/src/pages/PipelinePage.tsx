/* ── Pipeline page — kick off and monitor a run ──────────────────────── */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
  Rocket,
  Search,
} from 'lucide-react';
import { runPipeline } from '../api';
import type { PipelineRequest, PipelineResponse } from '../types';
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
  num_queries: 5,
  max_posts_per_query: 5,
  min_relevance: 0.5,
  platform: 'linkedin',
};

export default function PipelinePage() {
  const [form, setForm] = useState<PipelineRequest>(DEFAULT_VALUES);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<PipelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit =
    !running && form.problem_description.trim().length >= 10;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const res = await runPipeline({
        ...form,
        product_description: form.product_description || null,
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  function handleChange(
    key: keyof PipelineRequest,
    value: string | number,
  ) {
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
                  value={form.num_queries ?? 25}
                  min={1}
                  max={100}
                  disabled={running}
                  onChange={(v) => handleChange('num_queries', v)}
                />
                <NumberInput
                  label="Posts / Query"
                  value={form.max_posts_per_query ?? 10}
                  min={1}
                  max={50}
                  disabled={running}
                  onChange={(v) => handleChange('max_posts_per_query', v)}
                />
                <NumberInput
                  label="Min Relevance"
                  value={form.min_relevance ?? 0.5}
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
              <Button type="submit" disabled={!canSubmit} loading={running}>
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

      {/* Results */}
      {result && <PipelineResults data={result} />}
    </div>
  );
}

/* ── Pipeline results display ─────────────────────────────────────────── */

function PipelineResults({ data }: { data: PipelineResponse }) {
  const hasErrors = data.errors.length > 0;

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Pipeline Results
          </h2>
          <div className="flex items-center gap-3">
            {data.run_id && (
              <Link
                to={`/pipeline/runs/${data.run_id}`}
                className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                View Run Details
              </Link>
            )}
            <Badge variant={hasErrors ? 'warning' : 'success'}>
              {hasErrors ? 'Completed with warnings' : 'Success'}
            </Badge>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <MiniStat label="Queries" value={data.queries.length} />
            <MiniStat label="Posts Found" value={data.posts_found} />
            <MiniStat label="Relevant" value={data.posts_relevant} />
            <MiniStat label="Comments" value={data.comments_generated} />
          </div>
        </CardBody>
      </Card>

      {/* Steps timeline */}
      {data.steps.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-gray-700">Step Timeline</h3>
          </CardHeader>
          <CardBody className="space-y-3">
            {data.steps.map((step, i) => (
              <div key={i} className="flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                <div className="flex-1">
                  <span className="text-sm font-medium text-gray-800 capitalize">
                    {step.name.replace(/_/g, ' ')}
                  </span>
                  <span className="ml-2 text-xs text-gray-400">
                    {step.count} items
                  </span>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Clock className="h-3.5 w-3.5" />
                  {formatDuration(step.duration_ms)}
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      {/* Generated queries */}
      {data.queries.length > 0 && (
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
                  {q}
                </Badge>
              ))}
            </div>
          </CardBody>
        </Card>
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

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const secs = ms / 1000;
  if (secs < 60) return `${secs.toFixed(1)}s`;
  const mins = Math.floor(secs / 60);
  const remSecs = Math.round(secs % 60);
  return `${mins}m ${remSecs}s`;
}
