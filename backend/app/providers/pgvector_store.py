"""pgvector 기반 `VectorStore` 구현.

별도 벡터 인덱스 테이블 없이 `reviews.embedding` 컬럼을 직접 사용한다. `VectorStore`
Protocol은 `db` 세션을 받지 않으므로(포트를 인프라 관심사로 오염시키지 않기 위해),
이 구현은 자체 `sessionmaker`로 호출마다 짧은 세션을 열고 닫는다.

`add()`는 별도 인덱스 삽입이 아니라 **기존 리뷰 행의 embedding 컬럼을 id로 UPDATE**하는
것과 같다 — 존재하지 않는 id는 조용히 무시된다(0 rows affected). ingest 경로는 항상
실제 리뷰 id를 사용하므로 안전하다.
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import engine
from app.models.review import Review
from app.providers.base import Hit


class PgVectorStore:
    """`Review.embedding`(pgvector) 컬럼을 직접 조회/갱신하는 `VectorStore` 구현."""

    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or sessionmaker(bind=engine, future=True)

    def add(self, items: list[tuple[str, list[float]]]) -> None:
        if not items:
            return
        with self._session_factory() as db:
            for item_id, embedding in items:
                db.execute(
                    update(Review).where(Review.id == int(item_id)).values(embedding=embedding)
                )
            db.commit()

    def search(self, embedding: list[float], top_k: int) -> list[Hit]:
        with self._session_factory() as db:
            distance = Review.embedding.cosine_distance(embedding).label("distance")
            rows = db.execute(
                select(Review.id, distance)
                .where(Review.embedding.is_not(None))
                .order_by(distance)
                .limit(top_k)
            ).all()
        return [Hit(id=str(row.id), score=1.0 - row.distance) for row in rows]
