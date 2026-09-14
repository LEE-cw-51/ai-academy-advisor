# `/check`·`/checklists` 퇴역 — 공개 흐름을 `/app` 하나로

- 날짜: 2026-09-14
- 상태: 채택
- 대체:
  - `decision-log.md 2026-09-13 — 첫 MVP 공개 중심을 상황 입력 → 후보·상담 질문 → 직접 확인으로 확정`
    중 상황 카드 2장(`/checklists`·`/check`)을 보조 퍼널로 유지한 부분
  - `decision-log.md 2026-08-19` 3페이지 랜딩 퍼널(`/` 상황 선택 · `/checklists` 알아보는 중 · `/check` 다니는 중)

## 계기

2026-09-13에 `/`의 주 CTA가 `/app`(상황 입력 → 확인해 볼 후보 → 상담 질문)이 됐다.
`/app`에는 `새 학원을 알아보는 중 / 지금 다니는 학원 상담` 선택과 현재 학원 입력이 있고,
`POST /consultation/questions`는 재원 상황이면 재원 상담 문항을 쓴다. 그러면서 홈 아래
상황 카드가 보내던 두 페이지가 같은 일을 더 약하게 반복하게 됐다.

- `/check`(1분 학원 점검): 3문항 자가 점검 → 상담 질문 3개. `/app`의 "지금 다니는 학원 상담"이
  학년·과목·고민을 받아 같은 목적의 질문을 상황에 맞춰 만든다.
- `/checklists`(상담 전 질문): 고정 질문 목록. `/app`이 후보와 함께 상황에 맞춘 질문을 준다.

홈 한 화면에서 주 CTA와 보조 카드 두 장이 경쟁했다. 두 페이지 전용 컴포넌트·카피·이벤트 9종·
테스트도 유지보수 비용으로 남아 있었다. Founder가 삭제를 택했다.

## 결정

- `/check`·`/checklists` 라우트와 전용 컴포넌트(`components/check/`, `components/checklists/`,
  `landing/`의 `HeroSection`·`SituationSection`·`SituationCard`·`TrackedLink`)를 지운다.
  홈은 `HomeHero → GroundworkSection`만 남는다.
- 옛 URL은 `frontend/next.config.ts`의 `redirects()`로 `/app`에 **307**(`permanent: false`) 리다이렉트한다.
  - 카카오 웰컴 메시지 후속 응답과 광고 초안의 링크가 404가 되지 않게 하기 위해서다.
  - 308은 브라우저가 캐시해 되돌리기 어렵고, 보존할 검색 유입도 없다. 쿼리(utm)는 그대로 넘어간다.
- 상담 질문 톤의 정본을 백엔드로 옮긴다: `app/prompts/consultation.py`의 few-shot,
  `app/services/consultation_service.py`의 fallback. 질문 문장은 바꾸지 않았다.
  시스템 프롬프트에서 사라진 파일을 가리키던 "checkData/체크리스트와 같은 말투"만
  "아래 좋은 질문 예와 같은 말투"로 고쳤다.
- 메타 설명·푸터 고지·개인정보처리방침에서 1분 점검 언급을 뺀다. 방침 개정일은 2026-09-14로 바꾼다.

## 경로

| 경로 | 역할 |
|---|---|
| `/` | 소개 + 주 CTA `후보와 질문 정리하기` → `/app` |
| `/app` | 상황 입력(알아보는 중·다니는 중) → 확인해 볼 후보 → 상담 질문 |
| `/privacy` | 개인정보처리방침 |
| `/check`, `/checklists` | 307 → `/app` |

## 계측

- `ClickEvent`(백엔드)와 `ClickEventType`(프론트)에서 퍼널 이벤트 9종을 제거했다. 이제 이 값을 보내면 422다.
  - `mini_check_started`·`mini_check_completed`·`mini_check_result_viewed`·`mini_check_home_clicked`
  - `home_check_clicked`·`checklist_kakao_clicked`
  - `home_explore_selected`·`explore_check_clicked`·`check_explore_clicked`
- `click_logs.event`는 문자열 컬럼이라 마이그레이션이 없고, 과거 행은 그대로 남는다.
  2026-08-19에 `home_stage_*`를 제거한 방식과 같다.
- 카카오 CTA는 모두 `kakao_channel` 하나로 계측한다. `KakaoChannelLink`·`KakaoChannelCta`·
  `KakaoChannelModal`의 `event` prop을 없앴다.
- 홈 → `/app` 클릭 이벤트는 새로 만들지 않았다. `/app` 제출은 `POST /recommendations/ai`가
  `search_history`로 이미 남긴다.

## 검토한 대안·트레이드오프

- **홈 카드만 숨기고 라우트 유지**: 카카오 링크가 그대로 산다. 대신 쓰지 않는 두 페이지의 코드·카피·이벤트·테스트를 계속 맞춰야 한다.
- **리다이렉트 없이 삭제**: 가장 깔끔하지만, 코드 밖(카카오 웰컴 메시지)을 먼저 고치지 않으면 404가 난다.
- 리다이렉트된 사용자는 기대한 "질문 목록" 대신 입력 폼에 도착한다. 웰컴 메시지를 `/app` 기준으로 고치기 전까지 감수하는 과도기 비용이다.

## 바꾸지 않은 것

- `/app`의 폼·후보·상담 질문 흐름, 두 추천 API의 분리
- `POST /consultation/questions` 계약과 질문 문장
- 카카오 채널 CTA(`StickyKakaoBar`·`GroundworkSection`)와 모달 문구, `kakao_channel` 이벤트
- 학원 데이터, 디자인 토큰, `docs/decision-log.md`의 옛 항목 본문

## 하지 않은 것 (코드 밖, Founder)

- 카카오 채널 관리자센터에서 두 곳을 `/app` 기준으로 고친다. 리다이렉트가 있어 급하지 않다.
  - 웰컴 메시지의 "상담 전 질문과 1분 학원 점검을 이용하실 수 있으며" 문장
  - 후속 응답의 `/check`·`/checklists` 링크
- 당근 광고는 2026-08-21 게이트가 계속 닫혀 있다. 재개하면 착지를 `/app` 기준으로 다시 설계한다
  (`docs/marketing-daangn-kakao.md` 상단 고지).

## 검증·다음

- 퇴역 가드(`tests/test_landing_copy.py`)
  - `test_check_and_checklists_are_retired_and_redirect_to_app`: 파일 부재, 307 리다이렉트, 링크 부재
  - `test_retired_events_are_gone_on_both_sides_of_the_wire`
  - `test_no_dead_stage_vocabulary_remains`: `1분 점검` 문구
- `tests/test_engagement_api.py`: 퇴역 이벤트는 422
- 실행 결과(2026-09-14, 로컬)
  - `pytest ../tests`: 461 passed / 3 skipped. 기존 476에서 삭제·통합한 테스트 15개만큼 줄었다.
  - `npm ci && npm run build`: 성공. 라우트는 `/`·`/_not-found`·`/app`·`/privacy`이고 `/check`·`/checklists`는 없다.
  - `next start`에서 확인한 응답
    - `HEAD /check?utm_source=daangn&utm_content=current` → `307`, `location: /app?utm_source=daangn&utm_content=current`
    - `HEAD /checklists` → `307`, `location: /app`
    - `/` HTML에 `href="/app"` CTA가 있고, 상황 카드·`1분`·`/check` 링크는 없다.
- 웰컴 메시지와 광고 초안이 `/app`으로 정리되고 옛 URL 유입이 없으면 `redirects()`를 지운다.
