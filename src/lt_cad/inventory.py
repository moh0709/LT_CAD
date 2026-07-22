"""Inventory a DXF master library without modifying the source file."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import ezdxf


def inventory(path: Path) -> dict[str, object]:
    doc = ezdxf.readfile(path)
    modelspace = doc.modelspace()
    entity_types = Counter(entity.dxftype() for entity in modelspace)
    insert_names = Counter(
        entity.dxf.name
        for entity in modelspace.query("INSERT")
        if entity.dxf.hasattr("name")
    )
    blocks = sorted(block.name for block in doc.blocks)
    return {
        "source": str(path),
        "file_size_bytes": path.stat().st_size,
        "dxf_version": doc.dxfversion,
        "acad_release": doc.acad_release,
        "insunits": doc.header.get("$INSUNITS"),
        "extmin": list(doc.header.get("$EXTMIN", ())),
        "extmax": list(doc.header.get("$EXTMAX", ())),
        "layers": sorted(layer.dxf.name for layer in doc.layers),
        "layouts": [layout.name for layout in doc.layouts],
        "blocks": blocks,
        "modelspace_entities": len(modelspace),
        "modelspace_entity_types": dict(entity_types.most_common()),
        "modelspace_insert_references": sum(insert_names.values()),
        "unique_inserted_blocks": len(insert_names),
        "inserted_blocks": dict(insert_names.most_common()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dxf", type=Path, help="Input DXF file")
    parser.add_argument("--output", "-o", type=Path, help="Optional JSON output path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = json.dumps(inventory(args.dxf), indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + "\n", encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()

