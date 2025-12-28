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
    PieChart, Activity, Users, Loader2
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

    const question = 'Check my data quality...';
    const fullResponse = `I've checked your data quality, and it appears to be in good condition. The data is comprehensive, with 100 records across various categories.

**Data Quality Summary:**
• 20 unique customers
• 100 unique products  
• Total revenue: ₹13,85,149
• Average order value: ₹13,851.49
• Top customer: TechGiant (16% of revenue)

**Data Quality Score: 100/100** - No issues found

The data provides valuable insights into customer spending habits, product sales, and revenue trends.`;

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
            setReportGenerating(false);
            setCursorPos({ x: 300, y: 250 });

            // Scene 0: Data Hub - File upload (0-5s)
            timers.push(setTimeout(() => setCursorPos({ x: 380, y: 180 }), 1000));
            timers.push(setTimeout(() => {
                triggerClick();
                let progress = 0;
                const uploadInterval = setInterval(() => {
                    progress += 10;
                    setUploadProgress(progress);
                    if (progress >= 100) clearInterval(uploadInterval);
                }, 200);
            }, 1500));

            // Scene 1: Go to Overview (5-8s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 135 }), 5000));
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(1);
            }, 5500));

            // Scene 2: Go to Dashboards (8-12s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 188 }), 8500));
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(2);
            }, 9000));

            // Scene 3: Go to AI Analyst (12-15s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 268 }), 12000));
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(3);
            }, 12500));

            // Show MCP panel (15-18s)
            timers.push(setTimeout(() => {
                setCursorPos({ x: 180, y: 380 });
                triggerClick();
                setShowMCPPanel(true);
            }, 15000));

            // Close MCP, type query (18-24s)
            timers.push(setTimeout(() => {
                setShowMCPPanel(false);
                setCursorPos({ x: 400, y: 420 });
            }, 18000));

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
                }, 80);
            }, 18500));

            // Send, show permission (24-28s)
            timers.push(setTimeout(() => setCursorPos({ x: 560, y: 420 }), 23000));
            timers.push(setTimeout(() => {
                triggerClick();
                setShowPermission(true);
            }, 23500));

            // Click Allow, show Running MCP (26-28s)
            timers.push(setTimeout(() => setCursorPos({ x: 540, y: 320 }), 26000));
            timers.push(setTimeout(() => {
                triggerClick();
                setShowPermission(false);
                setShowRunningMCP(true);
                setScene(4);
            }, 26500));

            // Hide Running MCP, show response (30-38s)
            timers.push(setTimeout(() => {
                setShowRunningMCP(false);
                typeResponse();
            }, 30000));

            // Scene 5: Go to Reports (40-44s)
            timers.push(setTimeout(() => setCursorPos({ x: 80, y: 215 }), 40000));
            timers.push(setTimeout(() => {
                triggerClick();
                setScene(5);
            }, 40500));

            // Click Generate Report (44-48s)
            timers.push(setTimeout(() => setCursorPos({ x: 400, y: 285 }), 44000));
            timers.push(setTimeout(() => {
                triggerClick();
                setReportGenerating(true);
            }, 44500));

            // Show generated report (48s)
            timers.push(setTimeout(() => {
                setReportGenerating(false);
                setScene(6);
            }, 48000));

            // Loop (54s)
            timers.push(setTimeout(() => runDemo(), 54000));
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
        if (scene === 1) return 'overview';
        if (scene === 2) return 'dashboards';
        if (scene === 3 || scene === 4) return 'chat';
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
                                        { icon: BarChart2, label: 'Overview', path: 'overview' },
                                        { icon: Database, label: 'Data Hub', path: 'data-hub' },
                                        { icon: PieChart, label: 'Dashboards', path: 'dashboards' },
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

                                    {/* Overview - Exact Screenshot Match */}
                                    {activePage === 'overview' && (
                                        <motion.div key="overview" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full p-4 overflow-auto">
                                            <h2 className="text-base font-semibold mb-3" style={{ color: demoText }}>Overview</h2>

                                            {/* KPI Row */}
                                            <div className="grid grid-cols-4 gap-2 mb-3">
                                                {[
                                                    { label: 'TOTAL RECORDS', value: '100', change: '+18.5%', color: '#8B5CF6' },
                                                    { label: 'UNIQUE CUSTOMER SEGMENTS', value: '3', change: '+10.9%', color: '#F59E0B' },
                                                    { label: 'UNIQUE PRODUCT CATEGORIES', value: '3', change: '+18.1%', color: '#3B82F6' },
                                                    { label: 'UNIQUE SALES CHANNELS', value: '4', change: '+8.0%', color: '#22C55E' },
                                                ].map((kpi, i) => (
                                                    <div key={i} className="p-2 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                        <p className="text-[8px] font-medium mb-0.5" style={{ color: demoMuted }}>{kpi.label}</p>
                                                        <p className="text-xl font-bold" style={{ color: demoText }}>{kpi.value}</p>
                                                        <p className="text-[9px]" style={{ color: kpi.color }}>{kpi.change} vs last period</p>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Charts Row */}
                                            <div className="grid grid-cols-2 gap-2 mb-3">
                                                {/* Total Amount Trend */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <div className="flex justify-between items-center mb-2">
                                                        <p className="text-xs font-medium" style={{ color: demoText }}>Total Amount Trend</p>
                                                        <span className="text-[9px]" style={{ color: '#22C55E' }}>↗ +58.7%</span>
                                                    </div>
                                                    <div className="h-14 flex items-end">
                                                        <svg viewBox="0 0 200 50" className="w-full h-full">
                                                            <path d="M0 45 L30 40 L60 42 L90 35 L120 30 L150 20 L180 15 L200 10" fill="none" stroke="#EF4444" strokeWidth="2" />
                                                        </svg>
                                                    </div>
                                                </div>

                                                {/* Customer Segment Funnel */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-xs font-medium mb-2" style={{ color: demoText }}>Customer Segment Funnel</p>
                                                    <div className="space-y-1">
                                                        {[
                                                            { label: 'Enterprise', value: '1.3M', width: '100%', color: '#22C55E' },
                                                            { label: 'SMB', value: '62K', width: '45%', color: '#F59E0B' },
                                                            { label: 'Small Business', value: '40K', width: '35%', color: '#3B82F6' },
                                                        ].map((item, i) => (
                                                            <div key={i} className="flex items-center gap-2">
                                                                <span className="text-[8px] w-16" style={{ color: demoMuted }}>{item.label}</span>
                                                                <div className="flex-1 h-3 rounded" style={{ backgroundColor: item.color, width: item.width }} />
                                                                <span className="text-[8px] w-8 text-right" style={{ color: demoText }}>{item.value}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Bottom Row */}
                                            <div className="grid grid-cols-3 gap-2 mb-3">
                                                {/* Key Metrics */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-xs font-medium mb-2" style={{ color: demoText }}>Key Metrics</p>
                                                    <div className="grid grid-cols-2 gap-1.5">
                                                        {[
                                                            { label: 'Total Amount', value: '1.4M', color: accent },
                                                            { label: 'Unit Price', value: '156K', color: accent },
                                                            { label: 'Shipping Cost', value: '6K', color: accent },
                                                            { label: 'Quantity', value: '2K', color: accent },
                                                        ].map((m, i) => (
                                                            <div key={i} className="text-center p-1.5 rounded" style={{ backgroundColor: demoBg }}>
                                                                <p className="text-sm font-bold" style={{ color: m.color }}>{m.value}</p>
                                                                <p className="text-[7px]" style={{ color: demoMuted }}>{m.label}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Data Quality */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-xs font-medium mb-2" style={{ color: demoText }}>Data Quality</p>
                                                    {['Customer Name', 'Customer Segment', 'Product Category', 'Region'].map((field, i) => (
                                                        <div key={i} className="flex items-center justify-between py-0.5">
                                                            <div className="flex items-center gap-1">
                                                                <Check className="w-2.5 h-2.5" style={{ color: accent }} />
                                                                <span className="text-[8px]" style={{ color: demoMuted }}>{field}</span>
                                                            </div>
                                                            <span className="text-[8px]" style={{ color: accent }}>100%</span>
                                                        </div>
                                                    ))}
                                                </div>

                                                {/* Avg Total Amount */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-xs font-medium mb-2" style={{ color: demoText }}>Avg Total Amount</p>
                                                    <div className="flex items-center justify-center">
                                                        <div className="relative w-14 h-14">
                                                            <svg className="w-full h-full transform -rotate-90">
                                                                <circle cx="28" cy="28" r="24" fill="none" stroke={demoBorder} strokeWidth="5" />
                                                                <circle cx="28" cy="28" r="24" fill="none" stroke={accent} strokeWidth="5" strokeDasharray="150" strokeDashoffset="30" />
                                                            </svg>
                                                            <div className="absolute inset-0 flex items-center justify-center">
                                                                <span className="text-xs font-bold" style={{ color: demoText }}>14K</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Data Summary & AI Insight */}
                                            <div className="grid grid-cols-2 gap-2">
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-xs font-medium mb-2" style={{ color: demoText }}>Data Summary</p>
                                                    <div className="grid grid-cols-2 gap-2">
                                                        {[
                                                            { label: 'RECORDS', value: '100', icon: FileText },
                                                            { label: 'COLUMNS', value: '13', icon: BarChart2 },
                                                            { label: 'METRICS', value: '7', icon: Activity },
                                                            { label: 'DIMENSIONS', value: '3', icon: PieChart },
                                                        ].map((s, i) => (
                                                            <div key={i} className="text-center">
                                                                <p className="text-lg font-bold" style={{ color: demoText }}>{s.value}</p>
                                                                <p className="text-[7px]" style={{ color: demoMuted }}>{s.label}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <div className="flex items-center gap-1 mb-2">
                                                        <Zap className="w-3 h-3" style={{ color: '#F59E0B' }} />
                                                        <p className="text-xs font-medium" style={{ color: demoText }}>AI Insight</p>
                                                    </div>
                                                    <p className="text-[9px] mb-2" style={{ color: demoMuted }}>
                                                        Showing 100 records, 3 unique Customer Segments, Total Amount totals 1.4M.
                                                    </p>
                                                    <button className="w-full py-1.5 rounded-lg text-[10px] font-medium text-white" style={{ backgroundColor: accent }}>
                                                        View Full Dashboard →
                                                    </button>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* Dashboards - Exact Screenshot Match */}
                                    {activePage === 'dashboards' && (
                                        <motion.div key="dashboards" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full p-4 overflow-auto">
                                            {/* Header */}
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="flex items-center gap-2">
                                                    <Activity className="w-4 h-4" style={{ color: accent }} />
                                                    <span className="text-sm font-semibold" style={{ color: demoText }}>Analytics Dashboard</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px]" style={{ color: demoMuted }}>100 Records | All Data</span>
                                                    <button className="px-2 py-1 rounded text-[9px]" style={{ backgroundColor: accent, color: 'white' }}>Overview</button>
                                                </div>
                                            </div>

                                            {/* Filters */}
                                            <div className="flex gap-2 mb-3">
                                                {['CUSTOMER SEGMENT', 'PRODUCT CATEGORY', 'SALES CHANNEL'].map(f => (
                                                    <div key={f} className="flex items-center gap-1 px-2 py-1 rounded text-[9px]" style={{ backgroundColor: demoCard, color: demoMuted, border: `1px solid ${demoBorder}` }}>
                                                        {f} All <ChevronDown className="w-3 h-3" />
                                                    </div>
                                                ))}
                                                <div className="px-2 py-1 rounded text-[9px] text-white flex items-center gap-1" style={{ backgroundColor: accent }}>
                                                    <Check className="w-3 h-3" /> Apply Filters
                                                </div>
                                            </div>

                                            {/* KPIs */}
                                            <div className="grid grid-cols-4 gap-2 mb-3">
                                                {[
                                                    { label: 'TOTAL RECORDS', value: '100', icon: '📊' },
                                                    { label: 'UNIQUE CUSTOMER SEGMENTS', value: '3', icon: '👥' },
                                                    { label: 'UNIQUE PRODUCT CATEGORIES', value: '3', icon: '📦' },
                                                    { label: 'UNIQUE SALES CHANNELS', value: '4', icon: '🏪' },
                                                ].map((kpi, i) => (
                                                    <div key={i} className="p-2 rounded-lg flex items-center gap-2" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                        <div>
                                                            <p className="text-[8px]" style={{ color: demoMuted }}>{kpi.label}</p>
                                                            <p className="text-lg font-bold" style={{ color: demoText }}>{kpi.value}</p>
                                                            <p className="text-[8px]" style={{ color: '#22C55E' }}>vs last period</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Charts Row 1 */}
                                            <div className="grid grid-cols-3 gap-2 mb-3">
                                                {/* Scatter */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] font-medium mb-2" style={{ color: demoText }}>Total Amount vs Unit Price</p>
                                                    <div className="h-16 relative">
                                                        {[...Array(12)].map((_, i) => (
                                                            <div key={i} className="absolute w-2 h-2 rounded-full" style={{
                                                                backgroundColor: accent,
                                                                left: `${10 + Math.random() * 80}%`,
                                                                top: `${10 + Math.random() * 80}%`
                                                            }} />
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Bar Trend */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] font-medium mb-2" style={{ color: demoText }}>Total Amount Trend</p>
                                                    <div className="h-16 flex items-end gap-1">
                                                        {[40, 25, 55, 45, 65, 30, 50].map((h, i) => (
                                                            <div key={i} className="flex-1 rounded-t" style={{ height: `${h}%`, backgroundColor: ['#22C55E', '#F59E0B'][i % 2] }} />
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Category Flow */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] font-medium mb-2" style={{ color: demoText }}>Customer Segment → Product Category Flow</p>
                                                    <div className="space-y-0.5">
                                                        {['Electronics', 'First Order', 'Office Supplies'].map((cat, i) => (
                                                            <div key={cat} className="h-3 rounded" style={{ backgroundColor: ['#EF4444', '#22C55E', '#3B82F6'][i], width: `${100 - i * 20}%` }} />
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Charts Row 2 */}
                                            <div className="grid grid-cols-3 gap-2">
                                                {/* Correlations */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] font-medium mb-2" style={{ color: demoText }}>Metric Correlations</p>
                                                    <div className="grid grid-cols-4 gap-0.5">
                                                        {['1.0', '0.9', '0.2', '0.4', '0.9', '1.0', '0.1', '0.3', '0.6', '0.4', '1.0', '0.8', '0.3', '0.5', '0.8', '1.0'].map((v, i) => (
                                                            <div key={i} className="w-5 h-5 rounded text-[6px] flex items-center justify-center" style={{ backgroundColor: parseFloat(v) > 0.5 ? '#22C55E' : '#3B82F6', color: 'white' }}>
                                                                {v}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Data Summary */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] font-medium mb-2" style={{ color: demoText }}>Data Summary</p>
                                                    <div className="grid grid-cols-2 gap-2">
                                                        {[
                                                            { value: '100', label: 'Records' },
                                                            { value: '13', label: 'Columns' },
                                                            { value: '7', label: 'Metrics' },
                                                            { value: '3', label: 'Dimensions' },
                                                        ].map((s, i) => (
                                                            <div key={i} className="text-center">
                                                                <p className="text-sm font-bold" style={{ color: demoText }}>{s.value}</p>
                                                                <p className="text-[7px]" style={{ color: demoMuted }}>{s.label}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Product Category */}
                                                <div className="p-3 rounded-lg" style={{ backgroundColor: demoCard, border: `1px solid ${demoBorder}` }}>
                                                    <p className="text-[10px] font-medium mb-2" style={{ color: demoText }}>Total Amount by Product Category</p>
                                                    <div className="h-12 flex items-end gap-2">
                                                        {[85, 40, 65].map((h, i) => (
                                                            <div key={i} className="flex-1 rounded-t" style={{ height: `${h}%`, backgroundColor: ['#8B5CF6', '#F59E0B', '#3B82F6'][i] }} />
                                                        ))}
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
