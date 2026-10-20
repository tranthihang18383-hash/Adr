"""Android (and desktop preview) entry point for tetomidi. Build with: flet build apk"""
from mobile.app import main
import flet as ft

if __name__ == "__main__":
    ft.app(target=main, upload_dir="uploads")
