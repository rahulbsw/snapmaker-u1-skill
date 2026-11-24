# Optional SolidCraft CAD source

SolidCraft is not required for this skill. The core objective remains creating or importing geometry, preparing a Snapmaker U1 project, comparing print options, and validating the result. Preserve the existing CAD route when it already produces the requested editable part.

Use SolidCraft when parametric sketches, dimensions, shells, holes or assemblies make a functional part easier to build and revise. Appropriate examples include brackets, fitted organizers, enclosures, lids and stands. It is not a portrait-reconstruction engine, a slicer, or a source of calibrated U1 Full Spectrum recipes. Adding it to every job would widen setup without helping those other stages.

## Local MCP workflow

The official [MCP guide](https://github.com/tangency-labs/solidcraft/blob/main/docs/mcp.md) describes `solidcraft-cli mcp --headless` for an independent local design session and `--connect` for driving an open desktop design. Prefer an already configured MCP connection when available. Discover its tools and command schemas rather than assuming that current web documentation matches the installed release. No SolidCraft MCP configuration, plugin installation or application update is performed by this skill.

A typical optional route is:

1. Establish dimensions, intended loads, fits and print constraints. Create a separate new design; preserve the user's open/accepted design.
2. Use the exposed command/parameter inspection tools, then build the CAD history with named dimensions. Inspect evaluated geometry and bounds; a successful command does not prove the part is printable.
3. Save the editable native design in the job's `.work/cad/` folder. Export a millimeter STL for the existing mesh/project helpers, with a color-preserving source where applicable. Link the editable source from the print card.
4. Return to the U1 workflow: geometry checks, orientation, actual spool/process selection, constrained comparisons, all-plate slicing and review. Do not treat SolidCraft's generic 3MF export as a calibrated Orca project.

Create the job folder first, then keep the MCP server scoped to it; grant only that folder using the documented file-access options. Do not enable arbitrary filesystem access or use a desktop control connection to bypass an MCP path refusal. If the connection is unavailable, the separately installed CLI can run a reviewed local JSON modeling script; see [scripts](https://github.com/tangency-labs/solidcraft/blob/main/docs/scripts.md). It is an optional fallback, not a reason to replace the host's configured tools.

The native CAD engine and headless command route can run locally. An AI provider selected inside SolidCraft's own assistant is a separate choice; do not send prompts, photos or models to it under `local_only`. MCP availability does not itself establish offline processing by every client/provider.

## Capability and licensing boundaries

SolidCraft versions change quickly. Validate the installed executable's command catalog, exported geometry and round trips before relying on a new feature. A local review found the 0.22.0 macOS app/CLI and read its catalog; this did not establish a connected MCP modeling session or native CAD-to-print integration test.

Upstream geometry code is offered under MIT or Apache-2.0; the current project separately licenses branding and interface assets. This skill only documents an external-app workflow and distributes no SolidCraft binary, UI, icon or upstream modeling script. Consult the [official repository](https://github.com/tangency-labs/solidcraft), [MIT license](https://github.com/tangency-labs/solidcraft/blob/main/LICENSE-MIT) and [brand/interface license](https://github.com/tangency-labs/solidcraft/blob/main/LICENSE-BRAND) for the version actually used.
