"""config 기반 provider 선택 팩토리.

`core.config.get_settings`의 `@lru_cache` 팩토리 관례를 따른다. provider 이름과
구현을 여기서만 매핑하므로, 새 어댑터 추가/교체는 이 파일과 config만 건드리면 된다.
"""

from functools import lru_cache

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.providers.base import (
    EmbeddingProvider,
    LLMProvider,
    LocalSearchProvider,
    ReviewSource,
    VectorStore,
)
from app.providers.groq import GroqLLMProvider
from app.providers.huggingface_embedding import HuggingFaceEmbeddingProvider
from app.providers.naver_local import NaverLocalSearch
from app.providers.naver_review import NaverReviewSource
from app.providers.openai_embedding import OpenAIEmbeddingProvider
from app.providers.pgvector_store import PgVectorStore
from app.providers.stub import (
    StubEmbeddingProvider,
    StubLLMProvider,
    StubLocalSearchProvider,
    StubReviewSource,
    StubVectorStore,
)


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    name = settings.embedding_provider
    if name == "stub":
        return StubEmbeddingProvider(dim=settings.embedding_dim)
    if name == "openai":
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
            base_url=settings.openai_embedding_base_url,
            dim=settings.embedding_dim,
        )
    if name == "huggingface":
        return HuggingFaceEmbeddingProvider(
            api_key=settings.hf_api_key,
            model=settings.embedding_model,
            base_url=settings.hf_embedding_base_url,
            dim=settings.embedding_dim,
            timeout=settings.hf_embedding_timeout,
            max_retries=settings.hf_embedding_max_retries,
        )
    # Groq은 임베딩 모델이 없다 — 채팅·음성·가드뿐이라 여기에 분기가 생길 일은 없다.
    raise ValueError(
        f"지원하지 않는 embedding_provider: {name!r} "
        "(현재 'stub'/'openai'/'huggingface'만 구현됨)"
    )


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    name = settings.llm_provider
    if name == "stub":
        return StubLLMProvider()
    if name == "groq":
        return GroqLLMProvider(
            api_key=settings.groq_api_key,
            model=settings.llm_model,
            base_url=settings.groq_base_url,
        )
    # 다음 단계에서 추가: "openai"(gpt-4o-mini 등).
    raise ValueError(
        f"지원하지 않는 llm_provider: {name!r} (현재 'stub'/'groq'만 구현됨)"
    )


@lru_cache
def _cached_vector_store() -> VectorStore:
    """`db` 없이 호출될 때만 쓰는 싱글턴 경로.

    `StubVectorStore`는 in-memory `_items`를 들고 있어 `add()`(테스트 셋업)와
    `search()`(요청 처리)가 반드시 같은 인스턴스를 봐야 한다 — 여기서 캐시가
    깨지면 안 된다. `pgvector`+`db` 없음 경로(CLI 배치 등)도 기존처럼 프로세스
    수명 동안 하나의 엔진-바운드 sessionmaker를 재사용한다.
    """
    settings = get_settings()
    name = settings.vector_store
    if name == "stub":
        return StubVectorStore()
    if name == "pgvector":
        return PgVectorStore()
    raise ValueError(
        f"지원하지 않는 vector_store: {name!r} (현재 'stub'/'pgvector'만 구현됨)"
    )


def get_vector_store(db: Session | None = None) -> VectorStore:
    """`db`(요청 스코프 세션)가 주어지면 pgvector용 `PgVectorStore`가 그 커넥션을
    공유한다 — 그 경우에만 캐시를 우회해 매번 새로 만든다.

    `NullPool`(app/db/session.py, 2026-09-04 서버리스 이전) 아래서는 새
    `sessionmaker(bind=engine)`을 만들 때마다 물리 커넥션이 하나 더 열린다 —
    `db`를 넘기지 않으면 `PgVectorStore`가 자체 커넥션을 여는 옛 동작 그대로라
    요청당 커넥션이 2개(요청 세션 + 벡터 검색) 든다. `search()`는 읽기 전용이라
    `db.connection()`으로 얻은 라이브 커넥션에 얹힌 임시 `Session`을 열고 닫아도
    바깥 요청 트랜잭션을 건드리지 않는다(SQLAlchemy의 "외부 트랜잭션 공유" 패턴).
    이 경로를 캐시하지 않는 이유: `db`가 요청마다 다른 세션이라 메모이즈하면
    닫힌 세션의 커넥션을 재사용하려는 버그가 난다 — 객체 생성 자체는 가볍다.
    """
    settings = get_settings()
    if db is not None and settings.vector_store == "pgvector":
        return PgVectorStore(session_factory=sessionmaker(bind=db.connection(), future=True))
    return _cached_vector_store()


@lru_cache
def get_review_source() -> ReviewSource:
    settings = get_settings()
    name = settings.review_source
    if name == "stub":
        return StubReviewSource()
    if name == "naver":
        endpoints = tuple(
            part.strip()
            for part in settings.naver_review_endpoints.split(",")
            if part.strip()
        ) or ("blog", "cafearticle")
        return NaverReviewSource(
            client_id=settings.naver_client_id,
            client_secret=settings.naver_client_secret,
            base_url=settings.naver_base_url,
            endpoints=endpoints,
        )
    if name == "browser":
        # 이음새만 있고 어댑터는 없다. robots·약관이 허용하는 소스가 나타났을 때만
        # 비-우회 렌더러 어댑터를 여기 연결한다 (docs/decision-log.md 2026-09-11,
        # app/cli/check_robots.py 로 먼저 확인). 봇 차단 우회는 붙이지 않는다.
        raise NotImplementedError(
            "browser review_source 는 아직 어댑터가 없다 — 허용 소스를 "
            "check_robots 로 확인하고 Founder 승인 후 연결한다"
        )
    raise ValueError(
        f"지원하지 않는 review_source: {name!r} "
        "(현재 'stub'/'naver' 구현, 'browser'는 이음새만)"
    )


@lru_cache
def get_local_search_provider() -> LocalSearchProvider:
    settings = get_settings()
    name = settings.local_search_provider
    if name == "stub":
        return StubLocalSearchProvider()
    if name == "naver":
        return NaverLocalSearch(
            client_id=settings.naver_client_id,
            client_secret=settings.naver_client_secret,
            base_url=settings.naver_base_url,
        )
    raise ValueError(
        f"지원하지 않는 local_search_provider: {name!r} (현재 'stub'/'naver'만 구현됨)"
    )
