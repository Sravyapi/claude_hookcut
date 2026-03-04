from pydantic import BaseModel
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class AdminSessionSummary(BaseModel):
    id: str
    user_email: str
    video_title: str
    video_id: str
    niche: str
    status: str
    minutes_charged: float
    created_at: str

    model_config = {"from_attributes": True}


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_sessions: int
    total_shorts: int
    active_subscriptions: int
    recent_sessions: list[AdminSessionSummary]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


class AdminUserResponse(BaseModel):
    id: str
    email: str
    role: str
    plan_tier: str
    currency: str
    created_at: str
    session_count: int

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    users: list[AdminUserResponse]
    total: int
    page: int
    per_page: int


class RoleUpdateRequest(BaseModel):
    role: Literal["user", "admin"]


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class AdminSessionListResponse(BaseModel):
    sessions: list[AdminSessionSummary]
    total: int
    page: int
    per_page: int


class AdminSessionDetailResponse(AdminSessionSummary):
    hooks: list[dict]
    shorts: list[dict]
    transcript_text: Optional[str] = None


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditLogResponse(BaseModel):
    id: str
    admin_email: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: str
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    created_at: str

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int
    page: int
    per_page: int


# ---------------------------------------------------------------------------
# Prompt Rules
# ---------------------------------------------------------------------------


class PromptRuleResponse(BaseModel):
    id: str
    rule_key: str
    version: int
    title: str
    content: str
    is_base_rule: bool
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class PromptRuleListResponse(BaseModel):
    rules: list[PromptRuleResponse]


class PromptRuleCreateRequest(BaseModel):
    title: str
    content: str
    rule_key: Optional[str] = None


class PromptRuleUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


class PromptRuleHistoryResponse(BaseModel):
    versions: list[PromptRuleResponse]


class PromptPreviewRequest(BaseModel):
    niche: str
    language: str


class PromptPreviewResponse(BaseModel):
    prompt_text: str
    rule_count: int
    character_count: int


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


class ProviderConfigResponse(BaseModel):
    provider_name: str
    is_primary: bool
    is_fallback: bool
    is_enabled: bool
    model_id: str
    api_key_last4: str
    api_key_set: bool
    updated_at: str

    model_config = {"from_attributes": True}


class ProviderListResponse(BaseModel):
    providers: list[ProviderConfigResponse]


class ProviderUpdateRequest(BaseModel):
    is_enabled: Optional[bool] = None
    model_id: Optional[str] = None


class SetApiKeyRequest(BaseModel):
    api_key: str


# ---------------------------------------------------------------------------
# NARM (NyxPath Automated Retention Metrics)
# ---------------------------------------------------------------------------


class NarmInsightResponse(BaseModel):
    id: str
    insight_type: str
    title: str
    content: str
    confidence: float
    time_range_days: int
    created_at: str

    model_config = {"from_attributes": True}


class NarmInsightsListResponse(BaseModel):
    insights: list[NarmInsightResponse]


class NarmAnalyzeRequest(BaseModel):
    time_range_days: int = 30
