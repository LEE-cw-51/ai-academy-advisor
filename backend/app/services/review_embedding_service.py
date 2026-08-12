"""리뷰 임베딩 백필 서비스.

`data/`에는 리뷰 원본이 없다 — 이 서비스는 스크래핑 파이프라인이 아니라, DB에 이미
존재하는 `Review` 행 중 `embedding IS NULL`인 것을 배치로 임베딩해 채우는 최소
백필 유틸리티다.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.review import Review
from app.providers.factory import get_embedding_provider, get_vector_store


@dataclass
class BackfillReport:
    processed: int = 0


def _missing_embedding_clause():
    """미임베딩 행 필터.

    PostgreSQL(Vector)에서는 SQL NULL, SQLite(테스트·JSON)에서는 JSON null이
    텍스트 `'null'`로 저장되어 `IS NULL`에 안 걸린다. 둘 다 잡는다.
    """
    return or_(
        Review.embedding.is_(None),
        cast(Review.embedding, String) == "null",
    )


def count_missing_embeddings(db: Session) -> int:
    missing = db.scalar(
        select(func.count()).select_from(Review).where(_missing_embedding_clause())
    )
    return int(missing or 0)


def backfill_missing_embeddings(db: Session, batch_size: int = 100) -> BackfillReport:
    report = BackfillReport()
    embedder = get_embedding_provider()
    store = get_vector_store()

    from app.providers.pgvector_store import PgVectorStore

    if not isinstance(store, PgVectorStore):
        raise ValueError(
            "리뷰 임베딩 백필은 Review.embedding을 UPDATE할 VectorStore가 필요합니다. "
            "VECTOR_STORE=pgvector 로 설정하세요."
        )
    while True:
        missing_before = count_missing_embeddings(db)
        rows = db.scalars(
            select(Review).where(_missing_embedding_clause()).limit(batch_size)
        ).all()
        if not rows:
            break
        vectors = embedder.embed([row.content for row in rows])
        if len(vectors) != len(rows):
            raise ValueError(
                f"임베딩 결과 수 불일치: rows={len(rows)} vectors={len(vectors)}"
            )
        store.add(
            [(str(row.id), vector) for row, vector in zip(rows, vectors, strict=True)]
        )
        db.expire_all()
        missing_after = count_missing_embeddings(db)
        if missing_after >= missing_before:
            raise ValueError(
                "임베딩 백필 진행 없음: 배치 후에도 embedding IS NULL 행이 줄지 않았습니다 "
                f"(before={missing_before}, after={missing_after})"
            )
        report.processed += len(rows)

    return report
