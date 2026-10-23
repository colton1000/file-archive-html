# file archive html

This repository is a personal collection of browser experiments, automation utilities, and small productivity tools. The project contains a mix of standalone HTML apps, Python scripts, shell helpers, and lightweight server examples.

## Overview

The code in this repo is intended for local experimentation and personal use. Some files automate browser actions or manipulate files on a machine, so they should be used carefully and only in environments where you have permission to run them.

## Repository structure

- `apps/html/` — standalone browser-based pages and experiments
- `apps/python/` — Python scripts for automation, utilities, and local tools
- `apps/server/` — backend/server-related script files
- `apps/tools/` — helper scripts, PowerShell utilities, and shell commands
- `apps/frameforge_on_the_go_v2_2_fixed_colors/` — a packaged web app with its own assets and manifest

## Included project areas

### HTML experiments

Examples in this folder include:
- BlockStrike themed page
- cursor and drawing studios with local project recovery
- frameforge-themed UI prototypes
- Green Squish Toy, Multi-King boss demo, and holiday/world-clock views
- NovaChat API playground with conversation context and transcript export
- custom paper and dashboard-style pages

Open any `.html` file directly in a browser to use it.

NovaChat sends requests from the browser directly to AIMLAPI. Enter the API key
for the current session; the page does not save it. Cursor Studio keeps project
pixels and hotspot settings in browser storage so edits can be restored after
reopening the page.

### Python utilities

The Python collection includes utilities such as:
- `ASCII V3.py`
- `auto-clicker.py`
- `overlay.py`
- `random-w-a-s-d V3.py`
- `multitool_file_organizer.py`

These are generally local, script-based tools that may be run with Python directly.

The auto-clicker accepts an interval, click limit, and mouse button, for example:

```bash
python apps/python/auto-clicker.py --interval 0.2 --count 20 --button right
```

The package installer can preview commands with `--dry-run` or install a
selection with `--only requests flask`. The system overlay can display CPU,
memory, disk, and network usage; GPU usage is shown when the optional `GPUtil`
package and a supported GPU are available. The overlay requires `psutil`;
the auto-clicker requires `keyboard` and `pyautogui`; and the WASD helper
requires `keyboard` and `pynput`.

### Server and web app code

The server-side scripts and packaged app include:
- `apps/server/frameforge_server.py`
- `apps/frameforge_on_the_go_v2_2_fixed_colors/`

The packaged web app can be opened from its local folder as a static site or served with a local web server if needed.

### Shell and system helpers

The tools folder includes:
- `crazy-dangerous-version.ps1`
- `its-getting-crazy.ps1`
- `nano_cleaner.sh`
- `script installer.py`

These scripts are intended as local maintenance or automation helpers and may need permissions or environment-specific setup before they run.

## Quick start

1. Browse the relevant folder for the type of project you want to run.
2. For HTML files, open the page in a browser.
3. For Python scripts, run them with Python, for example:

   ```bash
   python apps/python/auto-clicker.py
   ```

4. For shell or PowerShell scripts, run them in the appropriate terminal environment.

## Notes and safety

- Some scripts may interact with system input, browser windows, or local files.
- Use only on machines where you understand the behavior and have permission to run the script.
- Before using automation scripts, confirm they align with the target environment and local policies.

## Maintenance

This repo is organized by function instead of by original filename so it is easier to browse and maintain over time. If you add new tools or apps, keep them grouped under the same category folders:

- `apps/html/`
- `apps/python/`
- `apps/server/`
- `apps/tools/`

This keeps the workspace easier to manage and reduces clutter at the root level.
