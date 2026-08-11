from __future__ import annotations

from .config import RuntimeConfig


def chrome_launch_options(visible: bool) -> dict:
    return {
        "channel": "chrome",
        "headless": not visible,
        "no_viewport": True,
    }


def open_echotik_context(playwright, config: RuntimeConfig):
    config.validate()
    return playwright.chromium.launch_persistent_context(
        config.profile_dir,
        **chrome_launch_options(visible=True),
    )
