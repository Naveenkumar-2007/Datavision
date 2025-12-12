import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    ArrowRight,
    Database,
    Brain,
    BarChart3,
    FileText,
    Sparkles,
    TrendingUp,
    Upload,
    MessageSquare,
    PieChart,
    FileSpreadsheet,
    Image,
    CheckCircle2,
    Users,
    LineChart,
    Target,
    Play,
} from 'lucide-react';

const Landing: React.FC = () => {
    const navigate = useNavigate();

    const coreFeatures = [
        {
            icon: Brain,
            title: 'Multi-Mode Intelligence',
            description: 'RAG, GraphRAG & Hybrid modes analyze your documents and return deep insights',
        },
        {
            icon: Sparkles,
            title: 'Automated Insights',
            description: 'Instantly detect trends, anomalies, and business opportunities from your data',
        },
        {
            icon: Database,
            title: 'Cross-Dataset Analysis',
            description: 'Merge Excel, CSV, PDFs & images to find patterns across all your data',
        },
        {
            icon: Target,
            title: 'Decision Simulations',
            description: 'Test business strategies and scenarios with AI-powered predictions',
        },
    ];

    const capabilities = [
        { icon: BarChart3, text: 'Auto-generated revenue reports' },
        { icon: Users, text: 'Customer segmentation analysis' },
        { icon: TrendingUp, text: 'Product performance scoring' },
        { icon: FileText, text: 'Monthly business summaries' },
        { icon: MessageSquare, text: 'Natural language data queries' },
        { icon: LineChart, text: 'Trend forecasting & predictions' },
        { icon: PieChart, text: 'Interactive chart generation' },
        { icon: FileSpreadsheet, text: 'PDF & Excel report export' },
    ];

    const howItWorks = [
        {
            step: '01',
            title: 'Upload Your Data',
            description: 'Excel, CSV, PDF, or images - simply drag and drop',
            icon: Upload,
        },
        {
            step: '02',
            title: 'Ask Questions',
            description: 'Chat naturally about your business data',
            icon: MessageSquare,
        },
        {
            step: '03',
            title: 'Get Insights',
            description: 'Receive charts, analysis, and recommendations',
            icon: Sparkles,
        },
        {
            step: '04',
            title: 'Take Action',
            description: 'Make data-driven decisions confidently',
            icon: Target,
        },
    ];

    const stats = [
        { value: '3', label: 'AI Modes', desc: 'RAG, GraphRAG & Hybrid' },
        { value: '20+', label: 'File Types', desc: 'Excel, CSV, PDF, Images' },
        { value: '<2s', label: 'Response Time', desc: 'Instant insights' },
        { value: '∞', label: 'Queries', desc: 'Unlimited analysis' },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-b from-amber-50 via-orange-50/50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 overflow-x-hidden transition-colors duration-300">
            {/* Navigation */}
            <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 dark:bg-gray-950/90 backdrop-blur-lg border-b border-orange-100/50 dark:border-gray-800">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <img src="/logo.png" alt="AI Business Analyst" className="w-10 h-10 rounded-xl shadow-md" />
                        <span className="text-xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
                            AI Business Analyst
                        </span>
                    </div>
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => navigate('/overview')}
                            className="text-gray-600 dark:text-gray-300 hover:text-orange-600 dark:hover:text-orange-400 font-medium transition-colors hidden sm:block"
                        >
                            Dashboard
                        </button>
                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => navigate('/login')}
                            className="px-6 py-2.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-full font-semibold shadow-lg hover:shadow-orange-200 dark:hover:shadow-orange-900/30 transition-all"
                        >
                            Get Started
                        </motion.button>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-28 pb-16 px-6 relative overflow-hidden">
                {/* Background decoration */}
                <div className="absolute top-20 right-0 w-96 h-96 bg-orange-200/30 dark:bg-orange-500/10 rounded-full blur-3xl -z-10" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-amber-200/30 dark:bg-amber-500/10 rounded-full blur-3xl -z-10" />

                <div className="max-w-7xl mx-auto">
                    <div className="grid lg:grid-cols-2 gap-12 items-center">
                        {/* Left Content */}
                        <motion.div
                            initial={{ opacity: 0, x: -30 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6 }}
                        >
                            <div className="inline-flex items-center space-x-2 bg-orange-100 dark:bg-orange-500/10 text-orange-700 dark:text-orange-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
                                <Sparkles className="w-4 h-4" />
                                <span>AI-Powered Business Intelligence</span>
                            </div>

                            <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 dark:text-white leading-tight mb-6">
                                See Your Business
                                <br />
                                <span className="bg-gradient-to-r from-orange-500 to-amber-500 bg-clip-text text-transparent">
                                    Through AI
                                </span>
                            </h1>

                            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 leading-relaxed">
                                AI that understands your data like a human — but faster.
                                Upload your files and get instant insights, charts & recommendations.
                            </p>

                            <div className="flex flex-wrap gap-4 mb-8">
                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => navigate('/login')}
                                    className="px-8 py-4 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-xl font-semibold flex items-center space-x-2 shadow-xl hover:shadow-orange-300/50 dark:hover:shadow-orange-900/30 transition-all"
                                >
                                    <span>Start Analyzing</span>
                                    <ArrowRight className="w-5 h-5" />
                                </motion.button>

                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => navigate('/overview')}
                                    className="px-8 py-4 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 rounded-xl font-semibold flex items-center space-x-2 hover:border-orange-300 dark:hover:border-orange-500 hover:bg-orange-50 dark:hover:bg-gray-700 transition-all"
                                >
                                    <Play className="w-5 h-5" />
                                    <span>View Demo</span>
                                </motion.button>
                            </div>

                            {/* Supported Formats */}
                            <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                                <span className="font-medium">Supports:</span>
                                <div className="flex items-center space-x-4">
                                    <div className="flex items-center space-x-1.5 bg-emerald-50 dark:bg-emerald-500/10 px-3 py-1.5 rounded-full">
                                        <FileSpreadsheet className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                                        <span className="text-emerald-700 dark:text-emerald-400 font-medium">Excel</span>
                                    </div>
                                    <div className="flex items-center space-x-1.5 bg-blue-50 dark:bg-blue-500/10 px-3 py-1.5 rounded-full">
                                        <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                        <span className="text-blue-700 dark:text-blue-400 font-medium">CSV</span>
                                    </div>
                                    <div className="flex items-center space-x-1.5 bg-red-50 dark:bg-red-500/10 px-3 py-1.5 rounded-full">
                                        <FileText className="w-4 h-4 text-red-600 dark:text-red-400" />
                                        <span className="text-red-700 dark:text-red-400 font-medium">PDF</span>
                                    </div>
                                    <div className="flex items-center space-x-1.5 bg-orange-50 dark:bg-orange-500/10 px-3 py-1.5 rounded-full">
                                        <Image className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                                        <span className="text-orange-700 dark:text-orange-400 font-medium">Images</span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Right - Product Screenshot */}
                        <motion.div
                            initial={{ opacity: 0, x: 30 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6, delay: 0.2 }}
                            className="relative"
                        >
                            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-700 p-4 overflow-hidden">
                                <div className="bg-gradient-to-br from-gray-50 to-orange-50/50 dark:from-gray-900 dark:to-gray-800 rounded-xl p-6">
                                    <div className="flex items-center space-x-2 mb-6">
                                        <div className="w-3 h-3 rounded-full bg-red-400" />
                                        <div className="w-3 h-3 rounded-full bg-yellow-400" />
                                        <div className="w-3 h-3 rounded-full bg-green-400" />
                                        <span className="text-xs text-gray-400 ml-4">AI Business Analyst</span>
                                    </div>

                                    {/* Mini Dashboard Preview */}
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-3 gap-3">
                                            <div className="bg-white dark:bg-gray-900 rounded-lg p-3 shadow-sm border border-gray-100 dark:border-gray-700">
                                                <div className="text-xs text-gray-500 dark:text-gray-400">Revenue</div>
                                                <div className="text-lg font-bold text-gray-800 dark:text-white">₹12.4L</div>
                                                <div className="text-xs text-emerald-500 flex items-center">
                                                    <TrendingUp className="w-3 h-3 mr-1" />
                                                    +12.5%
                                                </div>
                                            </div>
                                            <div className="bg-white dark:bg-gray-900 rounded-lg p-3 shadow-sm border border-gray-100 dark:border-gray-700">
                                                <div className="text-xs text-gray-500 dark:text-gray-400">Customers</div>
                                                <div className="text-lg font-bold text-gray-800 dark:text-white">2,847</div>
                                                <div className="text-xs text-emerald-500 flex items-center">
                                                    <TrendingUp className="w-3 h-3 mr-1" />
                                                    +8.3%
                                                </div>
                                            </div>
                                            <div className="bg-white dark:bg-gray-900 rounded-lg p-3 shadow-sm border border-gray-100 dark:border-gray-700">
                                                <div className="text-xs text-gray-500 dark:text-gray-400">Growth</div>
                                                <div className="text-lg font-bold text-gray-800 dark:text-white">23%</div>
                                                <div className="text-xs text-orange-500">On Track</div>
                                            </div>
                                        </div>

                                        {/* Chart Preview */}
                                        <div className="bg-white dark:bg-gray-900 rounded-lg p-4 shadow-sm border border-gray-100 dark:border-gray-700">
                                            <div className="flex items-center justify-between mb-3">
                                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Monthly Trends</span>
                                                <Sparkles className="w-4 h-4 text-orange-400" />
                                            </div>
                                            <div className="flex items-end space-x-2 h-24">
                                                {[40, 65, 45, 80, 55, 75, 90].map((h, i) => (
                                                    <motion.div
                                                        key={i}
                                                        initial={{ height: 0 }}
                                                        animate={{ height: `${h}%` }}
                                                        transition={{ delay: 0.5 + i * 0.1, duration: 0.5 }}
                                                        className="flex-1 bg-gradient-to-t from-orange-500 to-amber-400 rounded-t"
                                                    />
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Core Features Section */}
            <section className="py-20 px-6 bg-white dark:bg-gray-950">
                <div className="max-w-7xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                            Powerful Intelligence at Your Fingertips
                        </h2>
                        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
                            Transform raw data into actionable business insights
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {coreFeatures.map((feature, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="bg-gradient-to-br from-gray-50 to-orange-50/50 dark:from-gray-900 dark:to-gray-800/50 rounded-2xl p-6 border border-orange-100/50 dark:border-gray-800 hover:shadow-lg hover:border-orange-200 dark:hover:border-orange-700/50 transition-all group"
                            >
                                <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-amber-500 rounded-xl flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform">
                                    <feature.icon className="w-6 h-6 text-white" />
                                </div>
                                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{feature.title}</h3>
                                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{feature.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section className="py-20 px-6 bg-gradient-to-b from-white to-orange-50/50 dark:from-gray-950 dark:to-gray-900">
                <div className="max-w-7xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">How It Works</h2>
                        <p className="text-xl text-gray-600 dark:text-gray-300">Simple steps to business intelligence</p>
                    </motion.div>

                    <div className="grid lg:grid-cols-2 gap-12 items-start">
                        {/* Capabilities List */}
                        <div className="bg-white dark:bg-gray-900 rounded-2xl p-8 shadow-lg border border-gray-100 dark:border-gray-800">
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">What You Can Do</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {capabilities.map((cap, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, x: -20 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: i * 0.05 }}
                                        className="flex items-center space-x-3 text-gray-700 dark:text-gray-300"
                                    >
                                        <CheckCircle2 className="w-5 h-5 text-orange-500 flex-shrink-0" />
                                        <span className="text-sm">{cap.text}</span>
                                    </motion.div>
                                ))}
                            </div>
                        </div>

                        {/* Steps */}
                        <div className="grid grid-cols-2 gap-4">
                            {howItWorks.map((item, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.1 }}
                                    className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-100 dark:border-gray-800 shadow-sm hover:shadow-md hover:border-orange-200 dark:hover:border-orange-700/50 transition-all"
                                >
                                    <div className="text-3xl font-bold bg-gradient-to-r from-orange-500 to-amber-500 bg-clip-text text-transparent mb-3">
                                        {item.step}
                                    </div>
                                    <h4 className="font-bold text-gray-900 dark:text-white mb-2">{item.title}</h4>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">{item.description}</p>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="py-16 px-6 bg-white dark:bg-gray-950">
                <div className="max-w-7xl mx-auto">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        {stats.map((stat, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="text-center p-6 bg-gradient-to-br from-gray-50 to-orange-50/30 dark:from-gray-900 dark:to-gray-800 border border-gray-100 dark:border-gray-800 rounded-2xl"
                            >
                                <div className="text-4xl font-bold bg-gradient-to-r from-orange-500 to-amber-500 bg-clip-text text-transparent mb-2">
                                    {stat.value}
                                </div>
                                <div className="font-semibold text-gray-900 dark:text-white mb-1">{stat.label}</div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">{stat.desc}</div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 px-6 dark:bg-gray-950">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="max-w-4xl mx-auto"
                >
                    <div className="bg-gradient-to-r from-orange-500 to-amber-500 rounded-3xl p-12 text-center relative overflow-hidden">
                        {/* Background decoration */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
                        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full blur-3xl" />

                        <div className="relative z-10">
                            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">
                                Ready to Transform Your Data?
                            </h2>
                            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
                                Join businesses making smarter, data-driven decisions with AI
                            </p>
                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => navigate('/login')}
                                className="px-10 py-4 bg-white text-orange-600 rounded-xl font-bold text-lg flex items-center space-x-2 mx-auto shadow-2xl hover:shadow-white/20 transition-all"
                            >
                                <span>Start Now</span>
                                <ArrowRight className="w-5 h-5" />
                            </motion.button>
                        </div>
                    </div>
                </motion.div>
            </section>

            {/* Footer */}
            <footer className="bg-gray-50 dark:bg-[#0B0F19] text-gray-600 dark:text-gray-400 pt-20 pb-10 border-t border-gray-200 dark:border-white/5 transition-colors duration-300">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="grid md:grid-cols-4 gap-12 mb-16">
                        {/* Brand Section */}
                        <div className="md:col-span-2 space-y-6">
                            <div className="flex items-center space-x-3">
                                <img src="/logo.png" alt="AI Business Analyst" className="w-12 h-12 rounded-xl shadow-lg shadow-orange-500/20" />
                                <span className="text-lg font-medium text-gray-900 dark:text-gray-200">Enterprise Intelligence Platform</span>
                            </div>
                            <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed max-w-md">
                                Transform your business data into actionable insights with AI-powered analysis.
                                Upload documents, ask questions, and get instant charts and recommendations.
                            </p>
                        </div>

                        {/* Navigation Links */}
                        <div className="flex flex-col space-y-4 pt-2">
                            <button onClick={() => navigate('/overview')} className="text-gray-600 dark:text-gray-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors text-sm text-left font-medium">Dashboard</button>
                            <button onClick={() => navigate('/chat')} className="text-gray-600 dark:text-gray-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors text-sm text-left font-medium">AI Chat</button>
                            <button onClick={() => navigate('/data-hub')} className="text-gray-600 dark:text-gray-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors text-sm text-left font-medium">Data Hub</button>
                            <button onClick={() => navigate('/reports')} className="text-gray-600 dark:text-gray-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors text-sm text-left font-medium">Reports</button>
                        </div>

                        {/* Feature Links */}
                        <div className="flex flex-col space-y-4 pt-2">
                            <span className="text-gray-500 dark:text-gray-500 text-sm">Multi-Mode Intelligence</span>
                            <span className="text-gray-500 dark:text-gray-500 text-sm">Cross-Dataset Analysis</span>
                            <span className="text-gray-500 dark:text-gray-500 text-sm">Auto Chart Generation</span>
                            <span className="text-gray-500 dark:text-gray-500 text-sm">PDF & Excel Export</span>
                        </div>
                    </div>

                    {/* Bottom Bar */}
                    <div className="pt-8 border-t border-gray-200 dark:border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
                        <p className="text-gray-500 text-xs">
                            © 2025 AI Business Analyst. All rights reserved.
                        </p>
                        <p className="text-gray-500 text-xs">
                            Built for data-driven businesses
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Landing;
