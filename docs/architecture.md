# Architecture

LT_CAD separates AI interpretation from deterministic CAD generation.

## Pipeline

1. **Quotation ingestion** extracts order number, article numbers, models, quantities,
   options and technical parameters.
2. **Component resolution** maps quotation lines to approved catalogue entries.
3. **Topology planning** applies drying and conveying rules to create a typed connection
   graph.
4. **Layout planning** selects component views and positions them using approved layout
   patterns.
5. **Pipe routing** creates orthogonal routes while respecting component anchors,
   line classes and collision clearances.
6. **Validation** checks quotation coverage, allowed connections, complete material paths
   and vacuum return paths.
7. **CAD export** writes DXF and produces SVG/PDF review output.

## Open-source CAD stack

- **Canonical CAD:** DXF R2004 or later.
- **CAD API:** `ezdxf` (MIT).
- **Optional DWG import:** GNU LibreDWG (GPL-3.0-or-later).
- **Manual review:** LibreCAD (GPL-2.0).

Modern DWG writing is not a required system capability. Keeping DXF canonical avoids a
dependency on proprietary CAD SDKs.

## Component contract

An approved component must define:

- stable component identifier and family;
- source block or extracted geometry;
- view direction;
- native unit and bounding box;
- insertion/base point;
- typed pipe anchors;
- permitted connection classes;
- label anchor;
- review status and provenance.

AI may choose among approved components and topology patterns, but it must not invent
connection anchors or silently add unquoted equipment.

