/**
 * Landing Page - EXACT match to reference image
 * 
 * Headline: "Transform your data into actionable insights"
 * CTA: "Upload Data" (teal/green button)
 * Features: Zero Hardcoding, Automated Analysis, Interactive Dashboard, Adaptive Insights
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Upload,
    BarChart3,
    Zap,
    LineChart,
    PieChart,
    Sun,
    Moon,
    TrendingUp,
    CheckCircle,
} from 'lucide-react';

const Landing: React.FC = () => {
    const navigate = useNavigate();
    const [isDark, setIsDark] = useState(true);

    useEffect(() => {
        const saved = localStorage.getItem('theme');
        setIsDark(saved !== 'light');
        if (saved === 'light') {
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

    const features = [
        {
            icon: Zap,
            title: 'Zero Hardcoding',
            description: 'Upload any dataset and get automatic insights without configuration.',
            color: '#3B82F6',
        },
        {
            icon: BarChart3,
            title: 'Automated Analysis',
            description: 'AI detects patterns, trends, and anomalies in your data instantly.',
            color: '#22C55E',
        },
        {
            icon: LineChart,
            title: 'Interactive Dashboard',
            description: 'Dynamic charts and visualizations that adapt to your data schema.',
            color: '#F59E0B',
        },
        {
            icon: PieChart,
            title: 'Adaptive Insights',
            description: 'Natural language summaries that explain what your data means.',
            color: '#8B5CF6',
        },
    ];

    const bgColor = isDark ? '#0F172A' : '#F8FAFC';
    const cardBg = isDark ? '#1E293B' : '#FFFFFF';
    const textPrimary = isDark ? '#F8FAFC' : '#0F172A';
    const textMuted = isDark ? '#94A3B8' : '#64748B';
    const borderColor = isDark ? '#334155' : '#E2E8F0';

    return (
        <div className="min-h-screen transition-colors duration-300" style={{ backgroundColor: bgColor }}>
            {/* Navigation */}
            <nav
                className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md border-b"
                style={{
                    backgroundColor: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.95)',
                    borderColor
                }}
            >
                <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <img src="/logo.png" alt="DataVision Logo" className="w-9 h-9 object-contain" />
                        <span className="text-lg font-semibold" style={{ color: textPrimary }}>
                            DataVision
                        </span>
                    </div>

                    {/* Nav Links */}
                    <div className="hidden md:flex items-center gap-8">
                        {['Overview', 'Data Hub', 'Reports', 'Dashboards'].map((item) => (
                            <button
                                key={item}
                                onClick={() => navigate(`/${item.toLowerCase().replace(' ', '-')}`)}
                                className="text-sm font-medium transition-colors hover:text-blue-500"
                                style={{ color: textMuted }}
                            >
                                {item}
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-3">
                        <button onClick={toggleTheme} className="p-2 rounded-lg" style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
                            {isDark ? <Sun className="w-5 h-5 text-slate-400" /> : <Moon className="w-5 h-5 text-slate-500" />}
                        </button>
                        <button
                            onClick={() => navigate('/login')}
                            className="text-sm font-medium transition-colors"
                            style={{ color: textMuted }}
                        >
                            Sign In
                        </button>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-32 pb-20 px-6">
                <div className="max-w-6xl mx-auto">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        {/* Left - Text */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                        >
                            <h1 className="text-5xl lg:text-7xl font-bold mb-6 tracking-tight leading-tight" style={{ color: textPrimary }}>
                                Transform your <span className="bg-gradient-to-r from-teal-400 to-blue-500 bg-clip-text text-transparent">Raw data</span> into actionable insights
                            </h1>

                            <p
                                className="text-lg leading-relaxed mb-8"
                                style={{ color: textMuted }}
                            >
                                Upload any dataset and let AI automatically generate insights, charts,
                                and recommendations. No configuration required.
                            </p>

                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => navigate('/data-hub')}
                                className="flex items-center gap-2 px-8 py-4 bg-teal-500 hover:bg-teal-600 text-white rounded-full text-base font-semibold transition-all shadow-lg shadow-teal-500/25"
                            >
                                Upload Data
                            </motion.button>
                        </motion.div>

                        {/* Right - Preview Dashboard */}
                        <motion.div
                            initial={{ opacity: 0, y: 40 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.2 }}
                        >
                            <div
                                className="rounded-2xl overflow-hidden shadow-2xl border"
                                style={{ backgroundColor: cardBg, borderColor }}
                            >
                                {/* Mini Sidebar */}
                                <div className="flex">
                                    <div className="w-12 py-4 flex flex-col items-center gap-4" style={{ backgroundColor: isDark ? '#0F172A' : '#F1F5F9' }}>
                                        <div className="w-7 h-7 rounded-lg overflow-hidden flex items-center justify-center p-1 bg-white">
                                            <img src="/logo.png" alt="Logo" className="w-full h-full object-contain" />
                                        </div>
                                        {[1, 2, 3, 4].map(i => (
                                            <div key={i} className="w-5 h-5 rounded" style={{ backgroundColor: isDark ? '#334155' : '#E2E8F0' }}></div>
                                        ))}
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1 p-4">
                                        <div className="flex items-center gap-2 mb-4">
                                            <img src="/logo.png" alt="" className="w-5 h-5 object-contain" />
                                            <p className="text-lg font-semibold" style={{ color: textPrimary }}>Overview</p>
                                        </div>

                                        {/* KPI Cards */}
                                        <div className="grid grid-cols-4 gap-2 mb-4">
                                            {[
                                                { label: 'Total Sales', value: '₹12.4 Cr', color: '#14B8A6' },
                                                { label: 'Customers', value: '14.2k', color: '#2DD4BF' },
                                                { label: 'Avg Order', value: '₹8,450', color: '#0D9488' },
                                                { label: 'Conversion', value: '3.2%', color: '#14B8A6' },
                                            ].map((kpi, i) => (
                                                <div key={i} className="p-2 rounded-lg" style={{ backgroundColor: isDark ? '#1E293B' : '#F8FAFC' }}>
                                                    <p className="text-[10px] mb-1" style={{ color: textMuted }}>{kpi.label}</p>
                                                    <p className="text-sm font-bold" style={{ color: kpi.color }}>{kpi.value}</p>
                                                </div>
                                            ))}
                                        </div>

                                        {/* Chart Preview */}
                                        <div className="grid grid-cols-3 gap-2">
                                            {/* Trend */}
                                            <div className="col-span-2 p-3 rounded-lg" style={{ backgroundColor: isDark ? '#1E293B' : '#F8FAFC' }}>
                                                <p className="text-xs font-medium mb-2" style={{ color: textPrimary }}>Hiring Trend</p>
                                                <div className="flex items-end gap-1 h-16">
                                                    {[40, 60, 35, 80, 55, 70, 90, 65, 85].map((h, i) => (
                                                        <div key={i} className="flex-1 rounded-t bg-gradient-to-t from-teal-500 to-teal-400" style={{ height: `${h}%` }}></div>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Donut */}
                                            <div className="p-3 rounded-lg" style={{ backgroundColor: isDark ? '#1E293B' : '#F8FAFC' }}>
                                                <p className="text-xs font-medium mb-2" style={{ color: textPrimary }}>Roles</p>
                                                <div className="relative w-12 h-12 mx-auto">
                                                    <svg viewBox="0 0 36 36" className="w-full h-full">
                                                        <circle cx="18" cy="18" r="12" fill="none" stroke="#14B8A6" strokeWidth="6" strokeDasharray="35 65" strokeDashoffset="25" />
                                                        <circle cx="18" cy="18" r="12" fill="none" stroke="#2DD4BF" strokeWidth="6" strokeDasharray="25 75" strokeDashoffset="-10" />
                                                        <circle cx="18" cy="18" r="12" fill="none" stroke="#0D9488" strokeWidth="6" strokeDasharray="20 80" strokeDashoffset="-35" />
                                                        <circle cx="18" cy="18" r="12" fill="none" stroke="#5EEAD4" strokeWidth="6" strokeDasharray="20 80" strokeDashoffset="-55" />
                                                    </svg>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 px-6">
                <div className="max-w-6xl mx-auto">
                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {features.map((feature, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="p-6 rounded-2xl border transition-all hover:shadow-lg"
                                style={{ backgroundColor: cardBg, borderColor }}
                            >
                                <div
                                    className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                                    style={{ backgroundColor: `${feature.color}15` }}
                                >
                                    <feature.icon className="w-6 h-6" style={{ color: feature.color }} />
                                </div>
                                <h3 className="text-lg font-semibold mb-2" style={{ color: textPrimary }}>
                                    {feature.title}
                                </h3>
                                <p className="text-sm leading-relaxed" style={{ color: textMuted }}>
                                    {feature.description}
                                </p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 px-6">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="max-w-4xl mx-auto text-center"
                >
                    <div
                        className="p-12 rounded-3xl"
                        style={{ background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)' }}
                    >
                        <h2 className="text-4xl font-bold text-white mb-4">
                            Ready to unlock your data's potential?
                        </h2>
                        <p className="text-xl text-white/80 mb-8">
                            Start analyzing your business data in minutes
                        </p>
                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => navigate('/signup')}
                            className="px-10 py-4 bg-white text-teal-600 rounded-full font-semibold text-lg shadow-xl"
                        >
                            Get Started Free
                        </motion.button>
                    </div>
                </motion.div>
            </section>

            {/* Footer */}
            <footer className="py-10 px-6 border-t" style={{ borderColor }}>
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                            <BarChart3 className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: textMuted }}>DataVision</span>
                    </div>
                    <p className="text-xs" style={{ color: textMuted }}>
                        © 2025 DataVision. All rights reserved.
                    </p>
                </div>
            </footer>
        </div>
    );
};

export default Landing;
