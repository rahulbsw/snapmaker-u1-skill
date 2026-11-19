# Agents and operating systems

The skill entrypoint is standard `SKILL.md`; its Python helpers do not require a Codex API, Codex CLI or Codex-specific tool. An agent needs local file and shell access to run them. A chat-only interface cannot execute the workflow by loading these instructions alone.

Install into the agent you use:

```sh
npx skills add rahulbsw/snapmaker-u1-skill --skill snapmaker-u1 --agent claude-code openclaw pi
```

Use `codex` or `opencode` for those agents. Add `-g` for a global installation. The [official CLI agent table](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) describes installation locations. `agents/openai.yaml` only provides optional Codex UI metadata. Other agents use `SKILL.md` and the same scripts/references.

## Capability boundaries

| Workflow | macOS | Windows | Linux |
|---|---|---|---|
| Parametric CAD example, mesh preparation/checks, previews, color preparation | Python core environment | Python core environment | Python core environment |
| Read-only printer/spool checks | Python standard library | Python standard library | Python standard library |
| Orca CLI slicing and toolpath review | App bundle or executable | CLI executable and matching profiles | Compatible local build/executable and matching profiles |
| TripoSR candidates, local human segmentation | Separate optional environment; MPS/CPU | Separate optional environment; CPU/CUDA if available | Separate optional environment; CPU/CUDA if available |
| Native Vision, Foundation Models, Object Capture | Compatible Mac/SDK required | Unavailable | Unavailable |
| Bambu conversion | Separate pinned backend | Separate pinned backend | Separate pinned backend |
| Advanced patched TRELLIS adapter | Existing compatible Mac runtime | Not validated | Not validated |

Optional engine/model/package support depends on Python, architecture and hardware; package resolution does not establish successful inference. Do not claim every feature runs on every operating system. Apple frameworks are optional routes, not dependencies of the core. For non-Mac opaque images, use the configured TripoSR human-segmentation route or provide an RGBA cutout. No cloud fallback is implied. The TRELLIS wrapper's opaque-image route still requires Apple Vision; transparent input does not make its Mac runtime portable.

The optional Python 3.11 dependency set resolves for Windows x86-64, Linux x86-64 with glibc 2.28+, and macOS 14+ on Apple Silicon. Other architectures/older systems need separate compatible packages; this does not establish Intel Mac, Windows ARM or Alpine/musl inference support.

## Python environment

Use the [README setup](../README.md#install). Examples elsewhere using `.venv/bin/python` are POSIX commands. On Windows use `.venv/Scripts/python.exe` (PowerShell: `.\.venv\Scripts\python.exe`); after activation use `python` on any OS. Never run a copied virtual environment from another OS. Recreate it and provision optional runtimes separately.

All helper paths are relative to the installed skill, not necessarily the current project. Use absolute script/input/output paths when invoking from another directory. `local-runtime.json` can select that machine's Python/runtime paths; it is private machine state, and should be configured anew after moving the skill. Use forward slashes or doubled backslashes inside JSON Windows paths.

## Snapmaker Orca

`u1_slice.py --app-path` accepts a macOS app bundle, an installation directory or the executable itself. Without it, the adapter checks `/Applications/Snapmaker Orca.app` on macOS, then `snapmaker-orca`/`Snapmaker_Orca` on PATH. It never downloads or launches an unrelated slicer to fill a missing dependency.

The adapter resolves adjacent bundled Snapmaker profiles. For nonstandard layouts, FHS Linux packages or extracted AppImages, pass `--profiles-dir` explicitly. It must contain the `machine`, `process` and `filament` subdirectories from the **same compatible Snapmaker Orca build**. These paths follow [upstream resource layouts](https://github.com/Snapmaker/OrcaSlicer/blob/main/src/Snapmaker_Orca.cpp) and [executable names](https://github.com/Snapmaker/OrcaSlicer/blob/main/src/CMakeLists.txt). Availability of a compatible Linux package is separate from this skill.

Examples after setting up the Python core environment (adjust installation paths):

```sh
python scripts/u1_slice.py part.stl --output-dir outputs/slice --app-path "/Applications/Snapmaker Orca.app" --dry-run
python scripts/u1_slice.py part.stl --output-dir outputs/slice --app-path /opt/snapmaker-orca/bin/snapmaker-orca --profiles-dir /opt/snapmaker-orca/resources/profiles/Snapmaker --dry-run
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/u1_slice.py part.stl --output-dir outputs/slice --app-path "C:/Program Files/Snapmaker Orca/snapmaker-orca.exe" --profiles-dir "C:/Program Files/Snapmaker Orca/resources/profiles/Snapmaker" --dry-run
```

Use the actual CLI executable supplied by the installed build; do not pass a shell command, `.bat` or `.cmd` wrapper. `--dry-run` checks local profile preparation and writes the intended argument vector without launching the slicer. Remove it to request a real local slice. A successful dry run does not establish that a native executable works on this OS. All original single-filament/color guards, toolpath review and manual print checks still apply; no job is sent to the printer.

## Validation scope

CI defines Linux, Windows and macOS core checks. Synthetic fixtures cover application layouts and Windows virtual-environment paths without launching Orca. Native Apple tests skip on other systems. Optional neural engines and complete sessions in each agent require separate testing on the target machine; CI success does not certify portrait likeness or a physical print.
