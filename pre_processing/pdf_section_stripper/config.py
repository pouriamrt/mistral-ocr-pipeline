from dataclasses import dataclass


@dataclass(frozen=True)
class StripConfig:
    # What to remove
    remove_intro: bool = True
    remove_background: bool = True
    remove_ack: bool = True
    remove_refs: bool = True

    # Safety and heuristics
    keep_first_n_pages_always: int = 1  # title page
    keep_abstract_pages: int = 1  # page after title often has abstract
    max_scan_pages_for_intro: int = 5  # only early pages scanned for intro/methods
    min_heading_score: int = 70  # fuzzy threshold

    # Heading-likeness (layout-based, not regex)
    heading_min_fontsize_ratio: float = 1.1  # heading font / median font
    heading_max_chars: int = 80  # headings are rarely long
    require_methods_to_drop_intro: bool = True
