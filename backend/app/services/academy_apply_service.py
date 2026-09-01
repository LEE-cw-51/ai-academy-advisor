"""enrich-proposals CSV → 정본 JSON 반영 (subjects·URL null 필드만)."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from app.core.subjects import normalize_subjects
from app.schemas.academy import AcademyRecord
from app.services.academy_enrich_service import (
    addresses_match,
    blog_id_relates_to_names,
    is_homepage_url,
    is_official_blog_url,
    names_match,
)

_APPLY_SOURCE_NOTE = (
    "네이버 API HUB 지역·블로그 검색 A3 반영 (category 과목·URL), 2026-09-01"
)
_ROLLBACK_SOURCE_NOTE = "A3 URL 롤백 (잘못 매칭·비홈페이지), 2026-09-01"
_APPLY_VERIFIED_AT = date(2026, 9, 1)

_PROTECTED_FIELDS = frozenset(
    {"address", "latitude", "longitude", "phone", "registration_number", "name"}
)


@dataclass
class ApplyRowResult:
    file_name: str
    action: str  # "applied" | "skipped" | "error"
    detail: str = ""
    changes: list[str] = field(default_factory=list)


@dataclass
class ApplyReport:
    results: list[ApplyRowResult] = field(default_factory=list)

    @property
    def applied(self) -> int:
        return sum(1 for r in self.results if r.action == "applied")

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.action == "skipped")

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.action == "error")


def _parse_subjects(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in text.split("|") if p.strip()]
    if not parts:
        return []
    return normalize_subjects(parts)


def _load_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def apply_enrich_csv(
    csv_path: Path,
    json_dir: Path,
    *,
    confidence: str = "high",
    dry_run: bool = True,
) -> ApplyReport:
    """CSV 제안을 정본 JSON에 반영한다. `confidence` 행만, null 필드만 채운다."""
    report = ApplyReport()
    if not csv_path.is_file():
        report.results.append(
            ApplyRowResult("", "error", detail=f"CSV 없음: {csv_path}")
        )
        return report
    if not json_dir.is_dir():
        report.results.append(
            ApplyRowResult("", "error", detail=f"JSON 디렉터리 없음: {json_dir}")
        )
        return report

    for row in _load_csv_rows(csv_path):
        file_name = (row.get("file_name") or "").strip()
        row_confidence = (row.get("confidence") or "").strip().lower()
        if row_confidence != confidence.lower():
            report.results.append(
                ApplyRowResult(
                    file_name,
                    "skipped",
                    detail=f"confidence={row_confidence!r} (필터: {confidence})",
                )
            )
            continue

        if not file_name:
            report.results.append(
                ApplyRowResult("", "error", detail="file_name 누락")
            )
            continue

        json_path = json_dir / file_name
        if not json_path.is_file():
            report.results.append(
                ApplyRowResult(file_name, "error", detail="JSON 파일 없음")
            )
            continue

        try:
            raw = _read_json(json_path)
            record = AcademyRecord.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            report.results.append(
                ApplyRowResult(file_name, "error", detail=str(exc))
            )
            continue

        try:
            proposed_subjects = _parse_subjects(row.get("proposed_subjects") or "")
        except ValueError as exc:
            report.results.append(
                ApplyRowResult(file_name, "error", detail=str(exc))
            )
            continue
        proposed_website = (row.get("website_url") or "").strip()
        proposed_blog = (row.get("blog_url") or "").strip()
        matched_title = (row.get("matched_local_title") or "").strip()

        if proposed_website and not is_homepage_url(proposed_website):
            proposed_website = ""
        if proposed_blog and not is_official_blog_url(proposed_blog):
            proposed_blog = ""
        if matched_title:
            if proposed_website and not names_match(record.name, matched_title):
                proposed_website = ""
            if proposed_blog and not names_match(record.name, matched_title):
                proposed_blog = ""
        if proposed_blog and not blog_id_relates_to_names(
            record.name, matched_title, proposed_blog
        ):
            proposed_blog = ""

        changes: list[str] = []
        updated = dict(raw)

        if record.subjects is None and proposed_subjects:
            updated["subjects"] = proposed_subjects
            changes.append(f"subjects={proposed_subjects}")

        if record.website_url is None and proposed_website:
            updated["website_url"] = proposed_website
            changes.append(f"website_url={proposed_website}")

        if record.blog_url is None and proposed_blog:
            updated["blog_url"] = proposed_blog
            changes.append(f"blog_url={proposed_blog}")

        if not changes:
            report.results.append(
                ApplyRowResult(file_name, "skipped", detail="채울 null 필드 없음")
            )
            continue

        existing_note = (updated.get("source_note") or "").strip()
        if existing_note and _APPLY_SOURCE_NOTE not in existing_note:
            updated["source_note"] = f"{existing_note}; {_APPLY_SOURCE_NOTE}"
        else:
            updated["source_note"] = existing_note or _APPLY_SOURCE_NOTE
        updated["last_verified_at"] = _APPLY_VERIFIED_AT.isoformat()
        changes.extend(["source_note", "last_verified_at"])

        for protected in _PROTECTED_FIELDS:
            if protected in updated and updated[protected] != raw.get(protected):
                report.results.append(
                    ApplyRowResult(
                        file_name,
                        "error",
                        detail=f"보호 필드 변경 시도: {protected}",
                    )
                )
                break
        else:
            try:
                AcademyRecord.model_validate(updated)
            except ValidationError as exc:
                report.results.append(
                    ApplyRowResult(file_name, "error", detail=str(exc))
                )
                continue

            if not dry_run:
                _write_json(json_path, updated)

            report.results.append(
                ApplyRowResult(file_name, "applied", changes=changes)
            )

    return report


@dataclass
class RollbackRowResult:
    file_name: str
    action: str  # "rolled_back" | "skipped" | "error"
    detail: str = ""
    changes: list[str] = field(default_factory=list)


@dataclass
class RollbackReport:
    results: list[RollbackRowResult] = field(default_factory=list)

    @property
    def rolled_back(self) -> int:
        return sum(1 for r in self.results if r.action == "rolled_back")

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.action == "skipped")

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.action == "error")


def _dong_tokens(value: str) -> set[str]:
    return set(re.findall(r"[\w가-힣]+동", value))


def _blog_evidence_conflicts_address(
    academy_address: str | None, evidence: str
) -> bool:
    if not academy_address or "blog snippets=" not in evidence:
        return False
    blog_part = evidence.split("blog snippets=", 1)[1]
    canonical = _dong_tokens(academy_address)
    if not canonical:
        return False
    mentioned = _dong_tokens(blog_part)
    return bool(mentioned - canonical)


def _should_rollback_website(
    academy_name: str, matched_title: str, website_url: str | None
) -> bool:
    if not website_url:
        return False
    if not is_homepage_url(website_url):
        return True
    return bool(matched_title) and not names_match(academy_name, matched_title)


def _should_rollback_blog(
    academy_name: str,
    matched_title: str,
    blog_url: str | None,
    evidence: str,
    academy_address: str | None = None,
) -> bool:
    if not blog_url:
        return False
    if matched_title and not names_match(academy_name, matched_title):
        return True
    if blog_id_relates_to_names(academy_name, matched_title, blog_url):
        return False
    parent_markers = ("후기", "리뷰", "솔직", "다녀본", "다녀왔", "우리아이", "우리 아이", "학부모")
    if any(marker in evidence for marker in parent_markers):
        return True
    if academy_address and matched_title:
        road = evidence.split("road=", 1)[-1] if "road=" in evidence else ""
        if road and not addresses_match(academy_address, road.split(" | ", 1)[0]):
            return True
    if _blog_evidence_conflicts_address(academy_address, evidence):
        return True
    return False


def rollback_enrich_urls(
    csv_path: Path,
    json_dir: Path,
    *,
    dry_run: bool = True,
) -> RollbackReport:
    """A3로 잘못 반영된 website_url·blog_url(·이름 불일치 subjects)을 null로 되돌린다."""
    report = RollbackReport()
    if not csv_path.is_file():
        report.results.append(
            RollbackRowResult("", "error", detail=f"CSV 없음: {csv_path}")
        )
        return report
    if not json_dir.is_dir():
        report.results.append(
            RollbackRowResult("", "error", detail=f"JSON 디렉터리 없음: {json_dir}")
        )
        return report

    rows_by_file = {
        (row.get("file_name") or "").strip(): row
        for row in _load_csv_rows(csv_path)
        if (row.get("file_name") or "").strip()
    }

    for json_path in sorted(json_dir.glob("*.json")):
        file_name = json_path.name
        try:
            raw = _read_json(json_path)
            record = AcademyRecord.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            report.results.append(
                RollbackRowResult(file_name, "error", detail=str(exc))
            )
            continue

        source_note = (raw.get("source_note") or "").strip()
        if _APPLY_SOURCE_NOTE not in source_note:
            report.results.append(
                RollbackRowResult(file_name, "skipped", detail="A3 반영 아님")
            )
            continue

        row = rows_by_file.get(file_name)
        if row is None:
            report.results.append(
                RollbackRowResult(file_name, "error", detail="CSV 행 없음")
            )
            continue

        matched_title = (row.get("matched_local_title") or "").strip()
        evidence = row.get("evidence") or ""
        rollback_website = _should_rollback_website(
            record.name, matched_title, record.website_url
        )
        rollback_blog = _should_rollback_blog(
            record.name,
            matched_title,
            record.blog_url,
            evidence,
            record.address,
        )
        name_mismatch = bool(matched_title) and not names_match(
            record.name, matched_title
        )
        rollback_subjects = name_mismatch and record.subjects is not None

        if not rollback_website and not rollback_blog and not rollback_subjects:
            report.results.append(
                RollbackRowResult(file_name, "skipped", detail="롤백 대상 없음")
            )
            continue

        changes: list[str] = []
        updated = dict(raw)
        if rollback_website:
            updated["website_url"] = None
            changes.append("website_url=null")
        if rollback_blog:
            updated["blog_url"] = None
            changes.append("blog_url=null")
        if rollback_subjects:
            updated["subjects"] = None
            changes.append("subjects=null")

        existing_note = (updated.get("source_note") or "").strip()
        if _ROLLBACK_SOURCE_NOTE not in existing_note:
            updated["source_note"] = (
                f"{existing_note}; {_ROLLBACK_SOURCE_NOTE}"
                if existing_note
                else _ROLLBACK_SOURCE_NOTE
            )
            changes.append("source_note")

        for protected in _PROTECTED_FIELDS:
            if protected in updated and updated[protected] != raw.get(protected):
                report.results.append(
                    RollbackRowResult(
                        file_name,
                        "error",
                        detail=f"보호 필드 변경 시도: {protected}",
                    )
                )
                break
        else:
            try:
                AcademyRecord.model_validate(updated)
            except ValidationError as exc:
                report.results.append(
                    RollbackRowResult(file_name, "error", detail=str(exc))
                )
                continue

            if not dry_run:
                _write_json(json_path, updated)

            report.results.append(
                RollbackRowResult(file_name, "rolled_back", changes=changes)
            )

    return report
