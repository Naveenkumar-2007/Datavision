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
    animate = true,
    isDark = true
}) => {
    const sizes = {
        sm: { logo: 32, text: 'text-sm' },
        md: { logo: 48, text: 'text-lg' },
        lg: { logo: 72, text: 'text-2xl' },
        xl: { logo: 96, text: 'text-4xl' },
    };

    const currentSize = sizes[size];

    return (
        <div className="flex items-center gap-3">
            <motion.div
                animate={animate ? {
                    y: [0, -6, 0],
                } : {}}
                transition={{
                    duration: 2.5,
                    repeat: Infinity,
                    ease: 'easeInOut',
                }}
                className="relative"
                style={{
                    width: currentSize.logo,
                    height: currentSize.logo,
                }}
            >
                {/* Glow Effect Behind Logo */}
                <motion.div
                    animate={animate ? {
                        scale: [1, 1.15, 1],
                        opacity: [0.3, 0.5, 0.3],
                    } : {}}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: 'easeInOut',
                    }}
                    className="absolute inset-0 rounded-full"
                    style={{
                        background: 'radial-gradient(circle, rgba(45, 212, 191, 0.4) 0%, transparent 70%)',
                        filter: 'blur(12px)',
                        transform: 'scale(1.5)',
                    }}
                />

                {/* Logo Image with transparent background treatment */}
                <img
                    src="/logo.png"
                    alt="DataVision"
                    className="relative z-10 w-full h-full object-contain"
                    style={{
                        filter: isDark ? 'drop-shadow(0 0 8px rgba(45, 212, 191, 0.3))' : 'none',
                        mixBlendMode: isDark ? 'normal' : 'multiply'
                    }}
                />
            </motion.div>

            {showText && (
                <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                    className={`font-bold tracking-tight ${currentSize.text}`}
                    style={{
                        color: isDark ? '#ffffff' : '#0f172a', // Solid text color for perfect visibility
                    }}
                >
                    DataVision
                </motion.span>
            )}
        </div>
    );
};

export default AnimatedLogo;
