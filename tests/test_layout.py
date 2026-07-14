import json
from copy import deepcopy
from pathlib import Path

from lt_cad.layout import create_layout_svg, validate_layout


ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (ROOT / "examples" / "layouts" / "1094811_a3_review.json").read_text()
)


def test_1094811_layout_is_valid() -> None:
    assert validate_layout(SPEC) == []


def test_1094811_layout_contains_all_quoted_equipment(tmp_path: Path) -> None:
    output = tmp_path / "layout.svg"
    create_layout_svg(SPEC, ROOT, output)
    svg = output.read_text(encoding="utf-8")
    for label in ("DFD450", "DFD300", "DH2000-III", "SVR26", "LT5-I"):
        assert label in svg
    assert "PIPING NOT RELEASED" in svg


def test_duplicate_layout_ids_are_rejected() -> None:
    spec = deepcopy(SPEC)
    spec["items"][1]["id"] = spec["items"][0]["id"]
    assert any("Duplicate layout item id" in error for error in validate_layout(spec))
