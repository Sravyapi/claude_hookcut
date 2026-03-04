from pydantic import BaseModel, field_validator


class HookScores(BaseModel):
    scroll_stop: float = 0
    curiosity_gap: float = 0
    stakes_intensity: float = 0
    emotional_voltage: float = 0
    standalone_clarity: float = 0
    thematic_focus: float = 0
    thought_completeness: float = 0

    @field_validator(
        "scroll_stop",
        "curiosity_gap",
        "stakes_intensity",
        "emotional_voltage",
        "standalone_clarity",
        "thematic_focus",
        "thought_completeness",
    )
    @classmethod
    def clamp_score(cls, v: float) -> float:
        return max(0.0, min(10.0, v))


class HookResponse(BaseModel):
    id: str
    rank: int
    hook_text: str
    start_time: str
    end_time: str
    hook_type: str
    funnel_role: str
    scores: HookScores
    attention_score: float
    platform_dynamics: str
    viewer_psychology: str
    improvement_suggestion: str = ""
    is_composite: bool
    is_selected: bool


class HooksListResponse(BaseModel):
    session_id: str
    status: str
    hooks: list[HookResponse]
    regeneration_count: int
