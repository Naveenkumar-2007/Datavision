import React from 'react';
import { useUserStore } from '../store/userStore';

interface LogoImageProps {
  className?: string;
  size?: number;
  showText?: boolean;
  isDark?: boolean;
}

const LogoImage: React.FC<LogoImageProps> = ({ 
  className = '', 
  size = 36, 
  showText = true, 
  isDark: forceDark 
}) => {
  const { isDark: storeIsDark } = useUserStore();
  const isDark = forceDark !== undefined ? forceDark : storeIsDark;

  // Theme-aware logo assets: dark mode logo asset on dark mode, light mode logo asset on light mode
  const logoSrc = isDark ? '/datavision-logo-dark.png' : '/datavision-logo-light.png';

  return (
    <div className={`flex items-center gap-2.5 select-none font-sans ${className}`}>
      <img
        src={logoSrc}
        alt="DataVision Logo"
        width={size}
        height={size}
        className="object-contain rounded-lg shrink-0 shadow-xs transition-opacity duration-300"
        style={{ width: size, height: size }}
      />
      {showText && (
        <span className={`font-black tracking-tight text-xl ${isDark ? 'text-white' : 'text-[#111827]'}`}>
          DataVision
        </span>
      )}
    </div>
  );
};

export default LogoImage;
