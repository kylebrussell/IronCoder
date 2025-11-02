# IronCoder Gesture Control for Claude Code

**Control Claude Code with hand gestures!**
A macOS utility that uses webcam-based hand gesture recognition to trigger common Claude Code commands through intuitive hand movements.

## Features

- **Dual-Hand Gesture System**: Left hand for clutch engagement, right hand for commands
- **Zero Accidental Triggers**: Clutch mechanism prevents unintended gesture activation
- **4 Core Gestures**: Voice dictation, clear input, start dev server, stop dev server
- **Visual Feedback**: Real-time on-screen indicators for clutch status and detected gestures
- **Terminal Focus Detection**: Only active when Terminal/iTerm is focused (configurable)
- **Highly Configurable**: YAML-based configuration for all settings

## Gesture Commands

### Left Hand: Clutch Control
- **Closed Fist** → Clutch **ENGAGED** (enables right-hand gestures)
- **Open/No gesture** → Clutch **DISENGAGED** (all gestures ignored)

### Right Hand: Commands (only active when clutch engaged)
1. **Open Palm (5 fingers)** → Toggle voice dictation
2. **Peace Sign (2 fingers)** → Send Esc+Esc (clear input)
3. **Thumbs Up** → Send "start the dev server" + Enter
4. **Pointing Finger** → Send "kill the running server" + Enter

## Installation

### Prerequisites
- macOS (tested on macOS 10.15+)
- Python 3.9+
- Webcam
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd gesture-control-claude
   ```

2. **Install dependencies** (uv handles virtual environment automatically):
   ```bash
   uv sync
   ```

3. **Grant camera permissions**:
   - System Settings → Privacy & Security → Camera
   - Allow Terminal/iTerm to access camera

4. **Grant accessibility permissions** (for keyboard simulation):
   - System Settings → Privacy & Security → Accessibility
   - Add Terminal/iTerm to the list

5. **Create dictation shortcut** (optional, for dictation gesture):
   - Open **Shortcuts** app
   - Create a new **Quick Action** shortcut named **"Dictate Text"**
   - Add action: **"Dictate Text"** (search for it in actions)
   - Save the shortcut
   - Also enable dictation: System Settings → Keyboard → Dictation → Enable

## Usage

### Basic Usage

Run the gesture control system:
```bash
uv run python main.py
```

### Quick Start

1. Launch the application
2. Position your hands in front of the webcam
3. **Close your left fist** to engage the clutch (green border appears)
4. **Make right-hand gestures** to trigger commands
5. Press `q` to quit, `h` to toggle hints

### Configuration

Edit `config.yaml` to customize settings:

```yaml
clutch:
  hand: left
  gesture: closed_fist
  require_stable_frames: 5  # Frames required for stable detection

gestures:
  open_palm: voice_dictation
  peace_sign: double_escape
  thumbs_up: start_dev_server
  pointing: stop_dev_server

settings:
  confidence_threshold: 0.7      # Hand detection confidence (0.0-1.0)
  cooldown_ms: 500               # Milliseconds between gesture triggers
  require_terminal_focus: true   # Only work when Terminal is focused
  camera_resolution: [640, 480]  # Camera resolution
  camera_fps: 20                 # Camera frame rate

visual_feedback:
  show_overlay: true
  clutch_indicator_color: [0, 255, 0]      # Green (BGR format)
  clutch_disengaged_color: [255, 0, 0]     # Red (BGR format)
```

## How It Works

### Architecture

```
Webcam Feed → MediaPipe Hand Tracking → Dual Hand Detection
                                              ↓
                      ↓                                           ↓
            Left Hand (Clutch)                          Right Hand (Gestures)
                      ↓                                           ↓
              ClutchDetector                         CommandGestureRecognizer
                      ↓                                           ↓
                      ←─────────────────┬─────────────────────────┘
                                        ↓
                      If clutch engaged & terminal focused
                                        ↓
                                 ActionHandler
                                        ↓
                                 Execute Command
```

### Components

- **HandTracker**: MediaPipe wrapper for dual hand detection and landmark extraction
- **ClutchDetector**: Detects closed fist on left hand with frame smoothing
- **CommandGestureRecognizer**: Recognizes 4 right-hand gestures with debouncing
- **ActionHandler**: Executes system commands via pyautogui
- **WindowManager**: Detects active Terminal window (macOS)
- **VisualFeedback**: Renders on-screen overlays and indicators

### Safety Features

1. **Clutch Mechanism**: Gestures only processed when left fist is closed
2. **Terminal Focus Check**: Only active when Terminal/iTerm is focused
3. **Frame Smoothing**: Requires stable gesture over multiple frames
4. **Cooldown Period**: Prevents rapid double-triggers
5. **Hand Loss Reset**: Resets state when hands leave frame

## Development

### Project Structure

```
gesture-control-claude/
├── main.py                     # Entry point
├── config.yaml                 # Configuration
├── pyproject.toml              # Project metadata
├── src/
│   ├── hand_tracker.py         # MediaPipe hand tracking
│   ├── clutch_detector.py      # Left hand clutch detection
│   ├── gesture_recognizer.py   # Right hand gesture recognition
│   ├── action_handler.py       # Command execution
│   └── utils/
│       ├── window_manager.py   # Window focus detection
│       └── visual_feedback.py  # Visual overlays
└── README.md
```

### Running Tests

Currently, testing is manual:
1. Test clutch engagement/disengagement
2. Test each gesture individually
3. Verify no gestures fire without clutch
4. Test rapid gesture switching
5. Check performance (CPU/memory)

### Performance Optimization

- Camera resolution: 640x480 (balances accuracy and performance)
- Frame rate: 20fps (reduces CPU load)
- MediaPipe confidence: 0.7 (filters noisy detections)
- Gesture confidence: 3-5 frames (smoothing vs. responsiveness)

## Troubleshooting

### Gestures Not Triggering
- Ensure clutch (left fist) is engaged (green border)
- Check Terminal is the active window
- Verify camera permissions granted
- Try adjusting `confidence_threshold` in config
- Increase `require_stable_frames` for more stability

### Gestures Triggering Accidentally
- Increase `cooldown_ms` in config
- Increase `require_stable_frames` for stricter detection
- Keep hands out of frame when not in use

### Poor Hand Detection
- Improve lighting conditions
- Reduce background clutter
- Keep hands within camera view
- Clean camera lens
- Lower `confidence_threshold` (may increase false positives)

### Voice Dictation Not Working
- Create the "Dictate Text" Quick Action in Shortcuts app
- Enable dictation in System Settings → Keyboard
- Test the shortcut manually: `shortcuts run "Dictate Text"`
- Ensure Terminal.app is the active focused window
- Check logs for "Successfully triggered Dictate Text shortcut"

### High CPU Usage
- Lower camera resolution in config
- Reduce camera FPS
- Close other applications
- Check Activity Monitor for MediaPipe process

## Known Limitations

- **macOS Only**: Uses macOS-specific APIs for window management
- **Shortcuts Setup**: Requires creating a "Dictate Text" Quick Action in Shortcuts app
- **Lighting**: Hand detection accuracy depends on lighting conditions
- **Camera Position**: Requires hands to be visible and facing camera
- **Performance**: Real-time hand tracking is CPU-intensive

## Future Enhancements

- [ ] Linux/Windows support
- [ ] Custom gesture mapping via UI
- [ ] Gesture recording/replay
- [ ] Right-hand clutch option for left-handed users
- [ ] Integration with Claude Code API (if available)
- [ ] Background service mode (menu bar app)
- [ ] Gesture chaining for complex commands
- [ ] Alternative clutch gestures

## Credits

Built with:
- [MediaPipe](https://mediapipe.dev/) - Hand tracking
- [OpenCV](https://opencv.org/) - Computer vision
- [PyAutoGUI](https://pyautogui.readthedocs.io/) - Keyboard automation
- [uv](https://github.com/astral-sh/uv) - Python package management

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with Claude Code** 🤖
