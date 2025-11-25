import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import type { GestureName } from '../types';

const WS_URL = 'ws://localhost:8765';
const RECONNECT_DELAY = 2000;

interface WSMessage {
  type: string;
  payload: Record<string, unknown>;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const {
    setConnected,
    setCurrentFrame,
    setGesture,
    setClutch,
    setIsDictating,
    showAction,
    setGestureConfig,
  } = useAppStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        // Request current config
        ws.send(JSON.stringify({ type: 'get_config' }));
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        // Schedule reconnect
        reconnectTimeoutRef.current = window.setTimeout(connect, RECONNECT_DELAY);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect:', error);
      reconnectTimeoutRef.current = window.setTimeout(connect, RECONNECT_DELAY);
    }
  }, [setConnected, setCurrentFrame, setGesture, setClutch, setIsDictating, showAction, setGestureConfig]);

  const handleMessage = useCallback((message: WSMessage) => {
    switch (message.type) {
      case 'frame':
        setCurrentFrame(message.payload.frame as string);
        break;

      case 'gesture':
        setGesture({
          currentGesture: message.payload.gesture as GestureName,
          confidence: message.payload.confidence as number,
          detectionSource: message.payload.source as 'local' | 'gemini',
        });
        break;

      case 'clutch':
        setClutch({
          engaged: message.payload.engaged as boolean,
          stableFrames: message.payload.stableFrames as number,
        });
        break;

      case 'dictation':
        setIsDictating(message.payload.active as boolean);
        break;

      case 'action':
        showAction(
          message.payload.description as string,
          message.payload.gesture as GestureName
        );
        break;

      case 'config':
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setGestureConfig(message.payload.gestures as any);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [setCurrentFrame, setGesture, setClutch, setIsDictating, showAction, setGestureConfig]);

  const sendMessage = useCallback((type: string, payload: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, payload }));
    }
  }, []);

  const updateGestureCommand = useCallback((gesture: string, command: string) => {
    sendMessage('update_gesture', { gesture, command });
  }, [sendMessage]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    sendMessage,
    updateGestureCommand,
  };
}
