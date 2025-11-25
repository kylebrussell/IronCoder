"""
Configuration manager for gesture control system.
Handles loading, saving, and runtime updates of gesture-command mappings.
"""
import yaml
import logging
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path


class ConfigManager:
    """Manages gesture configuration with runtime updates."""

    DEFAULT_GESTURES = {
        'open_palm': {
            'action': 'voice_dictation',
            'description': 'Voice Input'
        },
        'peace_sign': {
            'command': 'start the dev server',
            'description': 'Start Server'
        },
        'thumbs_up': {
            'command': 'commit and push',
            'description': 'Commit & Push'
        },
        'thumbs_down': {
            'action': 'clear_input',
            'description': 'Clear Input'
        },
        'pointing': {
            'command': 'kill the running server',
            'description': 'Stop Server'
        },
        'ok_sign': {
            'command': '/help',
            'description': 'Help'
        },
        'rock_sign': {
            'command': 'run tests',
            'description': 'Run Tests'
        },
        'shaka': {
            'command': '/clear',
            'description': 'Clear Chat'
        },
        'three_fingers': {
            'command': 'explain this code',
            'description': 'Explain Code'
        },
        'four_fingers': {
            'command': '/cost',
            'description': 'Show Cost'
        },
    }

    DEFAULT_PRESETS = {
        'claude_commands': [
            '/help',
            '/clear',
            '/compact',
            '/cost',
            '/doctor',
            '/status',
        ],
        'dev_commands': [
            'start the dev server',
            'kill the running server',
            'run tests',
            'run the build',
            'check for errors',
        ],
        'git_commands': [
            'commit and push',
            'show git status',
            'create a pull request',
            'undo the last commit',
        ],
        'code_commands': [
            'explain this code',
            'find bugs in this code',
            'refactor this function',
            'add comments to this code',
        ],
    }

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.callbacks: List[Callable[[], None]] = []
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Configuration dictionary
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                self.logger.info(f"Loaded config from {self.config_path}")
            else:
                self.config = {}
                self.logger.warning(f"Config file not found: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.config = {}

        # Ensure gestures section exists with defaults
        self._ensure_defaults()
        return self.config

    def _ensure_defaults(self):
        """Ensure all required config sections exist with defaults."""
        # Ensure gestures section
        if 'gestures' not in self.config:
            self.config['gestures'] = {}

        # Add any missing gestures from defaults
        for gesture, default_config in self.DEFAULT_GESTURES.items():
            if gesture not in self.config['gestures']:
                self.config['gestures'][gesture] = default_config.copy()
            else:
                # Migrate old format (string value) to new format (dict)
                current = self.config['gestures'][gesture]
                if isinstance(current, str):
                    # Old format was just the action name
                    if current in ('voice_dictation', 'clear_input'):
                        self.config['gestures'][gesture] = {
                            'action': current,
                            'description': default_config.get('description', gesture.replace('_', ' ').title())
                        }
                    else:
                        self.config['gestures'][gesture] = {
                            'command': current,
                            'description': default_config.get('description', gesture.replace('_', ' ').title())
                        }

        # Ensure command presets
        if 'command_presets' not in self.config:
            self.config['command_presets'] = self.DEFAULT_PRESETS.copy()

        # Ensure settings section
        if 'settings' not in self.config:
            self.config['settings'] = {}

        # Ensure visual_feedback section
        if 'visual_feedback' not in self.config:
            self.config['visual_feedback'] = {
                'show_overlay': True,
                'show_hints': True,
            }

    def save_config(self):
        """Save current configuration to YAML file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            self.logger.info(f"Saved config to {self.config_path}")
            self.notify_changes()
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def get_gesture_config(self, gesture: str) -> Optional[Dict[str, str]]:
        """
        Get configuration for a specific gesture.

        Args:
            gesture: Gesture name (e.g., 'thumbs_up')

        Returns:
            Dict with 'command' or 'action' and 'description', or None
        """
        return self.config.get('gestures', {}).get(gesture)

    def get_gesture_command(self, gesture: str) -> Optional[str]:
        """
        Get the command string for a gesture.

        Args:
            gesture: Gesture name

        Returns:
            Command string or None if gesture uses special action
        """
        gesture_config = self.get_gesture_config(gesture)
        if gesture_config:
            return gesture_config.get('command')
        return None

    def get_gesture_action(self, gesture: str) -> Optional[str]:
        """
        Get the special action for a gesture.

        Args:
            gesture: Gesture name

        Returns:
            Action name ('voice_dictation', 'clear_input') or None
        """
        gesture_config = self.get_gesture_config(gesture)
        if gesture_config:
            return gesture_config.get('action')
        return None

    def get_gesture_description(self, gesture: str) -> str:
        """
        Get the display description for a gesture.

        Args:
            gesture: Gesture name

        Returns:
            Description string or formatted gesture name
        """
        gesture_config = self.get_gesture_config(gesture)
        if gesture_config:
            return gesture_config.get('description', gesture.replace('_', ' ').title())
        return gesture.replace('_', ' ').title()

    def set_gesture_command(self, gesture: str, command: str, description: Optional[str] = None):
        """
        Update the command for a gesture.

        Args:
            gesture: Gesture name
            command: New command string
            description: Optional description (keeps existing if not provided)
        """
        if 'gestures' not in self.config:
            self.config['gestures'] = {}

        if gesture not in self.config['gestures']:
            self.config['gestures'][gesture] = {}

        # Clear any existing action
        if 'action' in self.config['gestures'][gesture]:
            del self.config['gestures'][gesture]['action']

        self.config['gestures'][gesture]['command'] = command

        if description:
            self.config['gestures'][gesture]['description'] = description

        self.logger.info(f"Updated gesture '{gesture}' command to: {command}")
        self.notify_changes()

    def get_all_gestures(self) -> List[str]:
        """
        Get list of all configured gestures.

        Returns:
            List of gesture names
        """
        return list(self.config.get('gestures', {}).keys())

    def get_command_presets(self) -> Dict[str, List[str]]:
        """
        Get all command presets.

        Returns:
            Dict mapping preset names to command lists
        """
        return self.config.get('command_presets', self.DEFAULT_PRESETS)

    def get_preset_commands(self, preset_name: str) -> List[str]:
        """
        Get commands for a specific preset.

        Args:
            preset_name: Name of the preset

        Returns:
            List of command strings
        """
        return self.get_command_presets().get(preset_name, [])

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        return self.config.get('settings', {}).get(key, default)

    def set_setting(self, key: str, value: Any):
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'][key] = value
        self.notify_changes()

    def get_visual_feedback_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a visual feedback setting.

        Args:
            key: Setting key
            default: Default value

        Returns:
            Setting value or default
        """
        return self.config.get('visual_feedback', {}).get(key, default)

    def register_change_callback(self, callback: Callable[[], None]):
        """
        Register a callback for configuration changes.

        Args:
            callback: Function to call when config changes
        """
        self.callbacks.append(callback)

    def unregister_change_callback(self, callback: Callable[[], None]):
        """
        Unregister a change callback.

        Args:
            callback: Callback to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def notify_changes(self):
        """Notify all registered callbacks of configuration changes."""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in config change callback: {e}")

    def reset_to_defaults(self):
        """Reset gesture configuration to defaults."""
        self.config['gestures'] = {}
        for gesture, default_config in self.DEFAULT_GESTURES.items():
            self.config['gestures'][gesture] = default_config.copy()
        self.logger.info("Reset gestures to defaults")
        self.notify_changes()

    def is_special_action(self, gesture: str) -> bool:
        """
        Check if a gesture uses a special action (not a text command).

        Args:
            gesture: Gesture name

        Returns:
            True if gesture uses special action
        """
        return self.get_gesture_action(gesture) is not None
