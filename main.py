"""Android (and desktop preview) entry point for tetomidi. Build with: flet build apk"""
import flet as ft

from mobile.app import main

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
