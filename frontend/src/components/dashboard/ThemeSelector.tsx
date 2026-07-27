import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Palette, Check, X, Sparkles, Sun, Moon, Droplets, Flame, Trees, Gem, Zap, Eye, ChevronDown, Paintbrush } from 'lucide-react';

/* ===================================================================
   DASHBOARD THEME SYSTEM
   12 premium themes + custom theme builder
   =================================================================== */

export interface DashboardTheme {
    id: string;
    name: string;
    icon: React.ReactNode;
    preview: { bg: string; card: string; accent: string; text: string };
    colors: {
        bg: string;
        bgSecondary: string;
        cardBg: string;
        cardBorder: string;
        textPrimary: string;
        textSecondary: string;
        textMuted: string;
        accent: string;
        accentSecondary: string;
        chartColors: string[];
        kpiBg: string;
        kpiBorder: string;
        headerBg: string;
        sidebarBg: string;
        hoverBg: string;
        shadowColor: string;
        gradientFrom: string;
        gradientTo: string;
    };
    isDark: boolean;
}

export const DASHBOARD_THEMES: DashboardTheme[] = [
    {
        id: 'midnight',
        name: 'Midnight',
        icon: <Moon className="w-4 h-4" />,
        preview: { bg: '#0b1120', card: '#151e32', accent: '#38bdf8', text: '#f8fafc' },
        colors: {
            bg: '#0b1120', bgSecondary: '#0f172a', cardBg: '#151e32', cardBorder: '#2a3441',
            textPrimary: '#f8fafc', textSecondary: '#e2e8f0', textMuted: '#94a3b8',
            accent: '#38bdf8', accentSecondary: '#818cf8',
            chartColors: ['#38bdf8', '#818cf8', '#34d399', '#fbbf24', '#f472b6', '#a78bfa', '#22d3ee', '#fb923c'],
            kpiBg: 'rgba(56,189,248,0.08)', kpiBorder: 'rgba(56,189,248,0.2)',
            headerBg: '#0f172a', sidebarBg: '#0b1120', hoverBg: 'rgba(255,255,255,0.05)',
            shadowColor: 'rgba(0,0,0,0.5)', gradientFrom: '#0b1120', gradientTo: '#1e1b4b'
        },
        isDark: true
    },
    {
        id: 'ocean',
        name: 'Ocean',
        icon: <Droplets className="w-4 h-4" />,
        preview: { bg: '#0c1929', card: '#112240', accent: '#64ffda', text: '#ccd6f6' },
        colors: {
            bg: '#0c1929', bgSecondary: '#112240', cardBg: '#112240', cardBorder: '#1d3a5c',
            textPrimary: '#ccd6f6', textSecondary: '#a8b2d1', textMuted: '#8892b0',
            accent: '#64ffda', accentSecondary: '#57cbff',
            chartColors: ['#64ffda', '#57cbff', '#ff6b9d', '#ffd93d', '#6c5ce7', '#a29bfe', '#00cec9', '#fdcb6e'],
            kpiBg: 'rgba(100,255,218,0.08)', kpiBorder: 'rgba(100,255,218,0.2)',
            headerBg: '#0c1929', sidebarBg: '#0a192f', hoverBg: 'rgba(100,255,218,0.05)',
            shadowColor: 'rgba(0,0,0,0.6)', gradientFrom: '#0a192f', gradientTo: '#112240'
        },
        isDark: true
    },
    {
        id: 'sunset',
        name: 'Sunset',
        icon: <Flame className="w-4 h-4" />,
        preview: { bg: '#1a0a1e', card: '#2d1233', accent: '#ff6b6b', text: '#fce4ec' },
        colors: {
            bg: '#1a0a1e', bgSecondary: '#2d1233', cardBg: '#2d1233', cardBorder: '#4a1942',
            textPrimary: '#fce4ec', textSecondary: '#f8bbd0', textMuted: '#ce93d8',
            accent: '#ff6b6b', accentSecondary: '#ff9a9e',
            chartColors: ['#ff6b6b', '#ffa726', '#ffca28', '#ff7043', '#e91e63', '#ab47bc', '#f48fb1', '#ff8a65'],
            kpiBg: 'rgba(255,107,107,0.08)', kpiBorder: 'rgba(255,107,107,0.2)',
            headerBg: '#2d1233', sidebarBg: '#1a0a1e', hoverBg: 'rgba(255,107,107,0.05)',
            shadowColor: 'rgba(26,10,30,0.7)', gradientFrom: '#1a0a1e', gradientTo: '#4a1942'
        },
        isDark: true
    },
    {
        id: 'forest',
        name: 'Forest',
        icon: <Trees className="w-4 h-4" />,
        preview: { bg: '#0d1f0d', card: '#1a3a1a', accent: '#4ade80', text: '#dcfce7' },
        colors: {
            bg: '#0d1f0d', bgSecondary: '#1a3a1a', cardBg: '#1a3a1a', cardBorder: '#2d5a2d',
            textPrimary: '#dcfce7', textSecondary: '#bbf7d0', textMuted: '#86efac',
            accent: '#4ade80', accentSecondary: '#22d3ee',
            chartColors: ['#4ade80', '#22d3ee', '#fbbf24', '#fb923c', '#a78bfa', '#f472b6', '#34d399', '#84cc16'],
            kpiBg: 'rgba(74,222,128,0.08)', kpiBorder: 'rgba(74,222,128,0.2)',
            headerBg: '#1a3a1a', sidebarBg: '#0d1f0d', hoverBg: 'rgba(74,222,128,0.05)',
            shadowColor: 'rgba(13,31,13,0.7)', gradientFrom: '#0d1f0d', gradientTo: '#1a3a1a'
        },
        isDark: true
    },
    {
        id: 'neon',
        name: 'Neon',
        icon: <Zap className="w-4 h-4" />,
        preview: { bg: '#0a0a0a', card: '#1a1a2e', accent: '#00ff88', text: '#e0e0e0' },
        colors: {
            bg: '#0a0a0a', bgSecondary: '#1a1a2e', cardBg: '#1a1a2e', cardBorder: '#2a2a4e',
            textPrimary: '#e0e0e0', textSecondary: '#b0b0b0', textMuted: '#808080',
            accent: '#00ff88', accentSecondary: '#ff00ff',
            chartColors: ['#00ff88', '#ff00ff', '#00bfff', '#ffff00', '#ff6600', '#ff0066', '#66ff66', '#9966ff'],
            kpiBg: 'rgba(0,255,136,0.08)', kpiBorder: 'rgba(0,255,136,0.2)',
            headerBg: '#0a0a0a', sidebarBg: '#0a0a0a', hoverBg: 'rgba(0,255,136,0.05)',
            shadowColor: 'rgba(0,0,0,0.8)', gradientFrom: '#0a0a0a', gradientTo: '#16213e'
        },
        isDark: true
    },
    {
        id: 'corporate',
        name: 'Corporate',
        icon: <Eye className="w-4 h-4" />,
        preview: { bg: '#ffffff', card: '#f8fafc', accent: '#2563eb', text: '#1e293b' },
        colors: {
            bg: '#ffffff', bgSecondary: '#f8fafc', cardBg: '#ffffff', cardBorder: '#e2e8f0',
            textPrimary: '#1e293b', textSecondary: '#334155', textMuted: '#64748b',
            accent: '#2563eb', accentSecondary: '#7c3aed',
            chartColors: ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#9333ea', '#0891b2', '#ca8a04'],
            kpiBg: 'rgba(37,99,235,0.06)', kpiBorder: 'rgba(37,99,235,0.15)',
            headerBg: '#ffffff', sidebarBg: '#f8fafc', hoverBg: 'rgba(37,99,235,0.05)',
            shadowColor: 'rgba(0,0,0,0.08)', gradientFrom: '#f8fafc', gradientTo: '#e2e8f0'
        },
        isDark: false
    },
    {
        id: 'pearl',
        name: 'Pearl',
        icon: <Gem className="w-4 h-4" />,
        preview: { bg: '#fafaf9', card: '#ffffff', accent: '#0d9488', text: '#292524' },
        colors: {
            bg: '#fafaf9', bgSecondary: '#f5f5f4', cardBg: '#ffffff', cardBorder: '#e7e5e4',
            textPrimary: '#292524', textSecondary: '#44403c', textMuted: '#78716c',
            accent: '#0d9488', accentSecondary: '#6366f1',
            chartColors: ['#0d9488', '#6366f1', '#ea580c', '#ca8a04', '#db2777', '#4f46e5', '#0891b2', '#65a30d'],
            kpiBg: 'rgba(13,148,136,0.06)', kpiBorder: 'rgba(13,148,136,0.15)',
            headerBg: '#fafaf9', sidebarBg: '#f5f5f4', hoverBg: 'rgba(13,148,136,0.05)',
            shadowColor: 'rgba(0,0,0,0.06)', gradientFrom: '#fafaf9', gradientTo: '#f5f5f4'
        },
        isDark: false
    },
    {
        id: 'lavender',
        name: 'Lavender',
        icon: <Sparkles className="w-4 h-4" />,
        preview: { bg: '#f5f3ff', card: '#ffffff', accent: '#8b5cf6', text: '#3b0764' },
        colors: {
            bg: '#f5f3ff', bgSecondary: '#ede9fe', cardBg: '#ffffff', cardBorder: '#ddd6fe',
            textPrimary: '#3b0764', textSecondary: '#581c87', textMuted: '#7c3aed',
            accent: '#8b5cf6', accentSecondary: '#ec4899',
            chartColors: ['#8b5cf6', '#ec4899', '#06b6d4', '#f59e0b', '#10b981', '#3b82f6', '#a855f7', '#f43f5e'],
            kpiBg: 'rgba(139,92,246,0.06)', kpiBorder: 'rgba(139,92,246,0.15)',
            headerBg: '#f5f3ff', sidebarBg: '#ede9fe', hoverBg: 'rgba(139,92,246,0.05)',
            shadowColor: 'rgba(0,0,0,0.05)', gradientFrom: '#f5f3ff', gradientTo: '#ede9fe'
        },
        isDark: false
    },
    {
        id: 'aurora',
        name: 'Aurora',
        icon: <Sparkles className="w-4 h-4" />,
        preview: { bg: '#0f0f23', card: '#1a1a3e', accent: '#00d4ff', text: '#e8e8ff' },
        colors: {
            bg: '#0f0f23', bgSecondary: '#1a1a3e', cardBg: '#1a1a3e', cardBorder: '#2d2d5e',
            textPrimary: '#e8e8ff', textSecondary: '#b8b8e0', textMuted: '#8888b0',
            accent: '#00d4ff', accentSecondary: '#ff6bcb',
            chartColors: ['#00d4ff', '#ff6bcb', '#7cff6b', '#ffd700', '#ff4500', '#9b59b6', '#1abc9c', '#e74c3c'],
            kpiBg: 'rgba(0,212,255,0.08)', kpiBorder: 'rgba(0,212,255,0.2)',
            headerBg: '#0f0f23', sidebarBg: '#0a0a1a', hoverBg: 'rgba(0,212,255,0.05)',
            shadowColor: 'rgba(0,0,0,0.7)', gradientFrom: '#0f0f23', gradientTo: '#1a0a3e'
        },
        isDark: true
    },
    {
        id: 'rose-gold',
        name: 'Rose Gold',
        icon: <Gem className="w-4 h-4" />,
        preview: { bg: '#1c1017', card: '#2d1a24', accent: '#f9a8d4', text: '#fce7f3' },
        colors: {
            bg: '#1c1017', bgSecondary: '#2d1a24', cardBg: '#2d1a24', cardBorder: '#4a2d3a',
            textPrimary: '#fce7f3', textSecondary: '#f9a8d4', textMuted: '#f472b6',
            accent: '#f9a8d4', accentSecondary: '#fbbf24',
            chartColors: ['#f9a8d4', '#fbbf24', '#38bdf8', '#a78bfa', '#34d399', '#fb923c', '#e879f9', '#22d3ee'],
            kpiBg: 'rgba(249,168,212,0.08)', kpiBorder: 'rgba(249,168,212,0.2)',
            headerBg: '#2d1a24', sidebarBg: '#1c1017', hoverBg: 'rgba(249,168,212,0.05)',
            shadowColor: 'rgba(28,16,23,0.7)', gradientFrom: '#1c1017', gradientTo: '#2d1a24'
        },
        isDark: true
    },
    {
        id: 'arctic',
        name: 'Arctic',
        icon: <Sun className="w-4 h-4" />,
        preview: { bg: '#f0f9ff', card: '#ffffff', accent: '#0284c7', text: '#0c4a6e' },
        colors: {
            bg: '#f0f9ff', bgSecondary: '#e0f2fe', cardBg: '#ffffff', cardBorder: '#bae6fd',
            textPrimary: '#0c4a6e', textSecondary: '#075985', textMuted: '#0369a1',
            accent: '#0284c7', accentSecondary: '#0891b2',
            chartColors: ['#0284c7', '#0891b2', '#059669', '#d97706', '#dc2626', '#7c3aed', '#2563eb', '#ea580c'],
            kpiBg: 'rgba(2,132,199,0.06)', kpiBorder: 'rgba(2,132,199,0.15)',
            headerBg: '#f0f9ff', sidebarBg: '#e0f2fe', hoverBg: 'rgba(2,132,199,0.05)',
            shadowColor: 'rgba(0,0,0,0.06)', gradientFrom: '#f0f9ff', gradientTo: '#e0f2fe'
        },
        isDark: false
    },
    {
        id: 'charcoal',
        name: 'Charcoal',
        icon: <Moon className="w-4 h-4" />,
        preview: { bg: '#1c1c1c', card: '#2a2a2a', accent: '#ff9f43', text: '#e8e8e8' },
        colors: {
            bg: '#1c1c1c', bgSecondary: '#2a2a2a', cardBg: '#2a2a2a', cardBorder: '#3d3d3d',
            textPrimary: '#e8e8e8', textSecondary: '#c0c0c0', textMuted: '#909090',
            accent: '#ff9f43', accentSecondary: '#ee5a24',
            chartColors: ['#ff9f43', '#ee5a24', '#0abde3', '#10ac84', '#f368e0', '#48dbfb', '#ff6b6b', '#feca57'],
            kpiBg: 'rgba(255,159,67,0.08)', kpiBorder: 'rgba(255,159,67,0.2)',
            headerBg: '#1c1c1c', sidebarBg: '#1c1c1c', hoverBg: 'rgba(255,159,67,0.05)',
            shadowColor: 'rgba(0,0,0,0.7)', gradientFrom: '#1c1c1c', gradientTo: '#2d2d2d'
        },
        isDark: true
    },
    {
        id: 'cloud',
        name: 'Cloud White',
        icon: <Sun className="w-4 h-4" />,
        preview: { bg: '#ffffff', card: '#ffffff', accent: '#10b981', text: '#0f172a' },
        colors: {
            bg: '#ffffff', bgSecondary: '#f8fafc', cardBg: '#ffffff', cardBorder: '#e2e8f0',
            textPrimary: '#0f172a', textSecondary: '#334155', textMuted: '#64748b',
            accent: '#10b981', accentSecondary: '#0d9488',
            chartColors: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'],
            kpiBg: 'rgba(16,185,129,0.05)', kpiBorder: 'rgba(16,185,129,0.15)',
            headerBg: '#ffffff', sidebarBg: '#f8fafc', hoverBg: 'rgba(16,185,129,0.04)',
            shadowColor: 'rgba(0,0,0,0.04)', gradientFrom: '#ffffff', gradientTo: '#f8fafc'
        },
        isDark: false
    },
    {
        id: 'pearl',
        name: 'Pearl',
        icon: <Gem className="w-4 h-4" />,
        preview: { bg: '#faf9f7', card: '#ffffff', accent: '#b45309', text: '#1c1917' },
        colors: {
            bg: '#faf9f7', bgSecondary: '#f5f5f0', cardBg: '#ffffff', cardBorder: '#e7e5e4',
            textPrimary: '#1c1917', textSecondary: '#44403c', textMuted: '#78716c',
            accent: '#b45309', accentSecondary: '#a16207',
            chartColors: ['#b45309', '#0284c7', '#059669', '#c2410c', '#7c3aed', '#be185d', '#0891b2', '#ca8a04'],
            kpiBg: 'rgba(180,83,9,0.05)', kpiBorder: 'rgba(180,83,9,0.12)',
            headerBg: '#faf9f7', sidebarBg: '#f5f5f0', hoverBg: 'rgba(180,83,9,0.04)',
            shadowColor: 'rgba(0,0,0,0.04)', gradientFrom: '#faf9f7', gradientTo: '#f5f5f0'
        },
        isDark: false
    }
];

/* ===================================================================
   THEME SELECTOR COMPONENT
   =================================================================== */
interface ThemeSelectorProps {
    currentThemeId: string;
    onThemeChange: (theme: DashboardTheme) => void;
    isDark: boolean;
}

export const ThemeSelector: React.FC<ThemeSelectorProps> = ({ currentThemeId, onThemeChange, isDark }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [hoveredTheme, setHoveredTheme] = useState<string | null>(null);

    const currentTheme = DASHBOARD_THEMES.find(t => t.id === currentThemeId) || DASHBOARD_THEMES[0];

    return (
        <div className="relative">
            {/* Trigger Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-200 border ${
                    isDark
                        ? 'bg-white/5 border-white/10 text-white hover:bg-white/10'
                        : 'bg-gray-100 border-gray-200 text-gray-700 hover:bg-gray-200'
                }`}
            >
                <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded-full" style={{ background: currentTheme.colors.accent }} />
                    <Palette className="w-3.5 h-3.5" />
                    <span>{currentTheme.name}</span>
                </div>
                <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Panel */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop */}
                        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />

                        <motion.div
                            initial={{ opacity: 0, y: -8, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -8, scale: 0.95 }}
                            transition={{ duration: 0.15 }}
                            className={`absolute right-0 mt-2 w-80 rounded-2xl border shadow-2xl z-50 overflow-hidden ${
                                isDark
                                    ? 'bg-gray-900/95 border-gray-700/50 backdrop-blur-2xl'
                                    : 'bg-white/95 border-gray-200 backdrop-blur-2xl'
                            }`}
                        >
                            {/* Header */}
                            <div className={`px-4 py-3 border-b flex items-center justify-between ${
                                isDark ? 'border-gray-700/50' : 'border-gray-200'
                            }`}>
                                <div className="flex items-center gap-2">
                                    <Paintbrush className={`w-4 h-4 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
                                    <span className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                        Dashboard Theme
                                    </span>
                                </div>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className={`p-1 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10' : 'hover:bg-gray-100'}`}
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Dark Themes */}
                            <div className="p-3">
                                <div className={`text-[10px] font-bold uppercase tracking-wider mb-2 px-1 ${
                                    isDark ? 'text-gray-500' : 'text-gray-400'
                                }`}>
                                    Dark Themes
                                </div>
                                <div className="grid grid-cols-3 gap-2">
                                    {DASHBOARD_THEMES.filter(t => t.isDark).map(theme => (
                                        <ThemePreviewCard
                                            key={theme.id}
                                            theme={theme}
                                            isActive={currentThemeId === theme.id}
                                            isHovered={hoveredTheme === theme.id}
                                            onHover={() => setHoveredTheme(theme.id)}
                                            onLeave={() => setHoveredTheme(null)}
                                            onClick={() => { onThemeChange(theme); setIsOpen(false); }}
                                            isDark={isDark}
                                        />
                                    ))}
                                </div>
                            </div>

                            {/* Light Themes */}
                            <div className="px-3 pb-3">
                                <div className={`text-[10px] font-bold uppercase tracking-wider mb-2 px-1 ${
                                    isDark ? 'text-gray-500' : 'text-gray-400'
                                }`}>
                                    Light Themes
                                </div>
                                <div className="grid grid-cols-3 gap-2">
                                    {DASHBOARD_THEMES.filter(t => !t.isDark).map(theme => (
                                        <ThemePreviewCard
                                            key={theme.id}
                                            theme={theme}
                                            isActive={currentThemeId === theme.id}
                                            isHovered={hoveredTheme === theme.id}
                                            onHover={() => setHoveredTheme(theme.id)}
                                            onLeave={() => setHoveredTheme(null)}
                                            onClick={() => { onThemeChange(theme); setIsOpen(false); }}
                                            isDark={isDark}
                                        />
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

/* ===================================================================
   THEME PREVIEW CARD
   =================================================================== */
const ThemePreviewCard: React.FC<{
    theme: DashboardTheme;
    isActive: boolean;
    isHovered: boolean;
    onHover: () => void;
    onLeave: () => void;
    onClick: () => void;
    isDark: boolean;
}> = ({ theme, isActive, isHovered, onHover, onLeave, onClick, isDark }) => (
    <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onMouseEnter={onHover}
        onMouseLeave={onLeave}
        onClick={onClick}
        className={`relative rounded-xl overflow-hidden border-2 transition-all duration-200 ${
            isActive
                ? 'border-indigo-500 ring-2 ring-indigo-500/30'
                : isHovered
                    ? isDark ? 'border-white/30' : 'border-gray-400'
                    : isDark ? 'border-white/10' : 'border-gray-200'
        }`}
    >
        {/* Mini Dashboard Preview */}
        <div className="w-full h-14 p-1.5" style={{ background: theme.preview.bg }}>
            {/* Mini header bar */}
            <div className="h-1.5 rounded-full w-8 mb-1" style={{ background: theme.preview.accent, opacity: 0.6 }} />
            {/* Mini cards */}
            <div className="flex gap-0.5">
                <div className="flex-1 h-3 rounded-sm" style={{ background: theme.preview.card, border: `0.5px solid ${theme.colors.cardBorder}` }} />
                <div className="flex-1 h-3 rounded-sm" style={{ background: theme.preview.card, border: `0.5px solid ${theme.colors.cardBorder}` }} />
            </div>
            {/* Mini chart bars */}
            <div className="flex items-end gap-[1px] mt-1 h-3">
                {[0.4, 0.7, 0.5, 0.9, 0.6, 0.8].map((h, i) => (
                    <div
                        key={i}
                        className="flex-1 rounded-t-[1px]"
                        style={{ height: `${h * 100}%`, background: theme.colors.chartColors[i % theme.colors.chartColors.length], opacity: 0.8 }}
                    />
                ))}
            </div>
        </div>

        {/* Theme Name */}
        <div className={`px-2 py-1.5 text-[10px] font-semibold flex items-center justify-between ${
            isDark ? 'bg-gray-800/80 text-gray-300' : 'bg-gray-50 text-gray-600'
        }`}>
            <span className="truncate">{theme.name}</span>
            {isActive && <Check className="w-3 h-3 text-indigo-500 flex-shrink-0" />}
        </div>
    </motion.button>
);

export default ThemeSelector;
