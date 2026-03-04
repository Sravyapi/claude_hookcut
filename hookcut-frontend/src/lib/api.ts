import type {
  VideoValidation,
  AnalyzeResponse,
  TaskStatus,
  HooksResponse,
  SelectHooksResponse,
  RegenerateResponse,
  Short,
  DownloadResponse,
  CreditBalance,
  UserProfile,
  HistoryResponse,
  PlansResponse,
  CheckoutResponse,
  AdminDashboard,
  AdminUserList,
  AdminUser,
  AdminSessionList,
  AdminSessionDetail,
  AuditLogList,
  PromptRule,
  PromptRuleHistory,
  PromptPreview,
  ProviderConfig,
  NarmInsight,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// ─── Auth Token Helper ───

let cachedToken: string | null = null;
let tokenFetchedAt = 0;
const TOKEN_TTL_MS = 4 * 60 * 1000; // refresh every 4 min (JWT lives 5+ min)
let tokenPromise: Promise<string | null> | null = null;

async function getAuthToken(): Promise<string | null> {
  const now = Date.now();
  if (cachedToken && now - tokenFetchedAt < TOKEN_TTL_MS) {
    return cachedToken;
  }
  if (tokenPromise !== null) {
    return tokenPromise;
  }
  tokenPromise = (async () => {
    try {
      const res = await fetch("/api/auth/token");
      if (!res.ok) return null;
      const data = await res.json();
      cachedToken = data.token;
      tokenFetchedAt = Date.now();
      return cachedToken;
    } catch {
      return null;
    }
  })().finally(() => {
    tokenPromise = null;
  });
  return tokenPromise;
}

// ─── Request Helper ───

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = await getAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// ─── API Client ───

export const api = {
  // V0 endpoints
  validateUrl: (youtube_url: string) =>
    request<VideoValidation>("/validate-url", {
      method: "POST",
      body: JSON.stringify({ youtube_url }),
    }),

  analyze: (youtube_url: string, niche: string, language: string) =>
    request<AnalyzeResponse>("/analyze", {
      method: "POST",
      body: JSON.stringify({ youtube_url, niche, language }),
    }),

  getTaskStatus: (taskId: string) =>
    request<TaskStatus>(`/tasks/${taskId}`),

  getHooks: (sessionId: string) =>
    request<HooksResponse>(`/sessions/${sessionId}/hooks`),

  regenerateHooks: (sessionId: string) =>
    request<RegenerateResponse>(`/sessions/${sessionId}/regenerate`, {
      method: "POST",
    }),

  selectHooks: (
    sessionId: string,
    hookIds: string[],
    captionStyle: string = "clean",
    timeOverrides: Record<string, { start_seconds: number; end_seconds: number }> = {},
  ) =>
    request<SelectHooksResponse>(`/sessions/${sessionId}/select-hooks`, {
      method: "POST",
      body: JSON.stringify({
        hook_ids: hookIds,
        caption_style: captionStyle,
        time_overrides: timeOverrides,
      }),
    }),

  getShort: (shortId: string) =>
    request<Short>(`/shorts/${shortId}`),

  downloadShort: (shortId: string) =>
    request<DownloadResponse>(`/shorts/${shortId}/download`, {
      method: "POST",
    }),

  getBalance: () =>
    request<CreditBalance>("/user/balance"),

  // V1 auth / billing / user endpoints
  syncUser: (email: string) =>
    request<{ user_id: string; is_new: boolean; plan_tier: string; role: string }>(`/auth/sync?email=${encodeURIComponent(email)}`, {
      method: "POST",
    }),

  getPlans: () =>
    request<PlansResponse>("/billing/plans"),

  createCheckout: (planTier: string) =>
    request<CheckoutResponse>("/billing/checkout?plan_tier=" + planTier, {
      method: "POST",
    }),

  purchasePayg: (minutes: number) =>
    request<CreditBalance>("/billing/payg?minutes=" + minutes, {
      method: "POST",
    }),

  getHistory: (page?: number) =>
    request<HistoryResponse>("/user/history" + (page ? "?page=" + page : "")),

  getProfile: () =>
    request<UserProfile>("/user/profile"),

  updateCurrency: (currency: string) =>
    request<UserProfile>("/user/currency", {
      method: "PATCH",
      body: JSON.stringify({ currency }),
    }),

  // ─── Admin endpoints ───

  adminDashboard: () =>
    request<AdminDashboard>("/admin/dashboard"),

  adminUsers: (page?: number) =>
    request<AdminUserList>("/admin/users" + (page ? "?page=" + page : "")),

  adminUpdateRole: (userId: string, role: string) =>
    request<AdminUser>(`/admin/users/${userId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    }),

  adminSessions: (page?: number, status?: string) => {
    const params = new URLSearchParams();
    if (page) params.set("page", String(page));
    if (status) params.set("status", status);
    const qs = params.toString();
    return request<AdminSessionList>("/admin/sessions" + (qs ? "?" + qs : ""));
  },

  adminSessionDetail: (sessionId: string) =>
    request<AdminSessionDetail>(`/admin/sessions/${sessionId}`),

  adminAuditLogs: (page?: number, action?: string) => {
    const params = new URLSearchParams();
    if (page) params.set("page", String(page));
    if (action) params.set("action", action);
    const qs = params.toString();
    return request<AuditLogList>("/admin/audit-logs" + (qs ? "?" + qs : ""));
  },

  adminRules: () =>
    request<{ rules: PromptRule[] }>("/admin/rules"),

  adminCreateRule: (data: { title: string; content: string; rule_key?: string }) =>
    request<PromptRule>("/admin/rules", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  adminUpdateRule: (ruleId: string, data: { title?: string; content?: string; is_active?: boolean }) =>
    request<PromptRule>(`/admin/rules/${ruleId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  adminRuleHistory: (ruleKey: string) =>
    request<PromptRuleHistory>(`/admin/rules/${ruleKey}/history`),

  adminRevertRule: (ruleId: string, versionId: string) =>
    request<PromptRule>(`/admin/rules/${ruleId}/revert/${versionId}`, {
      method: "POST",
    }),

  adminDeleteRule: (ruleId: string) =>
    request<{ status: string }>(`/admin/rules/${ruleId}`, {
      method: "DELETE",
    }),

  adminPreviewPrompt: (niche: string, language: string) =>
    request<PromptPreview>("/admin/rules/preview", {
      method: "POST",
      body: JSON.stringify({ niche, language }),
    }),

  adminSeedRules: () =>
    request<{ rules: PromptRule[] }>("/admin/rules/seed", {
      method: "POST",
    }),

  adminProviders: () =>
    request<{ providers: ProviderConfig[] }>("/admin/providers"),

  adminUpdateProvider: (name: string, data: { is_enabled?: boolean; model_id?: string }) =>
    request<ProviderConfig>(`/admin/providers/${name}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  adminSetPrimary: (name: string) =>
    request<ProviderConfig>(`/admin/providers/${name}/set-primary`, {
      method: "POST",
    }),

  adminSetApiKey: (name: string, apiKey: string) =>
    request<ProviderConfig>(`/admin/providers/${name}/set-key`, {
      method: "POST",
      body: JSON.stringify({ api_key: apiKey }),
    }),

  adminNarmAnalyze: (timeRangeDays?: number) =>
    request<{ insights: NarmInsight[] }>("/admin/narm/analyze", {
      method: "POST",
      body: JSON.stringify({ time_range_days: timeRangeDays || 30 }),
    }),

  adminNarmInsights: () =>
    request<{ insights: NarmInsight[] }>("/admin/narm/insights"),
};
