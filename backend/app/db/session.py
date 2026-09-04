from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# Vercel Python Functions는 서버리스라 각 인스턴스가 짧게 살고 동시에 여러 개
# 뜬다 — SQLAlchemy 앱 레벨 풀을 유지할 이유가 없다(오히려 Supabase 커넥션 수만
# 낭비). NullPool로 매 요청 연결을 맺고 끊는다.
# `prepare_threshold=None`은 psycopg3의 자동 서버사이드 prepared statement를
# 끈다 — Supabase transaction-mode pooler(Supavisor, 포트 6543)는 커넥션을
# 문장 단위로 재사용하므로, prepare된 문장이 다른 물리 커넥션에서 재실행되며
# 깨질 수 있다 (Supabase 공식 가이드).
connect_args = {}
if settings.database_url.startswith("postgresql"):
    connect_args = {"prepare_threshold": None}

engine = create_engine(
    settings.database_url,
    future=True,
    poolclass=NullPool,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
