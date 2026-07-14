"""Render one named DXF block to a monochrome SVG preview."""

from __future__ import annotations

import argparse
from pathlib import Path

import ezdxf
from ezdxf.addons import Importer
from ezdxf.addons.drawing import Frontend, RenderContext, layout
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.svg import SVGBackend


def render_block(source: Path, block_name: str, output: Path) -> None:
    source_doc = ezdxf.readfile(source)
    source_doc.blocks.get(block_name)  # Fail clearly when the block does not exist.

    target_doc = ezdxf.new("R2004")
    importer = Importer(source_doc, target_doc)
    imported_name = importer.import_block(block_name, rename=False)
    importer.finalize()
    target_doc.modelspace().add_blockref(imported_name, (0, 0))

    backend = SVGBackend()
    config = Configuration(
        color_policy=ColorPolicy.BLACK,
        background_policy=BackgroundPolicy.WHITE,
        min_lineweight=0.15,
    )
    Frontend(RenderContext(target_doc), backend, config=config).draw_layout(
        target_doc.modelspace(), finalize=True
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(backend.get_string(layout.Page(0, 0)), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dxf", type=Path, help="Input DXF file")
    parser.add_argument("block", help="Exact DXF block name")
    parser.add_argument("output", type=Path, help="Output SVG path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    render_block(args.dxf, args.block, args.output)


if __name__ == "__main__":
    main()
