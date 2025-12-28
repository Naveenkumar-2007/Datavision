/**
 * Splash Screen Component - Premium Loading Experience
 * DataVision - Intelligent Data Analytics Platform
 */

import React from 'react';
import { motion } from 'framer-motion';

interface SplashScreenProps {
    onComplete?: () => void;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
    React.useEffect(() => {
        const timer = setTimeout(() => {
            onComplete?.();
        }, 2500);
        return () => clearTimeout(timer);
    }, [onComplete]);

    return (
        <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden"
            style={{
                background: 'linear-gradient(135deg, #0a0a0b 0%, #0f1419 25%, #1a1a2e 50%, #0f1419 75%, #0a0a0b 100%)',
            }}
        >
            {/* Animated Background Elements */}
            <div className="absolute inset-0 overflow-hidden">
                {/* Primary Glow */}
                <motion.div
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.3, 0.5, 0.3],
                    }}
                    transition={{
                        duration: 4,
                        repeat: Infinity,
                        ease: 'easeInOut',
                    }}
                    className="absolute top-1/4 left-1/3 w-[500px] h-[500px] rounded-full"
                    style={{
                        background: 'radial-gradient(circle, rgba(45, 212, 191, 0.2) 0%, transparent 70%)',
                        filter: 'blur(80px)',
                    }}
                />

                {/* Secondary Glow */}
                <motion.div
                    animate={{
                        scale: [1.2, 1, 1.2],
                        opacity: [0.2, 0.4, 0.2],
                    }}
                    transition={{
                        duration: 5,
                        repeat: Infinity,
                        ease: 'easeInOut',
                        delay: 0.5,
                    }}
                    className="absolute bottom-1/4 right-1/3 w-[400px] h-[400px] rounded-full"
                    style={{
                        background: 'radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%)',
                        filter: 'blur(80px)',
                    }}
                />

                {/* Particle Lines */}
                {[...Array(6)].map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ x: '-100%', opacity: 0 }}
                        animate={{
                            x: ['0%', '200%'],
                            opacity: [0, 0.3, 0],
                        }}
                        transition={{
                            duration: 3 + i * 0.5,
                            repeat: Infinity,
                            delay: i * 0.4,
                            ease: 'linear',
                        }}
                        className="absolute h-[1px]"
                        style={{
                            top: `${20 + i * 12}%`,
                            width: '150px',
                            background: 'linear-gradient(90deg, transparent, rgba(45, 212, 191, 0.5), transparent)',
                        }}
                    />
                ))}
            </div>

            {/* Main Content */}
            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
                className="relative flex flex-col items-center gap-8"
            >
                {/* Logo with Floating Animation */}
                <motion.div
                    animate={{
                        y: [0, -12, 0],
                    }}
                    transition={{
                        duration: 2.5,
                        repeat: Infinity,
                        ease: 'easeInOut',
                    }}
                    className="relative"
                >
                    {/* Logo Glow Effect */}
                    <motion.div
                        animate={{
                            scale: [1, 1.2, 1],
                            opacity: [0.4, 0.7, 0.4],
                        }}
                        transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: 'easeInOut',
                        }}
                        className="absolute inset-0 -m-8"
                        style={{
                            background: 'radial-gradient(circle, rgba(45, 212, 191, 0.4) 0%, transparent 70%)',
                            filter: 'blur(25px)',
                        }}
                    />

                    {/* Actual Logo Image */}
                    <img
                        src="/logo.png"
                        alt="DataVision"
                        className="relative z-10 w-24 h-24 md:w-32 md:h-32 object-contain"
                        style={{
                            filter: 'drop-shadow(0 0 20px rgba(45, 212, 191, 0.5))',
                        }}
                    />
                </motion.div>

                {/* Brand Name with Gradient */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, duration: 0.8 }}
                    className="text-center"
                >
                    <h1
                        className="text-4xl md:text-5xl font-bold tracking-tight mb-3"
                        style={{
                            background: 'linear-gradient(135deg, #f8fafc 0%, #2dd4bf 50%, #0d9488 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            textShadow: '0 0 40px rgba(45, 212, 191, 0.3)',
                        }}
                    >
                        DataVision
                    </h1>
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.7, duration: 0.6 }}
                        className="text-gray-400 text-base tracking-wider uppercase"
                        style={{ letterSpacing: '0.2em' }}
                    >
                        Intelligent Data Analytics
                    </motion.p>
                </motion.div>

                {/* Premium Loading Indicator */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1, duration: 0.5 }}
                    className="mt-6"
                >
                    {/* Progress Bar */}
                    <div className="relative w-48 h-1 bg-gray-800 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: '100%' }}
                            transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                ease: 'easeInOut',
                            }}
                            className="absolute inset-0 w-1/2"
                            style={{
                                background: 'linear-gradient(90deg, transparent, #2dd4bf, transparent)',
                            }}
                        />
                    </div>

                    {/* Loading Text */}
                    <motion.p
                        animate={{ opacity: [0.5, 1, 0.5] }}
                        transition={{
                            duration: 1.5,
                            repeat: Infinity,
                            ease: 'easeInOut',
                        }}
                        className="text-center text-gray-500 text-xs mt-4 tracking-widest uppercase"
                    >
                        Loading Experience
                    </motion.p>
                </motion.div>
            </motion.div>

            {/* Corner Accents */}
            <div className="absolute top-8 left-8 w-16 h-16 border-l-2 border-t-2 border-teal-500/20 rounded-tl-lg" />
            <div className="absolute top-8 right-8 w-16 h-16 border-r-2 border-t-2 border-teal-500/20 rounded-tr-lg" />
            <div className="absolute bottom-8 left-8 w-16 h-16 border-l-2 border-b-2 border-teal-500/20 rounded-bl-lg" />
            <div className="absolute bottom-8 right-8 w-16 h-16 border-r-2 border-b-2 border-teal-500/20 rounded-br-lg" />
        </motion.div>
    );
};

export default SplashScreen;
