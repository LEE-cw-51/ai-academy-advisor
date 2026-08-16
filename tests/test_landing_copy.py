"""랜딩 카피의 실측 숫자가 data/academies 정본과 어긋나지 않는지 검사한다."""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ACADEMIES = REPO_ROOT / "data" / "academies"
LANDING_FACTS = (
    REPO_ROOT / "frontend" / "src" / "components" / "landing" / "landingFacts.ts"
)


def test_misa_academy_count_matches_json_source():
    text = LANDING_FACTS.read_text(encoding="utf-8")
    match = re.search(r"export const MISA_ACADEMY_COUNT = (\d+);", text)
    assert match is not None, "MISA_ACADEMY_COUNT not found in landingFacts.ts"
    declared = int(match.group(1))

    counted = 0
    for path in ACADEMIES.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        address = record.get("address") or ""
        if "미사" in address:
            counted += 1

    assert counted == declared, (
        f"landing copy says {declared} Misa academies but JSON has {counted}. "
        "Update MISA_ACADEMY_COUNT in landingFacts.ts."
    )
