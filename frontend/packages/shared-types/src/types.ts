export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  plan: 'free' | 'starter' | 'pro' | 'enterprise';
  credits_remaining: number;
  is_verified: boolean;
  created_at: string;
}
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
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
export interface UploadedFile {
  file_id: string;
  original_url: string;
  mime_type: string;
  size_bytes: number;
  expires_at: string;
}
export type ToolModule = 'ocr' | 'photo' | 'creator' | 'business' | 'agriculture' | 'entertainment';
export interface Tool {
  id: string;
  slug: string;
  name: string;
  description: string;
  module: ToolModule;
  credits_cost: number;
  min_plan: 'free' | 'starter' | 'pro';
  is_active: boolean;
  is_novel: boolean;
  icon: string | null;
}
