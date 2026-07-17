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

Candidate DFD, DH, SVR, LT and WAM blocks have been identified. The supplied DFD300/450
left-side geometry is registered as the DFD family standard. The DH800-III front view is
provisional. Pipe anchors remain `needs_review`, so automatic routing cannot silently use
an unverified connection point.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
lt-cad-inventory "/path/to/Tegnings oversigt.dxf" --output output/inventory.json
lt-cad-render "/path/to/Tegnings oversigt.dxf" svr26 output/svr26.svg
lt-cad-validate-topology examples/topology/simple_drying_line.json
lt-cad-validate-views component_library/manifest/views_v0.json
lt-cad-review-svg component_library/manifest/views_v0.json dfd-family-left-side \
  component_library/previews/dfd-family-left-side.svg output/dfd-review.svg
lt-cad-validate-quotation examples/quotations/1094811.json --instances
lt-cad-layout examples/layouts/1094811_a3_review.json output/1094811-layout.svg
lt-cad-baseline output/standard-baseline.svg --order-number 1094222 --revision R01
lt-cad-baseline output/standard-grid-review.svg --show-grid
pytest
```

## Repository layout

```text
component_library/manifest/   Machine-readable component catalogue and view registry
component_library/previews/   Lightweight CAD-derived vector previews
component_library/reviews/    Numbered port-review drawings
docs/                         Architecture and catalogue guidance
examples/topology/            Example system graphs
examples/quotations/          Normalized quotation data with source provenance
examples/projects/            Design inputs and explicit unresolved decisions
examples/layouts/             Deterministic A3 component-layout specifications
master_library/               Link to externally stored source CAD
rules/                        Confirmed engineering and line rules
src/lt_cad/                   DXF inventory and rendering tools
tests/                        Automated checks
```

## Licensing

The project licence is intentionally pending owner confirmation. GPL-3.0-or-later is
recommended if GNU LibreDWG is distributed as an integrated part of the application.
