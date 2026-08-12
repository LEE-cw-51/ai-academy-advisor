"""가벼운 IP 기반 슬라이딩 윈도우 레이트리밋 (인메모리).

Redis 없이 waitlist 스팸을 완화한다. 프로세스 재시작 시 카운터가 초기화되며,
멀티 워커에서는 워커별 한도이다 — KPI 오염 완화용이지 완벽한 방어가 아니다.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_lock = threading.Lock()
_buckets: dict[str, list[float]] = defaultdict(list)

# 테스트에서 재설정할 수 있도록 모듈 상수.
WAITLIST_RATE_LIMIT = 10
WAITLIST_RATE_WINDOW_SEC = 60.0


def reset_waitlist_rate_limit() -> None:
    with _lock:
        _buckets.clear()


def enforce_waitlist_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _lock:
        recent = [t for t in _buckets[ip] if now - t < WAITLIST_RATE_WINDOW_SEC]
        if len(recent) >= WAITLIST_RATE_LIMIT:
            _buckets[ip] = recent
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
            )
        recent.append(now)
        _buckets[ip] = recent
