# 의사결정 로그

주요 기술적/제품적 의사결정과 그 이유를 기록한다.

## 2026-08-17 — `/` · `/check` · `/checklists` 가독성·계층 폴리시

- **계기**: 랜딩·점검·체크리스트 허브가 같은 Header/Footer를 쓰지만, 히어로 과밀·`ink-subtle` 과다·비상호작용 카드 밀도·긴 목록 스캔성이 가독성을 떨어뜨렸다.
- **결정**: 토큰·라우트 분리·CTA 문구·`checkData` 분류는 그대로 두고, 시각·계층만 좁게 손본다. 전면 리디자인·새 히어로 사진·`/check` CTA를 `/`에 복귀시키지 않는다.
- **반영**:
  - `/` — 로고 축소, h1→서포트→배지→CTA 순, Pain Card 제거·약속만 좌측 보더, Features/Preview 대비·밀도, 스티키 `leading-snug`, 히어로 fade-up(`prefers-reduced-motion` 존중)
  - `/check` — 서포트·hint·결과 보조 `ink-muted`, 상담 질문 구분선+라벨, 문항 버튼 간격
  - `/checklists` — 앵커 secondary 버튼형, 항목 `divide-y`·brand 번호
  - 공유 Footer Disclaimer 2단락
- **문서**: `docs/design/theme.md` 첫 화면 예산·대비 규칙 갱신.

## 2026-08-17 — `/check` 전용 퍼널로 랜딩·점검 역할 분리

- **계기**: `/`에 점검 CTA와 체크리스트·출시 알림이 겹쳐 “대기자 랜딩인지 점검 도구인지” 혼재해 보였다.
- **결정**: `/`는 출시 알림 중심의 원래 랜딩으로 되돌린다. 광고·점검·카카오 전환은 `/check`만 담당한다.
- **경로**:
  - `/` — 브랜드·410곳·출시 알림. 주 CTA `카카오톡으로 무료 출시 알림 받기`. `?from=check` 분기 없음.
  - `/check` — 인트로(“지금 다니는 아이의 학원을 점검해 보세요” + `1분 학원 점검`) → 3문항 → 결과. 결과에서 주 CTA `카카오톡 친구 추가하고 점검리스트 받기`(`checklist_kakao_clicked`), 보조 `학원콕 더 알아보기` → `/`.
  - `/checklists` — 웹 허브(PDF 없음). 웰컴메시지 링크 유지.
- **계측**: `mini_check_started`는 인트로 버튼 클릭 시. `checklist_kakao_clicked`는 `/check` 결과 화면 카카오 CTA. `kakao_channel`은 `/`·푸터 유기 유입.
- **이전(같은 날) 결정과의 차이**: 점검 결과 후 카카오 전환을 `/`(`?from=check`)로 미루지 않고, 결과 화면에서 바로 제공한다. 랜딩은 점검 주 CTA를 두지 않는다.

## 2026-08-17 — 랜딩을 3문항 미니 점검 → 체크리스트 3종 카카오 전환으로 바꿈

- **계기**: 당근 광고 초기 성과가 노출 약 600회·클릭 2회·CTR 약 0.33%였다. ‘출시 알림’만으로는 클릭·채널 추가의 즉시 보상이 약하다는 신호로 해석한다.
- **전환 원칙**: 3문항 점검 결과는 채널 추가 없이 먼저 보여 준다. 전체 체크리스트 3종과 출시 알림은 카카오톡 채널 친구 추가의 보상이다. 학원을 좋음/나쁨으로 판정하지 않는다.
- **경로**:
  - `/` — 브랜드·문제 정의. 주 CTA는 `1분 학원 점검 시작하기` → `/check`. 카카오 CTA는 하단·모달에 유지하고 혜택을 체크리스트 3종+출시 알림으로 바꾼다.
  - `/check` — 로그인·개인정보 입력·AI·DB 저장 없는 정적 3문항. 답변은 브라우저 안에서만 처리한다.
  - `/checklists` — 모바일 웹 허브(PDF 없음). URL만 알면 볼 수 있다. 카카오 로그인이 없어 가짜 잠금은 두지 않는다. 보상은 웰컴메시지로 배포하는 것이다.
- **광고**: 당근 광고는 `/check`로 직접 연결한다. 점검 결과의 주 CTA는 `학원콕 알아보기` → `/?from=check`이며, 카카오 전환은 `/`에서 일어난다. 결과를 읽기 전에 홈으로 자동 보내지 않는다. `from=check`이면 히어로·스티키 CTA를 점검 재시작이 아니라 카카오 모달로 바꾼다.
- **판정 규칙**: `개선이 필요해요`가 하나라도 있으면 보완 필요. 그게 아니고 `잘 모르겠어요`가 있거나 `가끔 아쉬워요`가 2개 이상이면 일부 확인 필요. 나머지는 전반적으로 안정적.
- **계측**: `ClickEvent`에 랜딩 퍼널 예외를 둔다. 페이지뷰는 넣지 않는다. `click_logs.event`는 DB enum이 아니라서 마이그레이션 없이 값을 추가한다.
  - `mini_check_started` / `mini_check_completed` / `mini_check_result_viewed` / `mini_check_home_clicked`
  - `checklist_kakao_clicked` — `from=check` 경로의 카카오 CTA
  - `kakao_channel` — 푸터·유기 유입 카카오 CTA (유지)
- **바꾸지 않은 것**: 추천 API, 학원 JSON, 랭킹, 지도, 로그인, 상담 연결, AI provider, PDF.
- **카카오 웰컴메시지 (채널 관리자에서 설정, 코드 밖)**:

  > 안녕하세요, 학원콕입니다.
  > 현직 수학 학원 강사가 정리한 학원 선택·점검 체크리스트 3종을 보내드립니다.
  > 지금 학원을 알아보는 중인지, 다니는 학원을 점검하고 싶은지, 옮기기 전인지에 맞춰 필요한 자료를 골라보세요.

  | 버튼 | 연결 |
  | --- | --- |
  | 체크리스트 보기 | `https://academykok.netlify.app/checklists` |
  | 학원콕 알아보기 | `https://academykok.netlify.app/` |

  밤 20:55~익일 08:00 친구 추가는 다음날 오전 8시에 웰컴메시지를 받을 수 있으므로, 랜딩에는 “채널 추가 후 웰컴메시지로 보내드려요”라고 적는다.

## 2026-08-17 — 랜딩 스티키 트리거·CTA 보조 문구·모달 포커스를 코드 리뷰 기준으로 정정

- **계기**: `landingpage_correction` 리뷰에서 (1) CTA 보조 문구가 모달보다 넓고 (2) 스티키 센티널이 히어로 섹션 끝에 있어 CTA 지나침과 무관하고 (3) 모달에 포커스 트랩이 없어 스티키 버튼으로 Tab이 새는 문제가 나왔다.
- **CTA 보조 문구**: `개인정보 입력 없음`은 모달의 「이 화면에서 이름·연락처를 따로 입력받지 않습니다」보다 넓다. 카카오 채널 추가는 카카오 계정 처리가 있다. `무료 · 이름·연락처 입력 없음 · 언제든 차단 가능`으로 좁히고, 히어로·대기자 섹션·스티키가 `landingFacts.ts`의 `CTA_REASSURANCE`를 공유한다.
- **스티키 센티널**: 히어로 섹션 끝이 아니라 CTA 직후(`h-px`)에 둔다. 카드를 읽는 중에도 CTA가 화면 위로 나가면 바가 뜬다. 대기자 모달이 열려 있으면 바를 내리고 `inert`로 포커스·클릭을 막는다.
- **모달**: 라이브러리 없이 열릴 때 패널로 포커스, Tab을 패널 안에서만 순환, 닫힐 때 이전 요소로 복원. `/app` 학원 상세 모달에도 같은 `Modal`이 적용된다.
- **숫자 정본**: `MISA_ACADEMY_COUNT`가 `data/academies/*.json`의 주소 `"미사"` 건수와 다르면 `tests/test_landing_copy.py`가 실패한다.

## 2026-08-16 — 전환율 개선안 사실검증 후, 검증된 사실만 랜딩에 반영

- **계기**: 외부 전환율 개선 리포트를 인증(사실검증)한 결과, 인용 통계 16건은 원문과 모두 일치했으나
  **제안 카피에 실측이 아닌 숫자 2개**가 섞여 있었다. 그대로 반영하면 허위 표시가 된다.
  - “미사 학원 187곳” — 정본 어디에도 없는 숫자
  - “미사 학부모 47분이 기다리는 중” — 실측 아님
- **정본 전수 조사 결과 (`data/academies/*.json` 411개)**:

  | 필드 | 채움률 |
  | --- | --- |
  | `name` · `address` · `latitude` · `longitude` | 100% (411/411) |
  | `phone` | 67.9% (279/411) |
  | `subjects` · `level_*` · `class_*` · `curriculum_*` · `shuttle_available` · `tuition_monthly_fee` · `operating_hours` · `tagline` | **0% (전부 `null`)** |

  - 출처는 411개 전부 `경기데이터드림(학원 및 교습소 현황), 2026-07-10 변환`
  - 주소에 “미사” 포함 **410곳**, 나머지 1곳은 덕풍동 → 미사로 말할 때는 **410**을 쓴다
- **여기서 나온 카피 원칙**: **목록은 다 모았고 속성은 아직 하나도 없다.** 카피는 “모았습니다”까지만 간다.
  “정보 정리 완료”·“조건별로 비교”·현재형 “추려드립니다”는 속성 필드가 채워지기 전까지 쓰지 않는다.
  대신 “경기도 공공데이터 기준·등록 학원”이라는 한정을 붙여 정직한 hedge를 신뢰 신호로 쓴다.
- **반영한 변경 (검증된 사실만, `frontend/src/components/landing/` 한정)**:
  - CTA 보조 문구 `비용 없음 · 수강 신청/결제 아님 · 출시 소식만 안내` → `무료 · 이름·연락처 입력 없음 · 언제든 차단 가능`.
    새 약속이 아니라 `WaitlistModal`이 모달 안에서만 보여주던 사실 3개를 버튼 옆으로 끌어올린 것이다.
    (`개인정보 입력 없음`은 모달·카카오 처리보다 넓어 2026-08-17에 범위를 좁혔다.)
    직전 문구의 “출시 소식만 안내”는 혜택을 스스로 깎아내려 되돌린다.
  - 히어로 제목·서브를 실측 숫자(410곳) + 출처 명시로 교체
  - 헤더의 “정식 출시 준비 중” 배지 제거 (히어로 배지와 중복 — 스크롤 내내 부정 신호가 따라다녔다)
  - 유보 문구를 푸터 `Disclaimer` **한 곳으로 통합**. `HeroSection`·`PlannedFeaturesSection`의
    `Disclaimer`를 제거하되, 푸터에 없던 “중개·수강료 대리수납 없음”은 **삭제가 아니라 푸터로 옮겼다.**
  - “정식 출시 후 제공될 기능” → “출시하면 이렇게 쓰시게 됩니다”, “아직 이용하실 수 없습니다” 삭제(푸터와 중복)
  - 서비스 화면 예시에 “💡 왜 추천했나요?” 한 줄 추가 — 근거를 대는 것이 경쟁 서비스와의 유일한 차별점인데
    랜딩 어디에도 그 모습이 없었다. 단 “풍산동 · 소수정예 8명” 같은 **구체 속성은 넣지 않았다** (해당 필드 0%).
  - 모바일 하단 스티키 CTA(`StickyCtaBar`) 추가. **상단 고정 CTA는 두지 않는다** — 스티키가 있으면
    상단 CTA가 더하는 효과가 거의 없다(스티키 단독 +11% / 둘 다 +12%). 버튼은 기존 `WaitlistModal`
    흐름을 그대로 태워 `KakaoChannelLink`의 `kakao_channel` 계측을 우회하지 않는다.
- **일부러 반영하지 않은 것**:
  - **“광고비 낸 학원을 위로 올릴 이유가 없습니다”** — 향후 수익모델에 대한 약속이다. 광고 모델 배제가
    확정되기 전에는 쓰지 않는다. 확정되면 구현 비용 0으로 넣을 수 있다.
  - **대기자 수 노출** — 카카오 채널 관리자센터에서 실측한 뒤, 임계값을 넘을 때만 넣는다.
  - **추천·순번 시스템** — 카카오 채널 추가는 사용자 식별자를 주지 않아 순번을 매길 수 없다. 별도 폼을 만들면
    현재 최대 강점인 “입력 필드 0개”를 포기하게 된다. 트래픽이 붙은 뒤 재검토한다.
- **측정 현황 정정**: 리포트는 “측정 세팅”을 선행 과제로 봤으나 **분자는 이미 있다**
  (`KakaoChannelLink` → `POST /events {kakao_channel}`). 없는 것은 **분모(페이지뷰)** 다.
  트래픽 규모상 자체 계측을 새로 짓기보다 Netlify Analytics 활성화가 낫다. `ClickEvent`는
  “외부 행동 클릭”이므로 페이지뷰를 이 enum에 넣지 않는다.
- **다음 병목은 제품이다**: 속성 필드가 0%인 한 “조건으로 추려준다”는 약속은 카피로만 존재한다.
  전부 채울 필요는 없다 — **100곳만 채워도** “100곳은 과목·수업형태까지 확인했습니다”가 가능해지고
  예시 카드도 실제 조건으로 채울 수 있다.

## 2026-08-16 — 출시 알림 랜딩의 메시지 우선순위와 CTA 개선안 기록

- **배경**: Founder는 맘카페·당근 등에서 학부모가 반복적으로 남긴 질문을 통해, 부모가 원하는 것은 단순히 유명한 학원을 찾는 일이 아니라 **우리 아이에게 맞는 학원을 고르는 일**임을 확인했다. 현재 랜딩은 출시 전 상태와 광고 심사 안전장치를 명확히 알리지만, 첫 화면의 중심 메시지가 “출시 준비 중”이라 이 문제 해결 가치가 늦게 전달된다.
- **현재 디자인 평가**: 오프화이트 배경·네이비 본문·오렌지 CTA·여백 중심의 시각 체계는 따뜻하고 신뢰감 있으며, 카드와 CTA의 계층도 MVP 대기자 페이지로 충분히 정돈되어 있다. 전환 병목은 전면적인 리디자인이 아니라 **히어로 카피의 메시지 순서**와 **CTA가 수행하는 실제 행동의 불명확성**이다. 현재 로고 중심의 시각 구성과 길게 이어지는 고지는 광고 유입자에게 “왜 지금 알림을 받아야 하는가”를 약하게 만들 수 있다.
- **결정 및 구현**: 디자인 토큰·섹션 순서·출시 전 고지 원칙은 유지한다. 이번 작업에서는 `HeroSection`과 `WaitlistSection`의 카피·CTA만 최소 변경하고, 새 이미지 제작이나 페이지 구조 개편은 이 카피 변경의 전환 데이터를 본 뒤 별도로 판단한다.

  | 요소 | 권장 문구 | 목적 |
  | --- | --- | --- |
  | 히어로 제목 | **유명한 학원보다, 우리 아이에게 맞는 학원** | 학부모의 핵심 선택 욕구를 첫 인상에서 전달 |
  | 히어로 설명 | 맘카페·블로그·당근을 찾아보고 여러 학원을 직접 비교해도, 우리 아이에게 맞는 곳을 고르기는 쉽지 않습니다. 학원콕은 하남 미사 학원 정보를 바탕으로 아이의 학년·과목·학습 스타일에 맞는 선택을 도울 서비스를 준비하고 있습니다. | 탐색·비교 피로와 출시 후 가치를 연결 |
  | 주 CTA | **카카오톡으로 무료 출시 알림 받기** | 버튼 클릭 후 카카오 채널 추가가 일어남을 명확히 고지 |
  | CTA 보조 문구 | **비용 없음 · 수강 신청/결제 아님 · 출시 소식만 안내** | 상담·결제·과도한 연락에 대한 불안을 버튼 주변에서 즉시 해소 |

- **범위 안전장치**: 이 변경은 현 시점에 추천·비교·상담을 제공하는 것처럼 보이게 해서는 안 된다. `POST /waitlist`를 연결하지 않고, 알림 신청은 기존처럼 카카오톡 채널 추가 전용으로 유지한다. 서비스 화면 예시는 가상·정적·비대화형 상태를 유지하며, 실제 후기·라이브 학원 데이터·현행 `/app` 링크를 랜딩에 추가하지 않는다.
- **측정과 다음 작업**: 기존 `kakao_channel` 클릭 이벤트로 CTA 클릭의 변화를 확인한다. 카카오 내부의 실제 채널 추가는 직접 계측할 수 없으므로, 이 변경의 1차 판정 지표는 랜딩 유입 대비 카카오 채널 클릭률이다. 광고 문구·타깃·예산은 동시에 바꾸지 않고, 히어로 카피와 CTA만 변경한 뒤 충분한 광고 노출 표본에서 비교한다. 이번 구현 범위는 `frontend/src/components/landing/HeroSection.tsx`와 `WaitlistSection.tsx`의 카피 변경으로 한정했다.

## 2026-08-15 — 랜딩을 출시 전 대기자 페이지로 전환

- **계기**: 광고 심사가 랜딩을 운영 중인 중개/통신판매로 오인했다. 결제·수강계약·예약금
  기능은 원래 없지만, `/`의 현재형 카피와 `/app`으로 가는 “무료 이용” CTA가 그 인상을
  만들었다. 사업자등록번호·통신판매신고번호는 만들어 넣지 않는다.
- **`/`에서 `/app` 링크를 전부 제거**한다. `/app` 자체는 직접 URL로 접근 가능하게 두고,
  `frontend/src/app/app/page.tsx`에만 `noindex, nofollow`를 넣는다.
  (`frontend/src/app/page.tsx`는 랜딩 `/`이므로 여기에 noindex를 넣지 않는다.)
  `/app`의 기능·레이아웃은 바꾸지 않되, 헤더에 `/privacy` 링크 한 줄만 넣는다 —
  랜딩에서 링크를 없앤 뒤로 `/app` 이용자는 직접 URL로 들어온 사람뿐인데,
  `/privacy`가 고지하는 검색 기록 저장이 바로 그 사람에게 적용되기 때문이다.
- **랜딩은 `POST /waitlist`를 호출하지 않는다.** 알림 신청은 카카오톡 채널 추가 전용.
  백엔드 계약·테스트 9개·`docs/api.md`의 `/waitlist` 본문은 유지한다. “안 쓰는
  테스트”로 오해해 지우지 말 것. 프론트 `joinWaitlist`도 계약 유지용으로 남긴다.
- **`kakao_channel` 클릭 이벤트 추가.** `click_logs.event`는 DB enum이 아니라
  `String(50)`이라 Alembic 리비전이 필요 없다. 기존 행·클라이언트의 의미는 바뀌지 않는다.
- **KPI 변경**: 대기자 등록률을 `waitlist` 테이블로 재던 지표가 멈춘다. 실제 채널
  추가는 카카오톡 안에서 일어나 전환 확인이 불가능하고, 클릭 수만 남는다. 광고 심사를
  위해 감수하는 계측 후퇴다.
- **목업 미리보기(추천 카드·지도) 섹션을 만들지 않은 이유**: 동작하는 것처럼 보이는
  UI가 중개 서비스 오인의 원인이었고, 텍스트로 “출시 후 제공될 기능”만 적는 편이
  범위에 맞다. *(→ 아래 후속 항목에서 조건부로 번복)*
- **개인정보처리방침 `/privacy`**: 소개 페이지는 이메일·카카오 아이디를 받지 않는다.
  다만 `POST /waitlist` API와 기존 대기자 행은 남아 있으므로, 서비스 전체에
  “개인정보를 수집하지 않는다”고 쓰지 않고 예전 기록은 문의 시 확인·삭제한다고 밝힌다.
- **헤더 로고는 `/` 링크.** `/privacy`에서 랜딩으로 돌아갈 경로가 필요해서다.
- **푸터 디스클레이머는 범위를 나눠 쓴다.** 푸터를 `/`와 `/privacy`가 공유하는데, 처리방침
  본문은 `/app`이 동작하는 시험용 화면이라고 밝힌다. "출시 알림 신청만 가능"을 사이트 전체에
  걸면 그 본문과 모순되므로 **소개 페이지로 한정**하고, `/app`을 포함해 참인 "결제·수강
  계약·예약금 결제 없음"만 **사이트 전체**로 쓴다. 후자가 광고 심사에서 실제로 중요한 주장이다.
- **색 토큰을 hex에서 RGB 채널값으로 바꾼다.** 브라우저로 화면을 확인하다 다크 밴드의 고지
  문장 두 줄이 배경과 같은 색(`rgb(30,43,60)`)으로 렌더되는 걸 발견했다. 토큰이 hex라
  `text-surface/80`이 `rgb(#ffffff / 0.8)`이라는 무효 CSS가 되고, 선언이 버려져
  `body`의 상속색이 그대로 나온 것이다. 같은 이유로 모달 딤(`bg-ink/40`), 배지 배경
  (`bg-brand/15`), 입력 포커스 링(`ring-brand/30`) 등 **투명도 표기 12곳이 전부 조용히
  실패**하고 있었다. `tokens.css`를 채널값으로, `tailwind.config.ts`를
  `rgb(var(--x) / <alpha-value>)`로 바꿔 12곳을 한 번에 고쳤다 — 호출부를 개별 패치하는
  것보다 변경량이 작다. 랜딩 범위를 넘지만, 광고 심사용 고지 문장이 안 보이는 형태로
  드러난 버그라 이번에 처리했다.
- **후속(같은 날): `ServicePreviewSection` 정적 예시 카드를 추가한다.** 화면이 전혀 없으니
  방문자가 서비스를 인식하기 어렵다는 지적이 있었다. 위 "만들지 않기로 한" 결정을 뒤집되,
  그 결정의 이유(동작하는 UI로 오인)는 아래 조건으로 봉쇄한다: (1) `/app` 스크린샷이
  아니라 새로 만든 컴포넌트 — `data/academies/*.json` 미참조, 가상 학원명("OO수학학원"
  "△△영어학원", `docs/design/academy-kok-landing.html` 목업의 표기 관례를 따름)
  (2) `onClick`·`Link`·API 호출 전무 — 카드가 눌러도 반응하지 않는다 (3) 전화·상세·
  길찾기는 "정식 출시 후 제공" 텍스트로만 표시하고 버튼을 렌더하지 않는다 (4) 인용
  후기는 넣지 않는다 — 실제 리뷰처럼 보이는 텍스트를 지어내는 게 가상 학원명보다
  위험이 크다고 판단했다 (5) 섹션 상단에 "서비스 화면 예시", 카드 아래
  `<Disclaimer>`에 "실제 학원 정보가 아닌 예시" 표기. 배치는 `PlannedFeaturesSection`과
  `WaitlistSection` 사이 — 원래 지시서의 권장 흐름(문제 → 3단계 설명 → 화면 예시 →
  CTA)과 같다.
- **카카오 채널 클릭 계측은 `KakaoChannelLink` 컴포넌트 안에 둔다.** 모달 CTA와 푸터 링크가
  같은 URL로 나가는데 계측이 모달에만 있으면 KPI가 과소 집계된다. 링크에 붙이면 누락 경로가
  없다. 모달 인스턴스는 닫을 때 언마운트돼 재집계되고, 푸터 인스턴스는 **페이지뷰당 1건**이
  상한이다 — KPI 의미로는 이쪽이 맞다.

## 2026-08-14 — GitHub를 다중 AI 협업 허브로 (AGENTS.md 도입, 느슨하게)

- **문제**: ChatGPT(전략)·Claude(아키텍처/리뷰)·Cursor(구현)·Manus(조사/실행)를 함께 쓰는데,
  각 AI의 운영 규칙이 **각 도구의 설정 화면에만** 존재했다. AI끼리는 서로의 대화를 볼 수 없고
  세션이 끝나면 맥락이 사라지므로, 채팅창에만 남은 규칙과 결정은 다른 AI에게 없는 것과 같다.
  저장소에는 에이전트가 읽을 진입점 파일이 하나도 없었다(`AGENTS.md`/`CLAUDE.md`/`.github/` 부재).
- **결정**: 저장소 루트 **`AGENTS.md`를 에이전트 공통 메모**로 삼는다. 제품 범위, 역할,
  계층 규칙, 데이터 정본 원칙, API 계약, 검증 명령을 여기 모은다. 도구별 파일
  (`CLAUDE.md`, `.cursor/rules/project-context.mdc`)은 **얇은 포인터 + 역할 특이사항**만 두고,
  규칙 변경은 도구 설정이 아니라 이 파일 PR로 한다.
- **왜 `AGENTS.md`인가**: Cursor·Codex 등이 공통으로 읽는 관례 파일이고 Claude Code도 읽는다.
  도구별 규칙 파일 N개를 두면 반드시 서로 어긋나므로 **정본 1개 + 포인터 N개** 구조로 간다.
- **의도적으로 느슨하게 시작한다**: 초안에서는 인계 항목 8개와 계약 위반 체크리스트를 PR
  템플릿에 넣고 Issue 폼을 역할별 4종(required 필드 포함)으로 나눴는데, **아직 아무도 안 해본
  워크플로에 강제부터 거는 구조**였다. 규칙이 현실과 어긋나는 순간 통째로 무시되고, 그러면
  문서 전체의 신뢰가 같이 죽는다. 그래서 PR 템플릿은 자유 서술 5칸, Issue 템플릿은 markdown
  2종(작업/조사, 결정)으로 줄이고 required 필드와 라벨 의존을 없앴다. 운영해보고 실제로 빠지는
  항목이 생기면 그때 조인다.
- **다만 §7의 항목들은 남겼다**: 하드/소프트 추천 경로 분리, `score`의 상대값 성격,
  `scoring.py` 순수성, 세션 경계, 학원 사실 데이터의 추측 금지·`null` 원칙. 전부 실제로 버그가
  났거나 데이터 신뢰를 깨는 지점이라 "바꾸려면 이 로그를 먼저 읽으라"는 형태로 유지한다.
- **문서 증식 방지**: 새 문서는 `AGENTS.md`와 `docs/ai-team.md` 둘뿐이고 나머지는 기존 문서
  갱신으로 처리했다. `docs/project.md`가 "OpenAI 연동·RAG·Vector DB를 하지 않는다"고 적힌 채
  방치되어 Phase 4 구현 현실과 반대였으므로 정정했고, 반대로 **자유 대화형 채팅·SSE
  (`POST /chat`)는 미구현**임을 명시했다 — 로드맵 Phase 5 문구가 구현된 것처럼 읽힐 여지가
  있었는데 실제 `backend/app/api/`에 chat 라우터가 없다.
- **하지 않기로 한 것**: 에이전트별 규칙 파일 분산, GitHub Actions로 규칙 자동 검사(MVP 단계에선
  유지비만 늘고 검증 대상이 아직 유동적이다), 조사 결과 전용 디렉터리 신설(Issue + 이 로그로 충분).

## 2026-07-31 — AI 경로 소프트 필터 + 진짜 적합도 점수 (P1)

- **증상**: `POST /recommendations/ai`가 실데이터(`data/academies` 411건)에서 항상 빈 배열.
  `level_*`/`class_*`/`curriculum_*`/`shuttle`/`tuition`/`subjects`가 **0/411 non-null**인데
  `_apply_filters`의 `.is_(True)`가 NULL(미확인)을 배제하기 때문. 동시에 `_score()`는
  파싱된 필터 **개수**만 세어 한 응답 안 모든 항목이 동일 점수였다.
- **결정**: AI 경로만 "넓은 후보 풀 + 랭킹"으로 전환. SQL 하드 필터는 `region`/`q`뿐이고
  3상태·예산은 `services/scoring.py`에서 채점한다 (`True`=+1, `False`=−2, `None`=0).
- **하드 엔드포인트는 유지**: `POST /recommendations`는 `docs/api.md`에 문서화된 계약이므로
  한 줄도 건드리지 않는다. 명시적 필터 UI·디버그용으로 계속 쓸모 있다.
- **과목 추출은 `scoring.py`에**: `RecommendationRequest`/`intent.py`에 넣으면 하드
  엔드포인트가 조용히 무시하는 유령 파라미터가 생기고, 추정 과목이 SQL WHERE로 샐 수 있다.
  scoring에 가두면 구조적으로 불가능. 키는 추정 신호임을 드러내도록 `"subject"`(단수).
  이름에 "수학"이 있다고 `subjects` 컬럼을 채우지 않는다 — 2026-07-31 휴리스틱 원칙의 구현.
- **완화 사다리**: 남는 하드 필터가 region/q뿐이므로 `q` → `region` 2단.
  (마스터 플랜의 budget→level→region 은 소프트화 이후 죽은 코드가 되어 폐기.)
- **`list_candidates`의 name_like 정렬 힌트**: region="미사"면 ~410행이 매치되는데
  `ORDER BY name LIMIT 200`은 가나다순 앞쪽만 채점한다. 과목 토큰이 이름에 든 행을
  풀 앞으로 올려 실버그를 막는다. `_apply_filters`와 절이 겹쳐도 **의도적 비공유** —
  두 계약을 다시 결합하는 DRY 리팩터를 하지 말 것.

## 2026-07-31 — 채팅+지도 웹 UI 및 리뷰 수집 착수: 범위·경로 결정

- **프론트엔드 스택을 Next.js(App Router) + TypeScript로 확정**: `README.md`/`docs/roadmap.md`의
  "Next.js vs Flutter 미정"을 여기서 종결한다. 화면 목표가 왼쪽 ChatGPT류 스트리밍 채팅 +
  오른쪽 지도인데, SSE 소비·지도 SDK 연동·향후 SEO 확장성 모두 React 생태계가 가장 무난하고,
  `.gitignore`에 이미 있던 Flutter 전용 블록은 이번에 Node 전용 블록으로 교체한다.
- **리뷰 소스를 네이버 플레이스 크롤링에서 네이버 개발자센터 공식 검색 API로 전환**:
  처음엔 오픈소스 크롤러를 붙이려 했으나 조사 결과 자체 호스팅 가능한 네이버 플레이스
  크롤러가 전부 방치 상태였다(`chalkpe/naver-place`는 2019년 아카이브에 리뷰 기능 자체가
  없음, `omnyx2/naver_place_crawling`은 라이선스 없음+README에 "현재 정상 작동하지 않습니다"
  명시, `seolhalee/Naver-Place-scraper`는 place id 추출만). 유지보수되는 건 Apify 같은
  상용 SaaS뿐이고 그마저 플레이스 전용이라 맘카페류 지역 카페를 다루지 못한다.
  지역 맘카페 직접 수집(로그인)도 검토했으나, 지역 맘카페는 본인 인증+거주 확인+등업이
  필요한 **로그인 담벼락 뒤**라 `docs/data-strategy.md` 수집 원칙 1번("공개된 사실만
  수집한다")에 정면으로 어긋나고 계정 약관·개인정보·학원 항의 리스크가 모두 크다.
  → **네이버 검색 오픈 API의 `cafearticle`(카페글, 공개 설정된 글만 색인)과 `blog`
  엔드포인트**로 대체. 무료 25,000회/일, ToS상 완전 합법, 크롤링이 아니라 공식 API 호출이다.
  `local`(지역검색) 엔드포인트는 리뷰가 아니라 학원 매칭·정본 보강(subjects/phone 채우기)에
  쓴다. 상세 계획은 세션 플랜(`P4`/`P5`) 참고.
- **수집은 실시간 폴링이 아니라 오프라인 배치**: 학원 리뷰는 분 단위로 바뀌지 않고,
  지속 폴링은 봇 트래픽 패턴만 명확해져 리스크 대비 실익이 없다. `--dry-run`/`--from-raw`를
  갖춘 CLI로 일/주 단위 재실행하는 구조로 간다 (`import_academies`/`convert_registry` 관례와
  동일선상).
- **`description` 필드는 스니펫(~200자)이지, 리뷰 전문이 아니다** — 원문 전체를 얻으려면
  결국 별도 크롤링이 필요한데 그 순간 위 결정의 합법성 이점이 사라지므로 의도적으로
  하지 않는다. 화면에는 이 스니펫들을 근거로 한 LLM 요약만 노출하고, 원문 자체는 절대
  git에 커밋하지 않으며(`data/raw/`, gitignored) UI에도 노출하지 않는다.
- **핵심 원칙**: 휴리스틱(과목 추정 등)은 런타임 랭킹(`scoring.py`)에만 반영하고,
  `data/academies/*.json`(git 정본)에는 검증된 사실만 쓴다 — 학원 이름에 "수학"이 들어간다고
  `subjects`를 추측해 파일에 쓰지 않는다. 추측 금지 원칙과 랭킹 정확도를 동시에 만족시키는
  방법이다.

## 2026-07-29 — `PgVectorStore.search()`의 `cosine_distance()` AttributeError 수정

- **증상**: `Review.embedding.cosine_distance(embedding)`을 호출하면 postgres
  dialect에서도 `AttributeError: Neither 'InstrumentedAttribute' object nor
  'Comparator' object associated with Review.embedding has an attribute
  'cosine_distance'`가 난다. `Review.embedding`이
  `JSON().with_variant(Vector(dim), "postgresql")`로 이중화되어 있는데,
  `with_variant()`는 DDL/바인드·결과 처리만 dialect별로 바꿔치기하고, `.cosine_distance()`
  같은 비교자를 제공하는 `comparator_factory`는 원본(JSON) 타입에 그대로 고정되기
  때문 — dialect와 무관하게 항상 재현된다.
  - **발견 경위**: `tests/test_pgvector_store.py`가 `PGVECTOR_TEST_DATABASE_URL`
    없이는 통째로 스킵되도록 되어 있어 기본 `pytest`(SQLite)로는 이 경로가 전혀
    실행되지 않았다 — 실제로 main 전체 스위트는 이 버그가 있는 채로도 계속
    통과해 왔다. 별도 세션에서 같은 기능(Phase 4b 임베딩/VectorStore)을 중복
    구현하다가 로컬에서 `uv run`으로 실제 provider 환경을 재현해보며 발견했다.
- **조치**: `Review.embedding.op("<=>", return_type=Float)(embedding)`으로 pgvector의
  코사인 거리 연산자를 직접 호출하도록 변경 (`app/providers/pgvector_store.py`).
  우변 바인드 파라미터는 여전히 컬럼과 같은 Variant 타입을 가지므로, 실행 시점에는
  postgres dialect_impl(Vector)의 bind_processor가 정상 적용된다.
- **테스트**: 실 Postgres 없이도 이 버그를 잡을 수 있도록 `tests/test_pgvector_store_query.py`를
  추가 — 가짜 세션(context manager)으로 `search()`를 호출해 거리 표현식을 만드는
  단계까지 DB 연결 없이 검증한다(표현식 생성 자체가 문제였으므로 DB 연결 여부와
  무관하게 재현/검증 가능). 기존 `tests/test_pgvector_store.py`(실 Postgres 필요,
  opt-in)는 그대로 유지.

## 2026-07-27 — OpenAI 임베딩 + pgvector VectorStore 실연동 (Phase 4b)

- **임베딩 provider로 한국어 특화 모델(KURE-v1, bge-m3) 대신 OpenAI
  `text-embedding-3-small`을 채택** (`app/providers/openai_embedding.py`의
  `OpenAIEmbeddingProvider`): 한국어 리트리버로 정평이 난 `nlpai-lab/KURE-v1`과
  config 기본값이던 `BAAI/bge-m3`도 검토했으나 (1) Hugging Face Inference
  Providers 무료 티어는 월 $0.10 크레딧 수준이라 실사용에 부적합하고 PRO($9/월)
  구독이 필요하며, (2) 로컬 실행은 `sentence-transformers`+`torch`(~1-2GB) 설치와
  모델 가중치 다운로드가 필요해 소규모 단일 큐레이터 프로젝트의 컨테이너 배포에
  부담스러움. OpenAI는 이 데이터 규모(학원 82건+리뷰)에서 실비용이 사실상
  0에 가깝고(1M 토큰당 $0.02) 추가 의존성도 없어 최종 선택.
- **`text-embedding-3-small`을 `dimensions=1024`로 요청해 truncate**: 네이티브
  차원은 1536이지만 v3 모델은 요청 시 Matryoshka truncation을 지원해 원하는
  차원을 지정할 수 있음 — 기존 `EMBEDDING_DIM=1024`/migration `0003`을 그대로
  유지하고 스키마 변경을 회피. `Groq`와 동일하게 SDK 없이 `httpx.post`만으로 호출.
- **`PgVectorStore`(`app/providers/pgvector_store.py`)는 `VectorStore` Protocol을
  변경하지 않고 자체 세션으로 동작**: `search()`/`add()`는 `db` 세션을 받지
  않는데, 호출부(`ai_recommendation_service._evidence_for`)에는 세션이 있지만
  포트 시그니처에 인프라 관심사(세션)를 끌어들이지 않기 위해 `PgVectorStore`가
  `app/db/session.py`의 `engine`에 바인딩된 자체 `sessionmaker`로 호출마다 짧은
  세션을 연다. 별도 벡터 인덱스 테이블 없이 `reviews.embedding` 컬럼을 직접
  조회/갱신하므로 `add()`는 신규 삽입이 아니라 id 기준 UPDATE 의미다(존재하지
  않는 id는 조용히 무시 — ingest는 항상 실제 id를 쓰므로 안전).
- **리뷰 임베딩 백필은 스크래핑 파이프라인이 아니라 최소 CLI**
  (`app/services/review_embedding_service.py` + `app/cli/ingest_review_embeddings.py`,
  `import_academies.py`와 동일한 서비스/CLI 분리 구조): `data/`에 리뷰 원본이
  전혀 없어 지금은 DB에 이미 존재하는 `embedding IS NULL` 행을 채우는 용도로만
  범위를 한정. 실제 리뷰 수집·적재 파이프라인은 별도 다음 단계.
- **`docker-compose.yml`의 `db` 이미지를 `postgres:16` → `pgvector/pgvector:pg16`으로
  교체**: 기존 plain Postgres 이미지에는 `vector` extension 바이너리가 없어
  migration `0003`의 `CREATE EXTENSION IF NOT EXISTS vector`가 실패함.
- **`pyproject.toml`은 변경하지 않음**: `httpx`, `pgvector>=0.3`(SQLAlchemy
  `cosine_distance()` comparator 포함), `psycopg[binary]`로 충분해
  `sentence-transformers`/`torch`/OpenAI SDK 추가를 의도적으로 회피.
- **pgvector 통합 테스트는 실제 Postgres가 필요해 스킵 처리**
  (`tests/test_pgvector_store.py`, `pytest.mark.skipif`로
  `PGVECTOR_TEST_DATABASE_URL` 미설정 시 스킵 — 저장소 최초의 skip 패턴): 기본
  CI는 SQLite 기반(`Review.embedding`이 JSON variant)이라 `cosine_distance()` SQL이
  동작하지 않음. `OpenAIEmbeddingProvider`는 Groq 테스트와 동일하게 `httpx.post`를
  monkeypatch해 일반 CI에서 검증.

## 2026-07-22 — Groq(Llama)로 첫 실제 LLM provider 연동 (Phase 4b)

- **LLM provider로 OpenAI 대신 Groq를 우선 채택** (`app/providers/groq.py`의
  `GroqLLMProvider`): 무료 티어로 Llama 계열 모델을 바로 쓸 수 있어 비용 없이
  실제 LLM 호출 경로를 검증할 수 있음. `LLMProvider` 포트만 만족하면 되므로
  기존 `ai_recommendation_service._build_reason` 등 호출부는 무변경 —
  `LLM_PROVIDER=groq`로 config만 바꾸면 교체된다.
- **별도 SDK 없이 `httpx.post`로 직접 호출**: Groq Chat Completions가 OpenAI와
  동일한 REST 스펙(`/chat/completions`, `Authorization: Bearer`, `{model,
  messages}`)이라 SDK 의존성을 추가할 필요가 없음. `httpx`는 기존에 dev
  전용이었으나 런타임에서 실제로 쓰이므로 `pyproject.toml` 메인 의존성으로 승격.
- **범위를 LLM 호출부로만 한정, 임베딩/VectorStore는 이번에도 stub 유지**:
  Groq는 임베딩 API를 제공하지 않고, RAG 근거검색(pgvector)은 별도 결정이 필요한
  더 큰 작업이라 이번 변경과 분리. `parsed_intent` 단계도 여전히 규칙 기반
  (`intent.parse_intent`)으로 미변경.
- **API 키 없이도 기존처럼 무설정 기동**: 기본값(`LLM_PROVIDER=stub`)은 그대로
  두고, 사용자가 `.env`에 `GROQ_API_KEY`를 직접 넣고 `LLM_PROVIDER=groq`로
  바꿔야 활성화되는 opt-in 구조 유지. 키 없이 `groq`로 호출 시엔 Groq API가
  401을 반환하고 그대로 전파(별도 방어 코드 없음) — 네트워크/인증 실패는
  시스템 경계이므로 서비스 계층에서 감추지 않는다는 기존 원칙과 일관.

## 2026-07-14 — PR 머지 후 자동수정 커밋이 main을 손상시킨 사고 (PR #7 → #8)

- **증상**: PR #7(AI 추천 스켈레톤 + engagement API) 머지 시 자동으로 붙은 "Potential fix
  for pull request finding" 정리 커밋 3개 중 하나가 `ai_recommendation_service.py`의
  `_build_reason()`에서 `messages = [` 대입문을 실수로 삭제했다. 이후 dict 리터럴들이
  고아 표현식이 되고 `return llm.chat(messages)`의 `messages`가 미정의로 남아, **main이
  `python -m py_compile` 단계부터 실패하는(IndentationError) 상태로 머지됐다**.
  같은 커밋 묶음의 다른 두 수정(intent.py 정규식 개선, api.md 문구)은 정상이었다.
- **발견 경위**: 다음 세션을 시작하며 "머지했으니 기록하고 넘어가자"는 요청을 받고, 무작정
  기록만 하지 않고 `origin/main`을 fetch해 실제 diff를 점검하다가 컴파일 확인으로 발견.
  **PR 머지 완료 = 검증 완료가 아니다**라는 교훈 — 자동 정리 커밋이라도 병합 후 반드시
  `py_compile`/`pytest`로 확인한다.
- **조치**: `fix/ai-recommendation-syntax` 브랜치(PR #8)로 삭제된 대입문 한 줄만 복구,
  `pytest`(78 passed)·앱 임포트·`POST /recommendations/ai` 실호출로 검증 후 머지.
  최소 diff 원칙 준수(다른 정상 변경분은 손대지 않음).

## 2026-07-14 — AI 추천 엔드포인트 스켈레톤 + engagement API (Phase 4b-skeleton / 4c)

- **자연어 추천(`POST /recommendations/ai`)을 provider 포트 경유 파이프라인으로 구현**
  (`ai_recommendation_service.recommend`): 질문 기록 → 의도 분석 → 필터 → 벡터 근거 검색
  → 추천 이유 생성. 기본 provider가 전부 stub이라 키·비용 없이 end-to-end 동작하고,
  실제 임베딩/LLM/pgvector·LlamaIndex는 config만 바꿔 교체된다.
- **의도 분석은 규칙 기반이 현재 기본 구현** (`app/services/intent.py`의 `parse_intent`):
  stub LLM은 구조화 출력을 못 하므로, 학년/커리큘럼/수업형태/지역/예산을 키워드로 뽑아
  기존 `RecommendationRequest`로 변환한다. 순수 함수라 LLM 기반 파서로 저비용 교체 가능.
- **필터링은 기존 `academy_repository.list_recommendations`를 그대로 재사용** — 규칙 기반
  추천 로직을 중복 구현하지 않고 AI 파이프라인의 후보 선별 단계로 흡수.
- **RAG 근거 검색은 `vector_store.search()` 포트로만 호출**: 리뷰 ingest 파이프라인과 실제
  pgvector 스토어는 4b로 이연했으므로, 지금은 stub in-memory 스토어가 비어 있어 근거가
  빈 배열일 수 있다. 포트 호출 경로는 완성돼 실제 스토어로 갈아끼우면 그대로 동작.
- **engagement 쓰기 API(`/events`,`/feedback`,`/waitlist`)는 승인된 DB 직접 쓰기 예외**:
  `data-strategy.md`가 사용자 행동/리뷰 데이터를 git 정본이 아닌 DB 직접 쓰기로 규정한 것과
  일관. KPI(외부 행동률·대기자 등록률) 측정이 MVP 검증 목표(§5)의 핵심이라 우선 구현.
- **`/events`는 없는 `academy_id`에 404, 잘못된 `event` enum에 422**: 기존 `academies.py`의
  404 관례(존재 검증 후 HTTPException)와 Pydantic enum 검증을 각각 재사용. `academy_id`는
  nullable이라 학원 무관 이벤트도 허용.
- **`/waitlist`는 email/kakao 중 최소 하나 필수** (`model_validator`): 연락 수단 없는 등록을
  막아 대기자 데이터의 유효성을 보장.

## 2026-07-14 — AI 기반 골격: provider 추상화 + 리뷰·engagement 스키마 (Phase 4a)

- **얇은 Protocol 포트 채택** (`app/providers/base.py`): `EmbeddingProvider`/`LLMProvider`/
  `VectorStore`를 `typing.Protocol`로 정의하고 서비스 계층은 이 포트에만 의존한다.
  - 이유: 사용자 요구("기술스택·API를 상황에 따라 교체 가능하게")의 실체는 모델
    provider·벡터 스토어의 교체다. 얇은 포트 + config 선택(`factory.py`) 방식이 기존
    계층형(api/service/repository) 구조와 정합하고 의존성을 최소화한다.
- **기본 provider는 전부 stub** (`stub.py`): 실제 LLM/임베딩 호출 없이 결정적 구현으로
  파이프라인 골격만 검증. API 키·비용 0, 무설정 기동. 테스트 안정성 확보(결정적).
- **LlamaIndex는 다음 단계(4b)에서 `RagEngine` 포트 뒤에 채택**: LlamaIndex 자체가
  llm/embed_model/vector_store를 플러그블하게 다루므로 "핵심 엔진 채택"과 "교체 가능"이
  충돌하지 않는다. 엔진조차 단일 포트 뒤에 두어 교체 비용을 낮게 유지한다. 이번 단계에는
  llama-index/openai/sentence-transformers 의존성을 **추가하지 않음**.
- **리뷰·engagement 테이블 신설 + pgvector 도입** (마이그레이션 `0003`):
  `reviews`(임베딩 포함) / `search_history` / `click_logs` / `feedback` / `waitlist`.
  이 테이블들은 학원 사실(Fact) 테이블과 달리 **git 정본이 아닌 DB 직접 쓰기**다
  (`data-strategy.md` Phase 2 AI 요약 / Phase 3 사용자 데이터, engagement=런타임 로그).
- **`embedding` 컬럼은 이중화**: `JSON().with_variant(Vector(dim), "postgresql")` — 기존
  `academy.SubjectsJSON` 관례 재사용. SQLite 테스트는 JSON, 운영 postgres는 pgvector.
  마이그레이션은 dialect 가드(`op.get_bind().dialect.name`)로 postgres에서만 확장/Vector 생성.
- **`embedding_dim` 고정(기본 1024) = 마이그레이션 결합**: pgvector 컬럼 차원은 DDL 시점에
  고정되므로 임베딩 모델을 차원이 다른 것으로 바꾸면(예: bge-m3 1024 → OpenAI 1536)
  마이그레이션이 필요하다. 이 트레이드오프를 인지하고 기본값을 config로 노출.
- **ANN 인덱스(ivfflat/hnsw)는 이번에 만들지 않음**: 인덱스는 데이터가 쌓인 뒤 파라미터
  튜닝이 필요하므로 실제 RAG 단계(4b)로 이연. 지금은 컬럼만 준비.

## 2026-07-10 — 하남 미사 실데이터 전량 재수집 (CSV 업로드, 411건)
- **1차 수집(82건, 대화창 수기 입력)의 한계 해소**: 746건 전체를 채팅으로 옮겨
  적는 방식은 비현실적이라 일부(미사 주소 위주 선별)만 반영됐었다. 사용자가
  경기데이터드림 포털에서 하남시 조회 결과를 **CSV로 다운로드해 첨부**하면서
  746건 전체를 정확히 확보할 수 있었다.
- **CSV는 CP949(EUC-KR 계열) 인코딩** — `file` 명령이 이를 ISO-8859로 오탐지할
  정도로 흔한 함정. `encoding="cp949"`로 읽어야 한글이 깨지지 않는다.
- **CSV 헤더(한글)는 기존에 확정한 실제 API 필드명(영문)과 1:1 대응**:
  `시군명`→`SIGUN_NM`, `업종구분명`→`INDUTYPE_DIV_NM`, `시설명`→`FACLT_NM`,
  `교습과정명`→`CRSE_CLASS_NM`, `전화번호`→`TELNO`, `소재지우편번호`→`REFINE_ZIP_CD`,
  `소재지지번주소`→`REFINE_LOTNO_ADDR`, `소재지도로명주소`→`REFINE_ROADNM_ADDR`,
  `WGS84위도`→`REFINE_WGS84_LAT`, `WGS84경도`→`REFINE_WGS84_LOGT`. 등록번호 필드는
  CSV에도 없음 — 이 데이터셋엔 등록번호가 없다는 기존 추정이 다시 확인됨.
- **CSV → data.go.kr 표준 JSON 봉투로 1회성 변환** (스크래치패드 스크립트, 저장소에
  커밋하지 않음) 후 `data/registry/hanam-gg.json`으로 저장 — 기존 `extract_rows()`/
  `gg_row_to_record()`를 코드 변경 없이 그대로 재사용. 파싱된 746건은 API의
  `list_total_count`와 정확히 일치.
- **`convert_registry.py --source gg --filter 미사` 재실행**: 기존 82건은 자연키
  (이름+주소) 매치로 `load_existing_keys()`가 인식해 덮어쓰지 않고 스킵, 신규
  329건만 추가 생성 → 총 411건. 오류 0건.
- 업로드된 CSV 원본 파일은 세션 임시 업로드 경로에만 존재하며 저장소에는 포함하지
  않는다 (원본은 `data/registry/hanam-gg.json`으로 이미 변환·보관됨).

## 2026-07-10 — 하남 미사 실데이터 1차 수집 (gg 단일 소스)
- **경기데이터드림(gg) `SIGUN_NM=하남시` 서버측 필터로 하남시 전체 746건 확보**
  (사용자가 직접 API 호출; 승인 전 키는 파라미터를 무시하는 샘플 키 고정 응답이었고,
  포털에서 정식 승인 후 재호출하여 정상 필터링 확인). `SIGUN_CD`는 실제 데이터에
  값이 비어 있어 필터로 쓸 수 없었다 (`SIGUN_NM`만 사용).
- **NEIS 골격 없이 gg 단일 소스로 진행**: 사용자가 NEIS API 키를 보유하지 않아
  2-소스 순차 워크플로(나이스 골격 → gg enrich) 대신 gg만으로 신규 파일을 생성.
  자연키는 등록번호 없이 이름+주소만 사용 (gg 데이터셋에 등록번호 필드가 없다는
  기존 문서의 추정과 일치).
- **과목(수학) 필터링을 이번 수집에서 강제하지 않음**: `CRSE_CLASS_NM`(교습과정명)이
  "종합(대)"·"입시.검정 및 보습" 같은 넓은 카테고리라 "수학" 키워드로 정확히
  걸러내기 어려움을 확인. 대신 지역(`--filter 미사`, 주소 부분 일치)만 적용해
  미사 지역 학원을 과목 무관하게 전부 수집하고, 수학 학원 여부는 이후 별도 단계
  (LLM/RAG 기반 후처리)에서 가려내기로 함. `subjects`는 원래도 자동 채움 대상이
  아니라 수동 큐레이션 영역이라 이 결정이 3상태 원칙과 충돌하지 않는다.
- **원본 API 응답은 이 세션의 대화 relay를 통해 전달받아, 전량(746건) 대신 주소에
  "미사"가 포함된 학원 위주로 선별해 `data/registry/hanam-gg.xml`에 저장** —
  세션이 `*.go.kr`에 직접 접근할 수 없어 사용자가 대화창에 응답을 붙여넣는 방식
  으로 전달했고, 746건 전체를 한 글자씩 옮기는 대신 실질적으로 `--filter 미사`를
  통과할 주소만 우선 선별해 입력량을 줄였다 (변환 결과 82건 생성, 43건 필터 제외 —
  일부는 의도적으로 선별 단계에서 이미 걸러졌고 일부는 CLI의 이름+주소 필터를
  통과하지 못함).
- **기존 "(예시)" 개발용 픽스처 4개를 삭제**하고 위 82건으로 교체 (`data/README.md`
  에 이미 명시된 트리거 조건 충족).
- **`tests/test_importer.py`의 하드코딩된 `4`를 파일 개수 기반 동적 계산으로 변경**:
  정본 픽스처 개수가 예시 4건에서 실데이터 82건으로 바뀌며 기존 테스트가 깨짐 —
  향후 데이터가 늘어나도 테스트가 픽스처 개수와 독립적으로 유지되도록 수정.

## 2026-07-08 — gg(경기데이터드림) API 실제 응답 확인 및 필드명 확정
- **실제 서비스키로 `https://openapi.gg.go.kr/TninsttInstutM` 호출해 응답 확보**
  (사용자가 직접 브라우저로 호출; 이 Claude Code 세션은 조직 네트워크 정책상
  `*.go.kr` 아웃바운드가 차단되어 있어 세션 내에서는 호출 불가했음).
  응답은 `INFO-000`(정상 처리) XML, `list_total_count=34012`.
  서비스키는 코드/git 어디에도 포함하지 않았다 (수동 다운로드 워크플로 유지).
- **`gg_row_to_record()`의 best-effort 후보 키를 실제 필드명으로 확정**:
  `FACLT_NM`(시설명) / `REFINE_ROADNM_ADDR`·`REFINE_LOTNO_ADDR`(주소) /
  `TELNO`(전화번호, 기존 추측이 우연히 맞았음) / `REFINE_WGS84_LAT`·
  `REFINE_WGS84_LOGT`(좌표, 기존 추측이 맞았음) / `CRSE_CLASS_NM`(교습과정명).
  등록번호·등록상태 필드는 응답에 없음을 확인 — 기존 문서의 추정이 맞았음
  (자연키는 이름+주소만 사용, 상태 기준 필터링은 적용 안 됨)
- **XML 입력 파싱 지원 추가** (`convert_registry.py`의 `parse_xml_payload()`):
  이 API는 `Type=json` 파라미터를 줘도 XML로 응답함이 확인됨. 새 XML을
  기존 "나이스류" JSON 봉투 구조로 변환해 `extract_rows()`를 그대로
  재사용하도록 구현 — 별도 파싱 경로를 늘리지 않고 기존 로직 재사용
- **범위를 필드명 수정 + XML 파싱까지로 한정**: 앱이 이 API를 자동으로 호출하는
  기능(서비스키 설정, 라이브 HTTP fetch)은 이번에 추가하지 않음 — 기존과 동일하게
  "사람이 포털에서 수동 다운로드 → CLI로 변환" 워크플로 유지 (data-as-git 원칙과
  일관, 자동 호출은 필요해지면 별도로 검토)

## 2026-07-08 — Phase 3 추천 API: 예산·지역 필드 처리
- **`tuition_monthly_fee`(월 수강료, nullable Integer) 컬럼 신규 추가**
  - 이유: Phase 3 추천 조건 중 "예산"을 지원하려 했으나 기존 스키마/정본 데이터
    어디에도 수강료 필드가 없었음. 3상태 Boolean과 달리 수치형이라 "확인됨-없음"
    상태는 없고 `NULL`=미확인만 존재
  - 예산 필터(`budget_max`)는 `tuition_monthly_fee IS NOT NULL AND <= budget_max`로
    구현 — 기존 tri-state Boolean 필터가 `IS TRUE`/`IS FALSE`로 미확인(`NULL`)을
    제외하는 것과 동일한 관례를 수치 필드에도 적용
- **지역(region) 필터는 구조화된 컬럼을 만들지 않고 `address` 부분 문자열
  매칭으로 처리**
  - 이유: 현재 전 데이터가 미사동 단일 지역 예시라 구조화 이득이 적음.
    `data-strategy.md`의 "비파괴적 확장" 원칙에 따라 다지역 확장이 실제로
    필요해질 때 nullable `region`/`dong` 컬럼을 추가하면 되므로 지금 선반영하지 않음
- **`RecommendationRequest`는 `AcademyListParams`를 상속**하여 기존
  `GET /academies` 필터(level/class_type/curriculum/shuttle/q)를 그대로 재사용하고
  `region`/`budget_max` 2개만 추가 — 필터 빌더(`academy_repository._apply_filters`)
  중복 없이 `_apply_recommendation_filters`에서 감싸는 방식으로 확장

## 2026-07-07 — 공공데이터 2-소스 확장 (나이스 + 경기데이터드림)
- **경기데이터드림 "경기도_학원 및 교습소 현황" API를 나이스와 함께 지원**
  (`convert_registry.py --source {neis,gg}`)
  - 이유: 나이스(acaInsTiInfo)에 없는 전화번호·좌표(위경도)·교습과정명을 제공,
    두 소스가 상호보완적 (나이스는 등록번호·개원년도·폐원상태가 강점)
- **`--enrich` 모드 도입**: 자연키가 매치되면 null 필드만 채우고 이미 채워진
  값은 절대 덮어쓰지 않음 — 두 소스를 순차 실행(나이스 골격 생성 → gg로 보강)
  하는 워크플로를 지원
- **상태 필터를 "개원과 일치" → "폐원류 키워드 미포함"으로 변경**
  - 이유: 구현 중 실제로 발견한 버그 — gg 소스의 상태 값 어휘를 정확히 알 수
    없는데 나이스 전용 값("개원")과의 동등 비교를 그대로 쓰면 gg 데이터가
    전부 걸러질 뻔했음. 폐원/폐업/휴원 키워드 포함 여부로 판단해 미확인
    어휘에도 안전하게 기본 포함되도록 수정
- **gg 소스 필드명은 미확정 상태로 문서화 후 진행**: 포털 봇 차단으로 실제
  응답 확인 불가 → 후보 키를 여러 개 시도하는 방식으로 구현하고 실 응답
  확보 시 한 곳(`gg_row_to_record`)만 고치면 되도록 격리

## 2026-07-06 — Fact DB 전략 및 스키마 결정
- **제품 전략**: 평가/리뷰 대신 객관적 사실(Fact)만 모으는 DB 우선
  (Phase 1 사실 → Phase 2 AI 요약 → Phase 3 사용자 리뷰, `docs/data-strategy.md`)
  - 이유: 객관성 유지, 학원 항의 리스크 회피, 수집·업데이트 용이. 정확한 DB 자체가 자산
- **3상태 nullable Boolean** (초/중/고, 수업형태, 커리큘럼, 차량): `NULL`=미확인 / `FALSE`=확인됨-없음 / `TRUE`=확인됨-있음
  - 이유: ARRAY 컬럼은 "없음"과 "미확인"을 구분하지 못함 — 이 구분이 "가장 정확한 DB"의 본질.
    부수 효과로 SQLite 테스트 호환 확보. 어휘가 작고 안정적이라 컬럼-값 방식이 저렴
- **data-as-git**: 정본은 `data/academies/*.json`, DB는 멱등 임포터로 재구성되는 파생 저장소. 쓰기 API 없음
  - 이유: PR 리뷰·이력·출처 추적을 git이 제공. 소규모 단일 큐레이터 데이터셋에 적합.
    Phase 3 사용자 리뷰는 예외(DB 직접 쓰기)
- **int autoincrement PK** (UUID 대신): 공개 데이터라 열거 우려 없음, 환경 간 식별은 자연키
  (registration_number, name+address)가 담당
- **수작성 초기 마이그레이션** + `Base.metadata` 네이밍 컨벤션 도입 (테이블 0개인 지금이 무통증 시점)
- **드라이버 스킴 수정**: `postgresql://` → `postgresql+psycopg://`
  - 이유: psycopg v3만 설치되어 있는데 기본 스킴은 psycopg2 dialect로 해석되어 DB 사용 시점에 크래시
- **공공데이터 부트스트랩**: 나이스 학원민원서비스 변환기는 신규 파일 생성 전용
  (기존 파일은 절대 덮어쓰지 않음 — 수동 큐레이션 보호)

## 2026-07-03 — 초기 기술 스택 결정
- **Backend**: FastAPI + SQLAlchemy + Alembic + PostgreSQL + uv + Pydantic Settings
  - 이유: 빠른 개발 속도, 타입 안정성, 향후 AI(OpenAI API) 연동 용이성
- **패키지 관리**: uv 채택
  - 이유: 빠른 의존성 해석/설치, 최신 Python 프로젝트 표준(pyproject.toml) 지원
- **아키텍처**: 계층형(Layered) 구조 (api/service/repository 분리)
  - 이유: MVP 단계에서도 유지보수성과 테스트 용이성 확보, 향후 AI 서비스 계층 추가가 쉬움
- **Frontend/AI**: MVP 단계에서는 구조만 고려하고 실제 구현은 보류
  - 이유: 백엔드 도메인/API 안정화가 우선
