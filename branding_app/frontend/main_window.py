# Main window with tabbed navigation

import tkinter as tk
from tkinter import ttk

from frontend.home_tab import HomeTab
from frontend.settings_tab import SettingsTab
from frontend.profiles_tab import ProfilesTab
from frontend.upload_tab import UploadTab
from frontend.apply_tab import ApplyTab
from frontend.restore_tab import RestoreTab
from frontend.track_tab import TrackTab


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TORCS Branding & Customisation Configurator")
        self.root.geometry("1100x700")
        self.root.minsize(800, 700)

        style = ttk.Style()
        style.layout("TNotebook.Tab", [])  # hide the default notebook/tab lines

        # header
        self.header = tk.Frame(self.root, bg="#f6f7ff", height=100)
        self.header.pack(side="top", fill="x")

        # logo on the left
        logo = tk.Label(
            self.header,
            text="TORCS",
            font=("Arial", 18, "bold"),
            bg="#f6f7ff",
            fg="#004aad",
        )
        logo.pack(side="left", padx=(20, 0))

        editor = tk.Label(
            self.header,
            text="EDITOR",
            font=("Arial", 14, "bold"),
            bg="#f6f7ff",
            fg="#555",
        )
        editor.pack(side="left", padx=(5, 40))

        # navigation container
        self.nav_frame = tk.Frame(self.header, bg="#f6f7ff")
        self.nav_frame.pack(side="left")

        # notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # create tab objects
        self.tabs = {
            "Home": HomeTab(self.notebook, self.switch_tab),
            "Settings": SettingsTab(self.notebook),
            "Profiles": ProfilesTab(self.notebook),
            "Track": TrackTab(self.notebook),
            "Livery": UploadTab(self.notebook),
            "Apply All": ApplyTab(self.notebook),
            "Restore": RestoreTab(self.notebook),
        }

        # store header buttons
        self.nav_buttons = {}

        # create "buttons" that will look nice over the notebook logic
        for name in self.tabs:
            btn = tk.Label(
                self.nav_frame,
                text=name,
                font=("Segoe UI", 13),
                bg="#f6f7ff",
                fg="#312e2d",
                cursor="hand2",
            )
            btn.pack(side="left", padx=25)
            btn.bind(
                "<Button-1>", lambda e, n=name: self.switch_tab(n)
            )  # when clicked switch to the tab
            self.nav_buttons[name] = btn

        # first tab when opened will be the home tab
        self.switch_tab("Home")

    # takes in the info from the header "button" and switches the tab using notebook
    def switch_tab(self, name):
        tab = self.tabs[name]
        self.notebook.select(tab.frame)

        # reset all buttons
        for btn in self.nav_buttons.values():
            btn.config(fg="#312e2d")

        # highlight the active tab
        self.nav_buttons[name].config(fg="#004aad")

    def run(self):
        self.root.mainloop()
