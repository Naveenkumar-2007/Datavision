import React, { useEffect, useState, useRef } from 'react';
import { motion, useInView, useSpring, useTransform } from 'framer-motion';
import { useUserStore } from '@/store/userStore';

interface AnimatedCounterProps {
  value: number;
  label: string;
  prefix?: string;
  suffix?: string;
  delay?: number;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  value,
  label,
  prefix = '',
  suffix = '',
  delay = 0,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });
  const { isDark } = useUserStore();
  const [hasAnimated, setHasAnimated] = useState(false);

  const spring = useSpring(0, {
    stiffness: 50,
    damping: 20,
    mass: 1,
  });

  const display = useTransform(spring, (current) => {
    return Math.round(current).toLocaleString();
  });

  useEffect(() => {
    if (isInView && !hasAnimated) {
      setTimeout(() => {
        spring.set(value);
        setHasAnimated(true);
      }, delay * 1000);
    }
  }, [isInView, spring, value, delay, hasAnimated]);

  const textColor = isDark ? 'text-white' : 'text-gray-900';
  const labelColor = isDark ? 'text-gray-400' : 'text-gray-500';

  return (
    <div ref={ref} className="flex flex-col items-center justify-center p-6 text-center">
      <div className={`text-4xl md:text-5xl font-black mb-2 flex items-center ${textColor}`}>
        <span>{prefix}</span>
        <motion.span>{display}</motion.span>
        <span>{suffix}</span>
      </div>
      <div className={`text-sm md:text-base font-medium tracking-wide uppercase ${labelColor}`}>
        {label}
      </div>
    </div>
  );
};
