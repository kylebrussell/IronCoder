# IronCoder Gesture Control for Claude Code

**Control Claude Code with hand gestures and voice!**

A macOS utility that combines AI-powered gesture recognition and voice transcription to control Claude Code through intuitive hand movements and speech.

## Features

- **Hybrid Gesture Detection**: Fast local detection with optional Gemini fallback
- **Low Latency**: ~100-200ms gesture response (vs 2-3s with API-only)
- **Voice Input**: Push-to-talk with real-time Whisper transcription
- **Dual-Hand System**: Left hand clutch + right hand gestures
- **Beautiful UI**: Modern card-based overlay with color-coded controls
- **Zero Accidental Triggers**: Clutch mechanism prevents unintended activation
- **5 Core Gestures**: Voice, commit & push, clear input, start/stop server
- **Highly Configurable**: YAML-based configuration for all settings

## Gesture Commands

### Left Hand: Clutch Control
- **Closed Fist** → Clutch **ENGAGED** (enables right-hand gestures)
- **Open/No gesture** → Clutch **DISENGAGED** (all gestures ignored)

### Right Hand: Commands (only active when clutch engaged)

| Gesture | Action | Description |
|---------|--------|-------------|
| **Open Palm** | Voice Dictation | Push-to-talk: Hold to record, release to transcribe |
| **Peace Sign** | Start Dev Server | Types "start the dev server" + Enter |
| **Thumbs Up** | Commit & Push | Types "commit and push" + Enter |
| **Thumbs Down** | Clear Input | Sends Escape + Escape to clear input |
| **Pointing** | Stop Dev Server | Types "kill the running server" + Enter |

## Installation

### Prerequisites
- macOS (tested on macOS 10.15+)
- Python 3.10+
- Webcam
- Google Gemini API Key ([Get one free](https://aistudio.google.com/app/apikey))

### Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd gesture-control-claude
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure Gemini API key**:
   Create a `.env.local` file:
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env.local
   ```

4. **Grant camera permissions**:
   - System Settings → Privacy & Security → Camera
   - Allow Terminal/iTerm to access camera

5. **Grant accessibility permissions** (for keyboard simulation):
   - System Settings → Privacy & Security → Accessibility
   - Add Terminal/iTerm to the list

## Usage

### Running the App

```bash
python3 main.py
```

### Quick Start Guide

1. **Launch** the application - webcam feed opens with overlay
2. **Position hands** in front of the camera
3. **Close left fist** to engage clutch (green border appears)
4. **Make gestures** with your right hand:
   - Hold **open palm** and speak, release when done
   - Show **thumbs up** to commit and push
   - Show **thumbs down** to clear input
   - And more!
5. **Press keys**:
   - `h` - Toggle hints overlay
   - `q` - Quit application

### Voice Input Tips

- **Hold open palm** gesture while speaking
- **Speak clearly** into your microphone
- **Release gesture** when finished speaking
- Text appears automatically in Claude Code input
- Uses Whisper AI for accurate transcription

## Configuration

Edit `config.yaml` to customize settings:

```yaml
clutch:
  hand: left                    # Which hand for clutch
  gesture: closed_fist
  require_stable_frames: 5      # Stability threshold

gestures:
  open_palm: voice_dictation
  peace_sign: start_dev_server
  thumbs_up: commit_push
  thumbs_down: clear_input
  pointing: stop_dev_server

settings:
  confidence_threshold: 0.7     # Hand detection confidence
  cooldown_ms: 500              # Delay between gestures
  require_terminal_focus: false # Terminal focus requirement
  camera_resolution: [640, 480]
  camera_fps: 20

# Hybrid detection: fast local + optional Gemini fallback
hybrid_detection:
  use_gemini_fallback: false    # Set true for Gemini verification
  gestures:
    open_palm:
      stability_frames: 2       # Frames needed (2 = ~100ms)
      skip_gemini_above: 0.75   # Confidence threshold
    peace_sign:
      stability_frames: 4
      skip_gemini_above: 0.85
    # ... other gestures

gemini:
  model: gemini-2.5-flash       # Gemini model (for fallback)
  sample_interval: 0.5          # Seconds between API calls
  resize_width: 256             # Image width sent to API
```

## Architecture

```
Webcam Feed
    ↓
MediaPipe Hand Tracking
    ├─→ Left Hand → Clutch Detection
    └─→ Right Hand → Hybrid Gesture Detector
                         ├─→ Local Detection (fast, ~1ms)
                         └─→ Gemini Fallback (optional)
    ↓
Action Handler
    ├─→ Whisper AI (Voice Transcription)
    └─→ PyAutoGUI (Keyboard Simulation)
```

### Key Components

- **HandTracker**: MediaPipe wrapper for hand landmark detection
- **ClutchDetector**: Detects closed fist on left hand
- **HybridGestureDetector**: Fast local detection with optional Gemini fallback
- **CommandGestureRecognizer**: Geometric landmark-based gesture detection with confidence scoring
- **AudioHandler**: Real-time audio recording and Whisper transcription (with artifact filtering)
- **ActionHandler**: Executes commands and manages voice input
- **VisualFeedback**: Card-based UI overlay

### Technology Stack

- **[MediaPipe](https://mediapipe.dev/)** - Hand tracking and landmark detection
- **[Google Gemini Vision API](https://ai.google.dev/)** - Optional gesture verification
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** - Speech-to-text
- **[OpenCV](https://opencv.org/)** - Computer vision
- **[PyAutoGUI](https://pyautogui.readthedocs.io/)** - Keyboard automation

## Safety Features

1. **Clutch Mechanism**: Gestures only work when left fist is closed
2. **Confidence Scoring**: Each gesture has a confidence threshold (0.0-1.0)
3. **Frame Stability**: Requires consistent detection over multiple frames
4. **Cooldown Period**: Prevents rapid double-triggers
5. **Hand Loss Reset**: Resets state when hands leave frame
6. **Strict Gesture Discrimination**: Gestures require clear, distinct hand positions

## Troubleshooting

### Gestures Not Triggering
- Ensure clutch (left fist) is engaged (green border)
- Make gestures clearly in front of camera
- Check camera permissions granted
- Verify `.env.local` has valid Gemini API key
- Try adjusting `confidence_threshold` in config

### Voice Input Not Working
- Hold open palm gesture while speaking
- Ensure microphone is working
- Check for "Processing..." logs
- Verify faster-whisper installed: `pip3 show faster-whisper`
- Wait 3 seconds before releasing gesture (chunk processing)

### Gemini API Issues
- Check API key in `.env.local`
- Verify API quota: [Google AI Studio](https://aistudio.google.com/)
- Look for "Sending frame to Gemini API..." in logs
- Check internet connection

### Poor Gesture Detection
- Improve lighting conditions
- Make gestures clearly and deliberately
- Try reducing `stability_frames` in hybrid_detection config
- Ensure hand is fully visible in camera frame

### Gestures Triggering Too Easily
- Increase `stability_frames` for problematic gestures
- Increase `skip_gemini_above` threshold (e.g., 0.90)
- Make more deliberate, exaggerated gestures

### High CPU Usage
- Lower camera resolution in config
- Reduce camera FPS
- Close other applications

## Project Structure

```
gesture-control-claude/
├── main.py                         # Entry point
├── config.yaml                     # Configuration
├── requirements.txt                # Dependencies
├── .env.local                      # API keys (create this)
├── src/
│   ├── hand_tracker.py             # MediaPipe hand tracking
│   ├── clutch_detector.py          # Left hand clutch detection
│   ├── hybrid_gesture_detector.py  # Fast local + Gemini fallback
│   ├── gesture_recognizer.py       # Geometric gesture detection with confidence
│   ├── gemini_gesture_detector.py  # Gemini Vision API integration
│   ├── audio_handler.py            # Whisper transcription + artifact filtering
│   ├── action_handler.py           # Command execution
│   └── utils/
│       ├── window_manager.py       # Window focus detection
│       └── visual_feedback.py      # UI overlays
└── README.md
```

## Future Enhancements

- [ ] Custom gesture training via Gemini fine-tuning
- [ ] Gesture chaining for complex commands
- [ ] Right-hand clutch option for left-handed users
- [ ] Background service mode (menu bar app)
- [ ] Multi-language voice support
- [ ] Gesture macros/shortcuts
- [ ] Linux/Windows support

## Development Notes

### Adding New Gestures

1. Add detection method to `gesture_recognizer.py` (e.g., `detect_new_gesture()`)
2. Add confidence method (e.g., `new_gesture_confidence()`)
3. Add to `recognize_gesture()` and `recognize_with_confidence()`
4. Add gesture config to `hybrid_gesture_detector.py` DEFAULT_GESTURE_CONFIG
5. Add action method to `ActionHandler`
6. Update `config.yaml` gesture mappings and hybrid_detection settings
7. Update visual feedback hints in `visual_feedback.py`

### Performance Optimization

- Camera: 640x480 @ 20fps (balances accuracy and performance)
- Local detection: ~1ms per frame (geometric landmark analysis)
- Stability frames: 2-4 frames = 100-200ms response time
- Whisper: int8 quantization for faster inference
- MediaPipe: 0.7 confidence threshold (filters noise)

## Credits

Built with:
- [Google Gemini Vision API](https://ai.google.dev/) - AI gesture detection
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Speech-to-text
- [MediaPipe](https://mediapipe.dev/) - Hand tracking
- [OpenCV](https://opencv.org/) - Computer vision
- [PyAutoGUI](https://pyautogui.readthedocs.io/) - Keyboard automation

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.
