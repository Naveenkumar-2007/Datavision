/**
 * DataVision Logo Component
 * Uses SVG icon for deployment compatibility
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
      {/* SVG Logo Icon */}
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
      >
        <rect width="64" height="64" rx="12" fill="url(#gradient)" />
        <path
          d="M20 44V24L32 18L44 24V44L32 50L20 44Z"
          stroke="white"
          strokeWidth="2.5"
          fill="none"
        />
        <path d="M32 18V50" stroke="white" strokeWidth="2" />
        <path d="M20 24L44 44" stroke="white" strokeWidth="2" />
        <path d="M44 24L20 44" stroke="white" strokeWidth="2" />
        <circle cx="32" cy="32" r="4" fill="white" />
        <defs>
          <linearGradient id="gradient" x1="0" y1="0" x2="64" y2="64">
            <stop stopColor="#10B981" />
            <stop offset="1" stopColor="#059669" />
          </linearGradient>
        </defs>
      </svg>

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
