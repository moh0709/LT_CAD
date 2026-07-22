import json
from pathlib import Path

from lt_cad.proposal import (
    _vacuum_system_for_receiver_count,
    create_multiline_con_evator_proposal_svg,
)
from lt_cad.quotation import validate_quotation


ROOT = Path(__file__).resolve().parents[1]
QUOTATION = json.loads(
    (ROOT / "examples" / "quotations" / "labotek_studio_qt_2026-07-22.json").read_text()
)


def test_labotek_studio_quotation_is_valid() -> None:
    assert validate_quotation(QUOTATION) == {"errors": [], "warnings": []}


def test_three_independent_lines_are_three_con_evators() -> None:
    lines = QUOTATION["conveying_lines"]
    assert len(lines) == 3
    assert all(line["blower"] == "LT3" for line in lines)
    assert all(
        _vacuum_system_for_receiver_count(line["shared_receiver_count"])
        == "Con-Evator"
        for line in lines
    )


def test_labotek_studio_generates_three_line_proposal(tmp_path: Path) -> None:
    output = tmp_path / "labotek-studio.svg"
    create_multiline_con_evator_proposal_svg(QUOTATION, ROOT, output)
    svg = output.read_text(encoding="utf-8")
    for label in (
        "DFD450",
        "DH1600",
        "EHR-100",
        "CATCHBOX 3 x Ø50 mm",
        "PA6 / 210 kg/h / 80 C / 4.0 h",
        "MACHINE 1",
        "MACHINE 2",
        "MACHINE 3",
        "3 x Con-Evator SVR 75 L / LT3",
    ):
        assert label in svg
    assert svg.count('data-route="dried-material-line-') == 3
    assert svg.count('data-route="vacuum-line-') == 3
    assert "MICRO SCAN" not in svg
    assert "Cyclone 10 L" in svg
    assert "placement pending confirmation" in svg
