/**
 * Landing Page — DataVision
 * Autonomous Data Intelligence Platform
 * 
 * Complete interactive demo - auto-playing
 * Premium $500M+ grade copy
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Sun, Moon, ArrowRight, Check, Upload,
    Home, BarChart2, Database, FileText, MessageSquare, Settings,
    ChevronRight, ChevronDown, TrendingUp, Search, Mic, Download,
    Shield, RefreshCw, Layers, GitBranch, Zap, Clock,
    PieChart, Activity, Users, Loader2, LayoutDashboard, BrainCircuit, Target
} from 'lucide-react';

const Landing: React.FC = () => {
    const navigate = useNavigate();
    const [isDark, setIsDark] = useState(true);
    const [scene, setScene] = useState(0);
    const [cursorPos, setCursorPos] = useState({ x: 300, y: 250 });
    const [cursorClick, setCursorClick] = useState(false);
    const [hoveredPage, setHoveredPage] = useState<string | null>(null);
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

    useEffect(() => {
        const saved = localStorage.getItem('theme');
        setIsDark(saved !== 'light');
        if (saved === 'light') {
            document.documentElement.classList.add('light-theme');
        }
    }, []);

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
            // Reset all states
            setScene(0);
            setTyping('');
            setResponseText('');
            setShowMCPPanel(false);
            setShowPermission(false);
            setShowRunningMCP(false);
            setUploadProgress(0);
            setAutomlProgress(0);
            setReportGenerating(false);
            setCursorPos({ x: 300, y: 250 });

            // Scene 0: Data Hub - File upload (0-4s)
            timers.push(setTimeout(() => setCursorPos({ x: 380, y: 180 }), 500));
            timers.push(setTimeout(() => {
                triggerClick();
                let progress = 0;
                const uploadInterval = setInterval(() => {
                    progress += 10;
                    setUploadProgress(progress);
                    if (progress >= 100) clearInterval(uploadInterval);
                }, 150);
            }, 1000));

            // Scene 1: Go to Dashboard (4-8s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 160 }), 4000)); // Dashboard position
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(1);
            }, 4500));

            // Scene 2: Go to AutoML (8-14s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 200 }), 8000)); // AutoML position
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
            }, 8500));

            // Scene 3: Go to Predictions (14-18s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 240 }), 14000)); // Predictions position
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(3);
                // Simulate filling form
            }, 14500));

            // Scene 4: Go to AI Analyst (18-22s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 320 }), 18000)); // Chat position
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(4);
            }, 18500));

            // Chat interactions (22-35s) - Simplified
            timers.push(setTimeout(() => {
                setCursorPos({ x: 400, y: 450 }); // Input box
            }, 20000));
            timers.push(setTimeout(() => {
                triggerClick();
                let i = 0;
                const typeInterval = setInterval(() => {
                    if (i <= question.length) {
                        setTyping(question.slice(0, i));
                        i++;
                    } else {
                        clearInterval(typeInterval);
                    }
                }, 50);
            }, 20500));
            // Send button
            timers.push(setTimeout(() => setCursorPos({ x: 560, y: 450 }), 23000));
            timers.push(setTimeout(() => {
                triggerClick();
                typeResponse();
            }, 23500));

            // Scene 5: Go to Reports (35-40s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 280 }), 35000)); // Reports position
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(5);
            }, 35500));

            // Generate report
            timers.push(setTimeout(() => setCursorPos({ x: 400, y: 285 }), 37500));
            timers.push(setTimeout(() => {
                triggerClick();
                setReportGenerating(true);
            }, 38000));
            timers.push(setTimeout(() => {
                setReportGenerating(false);
                setScene(6); // Show Result
            }, 40000));

            // Loop (45s)
            timers.push(setTimeout(() => runDemo(), 45000));
        };

        runDemo();
        return () => timers.forEach(t => clearTimeout(t));
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

    // Colors
    const accent = '#14b8a6';
    const bg = isDark ? '#0a0a0f' : '#fafafa';
    const text = isDark ? '#fafafa' : '#0f172a';
    const textMuted = isDark ? '#71717a' : '#64748b';
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
        if (hoveredPage) return hoveredPage;
        if (scene === 0) return 'data-hub';
        if (scene === 1) return 'dashboard';
        if (scene === 2) return 'automl';
        if (scene === 3) return 'ml-predictions';
        if (scene === 4) return 'chat';
        if (scene === 5 || scene === 6) return 'reports';
        return 'data-hub';
    };

    const activePage = getActivePage();

    return (
        <div className="min-h-screen" style={{ backgroundColor: bg, color: text }}>
            {/* Navigation */}
            <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-lg" style={{ backgroundColor: isDark ? 'rgba(10, 10, 15, 0.9)' : 'rgba(255, 255, 255, 0.95)', borderBottom: `1px solid ${border}` }}>
                <div className="max-w-6xl mx-auto px-6">
                    <div className="h-16 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <img src="/logo.png" alt="DataVision" className="w-8 h-8 object-contain" />
                            <span className="text-lg font-semibold">DataVision</span>
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

            {/* Hero Section - Premium Copy */}
            <section className="pt-28 pb-12 px-6">
                <div className="max-w-4xl mx-auto text-center">
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] mb-6"
                    >
                        Your data doesn't need dashboards.
                        <br />
                        <span style={{ color: accent }}>It needs intelligence.</span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-lg md:text-xl leading-relaxed mb-6 max-w-3xl mx-auto"
                        style={{ color: textMuted }}
                    >
                        A self-learning system that continuously understands any data, reasons autonomously
                        using multiple internal capabilities, and delivers actionable decisions — without manual configuration.
                    </motion.p>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="text-base leading-relaxed mb-10 max-w-2xl mx-auto"
                        style={{ color: textMuted }}
                    >
                        Upload any data. Ask any question. The system automatically interprets structure, context,
                        and relationships to produce reliable insights, explanations, and outcomes — in real time.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <button
                            onClick={() => navigate('/data-hub')}
                            className="flex items-center gap-2 text-sm font-semibold px-8 py-4 rounded-xl text-white mx-auto transition-all hover:scale-105"
                            style={{ backgroundColor: accent, boxShadow: `0 4px 20px ${accent}40` }}
                        >
                            Start with your data
                            <ArrowRight className="w-4 h-4" />
                        </button>
                    </motion.div>
                </div>
            </section>

            {/* Product Demo */}
            <section className="pb-20 px-6">
                <div className="max-w-5xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="rounded-2xl overflow-hidden shadow-2xl relative"
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
                                <span className="text-xs font-medium" style={{ color: demoMuted }}>DataVision - Enterprise Analytics</span>
                            </div>
                        </div>

                        {/* App Content */}
                        <div className="flex h-[520px] relative">
                            {/* Cursor */}
                            <motion.div
                                animate={{
                                    left: cursorPos.x,
                                    top: cursorPos.y,
                                    scale: cursorClick ? 0.8 : 1
                                }}
                                transition={{ type: 'spring', damping: 20, stiffness: 200 }}
                                className="absolute z-50 pointer-events-none"
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

                            {/* Sidebar */}
                            <div className="w-40 flex-shrink-0 border-r flex flex-col" style={{ backgroundColor: demoSidebar, borderColor: demoBorder }}>
                                <div className="p-3 border-b" style={{ borderColor: demoBorder }}>
                                    <div className="flex items-center gap-2">
                                        <img src="/logo.png" alt="" className="w-5 h-5" />
                                        <span className="text-sm font-semibold" style={{ color: demoText }}>DataVision</span>
                                    </div>
                                </div>

                                <div className="flex-1 py-2">
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
                                                key={item.label}
                                                onMouseEnter={() => setHoveredPage(item.path)}
                                                onMouseLeave={() => setHoveredPage(null)}
                                                className="flex items-center gap-2 px-3 py-2 mx-2 rounded-lg text-xs cursor-pointer transition-all"
                                                style={{
                                                    backgroundColor: isActive ? `${accent}15` : 'transparent',
                                                    color: isActive ? accent : demoMuted,
                                                    borderLeft: isActive ? `2px solid ${accent}` : '2px solid transparent'
                                                }}
                                            >
                                                <item.icon className="w-4 h-4" />
                                                {item.label}
                                            </div>
                                        );
                                    })}
                                </div>

                                <div className="p-3 border-t text-xs" style={{ borderColor: demoBorder, color: demoMuted }}>
                                    Sign Out
                                </div>
                            </div>

                            {/* Main Content */}
                            <div className="flex-1 overflow-hidden relative">
                                <AnimatePresence mode="wait">
                                    {/* Data Hub */}
                                    {activePage === 'data-hub' && (
                                        <motion.div key="datahub" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full p-5 overflow-auto">
                                            <div className="flex items-center justify-between mb-4">
                                                <div>
                                                    <h2 className="text-base font-semibold" style={{ color: demoText }}>Data Hub</h2>
                                                    <p className="text-xs" style={{ color: accent }}>Upload and manage your business data</p>
                                                </div>
                                            </div>
                                            <motion.div animate={{ borderColor: uploadProgress > 0 && uploadProgress < 100 ? accent : demoBorder }} className="border-2 border-dashed rounded-xl p-8 text-center mb-4">
                                                <Upload className="w-8 h-8 mx-auto mb-2" style={{ color: demoMuted }} />
                                                <p className="text-sm mb-1" style={{ color: demoText }}>Drag & drop files here</p>
                                                <p className="text-xs mb-3" style={{ color: demoMuted }}>or click to browse</p>
                                                <div className="flex justify-center gap-2 mb-3">
                                                    {['PDF', 'Excel', 'CSV', 'Images'].map((format, i) => (
                                                        <span key={format} className="text-[10px] px-2 py-1 rounded text-white" style={{ backgroundColor: ['#ef4444', '#22c55e', '#3b82f6', '#f59e0b'][i] }}>
                                                            {format}
                                                        </span>
                                                    ))}
                                                </div>
                                            </motion.div>
                                            <div className="flex items-center gap-2 px-3 py-2 rounded-lg mb-4" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                <Search className="w-4 h-4" style={{ color: demoMuted }} />
                                                <span className="text-xs" style={{ color: demoMuted }}>Search files...</span>
                                            </div>
                                            <div>
                                                <p className="text-xs font-medium mb-2" style={{ color: demoMuted }}>Uploaded Files (1)</p>
                                                <div className="flex items-center gap-3 p-3 rounded-xl" style={{ backgroundColor: demoCard }}>
                                                    <FileText className="w-5 h-5" style={{ color: demoMuted }} />
                                                    <div className="flex-1">
                                                        <p className="text-sm" style={{ color: demoText }}>test_data_sales_comprehensive.csv</p>
                                                        <p className="text-[10px]" style={{ color: demoMuted }}>10.9 KB · 12/26/2025</p>
                                                    </div>
                                                    <div className="flex items-center gap-1 text-xs" style={{ color: accent }}>
                                                        <Check className="w-3 h-3" />
                                                        {uploadProgress >= 100 ? 'Indexed' : `${uploadProgress}%`}
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* Dashboard (Autonomous) */}
                                    {activePage === 'dashboard' && (
                                        <motion.div key="dashboard" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full p-4 overflow-auto">
                                            <div className="flex items-center justify-between mb-4">
                                                <div>
                                                    <h2 className="text-base font-semibold" style={{ color: demoText }}>Autonomous Dashboard</h2>
                                                    <p className="text-xs" style={{ color: accent }}>AI-generated insights from your data</p>
                                                </div>
                                                <button className="text-[10px] px-3 py-1.5 rounded-lg text-white" style={{ backgroundColor: accent }}>Regenerate</button>
                                            </div>

                                            {/* KPIs */}
                                            <div className="grid grid-cols-4 gap-2 mb-4">
                                                {[
                                                    { label: 'Revenues', value: '₹1.4M', color: '#10b981' },
                                                    { label: 'Customers', value: '1,240', color: '#3b82f6' },
                                                    { label: 'Orders', value: '3,850', color: '#f59e0b' },
                                                    { label: 'Growth', value: '+14%', color: '#8b5cf6' },
                                                ].map((kpi, i) => (
                                                    <div key={i} className="p-3 rounded-xl" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                        <p className="text-lg font-bold" style={{ color: demoText }}>{kpi.value}</p>
                                                        <p className="text-[9px]" style={{ color: demoMuted }}>{kpi.label}</p>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Charts */}
                                            <div className="grid grid-cols-2 gap-3 h-48">
                                                <div className="p-3 rounded-xl flex flex-col" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] font-medium mb-auto" style={{ color: demoText }}>Revenue Trend</p>
                                                    <div className="h-32 flex items-end gap-1">
                                                        {[30, 45, 35, 60, 50, 70, 65, 80, 75, 90].map((h, i) => (
                                                            <div key={i} className="flex-1 rounded-t" style={{ height: `${h}%`, backgroundColor: accent, opacity: 0.6 + (i * 0.04) }} />
                                                        ))}
                                                    </div>
                                                </div>
                                                <div className="p-3 rounded-xl flex flex-col" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] font-medium mb-auto" style={{ color: demoText }}>Sales by Region</p>
                                                    <div className="flex-1 flex items-center justify-center relative">
                                                        <div className="w-24 h-24 rounded-full border-8" style={{ borderColor: '#3b82f6' }} />
                                                        <div className="absolute w-24 h-24 rounded-full border-8 border-transparent" style={{ borderColor: '#10b981', transform: 'rotate(45deg)', clipPath: 'polygon(50% 50%, 100% 0, 100% 100%, 0 100%, 0 0)' }} />
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* AutoML */}
                                    {activePage === 'automl' && (
                                        <motion.div key="automl" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full p-4 overflow-auto">
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
                                        <motion.div key="predictions" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full p-4 overflow-auto">
                                            <h2 className="text-base font-semibold mb-1" style={{ color: demoText }}>Make Prediction</h2>
                                            <p className="text-xs mb-4" style={{ color: accent }}>Active Model: XGBoost Classifier</p>

                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-3">
                                                    {[
                                                        { label: 'Customer Age', val: '32' },
                                                        { label: 'Purchase Amount', val: '12500' },
                                                        { label: 'Tenure (Months)', val: '14' },
                                                        { label: 'Support Calls', val: '2' },
                                                    ].map((field, i) => (
                                                        <div key={i}>
                                                            <label className="text-[9px] block mb-1" style={{ color: demoMuted }}>{field.label}</label>
                                                            <div className="w-full p-1.5 rounded border text-[10px]" style={{ borderColor: demoBorder, backgroundColor: demoBg, color: demoText }}>
                                                                {field.val}
                                                            </div>
                                                        </div>
                                                    ))}
                                                    <button className="w-full py-2 mt-2 rounded-lg text-xs text-white" style={{ backgroundColor: accent }}>Predict Churn</button>
                                                </div>

                                                <div className="flex flex-col items-center justify-center p-4 rounded-xl text-center" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] mb-2" style={{ color: demoMuted }}>Prediction Result</p>
                                                    <div className="text-2xl font-bold mb-1" style={{ color: '#10b981' }}>Low Risk</div>
                                                    <div className="text-[10px] mb-1" style={{ color: demoText }}>Probability: 12%</div>
                                                    <div className="w-full bg-gray-700 h-1 rounded-full mt-2">
                                                        <div className="h-full w-[12%] bg-green-500 rounded-full" />
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* Chat */}
                                    {activePage === 'chat' && (
                                        <motion.div key="chat" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full flex flex-col">
                                            <div className="px-5 py-3 border-b" style={{ borderColor: demoBorder }}>
                                                <p className="text-sm font-semibold" style={{ color: demoText }}>Analyst Chat</p>
                                                <p className="text-[10px]" style={{ color: demoMuted }}>RAG Mode • 10 Active Tools</p>
                                            </div>

                                            <div className="flex-1 p-5 overflow-auto relative">
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
                                                        <img src="/logo.png" alt="" className="w-4 h-4" />
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
                                                                <img src="/logo.png" alt="" className="w-4 h-4" />
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
                                                            <img src="/logo.png" alt="" className="w-4 h-4" />
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
                                        <motion.div key="reports" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full p-5 overflow-auto">
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
                                                    {['Metrics Analysis', 'Data Breakdown', 'Data Summary', 'Executive Summary'].map((report, i) => (
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
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Why Different Section - Premium Copy */}
            <section className="py-20 px-6" style={{ backgroundColor: isDark ? 'rgba(20, 184, 166, 0.03)' : 'rgba(20, 184, 166, 0.05)' }}>
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">
                        Why This Is <span style={{ color: accent }}>Different</span>
                    </h2>

                    <p className="text-center mb-6 max-w-3xl mx-auto leading-relaxed" style={{ color: textMuted }}>
                        DataVision is built as a continuously learning intelligence system — not a reporting layer.
                    </p>

                    <p className="text-center mb-12 max-w-3xl mx-auto leading-relaxed" style={{ color: textMuted }}>
                        It understands data of any kind, adapts as information changes, and produces reliable intelligence
                        without manual setup, configuration, or predefined logic. The system operates autonomously in the background,
                        maintaining context, updating understanding, and delivering decision-ready outputs whenever they are needed.
                    </p>

                    <h3 className="text-xl font-semibold text-center mb-8" style={{ color: text }}>
                        What the Platform Delivers
                    </h3>

                    <div className="space-y-4 max-w-2xl mx-auto">
                        {[
                            'Continuous understanding of structured and unstructured data',
                            'Autonomous reasoning across evolving datasets',
                            'Zero-configuration ingestion and interpretation',
                            'Always-up-to-date intelligence, not point-in-time results',
                            'Clear, explainable outputs designed for real decisions',
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
            </section>

            {/* Final Statement */}
            <section className="py-24 px-6">
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
            </section>

            {/* Footer */}
            <footer className="py-8 px-6 border-t" style={{ borderColor: border }}>
                <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <img src="/logo.png" alt="DataVision" className="w-6 h-6 object-contain" />
                        <span className="text-sm font-medium">DataVision</span>
                    </div>
                    <p className="text-xs text-center" style={{ color: textMuted }}>
                        © 2025 DataVision. The future of autonomous data intelligence.
                    </p>
                </div>
            </footer>
        </div>
    );
};

export default Landing;
