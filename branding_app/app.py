# Entry point for the TORCS branding app

import sys
import os

# Make sure imports work no matter where this is launched from
_app_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_app_dir)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from frontend.main_window import MainWindow  # noqa: E402


def main():
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
