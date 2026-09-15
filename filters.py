from dataclasses import dataclass, field

from config import Settings
from parser import ParsedJob, _normalize_location


@dataclass
class FilterResult:
    matched: bool
    matched_via: list[str] = field(default_factory=list)


def _any_in(haystack: list[str], needles: list[str]) -> bool:
    if not needles:
        return True
    if not haystack:
        return False
    return any(item in haystack for item in needles)


def _location_matches(job_location: str | None, allowed: list[str]) -> bool:
    if not allowed:
        return True
    if not job_location:
        return False
    loc = _normalize_location(job_location)
    return any(_normalize_location(part) in loc or loc in _normalize_location(part) for part in allowed)


def job_matches_filters(job: ParsedJob, settings: Settings) -> FilterResult:
    role_ok = _any_in(job.roles, settings.filter_roles)
    mode_ok = _any_in(job.work_modes, settings.filter_work_modes)
    loc_ok = _location_matches(job.location, settings.filter_locations)

    matched_via: list[str] = []
    if role_ok and settings.filter_roles:
        matched_via.append("intern")
    if mode_ok and settings.filter_work_modes:
        matched_via.append("remote")

    has_role_filter = bool(settings.filter_roles)
    has_mode_filter = bool(settings.filter_work_modes)

    if has_role_filter and has_mode_filter:
        core_match = role_ok or mode_ok
    elif has_role_filter:
        core_match = role_ok
    elif has_mode_filter:
        core_match = mode_ok
    else:
        core_match = True

    matched = core_match and loc_ok
    return FilterResult(matched=matched, matched_via=matched_via if matched else [])
