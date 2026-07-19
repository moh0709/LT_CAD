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
    for text in (
        "DFD",
        "DH",
        "CATCHBOX",
        "EXT 1",
        "EXT 2",
        "MICRO SCAN SVS / LT6-I",
        "1094222_1_R01",
    ):
        assert text in svg
    for colour in ("#35C4CF", "#D52AA3", "#31D843"):
        assert colour in svg
    assert 'data-route="drying-air-supply"' in svg
    assert 'data-route="drying-air-return"' in svg
    assert 'data-flow-arrow="drying-air-supply"' in svg
    assert 'data-flow-arrow="drying-air-return"' in svg
    assert 'data-component="dh-floor-frame"' in svg
    assert 'data-route="dried-material-ext1"' in svg
    assert 'data-route="dried-material-ext2"' in svg
    assert 'data-route="vacuum-header"' in svg
    assert 'data-route="vacuum-tee-ext1"' in svg
    assert 'data-route="vacuum-tee-ext2"' in svg
    assert 'data-component="micro-scan-svs"' in svg
    assert '.route{fill:none;stroke-width:2.25' in svg
    assert "Principle Sketch - Drying &amp; Conveying equipment" in svg
