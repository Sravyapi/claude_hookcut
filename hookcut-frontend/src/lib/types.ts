// ─── API Response Types ───

export interface VideoValidation {
  valid: boolean;
  video_id: string | null;
  title: string | null;
  duration_seconds: number | null;
  error: string | null;
}

export interface VideoMeta {
  video_id: string;
  title: string;
  duration_seconds: number;
}

export interface AnalyzeResponse {
  session_id: string;
  task_id: string;
  video_title: string;
  video_duration_seconds: number;
  minutes_charged: number;
  is_watermarked: boolean;
}

export interface TaskStatus {
  task_id: string;
  status: "PENDING" | "STARTED" | "PROGRESS" | "SUCCESS" | "FAILURE";
  progress: number | null;
  stage: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface HookScores {
  scroll_stop: number;
  curiosity_gap: number;
  stakes_intensity: number;
  emotional_voltage: number;
  standalone_clarity: number;
  thematic_focus: number;
  thought_completeness: number;
}

export interface Hook {
  id: string;
  rank: number;
  hook_text: string;
  start_time: string;
  end_time: string;
  hook_type: string;
  funnel_role: string;
  scores: HookScores;
  attention_score: number;
  platform_dynamics: string;
  viewer_psychology: string;
  improvement_suggestion: string;
  is_composite: boolean;
  is_selected: boolean;
}

export interface HooksResponse {
  session_id: string;
  status: string;
  hooks: Hook[];
  regeneration_count: number;
}

export interface SelectHooksResponse {
  short_ids: string[];
  task_ids: string[];
}

export interface RegenerateResponse {
  session_id: string;
  task_id: string;
  regeneration_count: number;
  fee_charged: number | null;
  currency: string | null;
}

export interface Short {
  id: string;
  hook_id: string;
  status: string;
  is_watermarked: boolean;
  title: string | null;
  cleaned_captions: string | null;
  duration_seconds: number | null;
  file_size_bytes: number | null;
  download_url: string | null;
  download_url_expires_at: string | null;
  thumbnail_url: string | null;
  error_message: string | null;
}

export interface DownloadResponse {
  download_url: string;
  expires_at: string;
}

export interface CreditBalance {
  paid_minutes_remaining: number;
  paid_minutes_total: number;
  free_minutes_remaining: number;
  free_minutes_total: number;
  payg_minutes_remaining: number;
  total_available: number;
}

export type CaptionStyle = "clean" | "bold" | "neon" | "minimal";

export type Step = "input" | "analyzing" | "hooks" | "shorts";

// ─── Constants ───

export const POLL_CONFIG = {
  initial: 1000,
  multiplier: 1.5,
  max: 5000,
} as const;

export const DEFAULT_LANGUAGE = "English";
export const DEFAULT_NICHE = "Generic";

export const SHORT_STATUS = {
  QUEUED: "queued",
  DOWNLOADING: "downloading",
  PROCESSING: "processing",
  UPLOADING: "uploading",
  READY: "ready",
  FAILED: "failed",
} as const;

// ─── V1 Types ───

export interface UserProfile {
  id: string;
  email: string;
  currency: string;
  plan_tier: string;
  role: string;
  created_at: string;
}

export interface SessionSummary {
  id: string;
  video_title: string;
  video_id: string;
  niche: string;
  language: string;
  status: string;
  minutes_charged: number;
  is_watermarked: boolean;
  regeneration_count: number;
  created_at: string;
}

export interface HistoryResponse {
  sessions: SessionSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface PlansResponse {
  current_tier: string;
  currency: string;
  plans: PlanInfo[];
}

export interface PlanInfo {
  tier: string;
  price_display: string;
  watermark_free_minutes: number;
  currency: string;
}

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

// ─── Admin Types ───

export interface AdminDashboard {
  total_users: number;
  total_sessions: number;
  total_shorts: number;
  active_subscriptions: number;
  recent_sessions: AdminSessionSummary[];
}

export interface AdminUser {
  id: string;
  email: string;
  role: string;
  plan_tier: string;
  currency: string;
  created_at: string;
  session_count: number;
}

export interface AdminUserList {
  users: AdminUser[];
  total: number;
  page: number;
  per_page: number;
}

export interface AdminSessionSummary {
  id: string;
  user_email: string;
  video_title: string;
  video_id: string;
  niche: string;
  status: string;
  minutes_charged: number;
  created_at: string;
}

export interface AdminSessionDetail extends AdminSessionSummary {
  hooks: Hook[];
  shorts: Short[];
  transcript_text: string | null;
}

export interface AdminSessionList {
  sessions: AdminSessionSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface AuditLog {
  id: string;
  admin_email: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  description: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogList {
  logs: AuditLog[];
  total: number;
  page: number;
  per_page: number;
}

export interface PromptRule {
  id: string;
  rule_key: string;
  version: number;
  title: string;
  content: string;
  is_base_rule: boolean;
  is_active: boolean;
  created_at: string;
}

export interface PromptRuleHistory {
  versions: PromptRule[];
}

export interface PromptPreview {
  prompt_text: string;
  rule_count: number;
  character_count: number;
}

export interface ProviderConfig {
  provider_name: string;
  is_primary: boolean;
  is_fallback: boolean;
  is_enabled: boolean;
  model_id: string;
  api_key_last4: string;
  api_key_set: boolean;
  updated_at: string;
}

export interface NarmInsight {
  id: string;
  insight_type: string;
  title: string;
  content: string;
  confidence: string;
  time_range_days: number;
  created_at: string;
}
