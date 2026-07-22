import json
from copy import deepcopy
from pathlib import Path

from lt_cad.quotation import component_instances, validate_quotation


ROOT = Path(__file__).resolve().parents[1]
QUOTATION = json.loads(
    (ROOT / "examples" / "quotations" / "1094811.json").read_text()
)


def test_1094811_quotation_is_valid() -> None:
    assert validate_quotation(QUOTATION) == {"errors": [], "warnings": []}


def test_1094811_component_coverage() -> None:
    instances = component_instances(QUOTATION)
    assert [(item["family"], item["model"]) for item in instances] == [
        ("DFD", "DFD450"),
        ("DFD", "DFD300"),
        ("DH", "DH2000-III"),
        ("SVR_LT_ASSEMBLY", "SVR26/LT5-I"),
    ]


def test_duplicate_positions_are_rejected() -> None:
    quotation = deepcopy(QUOTATION)
    quotation["items"][1]["position"] = 1
    result = validate_quotation(quotation)
    assert "Duplicate quotation position: 1" in result["errors"]


def test_component_requires_model() -> None:
    quotation = deepcopy(QUOTATION)
    del quotation["items"][0]["model"]
    result = validate_quotation(quotation)
    assert any("requires family and model" in error for error in result["errors"])
