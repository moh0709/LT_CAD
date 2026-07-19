"""Validate a proposed drying and conveying system topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate_topology(topology: dict[str, Any], rules: dict[str, Any]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    components = topology.get("components", [])
    connections = topology.get("connections", [])

    component_by_id: dict[str, dict[str, Any]] = {}
    for component in components:
        component_id = component.get("id")
        if not component_id:
            errors.append("A component is missing its id.")
            continue
        if component_id in component_by_id:
            errors.append(f"Duplicate component id: {component_id}")
        component_by_id[component_id] = component
        if component.get("origin") == "inferred":
            warnings.append(f"Inferred component requires approval: {component_id}")

    known_media = set(rules.get("line_classes", {}))
    permitted = {
        (
            rule["medium"],
            source_family,
            target_family,
        )
        for rule in rules.get("connection_rules", [])
        if rule.get("status") == "confirmed"
        for source_family in rule.get("source_families", [])
        for target_family in rule.get("target_families", [])
    }

    valid_connections: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    for index, connection in enumerate(connections):
        source_id = connection.get("source")
        target_id = connection.get("target")
        medium = connection.get("medium")
        source = component_by_id.get(source_id)
        target = component_by_id.get(target_id)
        if source is None or target is None:
            errors.append(
                f"Connection {index} references an unknown component: "
                f"{source_id} -> {target_id}"
            )
            continue
        if medium not in known_media:
            errors.append(f"Connection {index} uses unknown medium: {medium}")
            continue
        signature = (medium, source.get("family"), target.get("family"))
        if signature not in permitted:
            errors.append(
                f"Connection {index} is not permitted: {source.get('family')} "
                f"-({medium})-> {target.get('family')}"
            )
            continue
        valid_connections.append((source, target, medium))

    for requirement in rules.get("node_requirements", []):
        family = requirement["family"]
        for component in components:
            if component.get("family") != family or not component.get("id"):
                continue
            component_id = component["id"]
            for direction in ("incoming", "outgoing"):
                for expected in requirement.get(direction, []):
                    other_families = expected.get("other_families") or [
                        expected["other_family"]
                    ]
                    found = any(
                        medium == expected["medium"]
                        and (
                            direction == "incoming"
                            and target.get("id") == component_id
                            and source.get("family") in other_families
                            or direction == "outgoing"
                            and source.get("id") == component_id
                            and target.get("family") in other_families
                        )
                        for source, target, medium in valid_connections
                    )
                    if not found:
                        errors.append(
                            f"{component_id} requires {direction} "
                            f"{expected['medium']} connection with "
                            f"{' or '.join(other_families)}."
                        )

    return {"errors": errors, "warnings": warnings}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topology", type=Path, help="Topology JSON file")
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("rules/system_rules_v0.json"),
        help="Engineering rules JSON file",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    topology = json.loads(args.topology.read_text(encoding="utf-8"))
    rules = json.loads(args.rules.read_text(encoding="utf-8"))
    result = validate_topology(topology, rules)
    print(json.dumps(result, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
