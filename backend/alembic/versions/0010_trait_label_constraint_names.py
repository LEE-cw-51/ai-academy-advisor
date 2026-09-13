"""align academy_trait_labels constraint names with the ORM model

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-12

`0009`가 `op.create_table` 안에서 `sa.CheckConstraint(name=...)`에 이미 완성된
이름을 넘겼고, Alembic이 그 위에 `Base.metadata`의 naming_convention을 한 번 더
씌웠다. 그래서 운영 DB에는 `ck_academy_trait_labels_ck_academy_trait_labels_label`
처럼 접두사가 겹친 이름이 들어갔고, 모델이 만드는 `ck_academy_trait_labels_label`
과 갈라졌다. 테스트는 `Base.metadata.create_all`로 스키마를 만들어 마이그레이션
경로를 타지 않으므로 이 드리프트를 잡지 못했다.

`0009`는 짧은 이름을 넘기도록 고쳤으니 새 DB는 처음부터 올바른 이름을 갖는다.
이 리비전은 **이미 0009를 적용한 DB**를 맞춘다. 두 경우 모두 통과하도록 존재
검사 후에만 rename 한다.

같은 이유로 `ix_academy_trait_labels_academy_id`도 없앤다 — 유니크 제약
`(academy_id, label, source_url)`의 선두 컬럼이 같은 조회를 커버하므로 쓰기
비용만 늘던 중복 인덱스다.
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

# (겹친 이름, 올바른 이름)
_RENAMES = (
    (
        "ck_academy_trait_labels_ck_academy_trait_labels_label",
        "ck_academy_trait_labels_label",
    ),
    (
        "ck_academy_trait_labels_ck_academy_trait_labels_source_type",
        "ck_academy_trait_labels_source_type",
    ),
    (
        "ck_academy_trait_labels_ck_academy_trait_labels_status",
        "ck_academy_trait_labels_status",
    ),
)


def _rename_if_present(old_name: str, new_name: str) -> None:
    """제약 이름이 그 이름으로 존재할 때만 바꾼다 (신규 DB에서는 no-op)."""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = '{old_name}'
                  AND conrelid = 'academy_trait_labels'::regclass
            ) THEN
                ALTER TABLE academy_trait_labels
                    RENAME CONSTRAINT {old_name} TO {new_name};
            END IF;
        END $$
        """
    )


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    for old_name, new_name in _RENAMES:
        _rename_if_present(old_name, new_name)

    op.execute("DROP INDEX IF EXISTS ix_academy_trait_labels_academy_id")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_academy_trait_labels_academy_id "
        "ON academy_trait_labels (academy_id)"
    )
    for old_name, new_name in _RENAMES:
        _rename_if_present(new_name, old_name)
