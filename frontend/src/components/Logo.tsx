/**
 * DataVision Logo Component
 * Uses the new logo.png with optional text
 */

import React from 'react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 'md', showText = true, className = '' }) => {
  const sizes = {
    sm: { icon: 28, text: 'text-sm' },
    md: { icon: 36, text: 'text-xl' },
    lg: { icon: 48, text: 'text-2xl' },
    xl: { icon: 64, text: 'text-3xl' },
  };

  const { icon, text } = sizes[size];

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Logo Icon Only */}
      <img
        src="/datavision_icon_v3.png"
        alt="DataVision"
        className="object-contain"
        style={{ width: icon, height: icon }}
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
