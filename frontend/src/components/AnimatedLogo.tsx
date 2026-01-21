/**
 * Animated Logo Component - DataVision
 * Uses the actual logo with transparent background treatment
 * Adds gentle floating animation to the logo
 */

import React from 'react';
import { motion } from 'framer-motion';

interface AnimatedLogoProps {
    size?: 'sm' | 'md' | 'lg' | 'xl';
    showText?: boolean;
    animate?: boolean;
    isDark?: boolean;
}

const AnimatedLogo: React.FC<AnimatedLogoProps> = ({
    size = 'md',
    showText = false,
    animate = false, // Keep disabled for professional feel
    isDark = true
}) => {
    // Sizes are adjusted for the ICON only
    const sizes = {
        sm: { logo: 32, text: 'text-lg' },
        md: { logo: 48, text: 'text-2xl' },
        lg: { logo: 64, text: 'text-3xl' },
        xl: { logo: 80, text: 'text-4xl' },
    };

    const currentSize = sizes[size];

    return (
        <div className="flex items-center gap-3">
            {/* Static Logo Icon */}
            <div
                className="relative select-none"
                style={{
                    width: currentSize.logo,
                    height: currentSize.logo,
                }}
            >
                <img
                    src="/datavision_icon_v3.png"
                    alt="DataVision Icon"
                    className="w-full h-full object-contain"
                    style={{
                        // Icon is green, works on both. 
                        // Optional: Add drop shadow in dark mode for pop
                        filter: isDark ? 'drop-shadow(0 0 12px rgba(34, 197, 94, 0.4))' : 'none'
                    }}
                />
            </div>

            {/* Render Text in Code for Perfect Theme Contrast & Brand Match */}
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
