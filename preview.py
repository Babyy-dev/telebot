"""Test parsing on sample referral messages without Telegram."""

import sys

from config import Settings
from drafts import build_alert_message
from filters import job_matches_filters
from parser import parse_job_message

INTERN_SAMPLE = """
🚨 Referral Alert 🚨

Company - Ecoavenstra
Role - Junior Software Engineer Intern
Batch - 2025/2026/2027
Stipend - 25,000/month
Location - Remote

How to Apply:
Share CV/Resumes to hr@ecoavenstra.com
"""

TRAINEE_SAMPLE = """
🚨 Referral Alert 🚨

Company - Roxiler Systems
Role - Full-Stack Developer - Trainee
Batch - 2026/2027
Stipend - 25,000 - 30,000/ month
Location - Pune

How to Apply:
Fill form: https://forms.gle/example123
"""

REMOTE_SENIOR_SAMPLE = """
🚨 Referral Alert 🚨

Company - BigTech
Role - Senior Software Engineer
Batch - 2020/2021
Stipend - 25 LPA
Location - Remote

Apply: careers@bigtech.com
"""

BANGALORE_SAMPLE = """
🚨 Referral Alert 🚨

Company - Ecoavenstra
Role - Junior Software Engineer Intern
Batch - 2025/2026/2027
Location: banglore

How to Apply:
Share CV/Resumes to hr@ecoavenstra.com
"""

ONSITE_SENIOR_SAMPLE = """
🚨 Referral Alert 🚨

Company - BigTech
Role - Senior Software Engineer
Batch - 2020/2021
Stipend - 25 LPA
Location: Bangalore

Apply: careers@bigtech.com
"""

SETTINGS = Settings(
    api_id=1,
    api_hash="x",
    monitor_channels=[],
    alert_chat_id=1,
    whatsapp_phone=None,
    callmebot_api_key=None,
    filter_roles=["intern"],
    filter_work_modes=["remote"],
    filter_locations=[],
)


def test_sample(name: str, text: str) -> None:
    job = parse_job_message(text)
    result = job_matches_filters(job, SETTINGS)

    print(f"=== {name} ===")
    print(f"Role:        {job.role}")
    print(f"Location:    {job.location}")
    print(f"Tags:        roles={job.roles}, modes={job.work_modes}")
    print(f"Notify?      {result.matched} ({', '.join(result.matched_via) or 'skip'})")
    print()


def main() -> None:
    text = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    if not text:
        test_sample("Remote intern", INTERN_SAMPLE)
        test_sample("Onsite trainee (Pune)", TRAINEE_SAMPLE)
        test_sample("Location: banglore intern", BANGALORE_SAMPLE)
        test_sample("Remote senior", REMOTE_SENIOR_SAMPLE)
        test_sample("Onsite senior (skip)", ONSITE_SENIOR_SAMPLE)

        print("=== Alert preview ===")
        job = parse_job_message(REMOTE_SENIOR_SAMPLE)
        result = job_matches_filters(job, SETTINGS)
        print(build_alert_message(job, result.matched_via))
        return

    job = parse_job_message(text)
    result = job_matches_filters(job, SETTINGS)
    print(f"Notify: {result.matched} ({', '.join(result.matched_via)})")
    if result.matched:
        print(build_alert_message(job, result.matched_via))


if __name__ == "__main__":
    main()
