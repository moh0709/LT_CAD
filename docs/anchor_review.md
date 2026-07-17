# Component view and anchor review

The component silhouette and its pipe connections are approved separately. This keeps
an accurate CAD view usable while preventing the router from connecting a line to an
unverified port.

## Current proof of concept

| View | Geometry | Pipe anchors |
|---|---|---|
| DFD300/450 left side | Approved family standard | Approved |
| DH800-III front with frame | Approved family standard | Approved |

Coordinates are stored relative to the component bounding box: `(0, 0)` is bottom-left
and `(1, 1)` is top-right. This makes the same reviewed anchor reusable when a component
is scaled on an A3 principle sketch.

An approved anchor records:

- a stable ID;
- medium, such as `drying_air`, `vacuum_air`, `dried_material` or `undried_material`;
- direction (`in`, `out` or `bidirectional`);
- normalized `x` and `y` coordinates.

Views with `anchor_status: needs_review` must have an empty `anchors` list and cannot be
used by automatic routing.

The approved DFD/DH process-air circuit has two distinct routes:

- supply air: DFD top outlet to the DH side inlet;
- return air: DH side outlet to the DFD top inlet.

Both use black outlined ductwork with rounded bends and a direction arrow. The DFD top legs are
vertical, while the DH connection legs are horizontal. Horizontal pipe length stretches
automatically with machine spacing. DH side anchors and their connection geometry mirror
together whenever the DFD is placed on the opposite side.

Review drawings use yellow/red `P1`, `P2`, etc. markers for visual candidates. After
confirmation, a marker is converted into a named engineering anchor; rejected markers
are removed or moved.
