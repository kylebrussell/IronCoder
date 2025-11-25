import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronDown, ChevronUp, Save } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import type { GestureName } from '../types';

const GESTURE_ORDER: GestureName[] = [
  'open_palm',
  'peace_sign',
  'thumbs_up',
  'thumbs_down',
  'pointing',
  'ok_sign',
  'rock_sign',
  'shaka',
  'three_fingers',
  'four_fingers',
];

const PRESET_COMMANDS = {
  claude: ['/help', '/clear', '/compact', '/cost', '/config'],
  dev: ['start the dev server', 'run the tests', 'build the project', 'kill the running server'],
  git: ['git status', 'git diff', 'git add .', 'git commit', 'git push'],
};

interface SettingsPanelProps {
  onUpdateCommand: (gesture: string, command: string, description?: string) => void;
}

export function SettingsPanel({ onUpdateCommand }: SettingsPanelProps) {
  const { showSettings, toggleSettings, gestureConfig, updateGestureCommand } = useAppStore();
  const [selectedGesture, setSelectedGesture] = useState<GestureName | null>(null);
  const [editCommand, setEditCommand] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [activePreset, setActivePreset] = useState<keyof typeof PRESET_COMMANDS>('claude');

  const handleEdit = (gesture: GestureName) => {
    const config = gestureConfig[gesture];
    if (config?.action) return; // Can't edit special actions
    setSelectedGesture(gesture);
    setEditCommand(config?.command || '');
    // Only pre-fill description if it's different from the command
    const desc = config?.description || '';
    setEditDescription(desc !== config?.command ? desc : '');
  };

  const handleSave = () => {
    if (selectedGesture && editCommand.trim()) {
      const description = editDescription.trim() || editCommand.trim();
      updateGestureCommand(selectedGesture, editCommand.trim(), description);
      onUpdateCommand(selectedGesture, editCommand.trim(), description);
    }
    setSelectedGesture(null);
    setEditCommand('');
    setEditDescription('');
  };

  const handleCancel = () => {
    setSelectedGesture(null);
    setEditCommand('');
    setEditDescription('');
  };

  const handlePresetSelect = (command: string) => {
    setEditCommand(command);
  };

  return (
    <AnimatePresence>
      {showSettings && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={toggleSettings}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm z-40"
          />

          {/* Panel */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="absolute inset-8 z-50 flex items-center justify-center"
          >
            <div className="w-full max-w-2xl max-h-full overflow-hidden glass rounded-2xl shadow-2xl">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-border-default bg-bg-secondary/50">
                <h2 className="text-lg font-semibold text-text-primary">Settings</h2>
                <button
                  onClick={toggleSettings}
                  className="p-2 rounded-lg hover:bg-bg-elevated transition-colors"
                >
                  <X className="w-5 h-5 text-text-secondary" />
                </button>
              </div>

              {/* Content */}
              <div className="p-4 max-h-[60vh] overflow-y-auto">
                <h3 className="text-sm font-medium text-text-muted mb-3 uppercase tracking-wider">
                  Gesture Mappings
                </h3>

                <div className="space-y-2">
                  {GESTURE_ORDER.map((gesture) => {
                    const config = gestureConfig[gesture];
                    const isSpecial = !!config?.action;
                    const isEditing = selectedGesture === gesture;

                    return (
                      <motion.div
                        key={gesture}
                        layout
                        className={`
                          rounded-xl border transition-all
                          ${isEditing ? 'border-accent-blue bg-accent-blue/10' : 'border-border-subtle bg-bg-secondary/30'}
                        `}
                      >
                        <div
                          className={`
                            flex items-center justify-between p-3
                            ${!isSpecial && !isEditing ? 'cursor-pointer hover:bg-bg-elevated/30' : ''}
                          `}
                          onClick={() => !isSpecial && !isEditing && handleEdit(gesture)}
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-accent-purple" />
                            <span className="font-medium text-text-primary">
                              {gesture.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            {isSpecial ? (
                              <span className="text-sm text-text-muted px-3 py-1 rounded-lg bg-bg-elevated">
                                [{config.action}]
                              </span>
                            ) : (
                              <div className="text-right">
                                <span className="text-sm text-accent-cyan truncate max-w-[200px] block">
                                  {config?.description || config?.command || 'Not set'}
                                </span>
                                {config?.description && config.description !== config.command && (
                                  <span className="text-xs text-text-muted truncate max-w-[200px] block">
                                    {config.command}
                                  </span>
                                )}
                              </div>
                            )}

                            {!isSpecial && (
                              isEditing ? (
                                <ChevronUp className="w-4 h-4 text-text-muted" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-text-muted" />
                              )
                            )}
                          </div>
                        </div>

                        {/* Edit panel */}
                        <AnimatePresence>
                          {isEditing && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="overflow-hidden"
                            >
                              <div className="p-3 pt-0 space-y-3">
                                {/* Command input */}
                                <div>
                                  <label className="block text-xs text-text-muted mb-1">Command</label>
                                  <input
                                    type="text"
                                    value={editCommand}
                                    onChange={(e) => setEditCommand(e.target.value)}
                                    placeholder="Enter command to execute..."
                                    className="w-full px-4 py-2 rounded-lg bg-bg-primary border border-border-default text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-blue/50"
                                    autoFocus
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter' && !e.shiftKey) handleSave();
                                      if (e.key === 'Escape') handleCancel();
                                    }}
                                  />
                                </div>

                                {/* Description input */}
                                <div>
                                  <label className="block text-xs text-text-muted mb-1">
                                    Label <span className="text-text-muted/50">(shown in hints, optional)</span>
                                  </label>
                                  <input
                                    type="text"
                                    value={editDescription}
                                    onChange={(e) => setEditDescription(e.target.value)}
                                    placeholder="e.g. Start Server, Run Tests..."
                                    className="w-full px-4 py-2 rounded-lg bg-bg-primary border border-border-default text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-blue/50"
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter' && !e.shiftKey) handleSave();
                                      if (e.key === 'Escape') handleCancel();
                                    }}
                                  />
                                </div>

                                {/* Presets */}
                                <div>
                                  <div className="flex gap-2 mb-2">
                                    {(Object.keys(PRESET_COMMANDS) as Array<keyof typeof PRESET_COMMANDS>).map((preset) => (
                                      <button
                                        key={preset}
                                        onClick={() => setActivePreset(preset)}
                                        className={`
                                          px-3 py-1 rounded-lg text-xs font-medium transition-colors
                                          ${activePreset === preset
                                            ? 'bg-accent-blue/20 text-accent-blue'
                                            : 'bg-bg-elevated text-text-muted hover:text-text-secondary'
                                          }
                                        `}
                                      >
                                        {preset.charAt(0).toUpperCase() + preset.slice(1)}
                                      </button>
                                    ))}
                                  </div>
                                  <div className="flex flex-wrap gap-2">
                                    {PRESET_COMMANDS[activePreset].map((cmd) => (
                                      <button
                                        key={cmd}
                                        onClick={() => handlePresetSelect(cmd)}
                                        className="px-2 py-1 rounded-md text-xs bg-bg-elevated text-text-secondary hover:bg-bg-primary hover:text-text-primary transition-colors"
                                      >
                                        {cmd}
                                      </button>
                                    ))}
                                  </div>
                                </div>

                                {/* Actions */}
                                <div className="flex justify-end gap-2">
                                  <button
                                    onClick={handleCancel}
                                    className="px-4 py-2 rounded-lg text-sm text-text-muted hover:bg-bg-elevated transition-colors"
                                  >
                                    Cancel
                                  </button>
                                  <button
                                    onClick={handleSave}
                                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-accent-blue/20 text-accent-blue hover:bg-accent-blue/30 transition-colors"
                                  >
                                    <Save className="w-4 h-4" />
                                    Save
                                  </button>
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    );
                  })}
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between p-4 border-t border-border-default bg-bg-secondary/30">
                <p className="text-xs text-text-muted">
                  Press <kbd className="px-1.5 py-0.5 rounded bg-bg-elevated text-text-secondary">S</kbd> to toggle settings
                </p>
                <button
                  onClick={toggleSettings}
                  className="px-4 py-2 rounded-lg text-sm bg-accent-green/20 text-accent-green hover:bg-accent-green/30 transition-colors"
                >
                  Done
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
