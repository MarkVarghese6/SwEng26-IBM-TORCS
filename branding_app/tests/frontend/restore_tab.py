"""Tests for frontend.restore_tab."""

import os

import frontend.restore_tab as restore_tab


def test_restore_requires_torcs_root(monkeypatch):
    errors = []
    monkeypatch.setattr(restore_tab, "load_settings", lambda: {"torcs_root": ""})
    monkeypatch.setattr(
        restore_tab.messagebox,
        "showerror",
        lambda title, msg: errors.append((title, msg)),
    )

    restore_tab.RestoreTab._restore()
    assert errors == [("Restore", "Set TORCS root first in Settings.")]


def test_restore_warns_when_no_backups(monkeypatch):
    warns = []
    monkeypatch.setattr(
        restore_tab, "load_settings", lambda: {"torcs_root": "C:/torcs"}
    )
    monkeypatch.setattr(restore_tab, "get_active_profile_name", lambda: "baseline")
    monkeypatch.setattr(
        restore_tab,
        "get_profile_backup_root",
        lambda profile_name=None: "does-not-exist",
    )
    monkeypatch.setattr(
        restore_tab.messagebox,
        "showwarning",
        lambda title, msg: warns.append((title, msg)),
    )

    restore_tab.RestoreTab._restore()
    assert warns == [("Restore", "No backups are available.")]


def test_restore_uses_latest_snapshot(monkeypatch, tmp_path):
    infos = []
    restored = []

    backups = tmp_path / "backups"
    older = backups / "20260327_120000" / "data" / "img"
    newer = backups / "20260327_130000" / "data" / "img"
    older.mkdir(parents=True, exist_ok=True)
    newer.mkdir(parents=True, exist_ok=True)
    (older / "splash.png").write_text("old")
    (newer / "splash.png").write_text("new")

    monkeypatch.setattr(
        restore_tab, "load_settings", lambda: {"torcs_root": "C:/torcs"}
    )
    monkeypatch.setattr(restore_tab, "get_active_profile_name", lambda: "baseline")
    monkeypatch.setattr(
        restore_tab,
        "get_profile_backup_root",
        lambda profile_name=None: str(backups),
    )
    monkeypatch.setattr(
        restore_tab,
        "restore_backup",
        lambda snap, root, rel, profile_name=None: restored.append(
            (snap, root, rel, profile_name)
        ),
    )
    monkeypatch.setattr(
        restore_tab.messagebox,
        "showinfo",
        lambda title, msg: infos.append((title, msg)),
    )

    restore_tab.RestoreTab._restore()

    assert restored == [
        (
            "20260327_130000",
            "C:/torcs",
            os.path.join("data", "img", "splash.png"),
            "baseline",
        )
    ]
    assert infos == [("Restore", "Restored 1 file(s) from snapshot 20260327_130000.")]
