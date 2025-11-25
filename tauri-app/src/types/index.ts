export type GestureName =
  | 'none'
  | 'open_palm'
  | 'peace_sign'
  | 'thumbs_up'
  | 'thumbs_down'
  | 'pointing'
  | 'ok_sign'
  | 'rock_sign'
  | 'shaka'
  | 'three_fingers'
  | 'four_fingers';

export interface GestureConfig {
  command?: string;
  action?: 'voice_dictation' | 'clear_input';
  description: string;
}

export interface GestureState {
  currentGesture: GestureName;
  confidence: number;
  detectionSource: 'local' | 'gemini' | null;
}

export interface ClutchState {
  engaged: boolean;
  stableFrames: number;
}

export interface SystemState {
  connected: boolean;
  isDictating: boolean;
  lastAction: string | null;
  lastActionTime: number;
}

export interface WebSocketMessage {
  type: 'frame' | 'gesture' | 'clutch' | 'action' | 'status' | 'config';
  payload: unknown;
}

export interface FramePayload {
  frame: string; // base64 encoded JPEG
  timestamp: number;
}

export interface GesturePayload {
  gesture: GestureName;
  confidence: number;
  source: 'local' | 'gemini';
  triggered: boolean;
}

export interface ClutchPayload {
  engaged: boolean;
  stableFrames: number;
}

export interface ActionPayload {
  gesture: GestureName;
  action: string;
  description: string;
  success: boolean;
}

export interface ConfigPayload {
  gestures: Record<GestureName, GestureConfig>;
}

export const GESTURE_DISPLAY_NAMES: Record<GestureName, string> = {
  none: 'None',
  open_palm: 'Palm',
  peace_sign: 'Peace',
  thumbs_up: 'Thumbs Up',
  thumbs_down: 'Thumbs Down',
  pointing: 'Point',
  ok_sign: 'OK',
  rock_sign: 'Rock',
  shaka: 'Shaka',
  three_fingers: 'Three',
  four_fingers: 'Four',
};

export const GESTURE_COLORS: Record<GestureName, string> = {
  none: 'text-muted',
  open_palm: 'text-gesture-palm',
  peace_sign: 'text-gesture-peace',
  thumbs_up: 'text-gesture-thumbup',
  thumbs_down: 'text-gesture-thumbdown',
  pointing: 'text-gesture-point',
  ok_sign: 'text-gesture-ok',
  rock_sign: 'text-gesture-rock',
  shaka: 'text-gesture-shaka',
  three_fingers: 'text-gesture-three',
  four_fingers: 'text-gesture-four',
};

export const GESTURE_BG_COLORS: Record<GestureName, string> = {
  none: 'bg-bg-elevated',
  open_palm: 'bg-gesture-palm',
  peace_sign: 'bg-gesture-peace',
  thumbs_up: 'bg-gesture-thumbup',
  thumbs_down: 'bg-gesture-thumbdown',
  pointing: 'bg-gesture-point',
  ok_sign: 'bg-gesture-ok',
  rock_sign: 'bg-gesture-rock',
  shaka: 'bg-gesture-shaka',
  three_fingers: 'bg-gesture-three',
  four_fingers: 'bg-gesture-four',
};
