# Component Catalogue V0

The supplied master library is a valid DXF R2004 drawing in millimetres. It contains a
complete model space and a large mixture of final equipment views, nested subassemblies,
construction geometry and automatically generated block names.

Named blocks therefore cannot be approved solely from their names. Initial rendering
showed, for example, that `DH2000-III_T` is a top view and `dfd1` is not the complete
DFD cabinet representation.

## Review sequence

1. Render the master model space as review tiles.
2. Associate visible labels with geometry regions and block insertions.
3. Select the preferred principle-sketch view for each equipment family.
4. Extract or compose one clean vector block per view.
5. Assign insertion point, label anchor and typed pipe anchors.
6. Compare the result with an approved historical sketch.
7. Change status from `needs_review` to `approved`.

V0 includes candidate records for DFD, DH, SVR, LT and WAM. No candidate is yet an
engineering-approved symbol.

