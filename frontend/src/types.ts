/* ── Types mirroring backend schemas ─────────────────────────────────── */

export interface ScrapingWeapon {
  type: 'keyword' | 'hashtag' | 'url';
  value: string;
}


export interface PipelineRequest {
  problem_description: string;
  product_description?: string | null;
  num_queries?: number;
  max_posts_per_query?: number;
  min_relevance?: number;
  platform?: string;
}

export interface PipelineStepOut {
  name: string;
  count: number;
  duration_ms: number;
}

export interface PipelineResponse {
  run_id: string | null;
  problem_description: string;
  product_description: string | null;
  queries: (string | ScrapingWeapon)[];
  posts_found: number;
  posts_analysed: number;
  posts_relevant: number;
  debates_run: number;
  comments_generated: number;
  steps: PipelineStepOut[];
  errors: string[];
}

export interface AnalysisOut {
  id: string;
  relevance_score: number;
  opportunity_score: number;
  intent: string | null;
  emotion: string | null;
  reasoning: string | null;
}

export interface CommentOut {
  id: string;
  comment_text: string;
  score: number;
  status: CommentStatus;
  version: number;
  critique: string | null;
  created_at: string;
}

export interface PostDetailOut {
  id: string;
  platform: string;
  post_url: string;
  author: string | null;
  content: string;
  likes: number;
  comments_count: number;
  post_timestamp: string | null;
  source_query: string | null;
  pipeline_run_id: string | null;
  created_at: string;
  updated_at: string;
  analysis: AnalysisOut | null;
  comment_candidates: CommentOut[];
}

export interface PostListOut {
  items: PostDetailOut[];
  total: number;
  limit: number;
  offset: number;
}

export type CommentStatus = 'draft' | 'reviewed' | 'selected' | 'rejected';

export interface CommentStatusUpdate {
  status: CommentStatus;
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
}

/* ── Pipeline Run types ──────────────────────────────────────────────── */

export interface PipelineRunPostOut {
  id: string;
  platform: string;
  post_url: string;
  author: string | null;
  content: string;
  likes: number;
  comments_count: number;
  source_query: string | null;
  created_at: string;
  analysis: AnalysisOut | null;
  comment_candidates: CommentOut[];
}

/* ── Async pipeline start response ──────────────────────────────────── */

export interface PipelineStartResponse {
  run_id: string;
  status: string;
  message: string;
}

export interface PipelineRunOut {
  id: string;
  problem_description: string;
  product_description: string | null;
  platform: string;
  status: string;
  queries: (string | ScrapingWeapon)[];
  posts_found: number;
  posts_analysed: number;
  posts_relevant: number;
  debates_run: number;
  comments_generated: number;
  errors: string[];
  created_at: string;
  updated_at: string;
  posts: PipelineRunPostOut[];
}

export interface PipelineRunSummaryOut {
  id: string;
  problem_description: string;
  product_description: string | null;
  platform: string;
  status: string;
  posts_found: number;
  posts_relevant: number;
  comments_generated: number;
  errors: string[];
  created_at: string;
  updated_at: string;
}

export interface PipelineRunListOut {
  items: PipelineRunSummaryOut[];
  total: number;
  limit: number;
  offset: number;
}
