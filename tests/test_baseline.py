from pathlib import Path

from lt_cad.baseline import create_baseline_svg


ROOT = Path(__file__).resolve().parents[1]


def test_baseline_contains_standard_equipment_and_routes(tmp_path: Path) -> None:
    output = tmp_path / "baseline.svg"
    create_baseline_svg(
        ROOT,
        output,
        {"order_number": "1094222", "revision": "R01", "customer": "Example"},
    )
    svg = output.read_text(encoding="utf-8")
    for text in ("DFD", "DH", "CATCHBOX", "EXT 1", "LT", "1094222_1_R01"):
        assert text in svg
    for colour in ("#35C4CF", "#D52AA3", "#31D843"):
        assert colour in svg
    assert 'data-route="drying-air-supply"' in svg
    assert 'data-route="drying-air-return"' in svg
    assert 'data-flow-arrow="drying-air-supply"' in svg
    assert 'data-flow-arrow="drying-air-return"' in svg
    assert "Principle Sketch - Drying &amp; Conveying equipment" in svg
