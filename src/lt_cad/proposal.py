"""Generate an A3 drying-system principle sketch from normalized proposal data."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from lt_cad.anchors import anchor_point
from lt_cad.baseline import _callout, _dh_floor_frame
from lt_cad.grid import Grid, validate_top_mount
from lt_cad.layout import _nested_svg, _raster_b64
from lt_cad.quotation import component_instances, validate_quotation
from lt_cad.routing import (
    rounded_orthogonal_path,
    route_collisions,
    route_direction_arrow,
)


def _one_component(quotation: dict[str, Any], family: str) -> dict[str, Any]:
    matches = [item for item in component_instances(quotation) if item["family"] == family]
    if len(matches) != 1:
        raise ValueError(f"Proposal drawing requires exactly one {family}; found {len(matches)}.")
    return matches[0]


def _vacuum_system_for_receiver_count(receiver_count: int) -> str:
    """Select the only permitted vacuum architecture for the receiver count."""
    if receiver_count < 1:
        raise ValueError("A conveying system requires at least one SVR.")
    return "Con-Evator" if receiver_count == 1 else "Micro Scan"


def create_drying_proposal_svg(
    quotation: dict[str, Any], repo_root: Path, output: Path
) -> None:
    validation = validate_quotation(quotation)
    if validation["errors"]:
        raise ValueError("; ".join(validation["errors"]))

    dfd = _one_component(quotation, "DFD")
    dh = _one_component(quotation, "DH")
    ehr = _one_component(quotation, "EHR")
    catchbox = _one_component(quotation, "CATCHBOX")
    calculation = quotation["calculation"]
    reference = str(quotation.get("order_number") or quotation["project_reference"])
    customer = quotation.get("customer") or "TBD"
    date = quotation.get("quotation_date", "TBD")

    layout_rules = json.loads(
        (repo_root / "rules" / "layout_rules_v0.json").read_text(encoding="utf-8")
    )
    views_data = json.loads(
        (repo_root / "component_library" / "manifest" / "views_v0.json").read_text(
            encoding="utf-8"
        )
    )
    views = {view["id"]: view for view in views_data["views"]}

    def registered_anchor(view_id: str, anchor_id: str) -> dict[str, Any]:
        return next(
            anchor for anchor in views[view_id]["anchors"] if anchor["id"] == anchor_id
        )

    grid = Grid(layout_rules["grid"]["unit_mm"])
    boxes = {
        "dfd": grid.box(100, 110, 40, 50),
        "ehr": grid.box(185, 95, 20, 65),
        "dh": grid.box(250, 60, 40, 100),
        "catchbox": grid.box(260, 130, 20, 35),
    }
    dh_frame_policy = layout_rules["component_requirements"]["DH"]["frame_symbol"]
    drying_policy = layout_rules["process_air_circuit"]

    dfd_supply = anchor_point(
        registered_anchor("dfd-family-left-side", "drying-air-supply-top"),
        boxes["dfd"].tuple(),
    )
    dfd_return = anchor_point(
        registered_anchor("dfd-family-left-side", "drying-air-return-top"),
        boxes["dfd"].tuple(),
    )
    dh_supply = anchor_point(
        registered_anchor("dh-family-front", "drying-air-supply-side"),
        boxes["dh"].tuple(),
    )
    dh_return = anchor_point(
        registered_anchor("dh-family-front", "drying-air-return-side"),
        boxes["dh"].tuple(),
    )

    ehr_left = (boxes["ehr"].x, dh_supply[1])
    ehr_right = (boxes["ehr"].right, dh_supply[1])
    supply_before_ehr = [dfd_supply, (dfd_supply[0], dh_supply[1]), ehr_left]
    supply_after_ehr = [ehr_right, dh_supply]
    supply_for_arrow = [dfd_supply, (dfd_supply[0], dh_supply[1]), dh_supply]
    return_route = [dh_return, (dfd_return[0], dh_return[1]), dfd_return]
    supply_arrow = route_direction_arrow(supply_for_arrow)
    return_arrow = route_direction_arrow(return_route)

    def duct(points: list[tuple[float, float]], route_id: str) -> str:
        path = rounded_orthogonal_path(points, drying_policy["bend_radius_mm"])
        return (
            f'<path data-route="{route_id}" d="{path}" class="process-air" '
            f'stroke="#222" stroke-width="{drying_policy["outer_line_width_mm"]}"/>'
            f'<path d="{path}" class="process-air" stroke="white" '
            f'stroke-width="{drying_policy["inner_line_width_mm"]}"/>'
        )

    optional_names = [
        item["description"]
        for item in quotation["items"]
        if item.get("placement_status") == "unresolved_no_vacuum_station_quoted"
    ]

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="420mm" height="297mm" viewBox="0 0 420 297">',
        '<rect width="420" height="297" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111}.component path{vector-effect:non-scaling-stroke;stroke-width:.28!important}.equipment{font-size:4px;font-weight:bold}.small{font-size:3px}.legend{font-size:3.3px}.callout-circle{fill:white;stroke:#ff3030;stroke-width:.35}.callout-line{stroke:#ff3030;stroke-width:.35}.callout-number{font-size:4px;fill:#ff3030;text-anchor:middle}.title{font-size:4.5px}.process-air{fill:none;stroke-linecap:butt;stroke-linejoin:round}.ground{stroke:#111;stroke-width:.45}.note-box{fill:#fff8d7;stroke:#b78b00;stroke-width:.35}</style>',
        '<defs><marker id="arrow-process" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker></defs>',
        '<line x1="65" y1="160" x2="305" y2="160" class="ground"/>',
        '<path d="' + ' '.join(f'M{x} 159 l-4 6' for x in range(68, 306, 8)) + '" stroke="#777" stroke-width=".3" fill="none"/>',
        _nested_svg(repo_root / "component_library/previews/dfd-family-left-side.svg", *boxes["dfd"].tuple()),
        _nested_svg(repo_root / "component_library/previews/ehr-reference.svg", *boxes["ehr"].tuple()),
        _nested_svg(repo_root / "component_library/previews/dh-family-front.svg", *boxes["dh"].tuple()),
        _dh_floor_frame(boxes["dh"], dh_frame_policy),
        _raster_b64(repo_root / "component_library/raster/catchbox.png.b64", *boxes["catchbox"].tuple()),
        duct(supply_before_ehr, "drying-air-supply-before-ehr"),
        duct(supply_after_ehr, "drying-air-supply-after-ehr"),
        duct(return_route, "drying-air-return"),
        f'<line data-flow-arrow="drying-air-supply" x1="{supply_arrow[0][0]}" y1="{supply_arrow[0][1]}" x2="{supply_arrow[1][0]}" y2="{supply_arrow[1][1]}" stroke="#555" stroke-width=".4" marker-end="url(#arrow-process)"/>',
        f'<line data-flow-arrow="drying-air-return" x1="{return_arrow[0][0]}" y1="{return_arrow[0][1]}" x2="{return_arrow[1][0]}" y2="{return_arrow[1][1]}" stroke="#555" stroke-width=".4" marker-end="url(#arrow-process)"/>',
        '<text x="120" y="166" class="equipment" text-anchor="middle">DFD450</text>',
        '<text x="195" y="166" class="equipment" text-anchor="middle">EHR-100</text>',
        '<text x="270" y="166" class="equipment" text-anchor="middle">DH1600</text>',
        '<text x="270" y="173" class="equipment" text-anchor="middle">CATCHBOX 3 x 50</text>',
        _callout(1, 92, 102, 108, 118),
        _callout(2, 177, 87, 190, 104),
        _callout(3, 246, 48, 257, 76),
        _callout(4, 244, 133, 263, 145),
        '<rect x="315" y="48" width="92" height="78" rx="2" fill="white" stroke="#555" stroke-width=".35"/>',
        '<text x="320" y="57" font-size="4.5" font-weight="bold">CALCULATION BASIS</text>',
        f'<text x="320" y="66" class="small">Material: {html.escape(str(calculation["material"]))}</text>',
        f'<text x="320" y="73" class="small">Throughput: {calculation["throughput_kg_h"]:g} kg/h</text>',
        f'<text x="320" y="80" class="small">Drying temperature: {calculation["drying_temperature_c"]:g} C</text>',
        f'<text x="320" y="87" class="small">Residence time: {calculation["residence_time_min"]:g} min</text>',
        f'<text x="320" y="94" class="small">Required airflow: {calculation["required_process_airflow_m3_h"]:g} m3/h</text>',
        f'<text x="320" y="101" class="small">Required hopper: {calculation["required_hopper_volume_l"]:g} L</text>',
        f'<text x="320" y="108" class="small">Selected hopper: 1600 L</text>',
        f'<text x="320" y="115" class="small">Water removal: {calculation["water_removal_kg_h"]:.2f} kg/h</text>',
        '<rect x="315" y="133" width="92" height="38" rx="2" class="note-box"/>',
        '<text x="320" y="141" font-size="3.5" font-weight="bold">UNPLACED OPTIONS</text>',
        f'<text x="320" y="149" class="small">- {html.escape(optional_names[0])}</text>',
        f'<text x="320" y="156" class="small">- {html.escape(optional_names[1])}</text>',
        '<text x="320" y="164" font-size="2.7">Vacuum station / receiver not quoted.</text>',
        '<g class="legend">',
        '<circle cx="20" cy="184" r="5" class="callout-circle"/><text x="20" y="185.5" class="callout-number">1</text><text x="30" y="185.5">Desiccant Flex Dryer DFD450</text>',
        '<circle cx="20" cy="196" r="5" class="callout-circle"/><text x="20" y="197.5" class="callout-number">2</text><text x="30" y="197.5">External Heat Recovery EHR-100</text>',
        '<circle cx="20" cy="208" r="5" class="callout-circle"/><text x="20" y="209.5" class="callout-number">3</text><text x="30" y="209.5">Drying Hopper DH1600 with frame</text>',
        '<circle cx="20" cy="220" r="5" class="callout-circle"/><text x="20" y="221.5" class="callout-number">4</text><text x="30" y="221.5">Catchbox, 3 x 50 mm, manual</text>',
        '</g>',
        '<g class="small"><text x="175" y="205">Route Description</text><line x1="175" y1="212" x2="198" y2="212" stroke="#222" stroke-width="2.2"/><line x1="175" y1="212" x2="198" y2="212" stroke="white" stroke-width="1.4"/><text x="203" y="213">Closed process-air circuit</text><circle cx="176" cy="220" r="2" fill="#35C4CF"/><text x="182" y="221">EHR hot-water customer connection</text></g>',
        '<rect x="5" y="250" width="410" height="42" fill="white" stroke="#111" stroke-width=".45"/>',
        '<rect x="5" y="250" width="125" height="42" fill="white" stroke="#111" stroke-width=".45"/>',
        '<text x="14" y="268" font-size="14" fill="#063ee8" style="fill:#063ee8;font-weight:bold;font-style:italic">Labotek</text>',
        '<text x="35" y="276" font-size="5">Power in Plastics</text>',
        '<line x1="130" y1="264" x2="415" y2="264" stroke="#111" stroke-width=".35"/>',
        '<line x1="130" y1="278" x2="415" y2="278" stroke="#111" stroke-width=".35"/>',
        f'<text x="133" y="258" class="small">Customer: {html.escape(str(customer))}</text>',
        '<text x="133" y="262.5" class="title">Description: Principle Sketch - DFD450 / EHR-100 / DH1600</text>',
        '<text x="133" y="271" class="small">Source: Drying Calculator 2025</text>',
        f'<text x="320" y="271" class="small">Date: {html.escape(str(date))}</text>',
        '<text x="380" y="271" class="small">Scale: NTS</text>',
        '<text x="133" y="286" class="small">Status: Proposal test - topology based on quoted equipment only</text>',
        f'<text x="305" y="288" font-size="7">{html.escape(reference)}_1_R00</text>',
        '</svg>',
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(parts), encoding="utf-8")


def create_con_evator_proposal_svg(
    quotation: dict[str, Any], repo_root: Path, output: Path
) -> None:
    """Render a standard DFD/DH system with the receiver-count vacuum architecture."""
    validation = validate_quotation(quotation)
    if validation["errors"]:
        raise ValueError("; ".join(validation["errors"]))

    dfd = _one_component(quotation, "DFD")
    dh = _one_component(quotation, "DH")
    con_evator = _one_component(quotation, "SVR_LT_ASSEMBLY")
    additions = {item["family"]: item for item in quotation.get("design_additions", [])}
    include_dried_destination = {"CATCHBOX", "EXT", "SVR"}.issubset(additions)
    receiver_count = 1 + int(include_dried_destination)
    vacuum_system = _vacuum_system_for_receiver_count(receiver_count)
    use_micro_scan = vacuum_system == "Micro Scan"
    if use_micro_scan and additions.get("SVS", {}).get("model") != "SVS-I/LT6-I":
        raise ValueError("Two or more SVRs require a registered Micro Scan SVS station.")
    reference = str(quotation["order_number"])
    customer = str(quotation.get("customer") or "TBD")
    agent = str(quotation.get("agent") or "TBD")
    date = str(quotation.get("quotation_date") or "TBD")

    layout_rules = json.loads(
        (repo_root / "rules" / "layout_rules_v0.json").read_text(encoding="utf-8")
    )
    views_data = json.loads(
        (repo_root / "component_library" / "manifest" / "views_v0.json").read_text(
            encoding="utf-8"
        )
    )
    views = {view["id"]: view for view in views_data["views"]}

    def registered_anchor(view_id: str, anchor_id: str) -> dict[str, Any]:
        return next(
            anchor for anchor in views[view_id]["anchors"] if anchor["id"] == anchor_id
        )

    grid = Grid(layout_rules["grid"]["unit_mm"])
    svr_policy = layout_rules["component_size_policies"]["SVR"]
    svs_policy = layout_rules["component_size_policies"]["SVS"]
    mount_rules = {
        rule["host_family"]: rule for rule in layout_rules["mounting_rules"]
    }
    boxes = {
        "source": grid.box(65, 125, 25, 35),
        "dh": grid.box(110, 60, 35, 100),
        "dfd": grid.box(180, 105, 45, 55),
        "station": grid.box(
            365,
            140,
            svs_policy["width_mm"] if use_micro_scan else 20,
            svs_policy["height_mm"] if use_micro_scan else 20,
        ),
    }
    boxes["svr"] = grid.mounted_on_top(
        boxes["dh"],
        svr_policy["width_mm"],
        svr_policy["height_mm"],
        host_surface_offset=mount_rules["DH"]["host_mounting_plane_offset_from_box_top_mm"],
    )
    if include_dried_destination:
        boxes["catchbox"] = grid.box(120, 135, 20, 35)
        boxes["ext"] = grid.box(285, 120, 45, 40)
        boxes["ext_svr"] = grid.mounted_on_top(
            boxes["ext"],
            svr_policy["width_mm"],
            svr_policy["height_mm"],
            host_surface_offset=mount_rules["EXT"]["host_mounting_plane_offset_from_box_top_mm"],
        )
        mount_errors = validate_top_mount(
            boxes["ext_svr"],
            boxes["ext"],
            host_surface_offset=mount_rules["EXT"]["host_mounting_plane_offset_from_box_top_mm"],
        )
        if mount_errors:
            raise ValueError(f"Extruder SVR mounting invalid: {mount_errors}")
    dh_frame_policy = layout_rules["component_requirements"]["DH"]["frame_symbol"]
    drying_policy = layout_rules["process_air_circuit"]
    route_width = layout_rules["conveying_route_style"]["stroke_width_mm"]

    dfd_supply = anchor_point(
        registered_anchor("dfd-family-left-side", "drying-air-supply-top"),
        boxes["dfd"].tuple(),
    )
    dfd_return = anchor_point(
        registered_anchor("dfd-family-left-side", "drying-air-return-top"),
        boxes["dfd"].tuple(),
    )
    dh_supply = anchor_point(
        registered_anchor("dh-family-front", "drying-air-supply-side"),
        boxes["dh"].tuple(),
        mirror_x=True,
    )
    dh_return = anchor_point(
        registered_anchor("dh-family-front", "drying-air-return-side"),
        boxes["dh"].tuple(),
        mirror_x=True,
    )
    svr_material = anchor_point(
        registered_anchor("svr-reference-front", "material-side"),
        boxes["svr"].tuple(),
        mirror_x=True,
    )
    svr_vacuum = anchor_point(
        registered_anchor("svr-reference-front", "vacuum-top"),
        boxes["svr"].tuple(),
        mirror_x=True,
    )
    if include_dried_destination:
        catchbox_material = anchor_point(
            registered_anchor("catchbox-reference-side", "material-upper"),
            boxes["catchbox"].tuple(),
        )
        ext_material = anchor_point(
            registered_anchor("svr-reference-front", "material-side"),
            boxes["ext_svr"].tuple(),
            mirror_x=True,
        )
        ext_vacuum = anchor_point(
            registered_anchor("svr-reference-front", "vacuum-top"),
            boxes["ext_svr"].tuple(),
            mirror_x=True,
        )

    supply_route = [dfd_supply, (dfd_supply[0], dh_supply[1]), dh_supply]
    return_route = [dh_return, (dfd_return[0], dh_return[1]), dfd_return]
    supply_arrow = route_direction_arrow(supply_route)
    return_arrow = route_direction_arrow(return_route)
    undried_route = [
        (boxes["source"].center_x, boxes["source"].y),
        (boxes["source"].center_x, svr_material[1]),
        svr_material,
    ]
    station_vacuum_port = (
        anchor_point(
            registered_anchor("svs-microscan-reference", "vacuum-header-inlet"),
            boxes["station"].tuple(),
        )
        if use_micro_scan
        else (
            boxes["station"].x + boxes["station"].width * 0.25,
            boxes["station"].y,
        )
    )
    vacuum_route = [
        svr_vacuum,
        (100, svr_vacuum[1]),
        (100, 15),
        (station_vacuum_port[0], 15),
        station_vacuum_port,
    ]
    if include_dried_destination:
        dried_route = [
            catchbox_material,
            (155, catchbox_material[1]),
            (155, 178),
            (278, 178),
            (278, ext_material[1]),
            ext_material,
        ]
        ext_vacuum_tee = [
            ext_vacuum,
            (270, ext_vacuum[1]),
            (270, 15),
        ]

    obstacles = {name: box.tuple() for name, box in boxes.items()}
    conveying_routes = {
        "undried-material": (undried_route, {"source", "svr"}),
        "vacuum-header": (vacuum_route, {"svr", "station"}),
    }
    if include_dried_destination:
        conveying_routes.update(
            {
                "dried-material-ext1": (
                    dried_route,
                    {"catchbox", "dh", "ext_svr"},
                ),
                "vacuum-tee-ext1": (ext_vacuum_tee, {"ext_svr"}),
            }
        )
    for route_id, (points, ignored) in conveying_routes.items():
        collisions = route_collisions(points, obstacles, ignore=ignored, clearance=1)
        if collisions:
            raise ValueError(f"Route {route_id} crosses component borders: {collisions}")

    def duct(points: list[tuple[float, float]], route_id: str) -> str:
        path = rounded_orthogonal_path(points, drying_policy["bend_radius_mm"])
        return (
            f'<path data-route="{route_id}" d="{path}" class="process-air" '
            f'stroke="#222" stroke-width="{drying_policy["outer_line_width_mm"]}"/>'
            f'<path d="{path}" class="process-air" stroke="white" '
            f'stroke-width="{drying_policy["inner_line_width_mm"]}"/>'
        )

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="420mm" height="297mm" viewBox="0 0 420 297">',
        '<rect width="420" height="297" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111}.component path{vector-effect:non-scaling-stroke;stroke-width:.28!important}.equipment{font-size:4px;font-weight:bold}.small{font-size:3px}.legend{font-size:3.3px}.callout-circle{fill:white;stroke:#ff3030;stroke-width:.35}.callout-line{stroke:#ff3030;stroke-width:.35}.callout-number{font-size:4px;fill:#ff3030;text-anchor:middle}.title{font-size:4.5px}.route{fill:none;stroke-linejoin:round}.process-air{fill:none;stroke-linecap:butt;stroke-linejoin:round}.ground{stroke:#111;stroke-width:.45}</style>',
        '<defs><marker id="arrow-process" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker></defs>',
        '<line x1="55" y1="160" x2="395" y2="160" class="ground"/>',
        '<path d="' + ' '.join(f'M{x} 159 l-4 6' for x in range(58, 396, 8)) + '" stroke="#777" stroke-width=".3" fill="none"/>',
        '<rect x="65" y="125" width="25" height="35" fill="none" stroke="#111" stroke-width=".45"/>',
        '<path d="M65 138 h25 M65 143 h25 M65 148 h25 M65 153 h25" stroke="#31D843" stroke-width="1.1"/>',
        '<line x1="77.5" y1="118" x2="77.5" y2="158" stroke="#111" stroke-width=".65"/>',
        _nested_svg(repo_root / "component_library/previews/dh-family-front.svg", *boxes["dh"].tuple()),
        _dh_floor_frame(boxes["dh"], dh_frame_policy),
        _nested_svg(repo_root / "component_library/previews/dfd-family-left-side.svg", *boxes["dfd"].tuple()),
        _raster_b64(repo_root / "component_library/raster/svr.png.b64", *boxes["svr"].tuple(), mirror_x=True),
        _raster_b64(repo_root / "component_library/raster/catchbox.png.b64", *boxes["catchbox"].tuple()) if include_dried_destination else "",
        _raster_b64(repo_root / "component_library/raster/extruder.png.b64", *boxes["ext"].tuple()) if include_dried_destination else "",
        _raster_b64(repo_root / "component_library/raster/svr.png.b64", *boxes["ext_svr"].tuple(), mirror_x=True) if include_dried_destination else "",
        _raster_b64(
            repo_root
            / (
                "component_library/raster/svs.png.b64"
                if use_micro_scan
                else "component_library/raster/lt-family.png.b64"
            ),
            *boxes["station"].tuple(),
        ),
        duct(supply_route, "drying-air-supply"),
        duct(return_route, "drying-air-return"),
        f'<line data-flow-arrow="drying-air-supply" x1="{supply_arrow[0][0]}" y1="{supply_arrow[0][1]}" x2="{supply_arrow[1][0]}" y2="{supply_arrow[1][1]}" stroke="#555" stroke-width=".4" marker-end="url(#arrow-process)"/>',
        f'<line data-flow-arrow="drying-air-return" x1="{return_arrow[0][0]}" y1="{return_arrow[0][1]}" x2="{return_arrow[1][0]}" y2="{return_arrow[1][1]}" stroke="#555" stroke-width=".4" marker-end="url(#arrow-process)"/>',
        f'<path data-route="undried-material" d="{rounded_orthogonal_path(undried_route, 4)}" class="route" stroke="#31D843" stroke-width="{route_width}"/>',
        f'<path data-route="vacuum-header" d="{rounded_orthogonal_path(vacuum_route, 5)}" class="route" stroke="#35C4CF" stroke-width="{route_width}"/>',
        f'<path data-route="vacuum-tee-ext1" d="{rounded_orthogonal_path(ext_vacuum_tee, 4)}" class="route" stroke="#35C4CF" stroke-width="{route_width}"/>' if include_dried_destination else "",
        f'<path data-route="dried-material-ext1" d="{rounded_orthogonal_path(dried_route, 5)}" class="route" stroke="#D52AA3" stroke-width="{route_width}"/>' if include_dried_destination else "",
        '<text x="77.5" y="170" class="equipment" text-anchor="middle">CUSTOMER MATERIAL SOURCE</text>',
        f'<text x="127.5" y="166" class="equipment" text-anchor="middle">{html.escape(dh["model"])}</text>',
        '<text x="129" y="181" class="equipment" text-anchor="middle">CATCHBOX 50 mm</text>' if include_dried_destination else "",
        f'<text x="202.5" y="166" class="equipment" text-anchor="middle">{html.escape(dfd["model"])}</text>',
        '<text x="307.5" y="166" class="equipment" text-anchor="middle">EXT 1 - CUSTOMER EXTRUDER</text>' if include_dried_destination else "",
        '<text x="380" y="166" class="equipment" text-anchor="middle">MICRO SCAN SVS / LT6-I</text>' if use_micro_scan else '<text x="375" y="166" class="equipment" text-anchor="middle">LT4-I</text>',
        '<text x="127.5" y="26" class="equipment" text-anchor="middle">SVR16</text>',
        '<text x="307.5" y="76" class="equipment" text-anchor="middle">SVR16</text>' if include_dried_destination else "",
        _callout(1, 229, 96, 207, 116),
        _callout(2, 106, 86, 119, 109),
        _callout(3, 151, 139, 135, 150) if include_dried_destination else "",
        _callout(4, 146, 35, 131, 49),
        _callout(4, 285, 73, 303, 90) if include_dried_destination else "",
        _callout(4, 405, 128, 373, 145),
        _callout(5, 340, 118, 318, 134) if include_dried_destination else "",
        _callout(6, 175, 68, 191, 84),
        '<g class="legend">',
        '<circle cx="20" cy="181" r="5" class="callout-circle"/><text x="20" y="182.5" class="callout-number">1</text><text x="30" y="182.5">Desiccant Flex Dryer DFD600</text>',
        '<circle cx="20" cy="193" r="5" class="callout-circle"/><text x="20" y="194.5" class="callout-number">2</text><text x="30" y="194.5">Drying Hopper DH1200-III with frame</text>',
        '<circle cx="20" cy="205" r="5" class="callout-circle"/><text x="20" y="206.5" class="callout-number">3</text><text x="30" y="206.5">Catchbox 50 mm</text>',
        '<circle cx="20" cy="217" r="5" class="callout-circle"/><text x="20" y="218.5" class="callout-number">4</text><text x="30" y="218.5">Scanning SVRs / Micro Scan SVS / LT6-I</text>' if use_micro_scan else '<circle cx="20" cy="217" r="5" class="callout-circle"/><text x="20" y="218.5" class="callout-number">4</text><text x="30" y="218.5">Con-Evator SVR16 / LT4-I</text>',
        '<circle cx="20" cy="229" r="5" class="callout-circle"/><text x="20" y="230.5" class="callout-number">5</text><text x="30" y="230.5">Customer extruder EXT 1</text>',
        '<circle cx="20" cy="241" r="5" class="callout-circle"/><text x="20" y="242.5" class="callout-number">6</text><text x="30" y="242.5">Interconnecting duct system DFD600</text>',
        '</g>',
        '<g class="small"><text x="180" y="199">Route Description</text><line x1="180" y1="207" x2="203" y2="207" stroke="#35C4CF" stroke-width="1.5"/><text x="208" y="208">Vacuum pipe line</text><line x1="180" y1="215" x2="203" y2="215" stroke="#D52AA3" stroke-width="1.5"/><text x="208" y="216">Dried material line</text><line x1="180" y1="223" x2="203" y2="223" stroke="#31D843" stroke-width="1.5"/><text x="208" y="224">Undried material line</text><line x1="180" y1="231" x2="203" y2="231" stroke="#222" stroke-width="2.2"/><line x1="180" y1="231" x2="203" y2="231" stroke="white" stroke-width="1.4"/><text x="208" y="232">Closed process-air circuit</text></g>',
        '<rect x="5" y="250" width="410" height="42" fill="white" stroke="#111" stroke-width=".45"/>',
        '<rect x="5" y="250" width="125" height="42" fill="white" stroke="#111" stroke-width=".45"/>',
        '<text x="14" y="268" font-size="14" fill="#063ee8" style="fill:#063ee8;font-weight:bold;font-style:italic">Labotek</text>',
        '<text x="35" y="276" font-size="5">Power in Plastics</text>',
        '<line x1="130" y1="264" x2="415" y2="264" stroke="#111" stroke-width=".35"/>',
        '<line x1="130" y1="278" x2="415" y2="278" stroke="#111" stroke-width=".35"/>',
        f'<text x="133" y="258" class="small">Customer: {html.escape(customer)}</text>',
        '<text x="133" y="262.5" class="title">Description: Principle Sketch - Standard Drying &amp; Conveying system</text>',
        f'<text x="133" y="271" class="small">Agent: {html.escape(agent)}</text>',
        f'<text x="320" y="271" class="small">Date: {html.escape(date)}</text>',
        '<text x="380" y="271" class="small">Scale: NTS</text>',
        '<text x="133" y="286" class="small">Source: Quotation 1090052 + approved Micro Scan override</text>',
        f'<text x="330" y="288" font-size="8">{html.escape(reference)}_1_R02</text>',
        '</svg>',
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(parts), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quotation", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    quotation = json.loads(args.quotation.read_text(encoding="utf-8"))
    families = {item.get("family") for item in quotation.get("items", [])}
    if "SVR_LT_ASSEMBLY" in families:
        create_con_evator_proposal_svg(quotation, args.repo_root, args.output)
    else:
        create_drying_proposal_svg(quotation, args.repo_root, args.output)


if __name__ == "__main__":
    main()
