"""
Window manager utilities for macOS.
Detects active window to ensure gestures only work when Terminal is focused.
"""
import logging
from typing import Optional

try:
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )
    from AppKit import NSWorkspace
    MACOS_APIS_AVAILABLE = True
except ImportError:
    MACOS_APIS_AVAILABLE = False


class WindowManager:
    """Manages window focus detection on macOS."""

    # Terminal app bundle identifiers
    TERMINAL_APPS = [
        'com.apple.Terminal',      # Terminal.app
        'com.googlecode.iterm2',   # iTerm2
        'dev.warp.Warp-Stable',    # Warp
        'io.alacritty',            # Alacritty
        'org.hammerspoon',         # Hammerspoon (if running terminal)
    ]

    def __init__(self):
        """Initialize window manager."""
        self.logger = logging.getLogger(__name__)

        if not MACOS_APIS_AVAILABLE:
            self.logger.warning(
                "macOS APIs not available. Window focus detection disabled. "
                "Install pyobjc-framework-Quartz and pyobjc-framework-Cocoa."
            )

    def get_active_app_bundle_id(self) -> Optional[str]:
        """
        Get the bundle ID of the currently active application.

        Returns:
            Bundle ID string or None if unavailable
        """
        if not MACOS_APIS_AVAILABLE:
            return None

        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            return active_app.get('NSApplicationBundleIdentifier')
        except Exception as e:
            self.logger.error(f"Failed to get active app: {e}")
            return None

    def is_terminal_active(self) -> bool:
        """
        Check if a terminal application is currently the active window.

        Returns:
            True if terminal is active, False otherwise
        """
        if not MACOS_APIS_AVAILABLE:
            # If APIs not available, assume terminal is active (fallback)
            return True

        bundle_id = self.get_active_app_bundle_id()

        if bundle_id is None:
            return False

        is_active = bundle_id in self.TERMINAL_APPS
        self.logger.debug(f"Active app: {bundle_id}, Is terminal: {is_active}")

        return is_active

    def get_active_window_name(self) -> Optional[str]:
        """
        Get the name of the currently active window.

        Returns:
            Window name or None if unavailable
        """
        if not MACOS_APIS_AVAILABLE:
            return None

        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            return active_app.get('NSApplicationName')
        except Exception as e:
            self.logger.error(f"Failed to get active window name: {e}")
            return None
