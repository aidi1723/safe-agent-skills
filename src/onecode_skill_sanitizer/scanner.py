from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    status: str
    summary: str

    def to_json(self) -> dict[str, str]:
        return {
            "id": self.id,
            "severity": self.severity,
            "status": self.status,
            "summary": self.summary,
        }


RULES = [
    (
        "shell-download-execute",
        "critical",
        re.compile(r"\b(curl|wget)\b[^\n|;]*(\||;|&&)\s*(sh|bash)\b", re.IGNORECASE),
        "Found remote download followed by shell execution.",
    ),
    (
        "broad-filesystem-access",
        "high",
        re.compile(r"\b(whole machine|entire machine|all files|credentials|ssh keys?)\b", re.IGNORECASE),
        "Found broad filesystem or credential access guidance.",
    ),
    (
        "policy-bypass",
        "critical",
        re.compile(r"\b(ignore|disable|bypass)\b[^\n]*(sandbox|approval|policy|verification|system instructions)", re.IGNORECASE),
        "Found instruction to bypass policy, sandbox, approval, or verification.",
    ),
    (
        "secret-like-string",
        "high",
        re.compile(r"\b(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}", re.IGNORECASE),
        "Found secret-like credential material.",
    ),
    (
        "privilege-escalation",
        "critical",
        re.compile(r"\b(sudo|su\s+-|chmod\s+-R\s+777|chown\s+-R)\b", re.IGNORECASE),
        "Found privilege escalation or broad permission-changing guidance.",
    ),
    (
        "destructive-shell",
        "critical",
        re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\s+(/|~|\$HOME|/tmp|/var|/usr|\.)?", re.IGNORECASE),
        "Found destructive recursive deletion guidance.",
    ),
    (
        "inline-script-execution",
        "critical",
        re.compile(r"\b(python(?:3)?|node|perl|ruby|bash|sh)\s+(-c|-e)\b", re.IGNORECASE),
        "Found inline interpreter or shell execution guidance.",
    ),
    (
        "encoded-payload-execution",
        "critical",
        re.compile(r"\b(base64|openssl\s+enc)\b[^\n|;]*(\||;|&&)\s*(sh|bash|python(?:3)?|node)\b", re.IGNORECASE),
        "Found encoded payload decoding followed by execution.",
    ),
    (
        "environment-exfiltration",
        "high",
        re.compile(
            r"\b(upload|send|post|exfiltrat\w*)\b[^\n]*(environment variables?|env vars?|env|credentials?|secrets?)"
            r"|\b(printenv|env)\b[^\n|;]*(\||;|&&)\s*(curl|wget)\b",
            re.IGNORECASE,
        ),
        "Found guidance to expose environment variables or credentials.",
    ),
]

SEVERITY_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def read_text_files(source_dir: Path) -> list[tuple[str, str]]:
    files = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files.append((path.relative_to(source_dir).as_posix(), text))
    return files


def source_hash(files: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for relative_path, text in files:
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(text.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def scan_text(text: str) -> list[Finding]:
    normalized_text = normalize_scan_text(text)
    findings = []
    for finding_id, severity, pattern, summary in RULES:
        if pattern.search(normalized_text):
            findings.append(Finding(finding_id, severity, "unresolved", summary))
    return findings


def line_findings(line: str) -> list[Finding]:
    normalized_line = normalize_scan_text(line)
    findings = []
    for finding_id, severity, pattern, summary in RULES:
        if pattern.search(normalized_line):
            findings.append(Finding(finding_id, severity, "removed", summary))
    return findings


def normalize_scan_text(text: str) -> str:
    text = re.sub(r"\\\s*\n\s*", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*([|;&])", r" \1", text)
    text = re.sub(r"([|;&])[ \t]*\n[ \t]*", r"\1 ", text)
    return text


def highest_risk(findings: list[Finding]) -> str:
    if not findings:
        return "low"
    return max((finding.severity for finding in findings), key=lambda item: SEVERITY_ORDER[item])
