import json
from pathlib import Path

from lt_cad.proposal import (
    _vacuum_system_for_receiver_count,
    create_multiline_central_conveying_proposal_svg,
)
from lt_cad.quotation import validate_quotation


ROOT = Path(__file__).resolve().parents[1]
QUOTATION = json.loads(
    (ROOT / "examples" / "quotations" / "labotek_studio_qt_2026-07-22.json").read_text()
)


def test_labotek_studio_quotation_is_valid() -> None:
    assert validate_quotation(QUOTATION) == {"errors": [], "warnings": []}


def test_three_shared_receivers_require_micro_scan() -> None:
    lines = QUOTATION["conveying_lines"]
    assert len(lines) == 3
    assert all(line["blower"] == "SHARED LT4" for line in lines)
    assert all(
        _vacuum_system_for_receiver_count(line["shared_receiver_count"])
        == "Micro Scan"
        for line in lines
    )
    central = QUOTATION["central_conveying_override"]
    assert central["receiver_model"] == "SVR8"
    assert central["receiver_quantity"] == 3
    assert central["central_blower_model"] == "LT4"
    assert central["central_blower_quantity"] == 1


def test_labotek_studio_generates_three_line_proposal(tmp_path: Path) -> None:
    output = tmp_path / "labotek-studio.svg"
    create_multiline_central_conveying_proposal_svg(QUOTATION, ROOT, output)
    svg = output.read_text(encoding="utf-8")
    for label in (
        "DFD450",
        "DH1600",
        "EHR-100",
        "CATCHBOX 3 x Ø50 mm",
        "PA6 / 210 kg/h / 80 C / 4.0 h",
        "EXT 1",
        "EXT 2",
        "EXT 3",
        "MICRO SCAN: 3 x scanning SVR8 / central LT4",
    ):
        assert label in svg
    assert svg.count('data-route="dried-material-line-') == 3
    assert 'data-route="vacuum-header"' in svg
    assert svg.count('data-route="vacuum-tee-') == 2
    assert svg.count('data-component="extruder"') == 3
    assert "MICRO SCAN" in svg
    assert "Con-Evator" not in svg
    assert "SVR 75 L" not in svg
    assert ">LT3<" not in svg
    assert svg.count(">CENTRAL LT4<") == 1
    assert "Cyclone 10 L" in svg
    assert "placement pending confirmation" in svg
