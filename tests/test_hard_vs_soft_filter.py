"""하드(POST /recommendations) vs 소프트(POST /recommendations/ai) 계약 이음새."""

from app.models.academy import Academy


def test_hard_empty_soft_nonempty_on_null_facts(client, db_session):
    """사실이 전부 NULL 인 미사 학원 1건: 하드는 0건, AI 소프트는 비지 않음."""
    db_session.add(
        Academy(name="미확인수학", address="경기도 하남시 미사대로 1")
    )
    db_session.commit()

    hard = client.post(
        "/recommendations",
        json={"level": "high", "region": "미사", "budget_max": 300000},
    )
    assert hard.status_code == 200
    hard_body = hard.json()
    assert hard_body["items"] == []
    assert hard_body["total"] == 0

    soft = client.post(
        "/recommendations/ai",
        json={"query": "고1 내신 미사 수학학원"},
    )
    assert soft.status_code == 200
    assert soft.json()["items"]
