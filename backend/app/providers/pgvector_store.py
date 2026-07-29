"""pgvector 기반 VectorStore 구현 (`Review.embedding` 컬럼 대상).

`Review.embedding`은 `JSON().with_variant(Vector(dim), "postgresql")`로 이중화되어
있다. `with_variant()`는 DDL/바인드·결과 처리만 dialect별로 바꿔치기하고, Python
표현식 빌드에 쓰이는 `comparator_factory`는 원본(JSON) 타입에 고정된다 — 즉
`Review.embedding.cosine_distance(...)`는 postgres dialect라도 `AttributeError`를
낸다. 대신 `.op("<=>", ...)`로 pgvector의 코사인 거리 연산자를 직접 호출한다. 우변
바인드 파라미터는 여전히 컬럼과 같은 Variant 타입을 가지므로, 실행 시점에는 postgres
dialect_impl(Vector)의 bind_processor가 정상 적용된다.

`VectorStore.search(embedding, top_k)` 포트 시그니처에는 `db: Session`이 없으므로,
다른 provider(설정만으로 생성되는 무상태 싱글턴)와의 일관성을 위해 호출마다 자체
세션을 열고 닫는다 (요청 스코프 세션에 얹지 않음).
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import Float, Select, select, update
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.review import Review
from app.providers.base import Hit


class PgVectorStore:
    """`reviews.embedding`(pgvector) 기반 `VectorStore` 구현."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def add(self, items: list[tuple[str, list[float]]]) -> None:
        if not items:
            return
        db = self._session_factory()
        try:
            for item_id, vector in items:
                db.execute(
                    update(Review).where(Review.id == int(item_id)).values(embedding=vector)
                )
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _build_search_statement(embedding: list[float], top_k: int) -> Select:
        """질의 벡터와의 코사인 거리(`<=>`) 오름차순 상위 `top_k`건 검색문.

        DB 연결 없이도 컴파일해 SQL 형태를 검증할 수 있도록 순수 함수로 분리했다.
        """
        distance = Review.embedding.op("<=>", return_type=Float)(embedding)
        return (
            select(Review.id, distance.label("distance"))
            .where(Review.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
        )

    @staticmethod
    def _to_hit(review_id: int, distance: float) -> Hit:
        # pgvector `<=>`는 코사인 거리([0, 2]); Hit.score는 "클수록 유사"이므로
        # 코사인 유사도(1 - distance)로 변환한다 (StubVectorStore와 동일 스케일/방향).
        return Hit(id=str(review_id), score=1.0 - distance)

    def search(self, embedding: list[float], top_k: int) -> list[Hit]:
        stmt = self._build_search_statement(embedding, top_k)
        db = self._session_factory()
        try:
            rows = db.execute(stmt).all()
        finally:
            db.close()
        return [self._to_hit(row.id, row.distance) for row in rows]
