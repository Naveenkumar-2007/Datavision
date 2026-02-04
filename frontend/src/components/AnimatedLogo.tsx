/**
 * Animated Logo Component - DataVision
 * Uses inline SVG for deployment compatibility
 */

import React from 'react';
import LogoImage from './LogoImage';

interface AnimatedLogoProps {
    size?: 'sm' | 'md' | 'lg' | 'xl';
    showText?: boolean;
    animate?: boolean;
    isDark?: boolean;
}

const AnimatedLogo: React.FC<AnimatedLogoProps> = ({
    size = 'md',
    showText = false,
    animate = false,
    isDark = true
}) => {
    const sizes = {
        sm: { logo: 32, text: 'text-lg' },
        md: { logo: 48, text: 'text-2xl' },
        lg: { logo: 64, text: 'text-3xl' },
        xl: { logo: 80, text: 'text-4xl' },
    };

    const currentSize = sizes[size];

    return (
        <div className="flex items-center gap-3">
            <div
                className="relative select-none"
                style={{
                    width: currentSize.logo,
                    height: currentSize.logo,
                    filter: isDark ? 'drop-shadow(0 0 12px rgba(34, 197, 94, 0.4))' : 'none'
                }}
            >
                <LogoImage size={currentSize.logo} />
            </div>

            {showText && (
                <div className={`font-bold tracking-tight ${currentSize.text} flex items-center`}>
                    <span style={{ fontFamily: "'Outfit', sans-serif", color: isDark ? '#ffffff' : '#0f172a' }}>
                        Data
                    </span>
                    <span style={{ fontFamily: "'Outfit', sans-serif", color: '#22c55e' }}>
                        Vision
                    </span>
                </div>
            )}
        </div>
    );
};

export default AnimatedLogo;
