"""Validated router evaluation suites and independent review evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from . import safe_fs
from .router_eval_v2 import DatasetValidationError, EXPECTED_LABELING, _validate_case


SUITE_CATEGORIES = {
    "normal",
    "multi_intent",
    "ambiguous",
    "negative",
    "multilingual_typo_paraphrase",
    "safety_sensitive",
}
_INDEX_FIELDS = {"schema_version", "suite_id", "labeling", "case_count", "shards"}
_SHARD_FIELDS = {"path", "case_count", "sha256"}
_REVIEW_FIELDS = {
    "schema_version",
    "suite_id",
    "suite_sha256",
    "reviewed_commit",
    "rule_author_id",
    "reviewer_id",
    "reviewer_role",
    "reviewed_at",
    "decision",
    "independence_attestation",
    "reviewed_case_ids",
    "exceptions",
}
_EXCEPTION_FIELDS = {"case_id", "reason"}
_SUITE_IDENTITY_FIELDS = {"suite_id", "suite_sha256", "case_count", "case_ids"}
_SOURCE_IDENTITY_FIELDS = {"reviewed_commit", "rule_author_id"}
_SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
_UTC_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z\Z")
_MISSING_SOURCE_IDENTITY = object()
_GIT_TIMEOUT_SECONDS = 5


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(payload: object) -> str:
    return f"sha256:{hashlib.sha256(_canonical_bytes(payload)).hexdigest()}"


def _exact_nonblank(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and all(not character.isspace() or character == " " for character in value)
    )


def _exact_identifier(value: object) -> bool:
    return type(value) is str and bool(value) and not any(character.isspace() for character in value)


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _safe_relative_path(value: object) -> PurePosixPath:
    if type(value) is not str or not value or "\\" in value:
        raise DatasetValidationError("shard path must be a safe relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        raise DatasetValidationError("shard path must be a safe relative POSIX path")
    return path


def _read_regular_relative(root: Path, relative: PurePosixPath, label: str) -> bytes:
    content = bytearray()
    try:
        with safe_fs.open_root(root) as root_fd:
            assert root_fd is not None
            with ExitStack() as stack:
                parent_fd = root_fd
                for component in relative.parts[:-1]:
                    parent_fd = stack.enter_context(safe_fs.open_directory_at(parent_fd, component))
                safe_fs.visit_regular_file(
                    parent_fd,
                    relative.name,
                    lambda fd: content.extend(b"".join(safe_fs.iter_fd_chunks(fd))),
                )
    except (safe_fs.UnsafeDescriptorAccessError, OSError) as exc:
        raise DatasetValidationError(f"unable to read {label}: {exc}") from exc
    return bytes(content)


def _strict_json_loads(raw: bytes, label: str) -> object:
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise DatasetValidationError(f"duplicate object key in {label}: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise DatasetValidationError(f"nonstandard JSON constant in {label}: {value}")

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except DatasetValidationError:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise DatasetValidationError(f"invalid {label} JSON: {exc}") from exc


def _read_json_path(path: Path, label: str) -> object:
    relative = PurePosixPath(path.name)
    raw = _read_regular_relative(path.parent, relative, label)
    return _strict_json_loads(raw, label)


def _validate_index(payload: object) -> dict[str, Any]:
    if type(payload) is not dict or set(payload) != _INDEX_FIELDS:
        raise DatasetValidationError("suite index has missing or unknown fields")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise DatasetValidationError("suite index schema_version must be 1")
    if not _exact_identifier(payload["suite_id"]):
        raise DatasetValidationError("suite_id must be an exact nonempty string")
    if payload["labeling"] != EXPECTED_LABELING:
        raise DatasetValidationError("suite labeling metadata is invalid")
    if not _positive_int(payload["case_count"]):
        raise DatasetValidationError("suite case_count must be a positive integer")
    shards = payload["shards"]
    if type(shards) is not list or not shards:
        raise DatasetValidationError("suite shards must be a nonempty list")
    normalized_shards = []
    paths: set[str] = set()
    for index, shard in enumerate(shards):
        if type(shard) is not dict or set(shard) != _SHARD_FIELDS:
            raise DatasetValidationError(f"shards[{index}] has missing or unknown fields")
        relative = _safe_relative_path(shard["path"])
        if shard["path"] in paths:
            raise DatasetValidationError(f"duplicate shard path: {shard['path']}")
        paths.add(shard["path"])
        if not _positive_int(shard["case_count"]):
            raise DatasetValidationError(f"shards[{index}].case_count must be a positive integer")
        if type(shard["sha256"]) is not str or _SHA256_PATTERN.fullmatch(shard["sha256"]) is None:
            raise DatasetValidationError(f"shards[{index}].sha256 is invalid")
        normalized_shards.append({**shard, "_relative": relative})
    return {**payload, "shards": normalized_shards}


def _load_suite(index_path: Path, known_scenarios: set[str] | None) -> dict[str, Any]:
    index = _validate_index(_read_json_path(index_path, "suite index"))
    cases: list[dict[str, Any]] = []
    canonical_shards = []
    for shard_index, descriptor in enumerate(index["shards"]):
        raw = _read_regular_relative(index_path.parent, descriptor["_relative"], "suite shard")
        payload = _strict_json_loads(raw, f"suite shard {descriptor['path']}")
        if type(payload) is not dict or set(payload) != {"cases"} or type(payload["cases"]) is not list:
            raise DatasetValidationError(f"shards[{shard_index}] must contain only a cases list")
        actual_hash = _digest(payload)
        if actual_hash != descriptor["sha256"]:
            raise DatasetValidationError(f"shards[{shard_index}] hash mismatch")
        validated = [
            _validate_case(
                item,
                len(cases) + offset,
                known_scenarios,
                allowed_categories=SUITE_CATEGORIES,
            )
            for offset, item in enumerate(payload["cases"])
        ]
        if any(not _exact_identifier(item["id"]) for item in validated):
            raise DatasetValidationError(f"shards[{shard_index}] case ids must be exact identifiers")
        if len(validated) != descriptor["case_count"]:
            raise DatasetValidationError(f"shards[{shard_index}] case count mismatch")
        cases.extend(validated)
        canonical_shards.append(
            {
                "path": descriptor["path"],
                "case_count": descriptor["case_count"],
                "sha256": descriptor["sha256"],
                "content": payload,
            }
        )
    if len(cases) != index["case_count"]:
        raise DatasetValidationError("suite case count mismatch")
    case_ids = [item["id"] for item in cases]
    duplicates = sorted(case_id for case_id, count in Counter(case_ids).items() if count > 1)
    if duplicates:
        raise DatasetValidationError(f"duplicate case ids: {', '.join(duplicates)}")
    canonical_index = {
        key: value
        for key, value in index.items()
        if key != "shards"
    }
    canonical_index["shards"] = [
        {key: value for key, value in shard.items() if key != "_relative"}
        for shard in index["shards"]
    ]
    suite_sha256 = _digest({"index": canonical_index, "shards": canonical_shards})
    dataset_sha256 = _digest({"labeling": index["labeling"], "cases": cases})
    gate_identity = {
        "case_count": len(cases),
        "dataset_sha256": dataset_sha256,
        "labeling_generated_from_router": index["labeling"]["generated_from_router"],
        "labeling_method": index["labeling"]["method"],
        "labeling_reviewed_at": index["labeling"]["reviewed_at"],
        "labeling_reviewer_role": index["labeling"]["reviewer_role"],
        "suite_id": index["suite_id"],
        "suite_sha256": suite_sha256,
    }
    return {
        "cases": cases,
        "identity": gate_identity,
        "suite_identity": {
            "suite_id": index["suite_id"],
            "suite_sha256": suite_sha256,
            "case_count": len(cases),
            "case_ids": case_ids,
        },
    }


def load_eval_suite(index_path: Path, known_scenarios: set[str] | None = None) -> dict[str, Any]:
    """Load a suite in declared shard order and authenticate every case."""

    return _load_suite(index_path, known_scenarios)


def canonical_suite_sha256(index_path: Path) -> str:
    """Return the canonical identity of a validated suite and ordered shards."""

    return _load_suite(index_path, None)["identity"]["suite_sha256"]


def _valid_utc_timestamp(value: object) -> bool:
    if type(value) is not str or _UTC_PATTERN.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True


def _validate_suite_identity(identity: object) -> dict[str, Any]:
    if type(identity) is not dict or set(identity) != _SUITE_IDENTITY_FIELDS:
        raise DatasetValidationError("suite identity has missing or unknown fields")
    case_ids = identity["case_ids"]
    if (
        not _exact_identifier(identity["suite_id"])
        or type(identity["suite_sha256"]) is not str
        or _SHA256_PATTERN.fullmatch(identity["suite_sha256"]) is None
        or not _positive_int(identity["case_count"])
        or type(case_ids) is not list
        or len(case_ids) != identity["case_count"]
        or not all(_exact_identifier(case_id) for case_id in case_ids)
        or len(case_ids) != len(set(case_ids))
    ):
        raise DatasetValidationError("suite identity is invalid")
    return identity


def _validate_source_identity(identity: object) -> dict[str, str]:
    if type(identity) is not dict or set(identity) != _SOURCE_IDENTITY_FIELDS:
        raise DatasetValidationError("router source identity has missing or unknown fields")
    if (
        type(identity["reviewed_commit"]) is not str
        or _COMMIT_PATTERN.fullmatch(identity["reviewed_commit"]) is None
        or identity["reviewed_commit"] == "0" * 40
        or not _exact_identifier(identity["rule_author_id"])
    ):
        raise DatasetValidationError("router source identity is invalid")
    return dict(identity)


def _run_git(repository: Path, *arguments: str) -> str:
    command = ["git", "-C", str(repository), *arguments]
    try:
        completed = subprocess.run(
            command,
            shell=False,
            capture_output=True,
            text=True,
            check=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise DatasetValidationError(f"unable to validate router source identity: {exc}") from exc
    return completed.stdout


def load_router_source_identity(repository: Path) -> dict[str, str]:
    """Bind review evidence to a clean tracked Git HEAD and its author email."""

    commit = _run_git(repository, "rev-parse", "--verify", "HEAD^{commit}").strip()
    if _COMMIT_PATTERN.fullmatch(commit) is None or commit == "0" * 40:
        raise DatasetValidationError("router source HEAD is invalid")
    tracked_status = _run_git(repository, "status", "--porcelain=v1", "--untracked-files=no")
    if tracked_status:
        raise DatasetValidationError("router source has tracked worktree changes")
    author_id = _run_git(repository, "show", "-s", "--format=%ae", commit).strip()
    if not _exact_identifier(author_id):
        raise DatasetValidationError("router source commit author is invalid")
    finished_commit = _run_git(repository, "rev-parse", "--verify", "HEAD^{commit}").strip()
    finished_status = _run_git(repository, "status", "--porcelain=v1", "--untracked-files=no")
    if finished_commit != commit or finished_status:
        raise DatasetValidationError("router source changed during identity validation")
    return _validate_source_identity(
        {"reviewed_commit": commit, "rule_author_id": author_id}
    )


def load_review_record(
    review_path: Path,
    suite_identity: object,
    expected_source_identity: object = _MISSING_SOURCE_IDENTITY,
) -> dict[str, object]:
    """Authenticate accepted independent review evidence for one exact suite."""

    suite_identity = _validate_suite_identity(suite_identity)
    payload = _read_json_path(review_path, "review record")
    if type(payload) is not dict or set(payload) != _REVIEW_FIELDS:
        raise DatasetValidationError("review record has missing or unknown fields")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise DatasetValidationError("review schema_version must be 1")
    exact_strings = ("suite_id", "rule_author_id", "reviewer_id")
    if any(not _exact_identifier(payload[field]) for field in exact_strings):
        raise DatasetValidationError("review identifiers must be exact nonempty strings")
    if (
        payload["suite_id"] != suite_identity.get("suite_id")
        or payload["suite_sha256"] != suite_identity.get("suite_sha256")
    ):
        raise DatasetValidationError("review does not authenticate the current suite")
    if type(payload["suite_sha256"]) is not str or _SHA256_PATTERN.fullmatch(payload["suite_sha256"]) is None:
        raise DatasetValidationError("review suite_sha256 is invalid")
    if type(payload["reviewed_commit"]) is not str or _COMMIT_PATTERN.fullmatch(payload["reviewed_commit"]) is None:
        raise DatasetValidationError("reviewed_commit must be a lowercase 40-character commit")
    if payload["reviewer_id"] == payload["rule_author_id"]:
        raise DatasetValidationError("reviewer must be independent from the rule author")
    if expected_source_identity is not _MISSING_SOURCE_IDENTITY:
        source_identity = _validate_source_identity(expected_source_identity)
        if (
            payload["reviewed_commit"] != source_identity["reviewed_commit"]
            or payload["rule_author_id"] != source_identity["rule_author_id"]
        ):
            raise DatasetValidationError("review does not authenticate the evaluated router source")
    if payload["reviewer_role"] != "independent_dataset_review":
        raise DatasetValidationError("reviewer_role is invalid")
    if not _valid_utc_timestamp(payload["reviewed_at"]):
        raise DatasetValidationError("reviewed_at must be a valid UTC timestamp")
    if payload["decision"] != "accepted":
        raise DatasetValidationError("review decision must be accepted")
    if payload["independence_attestation"] is not True:
        raise DatasetValidationError("independence_attestation must be true")
    reviewed_ids = payload["reviewed_case_ids"]
    expected_ids = suite_identity.get("case_ids")
    if (
        type(expected_ids) is not list
        or type(reviewed_ids) is not list
        or not all(_exact_identifier(item) for item in reviewed_ids)
    ):
        raise DatasetValidationError("reviewed_case_ids are invalid")
    if len(reviewed_ids) != len(set(reviewed_ids)):
        raise DatasetValidationError("reviewed_case_ids must not contain duplicates")
    if set(reviewed_ids) != set(expected_ids) or len(reviewed_ids) != suite_identity.get("case_count"):
        raise DatasetValidationError("reviewed_case_ids must exactly cover the suite")
    exceptions = payload["exceptions"]
    if type(exceptions) is not list:
        raise DatasetValidationError("exceptions must be a list")
    exception_ids: set[str] = set()
    for index, exception in enumerate(exceptions):
        if type(exception) is not dict or set(exception) != _EXCEPTION_FIELDS:
            raise DatasetValidationError(f"exceptions[{index}] is invalid")
        if (
            not _exact_identifier(exception["case_id"])
            or exception["case_id"] not in set(expected_ids)
            or not _exact_nonblank(exception["reason"])
        ):
            raise DatasetValidationError(f"exceptions[{index}] is invalid")
        if exception["case_id"] in exception_ids:
            raise DatasetValidationError("exceptions must not repeat case IDs")
        exception_ids.add(exception["case_id"])
    return {
        "suite_id": payload["suite_id"],
        "suite_sha256": payload["suite_sha256"],
        "reviewed_commit": payload["reviewed_commit"],
        "rule_author_id": payload["rule_author_id"],
        "reviewer_id": payload["reviewer_id"],
        "reviewer_role": payload["reviewer_role"],
        "reviewed_at": payload["reviewed_at"],
        "decision": payload["decision"],
        "independence_attestation": payload["independence_attestation"],
        "reviewed_case_count": len(reviewed_ids),
        "exceptions_count": len(exceptions),
    }
