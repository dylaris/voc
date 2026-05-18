import os
import json
import sqlite3
import ctypes
import sys
import time
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

class Dict:
    def __init__(self, db_path="dict.db"):
        self.last_text = ""
        self.db_path = db_path
        self._conn = None

        # check environment variable
        env_db_path = os.environ.get("VOCDICT")

        if env_db_path and os.path.isfile(env_db_path):
            self.db_path = env_db_path
        elif not os.path.isfile(db_path):
            panic(f"database '{db_path}' is not found")

    @property
    def conn(self):
        # lazy load database connection
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def translate(self, word):
        self.last_text = word
        cursor = self.conn.cursor()

        # first try: search by word column
        cursor.execute("SELECT translation FROM dictionary WHERE word = ?", (word,))
        result = cursor.fetchone()

        if result:
            return result[0]

        # second try: remove spaces and search by sw column
        sw_word = word.replace(" ", "")
        cursor.execute("SELECT translation FROM dictionary WHERE sw = ?", (sw_word,))
        result = cursor.fetchone()

        return result[0] if result else "not found"

    def pick(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT word, translation FROM dictionary ORDER BY RANDOM() LIMIT 1")
        result = cursor.fetchone()
        return (result[0], result[1]) if result else ("", "not found")

    def __del__(self):
        if self._conn:
            self._conn.close()

class Voc:
    def __init__(self):
        self.dict            = Dict()
        self.on_top          = False
        self.flashcard       = False
        self.last_flash_time = 0
        self.flash_interval  = 5
        self.layout          = self.create_layout()
        self.window          = self.create_window()
        self.enhance_ui()
        self.bind_shortcuts()

    def run(self):
        while True:
            event, values = self.window.read(timeout=100)

            if event in (sg.WINDOW_CLOSED, "-CLOSE-"):
                break
            elif event == "-HELP-":
                self.show_help()
            elif event == "-TOGGLE-ON-TOP-":
                self.toggle_on_top()
            elif event == "-TOGGLE-FLASHCARD-":
                self.toggle_flashcard()
            elif event == "-CLEAR-INPUT-":
                self.clear_input()
            elif event == "-CLEAR-WORD-":
                self.clear_word(values)
            elif event == "-FOCUS-KEY-":
                self.focus_key()
            elif event == "-SCROLL-UP-VAL-":
                self.scroll_val(-3)
            elif event == "-SCROLL-DOWN-VAL-":
                self.scroll_val(3)
            else:
                if self.flashcard:
                    self.auto_play()
                else:
                    self.translate(values)

        self.cleanup()

    def cleanup(self):
        self.window.close()

    def auto_play(self):
        now_time = time.time()
        if now_time - self.last_flash_time >= self.flash_interval:
            self.last_flash_time = now_time
            k, v = self.dict.pick()
            self.window["-KEY-"].update(k)
            self.window["-VAL-"].update(v, text_color=PALETTE["white"])

    def create_layout(self):
        icon_data = load_icon_scaled("assets/icon.png", target_height=20),
        return [
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
                    "◇",
                    key="-TOGGLE-FLASHCARD-",
                    font=(FONT_NAME, 9),
                    size=(2, 1),
                    button_color=(PALETTE["black"], PALETTE["green"]),
                    border_width=0,
                    pad=(2, 1),
                    tooltip="Toggle flashcard"
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
                    focus=True,
                    disabled_readonly_background_color=PALETTE["gray"],
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

    def create_window(self):
        return sg.Window(
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

    def bind_shortcuts(self):
        self.window.bind("<Control-u>", "-CLEAR-INPUT-")
        self.window.bind("<Control-e>", "-CLOSE-")
        self.window.bind("<Control-f>", "-TOGGLE-FLASHCARD-")
        self.window.bind("<Control-o>", "-TOGGLE-ON-TOP-")
        self.window.bind("<Control-h>", "-CLEAR-WORD-")
        self.window.bind("<Control-l>", "-FOCUS-KEY-")
        self.window.bind("<Control-k>", "-SCROLL-UP-VAL-")
        self.window.bind("<Control-j>", "-SCROLL-DOWN-VAL-")

    def enhance_ui(self):
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

    def show_help(self):
        help_text = """Shortcuts:
        Ctrl+U       - Clear input
        Ctrl+E       - Exit
        Ctrl+F       - Toggle flashcard
        Ctrl+O       - Toggle on top
        Ctrl+H       - Clear previous word
        Ctrl+L       - Focus search box
        Ctrl+K/J     - Scroll VAL left/right
        """
        sg.popup(help_text, title="Help", font=(FONT_NAME, 10), keep_on_top=True)

    def translate(self, values):
        # translation
        text = values["-KEY-"].strip().lower()
        if len(text) > 32 or text == self.dict.last_text:
            return
        result = self.dict.translate(text)

        # visual feedback for not found results
        if result == "not found":
            color = PALETTE["red"]
        else:
            color = PALETTE["white"]
        self.window["-VAL-"].update(result, text_color=color)

    def toggle_flashcard(self):
        # visual feedback for flashcard
        self.flashcard = not self.flashcard
        if self.flashcard:
            text = "◆"
            color = (PALETTE["black"], PALETTE["white"])
            readonly = True
        else:
            text = "◇"
            color = (PALETTE["black"], PALETTE["green"])
            readonly = False
        self.window["-TOGGLE-FLASHCARD-"].update(text=text, button_color=color)
        self.window["-KEY-"].update(readonly=readonly)

    def toggle_on_top(self):
        # visual feedback for keep_on_top
        self.on_top = not self.on_top
        if self.on_top:
            text = "◉"
            color = (PALETTE["black"], PALETTE["white"])
        else:
            text = "○"
            color = (PALETTE["black"], PALETTE["cyan"])
        self.window.TKroot.attributes('-topmost', self.on_top)
        self.window["-TOGGLE-ON-TOP-"].update(text=text, button_color=color)

    def clear_input(self):
        self.window["-KEY-"].set_focus()
        self.window["-KEY-"].update("")
        self.window["-VAL-"].update("")

    def clear_word(self, values):
        self.window["-KEY-"].set_focus()
        current_text = values["-KEY-"].strip()
        if current_text:
            words = current_text.split()
            if words:
                words.pop()
                new_text = " ".join(words)
                self.window["-KEY-"].update(new_text)

    def focus_key(self):
        self.window["-KEY-"].set_focus()
        self.window["-KEY-"].update(select=True)

    def scroll_val(self, units):
        val_input = self.window["-VAL-"].Widget
        val_input.xview_scroll(units, "units")
        if self.window["-KEY-"].Widget.focus_get():
            self.window["-KEY-"].set_focus()

if __name__ == "__main__":
    app = Voc()
    app.run()
