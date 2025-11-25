import { create } from 'zustand';
import type { GestureName, GestureConfig, GestureState, ClutchState } from '../types';

interface AppState {
  // Connection
  connected: boolean;
  setConnected: (connected: boolean) => void;

  // Video frame
  currentFrame: string | null;
  setCurrentFrame: (frame: string | null) => void;

  // Gesture detection
  gesture: GestureState;
  setGesture: (gesture: Partial<GestureState>) => void;

  // Clutch state
  clutch: ClutchState;
  setClutch: (clutch: Partial<ClutchState>) => void;

  // System state
  isDictating: boolean;
  setIsDictating: (isDictating: boolean) => void;

  // Action feedback
  lastAction: { text: string; gesture: GestureName; timestamp: number } | null;
  showAction: (text: string, gesture: GestureName) => void;
  clearAction: () => void;

  // Gesture configuration
  gestureConfig: Record<string, GestureConfig>;
  setGestureConfig: (config: Record<string, GestureConfig>) => void;
  updateGestureCommand: (gesture: string, command: string, description?: string) => void;

  // UI state
  showSettings: boolean;
  toggleSettings: () => void;
  showHints: boolean;
  toggleHints: () => void;
}

const defaultGestureConfig: Record<string, GestureConfig> = {
  open_palm: { action: 'voice_dictation', description: 'Voice Input' },
  peace_sign: { command: 'start the dev server', description: 'Start Server' },
  thumbs_up: { command: '/compact', description: 'Compact' },
  thumbs_down: { action: 'clear_input', description: 'Clear Input' },
  pointing: { command: '/help', description: 'Help' },
  ok_sign: { command: 'run the tests', description: 'Run Tests' },
  rock_sign: { command: '/cost', description: 'Show Cost' },
  shaka: { command: 'git status', description: 'Git Status' },
  three_fingers: { command: '/clear', description: 'Clear Chat' },
  four_fingers: { command: 'build the project', description: 'Build' },
};

export const useAppStore = create<AppState>((set) => ({
  // Connection
  connected: false,
  setConnected: (connected) => set({ connected }),

  // Video frame
  currentFrame: null,
  setCurrentFrame: (frame) => set({ currentFrame: frame }),

  // Gesture detection
  gesture: {
    currentGesture: 'none',
    confidence: 0,
    detectionSource: null,
  },
  setGesture: (gesture) =>
    set((state) => ({
      gesture: { ...state.gesture, ...gesture },
    })),

  // Clutch state
  clutch: {
    engaged: false,
    stableFrames: 0,
  },
  setClutch: (clutch) =>
    set((state) => ({
      clutch: { ...state.clutch, ...clutch },
    })),

  // System state
  isDictating: false,
  setIsDictating: (isDictating) => set({ isDictating }),

  // Action feedback
  lastAction: null,
  showAction: (text, gesture) =>
    set({
      lastAction: { text, gesture, timestamp: Date.now() },
    }),
  clearAction: () => set({ lastAction: null }),

  // Gesture configuration
  gestureConfig: defaultGestureConfig,
  setGestureConfig: (config) => set({ gestureConfig: config }),
  updateGestureCommand: (gesture, command, description) =>
    set((state) => ({
      gestureConfig: {
        ...state.gestureConfig,
        [gesture]: {
          ...state.gestureConfig[gesture],
          command,
          // Use provided description, or fall back to command if no description set
          description: description || state.gestureConfig[gesture]?.description || command,
        },
      },
    })),

  // UI state
  showSettings: false,
  toggleSettings: () => set((state) => ({ showSettings: !state.showSettings })),
  showHints: true,
  toggleHints: () => set((state) => ({ showHints: !state.showHints })),
}));
