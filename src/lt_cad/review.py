"""Add numbered review markers to an SVG component preview."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


VIEWBOX = re.compile(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)"')


def create_review_svg(source: Path, output: Path, markers: list[dict]) -> None:
    svg = source.read_text(encoding="utf-8")
    match = VIEWBOX.search(svg)
    if not match:
        raise ValueError(f"SVG has no supported viewBox: {source}")
    x0, y0, width, height = (float(value) for value in match.groups())
    radius = min(width, height) * 0.025
    elements = [
        '<g id="lt-cad-review-markers" font-family="Arial, sans-serif" '
        'font-weight="bold" text-anchor="middle">'
    ]
    for marker in markers:
        x = x0 + marker["x"] * width
        y = y0 + (1.0 - marker["y"]) * height
        elements.append(
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius:.3f}" '
            'fill="#ffd400" stroke="#d00000" stroke-width="4000"/>'
        )
        elements.append(
            f'<text x="{x:.3f}" y="{y + radius * 0.34:.3f}" '
            f'font-size="{radius * 1.15:.3f}" fill="#111111">{marker["id"]}</text>'
        )
    elements.append("</g>")
    annotated = svg.replace("</svg>", "".join(elements) + "</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(annotated, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("view_id")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    view = next(item for item in registry["views"] if item["id"] == args.view_id)
    create_review_svg(args.source, args.output, view.get("review_markers", []))


if __name__ == "__main__":
    main()
