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

- **히어로**: “분 만에 우리 아이에게 딱 맞는 학원을 찾아드려요.”
- **서브**: “학교, 학년, 과목, 학습 스타일만 입력하면 AI가 우리 아이에게 가장 잘 맞는 학원을 골라드립니다.”
- **지역/상태**: “하남 미사 출시 알림 신청 중” / “주변 수학학원 12곳”
- **CTA**: “출시 알림 신청하기” — “신청은 완전 무료”
- **미리보기**: “서비스 미리보기” / “출시 전 예시로 만든 화면입니다” / “실제 화면이 아닌 예시 이미지입니다” — API 미연동
- **자주 찾는 질문**: “내신 대비를 잘하는 학원을 찾고 싶어요.” / “숙제가 너무 많지는 않았으면 좋겠어요.” / “소수정예 수업이면 좋겠습니다.”
- **대기자**: “출시 알림 신청 받는 중” / “무료로 먼저 이용해보세요.” / “출시 소식도 가장 먼저 알려드립니다.”
- **카카오 모달**: “출시 알림을 받으시겠어요?” / “카카오톡 채널을 추가하시면 출시 시 가장 먼저 알림을 보내드립니다.” / “채널 채팅으로 문의하기”
- **Pain → Gain**: 후기 찾아보는 데 오래 걸림 → 바로 맞춤 추천
- **앱 미리보기**: 순위 카드, AI 추천 라벨, 지도·리스트, 상담(중2 · 수학 심화 등)

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

## 하지 말 것

- HTML 번들을 `public/`에 두거나 iframe embed
- Alpine/inline style을 React로 그대로 이식
- 랜딩 목업 섹션을 라이브 API에 연결
- 랜딩과 앱에 서로 다른 색·타이포 체계 사용
