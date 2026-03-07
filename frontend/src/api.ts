/* ── API client — thin wrapper over fetch ────────────────────────────── */

import type {
  CommentOut,
  CommentStatus,
  HealthResponse,
  PipelineRequest,
  PipelineStartResponse,
  PipelineRunListOut,
  PipelineRunOut,
  PostDetailOut,
  PostListOut,
} from './types';

const BASE = '/api/v1';

class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API error ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });

  // Read body once as text, then parse — avoids "body stream already read"
  const text = await res.text();

  if (!res.ok) {
    let body: unknown;
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
    throw new ApiError(res.status, body);
  }

  return JSON.parse(text) as T;
}

/* ── Health ───────────────────────────────────────────────────────────── */

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

/* ── Pipeline ─────────────────────────────────────────────────────────── */

export function runPipeline(body: PipelineRequest): Promise<PipelineStartResponse> {
  return request<PipelineStartResponse>(`${BASE}/pipeline`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function listPipelineRuns(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<PipelineRunListOut> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.limit != null) qs.set('limit', String(params.limit));
  if (params?.offset != null) qs.set('offset', String(params.offset));
  const q = qs.toString();
  return request<PipelineRunListOut>(`${BASE}/pipeline/runs${q ? `?${q}` : ''}`);
}

export function getPipelineRun(runId: string): Promise<PipelineRunOut> {
  return request<PipelineRunOut>(`${BASE}/pipeline/runs/${runId}`);
}

/* ── Posts ─────────────────────────────────────────────────────────────── */

export function listPosts(params?: {
  platform?: string;
  min_relevance?: number;
  limit?: number;
  offset?: number;
}): Promise<PostListOut> {
  const qs = new URLSearchParams();
  if (params?.platform) qs.set('platform', params.platform);
  if (params?.min_relevance != null) qs.set('min_relevance', String(params.min_relevance));
  if (params?.limit != null) qs.set('limit', String(params.limit));
  if (params?.offset != null) qs.set('offset', String(params.offset));
  const q = qs.toString();
  return request<PostListOut>(`${BASE}/posts${q ? `?${q}` : ''}`);
}

export function getPost(postId: string): Promise<PostDetailOut> {
  return request<PostDetailOut>(`${BASE}/posts/${postId}`);
}

/* ── Comments ─────────────────────────────────────────────────────────── */

export function listComments(
  postId: string,
  status?: CommentStatus,
): Promise<CommentOut[]> {
  const qs = status ? `?status=${status}` : '';
  return request<CommentOut[]>(`${BASE}/comments/post/${postId}${qs}`);
}

export function updateCommentStatus(
  commentId: string,
  status: CommentStatus,
): Promise<CommentOut> {
  return request<CommentOut>(`${BASE}/comments/${commentId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export { ApiError };
