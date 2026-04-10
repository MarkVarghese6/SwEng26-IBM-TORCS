# Restore tab — revert to backed-up originals
import os
import tkinter as tk
from tkinter import ttk, messagebox

from backend.config_service import get_active_profile_name, load_settings
from backend.file_service import get_profile_backup_root, restore_backup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class RestoreTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, padding=16)
        notebook.add(self.frame, text="Restore")

        # add background colour
        BG = "#fcffff"
        style = ttk.Style()
        style.configure("BG.TFrame", background=BG)
        style.configure("BG.TLabel", background=BG, foreground="#321e2d")
        self.frame.configure(style="BG.TFrame")

        # add a frame for the tab
        inner = ttk.Frame(self.frame, style="BG.TFrame")
        inner.pack(pady=(150, 0))

        # label for title text
        ttk.Label(
            inner,
            text="Restore Originals",
            font=("Segoe UI", 28, "bold"),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 10))

        # label for subtitle text
        ttk.Label(
            inner,
            text="Revert to the backed-up original files.",
            font=("Segoe UI", 15),
            style="BG.TLabel",
            foreground="#321e2d",
        ).pack(anchor="center", pady=(0, 24))

        # add image to cover the button
        restore_image_path = os.path.join(
            BASE_DIR, "assets", "images", "restore_btn.png"
        )
        self.restore_photo = tk.PhotoImage(file=restore_image_path)

        # button!
        tk.Button(
            inner,
            image=self.restore_photo,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._restore,
        ).pack(anchor="center")

    @staticmethod
    def _restore():
        settings = load_settings()
        torcs_root = settings.get("torcs_root", "").strip()
        if not torcs_root:
            messagebox.showerror("Restore", "Set TORCS root first in Settings.")
            return

        profile_name = get_active_profile_name()
        backups_root = get_profile_backup_root(profile_name)

        if not os.path.isdir(backups_root):
            messagebox.showwarning("Restore", "No backups are available.")
            return

        snapshots = [
            name
            for name in os.listdir(backups_root)
            if os.path.isdir(os.path.join(backups_root, name))
        ]
        if not snapshots:
            messagebox.showwarning("Restore", "No backups are available.")
            return

        snapshot_id = sorted(snapshots)[-1]
        snapshot_root = os.path.join(backups_root, snapshot_id)

        restored_count = 0
        for root, _dirs, files in os.walk(snapshot_root):
            for filename in files:
                src = os.path.join(root, filename)
                rel = os.path.relpath(src, snapshot_root)
                restore_backup(snapshot_id, torcs_root, rel, profile_name=profile_name)
                restored_count += 1

        messagebox.showinfo(
            "Restore",
            f"Restored {restored_count} file(s) from snapshot {snapshot_id}.",
        )
