import json
from pathlib import Path

from lt_cad.proposal import (
    _vacuum_system_for_receiver_count,
    create_con_evator_proposal_svg,
)
from lt_cad.quotation import validate_quotation


ROOT = Path(__file__).resolve().parents[1]
QUOTATION = json.loads(
    (ROOT / "examples" / "quotations" / "1090052.json").read_text()
)


def test_1090052_quotation_is_valid() -> None:
    assert validate_quotation(QUOTATION) == {"errors": [], "warnings": []}


def test_1090052_generates_drying_and_extruder_conveying_topology(tmp_path: Path) -> None:
    output = tmp_path / "1090052.svg"
    create_con_evator_proposal_svg(QUOTATION, ROOT, output)
    svg = output.read_text(encoding="utf-8")
    for label in (
        "DFD600",
        "DH1200-III",
        "SVR16",
        "MICRO SCAN SVS / LT6-I",
        "CATCHBOX 50 mm",
        "EXT 1",
    ):
        assert label in svg
    assert 'data-route="vacuum-header"' in svg
    assert 'data-route="vacuum-tee-ext1"' in svg
    assert 'data-route="undried-material"' in svg
    assert 'data-route="dried-material-ext1"' in svg
    assert 'data-route="drying-air-supply"' in svg
    assert 'data-route="drying-air-return"' in svg
    assert "MICRO SCAN" in svg
    assert "Con-Evator" not in svg
    assert "LT4-I" not in svg
    assert "CUSTOMER EXTRUDER" in svg


def test_1090052_design_additions_are_machine_readable() -> None:
    additions = {item["family"]: item for item in QUOTATION["design_additions"]}
    assert additions["CATCHBOX"]["model"] == "CATCHBOX-50"
    assert additions["CATCHBOX"]["mounted_below"] == "DH1200-III"
    assert additions["SVR"]["mounted_on"] == "ext-1"
    assert additions["SVS"]["model"] == "SVS-I/LT6-I"


def test_two_receivers_can_never_select_con_evator() -> None:
    assert _vacuum_system_for_receiver_count(1) == "Con-Evator"
    assert _vacuum_system_for_receiver_count(2) == "Micro Scan"
    assert _vacuum_system_for_receiver_count(8) == "Micro Scan"
