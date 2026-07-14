# Component view and anchor review

The component silhouette and its pipe connections are approved separately. This keeps
an accurate CAD view usable while preventing the router from connecting a line to an
unverified port.

## Current proof of concept

| View | Geometry | Pipe anchors |
|---|---|---|
| DFD300/450 left side | Approved family standard | Needs review |
| DH800-III front | Needs review | Needs review |

Coordinates are stored relative to the component bounding box: `(0, 0)` is bottom-left
and `(1, 1)` is top-right. This makes the same reviewed anchor reusable when a component
is scaled on an A3 principle sketch.

An approved anchor records:

- a stable ID;
- medium, such as `drying_air`, `vacuum_air`, `dried_material` or `undried_material`;
- direction (`in`, `out` or `bidirectional`);
- normalized `x` and `y` coordinates.

Views with `anchor_status: needs_review` must have an empty `anchors` list and cannot be
used by automatic routing. The next review should mark each physical pipe port on the
SVG preview and identify its medium and direction.

The first review drawings use yellow/red `P1`, `P2`, etc. markers. These are visual
candidates only. After confirmation, a marker is converted into a named engineering
anchor; rejected markers are removed or moved.
