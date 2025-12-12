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

  const { icon, text, subtitle } = sizes[size];

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Logo Image */}
      <div
        className="relative flex-shrink-0 rounded-xl overflow-hidden shadow-lg"
        style={{ width: icon, height: icon }}
      >
        <img
          src="/logo.png"
          alt="AI Business Analyst Logo"
          className="w-full h-full object-cover"
        />
      </div>

      {/* Text */}
      {showText && (
        <div className="flex flex-col">
          <span className={`font-bold bg-gradient-to-r from-orange-400 via-amber-400 to-orange-500 bg-clip-text text-transparent ${text} leading-tight`}>
            AI Business Analyst
          </span>
          <span className={`text-orange-300/70 ${subtitle} uppercase tracking-wider font-medium`}>
            Enterprise Edition
          </span>
        </div>
      )}
    </div>
  );
};

export default Logo;
