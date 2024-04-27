import os
import glob
import json
import tkinter as tk
from tkinter import scrolledtext, simpledialog

SETTINGS_FILE = "settings.json"
HISTORY_LIMIT = 20


def get_files_and_content(directory, extensions, exclude_files):
    output = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            extension = os.path.splitext(filename)[1].lstrip(
                "."
            )  # Get the file extension
            if extension not in extensions and "*" not in extensions:
                continue
            if os.path.basename(filename) in exclude_files:
                continue
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(
                file_path, directory
            )  # Get the relative path
            output.append(("title", "########\n"))
            output.append(("title", f"# {relative_path}\n"))
            output.append(("title", "########\n"))
            with open(file_path, "r", encoding="utf8") as f:
                content = f.read()
                output.append(("content", content))
                output.append(("content", "\n\n"))
    return output


def save_settings(directory, extensions, exclude_files):
    new_setting = {
        "directory": directory,
        "extensions": extensions,
        "exclude_files": exclude_files,
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    # If the directory already exists in the history, remove it
    history = [setting for setting in history if setting["directory"] != directory]

    # Add the new settings at the beginning
    history.insert(0, new_setting)
    history = history[:HISTORY_LIMIT]  # Limit the history to the last 20 entries

    with open(SETTINGS_FILE, "w", encoding="utf8") as f:
        json.dump(history, f)

    return history


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def show_result():
    directory = dir_entry.get()
    extensions = ext_entry.get().split(",")
    exclude_files = exclude_entry.get().split(",")

    # Convert to list and remove "." and "*"
    extensions = [ext.strip().lstrip("*.") for ext in extensions]
    exclude_files = [file.strip() for file in exclude_files]

    result = get_files_and_content(directory, extensions, exclude_files)
    text_area.delete(1.0, tk.END)

    for tag, content in result:
        end_index = text_area.index(tk.INSERT)  # Current end index
        text_area.insert(tk.INSERT, content)
        start_index = text_area.index(tk.INSERT)  # New end index
        text_area.tag_add(tag, end_index, start_index)
        if tag == "title":
            text_area.tag_config(
                tag, background="lightgray"
            )  # Or whatever color you want

    global settings
    settings = save_settings(directory, extensions, exclude_files)

    update_dropdown()


def select_history(*args):
    selected_setting = history_var.get()
    for setting in settings:
        if setting["directory"] == selected_setting:
            dir_entry.delete(0, tk.END)
            dir_entry.insert(0, setting["directory"])

            ext_entry.delete(0, tk.END)
            ext_entry.insert(0, ", ".join(setting["extensions"]))

            exclude_entry.delete(0, tk.END)
            exclude_entry.insert(0, ", ".join(setting["exclude_files"]))


def update_dropdown():
    history_dropdown["menu"].delete(0, "end")
    # メニューコマンドを追加するが、表示は 'history' を維持
    for setting in settings:
        history_dropdown["menu"].add_command(
            label=setting["directory"],
            command=lambda value=setting["directory"]: history_var.set(value),
        )


# Tkinterウィンドウとウィジェットの初期化
root = tk.Tk()
root.geometry("1200x800")

input_frame = tk.Frame(root, width=1200, height=50)
input_frame.pack_propagate(0)  # Don't shrink
input_frame.pack(anchor="w")

# ラベルとエントリーの定義
dir_label = tk.Label(input_frame, text="Directory:")
dir_label.pack(side=tk.LEFT)

dir_entry = tk.Entry(input_frame, width=30)
dir_entry.pack(side=tk.LEFT)

ext_label = tk.Label(input_frame, text="Extensions:")
ext_label.pack(side=tk.LEFT)

ext_entry = tk.Entry(input_frame)
ext_entry.pack(side=tk.LEFT)

exclude_label = tk.Label(input_frame, text="Exclude Files:")
exclude_label.pack(side=tk.LEFT)

exclude_entry = tk.Entry(input_frame, width=50)
exclude_entry.pack(expand=True, fill=tk.X, side=tk.LEFT)

# ボタンの定義
btn = tk.Button(input_frame, text="Get Files and Content", command=show_result)
btn.pack(side=tk.LEFT)

# スクロール可能なテキストエリアの定義
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
text_area.pack(fill="both", expand=True)

# 設定のロード
settings = load_settings()

# ドロップダウンメニューの更新とイベントハンドラの設定
history_var = tk.StringVar(root)
history_var.trace_add("write", select_history)
if settings:
    history_var.set('history')

history_dropdown = tk.OptionMenu(input_frame, history_var, "No history")
history_dropdown.config(width=10)
history_dropdown.pack(side=tk.LEFT)
update_dropdown()

# 初期設定の適用
if settings:
    select_history(None)  # 初期選択を行う

root.mainloop()
