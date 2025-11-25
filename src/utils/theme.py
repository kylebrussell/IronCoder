"""
Theme constants for gesture control UI.
Minimal/clean design inspired by macOS/iOS with Tokyo Night color influences.
All colors are in BGR format for OpenCV.
"""

# Color palette
COLORS = {
    # Background colors
    'background_dark': (35, 30, 30),          # Near black with slight warmth
    'background_medium': (45, 40, 40),        # Panels
    'background_elevated': (55, 50, 50),      # Cards, elevated surfaces
    'background_overlay': (25, 22, 22),       # Modal overlays

    # Text colors
    'text_primary': (255, 255, 255),          # White - main text
    'text_secondary': (190, 185, 180),        # Muted - descriptions
    'text_tertiary': (130, 125, 120),         # Hints, disabled

    # Status colors
    'clutch_engaged': (140, 210, 140),        # Soft green
    'clutch_disengaged': (120, 110, 130),     # Muted purple-gray
    'recording': (130, 130, 220),             # Soft red

    # Accent colors for gestures (softer palette)
    'accent_voice': (210, 160, 190),          # Soft purple - voice dictation
    'accent_server': (170, 215, 160),         # Soft green - server control
    'accent_git': (160, 190, 230),            # Soft blue - git operations
    'accent_clear': (160, 150, 200),          # Soft coral - clear/cancel
    'accent_stop': (140, 180, 220),           # Soft orange - stop
    'accent_help': (200, 180, 160),           # Soft teal - help
    'accent_test': (180, 200, 160),           # Soft lime - testing
    'accent_chat': (190, 170, 200),           # Soft violet - chat
    'accent_code': (180, 190, 220),           # Soft sky - code
    'accent_cost': (200, 190, 170),           # Soft amber - cost

    # UI elements
    'border_light': (80, 75, 70),             # Subtle borders
    'border_medium': (100, 95, 90),           # Visible borders
    'shadow': (15, 12, 12),                   # Soft shadows
}

# Gesture to accent color mapping
GESTURE_COLORS = {
    'open_palm': COLORS['accent_voice'],
    'peace_sign': COLORS['accent_server'],
    'thumbs_up': COLORS['accent_git'],
    'thumbs_down': COLORS['accent_clear'],
    'pointing': COLORS['accent_stop'],
    'ok_sign': COLORS['accent_help'],
    'rock_sign': COLORS['accent_test'],
    'shaka': COLORS['accent_chat'],
    'three_fingers': COLORS['accent_code'],
    'four_fingers': COLORS['accent_cost'],
}

# Typography
FONTS = {
    'primary': 0,      # cv2.FONT_HERSHEY_SIMPLEX
    'header': 1,       # cv2.FONT_HERSHEY_PLAIN (actually use DUPLEX for headers)
}

# Font scales
FONT_SCALE = {
    'small': 0.4,
    'medium': 0.5,
    'large': 0.7,
    'xlarge': 0.9,
}

# UI dimensions
DIMENSIONS = {
    'border_thickness': 3,
    'glow_layers': 4,
    'panel_margin': 16,
    'card_gap': 8,
    'card_height': 90,
    'panel_height': 160,
    'status_pill_height': 28,
    'status_pill_padding': 12,
    'action_popup_width': 280,
    'action_popup_height': 60,
    'corner_radius': 6,
}

# Animation settings
ANIMATION = {
    'fade_frames': 25,
    'pulse_speed': 0.15,
    'pulse_min': 0.7,
    'pulse_max': 1.0,
}

# Alpha values for transparency
ALPHA = {
    'panel_background': 0.88,
    'card_background': 0.75,
    'overlay_dark': 0.6,
    'glow_base': 0.08,
    'shadow': 0.25,
}
