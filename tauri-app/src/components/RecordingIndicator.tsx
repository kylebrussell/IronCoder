import { motion, AnimatePresence } from 'framer-motion';
import { Mic } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export function RecordingIndicator() {
  const { isDictating } = useAppStore();

  return (
    <AnimatePresence>
      {isDictating && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          className="absolute top-4 right-4 z-20"
        >
          <div className="flex items-center gap-2 px-3 py-2 rounded-full bg-recording/20 border border-recording/40 backdrop-blur-md">
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                opacity: [1, 0.6, 1],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              <Mic className="w-4 h-4 text-recording" />
            </motion.div>
            <span className="text-sm font-medium text-recording">REC</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
