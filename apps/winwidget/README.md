# WinWidgetKit

WinWidgetKit is a Python package for creating movable, resizable, persistent Windows desktop widgets. It brings back the classic widget-style desktop experience on Windows and can be embedded into any Python script.

Note: the package is not yet published to PyPI, but it is expected to be available there soon. Until then, it can be used directly from source.

## Install from source

From the project directory:

```bash
python -m pip install -e .
```

This installs the package in editable mode so you can run it directly from the source tree while developing or testing.

## Example usage

```python
from winwidgetkit import WidgetApp, CalendarWidget, NoteWidget, MagicOrbWidget

app = WidgetApp(app_name="My Dashboard")
CalendarWidget(app, widget_id="calendar")
NoteWidget(app, widget_id="notes", max_notes=10)
MagicOrbWidget(app, widget_id="magic")

app.run()
```

## Features

- Movable and resizable widgets
- Persistent widget state
- Windows desktop widget experience
- Scriptable widget creation from Python
- Demo widgets for calendars, notes, and more

## Notes

If you are testing locally, you can run scripts normally after installing from source. Once the package is available on PyPI, installation will become as simple as:

```bash
python -m pip install winwidgetkit
```

Until then, the editable install command above is the recommended method.
