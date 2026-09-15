import re
from dataclasses import dataclass, field
from enum import Enum


class ApplyType(str, Enum):
    EMAIL = "email"
    WEBSITE = "website"
    DOCS = "docs"
    UNKNOWN = "unknown"


ROLE_KEYWORDS: dict[str, list[str]] = {
    "software": ["software", "sde", "swe", "full stack", "fullstack", "backend", "frontend", "developer", "engineer"],
    "devops": ["devops", "sre", "platform", "cloud", "infrastructure", "kubernetes", "k8s"],
    "analyst": ["analyst", "data analyst", "business analyst", "ba ", "bi "],
    "intern": ["intern", "internship", "trainee", "fresher", "graduate", "entry level", "entry-level"],
    "qa": ["qa", "quality", "test engineer", "sdet"],
    "product": ["product manager", "pm ", "product owner"],
    "design": ["designer", "ui/ux", "ux ", "ui "],
    "ml": ["machine learning", "ml ", "ai ", "data science", "data scientist"],
}

WORK_MODE_KEYWORDS: dict[str, list[str]] = {
    "remote": ["remote", "wfh", "work from home", "work-from-home"],
    "onsite": ["onsite", "on-site", "on site", "office based", "in-office", "in office"],
    "hybrid": ["hybrid"],
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
DOCS_HOSTS = ("docs.google.com", "drive.google.com", "forms.gle", "forms.google.com")
LOCATION_RE = re.compile(
    r"(?:location|based in|office at|city)\s*[:\-]?\s*([A-Za-z][A-Za-z\s,]{1,40})",
    re.IGNORECASE,
)
STRUCTURED_FIELD_RE = re.compile(
    r"^\s*(Company|Role|Batch|Stipend|Location)\s*[-:]\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class ParsedJob:
    raw_text: str
    company: str | None = None
    role: str | None = None
    batch: str | None = None
    stipend: str | None = None
    roles: list[str] = field(default_factory=list)
    work_modes: list[str] = field(default_factory=list)
    location: str | None = None
    emails: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    apply_type: ApplyType = ApplyType.UNKNOWN
    title_hint: str | None = None

    @property
    def primary_contact(self) -> str | None:
        if self.emails:
            return self.emails[0]
        if self.urls:
            return self.urls[0]
        return None


def _match_keywords(text: str, mapping: dict[str, list[str]]) -> list[str]:
    lowered = text.lower()
    found = []
    for label, keywords in mapping.items():
        if any(kw in lowered for kw in keywords):
            found.append(label)
    return found


def _classify_urls(urls: list[str]) -> ApplyType:
    if not urls:
        return ApplyType.UNKNOWN
    for url in urls:
        host = url.lower()
        if any(host_part in host for host_part in DOCS_HOSTS):
            return ApplyType.DOCS
    return ApplyType.WEBSITE


def _extract_title_hint(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    first = lines[0]
    if len(first) > 120:
        return first[:120] + "..."
    return first


def _extract_structured_fields(text: str) -> dict[str, str]:
    return {
        match.group(1).lower(): match.group(2).strip()
        for match in STRUCTURED_FIELD_RE.finditer(text)
    }


LOCATION_ALIASES = {
    "banglore": "bangalore",
    "bengaluru": "bangalore",
    "gurugram": "gurgaon",
}


def _normalize_location(value: str) -> str:
    return LOCATION_ALIASES.get(value.lower().strip(), value.lower().strip())


def _work_modes_from_location(location_value: str) -> list[str]:
    lowered = location_value.lower().strip()
    if "hybrid" in lowered:
        return ["hybrid"]
    if any(word in lowered for word in ("remote", "wfh", "work from home", "work-from-home")):
        return ["remote"]
    # City name (Bangalore, Banglore, Pune, ...) = onsite
    return ["onsite"]


def _build_title_hint(company: str | None, role: str | None, text: str) -> str | None:
    if role and company:
        return f"{role} @ {company}"
    if role:
        return role
    if company:
        return company
    return _extract_title_hint(text)


def parse_job_message(text: str) -> ParsedJob:
    fields = _extract_structured_fields(text)
    company = fields.get("company")
    role = fields.get("role")
    batch = fields.get("batch")
    stipend = fields.get("stipend")
    location_field = fields.get("location")

    emails = list(dict.fromkeys(EMAIL_RE.findall(text)))
    urls = list(dict.fromkeys(URL_RE.findall(text)))
    apply_type = ApplyType.EMAIL if emails else _classify_urls(urls)

    # Classify role from the Role line only — avoids "DevOps" in skills matching devops
    role_source = role if role else text
    roles = _match_keywords(role_source, ROLE_KEYWORDS)

    if location_field:
        location = location_field
        work_modes = _work_modes_from_location(location_field)
    else:
        work_modes = _match_keywords(text, WORK_MODE_KEYWORDS)
        location_match = LOCATION_RE.search(text)
        location = location_match.group(1).strip().rstrip(",.") if location_match else None

    return ParsedJob(
        raw_text=text,
        company=company,
        role=role,
        batch=batch,
        stipend=stipend,
        roles=roles,
        work_modes=work_modes,
        location=location,
        emails=emails,
        urls=urls,
        apply_type=apply_type,
        title_hint=_build_title_hint(company, role, text),
    )
