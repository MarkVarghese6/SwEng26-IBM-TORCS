# Track tab - Modify TORCS race tracks

import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

from backend.config_service import (
    get_active_profile_name,
    load_active_profile,
    load_profiles,
    load_settings,
    save_profiles,
)
from backend.file_service import UPLOADS_DIR, backup_file, copy_to_torcs
from backend.track_service import (
    list_track_categories,
    list_tracks_in_category,
    list_textures_in_track,
    read_texture_properties,
    validate_image_compatibility,
    auto_convert_image,
)


class TrackTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Track")

        # Scrollable content container so large previews never hide controls below.
        self.canvas = tk.Canvas(self.frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content = ttk.Frame(self.canvas, padding=16)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.content.bind(
            "<Enter>",
            lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel),
        )
        self.content.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.torcs_root = ""
        self.selected_texture_path = None  # Full path to selected target texture
        self.selected_upload_path = None  # Full path to selected upload file
        self.preview_img = None

        self._build_ui()
        # Re-check settings whenever the tab is shown.
        self.frame.bind("<Map>", lambda e: self._refresh_torcs_root())
        self._refresh_torcs_root()

    def _build_ui(self):
        """Build the track tab UI."""
        parent = self.content

        # Header
        ttk.Label(
            parent, text="Track Texture Editor", font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 12))
        ttk.Label(
            parent,
            text="Select track → Select texture → Upload file → Apply",
            foreground="gray",
        ).pack(anchor="w", pady=(0, 16))
        self.active_profile_var = tk.StringVar(value="Active profile: (none)")
        ttk.Label(
            parent, textvariable=self.active_profile_var, foreground="#004aad"
        ).pack(anchor="w", pady=(0, 10))

        # --- Track Selection ---
        ttk.Label(
            parent, text="Step 1: Select Track", font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        self.track_status_var = tk.StringVar(value="")
        ttk.Label(parent, textvariable=self.track_status_var, foreground="gray").pack(
            anchor="w", pady=(0, 8)
        )

        track_frame = ttk.Frame(parent)
        track_frame.pack(anchor="w", fill="x", pady=(0, 16))

        ttk.Label(track_frame, text="Category:").pack(side="left", padx=(0, 8))
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(
            track_frame, textvariable=self.cat_var, state="readonly", width=20
        )
        self.cat_combo.pack(side="left", padx=(0, 16))
        self.cat_combo.bind(
            "<<ComboboxSelected>>", lambda e: self._on_category_changed()
        )

        ttk.Label(track_frame, text="Track:").pack(side="left", padx=(0, 8))
        self.track_var = tk.StringVar()
        self.track_combo = ttk.Combobox(
            track_frame, textvariable=self.track_var, state="readonly", width=25
        )
        self.track_combo.pack(side="left", padx=(0, 16))
        self.track_combo.bind(
            "<<ComboboxSelected>>", lambda e: self._on_track_changed()
        )

        # --- Texture Selection ---
        ttk.Label(
            parent, text="Step 2: Select Target Texture", font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        texture_frame = ttk.Frame(parent)
        texture_frame.pack(anchor="w", fill="both", expand=False, pady=(0, 16))

        # Texture listbox with scrollbar
        listbox_frame = ttk.Frame(texture_frame)
        listbox_frame.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(texture_frame)
        scrollbar.pack(side="right", fill="y")

        self.texture_listbox = ttk.Treeview(
            listbox_frame,
            height=6,
            columns=("name"),
            show="headings",
            yscrollcommand=scrollbar.set,
        )
        self.texture_listbox.column("name", width=500, anchor="w")
        self.texture_listbox.heading("name", text="Texture Name", anchor="w")
        self.texture_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.texture_listbox.yview)

        self.texture_listbox.bind(
            "<<TreeviewSelect>>", lambda e: self._on_texture_selected()
        )

        # --- Selection Preview + Details ---
        ttk.Label(
            parent, text="Selection Preview & Details", font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        details_frame = ttk.Frame(parent)
        details_frame.pack(anchor="w", fill="x", pady=(0, 16))

        self.preview_label = ttk.Label(
            details_frame, text="(No texture selected)", anchor="w", width=52
        )
        self.preview_label.pack(side="left", padx=(0, 16), pady=(0, 0), anchor="n")

        props_panel = ttk.Frame(details_frame)
        props_panel.pack(side="left", fill="x", expand=True, anchor="n")

        self.props_var = tk.StringVar(value="(No texture selected)")
        ttk.Label(
            props_panel,
            textvariable=self.props_var,
            foreground="gray",
            font=("Courier", 10),
            justify="left",
            wraplength=360,
        ).pack(anchor="w")

        # --- Upload File Selection ---
        ttk.Label(
            parent, text="Step 3: Select File to Upload", font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        upload_frame = ttk.Frame(parent)
        upload_frame.pack(anchor="w", fill="x", pady=(0, 8))

        self.upload_var = tk.StringVar(value="(No upload selected)")
        ttk.Label(upload_frame, textvariable=self.upload_var, width=50).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(upload_frame, text="Browse Files", command=self._browse_upload).pack(
            side="left"
        )

        # --- Upload Properties & Auto-Convert ---
        ttk.Label(parent, text="File Properties", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", pady=(0, 8)
        )

        self.upload_props_var = tk.StringVar(value="(No upload selected)")
        ttk.Label(
            parent,
            textvariable=self.upload_props_var,
            foreground="gray",
            font=("Courier", 9),
        ).pack(anchor="w", pady=(0, 8))

        # --- Validation Messages ---
        self.validation_var = tk.StringVar(value="")
        self.validation_label = ttk.Label(
            parent,
            textvariable=self.validation_var,
            foreground="orange",
            wraplength=760,
        )
        self.validation_label.pack(anchor="w", pady=(0, 12), fill="x")

        # --- Auto-Convert Option ---
        self.auto_convert_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            parent,
            text="Auto-convert upload to match target size/format",
            variable=self.auto_convert_var,
        ).pack(anchor="w", pady=(0, 12))

        # --- Save Profile & Apply ---
        action_frame = ttk.Frame(parent)
        action_frame.pack(anchor="w", fill="x", pady=(0, 12))

        ttk.Button(
            action_frame, text="Save to Profile", command=self._save_to_profile
        ).pack(side="left", padx=(0, 8))
        ttk.Button(action_frame, text="Apply Now", command=self._apply).pack(
            side="left"
        )

    def _on_content_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _refresh_torcs_root(self):
        """Reload TORCS root and refresh track list."""
        settings = load_settings()
        configured_root = settings.get("torcs_root", "").strip()
        self.torcs_root = self._resolve_torcs_root(configured_root)
        self.active_profile_var.set(
            f"Active profile: {get_active_profile_name() or '(none)'}"
        )

        if not self.torcs_root or not os.path.isdir(self.torcs_root):
            self.cat_combo.config(state="disabled")
            self.cat_combo["values"] = []
            self.cat_combo.set("")
            self.track_combo["values"] = []
            self.track_combo.set("")
            self.track_status_var.set(
                "Set a valid TORCS root in Settings (must contain tracks/, cars/, data/)"
            )
            return

        self.cat_combo.config(state="readonly")
        categories = list_track_categories(self.torcs_root)
        self.cat_combo["values"] = categories
        if not categories:
            self.track_status_var.set(
                f"No track categories found under: {self.torcs_root}"
            )
            self.track_combo["values"] = []
            self.track_combo.set("")
            self._clear_texture_list()
            return

        self.track_status_var.set(f"TORCS root: {self.torcs_root}")
        if categories:
            self.cat_combo.current(0)
            self._on_category_changed()

    def _resolve_torcs_root(self, configured_root):
        """Accept either TORCS root directly or a parent folder containing /torcs."""
        if not configured_root:
            return ""

        configured_root = os.path.normpath(configured_root)
        if self._looks_like_torcs_root(configured_root):
            return configured_root

        candidate = os.path.join(configured_root, "torcs")
        if self._looks_like_torcs_root(candidate):
            return candidate

        return ""

    def _looks_like_torcs_root(self, path):
        return (
            os.path.isdir(path)
            and os.path.isdir(os.path.join(path, "tracks"))
            and os.path.isdir(os.path.join(path, "cars"))
            and os.path.isdir(os.path.join(path, "data"))
        )

    def _on_category_changed(self):
        """Update track list when category changes."""
        cat = self.cat_var.get()
        if not cat:
            self.track_combo["values"] = []
            return

        tracks = list_tracks_in_category(self.torcs_root, cat)
        self.track_combo["values"] = tracks
        self._clear_texture_list()
        if tracks:
            self.track_combo.set(tracks[0])
            self._on_track_changed()
        else:
            self.track_combo.set("")

    def _on_track_changed(self):
        """Update texture list when track changes."""
        cat = self.cat_var.get()
        track = self.track_var.get()

        if not cat or not track:
            self._clear_texture_list()
            return

        textures = list_textures_in_track(self.torcs_root, cat, track)
        self.texture_listbox.delete(*self.texture_listbox.get_children())

        for tex in textures:
            self.texture_listbox.insert("", "end", values=(tex["filename"]))

    def _clear_texture_list(self):
        """Clear texture list and properties."""
        self.texture_listbox.delete(*self.texture_listbox.get_children())
        self.selected_texture_path = None
        self.props_var.set("(No texture selected)")
        self._update_target_preview(None)
        self._update_validation()

    def _on_texture_selected(self):
        """Handle texture selection from list."""
        selection = self.texture_listbox.selection()
        if not selection:
            self.selected_texture_path = None
            self.props_var.set("(No texture selected)")
            self._update_validation()
            return

        item = selection[0]
        self.selected_texture_path = os.path.join(
            self.torcs_root,
            "tracks",
            self.cat_var.get(),
            self.track_var.get(),
            self.texture_listbox.item(item, "values")[0],
        )

        props = read_texture_properties(self.selected_texture_path)
        if props.get("error"):
            self.props_var.set(f"Error: {props['error']}")
            self._update_target_preview(None)
        else:
            props_str = (
                f"Size: {props['width']}×{props['height']}, "
                f"Format: {props['format']}, "
                f"Alpha: {'Yes' if props['has_alpha'] else 'No'}"
            )
            self.props_var.set(props_str)
            self._update_target_preview(self.selected_texture_path)

        self._update_validation()

    def _browse_upload(self):
        """Open file browser to select upload file."""
        path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tga"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )

        if path:
            self.selected_upload_path = path
            self.upload_var.set(os.path.basename(path))

            props = read_texture_properties(path)
            if props.get("error"):
                self.upload_props_var.set(f"Error: {props['error']}")
            else:
                props_str = (
                    f"Size: {props['width']}×{props['height']}, "
                    f"Format: {props['format']}, "
                    f"Alpha: {'Yes' if props['has_alpha'] else 'No'}"
                )
                self.upload_props_var.set(props_str)

            self._update_validation()

    def _update_validation(self):
        """Check compatibility between selected upload and target textures."""
        if not self.selected_texture_path or not self.selected_upload_path:
            self.validation_var.set("")
            self.validation_label.config(foreground="orange")
            return

        result = validate_image_compatibility(
            self.selected_upload_path, self.selected_texture_path
        )

        if result["compatible"]:
            self.validation_var.set("✓ Compatible - Ready to apply")
            self.validation_label.config(foreground="green")
        else:
            issues_str = "\n".join(
                f"• {issue_type}: {msg}" for issue_type, msg in result["issues"]
            )
            if self.auto_convert_var.get():
                self.validation_var.set(
                    f"Issues found (will auto-convert):\n{issues_str}"
                )
                self.validation_label.config(foreground="blue")
            else:
                self.validation_var.set(
                    f"Issues found:\n{issues_str}\nEnable 'Auto-convert' to proceed"
                )
                self.validation_label.config(foreground="orange")

    def _save_to_profile(self):
        """Save selected texture mapping to profile."""
        if not self.selected_texture_path:
            messagebox.showerror("Track", "Select a target texture first")
            return

        if not self.selected_upload_path:
            messagebox.showerror("Track", "Select an upload file first")
            return

        profiles = load_profiles()
        if not profiles:
            messagebox.showerror("Track", "No profile found")
            return

        active_profile_name = get_active_profile_name()
        profile = None
        if active_profile_name:
            for candidate in profiles:
                if str(candidate.get("name", "")).strip() == active_profile_name:
                    profile = candidate
                    break
        if profile is None:
            profile = profiles[0]
            active_profile_name = str(profile.get("name", "")).strip()

        # Read target properties
        target_props = read_texture_properties(self.selected_texture_path)
        if target_props.get("error"):
            messagebox.showerror(
                "Track", f"Cannot read target: {target_props['error']}"
            )
            return

        # Create or update tracks section in profile
        if "tracks" not in profile:
            profile["tracks"] = {}

        # Use relative path from torcs_root as key
        rel_path = os.path.relpath(self.selected_texture_path, self.torcs_root)
        rel_path_normalized = rel_path.replace("\\", "/")

        # Save entry with upload filename (will be resolved from uploads/ dir)
        upload_filename = os.path.basename(self.selected_upload_path)

        profile["tracks"][rel_path_normalized] = {
            "file": upload_filename,
            "target_path": rel_path_normalized,
            "width": target_props["width"],
            "height": target_props["height"],
            "format": target_props["format"],
            "has_alpha": target_props["has_alpha"],
            "auto_convert": self.auto_convert_var.get(),
        }

        save_profiles(profiles)
        messagebox.showinfo(
            "Track",
            f"Saved: {os.path.basename(self.selected_texture_path)}\n"
            f"Size: {target_props['width']}×{target_props['height']}\n"
            f"Upload: {upload_filename}\n"
            f"Profile: {active_profile_name or profile.get('name', '(unnamed)')}",
        )

    def _apply(self):
        """Apply track textures from profile."""
        if not self.torcs_root:
            messagebox.showerror("Track", "Set TORCS root first in Settings")
            return

        profiles = load_profiles()
        if not profiles:
            messagebox.showerror("Track", "No profile found")
            return

        profile = load_active_profile()
        profile_name = get_active_profile_name()
        if not profile:
            messagebox.showerror("Track", "No active profile found")
            return
        if "tracks" not in profile or not profile["tracks"]:
            messagebox.showerror("Track", "No track textures configured in profile")
            return

        snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        applied = 0
        errors = []

        for rel_path, config in profile["tracks"].items():
            try:
                target_path = os.path.join(self.torcs_root, rel_path.replace("/", "\\"))

                if not os.path.exists(target_path):
                    errors.append(f"{rel_path}: target not found")
                    continue

                # Resolve source file
                upload_file = config.get("file")
                source_path = None

                if upload_file:
                    candidate = os.path.join(UPLOADS_DIR, upload_file)
                    if os.path.exists(candidate):
                        source_path = candidate

                if not source_path:
                    errors.append(f"{rel_path}: upload '{upload_file}' not found")
                    continue

                # Auto-convert if enabled
                final_source = source_path
                if config.get("auto_convert"):
                    converted_path = os.path.join(
                        UPLOADS_DIR,
                        "_converted",
                        snapshot_id,
                        os.path.basename(source_path),
                    )
                    result = auto_convert_image(
                        source_path, target_path, converted_path
                    )
                    if not result["success"]:
                        errors.append(
                            f"{rel_path}: auto-convert failed: {result['error']}"
                        )
                        continue
                    final_source = result["output_path"]

                # Backup and apply
                backup_file(
                    target_path,
                    self.torcs_root,
                    snapshot_id,
                    profile_name=profile_name,
                )
                copy_to_torcs(
                    final_source,
                    self.torcs_root,
                    rel_path,
                    profile_name=profile_name,
                )
                applied += 1

            except Exception as e:
                errors.append(f"{rel_path}: {str(e)}")

        msg = f"Applied {applied} texture(s)"
        if errors:
            msg += f"\n\n{len(errors)} error(s):\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... and {len(errors) - 5} more"

        messagebox.showinfo("Track", msg)

    def _update_target_preview(self, image_path):
        """Render a scaled preview of the selected target texture."""
        if not image_path:
            self.preview_img = None
            self.preview_label.configure(image="", text="(No texture selected)")
            return

        try:
            with Image.open(image_path) as img:
                preview = img.copy()

            # Keep preview compact so the rest of the controls remain visible.
            preview.thumbnail((360, 180), Image.Resampling.LANCZOS)
            self.preview_img = ImageTk.PhotoImage(preview)
            self.preview_label.configure(image=self.preview_img, text="")
        except Exception as e:
            self.preview_img = None
            self.preview_label.configure(image="", text=f"Preview unavailable: {e}")
