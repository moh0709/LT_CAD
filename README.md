# LT_CAD

AI-assisted 2D principle-sketch designer for Labotek drying and vacuum-conveying systems.

The project uses an open-source CAD pipeline:

- `ezdxf` for reading, analysing, creating and writing DXF files.
- GNU LibreDWG as an optional DWG-to-DXF import bridge.
- LibreCAD for optional manual DXF inspection.

DXF is the canonical editable format. PDF and SVG are presentation outputs. The large
master library remains in OneDrive; this repository stores its link, lightweight
metadata, extraction scripts and reviewed component blocks.

## Current status

Component Catalogue V0 validates that the supplied master DXF can be opened directly:

- DXF R2004, millimetres
- 771,477 model-space entities
- 2,104 block definitions
- 97 layers
- 999 block insertions referencing 575 unique blocks

Candidate DFD, DH, SVR, LT and WAM blocks have been identified. They remain
`needs_review` until their preferred view, insertion point and pipe anchors are approved.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
lt-cad-inventory "/path/to/Tegnings oversigt.dxf" --output output/inventory.json
lt-cad-render "/path/to/Tegnings oversigt.dxf" svr26 output/svr26.svg
pytest
```

## Repository layout

```text
component_library/manifest/   Machine-readable component catalogue
docs/                         Architecture and catalogue guidance
master_library/               Link to externally stored source CAD
src/lt_cad/                   DXF inventory and rendering tools
tests/                        Automated checks
```

## Licensing

The project licence is intentionally pending owner confirmation. GPL-3.0-or-later is
recommended if GNU LibreDWG is distributed as an integrated part of the application.

