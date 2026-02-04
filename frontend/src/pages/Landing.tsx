/**
 * Landing Page — DataVision
 * Autonomous Data Intelligence Platform
 * 
 * Complete interactive demo - auto-playing
 * Premium $500M+ grade copy
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Sun, Moon, ArrowRight, Check, Upload,
    Home, BarChart2, Database, FileText, MessageSquare, Settings,
    ChevronRight, ChevronDown, TrendingUp, Search, Mic, Download,
    Shield, RefreshCw, Layers, GitBranch, Zap, Clock,
    PieChart, Activity, Users, Loader2, LayoutDashboard, BrainCircuit, Target,
    PanelLeftClose, PanelLeftOpen, LogOut
} from 'lucide-react';
import AnimatedLogo from '../components/AnimatedLogo';
import LogoImage from '../components/LogoImage';

import { useUserStore } from '@/store/userStore';

const Landing: React.FC = () => {
    const navigate = useNavigate();
    const { isDark, toggleTheme } = useUserStore();
    const [scene, setScene] = useState(1); // Start at Dashboard
    const [cursorPos, setCursorPos] = useState({ x: 300, y: 250 });
    const [cursorClick, setCursorClick] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [hoveredPage, setHoveredPage] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('Overview'); // For ML Predictions
    const [typing, setTyping] = useState('');
    const [responseText, setResponseText] = useState('');
    const [showMCPPanel, setShowMCPPanel] = useState(false);
    const [showPermission, setShowPermission] = useState(false);
    const [showRunningMCP, setShowRunningMCP] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [reportGenerating, setReportGenerating] = useState(false);
    const [automlProgress, setAutomlProgress] = useState(0);

    const question = 'Check my data quality...';
    const fullResponse = `I've checked your data quality, and it appears to be in good condition. The data is comprehensive, with 100 records across various categories.

**Data Quality Summary:**
• 20 unique customers
• 100 unique products  
• Total revenue: ₹13,85,149

**Data Quality Score: 100/100** - No issues found`;

    // Theme is now managed globally by userStore and App.tsx
    // No local useEffect needed for theme initialization

    const triggerClick = () => {
        setCursorClick(true);
        setTimeout(() => setCursorClick(false), 150);
    };

    // ChatGPT-style typing effect for response
    const typeResponse = () => {
        let i = 0;
        const interval = setInterval(() => {
            if (i <= fullResponse.length) {
                setResponseText(fullResponse.slice(0, i));
                i += 3;
            } else {
                clearInterval(interval);
            }
        }, 20);
    };

    // Demo sequence - Auto-play always
    useEffect(() => {
        const timers: NodeJS.Timeout[] = [];

        const runDemo = () => {
            // Disable demo animation on mobile/tablet as layout changes
            // if (typeof window !== 'undefined' && window.innerWidth < 1024) return;

            // Reset all states
            setScene(1);
            setActiveTab('Overview');
            setTyping('');
            setResponseText('');
            setShowMCPPanel(false);
            setShowPermission(false);
            setShowRunningMCP(false);
            setUploadProgress(0);
            setAutomlProgress(0);
            setReportGenerating(false);
            setCursorPos({ x: 80, y: 160 }); // Start at Dashboard sidebar

            // Scene 1: Dashboard (0-5s)
            // Interact with dashboard
            timers.push(setTimeout(() => setCursorPos({ x: 500, y: 300 }), 1500)); // Hover over chart
            timers.push(setTimeout(() => setCursorPos({ x: 200, y: 250 }), 3000)); // Hover over KPI

            // Scene 2: Go to AutoML (5-11s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 200 }), 5000)); // AutoML sidebar
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(2); // Show AutoML Training
                // Simulate AutoML Training Progress
                let p = 0;
                const progressInterval = setInterval(() => {
                    p += 5;
                    setAutomlProgress(p);
                    if (p >= 100) clearInterval(progressInterval);
                }, 100);
            }, 5500));

            // Scene 3: Go to Predictions (11-20s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 240 }), 11000)); // Predictions sidebar
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(3);
                setActiveTab('Overview');
            }, 11500));

            // Switch to ML Charts tab
            timers.push(setTimeout(() => setCursorPos({ x: 350, y: 200 }), 14000)); // Move to ML Charts tab
            timers.push(setTimeout(() => {
                triggerClick();
                setActiveTab('ML Charts');
            }, 14500));

            // Switch to Features tab
            timers.push(setTimeout(() => setCursorPos({ x: 450, y: 200 }), 17000)); // Move to Features tab
            timers.push(setTimeout(() => {
                triggerClick();
                setActiveTab('Features');
            }, 17500));

            // Switch to Make Prediction tab
            timers.push(setTimeout(() => setCursorPos({ x: 550, y: 200 }), 20000)); // Move to Make Prediction tab
            timers.push(setTimeout(() => {
                triggerClick();
                setActiveTab('Make Prediction');
            }, 20500));

            // Scene 4: Go to AI Analyst (23-34s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 280 }), 23000)); // Chat sidebar
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(4);
                // setTypeIndex(0); // This variable doesn't exist in the original code, removing.
                setTyping('');
                setShowPermission(false);
                setShowRunningMCP(false);
                setResponseText('');
                setShowMCPPanel(false);
            }, 23500));

            // Type message
            timers.push(setTimeout(() => setCursorPos({ x: 400, y: 500 }), 24500)); // Input field
            const typeMessage = () => {
                const msg = "Analyze the sentiment trends in this dataset";
                let i = 0;
                const interval = setInterval(() => {
                    setTyping(msg.substring(0, i + 1));
                    i++;
                    if (i > msg.length) clearInterval(interval);
                }, 50);
            };
            timers.push(setTimeout(typeMessage, 25000));

            // Send button
            timers.push(setTimeout(() => setCursorPos({ x: 560, y: 450 }), 27500));
            timers.push(setTimeout(() => {
                triggerClick();
                typeResponse();
            }, 28000));

            // Scene 5: Go to Reports (37-45s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 320 }), 37000)); // Reports sidebar
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(5);
            }, 37500));

            // Generate report
            timers.push(setTimeout(() => setCursorPos({ x: 400, y: 285 }), 39500));
            timers.push(setTimeout(() => {
                triggerClick();
                setReportGenerating(true);
            }, 40000));
            timers.push(setTimeout(() => {
                setReportGenerating(false);
                setScene(6); // Show Result
            }, 42000));

            // Scene 6: Go to Settings (45-50s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 360 }), 45000)); // Settings sidebar
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(7);
            }, 45500));
            timers.push(setTimeout(() => setCursorPos({ x: 600, y: 350 }), 47000)); // Hover toggle
            timers.push(setTimeout(() => triggerClick(), 47500));

            // Loop (55s)
            timers.push(setTimeout(() => runDemo(), 55000));
        };

        runDemo();
        return () => timers.forEach(t => clearTimeout(t));
    }, []);

    // Local toggleTheme removed in favor of store action

    // Colors
    const accent = '#22c55e'; // Vibrant Green Brand Color
    const bg = isDark ? '#0a0a0f' : '#fafafa';
    const text = isDark ? '#fafafa' : '#0f172a';
    const textMuted = isDark ? '#71717a' : '#64748b';
    const textSecondary = isDark ? '#d1d5db' : '#374151'; // Much brighter for dark mode visibility
    const border = isDark ? '#27272a' : '#e4e4e7';

    // Demo colors
    const demoBg = isDark ? '#0f1419' : '#ffffff';
    const demoSidebar = isDark ? '#1a1f2e' : '#f8fafc';
    const demoCard = isDark ? '#1e2536' : '#f1f5f9';
    const demoBorder = isDark ? '#2a3142' : '#e2e8f0';
    const demoText = isDark ? '#f1f5f9' : '#0f172a';
    const demoMuted = isDark ? '#94a3b8' : '#64748b';
    // Fix: Input text color for both themes
    const inputText = isDark ? '#f1f5f9' : '#1e293b';

    // Get active page
    const getActivePage = () => {
        if (scene === 1) return 'dashboard'; // Default start
        if (scene === 2) return 'automl';
        if (scene === 3) return 'ml-predictions';
        if (scene === 4) return 'chat';
        if (scene === 5 || scene === 6) return 'reports';
        if (scene === 7) return 'settings';
        return 'dashboard';
    };

    const activePage = getActivePage();

    // Auto-scroll mobile nav
    useEffect(() => {
        const activeEl = document.getElementById(`demo-nav-${activePage}`);
        if (activeEl) {
            activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
    }, [activePage]);

    return (
        <div className="min-h-screen" style={{ backgroundColor: bg, color: text }}>
            {/* Navigation */}
            <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-lg" style={{ backgroundColor: isDark ? 'rgba(10, 10, 15, 0.9)' : 'rgba(255, 255, 255, 0.95)', borderBottom: `1px solid ${border}` }}>
                <div className="max-w-6xl mx-auto px-6">
                    <div className="h-16 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <AnimatedLogo size="sm" showText={true} isDark={isDark} />
                        </div>
                        <div className="flex items-center gap-4">
                            <button onClick={toggleTheme} className="p-2 rounded-lg transition-colors" style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
                                {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
                            </button>
                            <button onClick={() => navigate('/login')} className="text-sm" style={{ color: textMuted }}>
                                Sign in
                            </button>
                            <button
                                onClick={() => navigate('/data-hub')}
                                className="text-sm font-medium px-4 py-2 rounded-lg text-white"
                                style={{ backgroundColor: accent }}
                            >
                                Get Started
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section - Premium $5M Copy */}
            <section className="pt-24 md:pt-28 pb-8 md:pb-12 px-4 md:px-6">
                <div className="max-w-4xl mx-auto text-center">

                    <motion.h1
                        initial={{ opacity: 1, y: 0 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] mb-4 md:mb-6"
                    >
                        Your data doesn't need dashboards.
                        <br />
                        <span style={{ color: accent }}>It needs intelligence.</span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 1, y: 0 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-base sm:text-lg md:text-xl leading-relaxed mb-4 md:mb-6 max-w-3xl mx-auto px-2"
                        style={{ color: textSecondary }}
                    >
                        A self-learning system that autonomously generates 15+ intelligent visualizations,
                        trains production-ready ML models with one click, and delivers LLM-powered insights —
                        all without writing a single line of code.
                    </motion.p>

                    <motion.p
                        initial={{ opacity: 1, y: 0 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="text-sm sm:text-base leading-relaxed mb-8 md:mb-10 max-w-2xl mx-auto px-2"
                        style={{ color: textSecondary }}
                    >
                        Upload any CSV or Excel file. Get autonomous dashboards, Ultra AutoML predictions,
                        executive reports, and an AI analyst that understands your data context — in real time.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 1, y: 0 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <button
                            onClick={() => navigate('/data-hub')}
                            className="flex items-center gap-2 text-sm font-semibold px-8 py-4 rounded-xl text-white mx-auto transition-all hover:scale-105"
                            style={{ backgroundColor: accent, boxShadow: `0 8px 30px -10px ${accent}` }}
                        >
                            Start with your data <ArrowRight className="w-4 h-4" />
                        </button>
                    </motion.div>

                    {/* Trust Indicators - Real Features */}
                    <motion.div
                        initial={{ opacity: 1 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="flex items-center justify-center gap-6 mt-8 flex-wrap"
                    >
                        {[
                            { icon: Zap, text: 'Ultra AutoML Training' },
                            { icon: LayoutDashboard, text: '15+ Auto Charts' },
                            { icon: BrainCircuit, text: 'LLM-Powered Insights' },
                        ].map((item, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs" style={{ color: textSecondary }}>
                                <item.icon className="w-4 h-4" style={{ color: accent }} />
                                <span>{item.text}</span>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* Product Demo */}
            <section className="pb-20 px-4 md:px-6 overflow-hidden">
                <div className="max-w-5xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="rounded-2xl overflow-hidden shadow-2xl relative max-w-full"
                        style={{
                            backgroundColor: demoBg,
                            border: `1px solid ${demoBorder}`,
                            boxShadow: isDark ? '0 25px 50px rgba(0,0,0,0.5)' : '0 25px 50px rgba(0,0,0,0.1)'
                        }}
                    >
                        {/* Window Chrome */}
                        <div className="flex items-center gap-2 px-4 py-3 border-b" style={{ borderColor: demoBorder, backgroundColor: isDark ? '#0c0f14' : '#f4f4f5' }}>
                            <div className="flex gap-2">
                                <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                                <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
                                <div className="w-3 h-3 rounded-full bg-[#28c840]" />
                            </div>
                            <div className="flex-1 text-center">
                                <span className="text-xs font-medium" style={{ color: demoMuted }}>DataVision</span>
                            </div>
                        </div>

                        {/* App Content */}
                        <div className="flex flex-col md:flex-row h-auto md:h-[520px] relative">
                            {/* Cursor - Hidden on mobile/tablet */}
                            <motion.div
                                animate={{
                                    left: cursorPos.x,
                                    top: cursorPos.y,
                                    scale: cursorClick ? 0.8 : 1
                                }}
                                transition={{ type: 'spring', damping: 20, stiffness: 200 }}
                                className="absolute z-50 pointer-events-none hidden lg:block"
                                style={{ marginLeft: -6, marginTop: -2 }}
                            >
                                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                                    <path
                                        d="M5 3L19 12L12 13L9 20L5 3Z"
                                        fill={isDark ? '#ffffff' : '#000000'}
                                        stroke={isDark ? '#000000' : '#ffffff'}
                                        strokeWidth="1.5"
                                    />
                                </svg>
                                {cursorClick && (
                                    <motion.div
                                        initial={{ scale: 0, opacity: 0.6 }}
                                        animate={{ scale: 2.5, opacity: 0 }}
                                        transition={{ duration: 0.4 }}
                                        className="absolute top-2 left-2 w-4 h-4 rounded-full"
                                        style={{ backgroundColor: accent }}
                                    />
                                )}
                            </motion.div>

                            {/* Sidebar - Responsive Nav on Mobile / Collapsible on Desktop */}
                            <motion.div
                                className={`flex-shrink-0 border-r-0 border-b md:border-r md:border-b-0 flex flex-row md:flex-col justify-between md:justify-start w-full transition-all duration-300 ${isSidebarOpen ? 'md:w-40' : 'md:w-16'}`}
                                style={{ backgroundColor: demoSidebar, borderColor: demoBorder }}
                            >
                                <div className="p-3 border-b-0 md:border-b border-r md:border-r-0 flex items-center justify-between" style={{ borderColor: demoBorder }}>
                                    <div className="flex items-center gap-2 overflow-hidden">
                                        <LogoImage size={20} className="rounded-sm flex-shrink-0" />
                                        {isSidebarOpen && (
                                            <motion.span
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                className="text-sm font-semibold whitespace-nowrap hidden md:inline"
                                                style={{ color: demoText }}
                                            >
                                                DataVision
                                            </motion.span>
                                        )}
                                        <span className="text-sm font-semibold whitespace-nowrap md:hidden" style={{ color: demoText }}>DataVision</span>
                                    </div>
                                    {/* Desktop Toggle Button */}
                                    <button
                                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                                        className="hidden md:flex p-1 hover:bg-white/10 rounded ml-1 transition-colors"
                                        style={{ color: demoMuted }}
                                        title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
                                    >
                                        {isSidebarOpen ? <PanelLeftClose size={14} /> : <PanelLeftOpen size={14} />}
                                    </button>
                                </div>

                                <div className="flex-1 py-0 md:py-2 flex flex-row md:flex-col items-center md:items-stretch overflow-x-auto md:overflow-visible no-scrollbar">
                                    {[
                                        { icon: Home, label: 'Home', path: 'home' },
                                        { icon: Database, label: 'Data Hub', path: 'data-hub' },
                                        { icon: LayoutDashboard, label: 'Dashboard', path: 'dashboard' },
                                        { icon: BrainCircuit, label: 'AutoML', path: 'automl' },
                                        { icon: Target, label: 'Predictions', path: 'ml-predictions' },
                                        { icon: FileText, label: 'Reports', path: 'reports' },
                                        { icon: MessageSquare, label: 'AI Analyst', path: 'chat' },
                                        { icon: Settings, label: 'Settings', path: 'settings' },
                                    ].map((item) => {
                                        const isActive = activePage === item.path;
                                        return (
                                            <div
                                                id={`demo-nav-${item.path}`}
                                                key={item.label}
                                                onMouseEnter={() => setHoveredPage(item.path)}
                                                onMouseLeave={() => setHoveredPage(null)}
                                                className={`flex items-center gap-2 px-3 py-2 mx-1 md:mx-2 rounded-lg text-xs cursor-pointer transition-all whitespace-nowrap flex-shrink-0 ${!isSidebarOpen ? 'md:justify-center md:px-0' : ''}`}
                                                style={{
                                                    backgroundColor: isActive ? `${accent}15` : 'transparent',
                                                    color: isActive ? accent : demoMuted,
                                                    borderLeft: isActive && isSidebarOpen ? `2px solid ${accent}` : '2px solid transparent'
                                                }}
                                                title={!isSidebarOpen ? item.label : ''}
                                            >
                                                <item.icon className="w-4 h-4 flex-shrink-0" />
                                                <span className="md:hidden">{item.label}</span>
                                                {isSidebarOpen && <span className="hidden md:inline">{item.label}</span>}
                                            </div>
                                        );
                                    })}
                                </div>

                                <div className="hidden md:block p-3 border-t text-xs overflow-hidden whitespace-nowrap" style={{ borderColor: demoBorder, color: demoMuted }}>
                                    {isSidebarOpen ? 'Sign Out' : <div className="flex justify-center"><LogOut size={14} /></div>}
                                </div>
                            </motion.div>

                            {/* Main Content */}
                            <div className="flex-1 overflow-visible md:overflow-hidden relative">
                                <AnimatePresence mode="wait">
                                    {/* Data Hub - REMOVED */}{/* Dashboard (Autonomous) */}
                                    {activePage === 'dashboard' && (
                                        <motion.div key="dashboard" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-auto md:h-full p-4 overflow-visible md:overflow-auto">
                                            <div className="flex items-center justify-between mb-4">
                                                <div>
                                                    <h2 className="text-base font-semibold" style={{ color: demoText }}>Social Media Insights</h2>
                                                    <p className="text-[10px]" style={{ color: demoMuted }}>732 rows x 17 columns • general Domain</p>
                                                </div>
                                                <div className="flex gap-2">
                                                    <div className="px-2 py-1 rounded border text-[10px]" style={{ borderColor: demoBorder, color: demoText }}>732 rows</div>
                                                    <div className="px-2 py-1 rounded border text-[10px]" style={{ borderColor: demoBorder, color: demoText }}>17 columns</div>
                                                </div>
                                            </div>

                                            {/* KPI Cards - FAVORITE FEATURE: Responsive Grid */}
                                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 mb-4">
                                                {[
                                                    { label: 'Total Records', value: '732', sub: '16 dimensions', color: '#10b981' },
                                                    { label: 'Avg Unnamed: 0.1', value: '366', sub: '+199.6% vs past avg', color: '#3b82f6' },
                                                    { label: 'Avg Unnamed: 0', value: '370', sub: '+197.8% vs past avg', color: '#f59e0b' },
                                                    { label: 'Avg Retweets', value: '22', sub: '-37.0% vs past avg', color: '#0ea5e9' },
                                                    { label: 'Avg Likes', value: '43', sub: '+36.2% vs past avg', color: '#ef4444' },
                                                    { label: 'Avg Year', value: '2.0K', sub: '0.0% vs past avg', color: '#8b5cf6' },
                                                ].map((kpi, i) => (
                                                    <div key={i} className="p-2 rounded-lg border-t-2" style={{ backgroundColor: demoCard, borderColor: demoBorder, borderTopColor: kpi.color }}>
                                                        <p className="text-[9px]" style={{ color: kpi.color }}>{kpi.label}</p>
                                                        <p className="text-sm font-bold my-0.5" style={{ color: demoText }}>{kpi.value}</p>
                                                        <p className="text-[8px]" style={{ color: demoMuted }}>{kpi.sub}</p>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Charts Grid - Responsive */}
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 h-auto md:h-32 mb-3">
                                                {/* Text Sunburst */}
                                                <div className="p-2 rounded-lg border relative" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Text Sunburst</p>
                                                        <span className="text-[8px] text-muted-foreground">sunburst</span>
                                                    </div>
                                                    <div className="flex items-center justify-center h-full pb-4">
                                                        <PieChart className="w-16 h-16 opacity-70 text-blue-500" />
                                                    </div>
                                                </div>
                                                {/* Stacked Bar */}
                                                <div className="p-2 rounded-lg border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Unnamed: 0.1 by Text</p>
                                                        <span className="text-[8px] text-muted-foreground">stacked_bar</span>
                                                    </div>
                                                    <div className="flex items-end gap-1 h-20 mt-1">
                                                        {[40, 60, 80, 50, 65, 55].map((h, i) => <div key={i} className="flex-1 bg-cyan-500 rounded-t opacity-80" style={{ height: `${h}%` }} />)}
                                                    </div>
                                                </div>
                                                {/* Scatter */}
                                                <div className="p-2 rounded-lg border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Retweets vs Unnamed: 0</p>
                                                        <span className="text-[8px] text-muted-foreground">scatter</span>
                                                    </div>
                                                    <div className="relative h-20 mt-1 bg-black/20 rounded">
                                                        {[...Array(30)].map((_, i) => (
                                                            <div key={i} className="absolute w-1 h-1 rounded-full bg-emerald-400" style={{ left: `${Math.random() * 100}%`, top: `${Math.random() * 100}%` }} />
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 h-auto md:h-32 mb-3">
                                                {/* Bubble/Scatter */}
                                                <div className="p-2 rounded-lg border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Year vs Unnamed: 0</p>
                                                        <span className="text-[8px] text-muted-foreground">bubble</span>
                                                    </div>
                                                    <div className="relative h-20 mt-1">
                                                        <div className="absolute top-1/2 left-0 right-0 h-4 bg-purple-500/30 rounded-full"></div>
                                                        <div className="absolute top-1/2 left-[80%] w-4 h-4 bg-purple-500 rounded-full"></div>
                                                        <div className="absolute top-1/2 left-[85%] w-6 h-6 bg-purple-500/60 rounded-full"></div>
                                                    </div>
                                                </div>
                                                {/* Trend + Forecast */}
                                                <div className="p-2 rounded-lg border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Unnamed: 0 Trend</p>
                                                        <span className="text-[8px] text-muted-foreground">line</span>
                                                    </div>
                                                    <div className="flex items-end gap-0.5 h-20 mt-1">
                                                        {[...Array(20)].map((_, i) => (
                                                            <div key={i} className="w-full bg-green-400" style={{ height: `${i * 5}%` }} />
                                                        ))}
                                                        <div className="w-full bg-green-400/50 border-t border-dashed border-white" style={{ height: '30%' }} />
                                                    </div>
                                                    <div className="flex items-center gap-2 mt-1 justify-center">
                                                        <span className="w-2 h-0.5 bg-green-400"></span><span className="text-[6px] text-muted-foreground">Actual</span>
                                                        <span className="w-2 h-0.5 border-t border-dashed border-green-400"></span><span className="text-[6px] text-muted-foreground">Forecast</span>
                                                    </div>
                                                </div>
                                                {/* Area */}
                                                <div className="p-2 rounded-lg border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Unnamed: 0.1 Over Time</p>
                                                        <span className="text-[8px] text-muted-foreground">area</span>
                                                    </div>
                                                    <svg viewBox="0 0 100 40" className="w-full h-full">
                                                        <path d="M0 40 L100 0 V40 H0 Z" fill="#22c55e" fillOpacity="0.3" />
                                                        <path d="M0 40 L100 0" stroke="#22c55e" strokeWidth="2" fill="none" />
                                                    </svg>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 h-auto md:h-32">
                                                {/* Stacked Bar 2 */}
                                                <div className="p-2 rounded-lg border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Unnamed: 0.1 by Text</p>
                                                        <span className="text-[8px] text-muted-foreground">stacked_bar</span>
                                                    </div>
                                                    <div className="flex items-end gap-1 h-20 mt-1">
                                                        <div className="w-4 bg-blue-500 h-[20%]"></div>
                                                        <div className="w-4 bg-yellow-500 h-[40%]"></div>
                                                    </div>
                                                </div>
                                                {/* Distribution Analysis */}
                                                <div className="p-2 rounded-lg border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Distribution Analysis</p>
                                                        <span className="text-[8px] text-muted-foreground">box</span>
                                                    </div>
                                                    <div className="relative h-20 mt-1 flex items-center justify-center">
                                                        <div className="w-3/4 h-8 border border-green-500 relative">
                                                            <div className="absolute left-[40%] h-full w-0.5 bg-green-500"></div>
                                                        </div>
                                                        <div className="absolute w-full h-0.5 bg-green-500/50 top-1/2"></div>
                                                    </div>
                                                    <div className="text-[6px] text-muted-foreground mt-1">200</div>
                                                </div>
                                                {/* Correlation Matrix */}
                                                <div className="p-2 rounded-lg border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex justify-between items-center mb-1">
                                                        <p className="text-[9px]" style={{ color: accent }}>Correlation Matrix</p>
                                                        <span className="text-[8px] text-muted-foreground">heatmap</span>
                                                    </div>
                                                    <div className="grid grid-cols-4 gap-0.5 h-full opacity-80">
                                                        {[...Array(16)].map((_, i) => (
                                                            <div key={i} style={{ backgroundColor: i % 5 === 0 ? '#22c55e' : '#22c55e40' }} />
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* AutoML */}
                                    {activePage === 'automl' && (
                                        <motion.div key="automl" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-auto md:h-full p-4 overflow-visible md:overflow-auto">
                                            <div className="flex items-center justify-between mb-4">
                                                <div>
                                                    <h2 className="text-base font-semibold" style={{ color: demoText }}>AutoML Training</h2>
                                                    <p className="text-xs" style={{ color: accent }}>Automated model selection & training</p>
                                                </div>
                                                {automlProgress < 100 && (
                                                    <span className="text-[10px] text-white px-2 py-0.5 rounded bg-blue-500">Training... {automlProgress}%</span>
                                                )}
                                            </div>

                                            {/* Progress / Status */}
                                            <div className="mb-4">
                                                <div className="flex justify-between text-[10px] mb-1" style={{ color: demoMuted }}>
                                                    <span>Data Preprocessing</span>
                                                    <span>Model Selection</span>
                                                    <span>Training</span>
                                                    <span>Evaluation</span>
                                                </div>
                                                <div className="h-1.5 w-full bg-gray-700 rounded-full overflow-hidden">
                                                    <div className="h-full bg-blue-500 transition-all duration-300" style={{ width: `${automlProgress}%` }} />
                                                </div>
                                            </div>

                                            {/* Leaderboard */}
                                            <div className="space-y-2">
                                                <div className="flex justify-between text-[10px] font-medium px-2" style={{ color: demoMuted }}>
                                                    <span>Model</span>
                                                    <span>Accuracy</span>
                                                    <span>Status</span>
                                                </div>
                                                {[
                                                    { name: 'XGBoost Classifier', acc: '98.5%', status: 'Best Model', color: '#10b981' },
                                                    { name: 'Random Forest', acc: '97.2%', status: 'Completed', color: demoMuted },
                                                    { name: 'Logistic Regression', acc: '89.0%', status: 'Completed', color: demoMuted },
                                                ].map((m, i) => (
                                                    <div key={i} className="flex items-center justify-between p-2 rounded-lg" style={{ backgroundColor: demoCard, border: i === 0 ? `1px solid ${accent}` : `1px solid ${demoBorder}` }}>
                                                        <span className="text-[10px]" style={{ color: demoText }}>{m.name}</span>
                                                        <span className="text-[10px] font-bold" style={{ color: demoText }}>{m.acc}</span>
                                                        <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ backgroundColor: m.color === '#10b981' ? '#10b98120' : 'transparent', color: m.color }}>{m.status}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* ML Predictions */}
                                    {activePage === 'ml-predictions' && (
                                        <motion.div key="predictions" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-auto md:h-full p-4 overflow-visible md:overflow-auto">
                                            <div className="flex items-center gap-2 mb-4">
                                                <div className="p-1.5 rounded-lg" style={{ backgroundColor: `${accent}20` }}>
                                                    <BrainCircuit className="w-4 h-4" style={{ color: accent }} />
                                                </div>
                                                <div>
                                                    <h2 className="text-sm font-semibold" style={{ color: demoText }}>ML Predictions</h2>
                                                    <p className="text-[10px]" style={{ color: demoMuted }}>Target: Sentiment • Task: multiclass_classification • 213.4s</p>
                                                </div>
                                                <button className="ml-auto text-[10px] px-3 py-1.5 rounded border" style={{ borderColor: demoBorder, color: demoText }}>New Training</button>
                                            </div>

                                            {/* Top Cards */}
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                                                <div className="p-3 rounded-xl border relative overflow-hidden" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <div className="w-1 h-3 rounded-full" style={{ backgroundColor: accent }} />
                                                        <span className="text-[10px]" style={{ color: demoMuted }}>Best Model</span>
                                                    </div>
                                                    <p className="text-lg font-bold" style={{ color: accent }}>LightGBM</p>
                                                </div>
                                                <div className="p-3 rounded-xl border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <div className="p-1 rounded bg-blue-500/10"><Activity className="w-3 h-3 text-blue-500" /></div>
                                                        <span className="text-[10px]" style={{ color: demoMuted }}>F1 Score</span>
                                                    </div>
                                                    <p className="text-lg font-bold text-[#ef4444]">28.5%</p>
                                                </div>
                                                <div className="p-3 rounded-xl border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <div className="p-1 rounded bg-green-500/10"><Layers className="w-3 h-3 text-green-500" /></div>
                                                        <span className="text-[10px]" style={{ color: demoMuted }}>Models Trained</span>
                                                    </div>
                                                    <p className="text-lg font-bold text-green-500">4</p>
                                                </div>
                                                <div className="p-3 rounded-xl border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <div className="p-1 rounded bg-amber-500/10"><Zap className="w-3 h-3 text-amber-500" /></div>
                                                        <span className="text-[10px]" style={{ color: demoMuted }}>Features</span>
                                                    </div>
                                                    <p className="text-lg font-bold text-amber-500">15</p>
                                                </div>
                                            </div>

                                            {/* Tabs */}
                                            <div className="flex gap-1 mb-4 border-b" style={{ borderColor: demoBorder }}>
                                                {['Overview', 'ML Charts', 'Features', 'Make Prediction'].map(tab => (
                                                    <button
                                                        key={tab}
                                                        className={`px-4 py-2 text-[10px] font-medium border-b-2 transition-colors ${activeTab === tab ? '' : 'border-transparent'}`}
                                                        style={{
                                                            borderColor: activeTab === tab ? accent : 'transparent',
                                                            color: activeTab === tab ? accent : demoMuted,
                                                            backgroundColor: activeTab === tab ? `${accent}15` : 'transparent'
                                                        }}
                                                    >
                                                        {tab}
                                                    </button>
                                                ))}
                                            </div>

                                            {/* Overview Tab Content (Image 2) */}
                                            {activeTab === 'Overview' && (
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    {/* All Models Performance */}
                                                    <div className="p-3 rounded-xl border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <p className="text-[10px] font-medium mb-3" style={{ color: demoText }}>All Models Performance</p>
                                                        <div className="space-y-3">
                                                            {[
                                                                { name: 'LightGBM', val: 28.5, color: '#10b981', best: true },
                                                                { name: 'RandomForest', val: 26.8, color: '#3b82f6', best: false },
                                                                { name: 'HistGradientBoosting', val: 26.4, color: '#3b82f6', best: false },
                                                                { name: 'LogisticRegression', val: 14.8, color: '#3b82f6', best: false },
                                                            ].map((m, i) => (
                                                                <div key={i}>
                                                                    <div className="flex justify-between text-[9px] mb-1" style={{ color: demoMuted }}>
                                                                        <span>{m.name}</span>
                                                                        <span className="font-bold" style={{ color: demoText }}>{m.val}%</span>
                                                                    </div>
                                                                    <div className="h-1.5 w-full rounded-full overflow-hidden flex items-center" style={{ backgroundColor: `${demoBorder}` }}>
                                                                        <div className="h-full rounded-full" style={{ width: `${m.val * 3}%`, backgroundColor: m.color }} />
                                                                        {m.best && <span className="ml-2 text-[8px] px-1 rounded" style={{ backgroundColor: `${accent}20`, color: accent }}>BEST</span>}
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    {/* AI Insights Card */}
                                                    <div className="space-y-2">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <Zap className="w-3 h-3 text-amber-500" />
                                                            <span className="text-[10px] font-medium" style={{ color: demoText }}>AI Insights</span>
                                                        </div>
                                                        <div className="p-2 rounded border flex items-center gap-2" style={{ backgroundColor: `${demoBg}`, borderColor: demoBorder }}>
                                                            <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                                                            <span className="text-[9px]" style={{ color: demoMuted }}>Best model: LightGBM</span>
                                                        </div>
                                                        <div className="p-2 rounded border flex items-center gap-2" style={{ backgroundColor: `${demoBg}`, borderColor: demoBorder }}>
                                                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                                                            <span className="text-[9px]" style={{ color: demoMuted }}>Trained on 732 samples with 10 features</span>
                                                        </div>
                                                        <div className="p-2 rounded border flex items-center gap-2" style={{ backgroundColor: `${demoBg}`, borderColor: demoBorder }}>
                                                            <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                                            <span className="text-[9px]" style={{ color: demoMuted }}>Task type: multiclass_classification</span>
                                                        </div>
                                                        <div className="p-2 rounded border flex items-center gap-2" style={{ backgroundColor: `${demoBg}`, borderColor: demoBorder }}>
                                                            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                                            <span className="text-[9px]" style={{ color: demoMuted }}>Found 2 natural clusters in your data</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* ML Charts Tab Content (Image 3) */}
                                            {activeTab === 'ML Charts' && (
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-auto md:h-64">
                                                    {/* Model Comparison Chart */}
                                                    <div className="p-2 rounded-xl border flex flex-col" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <span className="text-[9px] mb-1" style={{ color: demoText }}>Model Comparison</span>
                                                        <div className="flex-1 flex flex-col justify-center gap-1">
                                                            {[
                                                                { w: 80, c: '#10b981' },
                                                                { w: 75, c: '#3b82f6' },
                                                                { w: 74, c: '#3b82f6' },
                                                                { w: 40, c: '#3b82f6' }
                                                            ].map((item, i) => (
                                                                <div key={i} className="h-4 rounded opacity-90 transition-all duration-500" style={{ width: `${item.w}%`, backgroundColor: item.c }} />
                                                            ))}
                                                        </div>
                                                    </div>
                                                    {/* Training Time Chart */}
                                                    <div className="p-2 rounded-xl border flex flex-col" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <span className="text-[9px] mb-1" style={{ color: demoText }}>Training Time</span>
                                                        <div className="flex-1 flex items-end justify-between gap-1 px-2">
                                                            {[42.1, 10.8, 148.2, 2.6].map((val, i) => (
                                                                <div key={i} className="flex-1 flex flex-col justify-end items-center group">
                                                                    <div className="text-[8px] mb-1 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: demoMuted }}>{val}s</div>
                                                                    <div className="w-full rounded-t transition-all duration-500" style={{ height: `${(val / 150) * 100}%`, backgroundColor: '#0ea5e9', minHeight: '4px' }} />
                                                                </div>
                                                            ))}
                                                        </div>
                                                        <div className="flex justify-between mt-1 text-[8px]" style={{ color: demoMuted }}>
                                                            <span>LGBM</span>
                                                            <span>RF</span>
                                                            <span>HGB</span>
                                                            <span>LR</span>
                                                        </div>
                                                    </div>
                                                    {/* Feature Importance */}
                                                    <div className="p-2 rounded-xl border flex flex-col" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <span className="text-[9px] mb-1" style={{ color: demoText }}>Feature Importance</span>
                                                        <div className="flex-1 flex flex-col justify-center gap-1">
                                                            {[
                                                                { w: 90, l: 'Sentiment' },
                                                                { w: 45, l: 'Length' },
                                                                { w: 30, l: 'Time' }
                                                            ].map((item, i) => (
                                                                <div key={i} className="flex items-center gap-2">
                                                                    <div className="h-3 rounded bg-indigo-500 opacity-80" style={{ width: `${item.w}%` }} />
                                                                    <span className="text-[8px]" style={{ color: demoMuted }}>{item.l}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    {/* Confusion Matrix */}
                                                    <div className="p-2 rounded-xl border flex flex-col" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <span className="text-[9px] mb-1" style={{ color: demoText }}>Confusion Matrix</span>
                                                        <div className="flex-1 grid grid-cols-4 gap-0.5 p-2">
                                                            {[10, 2, 0, 1, 3, 15, 1, 0, 0, 2, 12, 1, 1, 0, 3, 18].map((val, i) => (
                                                                <div key={i} className="rounded-sm flex items-center justify-center text-[8px]" style={{ backgroundColor: `rgba(16, 185, 129, ${val / 20})`, color: val > 10 ? '#fff' : demoMuted }}>
                                                                    {val > 0 && val}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Features Tab Content (Image 2) */}
                                            {activeTab === 'Features' && (
                                                <div className="h-64 overflow-auto">
                                                    <h3 className="text-[10px] font-semibold mb-2" style={{ color: demoText }}>Feature Importance Ranking</h3>
                                                    <div className="space-y-2">
                                                        {[
                                                            { id: 1, name: 'Feature_0', val: 29.4 },
                                                            { id: 2, name: 'Feature_7', val: 14.4 },
                                                            { id: 3, name: 'Feature_6', val: 14.1 },
                                                            { id: 4, name: 'Feature_2', val: 10.8 },
                                                            { id: 5, name: 'Feature_5', val: 10.1 },
                                                            { id: 6, name: 'Feature_4', val: 8.0 },
                                                            { id: 7, name: 'Feature_3', val: 3.5 },
                                                            { id: 8, name: 'Feature_8', val: 3.3 },
                                                            { id: 9, name: 'Feature_45', val: 1.5 },
                                                        ].map((feat) => (
                                                            <div key={feat.id} className="flex items-center gap-2">
                                                                <div className="w-5 h-5 rounded flex items-center justify-center text-[9px] font-bold text-white shrink-0" style={{ backgroundColor: accent }}>
                                                                    {feat.id}
                                                                </div>
                                                                <div className="flex-1">
                                                                    <div className="flex justify-between items-center mb-0.5">
                                                                        <span className="text-[9px] font-medium" style={{ color: demoText }}>{feat.name}</span>
                                                                        <span className="text-[9px] font-bold" style={{ color: accent }}>{feat.val}%</span>
                                                                    </div>
                                                                    <div className="h-1.5 w-full bg-gray-700/50 rounded-full overflow-hidden">
                                                                        <div className="h-full rounded-full" style={{ width: `${feat.val}%`, backgroundColor: accent }} />
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Make Prediction Tab Content (Image 3) */}
                                            {activeTab === 'Make Prediction' && (
                                                <div className="h-64 overflow-auto">
                                                    <h3 className="text-[10px] font-semibold mb-3" style={{ color: demoText }}>Make a Prediction with LightGBM</h3>
                                                    <div className="grid grid-cols-3 gap-3 mb-4">
                                                        {[
                                                            { label: 'Unnamed: 0.1 (numeric)', placeholder: 'e.g. 366.5' },
                                                            { label: 'Unnamed: 0 (numeric)', placeholder: 'e.g. 369.7' },
                                                            { label: 'Retweets (numeric)', placeholder: 'e.g. 21.5' },
                                                            { label: 'Likes (numeric)', placeholder: 'e.g. 42.9' },
                                                            { label: 'Year (numeric)', placeholder: 'e.g. 2020.5' },
                                                            { label: 'Month (numeric)', placeholder: 'e.g. 6.1' },
                                                            { label: 'Day (numeric)', placeholder: 'e.g. 15.5' },
                                                            { label: 'Hour (numeric)', placeholder: 'e.g. 15.5' },
                                                        ].map((input, i) => (
                                                            <div key={i}>
                                                                <label className="text-[8px] mb-1 block" style={{ color: demoMuted }}>{input.label}</label>
                                                                <input
                                                                    type="text"
                                                                    placeholder={input.placeholder}
                                                                    className="w-full px-2 py-1.5 rounded text-[9px] bg-transparent border outline-none"
                                                                    style={{ borderColor: demoBorder, color: demoText }}
                                                                />
                                                            </div>
                                                        ))}
                                                        <div>
                                                            <label className="text-[8px] mb-1 block" style={{ color: demoMuted }}>Platform (select)</label>
                                                            <div className="w-full px-2 py-1.5 rounded text-[9px] border flex justify-between items-center" style={{ borderColor: demoBorder, color: demoText }}>
                                                                Select Platform <ChevronDown className="w-3 h-3" />
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <button className="px-4 py-2 rounded-lg text-[10px] font-semibold text-white flex items-center gap-2" style={{ backgroundColor: accent }}>
                                                        <Zap className="w-3 h-3" /> Get Prediction
                                                    </button>
                                                </div>
                                            )}
                                            {false && (
                                                <div className="grid grid-cols-2 gap-4 h-64">
                                                    {/* Model Comparison Chart */}
                                                    <div className="p-2 rounded-xl border flex flex-col" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <span className="text-[9px] mb-1" style={{ color: demoText }}>Model Comparison</span>
                                                        <div className="flex-1 flex flex-col justify-center gap-1">
                                                            {[80, 75, 74, 40].map((w, i) => (
                                                                <div key={i} className="h-4 rounded bg-orange-500 opacity-90" style={{ width: `${w}%` }} />
                                                            ))}
                                                        </div>
                                                    </div>
                                                    {/* Training Time Chart */}
                                                    <div className="p-2 rounded-xl border flex flex-col" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <span className="text-[9px] mb-1" style={{ color: demoText }}>Training Time</span>
                                                        <div className="flex-1 flex items-end justify-between gap-1 px-2">
                                                            {[30, 20, 90, 10].map((h, i) => (
                                                                <div key={i} className="flex-1 bg-cyan-600 rounded-t" style={{ height: `${h}%` }} />
                                                            ))}
                                                        </div>
                                                    </div>
                                                    {/* Feature Importance */}
                                                    <div className="p-2 rounded-xl border flex flex-col" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <span className="text-[9px] mb-1" style={{ color: demoText }}>Feature Importance</span>
                                                        <div className="flex-1 flex flex-col justify-center gap-1">
                                                            {[90, 45, 30].map((w, i) => (
                                                                <div key={i} className="h-3 rounded bg-indigo-500 opacity-80" style={{ width: `${w}%` }} />
                                                            ))}
                                                        </div>
                                                    </div>
                                                    {/* Confusion Matrix */}
                                                    <div className="p-2 rounded-xl border flex flex-col" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                        <span className="text-[9px] mb-1" style={{ color: demoText }}>Confusion Matrix</span>
                                                        <div className="flex-1 grid grid-cols-4 gap-0.5 p-2">
                                                            {[...Array(16)].map((_, i) => (
                                                                <div key={i} className="bg-gray-700 rounded-sm" style={{ opacity: Math.random() }} />
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </motion.div>
                                    )}

                                    {/* Chat */}
                                    {activePage === 'chat' && (
                                        <motion.div key="chat" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-auto md:h-full flex flex-col">
                                            <div className="px-5 py-3 border-b" style={{ borderColor: demoBorder }}>
                                                <p className="text-sm font-semibold" style={{ color: demoText }}>Analyst Chat</p>
                                                <p className="text-[10px]" style={{ color: demoMuted }}>RAG Mode • 10 Active Tools</p>
                                            </div>

                                            <div className="p-5 md:flex-1 overflow-visible md:overflow-auto relative">
                                                {/* MCP Panel */}
                                                <AnimatePresence>
                                                    {showMCPPanel && (
                                                        <motion.div initial={{ opacity: 0, y: 10, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 10, scale: 0.95 }} className="absolute left-5 top-16 w-64 rounded-xl shadow-xl z-40 p-4" style={{ backgroundColor: isDark ? '#1a1f2e' : '#ffffff', border: `1px solid ${demoBorder}` }}>
                                                            <div className="flex items-center justify-between mb-3">
                                                                <span className="text-sm font-medium" style={{ color: demoText }}>MCP SERVERS</span>
                                                                <span className="text-[10px]" style={{ color: accent }}>10/10 active</span>
                                                            </div>
                                                            {[
                                                                { name: 'Data Cleaner', icon: Shield, color: '#f59e0b' },
                                                                { name: 'Data Transformer', icon: RefreshCw, color: '#8b5cf6' },
                                                                { name: 'Data Validator', icon: Check, color: '#22c55e' },
                                                                { name: 'Vectorizer', icon: Layers, color: '#3b82f6' },
                                                                { name: 'Graph Builder', icon: GitBranch, color: '#ec4899' },
                                                            ].map((mcp) => (
                                                                <div key={mcp.name} className="flex items-center gap-3 py-2">
                                                                    <div className="w-6 h-6 rounded flex items-center justify-center" style={{ backgroundColor: `${mcp.color}20` }}>
                                                                        <mcp.icon className="w-3 h-3" style={{ color: mcp.color }} />
                                                                    </div>
                                                                    <div className="flex-1">
                                                                        <p className="text-xs" style={{ color: demoText }}>{mcp.name}</p>
                                                                    </div>
                                                                    <div className="w-8 h-4 rounded-full relative" style={{ backgroundColor: `${accent}30` }}>
                                                                        <div className="absolute top-0.5 w-3 h-3 rounded-full" style={{ backgroundColor: accent, left: '16px' }} />
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>

                                                {/* Welcome */}
                                                <div className="flex gap-3 mb-4">
                                                    <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${accent}20` }}>
                                                        <LogoImage size={16} className="rounded-sm" />
                                                    </div>
                                                    <p className="text-sm" style={{ color: demoText }}>
                                                        Hello! I'm your AI Data Analyst. Upload any data file and I'll help you analyze it.
                                                    </p>
                                                </div>

                                                {/* User Message */}
                                                {typing && (
                                                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end mb-4">
                                                        <div className="px-4 py-2 rounded-2xl text-sm max-w-xs text-white" style={{ backgroundColor: '#475569' }}>
                                                            {typing}
                                                        </div>
                                                    </motion.div>
                                                )}

                                                {/* Permission */}
                                                {showPermission && (
                                                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-4">
                                                        <div className="flex gap-3">
                                                            <Zap className="w-5 h-5 mt-1" style={{ color: '#f59e0b' }} />
                                                            <div className="flex-1 p-4 rounded-xl" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                                <div className="flex items-center gap-2 mb-2">
                                                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#f59e0b' }} />
                                                                    <span className="text-sm font-medium" style={{ color: demoText }}>Permission Required</span>
                                                                </div>
                                                                <p className="text-xs mb-3" style={{ color: demoMuted }}>DataVision wants to use the following tools:</p>
                                                                <div className="flex items-center gap-3 p-3 rounded-lg mb-3" style={{ backgroundColor: `${accent}10`, border: `1px solid ${accent}30` }}>
                                                                    <Check className="w-4 h-4" style={{ color: '#22c55e' }} />
                                                                    <div>
                                                                        <p className="text-xs font-medium" style={{ color: demoText }}>Data Validator</p>
                                                                        <p className="text-[10px]" style={{ color: demoMuted }}>Check data quality and validate schema</p>
                                                                    </div>
                                                                </div>
                                                                <div className="flex justify-end gap-2">
                                                                    <button className="px-4 py-1.5 rounded-lg text-xs" style={{ color: demoMuted }}>Deny</button>
                                                                    <button className="px-4 py-1.5 rounded-lg text-xs text-white" style={{ backgroundColor: accent }}>Allow</button>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                )}

                                                {/* Running MCP Tools - After Allow */}
                                                {showRunningMCP && (
                                                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-4">
                                                        {/* Running MCP Tools Card */}
                                                        <div className="flex gap-3 mb-3">
                                                            <Settings className="w-5 h-5 mt-0.5" style={{ color: '#8B5CF6' }} />
                                                            <div className="flex-1 p-3 rounded-xl" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                                <p className="text-xs font-medium mb-2" style={{ color: demoText }}>Running MCP Tools</p>
                                                                <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ backgroundColor: `${accent}10`, border: `1px solid ${accent}30` }}>
                                                                    <Check className="w-4 h-4" style={{ color: '#22c55e' }} />
                                                                    <span className="text-xs flex-1" style={{ color: demoText }}>Data Validator</span>
                                                                    <span className="text-[10px] font-medium" style={{ color: accent }}>Done</span>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Searching documents... */}
                                                        <div className="flex gap-3">
                                                            <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${accent}20` }}>
                                                                <LogoImage size={16} className="rounded-sm" />
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <motion.span
                                                                    animate={{ opacity: [0.3, 1, 0.3] }}
                                                                    transition={{ duration: 1.5, repeat: Infinity }}
                                                                    className="w-2 h-2 rounded-full"
                                                                    style={{ backgroundColor: accent }}
                                                                />
                                                                <motion.span
                                                                    animate={{ opacity: [0.3, 1, 0.3] }}
                                                                    transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                                                                    className="w-2 h-2 rounded-full"
                                                                    style={{ backgroundColor: accent }}
                                                                />
                                                                <motion.span
                                                                    animate={{ opacity: [0.3, 1, 0.3] }}
                                                                    transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                                                                    className="w-2 h-2 rounded-full"
                                                                    style={{ backgroundColor: accent }}
                                                                />
                                                                <span className="text-sm ml-2" style={{ color: demoMuted }}>Searching documents...</span>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                )}

                                                {/* ChatGPT Response */}
                                                {responseText && (
                                                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                                                        <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${accent}20` }}>
                                                            <LogoImage size={16} className="rounded-sm" />
                                                        </div>
                                                        <div className="flex-1 text-sm" style={{ color: demoText }}>
                                                            {responseText.split('\n').map((line, i) => (
                                                                <p key={i} className={line.startsWith('**') ? 'font-semibold mt-3 mb-1' : line.startsWith('•') ? 'ml-2' : 'mb-2'}>
                                                                    {line.replace(/\*\*/g, '')}
                                                                </p>
                                                            ))}
                                                            {responseText.length < fullResponse.length && (
                                                                <motion.span animate={{ opacity: [1, 0, 1] }} transition={{ duration: 0.8, repeat: Infinity }} className="inline-block w-2 h-4 ml-1" style={{ backgroundColor: accent }} />
                                                            )}
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </div>

                                            {/* Input - FIXED text color for white theme */}
                                            <div className="p-4 border-t" style={{ borderColor: demoBorder }}>
                                                <div className="flex items-center gap-3 px-4 py-3 rounded-2xl" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <FileText className="w-4 h-4" style={{ color: demoMuted }} />
                                                    <input
                                                        type="text"
                                                        placeholder="Ask anything..."
                                                        className="flex-1 bg-transparent text-sm outline-none"
                                                        style={{ color: inputText }}
                                                        value={typing}
                                                        readOnly
                                                    />
                                                    <Mic className="w-4 h-4" style={{ color: demoMuted }} />
                                                    <div className="px-2 py-1 rounded-lg text-xs text-white" style={{ backgroundColor: accent }}>
                                                        RAG <ChevronDown className="w-3 h-3 inline" />
                                                    </div>
                                                    <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: accent }}>
                                                        <ChevronRight className="w-4 h-4 text-white" />
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* Reports */}
                                    {activePage === 'reports' && (
                                        <motion.div key="reports" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-auto md:h-full p-5 overflow-visible md:overflow-auto">
                                            <div className="mb-4">
                                                <h2 className="text-base font-semibold" style={{ color: demoText }}>Data Reports</h2>
                                                <p className="text-xs" style={{ color: accent }}>Automatic reports generated from your uploaded data</p>
                                            </div>

                                            <div className="grid grid-cols-4 gap-3 mb-4">
                                                {[
                                                    { icon: TrendingUp, label: 'Total Revenue', value: '₹13,85,149' },
                                                    { icon: FileText, label: 'Total Records', value: '100' },
                                                    { icon: Users, label: 'Unique Entities', value: '4' },
                                                    { icon: Clock, label: 'Categories', value: '100' },
                                                ].map((stat, i) => (
                                                    <div key={i} className="p-3 rounded-xl" style={{ backgroundColor: demoCard }}>
                                                        <stat.icon className="w-4 h-4 mb-1" style={{ color: accent }} />
                                                        <p className="text-lg font-bold" style={{ color: demoText }}>{stat.value}</p>
                                                        <p className="text-[10px]" style={{ color: demoMuted }}>{stat.label}</p>
                                                    </div>
                                                ))}
                                            </div>

                                            <div className="mb-4">
                                                <p className="text-sm font-medium mb-3" style={{ color: demoText }}>Generate New Report</p>
                                                <div className="grid grid-cols-4 gap-3">
                                                {['Metrics Analysis', 'Data Summary', 'Executive Summary', 'Predictive Report'].map((report, i) => (
                                                        <div key={i} className="p-3 rounded-xl" style={{ backgroundColor: i === 0 ? `${accent}15` : demoCard, border: i === 0 ? `2px solid ${accent}` : `1px solid ${demoBorder}` }}>
                                                            <PieChart className="w-4 h-4 mb-1" style={{ color: i === 0 ? accent : demoMuted }} />
                                                            <p className="text-xs font-medium" style={{ color: demoText }}>{report}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                                <button className="w-full mt-3 py-2.5 rounded-xl text-sm font-medium text-white flex items-center justify-center gap-2" style={{ backgroundColor: accent }}>
                                                    {reportGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                                                    {reportGenerating ? 'Generating Report...' : 'Generate Metrics Analysis'}
                                                </button>
                                            </div>

                                            {/* Generated Report */}
                                            {scene >= 6 && (
                                                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="p-4 rounded-xl" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <div className="flex items-center justify-between mb-3">
                                                        <div className="flex items-center gap-2">
                                                            <Check className="w-4 h-4" style={{ color: accent }} />
                                                            <span className="text-sm font-medium" style={{ color: demoText }}>Metrics Analysis Report</span>
                                                        </div>
                                                        <button className="text-[10px] px-2 py-1 rounded flex items-center gap-1" style={{ color: '#ef4444', backgroundColor: '#ef444420' }}>
                                                            <Download className="w-3 h-3" /> Export PDF
                                                        </button>
                                                    </div>
                                                    <p className="text-[10px] mb-3" style={{ color: demoMuted }}>Generated: 12/26/2025 | Source: uploaded_files</p>
                                                    <div className="text-xs space-y-1" style={{ color: demoText }}>
                                                        <p style={{ color: accent }}>Data Overview</p>
                                                        <p>Total Records: 100 | Columns: 7 | Focus: Product</p>
                                                    </div>
                                                </motion.div>
                                            )}

                                        </motion.div>
                                    )}

                                    {/* Settings */}
                                    {activePage === 'settings' && (
                                        <motion.div key="settings" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-auto md:h-full p-6 overflow-visible md:overflow-auto">
                                            <h2 className="text-lg font-semibold mb-6" style={{ color: demoText }}>Settings</h2>

                                            {/* Preferences */}
                                            <div className="mb-8">
                                                <div className="flex items-center gap-2 mb-4">
                                                    <Shield className="w-4 h-4" style={{ color: accent }} />
                                                    <h3 className="text-sm font-medium" style={{ color: demoText }}>Preferences</h3>
                                                </div>
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div>
                                                        <label className="text-xs mb-1.5 block" style={{ color: demoMuted }}>Theme</label>
                                                        <div className="p-2 rounded-lg border text-sm flex justify-between items-center" style={{ backgroundColor: demoBg, borderColor: demoBorder, color: demoText }}>
                                                            Dark <ChevronDown className="w-3 h-3" />
                                                        </div>
                                                        <p className="text-[10px] mt-1 cursor-pointer" style={{ color: accent }}>Reset to Dark Mode</p>
                                                    </div>
                                                    <div>
                                                        <label className="text-xs mb-1.5 block" style={{ color: demoMuted }}>Language</label>
                                                        <div className="p-2 rounded-lg border text-sm flex justify-between items-center" style={{ backgroundColor: demoBg, borderColor: demoBorder, color: demoMuted }}>
                                                            English (Only)
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Email Reports */}
                                            <div className="p-4 rounded-xl border" style={{ backgroundColor: demoCard, borderColor: demoBorder }}>
                                                <div className="flex items-center gap-2 mb-4">
                                                    <MessageSquare className="w-4 h-4" style={{ color: accent }} />
                                                    <h3 className="text-sm font-medium" style={{ color: demoText }}>Email Reports</h3>
                                                </div>

                                                <div className="mb-4">
                                                    <label className="text-xs mb-1.5 block" style={{ color: demoMuted }}>Email Address for Reports</label>
                                                    <input type="text" value="naveenkumarchapala686@gmail.com" className="w-full p-2 rounded-lg border text-sm" style={{ backgroundColor: demoBg, borderColor: demoBorder, color: demoText }} readOnly />
                                                    <p className="text-[10px] mt-1" style={{ color: demoMuted }}>Leave blank to use your account email</p>
                                                </div>

                                                <div className="flex items-center justify-between mb-4">
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <Clock className="w-3 h-3 text-green-500" />
                                                            <p className="text-sm font-medium" style={{ color: demoText }}>Daily Reports</p>
                                                        </div>
                                                        <p className="text-[10px]" style={{ color: demoMuted }}>Receive daily data insights from DataVision</p>
                                                    </div>
                                                    <div className="w-8 h-4 rounded-full relative transition-colors" style={{ backgroundColor: accent }}>
                                                        <div className="absolute right-0.5 top-0.5 w-3 h-3 bg-white rounded-full shadow-sm" />
                                                    </div>
                                                </div>

                                                <div className="flex gap-2 mt-6">
                                                    <button className="px-3 py-2 rounded-lg text-[10px] font-medium text-white shadow-lg" style={{ backgroundColor: accent, boxShadow: `0 4px 10px ${accent}40` }}>Save Email Preferences</button>
                                                    <button className="px-3 py-2 rounded-lg text-[10px] font-medium border" style={{ borderColor: demoBorder, color: demoText }}>Send Test Email</button>
                                                    <button className="px-3 py-2 rounded-lg text-[10px] font-medium text-white flex items-center gap-2" style={{ backgroundColor: '#10b981' }}>
                                                        <MessageSquare className="w-3 h-3" /> Send Daily Report Now
                                                    </button>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section >

            {/* Core Capabilities - Premium Style (Compact) */}
            < section className="py-20 px-6 relative overflow-hidden" >
                <div className="max-w-7xl mx-auto relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-4xl lg:text-5xl font-extrabold tracking-tight mb-4 text-white">
                            One Platform. <span style={{ color: accent }}>Infinite Intelligence.</span>
                        </h2>
                        <p className="text-lg md:text-xl max-w-3xl mx-auto font-medium" style={{ color: isDark ? '#e2e8f0' : '#475569' }}>
                            From raw spreadsheet to production-ready ML model in <span className="text-white">under 60 seconds.</span>
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Capability 1: AutoML Engine */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            className="group p-8 rounded-[1.5rem] border transition-all duration-300 hover:-translate-y-1 hover:shadow-xl flex flex-col"
                            style={{
                                backgroundColor: isDark ? '#0f172a' : '#ffffff',
                                borderColor: border ? border : 'rgba(255,255,255,0.1)',
                            }}
                        >
                            <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-6 border" style={{ borderColor: `${accent}40`, backgroundColor: `${accent}10` }}>
                                <BrainCircuit className="w-6 h-6" style={{ color: accent }} />
                            </div>

                            <h3 className="text-xl font-bold mb-3 text-white">Ultra AutoML Engine</h3>

                            <p className="text-sm font-bold mb-2 text-white">
                                One click. 15+ algorithms. Best model selected.
                            </p>
                            <p className="text-sm leading-relaxed mb-6 flex-1" style={{ color: textMuted }}>
                                Upload any CSV or Excel file and watch the system automatically train XGBoost, LightGBM, Random Forest, Neural Networks, and 10+ other algorithms — then select the champion model with production-ready metrics.
                            </p>

                            <div className="flex flex-wrap gap-2 mt-auto">
                                <span className="px-2.5 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider border" style={{ borderColor: `${accent}30`, color: accent, backgroundColor: `${accent}05` }}>
                                    One-Click Training
                                </span>
                                <span className="px-2.5 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider border" style={{ borderColor: `${accent}30`, color: accent, backgroundColor: `${accent}05` }}>
                                    Auto Feature Engineering
                                </span>
                            </div>
                        </motion.div>

                        {/* Capability 2: Predictive Analytics */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.1 }}
                            className="group p-8 rounded-[1.5rem] border transition-all duration-300 hover:-translate-y-1 hover:shadow-xl flex flex-col"
                            style={{
                                backgroundColor: isDark ? '#0f172a' : '#ffffff',
                                borderColor: border ? border : 'rgba(255,255,255,0.1)',
                            }}
                        >
                            <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-6 border" style={{ borderColor: '#f59e0b40', backgroundColor: '#f59e0b10' }}>
                                <Target className="w-6 h-6 text-amber-500" />
                            </div>

                            <h3 className="text-xl font-bold mb-3 text-white">Autonomous Dashboards</h3>

                            <p className="text-sm font-bold mb-2 text-white">
                                15+ visualizations. Zero configuration.
                            </p>
                            <p className="text-sm leading-relaxed mb-6 flex-1" style={{ color: textMuted }}>
                                The system analyzes your data structure and automatically generates the perfect mix of charts — scatter plots, heatmaps, sunbursts, trend lines, correlation matrices — tailored to reveal the insights that matter most.
                            </p>

                            <div className="flex flex-wrap gap-2 mt-auto">
                                <span className="px-2.5 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider border" style={{ borderColor: '#f59e0b30', color: '#f59e0b', backgroundColor: '#f59e0b05' }}>
                                    Auto-Generated
                                </span>
                                <span className="px-2.5 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider border" style={{ borderColor: '#f59e0b30', color: '#f59e0b', backgroundColor: '#f59e0b05' }}>
                                    Real-Time KPIs
                                </span>
                            </div>
                        </motion.div>

                        {/* Capability 3: Smart Reporting */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.2 }}
                            className="group p-8 rounded-[1.5rem] border transition-all duration-300 hover:-translate-y-1 hover:shadow-xl flex flex-col"
                            style={{
                                backgroundColor: isDark ? '#0f172a' : '#ffffff',
                                borderColor: border ? border : 'rgba(255,255,255,0.1)',
                            }}
                        >
                            <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-6 border" style={{ borderColor: '#8b5cf640', backgroundColor: '#8b5cf610' }}>
                                <Zap className="w-6 h-6 text-violet-500" />
                            </div>

                            <h3 className="text-xl font-bold mb-3 text-white">LLM-Powered Analyst</h3>

                            <p className="text-sm font-bold mb-2 text-white">
                                Ask anything. Get executive answers.
                            </p>
                            <p className="text-sm leading-relaxed mb-6 flex-1" style={{ color: textMuted }}>
                                A conversational AI analyst that understands your data context. Generate 6 types of reports, get anomaly detection, predictive insights, and executive summaries — all through natural language.
                            </p>

                            <div className="flex flex-wrap gap-2 mt-auto">
                                <span className="px-2.5 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider border" style={{ borderColor: '#8b5cf630', color: '#8b5cf6', backgroundColor: '#8b5cf605' }}>
                                    Natural Language
                                </span>
                                <span className="px-2.5 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider border" style={{ borderColor: '#8b5cf630', color: '#8b5cf6', backgroundColor: '#8b5cf605' }}>
                                    6 Report Types
                                </span>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section >

            {/* Why Different Section - Premium Copy */}
            < section className="py-20 px-6" style={{ backgroundColor: isDark ? 'rgba(20, 184, 166, 0.03)' : 'rgba(20, 184, 166, 0.05)' }}>
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">
                        Why This Is <span style={{ color: accent }}>Different</span>
                    </h2>

                    <p className="text-center mb-6 max-w-3xl mx-auto leading-relaxed" style={{ color: textMuted }}>
                        DataVision isn't another BI tool that requires weeks of setup. It's an autonomous intelligence system
                        that starts working the moment you upload your first file.
                    </p>

                    <p className="text-center mb-12 max-w-3xl mx-auto leading-relaxed" style={{ color: textMuted }}>
                        No data engineering. No model configuration. No dashboard building.
                        The system handles everything — from data cleaning to ML training to executive reporting —
                        so you can focus on decisions, not infrastructure.
                    </p>

                    <h3 className="text-xl font-semibold text-center mb-8" style={{ color: text }}>
                        What You Get Out of the Box
                    </h3>

                    <div className="space-y-4 max-w-2xl mx-auto">
                        {[
                            'Ultra AutoML: Train 15+ algorithms with one click, get the champion model',
                            'Autonomous Dashboards: 15+ intelligent visualizations generated automatically',
                            'LLM-Powered Analyst: Ask questions in natural language, get executive answers',
                            '5 Report Types: Metrics, Summary, Executive, Predictive, Anomaly',
                            'Production-Ready Predictions: Make real predictions on new data instantly',
                        ].map((item, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="flex items-center gap-4 py-3 border-b"
                                style={{ borderColor: border }}
                            >
                                <Check className="w-5 h-5 flex-shrink-0" style={{ color: accent }} />
                                <p className="text-base" style={{ color: text }}>{item}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section >

            {/* Final Statement */}
            < section className="py-24 px-6" >
                <div className="max-w-3xl mx-auto text-center">
                    <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-12">
                        This is an <span style={{ color: accent }}>autonomous intelligence system</span> that continuously understands your data.
                    </h2>
                    <div className="flex flex-wrap items-center justify-center gap-4">
                        <button
                            onClick={() => navigate('/data-hub')}
                            className="flex items-center gap-2 text-base font-semibold px-8 py-4 rounded-xl text-white transition-all hover:scale-105"
                            style={{ backgroundColor: accent, boxShadow: `0 8px 30px ${accent}40` }}
                        >
                            Start with your data
                            <ArrowRight className="w-5 h-5" />
                        </button>
                        <button
                            onClick={() => navigate('/signup')}
                            className="text-base px-8 py-4 rounded-xl border transition-colors"
                            style={{ borderColor: border, color: textMuted }}
                        >
                            Request access
                        </button>
                    </div>
                </div>
            </section >

            {/* Footer */}
            < footer className="py-8 px-6 border-t" style={{ borderColor: border }}>
                <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <AnimatedLogo size="sm" showText={true} isDark={isDark} />
                    </div>
                    <div className="flex items-center gap-6 text-sm" style={{ color: textMuted }}>
                        <Link to="/privacy" className="hover:text-green-400 transition-colors">Privacy Policy</Link>
                        <Link to="/terms" className="hover:text-green-400 transition-colors">Terms of Service</Link>
                        <Link to="/help" className="hover:text-green-400 transition-colors">Help Center</Link>
                    </div>
                    <p className="text-xs text-center" style={{ color: textMuted }}>
                        © 2026 DataVision. Enterprise Analytics Platform.
                    </p>
                </div>
            </footer >
        </div >
    );
};

export default Landing;
