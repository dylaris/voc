import PySimpleGUI as sg
import pyautogui
import pyperclip
import time
import threading
import re
import json
import os
import sys
from pynput import mouse

# ----------------------
# Resource Path Helper
# ----------------------
def get_resource_path(relative_path):
    """Get absolute path for resource, compatible with PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Load external font
FONT_PATH = get_resource_path("fonts/IosevkaTerm.ttf")
if os.path.exists(FONT_PATH):
    FONT_NAME = FONT_PATH
else:
    FONT_NAME = "Consolas"  # Fallback if font not found
    print(f"Warning: Font file '{FONT_PATH}' not found, using fallback font.")

FONT_SIZE = 11

# ----------------------
# Palette
# ----------------------
COLOR_BG_DARK      = "#0F1419"  # Main background
COLOR_BG_MID       = "#131721"  # Panel/input background
COLOR_BG_LIGHT     = "#151A23"  # Slightly lighter bg
COLOR_FG           = "#E6E1CF"  # Main text
COLOR_FG_DIM       = "#707A8C"  # Comments/dimmed text
COLOR_RED          = "#FF3333"  # Error/close button
COLOR_GREEN        = "#BAE67E"  # Success/save button
COLOR_YELLOW       = "#FFD580"  # Highlight/keywords
COLOR_BLUE         = "#73D0FF"  # Selection/highlight
COLOR_PURPLE       = "#D4BFFF"  # Accent/punctuation
COLOR_ORANGE       = "#FFAA33"  # Numbers/strings

# ----------------------
# Dictionary
# ----------------------
def load_dict():
    try:
        with open("words.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

DICT = load_dict()

def translate(word):
    return DICT.get(word.strip().lower(), "not found")

# ----------------------
# UI Layout
# ----------------------
layout = [
    [
        sg.Push(background_color=COLOR_BG_DARK),
        sg.Button("✓", key="-SAVE-", font=(FONT_NAME, 9), size=(2, 1),
                  button_color=(COLOR_BG_DARK, COLOR_GREEN), border_width=0,
                  pad=((2, 6), (2, 1)), tooltip="Save translation"),
        sg.Button("✕", key="-CLOSE-", font=(FONT_NAME, 9), size=(2, 1),
                  button_color=(COLOR_BG_DARK, COLOR_RED), border_width=0,
                  pad=(2, 1), tooltip="Close window"),
    ],
    [
        sg.Text("term", font=(FONT_NAME, FONT_SIZE), text_color=COLOR_YELLOW,
                background_color=COLOR_BG_DARK, size=(4, 1), pad=((10, 5), (10, 5))),
        sg.Input(key="-KEY-", font=(FONT_NAME, FONT_SIZE), expand_x=True,
                 background_color=COLOR_BG_MID, text_color=COLOR_FG,
                 border_width=0, pad=(10, 10),
                 justification='left', focus=True),
    ],
    [
        sg.Text("defn", font=(FONT_NAME, FONT_SIZE), text_color=COLOR_GREEN,
                background_color=COLOR_BG_DARK, size=(4, 1), pad=((10, 5), (10, 10))),
        sg.Input(key="-VAL-", font=(FONT_NAME, FONT_SIZE), expand_x=True,
                 background_color=COLOR_BG_MID, text_color=COLOR_BLUE,
                 border_width=0, pad=(10, 10),
                 justification='left'),
    ]
]

# ----------------------
# Window
# ----------------------
window = sg.Window(
    "VOC", layout,
    no_titlebar=True,
    grab_anywhere=True,
    resizable=True,
    keep_on_top=True,
    background_color=COLOR_BG_DARK,
    finalize=True,
    margins=(15, 15),
    element_padding=(0, 0),
    element_justification='left',
    alpha_channel=0.98
)

# Apply enhanced styling after window creation
window.TKroot.configure(bg=COLOR_BG_DARK)

# Style input fields for better integration
if '-KEY-' in window.AllKeysDict:
    key_input = window['-KEY-']
    key_input.Widget.configure(
        insertbackground=COLOR_FG,
        selectbackground=COLOR_BLUE,
        selectforeground=COLOR_BG_MID,
        relief='flat',
        highlightthickness=1,
        highlightcolor=COLOR_BLUE,
        highlightbackground=COLOR_BG_LIGHT,
    )

if '-VAL-' in window.AllKeysDict:
    val_input = window['-VAL-']
    val_input.Widget.configure(
        insertbackground=COLOR_BLUE,
        selectbackground=COLOR_BLUE,
        selectforeground=COLOR_BG_MID,
        relief='flat',
        highlightthickness=1,
        highlightcolor=COLOR_BLUE,
        highlightbackground=COLOR_BG_LIGHT,
    )

last_text = ""

# ----------------------
# Text filter
# ----------------------
def is_valid_english(text, max_words=20):
    if not re.fullmatch(r'[A-Za-z\s\.,!?\'"-]+', text):
        return False
    return 1 <= len(text.split()) <= max_words

# ----------------------
# Get selected text
# ----------------------
def get_selected():
    old = pyperclip.paste()
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.02)
    res = pyperclip.paste().strip()
    pyperclip.copy(old)
    return res

# ----------------------
# Mouse listener
# ----------------------
def on_click(x, y, button, pressed):
    global last_text
    if button != mouse.Button.left or pressed:
        return

    # Ignore window clicks
    wx, wy = window.CurrentLocation()
    ww, wh = window.size
    if wx <= x <= wx + ww and wy <= y <= wy + wh:
        return

    text = get_selected()
    if not text or text == last_text or not is_valid_english(text):
        return

    last_text = text
    window["-KEY-"].update(text)
    window["-VAL-"].update(translate(text))

# ----------------------
# Background thread
# ----------------------
def start_listener():
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

thread = threading.Thread(target=start_listener, daemon=True)
thread.start()

# ----------------------
# Main loop
# ----------------------
while True:
    event, values = window.read(timeout=100)

    if event in (sg.WIN_CLOSED, "-CLOSE-"):
        break

    if event == "-SAVE-":
        k = values["-KEY-"].strip()
        v = values["-VAL-"].strip()
        print(f"Saving -> {k} : {v}")

    word = values["-KEY-"].strip()
    window["-VAL-"].update(translate(word))

window.close()


