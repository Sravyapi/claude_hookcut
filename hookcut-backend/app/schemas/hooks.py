from pydantic import BaseModel, field_validator


class HookScores(BaseModel):
    scroll_stop: float = 0
    curiosity_gap: float = 0
    stakes_intensity: float = 0
    emotional_voltage: float = 0
    standalone_clarity: float = 0
    thought_completeness: float = 0
    click_through_likelihood: float = 0
    linguistic_compression: float = 0
    novelty_delta: float = 0
    information_density: float = 0

    @field_validator(
        "scroll_stop",
        "curiosity_gap",
        "stakes_intensity",
        "emotional_voltage",
        "standalone_clarity",
        "thought_completeness",
        "click_through_likelihood",
        "linguistic_compression",
        "novelty_delta",
        "information_density",
    )
    @classmethod
    def clamp_score(cls, v: float) -> float:
        return max(0.0, min(10.0, v))


class AlgorithmDynamics(BaseModel):
    retention_mechanics: str = ""
    watch_time_effect: str = ""
    scroll_interruption: str = ""


class ViewerPsychology(BaseModel):
    primary_trigger: str = ""
    mechanism: str = ""
    tension_created: str = ""


class HookResponse(BaseModel):
    id: str
    rank: int
    hook_text: str
    start_time: str
    end_time: str
    hook_type: str
    funnel_role: str
    cognitive_tension: str = ""
    scores: HookScores
    attention_score: float
    virality_score: float = 0.0
    justification: str = ""
    algorithm_dynamics: AlgorithmDynamics = AlgorithmDynamics()
    viewer_psychology: ViewerPsychology = ViewerPsychology()
    improvement_suggestion: str = ""
    is_composite: bool
    is_selected: bool


class HooksListResponse(BaseModel):
    session_id: str
    status: str
    hooks: list[HookResponse]
    regeneration_count: int
