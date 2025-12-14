from dataclasses import dataclass
from typing import Optional, Dict, List
import fitz


@dataclass
class FoundHeading:
    page: int
    y0: float
    y1: float
    text: str
    kind: str  # "intro" | "methods" | "ack" | "refs"
    score: int


@dataclass
class SectionCuts:
    intro_start: Optional[int] = None
    methods_start: Optional[int] = None
    ack_start: Optional[int] = None
    refs_start: Optional[int] = None

    intro_heading: Optional[FoundHeading] = None
    ack_heading: Optional[FoundHeading] = None
    refs_heading: Optional[FoundHeading] = None


@dataclass
class Plan:
    keep_pages: List[int]
    # redactions in original page coordinates
    redactions: Dict[int, List[fitz.Rect]]
    cuts: SectionCuts
