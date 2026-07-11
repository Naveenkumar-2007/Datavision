import React from 'react';
import { motion } from 'framer-motion';

interface BackgroundPatternProps {
    pattern?: string;
    accentColor?: string;
    isDark?: boolean;
}

export const BackgroundPattern: React.FC<BackgroundPatternProps> = ({ 
    pattern = 'none', 
    accentColor = '#3b82f6',
    isDark = true
}) => {
    if (pattern === 'none') return null;

    const opacity = isDark ? 0.15 : 0.08;

    const getPattern = () => {
        switch (pattern) {
            case 'grid':
                return (
                    <div className="absolute inset-0 pointer-events-none" style={{
                        backgroundImage: `linear-gradient(${accentColor} 1px, transparent 1px), linear-gradient(90deg, ${accentColor} 1px, transparent 1px)`,
                        backgroundSize: '40px 40px',
                        opacity: opacity
                    }} />
                );
            case 'dots':
                return (
                    <div className="absolute inset-0 pointer-events-none" style={{
                        backgroundImage: `radial-gradient(${accentColor} 2px, transparent 2px)`,
                        backgroundSize: '30px 30px',
                        opacity: opacity
                    }} />
                );
            case 'stripes':
                return (
                    <div className="absolute inset-0 pointer-events-none" style={{
                        backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 10px, ${accentColor} 10px, ${accentColor} 11px)`,
                        opacity: opacity
                    }} />
                );
            case 'radial':
                return (
                    <div className="absolute inset-0 pointer-events-none" style={{
                        background: `radial-gradient(circle at 50% 0%, ${accentColor}40 0%, transparent 60%)`,
                        opacity: 0.8
                    }} />
                );
            case 'mesh':
                return (
                    <div className="absolute inset-0 pointer-events-none overflow-hidden">
                        <motion.div 
                            animate={{ x: [0, 100, 0], y: [0, -50, 0] }} 
                            transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                            className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full blur-[100px]"
                            style={{ backgroundColor: accentColor, opacity: opacity * 2 }} 
                        />
                        <motion.div 
                            animate={{ x: [0, -100, 0], y: [0, 100, 0] }} 
                            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                            className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full blur-[120px]"
                            style={{ backgroundColor: accentColor, opacity: opacity * 1.5 }} 
                        />
                    </div>
                );
            case 'aurora':
                return (
                    <div className="absolute inset-0 pointer-events-none overflow-hidden">
                        <motion.div 
                            animate={{ rotate: [0, 360] }} 
                            transition={{ duration: 50, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-[-50%] blur-[100px] opacity-30"
                            style={{
                                background: `conic-gradient(from 0deg at 50% 50%, ${accentColor}00 0deg, ${accentColor}80 120deg, ${accentColor}00 240deg)`
                            }} 
                        />
                    </div>
                );
            case 'waves':
                return (
                    <div className="absolute inset-x-0 bottom-0 pointer-events-none overflow-hidden h-[40vh] opacity-20">
                        <svg viewBox="0 0 1440 320" preserveAspectRatio="none" className="absolute bottom-0 w-full h-full">
                            <path fill={accentColor} fillOpacity="1" d="M0,192L48,197.3C96,203,192,213,288,229.3C384,245,480,267,576,250.7C672,235,768,181,864,181.3C960,181,1056,235,1152,234.7C1248,235,1344,181,1392,154.7L1440,128L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path>
                        </svg>
                    </div>
                );
            case 'topography':
                // Using a simplified SVG pattern for topography
                return (
                    <div className="absolute inset-0 pointer-events-none" style={{
                        backgroundImage: `url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%239C92AC' fill-opacity='1' fill-rule='evenodd'/%3E%3C/svg%3E")`,
                        opacity: opacity * 1.5,
                        filter: `opacity(0.8) drop-shadow(0 0 0 ${accentColor})`
                    }} />
                );
            case 'particles':
                return (
                    <div className="absolute inset-0 pointer-events-none overflow-hidden">
                        {[...Array(20)].map((_, i) => (
                            <motion.div
                                key={i}
                                className="absolute rounded-full"
                                style={{
                                    backgroundColor: accentColor,
                                    width: Math.random() * 4 + 2,
                                    height: Math.random() * 4 + 2,
                                    left: `${Math.random() * 100}%`,
                                    top: `${Math.random() * 100}%`,
                                    opacity: opacity * 3
                                }}
                                animate={{
                                    y: [0, Math.random() * -100 - 50],
                                    x: [0, (Math.random() - 0.5) * 50],
                                    opacity: [0, opacity * 3, 0]
                                }}
                                transition={{
                                    duration: Math.random() * 10 + 10,
                                    repeat: Infinity,
                                    delay: Math.random() * 5
                                }}
                            />
                        ))}
                    </div>
                );
            case 'circuit':
            case 'boxes':
            case 'honeycomb':
                // Using fallback CSS patterns for these specific complex geometric requests
                const size = pattern === 'honeycomb' ? '60px 104px' : '40px 40px';
                const bgImage = pattern === 'honeycomb' 
                    ? `radial-gradient(circle at 50% 50%, transparent 50%, ${accentColor} 55%)`
                    : `linear-gradient(45deg, ${accentColor} 25%, transparent 25%, transparent 75%, ${accentColor} 75%, ${accentColor}), linear-gradient(45deg, ${accentColor} 25%, transparent 25%, transparent 75%, ${accentColor} 75%, ${accentColor})`;
                
                return (
                    <div className="absolute inset-0 pointer-events-none" style={{
                        backgroundImage: bgImage,
                        backgroundSize: size,
                        backgroundPosition: pattern === 'boxes' ? '0 0, 20px 20px' : '0 0',
                        opacity: opacity * 0.5
                    }} />
                );
            default:
                return null;
        }
    };

    return (
        <div className="fixed inset-0 pointer-events-none z-0 mix-blend-screen overflow-hidden">
            {getPattern()}
        </div>
    );
};
