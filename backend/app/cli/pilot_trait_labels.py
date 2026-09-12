"""Stage 4b: read-only closed-label extraction pilot.

Writes proposals under gitignored data/raw/trait-labels-pilot/ only.
Never UPDATEs academies or creates academy_trait_labels rows (use
``app.cli.ingest_trait_labels`` for Stage 4c writes).

Usage:
    cd backend
    uv run python -m app.cli.pilot_trait_labels [--max-academies 20] [--max-reviews 50]
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.trait_label_matcher import (
    LABEL_KEYWORDS,
    match_labels,
    snippet_around,
    source_type_from_review_source,
)

_DEFAULT_OUT = Path("../data/raw/trait-labels-pilot")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 4b dry-run: extract closed trait labels from review snippets (no DB writes)."
    )
    parser.add_argument(
        "--max-academies",
        type=int,
        default=20,
        help="Pilot academies that have reviews (default 20)",
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=50,
        help="Max review rows to scan within the pilot academies (default 50)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=_DEFAULT_OUT,
        help="Output directory under gitignored data/raw/",
    )
    parser.add_argument(
        "--include-tagline",
        action="store_true",
        default=True,
        help="Also scan academies.tagline for the same closed labels (default on)",
    )
    parser.add_argument(
        "--no-tagline",
        action="store_true",
        help="Skip tagline matching",
    )
    args = parser.parse_args(argv)
    include_tagline = args.include_tagline and not args.no_tagline

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    proposals: list[dict] = []
    label_counts: Counter[str] = Counter()
    academies_touched: set[int] = set()
    reviews_scanned = 0
    taglines_scanned = 0

    with SessionLocal() as session:
        baseline = session.execute(
            text(
                """
                SELECT
                  COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE curriculum_seonhaeng IS NOT NULL) AS seonhaeng_set,
                  COUNT(*) FILTER (WHERE curriculum_naesin IS NOT NULL) AS naesin_set,
                  COUNT(*) FILTER (WHERE curriculum_suneung IS NOT NULL) AS suneung_set,
                  COUNT(*) FILTER (WHERE level_elementary IS NOT NULL) AS level_elem_set,
                  COUNT(*) FILTER (WHERE class_small_group IS NOT NULL) AS class_set
                FROM academies
                """
            )
        ).mappings().one()

        academy_ids = [
            row[0]
            for row in session.execute(
                text(
                    """
                    SELECT academy_id
                    FROM reviews
                    GROUP BY academy_id
                    ORDER BY MIN(id)
                    LIMIT :lim
                    """
                ),
                {"lim": args.max_academies},
            ).all()
        ]

        if not academy_ids:
            print("No academies with reviews; aborting.")
            return 1

        reviews = session.execute(
            text(
                """
                SELECT r.id, r.academy_id, r.content, r.source, r.source_url,
                       r.published_at, a.name AS academy_name, a.tagline
                FROM reviews r
                JOIN academies a ON a.id = r.academy_id
                WHERE r.academy_id = ANY(:ids)
                ORDER BY r.id
                LIMIT :lim
                """
            ),
            {"ids": academy_ids, "lim": args.max_reviews},
        ).mappings().all()

        tagline_by_academy: dict[int, tuple[str | None, str]] = {}
        if include_tagline:
            for row in session.execute(
                text(
                    """
                    SELECT id, name, tagline
                    FROM academies
                    WHERE id = ANY(:ids)
                    """
                ),
                {"ids": academy_ids},
            ).mappings():
                tagline_by_academy[row["id"]] = (row["tagline"], row["name"])

    seen: set[tuple[int, str, str]] = set()

    for row in reviews:
        reviews_scanned += 1
        content = row["content"] or ""
        for label, kw in match_labels(content):
            key = (row["academy_id"], label, row["source_url"] or f"review:{row['id']}")
            if key in seen:
                continue
            seen.add(key)
            prop = {
                "academy_id": row["academy_id"],
                "academy_name": row["academy_name"],
                "label": label,
                "matched_keyword": kw,
                "source_type": source_type_from_review_source(row["source"]),
                "source_url": row["source_url"],
                "review_id": row["id"],
                "snippet": snippet_around(content, kw),
                "observed_at": (
                    row["published_at"].isoformat()
                    if row["published_at"] is not None
                    else None
                ),
                "status": "candidate",
                "matcher": "keyword",
            }
            proposals.append(prop)
            label_counts[label] += 1
            academies_touched.add(row["academy_id"])

    if include_tagline:
        for aid, (tagline, name) in tagline_by_academy.items():
            if not tagline:
                continue
            taglines_scanned += 1
            for label, kw in match_labels(tagline):
                key = (aid, label, "tagline")
                if key in seen:
                    continue
                seen.add(key)
                prop = {
                    "academy_id": aid,
                    "academy_name": name,
                    "label": label,
                    "matched_keyword": kw,
                    "source_type": "homepage",
                    "source_url": None,
                    "review_id": None,
                    "snippet": snippet_around(tagline, kw),
                    "observed_at": None,
                    "status": "candidate",
                    "matcher": "keyword_tagline",
                }
                proposals.append(prop)
                label_counts[label] += 1
                academies_touched.add(aid)

    with SessionLocal() as session:
        after = session.execute(
            text(
                """
                SELECT
                  COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE curriculum_seonhaeng IS NOT NULL) AS seonhaeng_set,
                  COUNT(*) FILTER (WHERE curriculum_naesin IS NOT NULL) AS naesin_set,
                  COUNT(*) FILTER (WHERE curriculum_suneung IS NOT NULL) AS suneung_set,
                  COUNT(*) FILTER (WHERE level_elementary IS NOT NULL) AS level_elem_set,
                  COUNT(*) FILTER (WHERE class_small_group IS NOT NULL) AS class_set
                FROM academies
                """
            )
        ).mappings().one()
        table_exists = session.execute(
            text(
                """
                SELECT EXISTS (
                  SELECT 1 FROM information_schema.tables
                  WHERE table_schema = 'public'
                    AND table_name = 'academy_trait_labels'
                )
                """
            )
        ).scalar()

    facts_unchanged = dict(baseline) == dict(after)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = out_dir / f"trait-label-proposals-{stamp}.csv"
    report_path = out_dir / f"trait-label-pilot-report-{stamp}.json"
    latest_csv = out_dir / "trait-label-proposals.csv"
    latest_report = out_dir / "trait-label-pilot-report.json"

    fieldnames = [
        "academy_id",
        "academy_name",
        "label",
        "matched_keyword",
        "source_type",
        "source_url",
        "review_id",
        "snippet",
        "observed_at",
        "status",
        "matcher",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(proposals)
    latest_csv.write_bytes(csv_path.read_bytes())

    coverage = {label: label_counts.get(label, 0) for label in LABEL_KEYWORDS}
    report = {
        "stage": "4b",
        "mode": "dry-run_keyword_only",
        "llm_used": False,
        "openai_key_present": False,
        "pilot": {
            "max_academies": args.max_academies,
            "max_reviews": args.max_reviews,
            "academy_ids": academy_ids,
            "reviews_scanned": reviews_scanned,
            "taglines_scanned": taglines_scanned,
            "include_tagline": include_tagline,
        },
        "proposals_total": len(proposals),
        "academies_touched": sorted(academies_touched),
        "academies_touched_count": len(academies_touched),
        "per_label_counts": coverage,
        "academies_fact_baseline": dict(baseline),
        "academies_fact_after": dict(after),
        "academies_fact_columns_unchanged": facts_unchanged,
        "academy_trait_labels_table_exists": bool(table_exists),
        "stage_4c_unblocked": bool(
            facts_unchanged
            and len(proposals) > 0
            and (len(proposals) / max(reviews_scanned, 1)) >= 0.02
        ),
        "csv": str(csv_path.as_posix()),
        "keywords": {k: list(v) for k, v in LABEL_KEYWORDS.items()},
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    latest_report.write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if facts_unchanged else 2


if __name__ == "__main__":
    raise SystemExit(main())
