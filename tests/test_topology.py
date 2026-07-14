import json
from copy import deepcopy
from pathlib import Path

from lt_cad.topology import validate_topology


ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / "rules" / "system_rules_v0.json").read_text())
EXAMPLE = json.loads(
    (ROOT / "examples" / "topology" / "simple_drying_line.json").read_text()
)


def test_confirmed_simple_line_is_valid() -> None:
    result = validate_topology(EXAMPLE, RULES)
    assert result["errors"] == []
    assert result["warnings"] == [
        "Inferred component requires approval: catchbox-1"
    ]


def test_reversed_vacuum_air_is_rejected() -> None:
    topology = deepcopy(EXAMPLE)
    vacuum = next(c for c in topology["connections"] if c["medium"] == "vacuum_air")
    vacuum["source"], vacuum["target"] = vacuum["target"], vacuum["source"]
    result = validate_topology(topology, RULES)
    assert any("LT -(vacuum_air)-> SVR" in error for error in result["errors"])


def test_missing_catchbox_transport_is_rejected() -> None:
    topology = deepcopy(EXAMPLE)
    topology["connections"] = [
        connection
        for connection in topology["connections"]
        if connection["medium"] != "dried_material"
    ]
    result = validate_topology(topology, RULES)
    assert any(
        "catchbox-1 requires outgoing dried_material" in error
        for error in result["errors"]
    )


def test_unknown_component_reference_is_rejected() -> None:
    topology = deepcopy(EXAMPLE)
    topology["connections"][0]["target"] = "missing"
    result = validate_topology(topology, RULES)
    assert any("unknown component" in error for error in result["errors"])

