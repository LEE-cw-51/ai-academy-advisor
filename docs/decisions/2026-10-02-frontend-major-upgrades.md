# 프론트엔드 메이저 업그레이드 — Next 16 · React 19.3 · Tailwind 4, TypeScript 7은 보류

- 날짜: 2026-10-02
- 상태: 채택
- 대체: 없음

## 계기

Dependabot이 프론트 메이저 업데이트 다섯 개(#78 Next 16, #79 TypeScript 7, #80 Tailwind 4, #81 react 19.3, #82 react-dom 19.3)를 따로 올렸다. #81은 `react`와 `react-dom` 버전이 달라 빌드가 실패했고, #80은 PostCSS 플러그인이 `@tailwindcss/postcss`로 옮겨져 실패했다. #79는 Next 15가 `next.config.ts`를 읽을 때 쓰는 TypeScript JS API가 없어 실패했다. 하나씩 머지하면 매번 프로덕션이 중간 상태가 되므로 한 PR로 묶었다.

## 결정

- Next 16.3, `eslint-config-next` 16.3, React·React DOM 19.3을 함께 올린다. Next 16에서 `next lint`가 빠져 `lint` 스크립트를 `eslint`로 바꾸고, `eslint.config.mjs`를 패키지가 내보내는 flat config로 옮긴다.
- React Hooks 7의 새 규칙 `react-hooks/set-state-in-effect`는 `AcademyDetailModal`·`AcademySearchPage`의 effect 두 곳을 잡는다. 리팩터링은 동작과 소스 구조 테스트에 영향을 주므로 이 PR에서는 경고로 낮춘다. CI는 lint를 돌리지 않는다.
- Tailwind 4는 공식 업그레이드 도구로 옮기고, 화면이 v3와 같도록 다음을 고정한다.
  - `tokens.css` 채널 변수와 테마 변수 이름이 같아 `@theme inline reference`로 둔다. 기본 `@theme`은 유틸리티가 채널값만 받거나 `:root`에 순환 변수를 만들어 색이 전부 사라졌다.
  - v4가 바꾼 기본값을 v3에 맞춘다: 버튼 `cursor: pointer`, `leading-snug`가 반응형 `sm:text-*` line-height를 이기는 제목 세 곳에 `sm:leading-9`·`sm:leading-10`, `space-y`가 `sr-only` 라벨 뒤 간격을 잃는 입력창에 `mt-2.5`.
- TypeScript는 `^5`로 둔다. TypeScript 7에서 빌드와 `tsc`는 통과했지만 `eslint-config-next` 16의 `typescript-eslint`가 TypeScript `<6.1.0`만 지원해 ESLint가 시작하지 않는다(`typescript-eslint does not support TS 7.0`).

## 검토한 대안·트레이드오프

- **CI가 통과한 #78·#82만 머지.** Next 16과 react-dom만 오르고 react가 남아 다음 빌드가 다시 깨진다.
- **TypeScript 7도 함께 올리고 lint를 잠시 포기.** CI는 통과하지만 로컬 `npm run lint`가 통째로 멈춘다. 얻는 것은 타입 검사 속도뿐이다.
- **Tailwind 4 테마 변수 이름을 바꿔 충돌 피하기.** 가장 명시적이지만 `tokens.css`·`globals.css`·`theme.md`의 변수 이름을 모두 바꿔야 한다. `inline reference` 한 줄로 같은 결과를 얻는다.

## 바꾸지 않은 것

- `tokens.css` 값과 변수 이름, 컴포넌트 구조, 백엔드
- `next` 의존성의 `postcss` override
- 기존 `brace-expansion` 개발 의존성 취약점(`main`에도 있다)

## 검증·다음

- `npm ci`·`npm run build`·`npm run lint`(오류 0, 경고 2), `uv run pytest ../tests` 481 통과, `/check`·`/checklists`가 쿼리를 유지한 채 `/app`으로 307.
- 업그레이드 전(`main`)과 후의 화면 12개를 1280px·390px에서 비교했다. 랜딩·`/app`·학원 찾기·개인정보 페이지와 학원 찾기 결과·후보 결과 화면이다. 차이는 모두 0.6% 미만의 글자 안티앨리어싱이다.
- TypeScript 7은 `typescript-eslint`가 TS 7을 지원하면 다시 올린다. `set-state-in-effect` 경고 두 곳은 별도 PR에서 고친다.
