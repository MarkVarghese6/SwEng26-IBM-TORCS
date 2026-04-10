"""Tests for frontend.apply_tab."""

import os

import frontend.apply_tab as apply_tab


def test_apply_rejects_when_torcs_root_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(apply_tab, "load_settings", lambda: {"torcs_root": "  "})
    monkeypatch.setattr(
        apply_tab.messagebox, "showerror", lambda title, msg: calls.append((title, msg))
    )

    apply_tab.ApplyTab._apply()

    assert calls == [("Apply", "Set TORCS root first in Settings.")]


def test_apply_rejects_when_profile_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(apply_tab, "load_settings", lambda: {"torcs_root": "C:/torcs"})
    monkeypatch.setattr(apply_tab, "load_active_profile", lambda: None)
    monkeypatch.setattr(
        apply_tab.messagebox, "showerror", lambda title, msg: calls.append((title, msg))
    )

    apply_tab.ApplyTab._apply()

    assert calls == [("Apply", "No branding profile found in config.")]


def test_apply_warns_when_no_resolved_assets(monkeypatch):
    warns = []
    monkeypatch.setattr(apply_tab, "load_settings", lambda: {"torcs_root": "C:/torcs"})
    monkeypatch.setattr(apply_tab, "load_active_profile", lambda: {"name": "x"})
    monkeypatch.setattr(apply_tab, "get_active_profile_name", lambda: "x")
    monkeypatch.setattr(
        apply_tab, "build_apply_plan", lambda profile, uploads: ([], [])
    )
    monkeypatch.setattr(
        apply_tab.messagebox,
        "showwarning",
        lambda title, msg: warns.append((title, msg)),
    )

    apply_tab.ApplyTab._apply()

    assert warns == [
        (
            "Apply",
            "No assets are ready to apply. Upload files or set profile file paths.",
        )
    ]


def test_apply_rejects_when_validation_fails(monkeypatch):
    errors = []
    monkeypatch.setattr(apply_tab, "load_settings", lambda: {"torcs_root": "C:/torcs"})
    monkeypatch.setattr(apply_tab, "load_active_profile", lambda: {"name": "x"})
    monkeypatch.setattr(apply_tab, "get_active_profile_name", lambda: "x")
    monkeypatch.setattr(
        apply_tab,
        "build_apply_plan",
        lambda profile, uploads: (
            [
                {
                    "label": "banners.splash",
                    "source_path": "uploads/splash.png",
                    "target_path": "data/img/splash.png",
                    "width": 100,
                    "height": 100,
                }
            ],
            [],
        ),
    )
    monkeypatch.setattr(
        apply_tab,
        "validate_image_dimensions",
        lambda path, w, h: (False, "Incorrect proportions"),
    )
    monkeypatch.setattr(
        apply_tab.messagebox,
        "showerror",
        lambda title, msg: errors.append((title, msg)),
    )

    apply_tab.ApplyTab._apply()

    assert len(errors) == 1
    assert errors[0][0] == "Apply"
    assert "Validation failed" in errors[0][1]


def test_apply_copies_and_reports_success(monkeypatch):
    copied = []
    backed_up = []
    infos = []

    class _Now:
        @staticmethod
        def strftime(_fmt):
            return "20260327_120000"

    class _Datetime:
        @staticmethod
        def now():
            return _Now()

    monkeypatch.setattr(apply_tab, "datetime", _Datetime)
    monkeypatch.setattr(apply_tab, "load_settings", lambda: {"torcs_root": "C:/torcs"})
    monkeypatch.setattr(apply_tab, "load_active_profile", lambda: {"name": "x"})
    monkeypatch.setattr(apply_tab, "get_active_profile_name", lambda: "x")
    monkeypatch.setattr(
        apply_tab,
        "build_apply_plan",
        lambda profile, uploads: (
            [
                {
                    "label": "banners.splash",
                    "source_path": os.path.join("uploads", "splash.png"),
                    "target_path": "data/img/splash.png",
                    "width": None,
                    "height": None,
                }
            ],
            [{"label": "tracks.icon", "target_path": "tracks/test/icon.png"}],
        ),
    )
    monkeypatch.setattr(
        apply_tab,
        "validate_image_dimensions",
        lambda path, w, h: (True, ""),
    )
    monkeypatch.setattr(apply_tab.os.path, "exists", lambda p: p.endswith("splash.png"))
    monkeypatch.setattr(
        apply_tab,
        "backup_file",
        lambda src, root, snapshot_id, profile_name=None: backed_up.append(
            (src, root, snapshot_id, profile_name)
        ),
    )
    monkeypatch.setattr(
        apply_tab,
        "copy_to_torcs",
        lambda upload_path, torcs_root, target_rel, profile_name=None: copied.append(
            (upload_path, torcs_root, target_rel, profile_name)
        ),
    )
    monkeypatch.setattr(
        apply_tab.messagebox, "showinfo", lambda title, msg: infos.append((title, msg))
    )

    apply_tab.ApplyTab._apply()

    assert copied == [
        (os.path.join("uploads", "splash.png"), "C:/torcs", "data/img/splash.png", "x")
    ]
    assert backed_up == [
        (
            os.path.join("C:/torcs", "data/img/splash.png"),
            "C:/torcs",
            "20260327_120000",
            "x",
        )
    ]
    assert infos == [
        ("Apply", "Applied 1 file(s) (1 unresolved). Snapshot: 20260327_120000")
    ]
