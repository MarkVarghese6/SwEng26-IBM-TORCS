# Read/write settings and branding profiles

import json
import os

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(_BASE)
_SETTINGS_PATH = os.path.join(_BASE, "config", "settings.json")
_PROFILES_PATH = os.path.join(_BASE, "config", "default_profiles.json")

_DEFAULT_SETTINGS = {"torcs_root": "../torcs"}

_DEFAULT_PROFILES = {"active_profile": "", "profiles": []}


def _resolve_path(path_value):
    if not path_value:
        return ""

    expanded = os.path.expanduser(os.path.expandvars(path_value))
    if os.path.isabs(expanded):
        return os.path.normpath(expanded)

    return os.path.normpath(os.path.join(_BASE, expanded))


def _make_portable_path(path_value):
    if not path_value:
        return ""

    resolved = _resolve_path(path_value)
    try:
        relative_to_base = os.path.relpath(resolved, _BASE)
    except ValueError:
        return resolved

    try:
        in_repo = os.path.commonpath([resolved, _REPO_ROOT]) == _REPO_ROOT
    except ValueError:
        in_repo = False

    if in_repo:
        return relative_to_base.replace("\\", "/")

    return resolved


def load_settings():
    # Returns settings dict (creates defaults if file missing)
    if not os.path.exists(_SETTINGS_PATH):
        settings = dict(_DEFAULT_SETTINGS)
    else:
        with open(_SETTINGS_PATH, "r") as f:
            settings = dict(_DEFAULT_SETTINGS)
            settings.update(json.load(f))

    settings["torcs_root"] = _resolve_path(settings.get("torcs_root", ""))
    return settings


def save_settings(data):
    # Write settings to config/settings.json
    os.makedirs(os.path.dirname(_SETTINGS_PATH), exist_ok=True)
    payload = dict(data)
    payload["torcs_root"] = _make_portable_path(payload.get("torcs_root", ""))
    with open(_SETTINGS_PATH, "w") as f:
        json.dump(payload, f, indent=2)


def _load_profiles_document():
    if not os.path.exists(_PROFILES_PATH):
        return dict(_DEFAULT_PROFILES)

    with open(_PROFILES_PATH, "r") as f:
        raw = json.load(f)

    data = dict(_DEFAULT_PROFILES)
    data.update(raw)
    if not isinstance(data.get("profiles"), list):
        data["profiles"] = []
    if not isinstance(data.get("active_profile"), str):
        data["active_profile"] = ""
    return data


def load_profiles():
    # Load profiles list from default_profiles.json
    return _load_profiles_document().get("profiles", [])


def save_profiles(profiles_list):
    # Write profiles list to default_profiles.json
    os.makedirs(os.path.dirname(_PROFILES_PATH), exist_ok=True)
    data = _load_profiles_document()
    data["profiles"] = profiles_list

    profile_names = [
        str(p.get("name", "")).strip() for p in profiles_list if p.get("name")
    ]
    if data.get("active_profile") not in profile_names:
        data["active_profile"] = profile_names[0] if profile_names else ""

    with open(_PROFILES_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_active_profile_name():
    data = _load_profiles_document()
    profiles = data.get("profiles", [])
    active_name = data.get("active_profile", "").strip()

    if active_name and any(
        str(profile.get("name", "")).strip() == active_name for profile in profiles
    ):
        return active_name
    if profiles:
        return str(profiles[0].get("name", "")).strip()
    return ""


def load_active_profile():
    profiles = load_profiles()
    active_name = get_active_profile_name()

    if active_name:
        for profile in profiles:
            if str(profile.get("name", "")).strip() == active_name:
                return profile

    return profiles[0] if profiles else None


def save_profiles_document(data):
    os.makedirs(os.path.dirname(_PROFILES_PATH), exist_ok=True)
    with open(_PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def set_active_profile_name(name: str):
    data = _load_profiles_document()
    data["active_profile"] = name
    save_profiles_document(data)
