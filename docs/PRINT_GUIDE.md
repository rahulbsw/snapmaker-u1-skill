# Snapmaker U1 print guide

New to 3D printing? Follow [First reliable prints on the U1](BEGINNER_GUIDE.md) for material choice, plain-language settings, preparation, preview, first-layer checks and troubleshooting. SolidCraft is [optional CAD input](../references/SOLIDCRAFT.md), not a prerequisite for this print workflow.

## Intent presets

| Intent | Starting approach | Typical use |
|---|---|---|
| Draft | Coarser layer preset, modest infill, minimal supports | Shape and fit checks |
| Normal | Standard quality preset, balanced walls and infill | General-purpose parts |
| Strong | Orient load across layers, add perimeters, reinforce locally, then tune infill | Brackets, clips, frequently handled parts |
| Flexible | U1-compatible TPU profile, gentle geometry and no sharp thin hinges | Grips, bumpers, compliant parts |

These are intent labels, not fixed slicer profiles. Use current Snapmaker Orca presets for layer height, speed, temperature, cooling, and material behavior.

For new meshes, shared starting points explicitly apply 3 walls / 8% gyroid for Draft, 3 walls / 15% gyroid for Normal, and 4 walls / 25% gyroid for Strong. Flexible retains the dedicated profile's walls/pattern/density unless explicitly configured. Native projects retain their own settings. Support `auto` keeps the selected preset's style; `tree` and `normal` explicitly select those styles. Recommendations and slicing use the same intent values; exported settings in the print card are authoritative.

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

### One project, fewer plates, fewer delivery files

Use `u1_project.py` as the default final-delivery helper. The output folder contains **`project.3mf` and `PRINT_CARD.md`**; detailed settings, attempts, comparisons, G-code and previews stay in `.work/`. Keep editable CAD alongside these when appropriate. Intermediate preparation/preview helpers should also write into `.work/`, not create additional top-level deliveries. Original inputs are preserved in place. Output folders must be fresh (preprocessing under `.work/` is allowed), so an accepted project cannot be overwritten accidentally.

```sh
# Pack separate dimensioned parts into ONE project, retaining editable objects.
python scripts/u1_project.py body.stl lid.stl handle.stl \
  --output-dir outputs/organizer --intent strong --material 'Generic PLA'

# Existing reviewed U1 project: slice the original layout and global packing.
python scripts/u1_project.py reviewed-u1.3mf --plates compare \
  --objective balanced --output-dir outputs/optimized

# Explicit alternatives: preserve the current plates, or prioritize fewer plates.
python scripts/u1_project.py reviewed-u1.3mf --plates keep --output-dir outputs/kept
python scripts/u1_project.py reviewed-u1.3mf --plates compare \
  --objective plates --output-dir outputs/fewest-plates
```

`--plates combine` requests global arrangement directly. Packing uses Orca's actual machine/process settings and may still require several plates. All plates remain in the same project. Multiple independent calibrated 3MF files are not automatically merged: import compatible objects into one native project in Orca first, preserving part/paint assignments. Differing per-plate settings, filament maps or locked plates block packing; `keep` preserves those jobs, and `compare` falls back to the preserved layout with an explanation. Unmatched Full Spectrum targets still require Manual Match.

For a native U1 0.4 mm project, the helper invokes Orca **without process or filament overrides**. It verifies original settings, mesh/paint data, instance counts, composed orientation/scale/Z position, assembly spacing, and object/plate overrides after export; only whole-object XY placement and tower XY positions may change. Unknown changes prevent promotion. This conservative check may require manual Orca preparation for other project structures. New STL/OBJ parts use the chosen official intent and material profiles and carry no source color calibration.

`balanced` chooses packing only if slicer time, filament and plate count all stay equal or improve, with at least one improvement. `time`, `filament` and `plates` explicitly prioritize that metric and can trade off the others; the card shows both layouts. Estimates sum each plate once, even if loose and embedded G-code copies coexist. Two plates containing identical G-code still count twice. Missing plate data or estimates cannot establish savings. A native failure stops further attempts; a rejected packing result keeps a passing preserved original layout.

Start with layout to avoid lowering quality/strength settings. Keep layer height, perimeter count, wall/top/bottom thickness, infill, supports/interfaces, flow/cooling limits and calibrated colors unchanged. If further savings are needed, compare a few applicable alternatives: shorter support spans with a load-safe orientation, accessible support styles/interfaces, ribs/local reinforcement, or internal infill changes justified by the intended load and top-surface spans. Evaluate those changes separately with layer previews and fit/load coupons as needed. The bundled automatic comparison changes **placement only**; it does not certify equivalent physical strength or surface finish. Fewer plates can add travel, color changes, cooling/adhesion issues or increase the cost of a failed print. Include those risks in selection.

The slicer reports supports, brim and tower usage in its G-code estimates; custom macro purge, startup consumption and real wall-clock time are not independently measured. Do not label these estimates as measured spool consumption or guaranteed savings.

### Constrained process alternatives

Layout-only comparisons remain the default. To evaluate process changes, supply a JSON file declaring the part's requirements and acceptable alternatives. For example, after establishing that the intended part can use these values:

```json
{
  "minimum_walls": 3,
  "minimum_infill_percent": 15,
  "maximum_layer_height_mm": 0.2,
  "minimum_top_thickness_mm": 0.8,
  "minimum_bottom_thickness_mm": 0.6,
  "infill_patterns": ["gyroid", "cubic"],
  "infill_percentages": [15, 20],
  "support_types": ["normal(auto)", "tree(auto)"],
  "max_candidates": 4
}
```

```sh
python scripts/u1_project.py reviewed-u1.3mf --plates compare \
  --constraints limits.json --output-dir outputs/constrained
```

Limits must be finite and valid; unknown keys are refused. `max_candidates` counts **all** native slices, including baseline/layout, and is capped at six. Alternatives change one factor at a time in the listed pattern, density, then support order until the budget is exhausted. A larger combinatorial search is not performed. Supported patterns are `gyroid`, `cubic`, `adaptivecubic`, `grid` and `rectilinear`; support styles are normal/tree auto. Disabled supports stay disabled. No temperature, speed, flow, nozzle, layer-height, wall, shell, geometry, orientation, support-material or color-recipe change is permitted by this search.

Each process alternative is a new native working copy of the accepted layout, preserving materials/recipes and removing stale G-code. It receives a fresh all-plate slice, geometry/settings preservation check and declared-limit check. Wall count and top/bottom shell thickness cannot fall below the original; layer height cannot exceed the original. Infill can only use a listed value at or above the declared minimum. Do not choose a lower minimum without understanding the part's loads and finish needs. The same balanced/time/filament/plate objective selects among eligible results, with actual changes and failures recorded in the card.

Per-object process overrides and adaptive/range layers are not evaluated by these global constraints and require a manual workflow. Missing required settings or a baseline that fails the declared limits prevents automatic selection. A native failure stops further attempts and retains an already eligible candidate. Constraint checks enforce software limits; they do not establish equivalent mechanical strength, appearance or support removability. Review layers and test functional fits/loads as appropriate.

The print card separates slice, preservation and constraint status, shows the actual exported settings and estimates, and labels spool/color/physical checks as unverified. When opening an existing project, `--intent`, `--material` and `--supports` are refused; edit a reviewed source project or use the supported constraints instead of silently changing native settings.

### macOS CLI crash and compatibility handling

Orca's 3MF export initializes AppKit/OpenGL through `glfwInit` to render thumbnails. A restricted Codex seatbelt launch can abort during macOS application registration even after slicing wrote G-code. The helper refuses native execution in that environment before launching; dry runs still work. Use an approved execution with normal app access or run from Terminal. Do not reset user presets, reinstall Orca or repeatedly retry a failed native export as a workaround. An isolated run directory leaves normal Orca configuration untouched.

Snapmaker Orca 2.4.1 also has a legacy CLI version check that can reject its own 2.x exports. `--allow-newer-file` is an explicit compatibility override available on both helpers. Use it only after verifying the project is compatible with the selected installed build (as with a synthetic project exported by that exact build). It does not fix graphics initialization. [Snapmaker's CLI source](https://github.com/Snapmaker/OrcaSlicer/blob/main/src/Snapmaker_Orca.cpp) documents the version-check correction and thumbnail path; native `--help` is the authority for the installed build's flags. Shader/thumbnail errors remain separate from path validation and need inspection in the exported project's native preview.

## Toolpath review

`scripts/u1_slice.py` automatically checks each distinct external or project-embedded G-code artifact. It checks explicit positive-extrusion movement across **all layers and feature types**, including supports, brim, skirt and prime tower where present. Bounds use the resolved machine's `printable_area`, `bed_exclude_area` and `printable_height`; the nominal bed size is not substituted. Straight paths crossing concave boundaries or excluded polygons also fail.

Each review writes `toolpath-review.json`, `toolpaths-top.png` and `toolpaths-3d.png`. These show actual extrusion paths in their sliced orientation, with support, brim/skirt, outer-wall and top-surface colors. Large previews sample paths per feature and label the displayed count; validation still checks every segment. They are static overviews; use Orca for individual-layer inspection.

For G-code exported from a native calibrated or multicolor project, use the standalone reviewer. Supply a **resolved machine JSON from that same project/profile**, with the actual bounds and height; do not substitute another printer's profile. This reads G-code without editing colors, rewriting it or sending it to hardware:

```sh
.venv/bin/python scripts/u1_gcode.py exported-plate.gcode \
  --machine-json resolved-machine.json --output-dir outputs/toolpath-review
```

The output directory must be fresh. Exit codes are 0 for passing checks and generated previews, 1 for failed/incomplete review, 2 for invalid input or setup. The integrated slicer records native export separately as `slicer_output_completed`; `slice_completed` additionally requires passing checks and generated previews. Review failures retain their reports and line numbers.

Supported motion is millimeter Klipper/Orca G0/G1, absolute/relative XYZ and E with G92 resets, and absolute-XYZ XY I/J arcs (including helical moves and P1). Arc subdivision includes exact bed-edge extrema; arc checks require a convex printable polygon without excluded areas. Inches, R arcs, other arc planes, multi-turn arcs, unsupported coordinate-state commands and unknown extrusion origins fail review. The reviewer uses explicit G-code coordinates; it is not a firmware simulator.

`TYPE:Custom` start/end extrusion blocks are explicitly excluded and counted. Firmware macros, homing behavior, printer-side offsets and tool changes are not simulated; unknown macro names are reported. Travel paths, nozzle/bead width, material mixing, support quality and toolhead collisions are outside the geometric check. A passing report keeps `ready_to_print: false`: review those details in native Orca with the actual machine and spools.

Feature grouping was informed by [Brent Bolinger's U1 toolkit](https://github.com/bbolinger/snapmaker-u1-toolkit/tree/c66284ce990fa71ccf969cae517fbd3b0c780450); the parser is local and uses no toolkit runtime. Modal behavior follows the documented [Klipper G-code semantics](https://www.klipper3d.org/G-Codes.html) and [arc support](https://github.com/Klipper3d/klipper/blob/master/klippy/extras/gcode_arcs.py), within the narrower supported scope above.

## Validation checklist

- [ ] Units and scale confirmed; critical dimensions measured in CAD.
- [ ] Mesh has no degenerate triangles and is closed where a solid is intended.
- [ ] No unexpected self-intersections, disconnected shells, or reversed/open surfaces.
- [ ] Part fits the current U1 build-plate boundary and height limit.
- [ ] Snapmaker Orca uses the U1 profile, actual nozzle, actual plate, and matching filament preset.
- [ ] Layer preview shows sound supports, bridges, walls, seams, tool changes, and no collisions.
- [ ] Sliced material use, purge waste, and print time reviewed.
- [ ] Critical fit/load parts have a test print plan.
