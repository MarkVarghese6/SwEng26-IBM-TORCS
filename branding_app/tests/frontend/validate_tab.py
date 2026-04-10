"""Tests for frontend.validate_tab."""

import frontend.validate_tab as validate_tab


class DummyTree:
    def __init__(self):
        self.rows = []

    def get_children(self):
        return list(range(len(self.rows)))

    def delete(self, _row):
        if self.rows:
            self.rows.pop(0)

    def insert(self, _parent, _where, values):
        self.rows.append(values)


def test_populate_defaults_when_none_rows():
    tab = validate_tab.ValidateTab.__new__(validate_tab.ValidateTab)
    tab.tree = DummyTree()

    validate_tab.ValidateTab._populate(tab, None)

    assert tab.tree.rows == [
        ("splash_screen", "n/a", "Waiting for validation"),
        ("loading_screen", "n/a", "Waiting for validation"),
        ("livery", "n/a", "Waiting for validation"),
    ]


def test_validate_populates_pass_fail_results(monkeypatch):
    tab = validate_tab.ValidateTab.__new__(validate_tab.ValidateTab)
    tab.tree = DummyTree()
    tab.tree.rows = [("old", "old", "old")]

    monkeypatch.setattr(validate_tab, "load_active_profile", lambda: {"name": "x"})
    monkeypatch.setattr(
        validate_tab,
        "build_apply_plan",
        lambda profile, uploads: (
            [
                {
                    "label": "banners.splash",
                    "source_path": "splash.png",
                    "width": 256,
                    "height": 128,
                },
                {
                    "label": "banners.loading",
                    "source_path": "loading.png",
                    "width": 64,
                    "height": 64,
                },
            ],
            [{"label": "livery", "target_path": "cars/x.png"}],
        ),
    )

    outcomes = {
        "splash.png": (True, ""),
        "loading.png": (False, "Incorrect proportions"),
    }
    monkeypatch.setattr(
        validate_tab,
        "validate_image_dimensions",
        lambda path, _w, _h: outcomes.get(path, (True, "")),
    )

    validate_tab.ValidateTab._validate(tab)

    assert tab.tree.rows == [
        ("banners.splash", "Passed", ""),
        ("banners.loading", "Failed", "Incorrect proportions"),
        ("livery", "Failed", "Missing source file for target cars/x.png"),
    ]


def test_validate_handles_missing_profiles(monkeypatch):
    tab = validate_tab.ValidateTab.__new__(validate_tab.ValidateTab)
    tab.tree = DummyTree()
    monkeypatch.setattr(validate_tab, "load_active_profile", lambda: None)

    validate_tab.ValidateTab._validate(tab)

    assert tab.tree.rows == [
        ("profile", "Failed", "No profile configured in default_profiles.json")
    ]
