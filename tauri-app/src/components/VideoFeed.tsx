import { useAppStore } from '../store/useAppStore';

export function VideoFeed() {
  const { currentFrame, connected } = useAppStore();

  return (
    <div className="absolute inset-0 overflow-hidden bg-bg-primary">
      {currentFrame ? (
        <img
          src={`data:image/jpeg;base64,${currentFrame}`}
          alt="Camera feed"
          className="w-full h-full object-cover"
          style={{ transform: 'scaleX(-1)' }} // Mirror effect
        />
      ) : (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4 opacity-20">
              {connected ? '📷' : '🔌'}
            </div>
            <p className="text-text-muted text-lg">
              {connected ? 'Waiting for video feed...' : 'Connecting to gesture service...'}
            </p>
            {!connected && (
              <p className="text-text-muted text-sm mt-2 opacity-60">
                Make sure the Python backend is running
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
