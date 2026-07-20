import json
from pathlib import Path

from lt_cad.proposal import create_con_evator_proposal_svg
from lt_cad.quotation import validate_quotation


ROOT = Path(__file__).resolve().parents[1]
QUOTATION = json.loads(
    (ROOT / "examples" / "quotations" / "1090052.json").read_text()
)


def test_1090052_quotation_is_valid() -> None:
    assert validate_quotation(QUOTATION) == {"errors": [], "warnings": []}


def test_1090052_generates_one_to_one_con_evator_topology(tmp_path: Path) -> None:
    output = tmp_path / "1090052.svg"
    create_con_evator_proposal_svg(QUOTATION, ROOT, output)
    svg = output.read_text(encoding="utf-8")
    for label in ("DFD600", "DH1200-III", "SVR16", "LT4-I"):
        assert label in svg
    assert 'data-route="con-evator-vacuum"' in svg
    assert 'data-route="undried-material"' in svg
    assert 'data-route="drying-air-supply"' in svg
    assert 'data-route="drying-air-return"' in svg
    assert "MICRO SCAN" not in svg
    assert "CATCHBOX" not in svg
    assert "EXT 1" not in svg
