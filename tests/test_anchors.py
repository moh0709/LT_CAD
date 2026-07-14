import json
from copy import deepcopy
from pathlib import Path

from lt_cad.anchors import anchor_point, validate_views


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads(
    (ROOT / "component_library" / "manifest" / "views_v0.json").read_text()
)


def test_view_registry_is_valid_but_flags_reviews() -> None:
    result = validate_views(REGISTRY)
    assert result["errors"] == []
    assert len(result["warnings"]) == 2


def test_unreviewed_anchors_cannot_be_used_for_routing() -> None:
    registry = deepcopy(REGISTRY)
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


def test_geometry_can_be_approved_before_anchors() -> None:
    dfd = REGISTRY["views"][0]
    assert dfd["geometry_status"] == "approved_family_standard"
    assert dfd["anchor_status"] == "needs_review"
    assert dfd["anchors"] == []


def test_review_marker_coordinates_must_be_normalized() -> None:
    registry = deepcopy(REGISTRY)
    registry["views"][0]["review_markers"][0]["y"] = -0.1
    result = validate_views(registry)
    assert any("P1 y must be normalized" in error for error in result["errors"])


def test_anchor_point_mirrors_horizontally() -> None:
    anchor = {"x": 0.2, "y": 0.75}
    bounds = (10, 20, 100, 200)
    assert anchor_point(anchor, bounds) == (30, 70)
    assert anchor_point(anchor, bounds, mirror_x=True) == (90, 70)
