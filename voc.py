import os
import json
import sqlite3
import ctypes
import sys
import PySimpleGUI as sg
from PIL import Image
import io
import base64

def load_icon_scaled(png_path, target_height=20):
    img = Image.open(png_path)

    # Calculate proportional width
    w, h = img.size
    ratio = target_height / h
    new_size = (int(w * ratio), target_height)

    img = img.resize(new_size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode()

# based on mellow theme
PALETTE = {
    "black"     : "#131314",
    "white"     : "#f0f0f8",
    "gray"      : "#1e1e24",
    "red"       : "#ff7a5c",
    "orange"    : "#ffb8ae",
    "green"     : "#a8e6cf",
    "yellow"    : "#f5d9b0",
    "purple"    : "#c4b8e8",
    "blue"      : "#92a2d5",
    "cyan"      : "#85b5ba",
    "light_pink": "#f5b0e0",
    "deep_pink" : "#ff99cc",
    "lavender"  : "#cc99ff",
}

FONT_NAME = "Consolas"

def panic(message):
    raise RuntimeError(f"PANIC: {message}")

class Translator:
    def __init__(self, db_path="dict.db"):
        self.last_text = ""
        self.db_path = db_path
        self._conn = None

        # Check environment variable
        env_db_path = os.environ.get("VOCDICT")
        if env_db_path and os.path.isfile(env_db_path):
            self.db_path = env_db_path
        elif not os.path.isfile(db_path):
            panic(f"database '{db_path}' is not found")

    @property
    # lazy load database connection
    def conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def translate(self, word):
        self.last_text = word
        cursor = self.conn.cursor()
        cursor.execute("SELECT translation FROM dictionary WHERE word = ?", (word,))
        result = cursor.fetchone()
        return result[0] if result else "not found"

    def __del__(self):
        if self._conn:
            self._conn.close()

class Voc:
    def __init__(self):
        self.translator = Translator()

        icon_data = load_icon_scaled("assets/icon.png", target_height=20),
        self.layout = [
            [
               sg.Image(
                    data=icon_data,
                    background_color=PALETTE["black"],
                    pad=(2, 1),
                ),
                sg.Push(background_color=PALETTE["black"]),
                sg.Button(
                    "?",
                    key="-HELP-",
                    font=(FONT_NAME, 9),
                    size=(2, 1),
                    button_color=(PALETTE["black"], PALETTE["yellow"]),
                    border_width=0,
                    pad=(2, 1),
                    tooltip="Help"
                ),
                sg.Button(
                    "○",
                    key="-TOGGLE-ON-TOP-",
                    font=(FONT_NAME, 9),
                    size=(2, 1),
                    button_color=(PALETTE["black"], PALETTE["cyan"]),
                    border_width=0,
                    pad=(2, 1),
                    tooltip="Toggle on top"
                ),
                sg.Button(
                    "x",
                    key="-CLOSE-",
                    font=(FONT_NAME, 9),
                    size=(2, 1),
                    button_color=(PALETTE["black"], PALETTE["orange"]),
                    border_width=0,
                    pad=(2, 1),
                    tooltip="Close window"
                ),
            ],
            [
                sg.Text(
                    "key",
                    font=(FONT_NAME, 12),
                    text_color=PALETTE["deep_pink"],
                    background_color=PALETTE["black"],
                    size=(4, 1),
                    pad=((10, 5), (8, 5))
                ),
                sg.Input(
                    key="-KEY-",
                    font=(FONT_NAME, 12),
                    expand_x=True,
                    background_color=PALETTE["gray"],
                    text_color=PALETTE["white"],
                    border_width=0,
                    pad=(10, 8),
                    justification='left',
                    focus=True
                ),
            ],
            [
                sg.Text(
                    "val",
                    font=(FONT_NAME, 12),
                    text_color=PALETTE["purple"],
                    background_color=PALETTE["black"],
                    size=(4, 1),
                    pad=((10, 5), (5, 8))
                ),
                sg.Input(
                    key="-VAL-",
                    font=(FONT_NAME, 12),
                    expand_x=True,
                    background_color=PALETTE["gray"],
                    text_color=PALETTE["white"],
                    border_width=0,
                    pad=(10, 8),
                    justification='left',
                    readonly=True,
                    disabled_readonly_background_color=PALETTE["gray"],
                ),
            ]
        ]

        self.window = sg.Window(
            "VOC",
            self.layout,
            no_titlebar=True,
            grab_anywhere=True,
            resizable=False,
            keep_on_top=False,
            background_color=PALETTE["black"],
            finalize=True,
            margins=(6, 6),
            element_padding=(0, 0),
            element_justification='left',
            alpha_channel=1,
            size=(400, 120),
            icon="assets/icon.ico",
        )

        self._enhance_ui()
        self._bind_shortcuts()

    def run(self):
        while True:
            event, values = self.window.read(timeout=100)

            # handle event
            if event in (sg.WINDOW_CLOSED, "-CLOSE-"):
                break

            if event == "-HELP-":
                self._show_help()
                continue
            elif event == "-TOGGLE-ON-TOP-":
                self._toggle_on_top()
                continue
            elif event == "-CLEAR-ALL-":
                self.window["-KEY-"].set_focus()
                self.window["-KEY-"].update("")
                self.window["-VAL-"].update("")
                continue
            elif event == "-CLEAR-WORD-":
                self.window["-KEY-"].set_focus()
                current_text = values["-KEY-"].strip()
                if current_text:
                    words = current_text.split()
                    if words:
                        words.pop()
                        new_text = " ".join(words)
                        self.window["-KEY-"].update(new_text)
            elif event == "-FOCUS-KEY-":
                self.window["-KEY-"].set_focus()
                self.window["-KEY-"].update(select=True)
                continue
            elif event == "-SCROLL-UP-VAL-":
                val_input = self.window["-VAL-"].Widget
                val_input.xview_scroll(-3, "units")
                if self.window["-KEY-"].Widget.focus_get():
                    self.window["-KEY-"].set_focus()
                continue
            elif event == "-SCROLL-DOWN-VAL-":
                val_input = self.window["-VAL-"].Widget
                val_input.xview_scroll(3, "units")
                if self.window["-KEY-"].Widget.focus_get():
                    self.window["-KEY-"].set_focus()
                continue

            # translation
            text = values["-KEY-"].strip().lower()
            if len(text) > 32 or text == self.translator.last_text:
                continue
            result = self.translator.translate(text)

            # visual feedback for not found results
            if result == "not found":
                self.window["-VAL-"].update(
                    result,
                    text_color=PALETTE["red"]
                )
            else:
                self.window["-VAL-"].update(
                    result,
                    text_color=PALETTE["white"]
                )

        self.cleanup()

    def cleanup(self):
        self.window.close()

    def _bind_shortcuts(self):
        self.window.bind("<Control-u>", "-CLEAR-ALL-")
        self.window.bind("<Control-e>", "-CLOSE-")
        self.window.bind("<Control-o>", "-TOGGLE-ON-TOP-")
        self.window.bind("<Control-h>", "-CLEAR-WORD-")
        self.window.bind("<Control-l>", "-FOCUS-KEY-")
        self.window.bind("<Control-k>", "-SCROLL-UP-VAL-")
        self.window.bind("<Control-j>", "-SCROLL-DOWN-VAL-")

    def _enhance_ui(self):
        # make window appear in taskbar
        if sys.platform == "win32":
            # BUG: need extra action to active the icon in taskbar
            hwnd = ctypes.windll.user32.GetParent(self.window.TKroot.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x40000)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x23)

        # apply enhanced styling after window creation
        self.window.TKroot.configure(bg=PALETTE["black"])

        # style input fields for better integration
        if '-KEY-' in self.window.AllKeysDict:
            key_input = self.window['-KEY-']
            key_input.Widget.configure(
                insertbackground=PALETTE["deep_pink"],
                selectbackground=PALETTE["deep_pink"],
                selectforeground=PALETTE["black"],
                relief='flat',
            )
        if '-VAL-' in self.window.AllKeysDict:
            val_input = self.window['-VAL-']
            val_input.Widget.configure(
                insertbackground=PALETTE["purple"],
                selectbackground=PALETTE["purple"],
                selectforeground=PALETTE["black"],
                relief='flat',
            )
            self._bind_horizontal_scroll(val_input) # bind mouse wheel for horizontal scrolling

    def _bind_horizontal_scroll(self, val_input):
        """Bind mouse wheel to horizontal scroll on VAL input"""
        entry = val_input.Widget

        def on_mousewheel(event):
            # scroll horizontally with larger step (3 units per tick)
            if hasattr(event, 'delta'):  # Windows
                if event.delta > 0:
                    entry.xview_scroll(-3, "units")  # scroll left
                else:
                    entry.xview_scroll(3, "units")   # scroll right
            else:  # Linux (Button-4 up, Button-5 down)
                if event.num == 4:
                    entry.xview_scroll(-3, "units")
                elif event.num == 5:
                    entry.xview_scroll(3, "units")
            return "break"  # prevent event propagation

        # bind events for cross-platform support
        entry.bind("<MouseWheel>", on_mousewheel)   # Windows
        entry.bind("<Button-4>", on_mousewheel)     # Linux scroll up
        entry.bind("<Button-5>", on_mousewheel)     # Linux scroll down

    def _toggle_on_top(self):
        current = self.window.TKroot.attributes('-topmost')
        self.window.TKroot.attributes('-topmost', not current)
        # visual feedback for keep_on_top
        if current:
            text = "○"
            button_color = (PALETTE["black"], PALETTE["cyan"])
        else:
            text = "◉"
            button_color = (PALETTE["black"], PALETTE["white"])
        self.window["-TOGGLE-ON-TOP-"].update(text=text, button_color=button_color)

    def _show_help(self):
        help_text = """Shortcuts:
        Ctrl+U       - Clear all
        Ctrl+E       - Exit
        Ctrl+O       - Toggle on top
        Ctrl+H       - Clear previous word
        Ctrl+L       - Focus search box
        Ctrl+K/J     - Scroll VAL left/right
        """
        sg.popup(help_text, title="Help", font=(FONT_NAME, 10), keep_on_top=True)

if __name__ == "__main__":
    app = Voc()
    app.run()
