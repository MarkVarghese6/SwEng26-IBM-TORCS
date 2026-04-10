"""Tests for frontend.profiles_tab."""

import frontend.profiles_tab as profiles_tab


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


def test_refresh_inserts_placeholder_when_no_profiles(monkeypatch):
    tab = profiles_tab.ProfilesTab.__new__(profiles_tab.ProfilesTab)
    tab.tree = DummyTree()
    monkeypatch.setattr(profiles_tab, "load_profiles", lambda: [])

    profiles_tab.ProfilesTab._refresh(tab)

    assert tab.tree.rows == [
        ("(none)", "Add profiles to config/default_profiles.json", "")
    ]


def test_refresh_inserts_profile_rows(monkeypatch):
    tab = profiles_tab.ProfilesTab.__new__(profiles_tab.ProfilesTab)
    tab.tree = DummyTree()
    monkeypatch.setattr(
        profiles_tab,
        "load_profiles",
        lambda: [
            {
                "name": "Primary",
                "description": "Default",
                "livery": {"car_model": "car1-trb1"},
            },
            {"name": "Fallback", "description": "No car"},
        ],
    )

    profiles_tab.ProfilesTab._refresh(tab)

    assert tab.tree.rows == [
        ("Primary", "Default", "car1-trb1"),
        ("Fallback", "No car", "—"),
    ]
