from pathlib import Path

from lt_cad.review import create_review_svg


def test_review_svg_adds_numbered_marker(tmp_path: Path) -> None:
    source = tmp_path / "source.svg"
    output = tmp_path / "review.svg"
    source.write_text('<svg viewBox="0 0 100 200"></svg>', encoding="utf-8")
    create_review_svg(source, output, [{"id": "P1", "x": 0.25, "y": 0.75}])
    result = output.read_text(encoding="utf-8")
    assert 'id="lt-cad-review-markers"' in result
    assert ">P1</text>" in result
    assert 'cx="25.000"' in result
    assert 'cy="50.000"' in result
