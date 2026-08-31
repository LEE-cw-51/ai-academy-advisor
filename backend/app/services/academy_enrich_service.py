"""검색 결과에서 학원 과목·URL **제안**을 만든다. JSON 정본은 쓰지 않는다."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pydantic import ValidationError

from app.core.subjects import extract_subjects_from_text, normalize_subjects, subjects_csv
from app.providers.base import LocalPlace, LocalSearchProvider, ReviewItem, ReviewSource
from app.providers.naver_review import clean_text
from app.schemas.academy import AcademyRecord

_QUERY_REGION = "하남 미사"
_PLACE_HOST_MARKERS = (
    "map.naver.com",
    "naver.me",
    "search.naver.com",
    "place.naver.com",
    "pcmap.place.naver.com",
)
_CAFE_HOST_MARKERS = ("cafe.naver.com", "m.cafe.naver.com")


@dataclass
class EnrichProposal:
    file_name: str
    name: str
    address: str
    proposed_subjects: list[str]
    website_url: str
    blog_url: str
    confidence: str
    evidence: str
    source_note: str
    matched_local_title: str = ""

    def as_csv_row(self) -> dict[str, str]:
        return {
            "name": self.name,
            "address": self.address,
            "proposed_subjects": subjects_csv(self.proposed_subjects),
            "website_url": self.website_url,
            "blog_url": self.blog_url,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "source_note": self.source_note,
            "file_name": self.file_name,
            "matched_local_title": self.matched_local_title,
        }


@dataclass
class EnrichReport:
    proposals: list[EnrichProposal] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def load_academy_records(directory: Path) -> list[tuple[Path, AcademyRecord]]:
    """정본 JSON을 읽는다. 손상된 파일은 건너뛰고 stderr에 경고한다.

    `academy_import_service.load_records`와 일부러 별개다 — 저건 DB 임포트용이라
    SQLAlchemy/`app.models`를 끌고 오는데, 이 CLI 도구는 DB 없이 돈다.
    """
    pairs: list[tuple[Path, AcademyRecord]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            record = AcademyRecord.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            print(f"WARN: {path.name}: 건너뜀 — {exc}", file=sys.stderr)
            continue
        pairs.append((path, record))
    return pairs


def _addr_key(value: str) -> str:
    compact = re.sub(r"\s+", "", value)
    for token in ("대한민국", "경기도", "하남시", "경기"):
        compact = compact.replace(token, "")
    return re.split(r"[,，(（]", compact, maxsplit=1)[0]


def addresses_match(canonical: str | None, candidate: str) -> bool:
    if not canonical or not candidate:
        return False
    left = _addr_key(canonical)
    right = _addr_key(candidate)
    if len(left) < 6 or len(right) < 6:
        return False
    return left in right or right in left


def names_match(academy_name: str, title: str) -> bool:
    stem = re.sub(r"학원$", "", academy_name).strip().replace(" ", "")
    if len(stem) < 2:
        return False
    return stem in title.replace(" ", "")


def is_homepage_url(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    if any(marker in lowered for marker in _PLACE_HOST_MARKERS):
        return False
    if "blog.naver.com" in lowered:
        return False
    if any(marker in lowered for marker in _CAFE_HOST_MARKERS):
        return False
    host = urlparse(url).netloc.lower()
    if not host:
        return False
    return url.startswith("http://") or url.startswith("https://")


def _naver_blog_id(url: str) -> str:
    """blog.naver.com URL에서 블로그 id를 뽑는다. 아니면 빈 문자열.

    글 단위 링크(`/{id}/{postNo}`)와 레거시 `PostView.nhn?blogId=...` 링크,
    블로그 홈(`/{id}`) 모두에서 같은 id를 얻어야 pick_blog_url이 홈 URL로
    정규화할 수 있다.
    """
    parsed = urlparse(url)
    if "blog.naver.com" not in parsed.netloc.lower():
        return ""
    parts = [p for p in parsed.path.split("/") if p]
    if parts and parts[0].lower() != "postview.nhn":
        return parts[0]
    return parse_qs(parsed.query).get("blogId", [""])[0]


def is_official_blog_url(url: str) -> bool:
    if not url:
        return False
    blog_id = _naver_blog_id(url)
    if not blog_id:
        return False
    # 글 단위 URL(경로에 postNo가 더 있거나 레거시 PostView.nhn)은 공식 채널이
    # 아니다 — 블로그 홈(/id)만.
    parts = [p for p in urlparse(url).path.split("/") if p]
    return len(parts) == 1 and parts[0].lower() != "postview.nhn"


def pick_local(
    academy: AcademyRecord, places: list[LocalPlace]
) -> tuple[LocalPlace, bool] | None:
    """지역 검색 후보에서 학원을 고른다. bool은 주소로 매칭됐는지 여부.

    이름만으로 매칭된 경우 동명이인 학원(다른 도시)일 수 있어, 호출부가 신뢰도를
    낮게 잡을 수 있도록 매칭 방식을 함께 알려준다.
    """
    for place in places:
        if addresses_match(academy.address, place.road_address) or addresses_match(
            academy.address, place.address
        ):
            return place, True
    for place in places:
        if names_match(academy.name, place.title):
            return place, False
    return None


def pick_blog_url(academy: AcademyRecord, items: list[ReviewItem]) -> str:
    stem = re.sub(r"학원$", "", academy.name).strip().replace(" ", "")
    for item in items:
        haystack = f"{item.title} {item.content}".replace(" ", "")
        if stem and stem not in haystack:
            continue
        blog_id = _naver_blog_id(item.url)
        if not blog_id:
            continue
        return f"https://blog.naver.com/{blog_id}"
    return ""


def build_proposal(
    path: Path,
    academy: AcademyRecord,
    places: list[LocalPlace],
    blogs: list[ReviewItem],
) -> EnrichProposal:
    picked = pick_local(academy, places)
    local, matched_by_address = picked if picked is not None else (None, False)
    subjects: list[str] = []
    evidence_parts: list[str] = []
    website = ""
    matched_title = ""

    if local is not None:
        matched_title = local.title
        subjects.extend(extract_subjects_from_text(f"{local.title} {local.category}"))
        if is_homepage_url(local.link):
            website = local.link
        evidence_parts.append(
            f"local title={local.title}; category={local.category}; "
            f"road={local.road_address or local.address}"
        )

    blog_url = pick_blog_url(academy, blogs)
    blog_text = " ".join(f"{item.title} {item.content}" for item in blogs[:3])
    if blog_text:
        subjects.extend(extract_subjects_from_text(blog_text))
        evidence_parts.append(f"blog snippets={clean_text(blog_text)[:180]}")

    # 중복 제거는 extract 쪽 normalize가 아니라 합친 뒤 다시.
    try:
        subjects = normalize_subjects(subjects)
    except ValueError:
        subjects = []

    if matched_by_address and subjects:
        confidence = "high"
    elif matched_by_address or (blog_url and subjects):
        confidence = "medium"
    else:
        confidence = "low"
        subjects = []
        website = ""
        blog_url = ""

    if confidence == "low":
        source_note = "검색 매칭 불충분 — 정본 미기입 권고"
    else:
        source_note = "네이버 API HUB 지역·블로그 검색 제안 (정본 반영 전 Founder 확인)"

    return EnrichProposal(
        file_name=path.name,
        name=academy.name,
        address=academy.address or "",
        proposed_subjects=subjects,
        website_url=website,
        blog_url=blog_url,
        confidence=confidence,
        evidence=" | ".join(evidence_parts),
        source_note=source_note,
        matched_local_title=matched_title,
    )


def search_query(name: str) -> str:
    return f"{name} {_QUERY_REGION}"


def enrich_one(
    path: Path,
    academy: AcademyRecord,
    local: LocalSearchProvider,
    blogs: ReviewSource,
) -> EnrichProposal:
    query = search_query(academy.name)
    places = local.search(query, limit=5)
    posts = blogs.search(query, limit=5)
    return build_proposal(path, academy, places, posts)
