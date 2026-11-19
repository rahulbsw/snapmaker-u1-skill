# Snapmaker U1 print guide

## Intent presets

| Intent | Starting approach | Typical use |
|---|---|---|
| Draft | Coarser layer preset, modest infill, minimal supports | Shape and fit checks |
| Normal | Standard quality preset, balanced walls and infill | General-purpose parts |
| Strong | Orient load across layers, add perimeters, reinforce locally, then tune infill | Brackets, clips, frequently handled parts |
| Flexible | U1-compatible TPU profile, gentle geometry and no sharp thin hinges | Grips, bumpers, compliant parts |

These are intent labels, not fixed slicer profiles. Use current Snapmaker Orca presets for layer height, speed, temperature, cooling, and material behavior.

## Portraits and Full Spectrum

For complete portrait models, read [image reconstruction](../references/IMAGE_TO_3D.md). Confirm actual facial geometry and 360° subject isolation before print preparation. Chin, nose, glasses and ears can need supports even when a mesh is closed.

For additional apparent colors from four loaded filaments, read [Full Spectrum](../references/FULL_SPECTRUM.md). Use the current compatible color mixing preset and actual spool calibration, then compare material/time against a standard color slice. Keep photographic target colors until that evaluation; do not force skin to a primary spool color.

## Material selection

- **PLA:** easy to print and dimensionally convenient for indoor prototypes and decorative parts. Avoid where sustained heat or outdoor exposure is expected.
- **PETG:** a practical tougher choice for everyday parts exposed to moisture or moderate warmth. Account for stringing and fit changes.
- **TPU:** use for flexible parts only; follow the dedicated U1 TPU recommendations and matching preset.
- **ABS/ASA:** use when the application needs their temperature or outdoor properties. Follow Snapmaker's enclosure, plate, ventilation, and material-specific guidance.
- **Support interface material:** where the model needs cleaner removable supports, the Snapmaker Support for PLA guide recommends using it as the interface rather than the entire support structure, to reduce time and material.

Verify exact material compatibility and settings against the spool maker and current Snapmaker Orca preset. Dry moisture-sensitive filament as directed by its manufacturer.

## Infill and strength

Infill supports top surfaces and contributes to stiffness, but walls and orientation often determine useful strength more directly. Start with the preset matched to the intent. For a functional part, orient the load so it does not pull layers apart; increase perimeters or add ribs/bosses in CAD before making the entire interior dense. Test critical fits and loads with a small coupon or prototype.

## Material and plate efficiency

1. Prefer hollow or ribbed geometry when it preserves function.
2. Keep supportable overhangs and orient the broad stable face down.
3. Use tree/organic supports when the current slicer and geometry benefit; compare with normal supports in preview.
4. Arrange parts in one plate only when the printable polygon, clearances, support footprints, and print sequence all fit.
5. Compare sliced filament usage and time across viable orientations in Snapmaker Orca. Include purge waste for multicolor work.

## Validation checklist

- [ ] Units and scale confirmed; critical dimensions measured in CAD.
- [ ] Mesh has no degenerate triangles and is closed where a solid is intended.
- [ ] No unexpected self-intersections, disconnected shells, or reversed/open surfaces.
- [ ] Part fits the current U1 build-plate boundary and height limit.
- [ ] Snapmaker Orca uses the U1 profile, actual nozzle, actual plate, and matching filament preset.
- [ ] Layer preview shows sound supports, bridges, walls, seams, tool changes, and no collisions.
- [ ] Sliced material use, purge waste, and print time reviewed.
- [ ] Critical fit/load parts have a test print plan.
