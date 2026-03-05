from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_admin_user
from app.services.admin_service import AdminService
from app.schemas.admin import (
    AdminDashboardResponse, AdminUserListResponse, RoleUpdateRequest,
    AdminSessionListResponse, AdminSessionDetailResponse,
    AuditLogListResponse, PromptRuleResponse, PromptRuleListResponse,
    PromptRuleCreateRequest, PromptRuleUpdateRequest, PromptRuleHistoryResponse,
    PromptPreviewRequest, PromptPreviewResponse,
    ProviderConfigResponse, ProviderListResponse, ProviderUpdateRequest,
    SetApiKeyRequest, NarmAnalyzeRequest, NarmInsightsListResponse,
    AdminUserResponse,
)

router = APIRouter(prefix="/admin")


# ── Dashboard ──────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def admin_dashboard(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminDashboardResponse:
    stats = AdminService.get_dashboard_stats(db)
    return stats


# ── Users ──────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> AdminUserListResponse:
    return AdminService.list_users(db, page, per_page)


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    body: RoleUpdateRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    user = AdminService.update_user_role(db, user_id, body.role, admin_user)
    return user


# ── Sessions ───────────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
) -> AdminSessionListResponse:
    return AdminService.list_all_sessions(db, page, per_page, status)


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminSessionDetailResponse:
    detail = AdminService.get_session_detail(db, session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail


# ── Audit Logs ─────────────────────────────────────────────────────────────

@router.get("/audit-logs")
async def list_audit_logs(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: str | None = Query(None),
) -> AuditLogListResponse:
    return AdminService.list_audit_logs(db, page, per_page, action)


@router.get("/audit-logs/export")
async def export_audit_logs(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
) -> list[dict]:
    return AdminService.export_audit_logs(db, start_date, end_date)


# ── Prompt Rules ───────────────────────────────────────────────────────────
# NOTE: /rules/preview and /rules/seed are placed BEFORE /rules/{rule_key}/history
# to avoid FastAPI treating "preview" or "seed" as a path parameter.

@router.get("/rules")
async def list_rules(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleListResponse:
    return {"rules": AdminService.list_rules(db)}


@router.post("/rules")
async def create_rule(
    body: PromptRuleCreateRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleResponse:
    rule = AdminService.create_rule(db, body.title, body.content, body.rule_key, admin_user)
    return rule


@router.post("/rules/preview")
async def preview_prompt(
    body: PromptPreviewRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptPreviewResponse:
    return AdminService.preview_prompt(db, body.niche, body.language)


@router.post("/rules/seed")
async def seed_rules(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleListResponse:
    return {"rules": AdminService.seed_rules(db, admin_user)}


@router.get("/rules/{rule_key}/history")
async def get_rule_history(
    rule_key: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleHistoryResponse:
    return {"versions": AdminService.get_rule_history(db, rule_key)}


@router.patch("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    body: PromptRuleUpdateRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleResponse:
    rule = AdminService.update_rule(db, rule_id, admin_user, body.title, body.content, body.is_active)
    return rule


@router.post("/rules/{rule_id}/revert/{version_id}")
async def revert_rule(
    rule_id: str,
    version_id: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleResponse:
    rule = AdminService.revert_rule(db, rule_id, version_id, admin_user)
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    AdminService.delete_rule(db, rule_id, admin_user)
    return {"status": "deleted"}


# ── Provider Config ────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ProviderListResponse:
    return {"providers": AdminService.list_providers(db)}


@router.patch("/providers/{provider_name}")
async def update_provider(
    provider_name: str,
    body: ProviderUpdateRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    return AdminService.update_provider(db, provider_name, admin_user, body.is_enabled, body.model_id)


@router.post("/providers/{provider_name}/set-primary")
async def set_primary_provider(
    provider_name: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    return AdminService.set_primary_provider(db, provider_name, admin_user)


@router.post("/providers/{provider_name}/set-key")
async def set_api_key(
    provider_name: str,
    body: SetApiKeyRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    return AdminService.set_api_key(db, provider_name, body.api_key, admin_user)


# ── NARM (Niche Audience Response Modeling) ────────────────────────────────

@router.post("/narm/analyze")
async def trigger_narm_analysis(
    body: NarmAnalyzeRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> NarmInsightsListResponse:
    return {"insights": AdminService.trigger_narm_analysis(db, body.time_range_days, admin_user)}


@router.get("/narm/insights")
async def get_narm_insights(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> NarmInsightsListResponse:
    return {"insights": AdminService.get_narm_insights(db)}
