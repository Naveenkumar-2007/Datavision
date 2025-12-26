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
    sm: { icon: 28, text: 'text-sm', subtitle: 'text-[10px]' },
    md: { icon: 40, text: 'text-lg', subtitle: 'text-xs' },
    lg: { icon: 48, text: 'text-xl', subtitle: 'text-sm' },
    xl: { icon: 64, text: 'text-2xl', subtitle: 'text-base' },
  };

  const { icon, text } = sizes[size];

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Logo Image */}
      <img
        src="/logo.png"
        alt="DataVision Logo"
        className="flex-shrink-0 object-contain"
        style={{ width: icon, height: icon }}
      />

      {/* Text */}
      {showText && (
        <div className="flex flex-col">
          <span className={`font-bold text-gray-900 dark:text-gray-100 ${text} leading-tight`}>
            DataVision
          </span>
        </div>
      )}
    </div>
  );
};

export default Logo;
