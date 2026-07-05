# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A collection of independent Linux CLI utilities (Bash and Python 3), one per `script_*` directory. There is no build system, package manager, linter config, or test suite — each tool is run directly from its directory. Documentation, code comments, and terminal output are written in **Spanish**; keep that convention when editing or adding code.

## Running the tools

Each tool is executed via its entry point:

```bash
# Modular Bash tools (backup_suite, pdf-suite, proyect_tree, hardlinks-detector,
# git_sync_respos, count_files_by_extension, create_folders_batch, git_download_respos)
./script_backup_suite/main.sh --help
./script_create_folders_batch/main.sh -f lista.txt -d

# Python tools
python3 script_hardlinks-creator/main.py <filename> --dry-run
python3 script_pdf_page_counter/main.py --listar
```

- Most tools support a simulation flag (`--dry-run`, `-d`, or simulate mode) — use it to verify changes without touching the filesystem.
- Scripts need execute permission: `chmod +x <tool>/main.sh <tool>/lib/*.sh`.
- To sanity-check Bash edits without running side effects: `bash -n <file>.sh`.
- `script_git_sync_respos` reads its repository list from `repos-config.yml` in its own directory.

## Architecture: the shared modular pattern

The mature tools all follow the same three-part layout, in both Bash and Python:

```
script_<name>/
├── main.sh|main.py    # Entry point: orchestration only (~120 lines max by convention)
├── config.sh|config.py # User-editable defaults: paths, exclusions, rsync opts, colors
└── lib/               # Single-responsibility modules
    ├── cli.*          # Argument parsing (defines OPT_* variables / argparse parser)
    ├── logger.*       # Colored logging + optional log file with rotation
    ├── validator.*    # Dependency/input/environment checks
    └── ...            # Domain modules (scanner, processor, renderer, etc.)
```

Key conventions to preserve:

- **`main` orchestrates, `lib/` implements.** Entry points load `config` first, then source/import lib modules in dependency order, then run numbered phases (parse args → init logger → validate → confirm with user → process → summary). Business logic never lives in `main`.
- Bash tools use `set -euo pipefail` and resolve `SCRIPT_DIR` so they work from any CWD; the Python tool prepends its own directory to `sys.path` for the same reason.
- CLI options are stored in `OPT_*` globals (Bash) set by `parse_args`, and configuration constants live in `config.sh`/`config.py` — new tunables go there, not hardcoded in lib modules.
- Destructive operations ask for interactive confirmation unless a `--no-confirm`/`--auto` flag is passed, and honor the simulation flag end-to-end.
- File headers carry a version number and phase-by-phase description of the flow; module files state their single responsibility.

As of 2026-07 every tool follows this modular layout (the last four single-file tools — count_files_by_extension, create_folders_batch, git_download_respos, pdf_page_counter — were refactored into it; each README documents the bugs fixed in that migration). If a new single-file script is added, refactor it into the modular layout before substantially extending it.

Each tool has its own README.md with usage, architecture notes, and extension instructions — read it before modifying that tool, and update it when behavior changes.
