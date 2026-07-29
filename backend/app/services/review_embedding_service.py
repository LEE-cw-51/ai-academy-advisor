"""리뷰 임베딩 백필 서비스.

`data/`에는 리뷰 원본이 없다 — 이 서비스는 스크래핑 파이프라인이 아니라, DB에 이미
존재하는 `Review` 행 중 `embedding IS NULL`인 것을 배치로 임베딩해 채우는 최소
백필 유틸리티다.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import Review
from app.providers.factory import get_embedding_provider, get_vector_store


@dataclass
class BackfillReport:
    processed: int = 0


def count_missing_embeddings(db: Session) -> int:
    missing = db.scalar(select(func.count()).select_from(Review).where(Review.embedding.is_(None)))
    return int(missing or 0)


def backfill_missing_embeddings(db: Session, batch_size: int = 100) -> BackfillReport:
    report = BackfillReport()
    embedder = get_embedding_provider()
    store = get_vector_store()

    from app.providers.pgvector_store import PgVectorStore

    if not isinstance(store, PgVectorStore):
        raise ValueError("리뷰 임베딩 백필은 Review.embedding을 UPDATE할 VectorStore가 필요합니다. VECTOR_STORE=pgvector 로 설정하세요.")
    while True:
        rows = db.scalars(
            select(Review).where(Review.embedding.is_(None)).limit(batch_size)
        ).all()
        if not rows:
            break
        vectors = embedder.embed([row.content for row in rows])
        store.add([(str(row.id), vector) for row, vector in zip(rows, vectors)])
        db.expire_all()
        report.processed += len(rows)

    return report
