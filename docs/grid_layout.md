# Grid layout and mounting contract

The drawing area uses a hidden 5 mm grid. Component boxes, standard sizes and mounting
relationships are resolved before routing. The grid is available as a debug overlay but
is not visible in released drawings.

## SVR policy

- All SVR model labels use one fixed 15 x 40 mm sheet box.
- An SVR mounted on a DH or EXT is centred on the host.
- The SVR bottom must physically contact the host's declared mounting plane; the
  permitted gap is 0 mm.
- The DH front-view bounding box contains duct geometry above its receiver mounting
  plate. Its mounting plane is therefore 10 mm below the CAD-box top. EXT uses 0 mm.
- The component and all normalized pipe anchors are mirrored together about the vertical
  axis when the connection side changes.

These rules are machine-readable in `rules/layout_rules_v0.json`. They are intended for
the dynamic layout planner, not only the standard baseline drawing.
