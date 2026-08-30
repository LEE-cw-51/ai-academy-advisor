"""POST /consultation/questions — stub LLM + JSON 파싱 + 체크리스트 fallback."""

from __future__ import annotations

import ast
from pathlib import Path

from app.core.config import get_settings
from app.prompts.consultation import FEW_SHOT_CHECK, FEW_SHOT_CHECKLIST, SYSTEM_PROMPT
from app.providers.factory import get_llm_provider
from app.providers.stub import StubLLMProvider
from app.schemas.consultation import ConsultationRequest
from app.services import consultation_service

REPO_ROOT = Path(__file__).resolve().parents[1]

_PAYLOAD = {
    "grade": "중2",
    "subject": "수학",
    "school": "미사중학교",
    "current_academy": "",
    "style_tags": ["내신 대비"],
    "concern": "숙제가 많고 아이가 지쳐 보여요",
    "intent": "counsel_only",
}

_VALID_JSON = (
    '{"questions":['
    '{"topic":"난이도","prompt":"지금 반 진도가 아이 수준과 맞는지 어떻게 판단하나요?"},'
    '{"topic":"숙제","prompt":"숙제량은 어떻게 조절하나요?"},'
    '{"topic":"공유","prompt":"학습 결과는 얼마나 자주 공유하나요?"}'
    "]}"
)


class _JsonLLM:
    def __init__(self, text: str) -> None:
        self.text = text

    def chat(self, messages: list[dict]) -> str:
        assert messages[0]["role"] == "system"
        assert "JSON" in messages[0]["content"]
        return self.text


class _BoomLLM:
    def chat(self, messages: list[dict]) -> str:
        raise RuntimeError("provider down")


def test_stub_llm_uses_enroll_fallback(client):
    """기본 stub 응답은 JSON이 아니므로 등록 전 체크리스트로 떨어진다."""
    response = client.post("/consultation/questions", json=_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["used_fallback"] is True
    assert len(body["questions"]) == 5
    assert body["disclaimer"].startswith("학원 평가가 아닌")
    assert body["model"] == "StubLLMProvider"
    assert body["questions"][0]["prompt"] == (
        "이 수업을 담당할 강사는 누구이고, 아이와 어떻게 맞춰 가나요?"
    )


def test_current_academy_uses_checkdata_fallback(client):
    payload = {**_PAYLOAD, "current_academy": "미사한결수학"}
    body = client.post("/consultation/questions", json=payload).json()
    assert body["used_fallback"] is True
    prompts = [q["prompt"] for q in body["questions"]]
    assert "지금 반의 진도와 난이도가 아이 수준과 맞는지, 최근 수업에서 어떻게 판단하고 계신가요?" in prompts


def test_find_new_academy_uses_switch_fallback(client):
    payload = {**_PAYLOAD, "intent": "find_new_academy"}
    body = client.post("/consultation/questions", json=payload).json()
    assert body["used_fallback"] is True
    prompts = [q["prompt"] for q in body["questions"]]
    assert "옮기기 전에 현재 학원에서 보완할 수 있는 방법을 구체적으로 물어봤나요?" in prompts


def test_llm_json_is_used(monkeypatch):
    monkeypatch.setattr(
        consultation_service, "get_llm_provider", lambda: _JsonLLM(_VALID_JSON)
    )
    result = consultation_service.generate_questions(
        ConsultationRequest.model_validate(_PAYLOAD)
    )
    assert result.used_fallback is False
    assert len(result.questions) == 3
    assert result.questions[0].topic == "난이도"
    assert result.model == "_JsonLLM"


def test_http_uses_parsed_llm_json(client, monkeypatch):
    monkeypatch.setattr(
        consultation_service, "get_llm_provider", lambda: _JsonLLM(_VALID_JSON)
    )
    response = client.post("/consultation/questions", json=_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["used_fallback"] is False
    assert [q["topic"] for q in body["questions"]] == ["난이도", "숙제", "공유"]


def test_fenced_json_is_parsed(monkeypatch):
    fenced = "```json\n" + _VALID_JSON + "\n```"
    monkeypatch.setattr(
        consultation_service, "get_llm_provider", lambda: _JsonLLM(fenced)
    )
    result = consultation_service.generate_questions(
        ConsultationRequest.model_validate(_PAYLOAD)
    )
    assert result.used_fallback is False
    assert len(result.questions) == 3


def test_llm_exception_uses_fallback(monkeypatch):
    monkeypatch.setattr(consultation_service, "get_llm_provider", lambda: _BoomLLM())
    result = consultation_service.generate_questions(
        ConsultationRequest.model_validate(_PAYLOAD)
    )
    assert result.used_fallback is True
    assert len(result.questions) == 5
    assert result.model == "_BoomLLM"


def test_too_few_questions_uses_fallback(monkeypatch):
    skinny = '{"questions":[{"topic":"A","prompt":"하나만 있나요?"}]}'
    monkeypatch.setattr(
        consultation_service, "get_llm_provider", lambda: _JsonLLM(skinny)
    )
    result = consultation_service.generate_questions(
        ConsultationRequest.model_validate(_PAYLOAD)
    )
    assert result.used_fallback is True


def test_rejects_empty_concern(client):
    bad = {**_PAYLOAD, "concern": ""}
    assert client.post("/consultation/questions", json=bad).status_code == 422


def test_rejects_invalid_intent(client):
    bad = {**_PAYLOAD, "intent": "recommend_academy"}
    assert client.post("/consultation/questions", json=bad).status_code == 422


def test_rejects_missing_grade(client):
    bad = {k: v for k, v in _PAYLOAD.items() if k != "grade"}
    assert client.post("/consultation/questions", json=bad).status_code == 422


def test_factory_default_is_stub():
    get_settings.cache_clear()
    get_llm_provider.cache_clear()
    try:
        assert isinstance(get_llm_provider(), StubLLMProvider)
    finally:
        get_settings.cache_clear()
        get_llm_provider.cache_clear()


def test_system_prompt_forbids_judgment_and_requires_json():
    assert "판정" in SYSTEM_PROMPT
    assert "JSON" in SYSTEM_PROMPT
    assert "마크다운" in SYSTEM_PROMPT
    assert "추천" in SYSTEM_PROMPT


def test_few_shot_matches_check_and_checklist_copy():
    check = (REPO_ROOT / "frontend/src/components/check/checkData.ts").read_text(
        encoding="utf-8"
    )
    checklists = (
        REPO_ROOT / "frontend/src/components/checklists/checklistsData.ts"
    ).read_text(encoding="utf-8")
    for _topic, prompt in FEW_SHOT_CHECK:
        assert prompt in check
    for _topic, prompt in FEW_SHOT_CHECKLIST:
        assert prompt in checklists


def test_fallback_prompts_match_frontend_copy():
    check = (REPO_ROOT / "frontend/src/components/check/checkData.ts").read_text(
        encoding="utf-8"
    )
    checklists = (
        REPO_ROOT / "frontend/src/components/checklists/checklistsData.ts"
    ).read_text(encoding="utf-8")
    for item in consultation_service.FALLBACK_BEFORE_ENROLL:
        assert item.prompt in checklists
    for item in consultation_service.FALLBACK_BEFORE_SWITCH:
        assert item.prompt in checklists
    for item in consultation_service.FALLBACK_CURRENT:
        assert item.prompt in check or item.prompt in checklists


def test_consultation_service_imports_no_orm():
    path = Path(consultation_service.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        else:
            continue
        for name in names:
            assert not name.startswith("sqlalchemy")
            assert not name.startswith("app.models")
            assert "groq" not in name
            assert "openai" not in name
