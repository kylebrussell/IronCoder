import { motion, AnimatePresence } from 'framer-motion';
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

const GESTURE_ICONS: Record<GestureName, string> = {
  none: '',
  open_palm: '✋',
  peace_sign: '✌️',
  thumbs_up: '👍',
  thumbs_down: '👎',
  pointing: '👆',
  ok_sign: '👌',
  rock_sign: '🤘',
  shaka: '🤙',
  three_fingers: '3️⃣',
  four_fingers: '4️⃣',
};

const GESTURE_COLOR_CLASSES: Record<GestureName, string> = {
  none: 'from-bg-elevated to-bg-elevated',
  open_palm: 'from-gesture-palm/30 to-gesture-palm/10',
  peace_sign: 'from-gesture-peace/30 to-gesture-peace/10',
  thumbs_up: 'from-gesture-thumbup/30 to-gesture-thumbup/10',
  thumbs_down: 'from-gesture-thumbdown/30 to-gesture-thumbdown/10',
  pointing: 'from-gesture-point/30 to-gesture-point/10',
  ok_sign: 'from-gesture-ok/30 to-gesture-ok/10',
  rock_sign: 'from-gesture-rock/30 to-gesture-rock/10',
  shaka: 'from-gesture-shaka/30 to-gesture-shaka/10',
  three_fingers: 'from-gesture-three/30 to-gesture-three/10',
  four_fingers: 'from-gesture-four/30 to-gesture-four/10',
};

const GESTURE_ACCENT_CLASSES: Record<GestureName, string> = {
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

const GESTURE_TEXT_CLASSES: Record<GestureName, string> = {
  none: 'text-text-muted',
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

export function GestureHints() {
  const { showHints, gestureConfig, gesture } = useAppStore();

  return (
    <AnimatePresence>
      {showHints && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="absolute bottom-4 left-4 right-4 z-20"
        >
          <div className="glass-dark rounded-2xl p-4 shadow-2xl">
            <div className="grid grid-cols-5 gap-2">
              {GESTURE_ORDER.map((gestureName, index) => {
                const config = gestureConfig[gestureName];
                const isActive = gesture.currentGesture === gestureName;
                const description = config?.description || gestureName.replace('_', ' ');

                return (
                  <motion.div
                    key={gestureName}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.03 }}
                    className={`
                      relative overflow-hidden rounded-xl p-3
                      bg-gradient-to-b ${GESTURE_COLOR_CLASSES[gestureName]}
                      border border-border-subtle
                      transition-all duration-200
                      ${isActive ? 'ring-2 ring-white/30 scale-105' : ''}
                    `}
                  >
                    {/* Accent bar */}
                    <div className={`absolute top-0 left-0 right-0 h-1 ${GESTURE_ACCENT_CLASSES[gestureName]}`} />

                    {/* Icon */}
                    <div className="text-2xl mb-2 text-center">
                      {GESTURE_ICONS[gestureName]}
                    </div>

                    {/* Gesture name */}
                    <div className="text-xs font-medium text-text-primary text-center mb-1 truncate">
                      {gestureName.replace('_', ' ').toUpperCase()}
                    </div>

                    {/* Separator */}
                    <div className="h-px bg-border-subtle my-2" />

                    {/* Description/Command */}
                    <div className={`text-xs text-center truncate ${GESTURE_TEXT_CLASSES[gestureName]}`}>
                      {description}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
