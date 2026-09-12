"""Closed trait-label matcher + review ingest idempotency tests."""

from datetime import date

import pytest

from app.models.academy import Academy
from app.models.academy_trait_label import AcademyTraitLabel
from app.models.review import Review
from app.repositories import trait_label_repository
from app.services import trait_label_ingest_service
from app.services.trait_label_matcher import (
    LABEL_KEYWORDS,
    match_labels,
    snippet_around,
    source_type_from_review_source,
)


@pytest.fixture()
def academy(db_session):
    row = Academy(name="가온수학", address="경기도 하남시 미사강변대로 84")
    db_session.add(row)
    db_session.commit()
    return row


def _add_review(db_session, academy, *, content: str, url: str, source="naver_blog"):
    row = Review(
        academy_id=academy.id,
        content=content,
        source=source,
        source_url=url,
        published_at=date(2026, 9, 1),
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


# --- matcher ---


def test_match_curriculum_and_ops_keywords():
    text = "중등 선행이랑 내신·수능 대비, 숙제 많고 클리닉·보강 있어요"
    labels = {label for label, _ in match_labels(text)}
    assert labels == {
        "mentions_seonhaeng",
        "mentions_naesin",
        "mentions_suneung",
        "mentions_homework",
        "mentions_clinic",
    }


@pytest.mark.parametrize(
    "phrase",
    [
        "질문대응이 빨라요",
        "질문 대응이 좋아요",
        "질문 가능해서 좋아요",
        "질문하기 편해요",
        "질문할 수 있어요",
        "질문을 받아요",
        "질의응답 시간이 있어요",
        "QnA 게시판",
        "Q&A 코너",
    ],
)
def test_mentions_qna_safe_compounds(phrase):
    hits = match_labels(phrase)
    assert any(label == "mentions_qna" for label, _ in hits)


def test_bare_question_does_not_match_qna():
    """Raw '질문' alone must not fire mentions_qna (pilot over-match fix)."""
    assert match_labels("질문이 많아요") == []
    assert match_labels("오늘 질문했습니다") == []


def test_at_most_one_hit_per_label():
    hits = match_labels("숙제와 과제가 많아요")
    assert len([h for h in hits if h[0] == "mentions_homework"]) == 1
    assert hits[0][1] == "숙제"  # first keyword wins


def test_snippet_around_includes_keyword():
    text = "앞에 긴 문장입니다. " + ("가" * 50) + "내신 대비 " + ("나" * 50)
    snip = snippet_around(text, "내신")
    assert "내신" in snip
    assert snip.startswith("…")
    assert snip.endswith("…")


def test_source_type_mapping():
    assert source_type_from_review_source("naver_blog") == "blog"
    assert source_type_from_review_source("naver_cafearticle") == "review"
    assert source_type_from_review_source("other") == "review"


def test_closed_vocab_covers_six_labels():
    assert set(LABEL_KEYWORDS) == {
        "mentions_seonhaeng",
        "mentions_naesin",
        "mentions_suneung",
        "mentions_homework",
        "mentions_clinic",
        "mentions_qna",
    }


# --- ingest ---


def test_ingest_inserts_candidate_labels(db_session, academy):
    _add_review(
        db_session,
        academy,
        content="내신 관리와 질문 대응이 좋아요",
        url="https://blog.example/1",
    )

    report = trait_label_ingest_service.ingest_trait_labels_from_reviews(db_session)

    assert report.inserted == 2
    assert report.by_label["mentions_naesin"] == 1
    assert report.by_label["mentions_qna"] == 1
    rows = db_session.query(AcademyTraitLabel).order_by(AcademyTraitLabel.label).all()
    assert len(rows) == 2
    assert all(r.status == "candidate" for r in rows)
    assert all(r.source_type == "blog" for r in rows)
    assert rows[0].source_url == "https://blog.example/1"


def test_ingest_idempotent_on_rerun(db_session, academy):
    _add_review(
        db_session,
        academy,
        content="선행 수업과 클리닉이 있어요",
        url="https://cafe.example/2",
        source="naver_cafearticle",
    )

    first = trait_label_ingest_service.ingest_trait_labels_from_reviews(db_session)
    second = trait_label_ingest_service.ingest_trait_labels_from_reviews(db_session)

    assert first.inserted == 2
    assert second.inserted == 0
    assert second.skipped_duplicate == 2
    assert trait_label_repository.count_all(db_session) == 2


def test_ingest_dry_run_writes_nothing(db_session, academy):
    _add_review(
        db_session,
        academy,
        content="수능 대비 좋아요",
        url="https://blog.example/3",
    )

    report = trait_label_ingest_service.ingest_trait_labels_from_reviews(
        db_session, dry_run=True
    )
    assert report.inserted == 1
    assert trait_label_repository.count_all(db_session) == 0


def test_ingest_does_not_touch_curriculum_columns(db_session, academy):
    assert academy.curriculum_naesin is None
    _add_review(
        db_session,
        academy,
        content="내신 전문 학원",
        url="https://blog.example/4",
    )
    trait_label_ingest_service.ingest_trait_labels_from_reviews(db_session)
    db_session.refresh(academy)
    assert academy.curriculum_naesin is None
    assert academy.curriculum_seonhaeng is None
    assert academy.curriculum_suneung is None


def test_ingest_uses_review_id_when_url_missing(db_session, academy):
    row = Review(
        academy_id=academy.id,
        content="숙제가 많아요",
        source="manual",
        source_url=None,
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    report = trait_label_ingest_service.ingest_trait_labels_from_reviews(db_session)
    assert report.inserted == 1
    label = db_session.query(AcademyTraitLabel).one()
    assert label.source_url == f"review:{row.id}"
