from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Segment(str, Enum):
    UNBANKED = "unbanked"
    RECENTLY_BANKED = "recently_banked"
    VULNERABLE = "vulnerable"
    FUNCTIONAL = "functional"


class Avatar(BaseModel):
    name: str
    image_url: str


class Features(BaseModel):
    total_debt: float
    consumo_ratio: float
    past_due_ratio: float
    num_institutions: int
    num_refinancings: int
    has_mortgage: bool
    carga_financiera_pct: float
    dominant_signal: str


class Recommendation(BaseModel):
    id: str
    title: str
    trigger: str
    action: str
    priority: int
    explanation_short: Optional[str] = None
    articulos_referencia: Optional[list[str]] = None


class IngestResult(BaseModel):
    anon_id: str
    avatar: Avatar
    segment: Segment
    features: Features
    recommendations: list[Recommendation]
