from parser import ApplyType, ParsedJob


def build_email_draft(job: ParsedJob, your_name: str = "Your Name") -> str:
    role_label = job.role or job.title_hint or "the intern role"
    company = job.company or "your company"
    subject = f"Application for {role_label} - {company}"
    body = f"""Subject: {subject}

Hi,

I came across the referral for {role_label} at {company} and would like to apply.

I am eligible for batch {job.batch or 'N/A'} and have attached my resume for your review.

Best regards,
{your_name}
"""
    return body.strip()


def _alert_header(matched_via: list[str]) -> str:
    if "intern" in matched_via and "remote" in matched_via:
        return "🚨 INTERN + REMOTE — APPLY FAST 🚨"
    if "intern" in matched_via:
        return "🚨 INTERN JOB — APPLY FAST 🚨"
    if "remote" in matched_via:
        return "🌐 REMOTE JOB — APPLY FAST 🚨"
    return "🔔 JOB MATCH — APPLY FAST 🚨"


def build_alert_message(
    job: ParsedJob,
    matched_via: list[str],
    your_name: str = "Your Name",
) -> str:
    lines = [
        _alert_header(matched_via),
        "",
        f"🏢 Company: {job.company or '—'}",
        f"💼 Role: {job.role or job.title_hint or '—'}",
    ]

    if job.batch:
        lines.append(f"🎓 Batch: {job.batch}")
    if job.stipend:
        lines.append(f"💰 Stipend: {job.stipend}")
    if job.location:
        lines.append(f"📍 Location: {job.location}")
    if job.work_modes:
        lines.append(f"🌐 Mode: {', '.join(job.work_modes)}")

    lines.append("")

    if job.apply_type == ApplyType.EMAIL and job.emails:
        lines.append(f"📧 Send CV to: {job.emails[0]}")
        lines.append("")
        lines.append("── Email draft (copy & send) ──")
        lines.append(build_email_draft(job, your_name=your_name))

    elif job.apply_type == ApplyType.DOCS:
        lines.append("📄 Apply via Google Doc / Form:")
        for url in job.urls[:3]:
            lines.append(url)
        lines.append("")
        lines.append("⏰ Open the link and apply now.")

    elif job.apply_type == ApplyType.WEBSITE and job.urls:
        lines.append("🔗 Apply on website:")
        for url in job.urls[:3]:
            lines.append(url)
        lines.append("")
        lines.append("⏰ Fill the form and apply now.")

    else:
        lines.append("⚠️ No email/link found — check original message below.")

    lines.append("")
    lines.append("── Original post ──")
    preview = job.raw_text[:600]
    if len(job.raw_text) > 600:
        preview += "..."
    lines.append(preview)

    return "\n".join(lines)
