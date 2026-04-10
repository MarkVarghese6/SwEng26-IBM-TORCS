# Settings tab — set TORCS root path
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from backend.config_service import load_settings, save_settings


class SettingsTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Settings")

        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        # add background colour
        BG = "#fcffff"

        style = ttk.Style()
        style.configure("BG.TFrame", background=BG)
        style.configure("BG.TLabel", background=BG)
        style.configure("Rounded.TEntry", padding=10)

        self.frame.configure(style="BG.TFrame")

        # --------------------------- Left side text box --------------------------------
        text_frame = ttk.Frame(self.frame, padding=(40, 48, 40, 0), style="BG.TFrame")
        text_frame.grid(row=0, column=0, sticky="ew")
        text_frame.columnconfigure(0, weight=1)

        ttk.Label(
            text_frame,
            text="Settings",
            font=("Segoe UI", 28, "bold"),
            style="BG.TLabel",
        ).grid(row=0, column=0, pady=(80, 0))

        ttk.Label(
            text_frame,
            text="Set the path of your TORCS installation to allow the editor to locate files.",
            font=("Segoe UI", 15),
            justify="left",
            wraplength=480,
            style="BG.TLabel",
        ).grid(row=1, column=0)

        # -------------------------------------- Center part -------------------------------
        controls_frame = ttk.Frame(self.frame, style="BG.TFrame")
        controls_frame.grid(row=1, column=0)

        self.path_var = tk.StringVar(value=load_settings().get("torcs_root", ""))

        entry = ttk.Entry(
            controls_frame, textvariable=self.path_var, width=70, style="Rounded.TEntry"
        )
        entry.grid(row=1, column=0, padx=(0, 8))

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Load browse button image
        browse_image_path = os.path.join(BASE_DIR, "assets", "images", "browse_btn.png")
        self.browse_photo = tk.PhotoImage(file=browse_image_path)

        tk.Button(
            controls_frame,
            image=self.browse_photo,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._browse,
        ).grid(row=1, column=1, pady=(30, 0))

        # Load save button image
        save_image_path = os.path.join(BASE_DIR, "assets", "images", "save_btn.png")
        self.save_photo = tk.PhotoImage(file=save_image_path)

        tk.Button(
            controls_frame,
            image=self.save_photo,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._save,
        ).grid(row=2, column=0, columnspan=2, pady=(0, 0))

    # --------------------------------- Methods ----------------------------------------

    def _browse(self):
        path = filedialog.askdirectory(title="Select TORCS Root Folder")
        if path:
            self.path_var.set(path)

    def _save(self):
        if not self.validate_torcs_folder():
            messagebox.showerror("Error", "Selected path is not a valid torcs folder")
            return

        cfg = load_settings()
        cfg["torcs_root"] = self.path_var.get().strip()
        save_settings(cfg)
        messagebox.showinfo("Settings", "Settings saved.")

    def validate_torcs_folder(self):
        path = self.path_var.get()
        expected_subfolders = ["cars", "data", "tracks"]
        for folder in expected_subfolders:
            if not os.path.isdir(os.path.join(path, folder)):
                return False
        return True
