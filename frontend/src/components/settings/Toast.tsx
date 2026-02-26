import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSettings } from '../../contexts/SettingsContext';

export default function Toast() {
  const { toastMessage, hideToast } = useSettings();

  useEffect(() => {
    if (!toastMessage) return;
    const timer = setTimeout(hideToast, 3000);
    return () => clearTimeout(timer);
  }, [toastMessage, hideToast]);

  return (
    <AnimatePresence>
      {toastMessage && (
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 40 }}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[200] px-6 py-3 bg-emerald-600 text-white text-sm font-semibold rounded-2xl shadow-lg shadow-emerald-200 dark:shadow-emerald-900/30"
        >
          {toastMessage}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
