"""pgvector 기반 `VectorStore` 구현.

별도 벡터 인덱스 테이블 없이 `reviews.embedding` 컬럼을 직접 사용한다. `VectorStore`
Protocol은 `db` 세션을 받지 않으므로(포트를 인프라 관심사로 오염시키지 않기 위해),
이 구현은 자체 `sessionmaker`로 호출마다 짧은 세션을 열고 닫는다.

`add()`는 별도 인덱스 삽입이 아니라 **기존 리뷰 행의 embedding 컬럼을 id로 UPDATE**하는
것과 같다 — 존재하지 않는 id는 조용히 무시된다(0 rows affected). ingest 경로는 항상
실제 리뷰 id를 사용하므로 안전하다.

`Review.embedding.cosine_distance(...)`는 쓸 수 없다: 컬럼이
`JSON().with_variant(Vector(dim), "postgresql")`로 선언되어 있는데, `with_variant()`는
DDL/바인드·결과 처리만 dialect별로 바꿔치기하고 `.cosine_distance()` 같은 비교자를
제공하는 `comparator_factory`는 원본(JSON) 타입에 고정되어 postgres dialect에서도
`AttributeError`가 난다. 대신 `.op("<=>", ...)`로 pgvector의 코사인 거리 연산자를
직접 호출한다 — 우변 바인드 파라미터는 여전히 컬럼과 같은 Variant 타입을 가지므로
실행 시점엔 postgres dialect_impl(Vector)의 bind_processor가 정상 적용된다.
"""

from __future__ import annotations

from sqlalchemy import Float, select, update
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
            distance = Review.embedding.op("<=>", return_type=Float)(embedding).label("distance")
            rows = db.execute(
                select(Review.id, distance)
                .where(Review.embedding.is_not(None))
                .order_by(distance)
                .limit(top_k)
            ).all()
        return [Hit(id=str(row.id), score=1.0 - row.distance) for row in rows]
