import os
import json
import tkinter as tk
from tkinter import scrolledtext, ttk
from pathlib import Path
import fnmatch

SETTINGS_FILE = "settings.json"
HISTORY_LIMIT = 20


def read_gitignore(directory):
    gitignore_path = os.path.join(directory, ".gitignore")
    if not os.path.exists(gitignore_path):
        return set()

    ignored_patterns = set()
    with open(gitignore_path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                ignored_patterns.add(line)
    return ignored_patterns


def should_ignore_file(file_path, ignored_patterns):
    if not ignored_patterns:
        return False

    path = Path(file_path)

    for pattern in ignored_patterns:
        if path.match(pattern) or any(parent.match(pattern) for parent in path.parents):
            return True
    return False


def matches_pattern(filename, patterns, is_exclude=False):
    """
    ファイル名がパターンのいずれかにマッチするかチェックする
    patterns: カンマ区切りのパターン文字列のリスト
    is_exclude: 除外パターンかどうか（True の場合、空リストは何もマッチしない）
    """
    if is_exclude and not patterns:
        return False

    if not is_exclude and not patterns:
        return True

    if "*" in patterns:
        return True

    file_ext = os.path.splitext(filename)[1].lstrip(".")

    for pattern in patterns:
        pattern = pattern.strip()
        if not pattern:
            continue

        if any(c in pattern for c in "*?."):
            if fnmatch.fnmatch(filename, pattern):
                return True
        else:
            if pattern == file_ext:
                return True
            if not file_ext and pattern == filename:
                return True

    return False


def get_files_and_content(
    directory, include_patterns, exclude_patterns, respect_gitignore=False
):
    output = []
    ignored_patterns = read_gitignore(directory) if respect_gitignore else set()

    include_patterns = [p.strip() for p in include_patterns if p.strip()]
    exclude_patterns = [p.strip() for p in exclude_patterns if p.strip()]

    print(f"Include patterns: {include_patterns}")
    print(f"Exclude patterns: {exclude_patterns}")

    for root, dirs, files in os.walk(directory):
        if ".git" in dirs:
            dirs.remove(".git")

        for filename in files:
            if filename == ".gitignore":
                continue

            if not matches_pattern(filename, include_patterns, is_exclude=False):
                print(
                    f"Skipping {filename} - doesn't match include patterns"
                )
                continue
            if matches_pattern(filename, exclude_patterns, is_exclude=True):
                print(f"Skipping {filename} - matches exclude patterns")
                continue

            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, directory)

            if respect_gitignore and should_ignore_file(
                relative_path, ignored_patterns
            ):
                print(f"Skipping {filename} - ignored by .gitignore")
                continue

            print(f"Including file: {filename}")

            output.append(("title", "########\n"))
            output.append(("title", f"# {relative_path}\n"))
            output.append(("title", "########\n"))
            try:
                with open(file_path, "r", encoding="utf8") as f:
                    content = f.read()
                    output.append(("content", content))
                    output.append(("content", "\n\n"))
            except UnicodeDecodeError:
                output.append(
                    ("content", f"[Binary file or encoding error: {relative_path}]\n\n")
                )

    return output


def save_settings(directory, include_patterns, exclude_patterns, respect_gitignore):
    """
    設定を保存する
    """
    new_setting = {
        "directory": directory,
        "include_patterns": include_patterns,
        "exclude_patterns": exclude_patterns,
        "respect_gitignore": respect_gitignore,
    }

    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    history = [setting for setting in history if setting["directory"] != directory]
    history.insert(0, new_setting)
    history = history[:HISTORY_LIMIT]

    with open(SETTINGS_FILE, "w", encoding="utf8") as f:
        json.dump(history, f)

    return history


def load_settings():
    """
    保存された設定を読み込む
    """
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


class FileContentViewer:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x800")
        self.settings = load_settings()

        self.create_frames()
        self.create_history_section()
        self.create_input_section()
        self.create_text_area()

        if self.settings:
            self.select_history(None)

    def create_frames(self):
        self.history_frame = tk.Frame(self.root)
        self.history_frame.pack(fill="x", padx=5, pady=5)

        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(fill="x", padx=5, pady=5)

        self.text_frame = tk.Frame(self.root)
        self.text_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def create_history_section(self):
        history_label = tk.Label(self.history_frame, text="History:")
        history_label.pack(side=tk.LEFT)

        self.history_var = tk.StringVar(self.root)
        if self.settings:
            self.history_var.set("Select from history")

        style = ttk.Style()
        style.configure("History.TCombobox", width=50)

        self.history_combo = ttk.Combobox(
            self.history_frame,
            textvariable=self.history_var,
            style="History.TCombobox",
            state="readonly",
        )
        self.history_combo.pack(side=tk.LEFT, fill="x", expand=True, padx=(5, 0))
        self.update_dropdown()

        self.history_combo.bind("<<ComboboxSelected>>", self.select_history)
        self.history_combo.bind(
            "<Button-1>",
            lambda e: self.history_combo.event_generate("<<ComboboxSelected>>"),
        )

    def create_input_section(self):
        self.btn = tk.Button(
            self.input_frame, text="Get Files and Content", command=self.show_result
        )
        self.btn.pack(side=tk.LEFT)

        dir_label = tk.Label(self.input_frame, text="Directory:")
        dir_label.pack(side=tk.LEFT)

        self.dir_entry = tk.Entry(self.input_frame, width=30)
        self.dir_entry.pack(side=tk.LEFT, padx=(2, 10))

        include_label = tk.Label(self.input_frame, text="Include patterns:")
        include_label.pack(side=tk.LEFT)

        self.include_entry = tk.Entry(self.input_frame, width=20)
        self.include_entry.pack(side=tk.LEFT, padx=(2, 10))

        exclude_label = tk.Label(self.input_frame, text="Exclude patterns:")
        exclude_label.pack(side=tk.LEFT)

        self.exclude_entry = tk.Entry(self.input_frame, width=20)
        self.exclude_entry.pack(side=tk.LEFT, padx=(2, 10))

        self.gitignore_var = tk.BooleanVar()
        self.gitignore_check = tk.Checkbutton(
            self.input_frame, text="Respect .gitignore", variable=self.gitignore_var
        )
        self.gitignore_check.pack(side=tk.LEFT, padx=(0, 10))

    def create_text_area(self):
        self.text_area = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD)
        self.text_area.pack(fill="both", expand=True)

    def show_result(self):
        directory = self.dir_entry.get()
        include_patterns = [
            pattern.strip()
            for pattern in self.include_entry.get().split(",")
            if pattern.strip()
        ]
        exclude_patterns = [
            pattern.strip()
            for pattern in self.exclude_entry.get().split(",")
            if pattern.strip()
        ]
        respect_gitignore = self.gitignore_var.get()

        result = get_files_and_content(
            directory, include_patterns, exclude_patterns, respect_gitignore
        )

        self.text_area.delete(1.0, tk.END)

        for tag, content in result:
            end_index = self.text_area.index(tk.INSERT)
            self.text_area.insert(tk.INSERT, content)
            start_index = self.text_area.index(tk.INSERT)
            self.text_area.tag_add(tag, end_index, start_index)
            if tag == "title":
                self.text_area.tag_config(tag, background="lightgray")

        self.settings = save_settings(
            directory, include_patterns, exclude_patterns, respect_gitignore
        )
        self.update_dropdown()

    def select_history(self, event):
        selected_dir = self.history_var.get()
        for setting in self.settings:
            if setting["directory"] == selected_dir:
                self.dir_entry.delete(0, tk.END)
                self.dir_entry.insert(0, setting["directory"])

                self.include_entry.delete(0, tk.END)
                self.include_entry.insert(0, ", ".join(setting["include_patterns"]))

                self.exclude_entry.delete(0, tk.END)
                self.exclude_entry.insert(0, ", ".join(setting["exclude_patterns"]))

                self.gitignore_var.set(setting.get("respect_gitignore", False))

    def update_dropdown(self):
        if not self.settings:
            self.history_combo["values"] = ["No history"]
            return

        self.history_combo["values"] = [s["directory"] for s in self.settings]


if __name__ == "__main__":
    root = tk.Tk()
    root.title("File Content Viewer")
    app = FileContentViewer(root)
    root.mainloop()
