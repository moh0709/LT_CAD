"""Validate normalized quotation data before topology and CAD generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VALID_ITEM_TYPES = {"component", "pipe_system", "option", "service", "unresolved"}


def validate_quotation(quotation: dict[str, Any]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    order_number = str(quotation.get("order_number", ""))
    if not order_number.isdigit():
        errors.append("order_number must contain digits only.")

    positions: set[int] = set()
    for item in quotation.get("items", []):
        position = item.get("position")
        if not isinstance(position, int) or position < 1:
            errors.append("Every quotation item requires a positive integer position.")
        elif position in positions:
            errors.append(f"Duplicate quotation position: {position}")
        else:
            positions.add(position)

        quantity = item.get("quantity")
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            errors.append(f"Position {position} requires quantity greater than zero.")
        item_type = item.get("type")
        if item_type not in VALID_ITEM_TYPES:
            errors.append(f"Position {position} has invalid type: {item_type}")
        if item_type == "component":
            if not item.get("family") or not item.get("model"):
                errors.append(f"Component at position {position} requires family and model.")
        if item_type == "unresolved":
            warnings.append(f"Position {position} requires component resolution.")
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
            errors.append(f"Position {position} confidence must be within [0, 1].")

    return {"errors": errors, "warnings": warnings}


def component_instances(quotation: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand whole-number quoted component quantities into deterministic instances."""
    instances: list[dict[str, Any]] = []
    for item in quotation.get("items", []):
        if item.get("type") != "component":
            continue
        quantity = item.get("quantity")
        if not isinstance(quantity, int):
            raise ValueError(f"Component position {item.get('position')} quantity must be integer.")
        for index in range(1, quantity + 1):
            instances.append(
                {
                    "id": f"q{item['position']}-{index}",
                    "family": item["family"],
                    "model": item["model"],
                    "origin": "quoted",
                    "quotation_position": item["position"],
                }
            )
    return instances


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quotation", type=Path)
    parser.add_argument("--instances", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    quotation = json.loads(args.quotation.read_text(encoding="utf-8"))
    result = validate_quotation(quotation)
    output: dict[str, Any] = {"validation": result}
    if args.instances and not result["errors"]:
        output["component_instances"] = component_instances(quotation)
    print(json.dumps(output, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
