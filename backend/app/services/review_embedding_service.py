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


def backfill_missing_embeddings(
    db: Session, batch_size: int = 100, limit: int | None = None
) -> BackfillReport:
    """미임베딩 리뷰를 배치로 채운다. `limit`은 이번 실행에서 처리할 행 수 상한.

    `limit`이 필요한 이유: HuggingFace는 토큰이 아니라 CPU 시간으로 과금해서 전체
    비용을 사전에 계산할 수 없다. 소량을 먼저 돌려 실제 소모액을 확인한 뒤 나머지를
    이어 돌린다. `embedding IS NULL`만 집으므로 중단·재개는 원래 안전하다.
    """
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
        if limit is not None and report.processed >= limit:
            break
        take = batch_size
        if limit is not None:
            take = min(batch_size, limit - report.processed)
        missing_before = count_missing_embeddings(db)
        rows = db.scalars(
            select(Review).where(_missing_embedding_clause()).limit(take)
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
