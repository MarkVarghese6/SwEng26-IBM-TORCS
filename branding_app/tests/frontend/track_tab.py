"""Tests for frontend.track_tab."""

import os

import frontend.track_tab as track_tab


def test_track_apply_requires_torcs_root(monkeypatch):
    errors = []
    tab = track_tab.TrackTab.__new__(track_tab.TrackTab)
    tab.torcs_root = ""
    monkeypatch.setattr(
        track_tab.messagebox,
        "showerror",
        lambda title, msg: errors.append((title, msg)),
    )

    track_tab.TrackTab._apply(tab)
    assert errors == [("Track", "Set TORCS root first in Settings")]


def test_track_apply_warns_when_no_track_assets(monkeypatch):
    errors = []
    tab = track_tab.TrackTab.__new__(track_tab.TrackTab)
    tab.torcs_root = "C:/torcs"
    monkeypatch.setattr(track_tab, "load_profiles", lambda: [{"name": "x"}])
    monkeypatch.setattr(track_tab, "load_active_profile", lambda: {"name": "x"})
    monkeypatch.setattr(track_tab, "get_active_profile_name", lambda: "x")
    monkeypatch.setattr(
        track_tab.messagebox,
        "showerror",
        lambda title, msg: errors.append((title, msg)),
    )

    track_tab.TrackTab._apply(tab)
    assert errors == [("Track", "No track textures configured in profile")]


def test_track_apply_copies_and_reports(monkeypatch):
    copied = []
    backed_up = []
    infos = []

    class _Now:
        @staticmethod
        def strftime(_fmt):
            return "20260327_130000"

    class _Datetime:
        @staticmethod
        def now():
            return _Now()

    tab = track_tab.TrackTab.__new__(track_tab.TrackTab)
    tab.torcs_root = "C:/torcs"

    monkeypatch.setattr(track_tab, "datetime", _Datetime)
    monkeypatch.setattr(
        track_tab,
        "load_profiles",
        lambda: [
            {
                "name": "x",
                "tracks": {
                    "tracks/e-track/icon.png": {
                        "file": "icon.png",
                        "auto_convert": False,
                    }
                },
            }
        ],
    )
    monkeypatch.setattr(
        track_tab,
        "load_active_profile",
        lambda: {
            "name": "x",
            "tracks": {
                "tracks/e-track/icon.png": {
                    "file": "icon.png",
                    "auto_convert": False,
                }
            },
        },
    )
    monkeypatch.setattr(track_tab, "get_active_profile_name", lambda: "x")
    monkeypatch.setattr(track_tab.os.path, "exists", lambda p: True)
    monkeypatch.setattr(
        track_tab,
        "backup_file",
        lambda src, root, snapshot_id, profile_name=None: backed_up.append(
            (src, root, snapshot_id, profile_name)
        ),
    )
    monkeypatch.setattr(
        track_tab,
        "copy_to_torcs",
        lambda src, root, rel, profile_name=None: copied.append(
            (src, root, rel, profile_name)
        ),
    )
    monkeypatch.setattr(
        track_tab.messagebox, "showinfo", lambda title, msg: infos.append((title, msg))
    )

    track_tab.TrackTab._apply(tab)

    assert copied == [
        (
            os.path.join(track_tab.UPLOADS_DIR, "icon.png"),
            "C:/torcs",
            "tracks/e-track/icon.png",
            "x",
        )
    ]
    assert len(backed_up) == 1
    assert backed_up[0][1] == "C:/torcs"
    assert backed_up[0][2] == "20260327_130000"
    assert backed_up[0][3] == "x"
    assert backed_up[0][0].replace("\\", "/").endswith("tracks/e-track/icon.png")
    assert infos == [("Track", "Applied 1 texture(s)")]
