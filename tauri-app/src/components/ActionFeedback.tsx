import { motion, AnimatePresence } from 'framer-motion';
import { useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Check } from 'lucide-react';

const ACTION_DISPLAY_DURATION = 2000;

export function ActionFeedback() {
  const { lastAction, clearAction } = useAppStore();

  useEffect(() => {
    if (lastAction) {
      const timer = setTimeout(clearAction, ACTION_DISPLAY_DURATION);
      return () => clearTimeout(timer);
    }
  }, [lastAction, clearAction]);

  return (
    <AnimatePresence>
      {lastAction && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.9 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="absolute top-1/3 left-1/2 -translate-x-1/2 z-30"
        >
          <div className="flex items-center gap-3 px-6 py-4 rounded-2xl bg-accent-green/20 border border-accent-green/40 backdrop-blur-xl shadow-2xl">
            <div className="w-8 h-8 rounded-full bg-accent-green/30 flex items-center justify-center">
              <Check className="w-5 h-5 text-accent-green" />
            </div>
            <span className="text-lg font-medium text-text-primary">
              {lastAction.text}
            </span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
