"""Tests for frontend.home_tab."""

import frontend.home_tab as home_tab


def test_on_get_started_switches_to_settings():
    called = []
    tab = home_tab.HomeTab.__new__(home_tab.HomeTab)
    tab.switch_tab = lambda name: called.append(name)

    home_tab.HomeTab.on_get_started(tab)
    assert called == ["Settings"]
