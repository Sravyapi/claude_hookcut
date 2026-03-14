# -*- coding: utf-8 -*-
"""Pluggable evaluation config - swap for different markets/languages."""

from dataclasses import dataclass, field
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
TRANSCRIPTS_DIR = EVAL_DIR / "transcripts"
DB_PATH = EVAL_DIR / "eval.db"

BATCH_SIZE_PCT = 10  # review 10% at a time


@dataclass
class NicheTier:
    tier: int
    num_creators: int
    videos_per_creator: int
    best_videos: int
    mid_videos: int
    recent_videos: int


@dataclass
class EvalConfig:
    name: str = "English Indian Creators — Indian Audience"
    creator_country: str = "India"
    audience_country: str = "India"
    content_language: str = "English"
    train_ratio: float = 0.8
    niches: dict[str, NicheTier] = field(default_factory=lambda: {
        "Finance": NicheTier(1, 10, 10, 5, 3, 2),
        "Tech / AI": NicheTier(1, 10, 10, 5, 3, 2),
        "Entrepreneurship": NicheTier(1, 10, 10, 5, 3, 2),
        "Education": NicheTier(1, 10, 10, 5, 3, 2),
        "Podcast": NicheTier(1, 10, 10, 5, 3, 2),
        "Fitness": NicheTier(2, 5, 5, 3, 1, 1),
        "Drama / Commentary": NicheTier(2, 5, 5, 3, 1, 1),
    })

    @property
    def total_videos(self) -> int:
        return sum(n.num_creators * n.videos_per_creator for n in self.niches.values())

    @property
    def train_count(self) -> int:
        return int(self.total_videos * self.train_ratio)

    @property
    def test_count(self) -> int:
        return self.total_videos - self.train_count


DEFAULT_CONFIG = EvalConfig()
