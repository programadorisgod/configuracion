#!/usr/bin/env python3
import sys
import os
import signal
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

PID_FILE = "/tmp/omarchy_calendar_popup.pid"

GLib.set_prgname("omarchy-calendar-popup")
GLib.set_application_name("omarchy-calendar-popup")

# Toggle behavior: if already running, kill existing instance and exit
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())
        os.remove(PID_FILE)
        os.kill(old_pid, signal.SIGTERM)
        sys.exit(0)
    except (ValueError, ProcessLookupError, PermissionError):
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

# Save current PID
try:
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
except OSError:
    pass

class CalendarPopup(Gtk.Window):
    def __init__(self):
        super().__init__()
        
        # Configure Wayland Layer Shell (prevents window manager conflicts/flickering)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "omarchy-calendar-popup")
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 38)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        self.set_decorated(False)
        self.set_resizable(False)

        # Transparent ARGB visual for smooth rounded corners without square artifacts
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        # Outer box with border and background
        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer_box.set_name("popup-window")

        # Inner padding container
        inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        inner_box.set_name("inner-container")
        inner_box.set_margin_top(12)
        inner_box.set_margin_bottom(14)
        inner_box.set_margin_start(16)
        inner_box.set_margin_end(16)

        # Header box with Title + Close button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_name("header-box")

        now = GLib.DateTime.new_now_local()
        date_str = now.format("%A, %d de %B de %Y").capitalize()
        header_label = Gtk.Label(label=date_str)
        header_label.set_name("header-label")
        header_label.set_xalign(0.0)
        header_box.pack_start(header_label, True, True, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.set_name("close-button")
        close_btn.connect("clicked", lambda _: self.close())
        header_box.pack_end(close_btn, False, False, 0)

        inner_box.pack_start(header_box, False, False, 0)

        # Calendar widget
        self.calendar = Gtk.Calendar()
        self.calendar.set_name("calendar-widget")
        self.calendar.set_display_options(
            Gtk.CalendarDisplayOptions.SHOW_HEADING
            | Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES
        )
        inner_box.pack_start(self.calendar, True, True, 0)

        outer_box.pack_start(inner_box, True, True, 0)
        self.add(outer_box)

        # Stylesheet
        css = b"""
        window {
            background-color: transparent;
            background: transparent;
            border: none;
        }
        #popup-window {
            background-color: #111622;
            border: 2px solid #28b6f6;
            border-radius: 16px;
        }
        #inner-container {
            background: transparent;
        }
        #header-box {
            border-bottom: 1px solid rgba(40, 182, 246, 0.25);
            padding-bottom: 6px;
        }
        #header-label {
            color: #28b6f6;
            font-family: 'JetBrainsMono Nerd Font', sans-serif;
            font-size: 13px;
            font-weight: bold;
        }
        #close-button {
            background: transparent;
            color: #9aa5ce;
            border: none;
            font-family: monospace;
            font-size: 13px;
            padding: 2px 6px;
            border-radius: 6px;
        }
        #close-button:hover {
            color: #f7768e;
            background-color: rgba(247, 118, 142, 0.15);
        }
        #calendar-widget {
            background-color: #111622;
            color: #d8e6f3;
            font-family: 'JetBrainsMono Nerd Font', sans-serif;
            font-size: 13px;
            border: none;
        }
        #calendar-widget:selected {
            background-color: #28b6f6;
            color: #111622;
            border-radius: 6px;
            font-weight: bold;
        }
        #calendar-widget.header {
            color: #00e5ff;
            font-weight: bold;
        }
        #calendar-widget.button {
            color: #28b6f6;
            background: transparent;
            border: none;
        }
        #calendar-widget.button:hover {
            color: #00e5ff;
            background: rgba(40, 182, 246, 0.2);
            border-radius: 6px;
        }
        #calendar-widget.highlight {
            color: #28b6f6;
            font-weight: bold;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Keyboard and window events
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False
        return False

    def on_destroy(self, widget):
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
        Gtk.main_quit()

def main():
    def sig_handler(sig, frame):
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    win = CalendarPopup()
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
