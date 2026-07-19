import pytest
import json
from pathlib import Path

from lt_cad.grid import Grid, validate_top_mount


ROOT = Path(__file__).resolve().parents[1]


def test_fixed_svr_mount_contacts_and_centres_on_host() -> None:
    grid = Grid(5)
    host = grid.box(155, 60, 45, 95)
    svr = grid.mounted_on_top(host, 15, 40)
    assert svr.tuple() == (170, 20, 15, 40)
    assert validate_top_mount(svr, host) == []


def test_dh_mount_uses_internal_plate_not_cad_box_top() -> None:
    grid = Grid(5)
    dh = grid.box(155, 60, 45, 95)
    svr = grid.mounted_on_top(dh, 15, 40, host_surface_offset=10)
    assert svr.tuple() == (170, 30, 15, 40)
    assert validate_top_mount(svr, dh, host_surface_offset=10) == []


def test_unsnapped_component_is_rejected() -> None:
    with pytest.raises(ValueError, match="not snapped"):
        Grid(5).box(151, 60, 45, 95)


def test_separated_svr_mount_is_rejected() -> None:
    host = Grid(5).box(270, 110, 45, 45)
    separated = Grid(5).box(285, 65, 15, 40)
    assert "does not contact" in validate_top_mount(separated, host)[0]


def test_machine_readable_svr_policy_matches_mount_contract() -> None:
    rules = json.loads((ROOT / "rules" / "layout_rules_v0.json").read_text())
    policy = rules["component_size_policies"]["SVR"]
    assert (policy["width_mm"], policy["height_mm"]) == (15, 40)
    svs_policy = rules["component_size_policies"]["SVS"]
    assert (svs_policy["width_mm"], svs_policy["height_mm"]) == (30, 20)
    mounts = {rule["host_family"]: rule for rule in rules["mounting_rules"]}
    assert mounts["DH"]["gap_mm"] == 0
    assert mounts["DH"]["horizontal_alignment"] == "center"
    assert mounts["DH"]["host_mounting_plane_offset_from_box_top_mm"] == 10
    assert mounts["EXT"]["host_mounting_plane_offset_from_box_top_mm"] == 0
    dh_requirement = rules["component_requirements"]["DH"]
    assert dh_requirement["frame_required"] is True
    assert dh_requirement["applies_to_all_models"] is True
    assert dh_requirement["placement"] == "frame_bottom_on_floor_line"
    assert dh_requirement["frame_symbol"]["line_width_mm"] == 0.75
    assert dh_requirement["frame_symbol"]["left_leg_x_ratio"] == 0.08
    route_style = rules["conveying_route_style"]
    assert route_style["stroke_width_mm"] == 1.5
    assert route_style["reduction_percent_from_previous"] == 33.33
    assert route_style["reduction_percent_from_original"] == 40
    assert "drying_air" in route_style["excludes"]
    header = rules["shared_vacuum_header"]
    assert header["shared_blower"] is True
    assert header["assembly_type"] == "Micro Scan"
    assert header["station_family"] == "SVS"
    assert header["station_connection_face"] == "top"
    assert header["station_approach"] == "vertical_from_above"
    assert header["branch_connection"] == "tee"
    assert header["branch_per_SVR"] is True
    circuit = rules["process_air_circuit"]
    assert circuit["applies_to_all_DFD_DH_models"] is True
    assert circuit["dfd_connection_face"] == "top"
    assert circuit["dh_connection_face"] == "side_toward_dfd"
    assert circuit["horizontal_segment_policy"] == "stretch_to_machine_spacing"
    assert circuit["flow_arrows_required"] is True


def test_mirrored_svr_material_anchor_meets_visible_left_nozzle() -> None:
    from lt_cad.anchors import anchor_point

    svr = Grid(5).box(170, 30, 15, 40)
    point = anchor_point({"x": 0.844, "y": 0.424}, svr.tuple(), mirror_x=True)
    assert point == pytest.approx((172.34, 53.04))
