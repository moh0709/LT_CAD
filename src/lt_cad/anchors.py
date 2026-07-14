"""Validate component views and their reviewed piping anchors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


APPROVED_ANCHOR_STATUS = "approved"
VALID_GEOMETRY_STATUSES = {"needs_review", "approved_family_standard", "approved"}
VALID_ANCHOR_STATUSES = {"needs_review", APPROVED_ANCHOR_STATUS}
VALID_DIRECTIONS = {"in", "out", "bidirectional"}


def validate_views(registry: dict[str, Any]) -> dict[str, list[str]]:
    """Return validation errors and warnings for a component-view registry."""
    errors: list[str] = []
    warnings: list[str] = []
    view_ids: set[str] = set()

    for view in registry.get("views", []):
        view_id = view.get("id")
        if not view_id:
            errors.append("A view is missing its id.")
            continue
        if view_id in view_ids:
            errors.append(f"Duplicate view id: {view_id}")
        view_ids.add(view_id)

        geometry_status = view.get("geometry_status")
        anchor_status = view.get("anchor_status")
        anchors = view.get("anchors", [])
        if geometry_status not in VALID_GEOMETRY_STATUSES:
            errors.append(f"{view_id} has invalid geometry_status: {geometry_status}")
        if anchor_status not in VALID_ANCHOR_STATUSES:
            errors.append(f"{view_id} has invalid anchor_status: {anchor_status}")
        if anchor_status != APPROVED_ANCHOR_STATUS and anchors:
            errors.append(f"{view_id} has anchors that are not approved for routing.")
        if anchor_status == "needs_review":
            warnings.append(f"Pipe anchors require review: {view_id}")

        marker_ids: set[str] = set()
        for marker in view.get("review_markers", []):
            marker_id = marker.get("id")
            if not marker_id:
                errors.append(f"{view_id} has a review marker without an id.")
                continue
            if marker_id in marker_ids:
                errors.append(f"{view_id} has duplicate review marker id: {marker_id}")
            marker_ids.add(marker_id)
            for axis in ("x", "y"):
                value = marker.get(axis)
                if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                    errors.append(
                        f"{view_id}/{marker_id} {axis} must be normalized to [0, 1]."
                    )

        anchor_ids: set[str] = set()
        for anchor in anchors:
            anchor_id = anchor.get("id")
            if not anchor_id:
                errors.append(f"{view_id} has an anchor without an id.")
                continue
            if anchor_id in anchor_ids:
                errors.append(f"{view_id} has duplicate anchor id: {anchor_id}")
            anchor_ids.add(anchor_id)
            if not anchor.get("medium"):
                errors.append(f"{view_id}/{anchor_id} is missing medium.")
            if anchor.get("direction") not in VALID_DIRECTIONS:
                errors.append(f"{view_id}/{anchor_id} has invalid direction.")
            for axis in ("x", "y"):
                value = anchor.get(axis)
                if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                    errors.append(
                        f"{view_id}/{anchor_id} {axis} must be normalized to [0, 1]."
                    )

    return {"errors": errors, "warnings": warnings}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path, help="Component view registry JSON")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    result = validate_views(registry)
    print(json.dumps(result, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
