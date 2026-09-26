# 학원 찾기를 `/app/search`로 분리

- 날짜: 2026-09-26
- 상태: 채택
- 대체: 없음 (decision-log.md 2026-09-13 — `/app`에서 지도·검색은 보조. 보조 위치만 라우트로 옮김)

## 계기

`/app`에 조건 입력과 이름·주소·전화 검색이 한 화면에 있어, 검색이 후보 지도를 덮고
「후보로 돌아가기」로 되돌리는 보조 상태가 생겼다. 기본 흐름(상황 입력 → 후보·질문 →
후보 핀)과 이미 아는 학원을 찾는 일이 서로 다른 일이라 같은 지도·토글로 섞이면
주인공이 흐려진다.

## 결정

- 이름·주소·전화 검색 UI는 `frontend/src/app/app/search/page.tsx`(`/app/search`)로 둔다.
  `/app`과 같이 `robots: noindex`.
- `/app`에는 `SEARCH_MODE_LABEL` 링크만 남긴다. 검색 상태·토글·검색 폼·`mapMode ===
  "search"`·`SEARCH_OVERRIDES_CANDIDATES`는 제거한다. 지도는 조건 제출 뒤 후보 핀만.
- 조회는 기존 `GET /academies?q=`만 쓴다(`fetchAllAcademies({ q })`). 백엔드 검색
  엔드포인트·`api.ts`의 `/search` 문자열은 만들지 않는다. 빈 `q`로는 요청하지 않는다.
- 검색 제출 시 URL에 `?q=`를 남기고, 로드 시 `?q=`가 있으면 그 값으로 한 번 조회한다.
  결과가 있을 때만 지도·목록을 그린다. 「조건 입력으로 돌아가기」는 `/app` 링크.
- `/app`·`/app/search` 헤더(학원콕·하남 미사·중개 없음·개인정보)는 공통 컴포넌트로 둔다.

## 바꾸지 않은 것

- `GET /academies?q=` 계약·페이지네이션·`docs/api.md`
- `/app`의 상황 입력 → 상담 질문 → 후보 흐름과 AI 추천·상담 질문 API
- 상세 모달(전화·길찾기·웹사이트)·클릭 이벤트 이름

## 하지 않은 것

- 백엔드 신규 검색 라우트
- `/app`과 검색을 다시 한 화면 토글로 합치는 일
- 빈 `q`로 전체 학원 목록을 올리는 일

## 검증·다음

- `cd frontend && npm run build`
- `cd backend && uv run pytest ../tests/test_app_explore_copy.py`
- 브라우저: `/app` 링크 → `/app/search`, 검색 제출 후 목록, 돌아가기 → `/app`
