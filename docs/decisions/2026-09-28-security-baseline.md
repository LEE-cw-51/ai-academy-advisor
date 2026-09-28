# 보안 기준 — 이 저장소에 없는 검사는 넣지 않는다

- 날짜: 2026-09-28
- 상태: 채택
- 대체: 없음

## 계기

범용 스캐너와 루트 아키텍처 문서, 유료 정기 리뷰를 그대로 얹으면 이 저장소의 배포·잠금파일·문서 정본과 어긋난다. 운영은 Vercel Services(Next.js + FastAPI)와 Supabase Postgres다. Docker(`backend/Dockerfile`, `docker-compose.yml`)는 로컬 전용이다.

## 결정

- 보안 정책 정본은 루트 `SECURITY.md`다. 공통 규칙은 `AGENTS.md`에 둔다. `CLAUDE.md`와 `.cursor/rules/`는 그 문서를 가리키는 얇은 포인터로 유지한다.
- PR 게이트의 보안 검사는 security 워크플로로 둔다. Semgrep ERROR, 이번 PR이 새로 들인 의존성의 high/critical(dependency-review), Trivy는 `backend/Dockerfile`과 `docker-compose.yml`의 config 스캔만.
- 의존성 알림의 정본은 Dependabot 하나다.

## 검토한 대안·트레이드오프

- **Checkov.** IaC 스캐너인데 검사할 Terraform·Kubernetes·Helm이 없다. 통과해도 운영 형상을 본 것이 아니다. 운영은 `vercel.json`의 Vercel Services와 Supabase다.
- **OSV-Scanner.** `frontend/package-lock.json`과 `backend/uv.lock`을 Dependabot과 같이 보면 같은 잠금파일 알림이 두 벌이 된다. 의존성 정본은 Dependabot으로 둔다.
- **매 PR Docker 이미지 빌드·스캔.** 이미지는 로컬용이다. PR마다 빌드하면 비용만 늘고 의존성 검사와 겹친다. Trivy는 그 두 파일의 config만 본다.
- **루트 `ARCHITECTURE.md`.** 구조 정본은 `docs/architecture.md`다. 루트에 같은 문서를 두면 바로 갈라진다. 규칙도 `AGENTS.md`에만 둔다.
- **유료 정기 Claude API 리뷰.** 혼자 운영하는 MVP에서 매주 API를 호출하는 비용보다, 배포·인증·DB·provider·공개 쓰기를 건드리는 PR에서 `CLAUDE.md` 체크리스트를 보는 쪽이 맞다. 정기 크론은 두지 않는다.

## 바꾸지 않은 것

- 앱 코드, 스키마, `vercel.json`, Dockerfile
- 기능 검증 CI(pytest, 프론트 빌드)
- 정책 없는 RLS + `REVOKE`(migration `0007`), 학원 사실 공개 쓰기 API 금지, 비밀은 `.env` / 플랫폼 변수만

## 하지 않은 것

- Checkov, OSV-Scanner, 매 PR Docker 이미지 빌드·스캔
- 루트 `ARCHITECTURE.md`
- Claude API를 부르는 유료 정기 워크플로
- 스캐너를 로컬에 상시 설치하는 스크립트. 검사 정본은 Actions이고, 로컬 재현은 `SECURITY.md`에 짧게만 적는다.
- 비공개 저장소의 GitHub Secret scanning(Advanced Security, 유료)을 필수로 두는 일. 비밀 패턴은 Semgrep이 본다. 공개 저장소의 Secret scanning·push protection은 대시보드 설정이라 이번 파일 범위 밖이다.

## 검증·다음

- security 워크플로가 위 세 검사만 실패 조건으로 갖는지 확인한다. 브랜치 보호의 required check는 파일 머지 후 Founder가 켠다.
- Dependabot alerts·security updates, 그리고 비공개 취약점 제보(Private vulnerability reporting)도 저장소 설정이라 Founder가 켠다. 공개 보안 연락 이메일은 없다.
