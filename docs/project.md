# 프로젝트 개요

## 이름
AI Academy Advisor (서비스명: 학원콕)

## 목표
하남 미사 지역 학원의 구조화된 정보를 바탕으로 조건에 맞는 학원을 추천하는 도메인 특화
AI 서비스의 MVP를 개발한다.

## 배경
학부모/학생이 지역 내 다수의 학원 중 자신에게 맞는 곳을 찾기 어렵다는 문제를 해결하기 위해,
학원 정보(커리큘럼, 대상 학년, 위치, 후기 등)를 구조화하고 AI가 사용자 조건에 맞춰 추천한다.

핵심 자산은 UI 자체가 아니라 **출처와 확인일을 갖춘 정확한 지역 학원 사실 데이터베이스**다.

## 현재 단계
MVP(Minimum Viable Product) 단계. 확장성보다 명확한 구조와 유지보수성을 우선한다.
Phase별 진행 상황은 [roadmap.md](roadmap.md), 이미 내려진 결정은 [decision-log.md](decision-log.md) 참고.

## 범위
- 대상 지역: 하남 미사 (UI에 고정)
- 핵심 기능: 학원 사실 데이터 기반 추천 + 지도 표시 + engagement 계측
- 배포된 웹 UI: 학년·학교·과목·학습 스타일·추가 요구를 입력받는 **안내형 추천 화면**

## 현재 구현 완료로 보지 않는 것
- **자유 대화형 채팅 및 SSE 스트리밍 채팅(`POST /chat`)** — 로드맵 상 계획일 뿐 미구현
- LlamaIndex 기반 RAG 엔진, LLM 기반 의도 분석 (현재 의도 분석은 규칙 기반)
- 로그인/인증(JWT), 관리자 페이지
- Flutter 클라이언트 (프론트 스택은 Next.js로 확정 — `decision-log.md` 2026-07-31)

## 협업 방식
여러 AI(ChatGPT·Claude·Cursor·Manus)와 Founder가 GitHub 저장소를 단일 정본으로 삼아 일한다.
공통 계약은 [../AGENTS.md](../AGENTS.md), 역할·인계 규약은 [ai-team.md](ai-team.md)에 있다.
