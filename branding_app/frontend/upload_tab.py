# Upload tab — pick and store banner/livery images
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from backend.config_service import (
    get_active_profile_name,
    load_profiles,
    load_settings,
    save_profiles,
)
from backend.file_service import (
    allowed_file,
    save_upload,
    list_uploaded_files,
    delete_upload,
    UPLOADS_DIR,
    validate_image_dimensions,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class UploadTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, padding=16)
        notebook.add(self.frame, text="Livery")

        # Set background colour for tab
        BG = "#fcffff"

        # Styles for the texts
        style = ttk.Style()
        style.configure("BG.TFrame", background=BG)
        style.configure("BG.TLabel", background=BG, foreground="#321e2d")
        style.configure("Path.TLabel", background=BG, foreground="#666666")

        self.frame.configure(style="BG.TFrame")
        self.slot_preview_labels = {}
        self.slot_preview_images = {"livery": None, "splash": None, "loading": None}
        self.slot_current_vars = {}

        # center content container
        inner = ttk.Frame(self.frame, style="BG.TFrame")
        inner.pack(pady=(48, 0))

        # Label for the title
        ttk.Label(
            inner,
            text="Livery Assets",
            font=("Segoe UI", 28, "bold"),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 8))

        # Label for the subtitle
        ttk.Label(
            inner,
            text="Choose car, splash, and loading assets for the active profile.",
            font=("Segoe UI", 15),
            style="BG.TLabel",
        ).pack(anchor="center", pady=(0, 10))

        self.active_profile_var = tk.StringVar(value="")
        ttk.Label(
            inner,
            textvariable=self.active_profile_var,
            font=("Segoe UI", 10),
            style="BG.TLabel",
        ).pack(anchor="w", pady=(4, 6))

        mapping_frame = tk.Frame(inner, bg=BG)
        mapping_frame.pack(fill="x", pady=(0, 8))

        self.car_var = tk.StringVar(value="")
        self.splash_var = tk.StringVar(value="")
        self.loading_var = tk.StringVar(value="")

        self._build_asset_row(mapping_frame, "Car Livery", self.car_var, "livery")
        self._build_asset_row(mapping_frame, "Splash Screen", self.splash_var, "splash")
        self._build_asset_row(
            mapping_frame, "Loading Screen", self.loading_var, "loading"
        )

        ttk.Button(
            inner, text="Save Asset Mapping", command=self._save_asset_mapping
        ).pack(anchor="w", pady=(4, 12))
        ttk.Button(
            inner, text="Check Compatibility", command=self._check_compatibility
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(
            inner,
            text="Asset Library",
            font=("Segoe UI", 11, "bold"),
            style="BG.TLabel",
        ).pack(anchor="w", pady=(0, 4))

        # Upload button
        file_btn_path = os.path.join(
            BASE_DIR, "assets", "images", "choose_file_btn.png"
        )
        self.upload_img = tk.PhotoImage(file=file_btn_path)

        tk.Button(
            inner,
            image=self.upload_img,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._choose,
        ).pack(anchor="center", pady=(0, 0))

        # Label to display the path of a selected file
        self._path_var = tk.StringVar(value="")
        tk.Label(
            inner,
            textvariable=self._path_var,
            font=("Segoe UI", 9),
            bg=BG,
            fg="#666666",
            wraplength=500,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(2, 4))

        # Display panel for uploaded files
        panel = tk.Frame(
            inner,
            width=500,
            height=150,
            bg="#dfe3ee",
        )
        panel.pack(pady=(8, 4))
        panel.pack_propagate(False)

        # Vertical scrollbar
        y_scrollbar = tk.Scrollbar(panel, orient="vertical")
        y_scrollbar.pack(side="right", fill="y", pady=10)

        # List box to display file names in the panel
        self.listbox = tk.Listbox(
            panel,
            borderwidth=0,
            bg="#dfe3ee",
            font=("Segoe UI", 10),
            yscrollcommand=y_scrollbar.set,
            activestyle="none",
            selectbackground="#4c72b0",
            selectforeground="white",
        )
        self.listbox.pack(fill="both", expand=True, padx=(10, 0), pady=10)
        y_scrollbar.config(command=self.listbox.yview)

        # Update path label whenever selection changes
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Buttons underneath the list box
        btn_row = tk.Frame(inner, bg=BG)
        btn_row.pack(pady=(6, 0))

        # Refresh button
        refresh_btn_path = os.path.join(BASE_DIR, "assets", "images", "refresh_btn.png")
        self.refresh_img = tk.PhotoImage(file=refresh_btn_path)

        tk.Button(
            btn_row,
            image=self.refresh_img,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._refresh,
        ).pack(side="left", padx=(0, 0))

        # Remove button
        remove_btn_path = os.path.join(BASE_DIR, "assets", "images", "remove_btn.png")
        self.remove_img = tk.PhotoImage(file=remove_btn_path)

        tk.Button(
            btn_row,
            image=self.remove_img,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self._remove,
        ).pack(side="right", padx=(50, 0))

        self._refresh()
        self._refresh_profile_mapping()
        self.frame.bind("<Map>", lambda e: self._refresh_profile_mapping())

    def _build_asset_row(self, parent, title, var, slot):
        row = tk.Frame(parent, bg=parent["bg"])
        row.pack(fill="x", pady=(2, 2))

        ttk.Label(row, text=title, style="BG.TLabel", width=14).pack(side="left")
        ttk.Entry(row, textvariable=var, width=42).pack(side="left", padx=(0, 8))
        ttk.Button(
            row, text="Choose", command=lambda s=slot: self._choose_slot(s)
        ).pack(side="left")
        preview = ttk.Label(row, text="(no preview)", width=18, anchor="center")
        preview.pack(side="left", padx=(8, 0))
        self.slot_preview_labels[slot] = preview

        current_var = tk.StringVar(value="Current: (unknown)")
        ttk.Label(
            row,
            textvariable=current_var,
            style="BG.TLabel",
            foreground="#666666",
        ).pack(side="left", padx=(8, 0))
        self.slot_current_vars[slot] = current_var

    def _choose_slot(self, slot):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All", "*.*")],
        )
        if not path:
            return

        name = os.path.basename(path)
        if not allowed_file(name):
            messagebox.showerror("Livery", f"Unsupported file type: {name}")
            return

        save_upload(path)
        if slot == "livery":
            self.car_var.set(name)
        elif slot == "splash":
            self.splash_var.set(name)
        else:
            self.loading_var.set(name)

        self._set_slot_preview(slot, name)
        self._refresh()

    def _refresh_profile_mapping(self):
        profiles = load_profiles()
        active_name = get_active_profile_name()
        torcs_root = load_settings().get("torcs_root", "")
        if not profiles:
            self.active_profile_var.set("Active profile: (none)")
            self.car_var.set("")
            self.splash_var.set("")
            self.loading_var.set("")
            self.slot_current_vars["livery"].set("Current: (none)")
            self.slot_current_vars["splash"].set("Current: (none)")
            self.slot_current_vars["loading"].set("Current: (none)")
            return

        active_profile = profiles[0]
        for profile in profiles:
            if str(profile.get("name", "")).strip() == active_name:
                active_profile = profile
                break

        self.active_profile_var.set(f"Active profile: {active_profile.get('name', '')}")
        self.car_var.set((active_profile.get("livery", {}).get("texture_file") or ""))
        self.splash_var.set(
            (
                active_profile.get("banners", {}).get("splash_screen", {}).get("file")
                or ""
            )
        )
        self.loading_var.set(
            (
                active_profile.get("banners", {}).get("loading_screen", {}).get("file")
                or ""
            )
        )

        livery_target = active_profile.get("livery", {}).get("target_path", "")
        splash_target = (
            active_profile.get("banners", {})
            .get("splash_screen", {})
            .get("target_path", "")
        )
        loading_target = (
            active_profile.get("banners", {})
            .get("loading_screen", {})
            .get("target_path", "")
        )

        self.slot_current_vars["livery"].set(
            f"Current: {os.path.basename(livery_target) if livery_target else '(none)'}"
        )
        self.slot_current_vars["splash"].set(
            f"Current: {os.path.basename(splash_target) if splash_target else '(none)'}"
        )
        self.slot_current_vars["loading"].set(
            f"Current: {os.path.basename(loading_target) if loading_target else '(none)'}"
        )

        livery_fallback = self._resolve_target_preview_path(torcs_root, livery_target)
        splash_fallback = self._resolve_target_preview_path(torcs_root, splash_target)
        loading_fallback = self._resolve_target_preview_path(torcs_root, loading_target)

        self._set_slot_preview(
            "livery", self.car_var.get(), fallback_path=livery_fallback
        )
        self._set_slot_preview(
            "splash", self.splash_var.get(), fallback_path=splash_fallback
        )
        self._set_slot_preview(
            "loading", self.loading_var.get(), fallback_path=loading_fallback
        )

    @staticmethod
    def _resolve_target_preview_path(torcs_root, target_path):
        if not torcs_root or not target_path:
            return None
        candidate = os.path.join(torcs_root, target_path.replace("/", os.sep))
        if os.path.exists(candidate):
            return candidate
        return None

    def _save_asset_mapping(self):
        profiles = load_profiles()
        if not profiles:
            messagebox.showerror("Livery", "No profiles found.")
            return

        checks = [
            ("Car Livery", self.car_var.get().strip()),
            ("Splash Screen", self.splash_var.get().strip()),
            ("Loading Screen", self.loading_var.get().strip()),
        ]
        missing = []
        for label, filename in checks:
            if filename and not os.path.exists(os.path.join(UPLOADS_DIR, filename)):
                missing.append(f"{label}: {filename}")
        if missing:
            messagebox.showerror(
                "Livery",
                "These files are not in uploads/:\n" + "\n".join(missing),
            )
            return

        active_name = get_active_profile_name()
        active_idx = 0
        for idx, profile in enumerate(profiles):
            if str(profile.get("name", "")).strip() == active_name:
                active_idx = idx
                break

        profile = profiles[active_idx]
        profile.setdefault("livery", {})
        profile.setdefault("banners", {})
        profile["banners"].setdefault("splash_screen", {})
        profile["banners"].setdefault("loading_screen", {})

        profile["livery"]["texture_file"] = self.car_var.get().strip() or None
        profile["banners"]["splash_screen"]["file"] = (
            self.splash_var.get().strip() or None
        )
        profile["banners"]["loading_screen"]["file"] = (
            self.loading_var.get().strip() or None
        )

        profiles[active_idx] = profile
        save_profiles(profiles)
        messagebox.showinfo("Livery", "Asset mapping saved for active profile.")

    def _set_slot_preview(self, slot, filename, fallback_path=None):
        label = self.slot_preview_labels.get(slot)
        if label is None:
            return

        img_path = None
        if not filename:
            img_path = fallback_path
        else:
            upload_path = os.path.join(UPLOADS_DIR, filename)
            if os.path.exists(upload_path):
                img_path = upload_path
            else:
                img_path = fallback_path

        if not img_path:
            self.slot_preview_images[slot] = None
            label.configure(image="", text="(no preview)")
            return

        try:
            with Image.open(img_path) as img:
                preview = img.copy()
            preview.thumbnail((110, 60), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(preview)
            self.slot_preview_images[slot] = photo
            label.configure(image=photo, text="")
        except Exception:
            self.slot_preview_images[slot] = None
            label.configure(image="", text="(preview error)")

    def _check_compatibility(self):
        profiles = load_profiles()
        if not profiles:
            messagebox.showerror("Livery", "No profiles found.")
            return

        active_name = get_active_profile_name()
        active_profile = profiles[0]
        for profile in profiles:
            if str(profile.get("name", "")).strip() == active_name:
                active_profile = profile
                break

        checks = []
        livery = self.car_var.get().strip()
        splash = self.splash_var.get().strip()
        loading = self.loading_var.get().strip()

        if livery:
            checks.append(("Car Livery", livery, None, None))

        splash_cfg = active_profile.get("banners", {}).get("splash_screen", {})
        if splash:
            checks.append(
                (
                    "Splash Screen",
                    splash,
                    splash_cfg.get("width"),
                    splash_cfg.get("height"),
                )
            )

        loading_cfg = active_profile.get("banners", {}).get("loading_screen", {})
        if loading:
            checks.append(
                (
                    "Loading Screen",
                    loading,
                    loading_cfg.get("width"),
                    loading_cfg.get("height"),
                )
            )

        if not checks:
            messagebox.showwarning("Livery", "No files selected to check.")
            return

        results = []
        failed = False
        for title, filename, exp_w, exp_h in checks:
            path = os.path.join(UPLOADS_DIR, filename)
            ok, msg = validate_image_dimensions(path, exp_w, exp_h)
            if ok:
                results.append(f"{title}: OK")
            else:
                failed = True
                results.append(f"{title}: {msg}")

        if failed:
            messagebox.showerror(
                "Livery", "Compatibility check failed:\n" + "\n".join(results)
            )
        else:
            messagebox.showinfo(
                "Livery", "Compatibility check passed:\n" + "\n".join(results)
            )

    # Method to display path of file selected
    def _on_select(self, event=None):
        selection = self.listbox.curselection()
        # If a file is selected display its path
        if selection:
            filename = self.listbox.get(selection[0])
            self._path_var.set(os.path.join(UPLOADS_DIR, filename))
        else:
            # If a file is not selected, leave the path display box empty
            self._path_var.set("")

    # Method to choose file for upload
    def _choose(self):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All", "*.*")],
        )
        if not paths:
            return

        # Store the correct and incorrect image files
        saved = []
        errors = []

        # Store file in the errors array  if the file type is not allowed
        for path in paths:
            if not allowed_file(os.path.basename(path)):
                errors.append(os.path.basename(path))
                continue
            # Store file in the saved array if the file type is allowed
            dest = save_upload(path)
            saved.append(dest)

        # Display message showing how many files were successfully uploaded
        if saved:
            messagebox.showinfo("Upload", f"Saved {len(saved)} file(s).")
        # Display error message and show which files are unsupported
        if errors:
            messagebox.showerror(
                "Upload",
                f"Skipped {len(errors)} unsupported file(s):\n" + "\n".join(errors),
            )
        self._refresh()

    # Method to refresh the list displaying the uploaded files
    def _refresh(self):
        self.listbox.delete(0, "end")
        self._path_var.set("")

        for f in list_uploaded_files():
            name = f.get("name", "") if isinstance(f, dict) else str(f)
            self.listbox.insert("end", name)

    # Method to remove the list displaying the uploaded files
    def _remove(self):
        selection = self.listbox.curselection()
        # warning message if a file has not been selected
        if not selection:
            messagebox.showwarning("Remove File", "No file selected.")
            return

        filename = self.listbox.get(selection[0])
        if delete_upload(filename):
            messagebox.showinfo("Remove", f"Deleted: {filename}")
        else:
            # Error message if the file could not be deleted
            messagebox.showerror("Remove", "File could not be deleted.")
        self._refresh()
