/**
 * DataVision Logo Component - Theme-aware
 * Uses the official logo images with automatic light/dark mode switching
 */

import React from 'react';
import { useUserStore } from '../store/userStore';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 'md', showText = true, className = '' }) => {
  const { isDark } = useUserStore();

  const sizes = {
    sm: { icon: 28, text: 'text-sm' },
    md: { icon: 36, text: 'text-xl' },
    lg: { icon: 48, text: 'text-2xl' },
    xl: { icon: 64, text: 'text-3xl' },
  };

  const { icon, text } = sizes[size];

  // Use dark logo for dark mode, light logo for light mode
  const logoSrc = isDark ? '/datavision-logo-dark.jpg' : '/datavision-logo-light.jpg';

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Logo Image */}
      <img
        src={logoSrc}
        alt="DataVision Logo"
        width={icon}
        height={icon}
        className="flex-shrink-0"
        style={{
          width: icon,
          height: icon,
          objectFit: 'contain',
          borderRadius: '6px',
        }}
      />

      {/* Dynamic Text - Data(Theme) + Vision(Green) */}
      {showText && (
        <div className={`font-bold ${text} tracking-tight flex items-center`}>
          <span style={{ color: 'var(--text-primary)', fontFamily: "'Outfit', sans-serif" }}>
            Data
          </span>
          <span className="text-emerald-500" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Vision
          </span>
        </div>
      )}
    </div>
  );
};

export default Logo;
