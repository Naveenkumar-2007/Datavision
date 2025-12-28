/**
 * Theme Hook - Shared theme state
 * Pure dark theme with teal/green accents
 */

import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react';

interface ThemeColors {
    bgColor: string;
    cardBg: string;
    textPrimary: string;
    textMuted: string;
    borderColor: string;
    accentColor: string;
    isDark: boolean;
}

interface ThemeContextType extends ThemeColors {
    toggleTheme: () => void;
}

const darkColors: ThemeColors = {
    bgColor: '#0a0a0b',
    cardBg: '#141414',
    textPrimary: '#F8FAFC',
    textMuted: '#9CA3AF',
    borderColor: '#262626',
    accentColor: '#14B8A6',
    isDark: true,
};

const lightColors: ThemeColors = {
    bgColor: '#F8FAFC',
    cardBg: '#FFFFFF',
    textPrimary: '#0F172A',
    textMuted: '#64748B',
    borderColor: '#E2E8F0',
    accentColor: '#0D9488',
    isDark: false,
};

const ThemeContext = createContext<ThemeContextType | null>(null);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [isDark, setIsDark] = useState(true);

    useEffect(() => {
        const saved = localStorage.getItem('theme');
        const prefersDark = saved !== 'light';
        setIsDark(prefersDark);
        if (!prefersDark) {
            document.documentElement.classList.add('light-theme');
        }
    }, []);

    const toggleTheme = () => {
        const newIsDark = !isDark;
        setIsDark(newIsDark);
        if (newIsDark) {
            document.documentElement.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
        }
    };

    const colors = isDark ? darkColors : lightColors;

    return (
        <ThemeContext.Provider value={{ ...colors, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};

export const useTheme = (): ThemeContextType => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within ThemeProvider');
    }
    return context;
};

export default useTheme;
