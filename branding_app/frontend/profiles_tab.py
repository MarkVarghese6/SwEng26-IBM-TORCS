# Profiles tab — shows branding profiles from JSON
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from backend.config_service import (
    load_profiles,
    get_active_profile_name,
    set_active_profile_name,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ProfilesTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, padding=16)
        notebook.add(self.frame, text="Profiles")

        self.profiles = []

        # background colour
        BG = "#fcffff"

        style = ttk.Style()
        style.configure("BG.TFrame", background=BG)
        style.configure("BG.TLabel", background=BG, foreground="#321e2d")

        # treeview colours, size and font
        style.configure(
            "Profiles.Treeview",
            background="#dfe3ee",
            fieldbackground="#dfe3ee",
            foreground="#321e2d",
            font=("Segoe UI", 10),
            rowheight=31,
        )
        style.configure(
            "Profiles.Treeview.Heading",
            background="#dfe3ee",
            foreground="#321e2d",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Profiles.Treeview",
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
            text="Profiles",
            font=("Segoe UI", 28, "bold"),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 8))

        # subtitle
        ttk.Label(
            inner,
            text="Choose one of the branding profiles currently available in your configuration",
            font=("Segoe UI", 15),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 16))

        # treeview
        cols = ("name", "description", "car")
        self.tree = ttk.Treeview(
            inner,
            columns=cols,
            show="headings",
            height=5,
            style="Profiles.Treeview",
        )
        self.tree.heading("name", text="Name")
        self.tree.heading("description", text="Description")
        self.tree.heading("car", text="Car Model")
        self.tree.column("name", width=150, anchor="w")
        self.tree.column("description", width=320, anchor="w")
        self.tree.column("car", width=140, anchor="center")
        self.tree.pack(pady=(0, 12))

        self.status_label = ttk.Label(
            inner,
            text="No profile selected",
            font=("Segoe UI", 11),
            style="BG.TLabel",
        )
        self.status_label.pack(anchor="center", pady=(0, 12))

        # image button
        apply_btn_path = os.path.join(BASE_DIR, "assets", "images", "apply_btn.png")
        self.apply_img = tk.PhotoImage(file=apply_btn_path)

        tk.Button(
            inner,
            image=self.apply_img,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._select_profile,
        ).pack(anchor="center", pady=(0, 0))

        self._refresh()

    def _refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.profiles = load_profiles() or []
        active_name = get_active_profile_name()

        if not self.profiles:
            self.tree.insert(
                "",
                "end",
                values=("(none)", "Add profiles to config/default_profiles.json", ""),
            )
            if hasattr(self, "status_label"):
                self.status_label.config(text="No profile selected")
            return

        active_iid = None

        for i, p in enumerate(self.profiles):
            car = p.get("livery", {}).get("car_model", "—")

            try:
                self.tree.insert(
                    "",
                    "end",
                    iid=str(i),
                    values=(p["name"], p.get("description", ""), car),
                )
                row_id = str(i)
            except TypeError:
                row_id = self.tree.insert(
                    "",
                    "end",
                    values=(p["name"], p.get("description", ""), car),
                )

            if str(p.get("name", "")).strip() == active_name:
                active_iid = row_id

        if active_iid is not None:
            if hasattr(self.tree, "selection_set"):
                self.tree.selection_set(active_iid)
            if hasattr(self.tree, "focus"):
                self.tree.focus(active_iid)
            if hasattr(self.tree, "see"):
                self.tree.see(active_iid)

            if hasattr(self, "status_label"):
                self.status_label.config(text=f"Selected profile: {active_name}")
        else:
            if hasattr(self, "status_label"):
                self.status_label.config(text="No profile selected")

    def _select_profile(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a profile first.")
            return

        row_id = selected[0]

        if not self.profiles:
            return
        # convert row ID back to profile index
        try:
            profile = self.profiles[int(row_id)]
        except (ValueError, IndexError):
            return
        # get profile name
        profile_name = str(profile.get("name", "")).strip()
        if not profile_name:
            return
        # save active profile to config
        set_active_profile_name(profile_name)
        self.status_label.config(text=f"Selected profile: {profile_name}")
        # display message once profile is selected
        messagebox.showinfo("Profile Selected", f'"{profile_name}" is now active.')

        self._refresh()
