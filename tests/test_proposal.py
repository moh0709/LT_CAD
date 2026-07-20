import json
from pathlib import Path

from lt_cad.proposal import create_drying_proposal_svg
from lt_cad.quotation import validate_quotation


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = json.loads(
    (ROOT / "examples" / "quotations" / "drying_calculator_2025.json").read_text()
)


def test_drying_calculator_proposal_is_valid_without_order_number() -> None:
    assert validate_quotation(PROPOSAL) == {"errors": [], "warnings": []}
    assert PROPOSAL["project_reference"] == "DRYING-CALCULATOR-2025"


def test_drying_calculator_generates_quoted_topology_only(tmp_path: Path) -> None:
    output = tmp_path / "proposal.svg"
    create_drying_proposal_svg(PROPOSAL, ROOT, output)
    svg = output.read_text(encoding="utf-8")
    for label in ("DFD450", "EHR-100", "DH1600", "CATCHBOX 3 x 50"):
        assert label in svg
    assert 'data-route="drying-air-supply-before-ehr"' in svg
    assert 'data-route="drying-air-supply-after-ehr"' in svg
    assert 'data-route="drying-air-return"' in svg
    assert "MICRO SCAN" not in svg
    assert "EXT 1" not in svg
    assert "Vacuum station / receiver not quoted." in svg
