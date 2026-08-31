"""검색 결과에서 학원 과목·URL **제안**을 만든다. JSON 정본은 쓰지 않는다."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from app.core.subjects import extract_subjects_from_text, subjects_csv
from app.providers.base import ReviewItem
from app.providers.naver_local import LocalPlace, NaverLocalSearch
from app.providers.naver_review import NaverReviewSource, clean_text
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
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def load_academy_records(directory: Path) -> list[tuple[Path, AcademyRecord]]:
    pairs: list[tuple[Path, AcademyRecord]] = []
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        pairs.append((path, AcademyRecord.model_validate(raw)))
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
    stem = re.sub(r"학원$", "", academy_name).strip()
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


def is_official_blog_url(url: str) -> bool:
    if not url:
        return False
    host = urlparse(url).netloc.lower()
    path = urlparse(url).path
    if "blog.naver.com" not in host:
        return False
    if any(marker in host for marker in _CAFE_HOST_MARKERS):
        return False
    # 글 단위 URL은 공식 채널이 아니다 — 블로그 홈(/id)만.
    parts = [p for p in path.split("/") if p]
    return len(parts) == 1


def pick_local(academy: AcademyRecord, places: list[LocalPlace]) -> LocalPlace | None:
    for place in places:
        if addresses_match(academy.address, place.road_address) or addresses_match(
            academy.address, place.address
        ):
            return place
    for place in places:
        if names_match(academy.name, place.title):
            return place
    return None


def pick_blog_url(academy: AcademyRecord, items: list[ReviewItem]) -> str:
    stem = re.sub(r"학원$", "", academy.name).strip()
    for item in items:
        haystack = f"{item.title} {item.content}"
        if stem and stem not in haystack.replace(" ", ""):
            continue
        parsed = urlparse(item.url)
        host = parsed.netloc.lower()
        if "blog.naver.com" not in host:
            continue
        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            continue
        return f"https://blog.naver.com/{parts[0]}"
    return ""


def build_proposal(
    path: Path,
    academy: AcademyRecord,
    places: list[LocalPlace],
    blogs: list[ReviewItem],
) -> EnrichProposal:
    local = pick_local(academy, places)
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
    from app.core.subjects import normalize_subjects

    try:
        subjects = normalize_subjects(subjects)
    except ValueError:
        subjects = []

    address_ok = local is not None and (
        addresses_match(academy.address, local.road_address)
        or addresses_match(academy.address, local.address)
    )

    if address_ok and subjects:
        confidence = "high"
    elif local is not None or (blog_url and subjects):
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
    local: NaverLocalSearch,
    blogs: NaverReviewSource,
) -> EnrichProposal:
    query = search_query(academy.name)
    places = local.search(query, limit=5)
    posts = blogs.search(query, limit=5)
    return build_proposal(path, academy, places, posts)
