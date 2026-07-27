import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const phrases = [
  "Advanced Dashboards",
  "Computer Vision AutoML",
  "AI Analytics",
  "Data-Native Intelligence",
  "Predictive Customer 360",
  "Business Autopilot"
];

export const TypewriterHero: React.FC = () => {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % phrases.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-[80px] flex items-center justify-center overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.div
          key={index}
          initial={{ y: 20, opacity: 0, filter: 'blur(8px)' }}
          animate={{ y: 0, opacity: 1, filter: 'blur(0px)' }}
          exit={{ y: -20, opacity: 0, filter: 'blur(8px)' }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
          className="text-5xl md:text-7xl font-extrabold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"
        >
          {phrases[index]}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};
