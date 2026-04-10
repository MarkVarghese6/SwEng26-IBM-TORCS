"""Tests for backend.config_service."""

import json
import os

import backend.config_service as config_service


def test_load_settings_returns_default_when_missing(tmp_path, monkeypatch):
    settings_path = tmp_path / "config" / "settings.json"
    monkeypatch.setattr(config_service, "_SETTINGS_PATH", str(settings_path))
    monkeypatch.setattr(config_service, "_BASE", str(tmp_path))

    assert config_service.load_settings() == {
        "torcs_root": os.path.normpath(str(tmp_path.parent / "torcs"))
    }


def test_save_then_load_settings_round_trip(tmp_path, monkeypatch):
    settings_path = tmp_path / "config" / "settings.json"
    monkeypatch.setattr(config_service, "_SETTINGS_PATH", str(settings_path))
    monkeypatch.setattr(config_service, "_BASE", str(tmp_path))
    monkeypatch.setattr(config_service, "_REPO_ROOT", str(tmp_path.parent))

    payload = {"torcs_root": str(tmp_path.parent / "torcs"), "extra": True}
    config_service.save_settings(payload)

    with open(settings_path, "r") as fh:
        on_disk = json.load(fh)
    assert on_disk == {"torcs_root": "../torcs", "extra": True}
    assert config_service.load_settings() == payload


def test_load_settings_resolves_relative_torcs_path(tmp_path, monkeypatch):
    settings_path = tmp_path / "config" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as fh:
        json.dump({"torcs_root": "../torcs"}, fh)

    monkeypatch.setattr(config_service, "_SETTINGS_PATH", str(settings_path))
    monkeypatch.setattr(config_service, "_BASE", str(tmp_path))

    assert config_service.load_settings() == {
        "torcs_root": os.path.normpath(str(tmp_path.parent / "torcs"))
    }


def test_load_profiles_returns_empty_when_missing(tmp_path, monkeypatch):
    profiles_path = tmp_path / "config" / "default_profiles.json"
    monkeypatch.setattr(config_service, "_PROFILES_PATH", str(profiles_path))

    assert config_service.load_profiles() == []


def test_load_profiles_returns_profiles_key(tmp_path, monkeypatch):
    profiles_path = tmp_path / "config" / "default_profiles.json"
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profiles_path, "w") as fh:
        json.dump({"profiles": [{"name": "baseline"}, {"name": "alt"}]}, fh)

    monkeypatch.setattr(config_service, "_PROFILES_PATH", str(profiles_path))
    assert config_service.load_profiles() == [{"name": "baseline"}, {"name": "alt"}]


def test_save_profiles_then_load_profiles_round_trip(tmp_path, monkeypatch):
    profiles_path = tmp_path / "config" / "default_profiles.json"
    monkeypatch.setattr(config_service, "_PROFILES_PATH", str(profiles_path))

    profiles = [{"name": "baseline"}, {"name": "alt"}]
    config_service.save_profiles(profiles)

    with open(profiles_path, "r") as fh:
        on_disk = json.load(fh)

    assert on_disk == {"active_profile": "baseline", "profiles": profiles}
    assert config_service.load_profiles() == profiles


def test_get_active_profile_name_prefers_configured_profile(tmp_path, monkeypatch):
    profiles_path = tmp_path / "config" / "default_profiles.json"
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profiles_path, "w") as fh:
        json.dump(
            {
                "active_profile": "alt",
                "profiles": [{"name": "baseline"}, {"name": "alt"}],
            },
            fh,
        )

    monkeypatch.setattr(config_service, "_PROFILES_PATH", str(profiles_path))

    assert config_service.get_active_profile_name() == "alt"
    assert config_service.load_active_profile() == {"name": "alt"}
