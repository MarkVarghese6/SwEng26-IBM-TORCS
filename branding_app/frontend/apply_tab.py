# Apply tab — backup originals + copy branding into TORCS
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from backend.config_service import (
    load_active_profile,
    get_active_profile_name,
    load_settings,
)
from backend.branding_service import build_apply_plan
from backend.file_service import (
    UPLOADS_DIR,
    backup_file,
    copy_to_torcs,
    validate_image_dimensions,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ApplyTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, padding=16)
        notebook.add(self.frame, text="Apply All")

        # add background colour
        BG = "#fcffff"
        style = ttk.Style()
        style.configure("BG.TFrame", background=BG)
        style.configure("BG.TLabel", background=BG, foreground="#321e2d")
        self.frame.configure(style="BG.TFrame")

        # Frame for stuff in the center of the page e.g. text, button
        inner = ttk.Frame(self.frame, style="BG.TFrame")
        inner.pack(pady=(150, 0))

        # label for title text
        ttk.Label(
            inner,
            text="Apply All Branding",
            font=("Segoe UI", 28, "bold"),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 10))

        self.profile_var = tk.StringVar(value="")
        ttk.Label(
            inner,
            textvariable=self.profile_var,
            font=("Segoe UI", 10),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 10))

        # label for subtitle text
        ttk.Label(
            inner,
            text="Copies your uploaded assets into TORCS and backs up the original files.",
            font=("Segoe UI", 15),
            style="BG.TLabel",
            foreground="#321e2d",
        ).pack(anchor="center", pady=(0, 24))

        # Add image to the button
        apply_image_path = os.path.join(BASE_DIR, "assets", "images", "apply_btn.png")
        self.apply_photo = tk.PhotoImage(file=apply_image_path)

        # button!
        tk.Button(
            inner,
            image=self.apply_photo,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._apply,
        ).pack(anchor="center")

        self._refresh_profile_label()
        self.frame.bind("<Map>", lambda e: self._refresh_profile_label())

    def _refresh_profile_label(self):
        self.profile_var.set(f"Active profile: {get_active_profile_name() or '(none)'}")

    @staticmethod
    def _apply():
        settings = load_settings()
        torcs_root = settings.get("torcs_root", "").strip()
        if not torcs_root:
            messagebox.showerror("Apply", "Set TORCS root first in Settings.")
            return

        profile = load_active_profile()
        if not profile:
            messagebox.showerror("Apply", "No branding profile found in config.")
            return

        profile_name = get_active_profile_name()
        planned_copies, unresolved = build_apply_plan(profile, UPLOADS_DIR)

        if not planned_copies:
            messagebox.showwarning(
                "Apply",
                "No assets are ready to apply. Upload files or set profile file paths.",
            )
            return

        invalid = []
        for item in planned_copies:
            ok, msg = validate_image_dimensions(
                item["source_path"], item.get("width"), item.get("height")
            )
            if not ok:
                invalid.append(f"{item['label']}: {msg}")
        if invalid:
            messagebox.showerror(
                "Apply",
                "Validation failed:\n" + "\n".join(invalid[:6]),
            )
            return

        snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        for item in planned_copies:
            dest = os.path.join(torcs_root, item["target_path"])
            if os.path.exists(dest):
                backup_file(
                    dest,
                    torcs_root,
                    snapshot_id=snapshot_id,
                    profile_name=profile_name,
                )
            copy_to_torcs(
                item["source_path"],
                torcs_root,
                item["target_path"],
                profile_name=profile_name,
            )

        unresolved_note = f" ({len(unresolved)} unresolved)" if unresolved else ""
        messagebox.showinfo(
            "Apply",
            f"Applied {len(planned_copies)} file(s){unresolved_note}. Snapshot: {snapshot_id}",
        )
