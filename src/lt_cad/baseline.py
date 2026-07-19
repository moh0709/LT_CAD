"""Render the standard single-line drying and conveying principle sketch."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from lt_cad.layout import _nested_svg, _raster_b64
from lt_cad.routing import (
    drying_air_circuit_routes,
    rounded_orthogonal_path,
    route_collisions,
    route_direction_arrow,
)
from lt_cad.anchors import anchor_point
from lt_cad.grid import Box, Grid, validate_top_mount


def _callout(number: int, cx: float, cy: float, tx: float, ty: float) -> str:
    return (
        f'<line x1="{cx}" y1="{cy + 5}" x2="{tx}" y2="{ty}" class="callout-line"/>'
        f'<circle cx="{cx}" cy="{cy}" r="5" class="callout-circle"/>'
        f'<text x="{cx}" y="{cy + 1.8}" class="callout-number">{number}</text>'
    )


def _dh_floor_frame(box: Box, policy: dict[str, object]) -> str:
    """Render the mandatory, visible floor frame around the DH discharge area."""
    left_x = box.x + box.width * float(policy["left_leg_x_ratio"])
    right_x = box.x + box.width * float(policy["right_leg_x_ratio"])
    top_y = box.y + box.height * float(policy["top_y_ratio"])
    floor_y = box.bottom
    foot = float(policy["foot_width_mm"])
    stroke = float(policy["line_width_mm"])
    return (
        f'<g data-component="dh-floor-frame" fill="none" stroke="#111" '
        f'stroke-width="{stroke}" stroke-linecap="square">'
        f'<line x1="{left_x}" y1="{top_y}" x2="{left_x}" y2="{floor_y}"/>'
        f'<line x1="{right_x}" y1="{top_y}" x2="{right_x}" y2="{floor_y}"/>'
        f'<line x1="{left_x}" y1="{top_y}" x2="{right_x}" y2="{top_y}"/>'
        f'<line x1="{left_x - foot / 2}" y1="{floor_y}" '
        f'x2="{left_x + foot / 2}" y2="{floor_y}"/>'
        f'<line x1="{right_x - foot / 2}" y1="{floor_y}" '
        f'x2="{right_x + foot / 2}" y2="{floor_y}"/>'
        '</g>'
    )


def create_baseline_svg(repo_root: Path, output: Path, metadata: dict[str, str]) -> None:
    def raster(path: str, box: Box, mirror_x: bool = False) -> str:
        return _raster_b64(repo_root / path, *box.tuple(), mirror_x=mirror_x)

    def cad(path: str, x: float, y: float, width: float, height: float) -> str:
        return _nested_svg(repo_root / path, x, y, width, height)

    order = html.escape(metadata.get("order_number", "STANDARD"))
    revision = html.escape(metadata.get("revision", "R00"))
    customer = html.escape(metadata.get("customer", "TBD"))
    agent = html.escape(metadata.get("agent", "TBD"))
    date = html.escape(metadata.get("date", "TBD"))

    layout_rules = json.loads(
        (repo_root / "rules" / "layout_rules_v0.json").read_text(encoding="utf-8")
    )
    view_registry = json.loads(
        (repo_root / "component_library" / "manifest" / "views_v0.json").read_text(
            encoding="utf-8"
        )
    )
    views = {view["id"]: view for view in view_registry["views"]}

    def registered_anchor(view_id: str, anchor_id: str) -> dict[str, object]:
        for anchor in views[view_id]["anchors"]:
            if anchor["id"] == anchor_id:
                return anchor
        raise ValueError(f"Registered anchor not found: {view_id}/{anchor_id}")

    grid = Grid(layout_rules["grid"]["unit_mm"])
    svr_policy = layout_rules["component_size_policies"]["SVR"]
    dh_frame_policy = layout_rules["component_requirements"]["DH"]["frame_symbol"]
    conveying_route_policy = layout_rules["conveying_route_style"]
    conveying_route_width = conveying_route_policy["stroke_width_mm"]
    drying_air_policy = layout_rules["process_air_circuit"]
    svr_fixed_size = (svr_policy["width_mm"], svr_policy["height_mm"])
    mount_rules = {rule["host_family"]: rule for rule in layout_rules["mounting_rules"]}
    dh_mount_offset = mount_rules["DH"]["host_mounting_plane_offset_from_box_top_mm"]
    ext_mount_offset = mount_rules["EXT"]["host_mounting_plane_offset_from_box_top_mm"]
    boxes = {
        "source": grid.box(120, 120, 25, 35),
        # 35:95 follows the complete DH800 CAD extent, including its floor frame.
        "dh": grid.box(160, 60, 35, 95),
        "dfd": grid.box(205, 105, 35, 45),
        "catchbox": grid.box(170, 135, 20, 35),
        "ext1": grid.box(260, 110, 45, 45),
        "ext2": grid.box(315, 110, 45, 45),
        "lt": grid.box(385, 130, 15, 25),
    }
    boxes["dh_svr"] = grid.mounted_on_top(
        boxes["dh"], *svr_fixed_size, host_surface_offset=dh_mount_offset
    )
    boxes["ext1_svr"] = grid.mounted_on_top(
        boxes["ext1"], *svr_fixed_size, host_surface_offset=ext_mount_offset
    )
    boxes["ext2_svr"] = grid.mounted_on_top(
        boxes["ext2"], *svr_fixed_size, host_surface_offset=ext_mount_offset
    )
    for child_id, host_id, offset in (
        ("dh_svr", "dh", dh_mount_offset),
        ("ext1_svr", "ext1", ext_mount_offset),
        ("ext2_svr", "ext2", ext_mount_offset),
    ):
        mount_errors = validate_top_mount(
            boxes[child_id], boxes[host_id], host_surface_offset=offset
        )
        if mount_errors:
            raise ValueError(f"{child_id} mounting invalid: {mount_errors}")

    svr_material = registered_anchor("svr-reference-front", "material-side")
    svr_vacuum = registered_anchor("svr-reference-front", "vacuum-top")
    catchbox_upper = registered_anchor("catchbox-reference-side", "material-upper")
    catchbox_lower = registered_anchor("catchbox-reference-side", "material-lower")
    dh_material_port = anchor_point(svr_material, boxes["dh_svr"].tuple(), mirror_x=True)
    dh_vacuum_port = anchor_point(svr_vacuum, boxes["dh_svr"].tuple(), mirror_x=True)
    ext1_material_port = anchor_point(svr_material, boxes["ext1_svr"].tuple(), mirror_x=True)
    ext1_vacuum_port = anchor_point(svr_vacuum, boxes["ext1_svr"].tuple(), mirror_x=True)
    ext2_material_port = anchor_point(svr_material, boxes["ext2_svr"].tuple(), mirror_x=True)
    ext2_vacuum_port = anchor_point(svr_vacuum, boxes["ext2_svr"].tuple(), mirror_x=True)
    catchbox_upper_port = anchor_point(catchbox_upper, boxes["catchbox"].tuple())
    catchbox_lower_port = anchor_point(catchbox_lower, boxes["catchbox"].tuple())

    # Approved standard process-air anchors. The DH reference view faces a DFD on
    # its left; this baseline has the DFD on the right, so both DH side anchors are
    # mirrored with the component connection side.
    dfd_supply_port = anchor_point(
        registered_anchor("dfd-family-left-side", "drying-air-supply-top"),
        boxes["dfd"].tuple(),
    )
    dfd_return_port = anchor_point(
        registered_anchor("dfd-family-left-side", "drying-air-return-top"),
        boxes["dfd"].tuple(),
    )
    dh_supply_port = anchor_point(
        registered_anchor("dh-family-front", "drying-air-supply-side"),
        boxes["dh"].tuple(),
        mirror_x=True,
    )
    dh_return_port = anchor_point(
        registered_anchor("dh-family-front", "drying-air-return-side"),
        boxes["dh"].tuple(),
        mirror_x=True,
    )

    obstacles = {
        key: box.tuple() for key, box in boxes.items()
    }
    routes = {
        "undried": [(132.5, 120), (132.5, dh_material_port[1]), dh_material_port],
        "dried_ext1": [catchbox_upper_port, (200, catchbox_upper_port[1]), (200, 175), (250, 175), (250, ext1_material_port[1]), ext1_material_port],
        "dried_ext2": [catchbox_lower_port, (205, catchbox_lower_port[1]), (205, 185), (310, 185), (310, ext2_material_port[1]), ext2_material_port],
        "vacuum_header": [dh_vacuum_port, (155, dh_vacuum_port[1]), (155, 15), (375, 15), (375, 142.5), (385, 142.5)],
        "vacuum_ext1_tee": [ext1_vacuum_port, (250, ext1_vacuum_port[1]), (250, 15)],
        "vacuum_ext2_tee": [ext2_vacuum_port, (305, ext2_vacuum_port[1]), (305, 15)],
    }
    drying_air_routes = drying_air_circuit_routes(
        dfd_supply_port,
        dfd_return_port,
        dh_supply_port,
        dh_return_port,
    )
    drying_air_arrows = {
        route_id: route_direction_arrow(points)
        for route_id, points in drying_air_routes.items()
    }
    collision_rules = {
        "undried": {"source", "dh_svr"},
        "dried_ext1": {"catchbox", "ext1_svr"},
        "dried_ext2": {"catchbox", "ext2_svr"},
        "vacuum_header": {"dh_svr", "lt"},
        "vacuum_ext1_tee": {"ext1_svr"},
        "vacuum_ext2_tee": {"ext2_svr"},
    }
    for route_id, points in routes.items():
        collisions = route_collisions(points, obstacles, ignore=collision_rules[route_id], clearance=1)
        if collisions:
            raise ValueError(f"Route {route_id} crosses component borders: {collisions}")
    for route_id, points in drying_air_routes.items():
        collisions = route_collisions(
            points,
            obstacles,
            ignore={"dh", "dfd"},
            clearance=1,
        )
        if collisions:
            raise ValueError(
                f"Drying-air route {route_id} crosses component borders: {collisions}"
            )

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="420mm" height="297mm" viewBox="0 0 420 297">',
        '<rect width="420" height="297" fill="white"/>',
        ('<g opacity=".18" stroke="#6aa9d8" stroke-width=".2">' + ''.join(f'<path d="M {x} 10 V 180"/>' for x in range(75, 411, 5)) + ''.join(f'<path d="M 75 {y} H 410"/>' for y in range(10, 181, 5)) + '</g>') if metadata.get("show_grid") == "true" else '',
        '<style>text{font-family:Arial,sans-serif;fill:#111}.component path{vector-effect:non-scaling-stroke;stroke-width:.28!important}'
        '.equipment{font-size:4px;font-weight:bold}.small{font-size:3px}.legend{font-size:3.3px}'
        '.callout-circle{fill:white;stroke:#ff3030;stroke-width:.35}.callout-line{stroke:#ff3030;stroke-width:.35}'
        '.callout-number{font-size:4px;fill:#ff3030;text-anchor:middle}.title{font-size:4.5px}'
        f'.route{{fill:none;stroke-width:{conveying_route_width};stroke-linejoin:round}}.process-air{{fill:none;stroke-linecap:butt;stroke-linejoin:round}}'
        '.ground{stroke:#111;stroke-width:.45}</style>',
        '<defs><marker id="arrow-cyan" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#35C4CF"/></marker>'
        '<marker id="arrow-process" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker></defs>',
        # Floor and hatch.
        '<line x1="75" y1="155" x2="410" y2="155" class="ground"/>',
        '<path d="' + ' '.join(f'M{x} 154 l-4 6' for x in range(78, 411, 8)) + '" stroke="#777" stroke-width=".3" fill="none"/>',
        '<text x="88" y="145" font-size="6">±3</text>',
        # Undried material source bin.
        '<rect x="120" y="120" width="25" height="35" fill="none" stroke="#111" stroke-width=".45"/>',
        '<path d="M120 133 h25 M120 138 h25 M120 143 h25 M120 148 h25" stroke="#31d843" stroke-width="1.5"/>',
        '<line x1="132.5" y1="110" x2="132.5" y2="153" stroke="#111" stroke-width=".8"/>',
        # Confirmed/reference components.
        cad("component_library/previews/dh-family-front.svg", *boxes["dh"].tuple()),
        _dh_floor_frame(boxes["dh"], dh_frame_policy),
        cad("component_library/previews/dfd-family-left-side.svg", *boxes["dfd"].tuple()),
        raster("component_library/raster/catchbox.png.b64", boxes["catchbox"]),
        raster("component_library/raster/svr.png.b64", boxes["dh_svr"], mirror_x=True),
        raster("component_library/raster/extruder.png.b64", boxes["ext1"]),
        raster("component_library/raster/svr.png.b64", boxes["ext1_svr"], mirror_x=True),
        raster("component_library/raster/extruder.png.b64", boxes["ext2"]),
        raster("component_library/raster/svr.png.b64", boxes["ext2_svr"], mirror_x=True),
        raster("component_library/raster/lt-family.png.b64", boxes["lt"]),
        # Standard closed DFD/DH drying-air circuit: DFD top ports to DH side ports.
        f'<path data-route="drying-air-supply" d="{rounded_orthogonal_path(drying_air_routes["supply"], drying_air_policy["bend_radius_mm"])}" class="process-air" stroke="#222" stroke-width="{drying_air_policy["outer_line_width_mm"]}"/>',
        f'<path d="{rounded_orthogonal_path(drying_air_routes["supply"], drying_air_policy["bend_radius_mm"])}" class="process-air" stroke="white" stroke-width="{drying_air_policy["inner_line_width_mm"]}"/>',
        f'<path data-route="drying-air-return" d="{rounded_orthogonal_path(drying_air_routes["return"], drying_air_policy["bend_radius_mm"])}" class="process-air" stroke="#222" stroke-width="{drying_air_policy["outer_line_width_mm"]}"/>',
        f'<path d="{rounded_orthogonal_path(drying_air_routes["return"], drying_air_policy["bend_radius_mm"])}" class="process-air" stroke="white" stroke-width="{drying_air_policy["inner_line_width_mm"]}"/>',
        f'<line data-flow-arrow="drying-air-supply" x1="{drying_air_arrows["supply"][0][0]}" y1="{drying_air_arrows["supply"][0][1]}" x2="{drying_air_arrows["supply"][1][0]}" y2="{drying_air_arrows["supply"][1][1]}" stroke="#555" stroke-width=".4" marker-end="url(#arrow-process)"/>',
        f'<line data-flow-arrow="drying-air-return" x1="{drying_air_arrows["return"][0][0]}" y1="{drying_air_arrows["return"][0][1]}" x2="{drying_air_arrows["return"][1][0]}" y2="{drying_air_arrows["return"][1][1]}" stroke="#555" stroke-width=".4" marker-end="url(#arrow-process)"/>',
        # Green undried material route: source to receiver above DH.
        f'<path d="{rounded_orthogonal_path(routes["undried"], 4)}" class="route" stroke="#31D843"/>',
        # Separate magenta material lines from the catchbox outlets to both receivers.
        f'<path data-route="dried-material-ext1" d="{rounded_orthogonal_path(routes["dried_ext1"], 5)}" class="route" stroke="#D52AA3"/>',
        f'<path data-route="dried-material-ext2" d="{rounded_orthogonal_path(routes["dried_ext2"], 5)}" class="route" stroke="#D52AA3"/>',
        # Shared turquoise vacuum header with one T-branch from each EXT receiver.
        f'<path data-route="vacuum-header" d="{rounded_orthogonal_path(routes["vacuum_header"], 5)}" class="route" stroke="#35C4CF" marker-end="url(#arrow-cyan)"/>',
        f'<path data-route="vacuum-tee-ext1" d="{rounded_orthogonal_path(routes["vacuum_ext1_tee"], 4)}" class="route" stroke="#35C4CF"/>',
        f'<path data-route="vacuum-tee-ext2" d="{rounded_orthogonal_path(routes["vacuum_ext2_tee"], 4)}" class="route" stroke="#35C4CF"/>',
        # Labels.
        '<text x="180" y="176" class="equipment" text-anchor="middle">CATCHBOX</text>',
        '<text x="222.5" y="154" class="equipment" text-anchor="middle">DFD</text>',
        '<text x="177.5" y="154" class="equipment" text-anchor="middle">DH</text>',
        '<text x="282.5" y="154" class="equipment" text-anchor="middle">EXT 1</text>',
        '<text x="337.5" y="154" class="equipment" text-anchor="middle">EXT 2</text>',
        '<text x="392.5" y="160" class="equipment" text-anchor="middle">LT</text>',
        # Red item callouts matching the baseline convention.
        _callout(1, 238, 96, 225, 112),
        _callout(2, 160, 84, 168, 105),
        _callout(3, 157, 132, 175, 145),
        _callout(4, 177, 37, 180, 52),
        _callout(4, 276, 68, 278, 83),
        _callout(4, 331, 68, 333, 83),
        _callout(4, 407, 119, 389, 139),
        _callout(5, 239, 126, 225, 141),
        # Equipment list.
        '<g class="legend">',
        '<circle cx="20" cy="181" r="5" class="callout-circle"/><text x="20" y="182.5" class="callout-number">5</text><text x="30" y="182.5">Mobile Frame</text>',
        '<circle cx="20" cy="193" r="5" class="callout-circle"/><text x="20" y="194.5" class="callout-number">4</text><text x="30" y="194.5">Con-Evator SVR / LT</text>',
        '<circle cx="20" cy="205" r="5" class="callout-circle"/><text x="20" y="206.5" class="callout-number">3</text><text x="30" y="206.5">Catchbox</text>',
        '<circle cx="20" cy="217" r="5" class="callout-circle"/><text x="20" y="218.5" class="callout-number">2</text><text x="30" y="218.5">Drying Hopper DH</text>',
        '<circle cx="20" cy="229" r="5" class="callout-circle"/><text x="20" y="230.5" class="callout-number">1</text><text x="30" y="230.5">Desiccant Flex Dryer DFD</text>',
        '</g>',
        # Route legend.
        '<g class="small"><text x="172" y="222">Route Description</text>',
        '<line x1="172" y1="228" x2="193" y2="228" stroke="#35C4CF" stroke-width="1"/><text x="197" y="229">Vacuum pipe line</text>',
        '<line x1="172" y1="234" x2="193" y2="234" stroke="#D52AA3" stroke-width="1"/><text x="197" y="235">Dried material line</text>',
        '<line x1="172" y1="240" x2="193" y2="240" stroke="#31D843" stroke-width="1"/><text x="197" y="241">Undried material line</text></g>',
        # Title block.
        '<rect x="5" y="250" width="410" height="42" fill="white" stroke="#111" stroke-width=".45"/>',
        '<rect x="5" y="250" width="125" height="42" fill="white" stroke="#111" stroke-width=".45"/>',
        '<text x="14" y="268" font-size="14" fill="#063ee8" style="fill:#063ee8;font-weight:bold;font-style:italic">Labotek</text>',
        '<text x="35" y="276" font-size="5">Power in Plastics</text>',
        '<line x1="130" y1="264" x2="415" y2="264" stroke="#111" stroke-width=".35"/>',
        '<line x1="130" y1="278" x2="415" y2="278" stroke="#111" stroke-width=".35"/>',
        f'<text x="133" y="258" class="small">Customer: {customer}</text>',
        '<text x="133" y="262.5" class="title">Description: Principle Sketch - Drying &amp; Conveying equipment</text>',
        f'<text x="133" y="271" class="small">Agent: {agent}</text>',
        f'<text x="320" y="271" class="small">Date: {date}</text>',
        '<text x="380" y="271" class="small">Scale: NTS</text>',
        f'<text x="133" y="286" class="small">Our ref: LT_CAD</text>',
        f'<text x="318" y="288" font-size="8">{order}_1_{revision}</text>',
        '</svg>',
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(parts), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--order-number", default="STANDARD")
    parser.add_argument("--revision", default="R00")
    parser.add_argument("--customer", default="TBD")
    parser.add_argument("--agent", default="TBD")
    parser.add_argument("--date", default="TBD")
    parser.add_argument("--show-grid", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    create_baseline_svg(
        args.repo_root,
        args.output,
        {
            "order_number": args.order_number,
            "revision": args.revision,
            "customer": args.customer,
            "agent": args.agent,
            "date": args.date,
            "show_grid": "true" if args.show_grid else "false",
        },
    )


if __name__ == "__main__":
    main()
