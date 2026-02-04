import React, { useEffect, useState } from 'react';
import LogoImage from './LogoImage';

interface SplashScreenProps {
  onComplete?: () => void;
  duration?: number;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete, duration = 2000 }) => {
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    const fadeTimer = setTimeout(() => {
      setFadeOut(true);
    }, duration - 500);

    const completeTimer = setTimeout(() => {
      onComplete?.();
    }, duration);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(completeTimer);
    };
  }, [duration, onComplete]);

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-slate-900 via-emerald-900 to-slate-900 transition-opacity duration-500 ${fadeOut ? 'opacity-0' : 'opacity-100'
        }`}
    >
      <div className="text-center">
        {/* Logo/Icon */}
        <div className="mb-6 flex justify-center">
          <div className="relative">
            <div className="w-20 h-20 rounded-2xl bg-white/10 backdrop-blur flex items-center justify-center shadow-2xl overflow-hidden">
              <LogoImage size={64} className="rounded-lg" />
            </div>
            {/* Animated ring */}
            <div className="absolute inset-0 w-20 h-20 rounded-2xl border-2 border-emerald-400/30 animate-ping" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-white mb-2">
          <span>Data</span>
          <span className="text-emerald-400">Vision</span>
        </h1>
        <p className="text-gray-400 text-sm mb-8">
          Enterprise Analytics Platform
        </p>

        {/* Loading indicator */}
        <div className="flex justify-center space-x-2">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-lime-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
};

export default SplashScreen;
