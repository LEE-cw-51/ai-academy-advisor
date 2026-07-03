# 데이터베이스

## 현재 상태
MVP 스캐폴딩 단계로 아직 도메인 테이블은 정의되지 않았다.
SQLAlchemy `Base`와 세션 팩토리(`app/db/session.py`)만 구성되어 있다.

## 예정된 스키마 (초안, 미확정)

### academies (학원)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | UUID/int | PK |
| name | varchar | 학원명 |
| address | varchar | 주소 (하남 미사 권역) |
| target_grades | varchar/array | 대상 학년 |
| subjects | varchar/array | 과목 (현재는 수학 중심) |
| description | text | 학원 소개 |
| created_at | timestamp | 생성일시 |
| updated_at | timestamp | 수정일시 |

### reviews (후기) — 추후 검토
학원별 후기/평점 데이터. 추천 로직의 입력으로 사용 가능.

## 마이그레이션
- Alembic으로 관리 (`backend/alembic/`)
- 최초 모델 정의 후 `alembic revision --autogenerate -m "create academies table"` 실행 예정
