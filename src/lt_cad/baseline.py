"""Render the standard single-line drying and conveying principle sketch."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from lt_cad.layout import _nested_svg, _raster_b64
from lt_cad.routing import rounded_orthogonal_path, route_collisions
from lt_cad.anchors import anchor_point


def _callout(number: int, cx: float, cy: float, tx: float, ty: float) -> str:
    return (
        f'<line x1="{cx}" y1="{cy + 5}" x2="{tx}" y2="{ty}" class="callout-line"/>'
        f'<circle cx="{cx}" cy="{cy}" r="5" class="callout-circle"/>'
        f'<text x="{cx}" y="{cy + 1.8}" class="callout-number">{number}</text>'
    )


def create_baseline_svg(repo_root: Path, output: Path, metadata: dict[str, str]) -> None:
    def raster(path: str, x: float, y: float, width: float, height: float) -> str:
        return _raster_b64(repo_root / path, x, y, width, height)

    def cad(path: str, x: float, y: float, width: float, height: float) -> str:
        return _nested_svg(repo_root / path, x, y, width, height)

    order = html.escape(metadata.get("order_number", "STANDARD"))
    revision = html.escape(metadata.get("revision", "R00"))
    customer = html.escape(metadata.get("customer", "TBD"))
    agent = html.escape(metadata.get("agent", "TBD"))
    date = html.escape(metadata.get("date", "TBD"))

    svr_material = {"x": 0.0, "y": 0.625}
    svr_vacuum = {"x": 0.311, "y": 0.925}
    catchbox_upper = {"x": 1.0, "y": 0.354}
    dh_svr_bounds = (174, 48, 12, 32)
    ext_svr_bounds = (283, 80, 10, 28)
    catchbox_bounds = (172, 137, 16, 30)
    dh_material_port = anchor_point(svr_material, dh_svr_bounds)
    dh_vacuum_port = anchor_point(svr_vacuum, dh_svr_bounds)
    ext_material_port = anchor_point(svr_material, ext_svr_bounds)
    ext_vacuum_port = anchor_point(svr_vacuum, ext_svr_bounds)
    catchbox_material_port = anchor_point(catchbox_upper, catchbox_bounds)

    obstacles = {
        "source": (118, 121, 23, 32),
        "dh": (155, 62, 45, 91),
        "dfd": (204, 103, 36, 44),
        "ext": (268, 112, 43, 42),
    }
    routes = {
        "undried": [(129.5, 121), (129.5, dh_material_port[1]), dh_material_port],
        "dried": [catchbox_material_port, (198, catchbox_material_port[1]), (198, 166), (252, 166), (252, ext_material_port[1]), ext_material_port],
        "vacuum_main": [dh_vacuum_port, (165, dh_vacuum_port[1]), (165, 42), (320, 42), (320, 139), (332, 139)],
        "vacuum_ext": [ext_vacuum_port, (275, ext_vacuum_port[1]), (275, 67), (320, 67)],
    }
    collision_rules = {
        "undried": {"source", "dh"},
        "dried": {"dh"},
        "vacuum_main": {"dh"},
        "vacuum_ext": set(),
    }
    for route_id, points in routes.items():
        collisions = route_collisions(points, obstacles, ignore=collision_rules[route_id], clearance=1)
        if collisions:
            raise ValueError(f"Route {route_id} crosses component borders: {collisions}")

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="420mm" height="297mm" viewBox="0 0 420 297">',
        '<rect width="420" height="297" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111}.component path{vector-effect:non-scaling-stroke;stroke-width:.28!important}'
        '.equipment{font-size:4px;font-weight:bold}.small{font-size:3px}.legend{font-size:3.3px}'
        '.callout-circle{fill:white;stroke:#ff3030;stroke-width:.35}.callout-line{stroke:#ff3030;stroke-width:.35}'
        '.callout-number{font-size:4px;fill:#ff3030;text-anchor:middle}.title{font-size:4.5px}'
        '.route{fill:none;stroke-width:2.5;stroke-linejoin:round}.ground{stroke:#111;stroke-width:.45}</style>',
        '<defs><marker id="arrow-cyan" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#35C4CF"/></marker></defs>',
        # Floor and hatch.
        '<line x1="76" y1="154" x2="362" y2="154" class="ground"/>',
        '<path d="M78 154 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6 m12-6 l-4 6" stroke="#777" stroke-width=".3" fill="none"/>',
        '<text x="88" y="145" font-size="6">±3</text>',
        # Undried material source bin.
        '<rect x="118" y="121" width="23" height="32" fill="none" stroke="#111" stroke-width=".45"/>',
        '<path d="M118 133 h23 M118 137 h23 M118 141 h23 M118 145 h23 M118 149 h23" stroke="#31d843" stroke-width="1.5"/>',
        '<line x1="129.5" y1="111" x2="129.5" y2="151" stroke="#111" stroke-width=".8"/>',
        # Confirmed/reference components.
        cad("component_library/previews/dh-family-front.svg", 155, 62, 45, 91),
        cad("component_library/previews/dfd-family-left-side.svg", 204, 103, 36, 44),
        raster("component_library/raster/catchbox.png.b64", 172, 137, 16, 30),
        raster("component_library/raster/svr.png.b64", 174, 48, 12, 32),
        raster("component_library/raster/extruder.png.b64", 268, 112, 43, 42),
        raster("component_library/raster/svr.png.b64", 283, 80, 10, 28),
        raster("component_library/raster/lt-family.png.b64", 332, 130, 14, 22),
        # Drying-air short couplings between DH and DFD.
        '<path d="M199 131 H204 M199 139 H204" fill="none" stroke="#222" stroke-width="1.1"/>',
        # Green undried material route: source to receiver above DH.
        f'<path d="{rounded_orthogonal_path(routes["undried"], 4)}" class="route" stroke="#31D843"/>',
        # Magenta dried-material route below the floor and to EXT receiver.
        f'<path d="{rounded_orthogonal_path(routes["dried"], 5)}" class="route" stroke="#D52AA3"/>',
        # Vacuum return header from both receivers to LT.
        f'<path d="{rounded_orthogonal_path(routes["vacuum_main"], 5)}" class="route" stroke="#35C4CF" marker-end="url(#arrow-cyan)"/>',
        f'<path d="{rounded_orthogonal_path(routes["vacuum_ext"], 4)}" class="route" stroke="#35C4CF"/>',
        # Labels.
        '<text x="177" y="172" class="equipment">CATCHBOX</text>',
        '<text x="217" y="151" class="equipment" text-anchor="middle">DFD</text>',
        '<text x="177" y="151" class="equipment" text-anchor="middle">DH</text>',
        '<text x="289" y="149" class="equipment" text-anchor="middle">EXT 1</text>',
        '<text x="339" y="157" class="equipment" text-anchor="middle">LT</text>',
        # Red item callouts matching the baseline convention.
        _callout(1, 238, 96, 225, 112),
        _callout(2, 160, 84, 168, 105),
        _callout(3, 157, 132, 175, 145),
        _callout(4, 177, 37, 180, 52),
        _callout(4, 286, 68, 288, 83),
        _callout(4, 352, 119, 339, 139),
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
        },
    )


if __name__ == "__main__":
    main()
