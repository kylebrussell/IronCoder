import { useEffect } from 'react';
import { VideoFeed } from './components/VideoFeed';
import { StatusPill } from './components/StatusPill';
import { ClutchBorder } from './components/ClutchBorder';
import { RecordingIndicator } from './components/RecordingIndicator';
import { ActionFeedback } from './components/ActionFeedback';
import { GestureHints } from './components/GestureHints';
import { SettingsPanel } from './components/SettingsPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useAppStore } from './store/useAppStore';

function App() {
  const { updateGestureCommand } = useWebSocket();
  const { toggleSettings, toggleHints } = useAppStore();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 's' || e.key === 'S') {
        toggleSettings();
      } else if (e.key === 'h' || e.key === 'H') {
        toggleHints();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleSettings, toggleHints]);

  return (
    <div className="relative w-full h-full overflow-hidden bg-bg-primary">
      {/* Video layer */}
      <VideoFeed />

      {/* Clutch border overlay */}
      <ClutchBorder />

      {/* Status indicators */}
      <StatusPill />
      <RecordingIndicator />

      {/* Action feedback */}
      <ActionFeedback />

      {/* Gesture hints panel */}
      <GestureHints />

      {/* Settings panel */}
      <SettingsPanel onUpdateCommand={updateGestureCommand} />

      {/* Help hint */}
      <div className="absolute bottom-4 right-4 z-10">
        <p className="text-xs text-text-muted/50">
          <kbd className="px-1 rounded bg-bg-elevated/50">H</kbd> hints
          {' '}
          <kbd className="px-1 rounded bg-bg-elevated/50">S</kbd> settings
        </p>
      </div>
    </div>
  );
}

export default App;
