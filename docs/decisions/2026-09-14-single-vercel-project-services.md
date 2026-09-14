# 프론트·백엔드를 Vercel 프로젝트 하나로 — Services

- 날짜: 2026-09-14
- 상태: 채택 (코드 반영, 대시보드 전환은 Founder 대기)
- 대체:
  - `decision-log.md 2026-09-04 — 백엔드 호스팅을 Railway에서 Vercel Python Function으로 이전`
    중 "프론트와 별도의 Vercel 프로젝트(Root Directory `backend`)로 배포한다"와 프론트
    `BACKEND_ORIGIN` 프록시 부분
  - `decision-log.md 2026-09-07 — PR #37·#38·#39·#40 통합 및 문서 정합성 정리` 중
    "루트 `vercel.json` 제거" 부분

## 계기

Founder가 "프론트와 백엔드가 Vercel에서 다른 프로젝트인데 꼭 둘이어야 하냐"고 물었다.

두 프로젝트로 나눈 것은 구조상 꼭 필요해서가 아니었다. 2026-09-04 당시에는 Next.js와 FastAPI를
한 Vercel 프로젝트에 올리는 표준 방법이 Root Directory별 프로젝트였다. 그 결정의 계기부터
"플랫폼을 하나로 합쳐 관리 대상을 줄이자"였다.

그사이 Vercel **Services**가 나왔다. 한 프로젝트에 여러 프레임워크를 올리고 도메인·환경변수·
배포를 공유한다. 공식 가이드는 "available in Beta on all plans"라고 적는다(Hobby 포함).
과금은 기존 함수 과금과 같다.

지금 구조가 실제로 치르던 비용은 이렇다.

- **PR Preview가 반쪽이다**: Preview 프론트는 프로덕션 백엔드를 봐서, 이벤트 enum 제거 같은
  API 계약 변경을 Preview에서 함께 확인할 수 없었다.
- **배포와 롤백이 따로다**: 한 번 push에 두 프로젝트가 따로 배포돼 잠깐 버전이 어긋날 수 있다.
- **설정이 흩어져 있다**: 환경변수가 두 곳이고, `BACKEND_ORIGIN`은 빌드 때 고정돼 필수 가드가
  필요했다. 백엔드 공개 URL도 따로 노출돼 있었다.

## 결정

- 저장소 루트 `vercel.json`에 `frontend`(Next.js)와 `backend`(FastAPI, `app.main:app`)
  서비스를 둔다.
  - 최상위 rewrite 순서: `/api/backend/(.*)` → backend, 그 뒤에 `/(.*)` → frontend.
  - 서비스는 접두사가 붙은 원래 경로를 받는다. FastAPI `root_path="/api/backend"`
    (`backend/app/main.py`의 `PUBLIC_PATH_PREFIX`)가 앞부분을 떼고 라우팅한다.
    - 라우트 정의는 그대로다.
    - 접두사 없는 요청(로컬 uvicorn·`next dev` 프록시·옛 백엔드 프로젝트·테스트)도 계속 동작한다.
    - 처음에는 서비스 `routes`의 `request.path` 변환(`/$1`)을 썼다. 2026-09-15 시험 배포에서
      설정에는 들어갔지만 적용되지 않아 모든 API가 FastAPI 404였고, 그래서 바꿨다(아래 검증 참고).
  - 함수 설정(`maxDuration=30`, `excludeFiles`)은 backend 서비스의 `functions`로 옮기고
    `backend/vercel.json`을 지운다. Services 모드에서는 `functions`를 최상위에 둘 수 없다.
- 브라우저는 지금처럼 `/api/backend/*`만 호출한다(`frontend/src/lib/api.ts` 불변).
- `frontend/next.config.ts`
  - `BACKEND_ORIGIN` 필수 가드를 없앤다.
  - 프록시 rewrite는 `BACKEND_ORIGIN`이 있을 때만 등록한다. 로컬·CI는 `localhost:8000`을 쓴다.
  - Vercel에 `BACKEND_ORIGIN`이 남아 있으면 옛 2-프로젝트 방식으로 동작한다. 그래서 이 코드가
    대시보드 전환보다 먼저 배포돼도 프로덕션이 깨지지 않고, 롤백도 설정만으로 된다.
  - 계획 단계에서는 "Vercel이면 프록시를 등록하지 않는다"였는데, 이 배포 순서 위험 때문에 바꿨다.
- 계약은 `tests/test_deploy_config.py`가 지킨다. pytest와 `npm run build`는 루트
  `vercel.json`을 읽지 않기 때문이다.
  - 서비스 두 개, entrypoint, `maxDuration=30`
  - rewrite 순서, FastAPI `root_path`(접두사 있는·없는 경로 모두 200, 쿼리·경로 파라미터 422)
  - backend 서비스에 `routes` 변환 없음, `backend/vercel.json` 부재, `next.config.ts` 필수 가드 부재

## 검토한 대안·트레이드오프

- **두 프로젝트 유지**: 지금 잘 동작하고 Beta 위험이 없다. 대신 위의 반쪽 Preview·분리 배포·
  설정 분산을 계속 떠안는다.
- **서비스 `routes`의 `request.path` 변환**: 공식 문서 예시와 같은 형태라 처음에 골랐다. 시험
  배포에서 설정에는 들어갔지만 적용되지 않았다.
- **ASGI 래퍼로 접두사 떼기**: 로컬 결과는 `root_path`와 같았다. 하지만 `app`이 FastAPI
  인스턴스가 아니게 돼 Vercel의 FastAPI 감지 흐름을 벗어난다.
- **FastAPI `root_path`**(채택): 한 줄이고 `app`이 그대로 FastAPI다.
  - Starlette 1.3.1은 root_path로 시작하지 않는 경로를 그대로 매칭해서, 접두사 없는 호출도 동작한다.
  - 부수 효과는 OpenAPI `servers`에 `/api/backend`가 들어가는 정도다.
- **Services의 위험**: 아직 Beta다. 서비스별 `functions` 경로 표기는 문서에 예시가 없어 시험
  배포에서 확인해야 한다. 공유 환경변수라 프론트 빌드 환경에도 백엔드 비밀값이 들어간다
  (Next.js는 `NEXT_PUBLIC_*`만 번들에 넣으므로 노출되지 않는다).

## 운영 전환 (Founder, 대시보드)

카카오 링크가 걸린 `ai-academy-advisor-ten.vercel.app` 주소를 지키려면 새 프로젝트가 아니라
기존 프론트 프로젝트 `ai-academy-advisor`를 전환해야 한다.

1. **임시 프로젝트로 먼저 검증** (Hobby 팀, 예: `ai-academy-advisor-services-trial`)
   - Framework Preset `Services`, Root Directory는 저장소 루트
   - 백엔드 환경변수 전부 + `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID`, Deployment Protection 해제
   - 이 브랜치를 배포해 확인한다.
     - `/api/backend/health`
     - `/api/backend/academies?q=미사`: 경로를 뗀 뒤 쿼리가 유지되는지
     - `/`, `/check` → 307 `/app`
     - `POST /api/backend/recommendations/ai` 30초 안 응답, `/app` 제출 E2E
     - 배포 상세에서 함수 `maxDuration`이 30인지
   - 끝나면 임시 프로젝트를 삭제한다.
   - **중단 조건**: Hobby에서 Services를 고를 수 없거나 경로 변환·함수 설정이 적용되지 않으면
     멈추고 두 프로젝트를 유지한다. 이 파일 상태를 `폐기`로 바꾸고 사유를 남긴다.
2. **기존 프로젝트 전환**
   - 백엔드 환경변수를 Production·Preview에 추가한다.
   - Framework Preset `Services`, Root Directory를 비운다(저장소 루트).
   - 재배포 후 프로덕션 스모크: `/`, `/app` 제출, `/api/backend/health`, `/check` 307, 카카오 모달.
   - 통과하면 `BACKEND_ORIGIN` 환경변수를 지운다.
3. **롤백**: 설정을 되돌린다(Framework Next.js, Root `frontend`, `BACKEND_ORIGIN` 재설정)와
   재배포. 코드는 되돌리지 않아도 된다.
   - 백엔드 프로젝트 `ai-academy-advisor-backend`는 1~2주 남겼다가 삭제한다.
   - 그전에 main이 배포되면 이 프로젝트는 `backend/vercel.json` 없이 빌드된다. 기본
     `maxDuration`이 30초보다 길어질 뿐이고, 앱 자체의 28초 deadline이 있어 동작은 같다.

## 알고 가야 할 점

- Preview 백엔드도 운영 Supabase를 쓴다(지금 백엔드 프로젝트 Preview와 같다). 마이그레이션이
  필요한 PR은 머지 전에 적용해야 Preview가 동작한다.
- 비밀값에 `NEXT_PUBLIC_` 접두사를 쓰지 않는다.

## 바꾸지 않은 것

- FastAPI 라우트와 API 계약, `/api/backend` 공개 경로
- `NullPool` + transaction pooler(6543), 요청 28초 deadline과 `maxDuration=30`
- 로컬 개발 흐름(uvicorn + `next dev` + docker compose), CI
- `/check`·`/checklists` 307 리다이렉트

## 검증·다음

- 로컬 검증(2026-09-14)
  - `pytest ../tests`: 468 passed / 3 skipped(새 `test_deploy_config.py` 7개 포함).
  - `npm run build`는 세 경우 모두 성공했다. `.next/routes-manifest.json` 기준:
    - `VERCEL_ENV` 없음: `/api/backend/:path* → http://localhost:8000` 프록시가 등록된다.
    - `VERCEL_ENV=development`: 같은 프록시가 등록된다.
    - `VERCEL_ENV=preview`, `BACKEND_ORIGIN` 없음: 가드 없이 통과하고 프록시가 없다.
    - 세 경우 모두 `/check`·`/checklists` 307은 유지된다.
  - `vercel dev -L`(CLI 59.11.0)
    - 연결 정보 없는 복사본에서는 `frontend [Next.js]`·`backend [FastAPI]` 두 서비스로
      인식됐다. 루트 `vercel.json`이 Services로 읽힌다는 뜻이다.
    - 그러나 CLI가 만드는 Python 시작 파일에 Windows 경로가 이스케이프 없이 들어가
      (`SyntaxError: truncated \UXXXXXXXX escape`) 백엔드가 뜨지 않았다. CLI 버그라
      경로 변환·쿼리 전달·함수 설정은 로컬에서 확인하지 못했다.
    - 저장소 루트에서는 `.vercel` 연결(옛 Next.js 프로젝트) 설정을 따라 `next dev`만 떴다.
  - 이 과정에서 `next.config.ts` 버그를 잡았다. 처음엔 `VERCEL_ENV`가 있기만 하면 Vercel로 봐서
    `vercel dev`(development)에서 로컬 프록시가 사라졌다. production·preview만 배포로 보도록
    고치고 테스트로 막았다.
- 다음: 위 1단계(임시 프로젝트 배포)가 경로 변환·쿼리 전달·함수 `maxDuration`을 확인하는 첫
  실측이다. Founder가 진행하거나, CLI 배포를 확인받고 실행한다.
