# IronCoder Gesture Control for Claude Code

Control Claude Code with hand gestures and voice.

A macOS utility that combines AI-powered gesture recognition and voice transcription to control Claude Code through intuitive hand movements and speech.

## Features

- **Native Tauri App**: Modern React + Tailwind UI with glass morphism effects
- **Hybrid Gesture Detection**: Fast local detection with optional Gemini fallback
- **Low Latency**: ~100-200ms gesture response
- **Voice Input**: Push-to-talk with real-time Whisper transcription
- **Dual-Hand System**: Left hand clutch + right hand gestures
- **10 Configurable Gestures**: Customizable commands via settings panel
- **Zero Accidental Triggers**: Clutch mechanism prevents unintended activation

## Gesture Commands

### Left Hand: Clutch Control
- **Closed Fist** - Clutch ENGAGED (enables right-hand gestures)
- **Open/No gesture** - Clutch DISENGAGED (all gestures ignored)

### Right Hand: Commands (only active when clutch engaged)

| Gesture | Default Action | Description |
|---------|----------------|-------------|
| Open Palm | Voice Dictation | Push-to-talk: Hold to record, release to transcribe |
| Peace Sign | Start Server | Types "start the dev server" + Enter |
| Thumbs Up | Compact | Types "/compact" + Enter |
| Thumbs Down | Clear Input | Sends Escape + Escape |
| Pointing | Help | Types "/help" + Enter |
| OK Sign | Run Tests | Types "run the tests" + Enter |
| Rock Sign | Show Cost | Types "/cost" + Enter |
| Shaka | Git Status | Types "git status" + Enter |
| Three Fingers | Clear Chat | Types "/clear" + Enter |
| Four Fingers | Build | Types "build the project" + Enter |

All gesture commands are configurable via the in-app settings panel (press `S`).

## Installation

### Prerequisites
- macOS (tested on macOS 10.15+)
- Python 3.10+
- Node.js 18+
- Rust (install via `rustup`)
- Webcam
- Google Gemini API Key (optional, for fallback detection)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd gesture-control-claude
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Install Tauri app dependencies**:
   ```bash
   cd tauri-app
   npm install
   cd ..
   ```

4. **Configure Gemini API key** (optional):
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env.local
   ```

5. **Grant permissions**:
   - System Settings > Privacy & Security > Camera (allow Terminal)
   - System Settings > Privacy & Security > Accessibility (add Terminal)

## Usage

### Running the App

**Terminal 1 - Start the Python backend**:
```bash
python3 ws_server.py
```

**Terminal 2 - Start the Tauri app**:
```bash
cd tauri-app
npm run tauri dev
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `H` | Toggle gesture hints panel |
| `S` | Open settings panel |

### Quick Start

1. Launch both the Python backend and Tauri app
2. Position hands in front of the camera
3. Close left fist to engage clutch (green border appears)
4. Make gestures with your right hand
5. Press `S` to customize gesture commands

## Architecture

```
+------------------------------------------+
|          Tauri Frontend (React)          |
|  - Modern UI with Tailwind + Framer      |
|  - Glass morphism, animations            |
|  - Real-time video display               |
|  - Settings panel with gesture config    |
+--------------------+---------------------+
                     | WebSocket (ws://localhost:8765)
                     v
+------------------------------------------+
|       Python WebSocket Server            |
|  - Streams video frames (base64 JPEG)    |
|  - MediaPipe hand tracking               |
|  - Hybrid gesture detection              |
|  - Whisper voice transcription           |
+------------------------------------------+
```

### Key Components

- **ws_server.py**: WebSocket server streaming frames and gesture data
- **HandTracker**: MediaPipe wrapper for hand landmark detection
- **ClutchDetector**: Detects closed fist on left hand
- **HybridGestureDetector**: Fast local detection with optional Gemini fallback
- **CommandGestureRecognizer**: Geometric gesture detection with confidence scoring
- **AudioHandler**: Real-time Whisper transcription
- **Tauri Frontend**: React + Tailwind + Framer Motion UI

### Technology Stack

- **[Tauri](https://tauri.app/)** - Native desktop app framework
- **[React](https://react.dev/)** - UI framework
- **[Tailwind CSS](https://tailwindcss.com/)** - Styling
- **[Framer Motion](https://www.framer.com/motion/)** - Animations
- **[MediaPipe](https://mediapipe.dev/)** - Hand tracking
- **[Google Gemini](https://ai.google.dev/)** - Optional gesture verification
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** - Speech-to-text
- **[OpenCV](https://opencv.org/)** - Computer vision

## Configuration

Edit `config.yaml` to customize settings:

```yaml
clutch:
  hand: left
  gesture: closed_fist
  require_stable_frames: 5

gestures:
  open_palm:
    action: voice_dictation
    description: "Voice Input"
  peace_sign:
    command: "start the dev server"
    description: "Start Server"
  # ... more gestures

settings:
  confidence_threshold: 0.7
  cooldown_ms: 500
  camera_resolution: [640, 480]
  camera_fps: 20

hybrid_detection:
  use_gemini_fallback: false
  gestures:
    open_palm:
      stability_frames: 2
      skip_gemini_above: 0.75
```

Command presets are available in the settings panel for quick configuration.

## Project Structure

```
gesture-control-claude/
├── ws_server.py                    # WebSocket server (run this)
├── main.py                         # Legacy OpenCV UI (deprecated)
├── config.yaml                     # Configuration
├── requirements.txt                # Python dependencies
├── .env.local                      # API keys (create this)
├── src/
│   ├── hand_tracker.py             # MediaPipe hand tracking
│   ├── clutch_detector.py          # Left hand clutch detection
│   ├── hybrid_gesture_detector.py  # Fast local + Gemini fallback
│   ├── gesture_recognizer.py       # Geometric gesture detection
│   ├── gemini_gesture_detector.py  # Gemini Vision API
│   ├── audio_handler.py            # Whisper transcription
│   ├── action_handler.py           # Command execution
│   ├── config_manager.py           # Configuration management
│   └── utils/
│       ├── window_manager.py       # Window focus detection
│       ├── visual_feedback.py      # Legacy UI overlays
│       ├── settings_ui.py          # Legacy settings UI
│       └── theme.py                # Color definitions
└── tauri-app/                      # Native desktop app
    ├── src/
    │   ├── App.tsx                 # Main React component
    │   ├── components/             # UI components
    │   ├── hooks/                  # React hooks
    │   ├── store/                  # Zustand state
    │   └── types/                  # TypeScript types
    └── src-tauri/                  # Rust backend
```

## Troubleshooting

### No Video in App
- Ensure Python backend is running (`python3 ws_server.py`)
- Check WebSocket connection in browser dev tools
- Verify camera permissions

### Gestures Not Triggering
- Ensure clutch (left fist) is engaged (green border)
- Make gestures clearly in front of camera
- Check Python backend logs for detection output

### Voice Input Not Working
- Hold open palm gesture while speaking
- Ensure microphone is working
- Check for transcription logs in Python backend

### Build Errors
- Update Rust: `rustup update stable`
- Clear npm cache: `cd tauri-app && rm -rf node_modules && npm install`

## License

MIT License

## Support

For issues, questions, or contributions, please open an issue on GitHub.
