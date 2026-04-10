# Home tab
import os
import tkinter as tk
from tkinter import ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class HomeTab:
    def __init__(self, notebook, switch_tab):
        self.frame = ttk.Frame(notebook, padding=(40, 30))
        notebook.add(self.frame, text="Home")
        self.switch_tab = switch_tab
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.build_homeframe()

    def on_get_started(self):
        self.switch_tab("Settings")

    # frame for entire page
    def build_homeframe(self):
        BG = "#fcffff"

        # set styles for background, title, subtitle
        style = ttk.Style()
        style.configure("Home.TFrame", background=BG)
        style.configure(
            "HeroTitle.TLabel",
            font=("Segoe UI", 30, "bold"),
            foreground="#312e2d",
            background=BG,
        )
        style.configure(
            "HeroSubtitle1.TLabel",
            font=("Segoe UI", 17),
            foreground="#312e2d",
            background=BG,
        )

        # uses background colour for entire page
        self.frame.configure(style="Home.TFrame")

        # set up for home frame that will hold everything
        home_frame = ttk.Frame(self.frame, style="Home.TFrame")
        home_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 40))
        home_frame.grid_anchor("center")
        home_frame.columnconfigure(0, weight=1)
        home_frame.columnconfigure(1, weight=1)

        # set up frame that will hold the text on the left
        text_frame = ttk.Frame(home_frame, style="Home.TFrame")
        text_frame.grid(row=0, column=0, sticky="nw", padx=(40, 0))

        # label for main title
        ttk.Label(
            text_frame,
            text="TORCS Branding &\nCustomisation Tool",
            style="HeroTitle.TLabel",
        ).grid(row=3, column=0, sticky="w")

        # label for subtitle
        ttk.Label(
            text_frame,
            text="TCD Trailblazers — SwEng Group 10\n\n"
            "Easily upload and validate your TORCS\ncar and track assets.",
            style="HeroSubtitle1.TLabel",
            justify="left",
        ).grid(row=4, column=0, sticky="w", pady=(15, 15))

        # Load button image
        btn_image_path = os.path.join(
            BASE_DIR, "assets", "images", "get_started_btn2.png"
        )

        self.btn_photo = tk.PhotoImage(file=btn_image_path)

        # create button
        btn = tk.Button(
            text_frame,
            image=self.btn_photo,
            borderwidth=0,
            cursor="hand2",
            bg=BG,
            activebackground=BG,
            relief="flat",
            command=self.on_get_started,
        )
        btn.grid(row=5, column=0, sticky="w")

        # Main image on the right
        image_panel = ttk.Frame(home_frame, width=480, height=300, style="Home.TFrame")
        image_panel.grid(row=0, column=1, sticky="e")
        image_panel.grid_propagate(False)

        image_path = os.path.join(BASE_DIR, "assets", "images", "torcs_homepage.png")
        self.photo = tk.PhotoImage(file=image_path)

        tk.Label(image_panel, image=self.photo, borderwidth=0, bg=BG).grid(
            row=0, column=0, sticky="nsew"
        )
