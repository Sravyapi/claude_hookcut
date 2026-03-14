from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_admin_user
from app.exceptions import ResourceNotFoundError
from app.services.admin_service import AdminService
from app.services.admin_rule_service import AdminRuleService
from app.services.admin_provider_service import AdminProviderService
from app.services.narm_service import NarmService
from app.middleware.rate_limit import get_rate_limiter
from app.schemas.admin import (
    AdminDashboardResponse, AdminUserListResponse, RoleUpdateRequest,
    AdminSessionListResponse, AdminSessionDetailResponse,
    AuditLogListResponse, PromptRuleResponse, PromptRuleListResponse,
    PromptRuleCreateRequest, PromptRuleUpdateRequest, PromptRuleHistoryResponse,
    PromptPreviewRequest, PromptPreviewResponse,
    ProviderConfigResponse, ProviderListResponse, ProviderUpdateRequest,
    SetApiKeyRequest, NarmAnalyzeRequest, NarmInsightsListResponse,
    AdminUserResponse, HookEngineModeResponse, HookEngineModeUpdateRequest,
)
from app.services.engine_mode import get_engine_mode, set_engine_mode

ADMIN_WRITE_RATE_LIMIT = 20
ADMIN_WRITE_RATE_WINDOW = 3600
ADMIN_KEY_RATE_LIMIT = 5
ADMIN_KEY_RATE_WINDOW = 3600
ADMIN_NARM_RATE_LIMIT = 3
ADMIN_NARM_RATE_WINDOW = 3600

router = APIRouter(prefix="/admin")
rate_limiter = get_rate_limiter()


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
    search: str | None = Query(None, max_length=100),
) -> AdminUserListResponse:
    return AdminService.list_users(db, page, per_page, search)


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
        raise ResourceNotFoundError("Session not found")
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
    return {"rules": AdminRuleService.list_rules(db)}


@router.post("/rules")
async def create_rule(
    request: Request,
    body: PromptRuleCreateRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleResponse:
    rate_limiter.check(admin_user.id, "admin_write", limit=ADMIN_WRITE_RATE_LIMIT, window_seconds=ADMIN_WRITE_RATE_WINDOW, request=request)
    rule = AdminRuleService.create_rule(db, body.title, body.content, body.rule_key, admin_user)
    return rule


@router.post("/rules/preview")
async def preview_prompt(
    body: PromptPreviewRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptPreviewResponse:
    return AdminRuleService.preview_prompt(db, body.niche, body.language)


@router.post("/rules/seed")
async def seed_rules(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleListResponse:
    return {"rules": AdminRuleService.seed_rules(db, admin_user)}


@router.get("/rules/{rule_key}/history")
async def get_rule_history(
    rule_key: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleHistoryResponse:
    return {"versions": AdminRuleService.get_rule_history(db, rule_key)}


@router.patch("/rules/{rule_id}")
async def update_rule(
    request: Request,
    rule_id: str,
    body: PromptRuleUpdateRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleResponse:
    rate_limiter.check(admin_user.id, "admin_write", limit=ADMIN_WRITE_RATE_LIMIT, window_seconds=ADMIN_WRITE_RATE_WINDOW, request=request)
    rule = AdminRuleService.update_rule(db, rule_id, admin_user, body.title, body.content, body.is_active)
    return rule


@router.post("/rules/{rule_id}/revert/{version_id}")
async def revert_rule(
    request: Request,
    rule_id: str,
    version_id: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PromptRuleResponse:
    rate_limiter.check(admin_user.id, "admin_write", limit=ADMIN_WRITE_RATE_LIMIT, window_seconds=ADMIN_WRITE_RATE_WINDOW, request=request)
    rule = AdminRuleService.revert_rule(db, rule_id, version_id, admin_user)
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    AdminRuleService.delete_rule(db, rule_id, admin_user)
    return {"status": "deleted"}


# ── Provider Config ────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ProviderListResponse:
    return {"providers": AdminProviderService.list_providers(db)}


@router.patch("/providers/{provider_name}")
async def update_provider(
    provider_name: str,
    body: ProviderUpdateRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    return AdminProviderService.update_provider(db, provider_name, admin_user, body.is_enabled, body.model_id)


@router.post("/providers/{provider_name}/set-primary")
async def set_primary_provider(
    provider_name: str,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    return AdminProviderService.set_primary_provider(db, provider_name, admin_user)


@router.post("/providers/{provider_name}/set-key")
async def set_api_key(
    request: Request,
    provider_name: str,
    body: SetApiKeyRequest,
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    rate_limiter.check(admin_user.id, "admin_set_key", limit=ADMIN_KEY_RATE_LIMIT, window_seconds=ADMIN_KEY_RATE_WINDOW, request=request)
    return AdminProviderService.set_api_key(db, provider_name, body.api_key, admin_user)


# ── NARM (Niche Audience Response Modeling) ────────────────────────────────

@router.post("/narm/analyze", status_code=202)
async def trigger_narm_analysis(
    request: Request,
    body: NarmAnalyzeRequest,
    admin_user=Depends(get_admin_user),
):
    rate_limiter.check(admin_user.id, "admin_narm", limit=ADMIN_NARM_RATE_LIMIT, window_seconds=ADMIN_NARM_RATE_WINDOW, request=request)
    from app.tasks.narm_task import run_narm_analysis
    run_narm_analysis.delay(body.time_range_days, admin_user.id)
    return {"status": "accepted", "message": "NARM analysis started"}


@router.get("/narm/insights")
async def get_narm_insights(
    admin_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> NarmInsightsListResponse:
    return {"insights": NarmService.get_narm_insights(db)}


# ── Hook Engine Mode ──────────────────────────────────────────────────────


@router.get("/hook-engine-mode")
async def get_hook_engine_mode_endpoint(
    admin_user=Depends(get_admin_user),
) -> HookEngineModeResponse:
    return HookEngineModeResponse(mode=get_engine_mode())


@router.patch("/hook-engine-mode")
async def set_hook_engine_mode_endpoint(
    body: HookEngineModeUpdateRequest,
    admin_user=Depends(get_admin_user),
) -> HookEngineModeResponse:
    mode = set_engine_mode(body.mode)
    return HookEngineModeResponse(mode=mode)
