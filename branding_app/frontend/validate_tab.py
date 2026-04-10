# Validate tab — stub for image checks
import os
import tkinter as tk
from tkinter import ttk
from backend.config_service import load_active_profile
from backend.branding_service import build_apply_plan
from backend.file_service import UPLOADS_DIR
from backend.file_service import validate_image_dimensions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ValidateTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, padding=16)
        notebook.add(self.frame, text="Validate")

        # background colour
        BG = "#fcffff"

        style = ttk.Style()
        style.configure("BG.TFrame", background=BG)
        style.configure("BG.TLabel", background=BG, foreground="#321e2d")

        # treeview colours
        style.configure(
            "Validate.Treeview",
            background="#dfe3ee",
            fieldbackground="#dfe3ee",
            foreground="#321e2d",
            font=("Segoe UI", 10),
            rowheight=26,
        )
        style.configure(
            "Validate.Treeview.Heading",
            background="#dfe3ee",
            foreground="#321e2d",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Validate.Treeview",
            background=[("selected", "#4c72b0")],
            foreground=[("selected", "white")],
        )

        self.frame.configure(style="BG.TFrame")

        # centered frame for content
        inner = ttk.Frame(self.frame, style="BG.TFrame")
        inner.pack(pady=(60, 0))

        # title
        ttk.Label(
            inner,
            text="Validate",
            font=("Segoe UI", 28, "bold"),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 8))

        # subtitle
        ttk.Label(
            inner,
            text="Check your image files meet their required dimensions.",
            font=("Segoe UI", 15),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 16))

        # treeview to display validation
        cols = ("slot", "status", "details")
        self.tree = ttk.Treeview(
            inner,
            columns=cols,
            show="headings",
            height=4,
            style="Validate.Treeview",
        )
        self.tree.heading("slot", text="Slot")
        self.tree.heading("status", text="Status")
        self.tree.heading("details", text="Details")
        self.tree.column("slot", width=140, anchor="w")
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("details", width=320, anchor="w")
        self.tree.pack(pady=(0, 12))

        # button to validate images
        validate_btn_path = os.path.join(
            BASE_DIR, "assets", "images", "validate_btn.png"
        )
        self.run_img = tk.PhotoImage(file=validate_btn_path)

        tk.Button(
            inner,
            image=self.run_img,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._validate,
        ).pack(anchor="center", pady=(0, 0))

        self._populate(None)

    def _populate(self, rows):
        if rows is None:
            rows = [
                ("splash_screen", "n/a", "Waiting for validation"),
                ("loading_screen", "n/a", "Waiting for validation"),
                ("livery", "n/a", "Waiting for validation"),
            ]

        for slot, status, detail in rows:
            self.tree.insert("", "end", values=(slot, status, detail))

    def _validate(self):
        profile = load_active_profile()
        if not profile:
            profile_status = [
                ("profile", "Failed", "No profile configured in default_profiles.json")
            ]
        else:
            plan, unresolved = build_apply_plan(profile, UPLOADS_DIR)

            profile_status = []
            for item in plan:
                ok, msg = validate_image_dimensions(
                    item["source_path"], item.get("width"), item.get("height")
                )
                profile_status.append(
                    (item["label"], "Passed" if ok else "Failed", msg)
                )

            for item in unresolved:
                profile_status.append(
                    (
                        item["label"],
                        "Failed",
                        f"Missing source file for target {item['target_path']}",
                    )
                )

            if not profile_status:
                profile_status = [
                    ("profile", "Failed", "No target assets configured in profile")
                ]

        for row in self.tree.get_children():
            self.tree.delete(row)
        self._populate(profile_status)
