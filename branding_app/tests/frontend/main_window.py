"""Tests for frontend.main_window."""

import frontend.main_window as main_window


class DummyNotebook:
    def __init__(self):
        self.selected = None

    def select(self, frame):
        self.selected = frame


class DummyButton:
    def __init__(self):
        self.fg = None

    def config(self, **kwargs):
        if "fg" in kwargs:
            self.fg = kwargs["fg"]


class DummyTab:
    def __init__(self, frame):
        self.frame = frame


def test_switch_tab_selects_frame_and_updates_nav_colors():
    window = main_window.MainWindow.__new__(main_window.MainWindow)
    window.notebook = DummyNotebook()
    window.tabs = {
        "Home": DummyTab("home-frame"),
        "Upload": DummyTab("upload-frame"),
    }
    window.nav_buttons = {
        "Home": DummyButton(),
        "Upload": DummyButton(),
    }

    main_window.MainWindow.switch_tab(window, "Upload")

    assert window.notebook.selected == "upload-frame"
    assert window.nav_buttons["Home"].fg == "#312e2d"
    assert window.nav_buttons["Upload"].fg == "#004aad"
