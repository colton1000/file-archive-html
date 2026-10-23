# File Archive HTML

This repository is a personal archive of browser experiments, local tools, scripts, and small app prototypes. It mixes standalone HTML pages, Python automation utilities, a lightweight local server, helper scripts, and a small Node-based project dashboard. The code is meant for local experimentation and personal productivity, so use it only in environments where you have permission to run it.

## Repository layout

- `README.md` — project overview and file-by-file guide
- `LICENSE` — licensing terms for the repository
- `.gitignore` — ignores local editor, cache, and runtime artifacts
- `apps/html/` — standalone browser experiences and mockups
- `apps/python/` — local automation and utility scripts
- `apps/server/` — backend/server code for local projects
- `apps/tools/` — shell, PowerShell, and maintenance utilities
- `apps/frameforge_on_the_go_v2_2_fixed_colors/` — packaged browser app with its own manifest and assets
- `apps/super file host/` — local Node project dashboard with auth flow
- `apps/winwidget/` — Windows widget toolkit source and demo content
- `tests/` — automated regression tests

## Root-level files

- `README.md` — this guide; explains the purpose of each folder and major file.
- `LICENSE` — repository license text.
- `.gitignore` — keeps local workspace noise such as generated files, caches, and user-only data out of version control.

## HTML experiments and prototypes

These files live in `apps/html/` and are mostly single-page experiments that can be opened in a browser. They are not packaged applications with install steps unless otherwise noted.

- `BlockStrike_3D_Focused_Bot_Targets.html` — a BlockStrike-inspired tactical aim target mockup focused on bot-target practice.
- `clock.html` — simple time and clock-focused interface.
- `cursor_studio.html` — a drawing and cursor workspace with saved project state in browser storage for later restoration.
- `drawing V5 - pro - fixed.html` — canvas-based drawing app with a polished interface and local project recovery.
- `frameforge_gold_galaxy_themes.html` — themed FrameForge concept page with galaxy-style visuals.
- `frameforge_online.html` — online-style FrameForge prototype UI.
- `frameforge_online_777.html` — alternate FrameForge-themed mockup with a different presentation.
- `frameforge_online_market.html` — market/inventory styled FrameForge page.
- `frameforge_online_mvp_luck.html` — MVP-style FrameForge page emphasizing utility and layout experiments.
- `frameforge_update_NEW.html` — a newer FrameForge update view.
- `frameforge_update_NEWER.html` — another iterative visual update to the FrameForge interface.
- `frameforge_update_NEW_v2.html` — second-generation FrameForge update layout.
- `frameforge_update_NEW_v3.html` — third-generation iteration.
- `frameforge_update_NEW_v4_credits_hints.html` — update screen with credits and hint content.
- `green_squish_toy.html` — stylized toy or interaction demo with a squishy visual motif.
- `lined_paper_studio-v5.html` — notepad or lined-paper workspace.
- `multi-king.html` — boss battle or multi-king game prototype.
- `novachatai V3.html` — NovaChat API playground for prompt and transcript experiments.
- `frameforge_online_market.html` and related FrameForge pages — UI prototypes for the FrameForge project family.

Notes:
- Many of these pages were built as local experiments and may rely on browser-only features.
- `novaChat`-style pages may send requests to external APIs and should only be used with a valid key and the proper permissions.
- `cursor_studio.html` and similar pages use browser storage so edits can persist locally between visits.

## Python utilities

The `apps/python/` folder contains scripts for local automation, overlays, and file management.

- `ASCII V3.py` — text-mode ASCII art engine with static categories and animated scenes such as fire, rain, bouncing text, and starfields.
- `auto-clicker.py` — macro-style utility that performs mouse clicks at a chosen interval, count, and button type.
- `multitool_file_organizer.py` — general-purpose local file organizer for sorting content into folders based on file type or patterns.
- `overlay.py` — lightweight system overlay for CPU, memory, disk, and network usage; may use optional GPU data if `GPUtil` is available.
- `random-w-a-s-d V3.py` — helper for simulating WASD-style keyboard input and movement automation.

Typical usage examples:

```bash
python apps/python/auto-clicker.py --interval 0.2 --count 20 --button right
```

These scripts are local tools and may require packages such as `keyboard`, `pyautogui`, `pynput`, or `psutil` depending on what you run.

## Local server and project hosting

- `apps/server/frameforge_server.py` — a lightweight Python HTTP server that hosts a FrameForge HTML page and provides JSON project APIs for saving/loading frame projects. It creates a local project directory, detects an HTML entry file, serves the app locally, and can open it in a browser automatically.

The server supports: 
- project upload through `/api/projects`
- project listing through `/api/projects`
- direct project retrieval via `/api/projects/{id}`
- default routing from the web root to the selected HTML file

## Utility scripts and maintenance helpers

The `apps/tools/` folder contains maintenance and shell utilities.

- `crazy-dangerous-version.ps1` — a system-level or experimental PowerShell helper. Use only with caution; it is intended for local maintenance/development tasks.
- `its-getting-crazy.ps1` — another PowerShell helper for ad hoc automation or task remediation.
- `nano_cleaner.sh` — Unix shell utility for cleaning or optimizing a workspace, likely intended for local system housekeeping.
- `script installer.py` — installs Python packages for the active interpreter using `pip`, with optional dry runs and selective package installs.

## Packaged browser app: FrameForge on the GO!

This directory holds a small standalone web app for local use:

- `apps/frameforge_on_the_go_v2_2_fixed_colors/README.txt` — notes about the fixed palette and behavior changes.
- `apps/frameforge_on_the_go_v2_2_fixed_colors/index.html` — app UI.
- `apps/frameforge_on_the_go_v2_2_fixed_colors/app.js` — app logic.
- `apps/frameforge_on_the_go_v2_2_fixed_colors/styles.css` — styling.
- `apps/frameforge_on_the_go_v2_2_fixed_colors/manifest.json` — Firefox extension manifest for the packaged app.
- `apps/frameforge_on_the_go_v2_2_fixed_colors/icon.svg` — app icon.

This app is a compact browser-based drawing and frame animation studio for local experimentation. It is designed to be loaded as a local web page or packaged extension-style app, and it uses browser storage for persisted settings.

## Super file host

The `apps/super file host/` folder is a local web app used as a project dashboard.

- `README.md` — explains the Node-based auth flow, account rules, and local storage behavior.
- `package.json` — declares the app metadata and scripts: `npm start` and `npm test`.
- `server.mjs` — Node HTTP server implementing local account registration, sign-in, session handling, password hashing, and security checks.
- `index.html` — the dashboard browser UI.
- `app.js` — client-side dashboard logic for project management, filtering, sorting, and user auth flows.
- `styles.css` — styling for the dashboard.
- `server.test.mjs` — tests for the server logic.
- `.gitignore` — ignores local data folders and temporary artifacts.

This is a local-first project management dashboard with a GitHub-like UI and browser login model. It stores account data under a private `data/` folder and keeps project lists in browser storage rather than uploading them to a server.

## WinWidgetKit

The `apps/winwidget/` folder is a Windows widget toolkit source package.

- `winwidgetkit-0.8.0-source/winwidgetkit-0.8.0/README.md` — explains the toolkit, orb controller, and widget features.
- `install_windows.bat` — Windows installation helper.
- `run_demo.bat` — launches a demo app.
- `pyproject.toml` — project metadata and packaging configuration.
- `src/winwidgetkit/__init__.py` — package entry point.
- `src/winwidgetkit/base.py` — base widget and application classes.
- `src/winwidgetkit/core.py` — core runtime and widget functionality.
- `src/winwidgetkit/extras.py` — support widgets and extras.
- `src/winwidgetkit/clock.py` — clock widget implementation.
- `src/winwidgetkit/stopwatch.py` — stopwatch widget.
- `src/winwidgetkit/water.py` — water animation widget.
- `src/winwidgetkit/orb_bouncer.py` — orb animation controller.
- `examples/all_widgets.py` — demo script showing widgets together.
- `examples/orb_demo.py` — orb animation demo script.

This toolkit is intended for Windows desktop demos and utility widgets, with camera-related code removed in the current release.

## Tests

- `tests/test_refactors.py` — regression tests that verify shortcut functions work as expected after refactoring, including safe terminal clearing, HTML selection, and pip command generation.

## Quick start

1. Browse the relevant folder for the type of project you want to run.
2. For HTML files, open them directly in a browser.
3. For Python scripts, run them with Python, for example:

```bash
python apps/python/auto-clicker.py
```

4. For the local Node app, run:

```bash
cd apps/super file host
npm start
```

5. For the server app, run:

```bash
python apps/server/frameforge_server.py
```

6. For shell or PowerShell helpers, run the script in the appropriate shell environment.

## Safety notes

- Some scripts interact with system input, mouse movement, browser state, or filesystem content.
- Use these tools only on machines where you understand the behavior and have permission to run them.
- Browser/API tools may send requests to external services; verify that the destination is appropriate before using them.
- Local automation and system helpers may affect your environment; review them before running in production or shared systems.

## Maintenance guidance

This repository is organized by function rather than by original filename so it is easier to browse and maintain. Keep new projects grouped under the same category folders:

- `apps/html/`
- `apps/python/`
- `apps/server/`
- `apps/tools/`
- `apps/frameforge_on_the_go_v2_2_fixed_colors/`
- `apps/super file host/`
- `apps/winwidget/`

This keeps the workspace easier to manage and reduces clutter at the root level.

