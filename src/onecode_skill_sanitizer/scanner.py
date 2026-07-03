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
    (
        "dynamic-code-execution",
        "critical",
        re.compile(r"\b(eval|exec)\s*\(\s*(compile|__import__|\w+\()", re.IGNORECASE),
        "Found dynamic code execution through eval or exec.",
    ),
    (
        "chinese-secret-exfiltration",
        "high",
        re.compile(r"(密钥|凭证|令牌|token|密码)[^\n]*(发到|发送到|传到|上传到|发给|发送给)[^\n]*(服务器|接口|网址|webhook)", re.IGNORECASE),
        "Found Chinese-language guidance to send secrets or credentials to an external destination.",
    ),
    (
        "ssh-key-exfiltration",
        "critical",
        re.compile(r"\bscp\b[^\n]*(~/\.ssh/id_rsa|/\.ssh/id_rsa|\bid_rsa\b|ssh keys?|credentials?|secrets?)", re.IGNORECASE),
        "Found SSH key or credential copy through scp.",
    ),
    (
        "netcat-shell",
        "critical",
        re.compile(r"\b(nc|netcat)\b[^\n]*\s-e\s+(?:/bin/)?(?:sh|bash)\b", re.IGNORECASE),
        "Found netcat shell execution guidance.",
    ),
    (
        "powershell-encoded-command",
        "critical",
        re.compile(r"\b(?:powershell|pwsh)\b[^\n]*(?:-EncodedCommand|-enc)\b", re.IGNORECASE),
        "Found PowerShell encoded command execution guidance.",
    ),
    (
        "javascript-fetch-eval",
        "critical",
        re.compile(r"\bfetch\s*\([^\n]{0,300}\)[^\n]{0,500}\b(?:eval|Function)\s*\(", re.IGNORECASE),
        "Found JavaScript fetch followed by dynamic code execution.",
    ),
]

PROTECTIVE_SENSITIVE_BOUNDARY_PATTERN = re.compile(
    r"^\s*(?:\d+\.\s*)?"
    r"(remove|redact|check|review|avoid|exclude|minimi[sz]e|prevent|do not|don't|never|block|stop|flag|require)\b",
    re.IGNORECASE,
)

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
    findings.extend(structural_findings(normalized_text, "unresolved"))
    return dedupe_findings(findings)


def structural_findings(text: str, status: str) -> list[Finding]:
    findings = []
    rm_variables = {
        match.group("name")
        for match in re.finditer(
            r"(?m)^\s*(?:export\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*['\"]?rm['\"]?\s*$",
            text,
        )
    }
    for name in rm_variables:
        if re.search(rf"\${{{re.escape(name)}}}|\${re.escape(name)}", text) and re.search(
            rf"(?:\${{{re.escape(name)}}}|\${re.escape(name)})\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\s+(/|~|\$HOME|/tmp|/var|/usr|\.)?",
            text,
            re.IGNORECASE,
        ):
            findings.append(
                Finding(
                    "indirect-destructive-shell",
                    "critical",
                    status,
                    "Found variable-indirected destructive recursive deletion guidance.",
                )
            )
            break

    downloaded_paths = {
        match.group("path").strip("'\".,;:)")
        for match in re.finditer(
            r"\b(?:curl|wget)\b[^\n;|&]*(?:-o|-O|--output-document)\s+(?P<path>\S+)",
            text,
            re.IGNORECASE,
        )
    }
    for path in downloaded_paths:
        escaped_path = re.escape(path)
        if re.search(rf"\b(?:sh|bash|python(?:3)?|node)\b\s+{escaped_path}\b", text, re.IGNORECASE):
            findings.append(
                Finding(
                    "staged-download-execution",
                    "critical",
                    status,
                    "Found downloaded file later executed by an interpreter or shell.",
                )
            )
            break

    if re.search(r"\b(?:python(?:3)?|node|perl|ruby|bash|sh)\b\s*<<\s*['\"]?\w+", text, re.IGNORECASE):
        findings.append(
            Finding(
                "heredoc-interpreter-execution",
                "critical",
                status,
                "Found heredoc content passed to an interpreter or shell.",
            )
        )
    return findings


def line_findings(line: str) -> list[Finding]:
    normalized_line = normalize_scan_text(line)
    findings = []
    for finding_id, severity, pattern, summary in RULES:
        if finding_id == "broad-filesystem-access" and PROTECTIVE_SENSITIVE_BOUNDARY_PATTERN.search(normalized_line):
            continue
        if pattern.search(normalized_line):
            findings.append(Finding(finding_id, severity, "removed", summary))
    findings.extend(structural_findings(normalized_line, "removed"))
    return dedupe_findings(findings)


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen = set()
    deduped = []
    for finding in findings:
        if finding.id in seen:
            continue
        seen.add(finding.id)
        deduped.append(finding)
    return deduped


def normalize_scan_text(text: str) -> str:
    text = re.sub(r"\\\s*\n\s*", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*([|;&])", r" \1", text)
    text = re.sub(r"([|;&])[ \t]*\n[ \t]*", r"\1 ", text)
    return text


def highest_risk(findings: list[Finding]) -> str:
    if not findings:
        return "low"
    return max((finding.severity for finding in findings), key=lambda item: SEVERITY_ORDER[item])
