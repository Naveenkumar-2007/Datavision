/**
 * DataVision Logo Component - Theme-aware logo with light/dark mode support
 * Displays light mode logo on light backgrounds, dark mode logo on dark backgrounds
 */

import React from 'react';
import { useUserStore } from '../store/userStore';

interface LogoImageProps {
  className?: string;
  size?: number;
}

const LogoImage: React.FC<LogoImageProps> = ({ className = '', size = 48 }) => {
  const { isDark } = useUserStore();

  // Use dark logo (transparent background) for dark mode
  // Use light logo (light background) for light mode
  const logoSrc = isDark ? '/datavision-logo-dark.jpg' : '/datavision-logo-light.jpg';

  return (
    <img
      src={logoSrc}
      alt="DataVision Logo"
      width={size}
      height={size}
      className={className}
      style={{
        width: size,
        height: size,
        objectFit: 'contain',
        borderRadius: '8px',
      }}
    />
  );
};

export default LogoImage;
