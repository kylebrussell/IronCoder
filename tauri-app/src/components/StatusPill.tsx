import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store/useAppStore';
import { GESTURE_DISPLAY_NAMES } from '../types';

export function StatusPill() {
  const { clutch, gesture, connected } = useAppStore();

  const getStatusConfig = () => {
    if (!connected) {
      return {
        text: 'OFFLINE',
        bgClass: 'bg-accent-red/20',
        textClass: 'text-accent-red',
        borderClass: 'border-accent-red/30',
      };
    }

    if (!clutch.engaged) {
      return {
        text: 'READY',
        bgClass: 'bg-bg-primary/90',
        textClass: 'text-text-secondary',
        borderClass: 'border-border-default',
      };
    }

    if (gesture.currentGesture && gesture.currentGesture !== 'none') {
      const gestureName = GESTURE_DISPLAY_NAMES[gesture.currentGesture];
      return {
        text: gestureName.toUpperCase(),
        bgClass: 'bg-accent-purple/20',
        textClass: 'text-accent-purple',
        borderClass: 'border-accent-purple/40',
      };
    }

    return {
      text: 'ENGAGED',
      bgClass: 'bg-clutch-engaged/20',
      textClass: 'text-clutch-engaged',
      borderClass: 'border-clutch-engaged/40',
    };
  };

  const config = getStatusConfig();

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="absolute top-4 left-4 z-20"
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={config.text}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.15 }}
          className={`
            px-4 py-2 rounded-full
            ${config.bgClass}
            border ${config.borderClass}
            backdrop-blur-xl
            shadow-lg shadow-black/30
          `}
        >
          <span
            className={`text-sm font-semibold tracking-wide ${config.textClass}`}
            style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
          >
            {config.text}
          </span>
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}
