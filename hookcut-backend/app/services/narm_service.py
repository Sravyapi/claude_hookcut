"""NarmService — NARM (Niche-Aware Recommendation Model) insight generation."""

import json
import logging
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import AnalysisSession, Hook
from app.models.learning import LearningLog
from app.models.admin import NarmInsight
from app.exceptions import HookCutError

logger = logging.getLogger(__name__)


class NarmService:
    """All methods are static — no instance state required."""

    @staticmethod
    def _aggregate_hook_selection_data(db: Session, cutoff: datetime) -> dict:
        """Aggregate hook selection rates by hook_type since cutoff."""
        presented_stmt = (
            select(
                LearningLog.event_metadata["hook_type"].label("hook_type"),
                func.count(LearningLog.id).label("cnt"),
            )
            .where(
                LearningLog.event_type == "hook_presented",
                LearningLog.created_at >= cutoff,
            )
            .group_by("hook_type")
        )
        selected_stmt = (
            select(
                LearningLog.event_metadata["hook_type"].label("hook_type"),
                func.count(LearningLog.id).label("cnt"),
            )
            .where(
                LearningLog.event_type == "hook_selected",
                LearningLog.created_at >= cutoff,
            )
            .group_by("hook_type")
        )

        presented_rows = db.execute(presented_stmt).all()
        selected_rows = db.execute(selected_stmt).all()

        presented_map = {
            str(row.hook_type): row.cnt for row in presented_rows
        }
        selected_map = {
            str(row.hook_type): row.cnt for row in selected_rows
        }

        selection_rates = {}
        for ht, presented_count in presented_map.items():
            sel_count = selected_map.get(ht, 0)
            rate = (sel_count / presented_count * 100) if presented_count > 0 else 0
            selection_rates[ht] = {
                "presented": presented_count,
                "selected": sel_count,
                "rate_pct": round(rate, 1),
            }
        return selection_rates

    @staticmethod
    def _aggregate_niche_data(db: Session, cutoff: datetime) -> tuple[list[dict], int, int, float]:
        """Aggregate popular niches and regeneration rate since cutoff.

        Returns (popular_niches, total_sessions_count, regen_sessions_count, regen_rate).
        """
        niche_stmt = (
            select(
                LearningLog.niche,
                func.count(LearningLog.id).label("cnt"),
            )
            .where(
                LearningLog.event_type == "hook_presented",
                LearningLog.created_at >= cutoff,
            )
            .group_by(LearningLog.niche)
            .order_by(desc("cnt"))
            .limit(10)
        )
        niche_rows = db.execute(niche_stmt).all()
        popular_niches = [
            {"niche": row.niche, "count": row.cnt}
            for row in niche_rows
        ]

        total_sessions_count = db.scalar(
            select(func.count(func.distinct(LearningLog.session_id)))
            .where(LearningLog.created_at >= cutoff)
        ) or 0

        regen_sessions_count = db.scalar(
            select(func.count(func.distinct(LearningLog.session_id)))
            .where(
                LearningLog.event_type == "regeneration_triggered",
                LearningLog.created_at >= cutoff,
            )
        ) or 0

        regen_rate = (
            (regen_sessions_count / total_sessions_count * 100)
            if total_sessions_count > 0
            else 0
        )

        return popular_niches, total_sessions_count, regen_sessions_count, regen_rate

    @staticmethod
    def _aggregate_attention_scores(db: Session, cutoff: datetime) -> dict:
        """Aggregate average attention scores by niche since cutoff."""
        attn_stmt = (
            select(
                AnalysisSession.niche,
                func.avg(Hook.attention_score).label("avg_score"),
            )
            .join(
                AnalysisSession,
                Hook.session_id == AnalysisSession.id,
            )
            .where(AnalysisSession.created_at >= cutoff)
            .group_by(AnalysisSession.niche)
        )
        attn_rows = db.execute(attn_stmt).all()
        return {
            row.niche: round(float(row.avg_score), 2)
            for row in attn_rows
            if row.avg_score is not None
        }

    @staticmethod
    def _build_narm_summary(
        time_range_days: int,
        selection_rates: dict,
        popular_niches: list[dict],
        regen_rate: float,
        total_sessions_count: int,
        regen_sessions_count: int,
        avg_attention: dict,
    ) -> dict:
        """Format aggregated data into the summary dict for LLM consumption."""
        return {
            "time_range_days": time_range_days,
            "hook_selection_rates": selection_rates,
            "popular_niches": popular_niches,
            "regeneration_rate_pct": round(regen_rate, 1),
            "total_sessions": total_sessions_count,
            "regen_sessions": regen_sessions_count,
            "avg_attention_by_niche": avg_attention,
        }

    @staticmethod
    def trigger_narm_analysis(
        db: Session, time_range_days: int, admin_user: User
    ) -> list[NarmInsight]:
        """
        Query LearningLog aggregates, call primary LLM provider to
        generate insights, store and return NarmInsight records.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_range_days)

        try:
            selection_rates = NarmService._aggregate_hook_selection_data(db, cutoff)
            popular_niches, total_sessions_count, regen_sessions_count, regen_rate = (
                NarmService._aggregate_niche_data(db, cutoff)
            )
            avg_attention = NarmService._aggregate_attention_scores(db, cutoff)

            summary = NarmService._build_narm_summary(
                time_range_days, selection_rates, popular_niches,
                regen_rate, total_sessions_count, regen_sessions_count,
                avg_attention,
            )

            # --- Call LLM ---
            # Use ensure_ascii=True + code fences to prevent prompt injection
            # from any string values embedded in the analytics data
            data_str = json.dumps(summary, ensure_ascii=True, separators=(",", ":"))
            llm_prompt = (
                "You are an analytics expert for HookCut, a YouTube Shorts "
                "hook extraction platform. Analyze this data and generate "
                "3-5 actionable insights.\n\n"
                f"DATA:\n```json\n{data_str}\n```\n\n"
                "Return ONLY valid JSON array with 3-5 objects, each with:\n"
                '{"insight_type": "hook_preference|niche_trend|'
                'regeneration_pattern|engagement_pattern",\n'
                ' "title": "short title",\n'
                ' "content": "detailed insight (2-3 sentences)",\n'
                ' "confidence": "high|medium|low"}\n'
            )

            insights: list[NarmInsight] = []

            try:
                from app.llm.provider import get_provider
                from app.config import get_settings

                provider = get_provider(
                    get_settings().LLM_PRIMARY_PROVIDER
                )
                response = provider.generate(llm_prompt, max_tokens=2000)
                raw_text = response.text.strip()

                # Try to parse JSON from the response
                # Handle markdown code blocks wrapping
                if raw_text.startswith("```"):
                    raw_text = re.sub(
                        r"^```(?:json)?\s*", "", raw_text
                    )
                    raw_text = re.sub(r"\s*```$", "", raw_text)

                parsed = json.loads(raw_text)
                if not isinstance(parsed, list):
                    parsed = [parsed]

                # Map LLM string confidence labels to float values
                _CONFIDENCE_MAP = {"high": 0.9, "medium": 0.5, "low": 0.2}

                for item in parsed[:5]:
                    raw_conf = item.get("confidence", "medium")
                    if isinstance(raw_conf, str):
                        conf_float = _CONFIDENCE_MAP.get(raw_conf.lower(), 0.5)
                    else:
                        conf_float = float(raw_conf) if raw_conf else 0.5
                    insight = NarmInsight(
                        insight_type=item.get(
                            "insight_type", "engagement_pattern"
                        ),
                        title=item.get("title", "Untitled Insight"),
                        content=item.get("content", ""),
                        data_summary=summary,
                        confidence=conf_float,
                        time_range_days=time_range_days,
                    )
                    db.add(insight)
                    insights.append(insight)

            except Exception as llm_err:
                logger.warning(
                    "LLM call for NARM failed, generating basic insights: %s",
                    llm_err,
                )
                # Generate basic insights from data without LLM
                basic_insight = NarmInsight(
                    insight_type="engagement_pattern",
                    title=f"Data summary for last {time_range_days} days",
                    content=(
                        f"Analyzed {total_sessions_count} sessions. "
                        f"Regeneration rate: {round(regen_rate, 1)}%. "
                        f"Top niches: {', '.join(n['niche'] for n in popular_niches[:3])}."
                    ),
                    data_summary=summary,
                    confidence=0.2,
                    time_range_days=time_range_days,
                )
                db.add(basic_insight)
                insights.append(basic_insight)

            db.flush()

            from app.services.admin_service import AdminService
            AdminService.create_audit_log(
                db,
                admin_user=admin_user,
                action="narm_triggered",
                resource_type="narm_insight",
                resource_id=None,
                before_state=None,
                after_state={
                    "time_range_days": time_range_days,
                    "insights_generated": len(insights),
                },
                description=(
                    f"Triggered NARM analysis for {time_range_days} days, "
                    f"generated {len(insights)} insights"
                ),
            )
            db.commit()
            for ins in insights:
                db.refresh(ins)
            return insights

        except HookCutError:
            raise
        except Exception as e:
            db.rollback()
            logger.exception("NARM analysis failed")
            raise HookCutError(f"NARM analysis error: {e}") from e

    @staticmethod
    def get_narm_insights(db: Session) -> list[NarmInsight]:
        """Latest insights ordered by created_at desc, limit 20."""
        stmt = (
            select(NarmInsight)
            .order_by(desc(NarmInsight.created_at))
            .limit(20)
        )
        return list(db.scalars(stmt).all())
