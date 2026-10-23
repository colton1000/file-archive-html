"""Analog clock widget with optional numbers and persistent daily alarms."""

import math
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog

from .base import DesktopWidget


class AnalogClockWidget(DesktopWidget):
    def __init__(self, app, *, show_numbers=False, alarms=None, **kwargs):
        kwargs.setdefault("title", "Analog Clock")
        kwargs.setdefault("width", 230)
        kwargs.setdefault("height", 260)

        saved = app.settings_for(kwargs["widget_id"])
        self.show_numbers = saved.get("show_numbers", show_numbers)
        self.alarms = saved.get("alarms", list(alarms or []))
        self._fired_alarm_minutes = set()
        self._tick_job = None

        super().__init__(app, **kwargs)

        self.canvas = tk.Canvas(
            self.body,
            bg=self.color,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.menu.insert_checkbutton(
            0,
            label="Show numbers",
            command=self.toggle_numbers,
        )
        self.menu.insert_command(1, label="Add alarm", command=self.add_alarm)
        self.menu.insert_command(2, label="Remove alarm", command=self.remove_alarm)

        self._tick()

    def toggle_numbers(self):
        self.show_numbers = not self.show_numbers
        self.app.save_widget(self)
        self.app.log(
            "clock_numbers_changed",
            widget_id=self.widget_id,
            enabled=self.show_numbers,
        )

    def add_alarm(self):
        value = simpledialog.askstring(
            "Add alarm",
            "Enter a daily alarm in 24-hour HH:MM format:",
            parent=self.window,
        )
        if value is None:
            return

        try:
            normalized = datetime.strptime(value.strip(), "%H:%M").strftime("%H:%M")
        except ValueError:
            messagebox.showerror(
                "Invalid alarm",
                "Use 24-hour HH:MM format, such as 07:30 or 18:45.",
                parent=self.window,
            )
            return

        if normalized not in self.alarms:
            self.alarms.append(normalized)
            self.alarms.sort()
            self.app.save_widget(self)
            self.app.log("alarm_added", widget_id=self.widget_id, time=normalized)

    def remove_alarm(self):
        if not self.alarms:
            messagebox.showinfo("Alarms", "No alarms are set.", parent=self.window)
            return

        value = simpledialog.askstring(
            "Remove alarm",
            "Current alarms: " + ", ".join(self.alarms)
            + "\n\nType the exact time to remove:",
            parent=self.window,
        )
        if value and value.strip() in self.alarms:
            alarm = value.strip()
            self.alarms.remove(alarm)
            self.app.save_widget(self)
            self.app.log("alarm_removed", widget_id=self.widget_id, time=alarm)

    def _tick(self):
        try:
            if not self.window.winfo_exists():
                return

            now = datetime.now()
            self._check_alarms(now)
            self._draw(now)
            self._tick_job = self.window.after(250, self._tick)
        except tk.TclError:
            # The window was closed while an update was pending.
            self._tick_job = None

    def _check_alarms(self, now):
        minute_key = now.strftime("%Y-%m-%d %H:%M")
        alarm_time = now.strftime("%H:%M")

        if alarm_time in self.alarms and minute_key not in self._fired_alarm_minutes:
            self._fired_alarm_minutes.add(minute_key)
            self.window.bell()
            self.app.log(
                "alarm_triggered",
                widget_id=self.widget_id,
                time=alarm_time,
            )
            messagebox.showinfo("Alarm", f"Alarm: {alarm_time}", parent=self.window)

        if len(self._fired_alarm_minutes) > 20:
            self._fired_alarm_minutes = {
                key for key in self._fired_alarm_minutes if key == minute_key
            }

    def _draw(self, now):
        canvas = self.canvas
        canvas.delete("all")

        width = max(20, canvas.winfo_width())
        height = max(20, canvas.winfo_height())
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) * 0.41

        canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=self.color,
            outline="white",
            width=3,
        )

        for number in range(1, 13):
            angle = math.radians(number * 30 - 90)
            inner = radius * 0.82
            outer = radius * 0.94
            canvas.create_line(
                center_x + inner * math.cos(angle),
                center_y + inner * math.sin(angle),
                center_x + outer * math.cos(angle),
                center_y + outer * math.sin(angle),
                fill="white",
                width=3 if number % 3 == 0 else 1,
            )

            if self.show_numbers:
                text_radius = radius * 0.65
                canvas.create_text(
                    center_x + text_radius * math.cos(angle),
                    center_y + text_radius * math.sin(angle),
                    text=str(number),
                    fill="white",
                    font=("Segoe UI", max(8, int(radius / 10)), "bold"),
                )

        # Each hand is a separate four-item tuple. This fixes the startup crash.
        hands = [
            (((now.hour % 12) + now.minute / 60) * 30, 0.48, "white", 5),
            ((now.minute + now.second / 60) * 6, 0.68, "#7dd3fc", 3),
            ((now.second + now.microsecond / 1_000_000) * 6, 0.78, "#fb7185", 2),
        ]

        for degrees, length_factor, color, line_width in hands:
            angle = math.radians(degrees - 90)
            canvas.create_line(
                center_x,
                center_y,
                center_x + radius * length_factor * math.cos(angle),
                center_y + radius * length_factor * math.sin(angle),
                fill=color,
                width=line_width,
                capstyle="round",
            )

        canvas.create_oval(
            center_x - 4,
            center_y - 4,
            center_x + 4,
            center_y + 4,
            fill="white",
            outline="",
        )

        if self.alarms:
            canvas.create_text(
                center_x,
                center_y + radius * 0.9,
                text="Alarms: " + ", ".join(self.alarms[:3]),
                fill="#fbbf24",
                font=("Segoe UI", 8, "bold"),
            )

    def on_color_changed(self, color):
        self.canvas.configure(bg=color)

    def get_settings(self):
        settings = super().get_settings()
        settings["show_numbers"] = self.show_numbers
        settings["alarms"] = self.alarms
        return settings

    def close(self):
        if self._tick_job is not None:
            try:
                self.window.after_cancel(self._tick_job)
            except tk.TclError:
                pass
            self._tick_job = None
        super().close()
