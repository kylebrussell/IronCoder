import { motion } from 'framer-motion';
import { useAppStore } from '../store/useAppStore';

export function ClutchBorder() {
  const { clutch } = useAppStore();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{
        opacity: clutch.engaged ? 1 : 0.3,
      }}
      transition={{ duration: 0.2 }}
      className="absolute inset-0 pointer-events-none z-10"
      style={{
        boxShadow: clutch.engaged
          ? 'inset 0 0 0 3px rgba(158, 206, 106, 0.8), inset 0 0 30px rgba(158, 206, 106, 0.15)'
          : 'inset 0 0 0 1px rgba(86, 95, 137, 0.4)',
      }}
    />
  );
}
