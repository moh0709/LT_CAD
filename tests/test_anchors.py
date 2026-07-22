import json
from copy import deepcopy
from pathlib import Path

from lt_cad.anchors import anchor_point, validate_views


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads(
    (ROOT / "component_library" / "manifest" / "views_v0.json").read_text()
)


def test_view_registry_is_valid_with_approved_standard_anchors() -> None:
    result = validate_views(REGISTRY)
    assert result["errors"] == []
    assert result["warnings"] == []


def test_unreviewed_anchors_cannot_be_used_for_routing() -> None:
    registry = deepcopy(REGISTRY)
    registry["views"][0]["anchor_status"] = "needs_review"
    registry["views"][0]["anchors"] = [
        {"id": "air-out", "medium": "drying_air", "direction": "out", "x": 0.5, "y": 0.5}
    ]
    result = validate_views(registry)
    assert any("not approved for routing" in error for error in result["errors"])


def test_approved_anchor_coordinates_must_be_normalized() -> None:
    registry = deepcopy(REGISTRY)
    view = registry["views"][0]
    view["anchor_status"] = "approved"
    view["anchors"] = [
        {"id": "air-out", "medium": "drying_air", "direction": "out", "x": 1.1, "y": 0.5}
    ]
    result = validate_views(registry)
    assert any("x must be normalized" in error for error in result["errors"])


def test_dfd_and_dh_process_air_anchors_are_approved() -> None:
    dfd = REGISTRY["views"][0]
    dh = REGISTRY["views"][1]
    assert dfd["geometry_status"] == "approved_family_standard"
    assert dfd["anchor_status"] == "approved"
    assert {anchor["id"] for anchor in dfd["anchors"]} == {
        "drying-air-supply-top",
        "drying-air-return-top",
    }
    assert dh["geometry_status"] == "approved_family_standard"
    assert dh["source_block"] == "MODEL_SPACE_COMPOSITE"
    assert {anchor["id"] for anchor in dh["anchors"]} >= {
        "drying-air-supply-side",
        "drying-air-return-side",
    }


def test_microscan_svs_vacuum_anchor_is_top_entry() -> None:
    svs = next(view for view in REGISTRY["views"] if view["family"] == "SVS")
    inlet = next(anchor for anchor in svs["anchors"] if anchor["id"] == "vacuum-header-inlet")
    assert inlet["side"] == "top"
    assert inlet["x"] == 0.270
    assert inlet["y"] == 1.000
    assert anchor_point(inlet, (375, 135, 30, 20)) == (383.1, 135.0)


def test_review_marker_coordinates_must_be_normalized() -> None:
    registry = deepcopy(REGISTRY)
    registry["views"][0]["review_markers"] = [
        {"id": "P1", "x": 0.5, "y": -0.1, "question": "Test"}
    ]
    result = validate_views(registry)
    assert any("P1 y must be normalized" in error for error in result["errors"])


def test_anchor_point_mirrors_horizontally() -> None:
    anchor = {"x": 0.2, "y": 0.75}
    bounds = (10, 20, 100, 200)
    assert anchor_point(anchor, bounds) == (30, 70)
    assert anchor_point(anchor, bounds, mirror_x=True) == (90, 70)
