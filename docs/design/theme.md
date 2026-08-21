# Academy Kok 디자인 시스템

소스: [`academy-kok-landing.html`](./academy-kok-landing.html) (Design Canvas 번들, ~7.8MB).  
이 HTML은 **테마 참조 전용**입니다. Next.js에 embed/복붙하지 마세요.

## 브랜드

| 항목 | 값 |
|------|-----|
| 제품명 | 학원콕 |
| 타깃 | 하남 미사 학부모 |
| 톤 | 따뜻하고 신뢰감 — 짧은 문장, 이모지 소량(📍 🎉 ✨) |

## 색 토큰

| 토큰 | Hex | 용도 |
|------|-----|------|
| `canvas` | `#faf9f5` | 페이지 배경 |
| `surface` | `#FFFFFF` | 카드·패널 |
| `surface-muted` | `#F9FAFB` | 보조 서피스 |
| `surface-subtle` | `#F3F4F6` | 입력·리스트 배경 |
| `brand` | `#F5A623` | Primary CTA |
| `brand-dark` | `#D98C0E` | Hover / 강조 |
| `ink` | `#1E2B3C` | 본문·헤드라인 |
| `ink-strong` | `#111827` | 강한 텍스트 |
| `ink-muted` | `#374151` | 보조 본문 |
| `ink-subtle` | `#6B7280` | 캡션·힌트 |
| `border` | `#E5E7EB` | 기본 보더 |
| `border-soft` | `#E7EBF0` | 소프트 보더 |
| `success-bg` / `success` | `#F0FDF4` / `#15803D` | 성공 |
| `warn-bg` / `warn` | `#FEF3C7` / `#B45309` | 알림·디스클레이머 |
| `kakao` | `#FEE500` | 카카오 CTA |

## 타이포

- 본문/UI: **Noto Sans KR** (Google Fonts)
- 헤드라인: 굵은 weight, ink 색
- 본문: 짧고 읽기 쉬운 문장

## 레이아웃·형태

- 카드: 둥근 모서리(~12px) + 부드러운 그림자
- 버튼: ~8px radius
- 랜딩 첫 화면: 축소 로고 + 헤드라인 + 한 줄 서포트 + 상태 배지 + CTA. CTA 아래 약속은 카드 없이 좌측 보더 텍스트.
- 보조 본문은 `ink-muted`, 법적 각주·캡션만 `ink-subtle`.
- 앱 셸: 좌 채팅/추천, 우 지도/리스트 (동일 시각 언어)

## UI 패턴 (랜딩·앱 공통)

| 패턴 | 설명 |
|------|------|
| Primary Button | 오렌지 배경, 흰/잉크 텍스트 |
| Secondary Button | outline, border + ink |
| Kakao Button | `#FEE500` 배경 |
| Badge | 지역(“하남 미사”), 출처 확인일, 후보 근거, 미확인 항목 |
| Card | 후보 학원·정보 패널 |
| Modal | 카카오 채널 / 확인 |
| Input | 선택형 상황 입력·폼, soft surface |
| Disclaimer | 출처·확인일·미확인 항목·출시 전 예시 등 warn 톤 |

## 랜딩·탐색 MVP 카피 원칙

현재 `/`·`/check`·`/checklists`는 소개·점검·체크리스트 퍼널이다. 실제 공개 탐색 MVP가 구현되기 전까지 현재형 후보 탐색·맞춤 결과·`/app` CTA를 랜딩에 약속하지 않는다. 숫자는 `landingFacts.ts`의 실측값만 사용하며, 과목·수업 형태처럼 정본에 없는 속성으로 비교를 약속하지 않는다.

- **문제 프레이밍**: ‘더 좋은 학원을 골라드립니다’보다, ‘학원과 아이의 학습 상태를 둘러싼 블랙박스를 줄이고 더 나은 질문과 판단을 돕습니다’를 우선한다.
- **현재 퍼널**: `/check`는 학원 좋음/나쁨을 판정하지 않는 점검·상담 질문 도구다. `/checklists`는 상담 전·재원·이전 고민에 쓸 웹 체크리스트이며, PDF·페이월은 없다.
- **실제 탐색 MVP의 입력**: 현재 상황, 학년군, 과목, 가장 큰 걱정을 우선하는 선택형 폼이다. 자유 대화형 AI 채팅은 첫 MVP 범위가 아니다.
- **결과 표현**: `조건과 관련해 확인해 볼 후보 정보`, `왜 이 후보를 보여드렸나요?`, `상담에서 확인할 점`을 쓴다. `최고`, `확정 추천`, `가장 맞는 학원`, 별점·신뢰도·퍼센트는 쓰지 않는다.
- **후보 카드**: 학원명, 주소·지도, 공개 연락처/웹사이트, 출처·확인일, 후보 근거, 미확인 항목을 표시한다. 구체 속성은 검증된 사실이 있을 때만 쓴다.
- **직접 행동**: `전화하기`, `웹사이트 방문`, `길찾기`는 사용자가 직접 수행한다. `상담 신청`, `예약하기`, `학원에서 연락드려요` 같은 중개 흐름은 첫 MVP에서 쓰지 않는다.
- **사실 구분**: 확인된 사실·런타임 탐색 신호·상담에서 확인할 점을 시각적으로 구분한다. 미확인 정보는 공란·`미확인` 또는 질문으로 남긴다.
- **개인정보**: 자녀 실명·생년월일·성적표·상세 자유 서술을 기본 입력으로 요구하지 않는다. 로그인은 저장/재방문 수요가 검증된 뒤 선택적으로 검토한다.
- **광고/강화 프로필**: 향후 도입되면 일반 후보와 시각적으로 분리하고 명확히 표시한다. 유료 여부가 일반 후보의 순서·AI 근거에 영향을 주는 표현을 만들지 않는다.

## 앱에서 재사용할 탐색 결과 패턴

- 좌: 선택형 상황 입력 + AI가 정리한 조건·상담 질문
- 우: 지도 + 조건과 관련해 확인해 볼 후보 목록
- 후보 카드: 학원명, 거리/주소, 공개 연락처, 출처·확인일, 후보 근거, 상담에서 확인할 점
- 클릭 추적: 전화 / 홈페이지 / 길찾기 / 상세

## 구현 매핑

| 문서 | 코드 |
|------|------|
| 토큰 | `frontend/src/styles/tokens.css` + Tailwind theme |
| 공통 UI | `frontend/src/components/ui/` |
| 랜딩 | `frontend/src/components/landing/` → `/` |
| 미니 점검 | `frontend/src/components/check/` → `/check` |
| 체크리스트 | `frontend/src/components/checklists/` → `/checklists` |
| 앱 | `frontend/src/components/app/` → `/app` |

## 색 토큰 표기 주의

`frontend/src/styles/tokens.css`의 색 토큰은 **hex가 아니라 공백으로 구분한 RGB 채널값**이다
(`--color-ink: 30 43 60;` = `#1e2b3c`). 위 표의 hex와 값은 같고 표기만 다르다.

Tailwind 투명도 표기(`text-surface/80`, `bg-ink/40`)가 동작하려면 `tailwind.config.ts`에서
`rgb(var(--x) / <alpha-value>)`로 합성해야 하고, 그러려면 변수가 채널값이어야 한다.
hex를 넣으면 `rgb(#ffffff / 0.8)`이라는 무효 CSS가 만들어져 **선언이 조용히 버려지고**
상속색이 그대로 보인다 — 흰 글씨가 어두운 배경 위에서 안 보이는 식으로 드러난다.
CSS에서 직접 쓸 때도 `rgb(var(--color-ink))`로 감싼다.

## 하지 말 것

- HTML 번들을 저장소 루트 `index.html`로 두지 말 것 — GitHub Pages·Vercel 등이 이걸 사이트 진입점으로 배포한다
- HTML 번들을 `frontend/public/`에 두거나 iframe embed
- Alpine/inline style을 React로 그대로 이식
- 랜딩 목업 섹션을 라이브 API에 연결
- 랜딩과 앱에 서로 다른 색·타이포 체계 사용
