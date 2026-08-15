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
- 랜딩 첫 화면: 브랜드 + 한 줄 헤드라인 + 짧은 설명 + CTA
- 앱 셸: 좌 채팅/추천, 우 지도/리스트 (동일 시각 언어)

## UI 패턴 (랜딩·앱 공통)

| 패턴 | 설명 |
|------|------|
| Primary Button | 오렌지 배경, 흰/잉크 텍스트 |
| Secondary Button | outline, border + ink |
| Kakao Button | `#FEE500` 배경 |
| Badge | 지역(“하남 미사”), AI 추천, 순위(1순위/2순위) |
| Card | 추천 학원·정보 패널 |
| Modal | 카카오 채널 / 확인 |
| Input | 채팅·폼, soft surface |
| Disclaimer | “출시 전 예시” 등 warn 톤 |

## 랜딩 카피 (추출)

출시 전 대기자 페이지. 현재형 추천 카피·`/app` CTA·미리보기 목업은 쓰지 않는다.

- **상태**: “정식 출시 준비 중” / “정식 출시 준비 중 · 하남 미사”
- **히어로**: “하남 미사 학원 추천 서비스, 출시를 준비하고 있어요.”
- **서브**: “아직 정식 출시 전이라 학원 추천은 제공하지 않습니다. 카카오톡 채널을 추가해 두시면, 출시하는 날 가장 먼저 알려드릴게요.”
- **CTA**: “무료 출시 알림 신청하기” — “카카오톡 채널 추가로 신청해요. 비용은 들지 않습니다.”
- **첫 화면 Disclaimer**: 지금 이 사이트에서 하실 수 있는 것은 출시 알림 신청뿐. 추천·비교·상담 연결, 결제·수강 계약·예약금 없음.
- **Pain → Gain**: 후기 찾아보는 데 오래 걸림 / 비교해도 확신이 안 섬 / “출시 후엔 AI가 맞춤 추천”
- **출시 후 기능**: 맞춤 학원 추천 · 학원 정보 비교 · 상담 연결 — “아래 기능은 준비 중이며, 아직 이용하실 수 없습니다.”
- **대기자**: “출시하면 가장 먼저 알려드릴게요.” / “지금 하실 수 있는 건 무료 출시 알림 신청뿐이에요.”
- **카카오 모달**: “출시 알림을 받으시겠어요?” / “카카오톡 채널을 추가하시면, 학원콕이 정식 출시하는 날 가장 먼저 알림을 보내드립니다.” / “카카오톡 채널 추가하고 알림 받기”
- **푸터**: 출시 전·알림 신청만 가능. 문의 이메일 · 개인정보처리방침 · 카카오톡 채널. 사업자 정보는 출시 시점에 표기.

## 앱에서 재사용할 미리보기 패턴

- 좌: 대화형 AI 입력 + 추천 카드
- 우: 지도 + 학원 리스트
- 추천 카드: 순위, 학원명, 거리/주소, AI 추천 라벨, 이유
- 클릭 추적: 전화 / 홈페이지 / 길찾기 / 상세

## 구현 매핑

| 문서 | 코드 |
|------|------|
| 토큰 | `frontend/src/styles/tokens.css` + Tailwind theme |
| 공통 UI | `frontend/src/components/ui/` |
| 랜딩 | `frontend/src/components/landing/` → `/` |
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
