# 홈(`/`)을 히어로만 남기고 왼쪽 정렬

- 날짜: 2026-09-25
- 상태: 채택
- 대체: 없음 (홈 레이아웃·크롬 옵션만 좁힌다. `/app` CTA·카피·푸터 문구는 유지)

## 계기

홈 첫 화면이 가운데 정렬 히어로 + 근거 구간 + 법적 푸터 + 노란 카카오 고정 바로
길어졌다. Founder가 홈은 헤더와 히어로(로고·제목·`/app` 버튼·신뢰 문구)만 남기고
왼쪽 정렬로 단순화하기로 했다. 문의·개인정보·카카오 진입은 방침 페이지에 둔다.

## 결정

- `PageHero`와 홈 CTA 묶음을 왼쪽 정렬한다. 히어로 카피·`HOME_CTA_HREF`(`/app`)는
  바꾸지 않는다.
- `GroundworkSection`과 `GROUNDWORK_*` 카피를 제거한다. `MISA_ACADEMY_COUNT`는 JSON
  건수 검사용으로만 남긴다.
- `SiteChrome`의 `footer`·`kakaoBar`는 기본 끔. 홈은 둘 다 끄고 하단 `8rem` 패딩도
  뺀다. `/privacy`만 `footer`·`kakaoBar`를 켠다.

## 바꾸지 않은 것

- 히어로·메타·푸터 카피 문구, `/app` 동작, 추천·스코어링·학원 데이터
- `LandingFooter`·`StickyKakaoBar` 컴포넌트 자체 (방침 페이지에서 계속 사용)

## 검증·다음

- `tests/test_landing_copy.py`로 홈 구성·크롬 옵션·히어로 CTA(`/app`)를 감시한다.
- 로컬 `/`에서 왼쪽 히어로·빈 하단, `/privacy`에서 푸터·노란 바를 확인한다.
