# 보안 정책

학원콕의 취약점 제보와 지원 범위는 이 파일이 정본이다. 공통 작업 규칙은 [AGENTS.md](AGENTS.md)에 있다.

## 지원 버전

지원 버전은 배포된 `main` 하나다. 그 이전 커밋과 Preview 배포는 보안 지원 대상이 아니다.

## 취약점 제보

이 저장소에는 공개 보안 연락 이메일이 없다. 취약점은 GitHub **비공개 취약점 제보**(Private vulnerability reporting)로 보낸다. 저장소 Security 탭의 **Report a vulnerability**가 초안 Security Advisory를 만든다.

공개 Issue, PR, 채팅에 올리지 않는다. 재현에 필요한 비밀·토큰·연결 문자열·키도 이슈나 PR 본문에 붙이지 않는다. 유지보수자가 비공개 채널에서 요청할 때만 전달한다.

## 범위

- 앱: 프론트엔드·백엔드 코드와 공개 API
- 의존성: npm, uv, GitHub Actions
- 설정: 환경 변수 노출, 배포 설정의 비밀·권한, 로컬 Docker 설정의 잘못된 노출

## 범위 밖

- 첫 MVP에는 사용자 로그인·JWT가 없다. 인증이 없는 상태 자체는 취약점으로 보지 않는다.
- 학원 품질·추천의 옳고 그름은 보안 결함이 아니다. 확인되지 않은 사실은 `null`로 두고, 품질 단정은 하지 않는다.

## CI

이 기준은 `.github/workflows/security.yml`이 PR과 `main` push에서 강제한다. 실패 조건은 Semgrep ERROR, dependency-review가 그 PR에서 새로 추가한 의존성의 high/critical, Trivy의 config 스캔(`backend/Dockerfile`과 `docker-compose.yml`만)이다.

로컬에서 같은 기준을 다시 볼 때는 그 세 가지만 돌린다. Semgrep은 Python·TypeScript·secrets 커뮤니티 규칙의 ERROR만 보고, 의존성은 이번 변경이 새로 들인 high/critical만 보고, Trivy는 위 두 파일의 config만 본다. 이미지 빌드와 잠금파일 전체 스캔은 넣지 않는다. 검사 정본은 Actions다.
