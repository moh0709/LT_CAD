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

## DH full assembly

The registered DH front view is a model-space composite, not only the hopper body block.
Its bounding box includes the standard floor frame, and the bottom of that frame is
placed on the drawing floor line. This full extent is also used when calculating the
display scale and the receiver mounting plane.

## DFD/DH process-air circuit

The DFD/DH circuit is independent of material and vacuum conveying routes. Its two DFD
ports are on top of the dryer, its two DH ports are on the side facing the DFD, and the
horizontal sections stretch to the selected machine spacing. Both routes use rounded
bends and explicit airflow arrows.
