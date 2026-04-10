"""Tests for frontend.settings_tab."""

import frontend.settings_tab as settings_tab


class DummyVar:
    def __init__(self, value=""):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


def test_validate_torcs_folder_true(tmp_path):
    root = tmp_path / "torcs"
    for name in ("cars", "data", "tracks"):
        (root / name).mkdir(parents=True, exist_ok=True)

    tab = settings_tab.SettingsTab.__new__(settings_tab.SettingsTab)
    tab.path_var = DummyVar(str(root))

    assert settings_tab.SettingsTab.validate_torcs_folder(tab) is True


def test_validate_torcs_folder_false_when_missing_subfolder(tmp_path):
    root = tmp_path / "torcs"
    (root / "cars").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)

    tab = settings_tab.SettingsTab.__new__(settings_tab.SettingsTab)
    tab.path_var = DummyVar(str(root))

    assert settings_tab.SettingsTab.validate_torcs_folder(tab) is False


def test_browse_updates_path(monkeypatch):
    tab = settings_tab.SettingsTab.__new__(settings_tab.SettingsTab)
    tab.path_var = DummyVar("")
    monkeypatch.setattr(
        settings_tab.filedialog,
        "askdirectory",
        lambda title: "C:/TORCS",
    )

    settings_tab.SettingsTab._browse(tab)
    assert tab.path_var.get() == "C:/TORCS"


def test_save_rejects_invalid_folder(monkeypatch):
    errors = []
    tab = settings_tab.SettingsTab.__new__(settings_tab.SettingsTab)
    tab.path_var = DummyVar("C:/invalid")
    tab.validate_torcs_folder = lambda: False
    monkeypatch.setattr(
        settings_tab.messagebox,
        "showerror",
        lambda title, msg: errors.append((title, msg)),
    )

    settings_tab.SettingsTab._save(tab)
    assert errors == [("Error", "Selected path is not a valid torcs folder")]


def test_save_persists_valid_path(monkeypatch):
    saved_payloads = []
    infos = []

    tab = settings_tab.SettingsTab.__new__(settings_tab.SettingsTab)
    tab.path_var = DummyVar(" C:/torcs ")
    tab.validate_torcs_folder = lambda: True

    monkeypatch.setattr(settings_tab, "load_settings", lambda: {"torcs_root": ""})
    monkeypatch.setattr(
        settings_tab,
        "save_settings",
        lambda payload: saved_payloads.append(payload.copy()),
    )
    monkeypatch.setattr(
        settings_tab.messagebox,
        "showinfo",
        lambda title, msg: infos.append((title, msg)),
    )

    settings_tab.SettingsTab._save(tab)

    assert saved_payloads == [{"torcs_root": "C:/torcs"}]
    assert infos == [("Settings", "Settings saved.")]
