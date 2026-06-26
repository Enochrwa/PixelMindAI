// ─────────────────────────────────────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  plan: 'free' | 'starter' | 'professional' | 'business';
  credits_remaining: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Files
// ─────────────────────────────────────────────────────────────────────────────

export interface UploadedFile {
  file_id: string;
  original_url: string;
  mime_type: string;
  size_bytes: number;
  expires_at: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Jobs
// ─────────────────────────────────────────────────────────────────────────────

export type JobStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface Job {
  job_id: string;
  status: JobStatus;
  tool_slug: string;
  result: unknown;
  error: string | null;
  credits_used: number;
  processing_time_ms: number | null;
}

export interface ProcessResponse {
  job_id: string;
  status: string;
  message: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Tools
// ─────────────────────────────────────────────────────────────────────────────

export interface Tool {
  id: string;
  slug: string;
  name: string;
  description: string;
  module: string;
  credits_cost: number;
  min_plan: string;
  is_active: boolean;
  is_novel: boolean;
  icon: string | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// API errors
// ─────────────────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | { error: string; message?: string };
}
