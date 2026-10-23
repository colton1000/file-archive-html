# WinWidgetKit 0.8.0

Camera-free release. Extract and double-click `install_windows.bat`.

## Orb Controller

The bouncing orbs are **off by default every time the app starts**. Press **Turn Orbs On** to spawn them and **Turn Orbs Off** to remove them.

- Desktop mode: orbs bounce around the Windows work area and avoid the taskbar.
- Taskbar mode: orbs move left and right along the lower work-area edge above the taskbar.
- Choose 1 to 20 orbs.
- Change orb size from 24 to 100 pixels.
- Change speed from 2 to 12.
- Click an orb to reverse its direction.
- The controller remembers mode, count, size, and speed, but never automatically turns the orbs on.

```python
from winwidgetkit import WidgetApp, OrbControllerWidget
app=WidgetApp()
OrbControllerWidget(app,widget_id="orbs",orb_count=4,orb_mode="desktop")
app.run()
```

## Retained widgets

Clock with numbers and alarms, stopwatch, holiday calendar, shortcut, notes, Focus Orb, Magic Orb, water, CombinedWidget, CustomWidget, ScriptWidget, resizing, colors, persistence, and activity logs. Camera dependencies and camera code are removed.
