import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Play, ChevronLeft, ChevronRight, Download, Loader2, Sparkles, FileText, Image, Presentation, LayoutDashboard, Save } from 'lucide-react';
import apiService from '@/services/api';
import { api } from '@/services/api';
import { useUserStore } from '@/store/userStore';
import { useToast } from '@/contexts/ToastContext';

export const DataStories: React.FC = () => {
    const isDark = useUserStore((state) => state.isDark);
    const { addToast } = useToast();
    const [files, setFiles] = useState<any[]>([]);
    const [selectedFile, setSelectedFile] = useState('');
    const [topic, setTopic] = useState('');
    const [loading, setLoading] = useState(false);
    
    // Presentation State
    const [story, setStory] = useState<any>(null);
    const [currentSlide, setCurrentSlide] = useState(0);

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = async () => {
        try {
            const userId = useUserStore.getState().user?.id || 'default';
            const res = await api.get(`/api/v1/files/${userId}/files`);
            if (res.data && res.data.files) {
                setFiles(res.data.files);
                if (res.data.files.length > 0) {
                    setSelectedFile(res.data.files[0].name);
                }
            }
        } catch (e) {
            console.error("Failed to fetch files", e);
        }
    };

    const handleGenerateStory = async () => {
        if (!selectedFile) {
            addToast('error', 'Missing Data', 'Please select a dataset first.');
            return;
        }

        setLoading(true);
        setStory(null);
        setCurrentSlide(0);

        try {
            const res = await api.post('/api/v1/reports/story', {
                filename: selectedFile,
                topic: topic
            });
            setStory(res.data);
            addToast('success', 'Story Generated', 'Your AI data story is ready to present.');
        } catch (e: any) {
            addToast('error', 'Generation Failed', e.response?.data?.detail || e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveStory = async () => {
        if (!story) return;
        try {
            const res = await api.post('/api/v1/reports/save-story', {
                title: story.title,
                content: JSON.stringify(story),
                dataset_name: selectedFile
            });
            if (res.data.success) {
                addToast('success', 'Story Saved', 'Data Story successfully saved to PostgreSQL database.');
            } else {
                addToast('error', 'Failed to Save', res.data.error);
            }
        } catch (e: any) {
            addToast('error', 'Save Error', e.response?.data?.detail || e.message);
        }
    };

    const nextSlide = () => {
        if (story && currentSlide < story.slides.length - 1) {
            setCurrentSlide(prev => prev + 1);
        }
    };

    const prevSlide = () => {
        if (currentSlide > 0) {
            setCurrentSlide(prev => prev - 1);
        }
    };

    // Keyboard navigation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!story) return;
            if (e.key === 'ArrowRight' || e.key === 'Space') {
                nextSlide();
            } else if (e.key === 'ArrowLeft') {
                prevSlide();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [story, currentSlide]);

    return (
        <div className="flex-1 overflow-y-auto h-full" style={{ backgroundColor: 'var(--bg-main)' }}>
            <div className="max-w-7xl mx-auto p-4 md:p-8">
                
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 text-white shadow-lg shadow-indigo-500/20">
                                <BookOpen className="w-6 h-6" />
                            </div>
                            <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                                Data Stories
                            </h1>
                        </div>
                        <p className="text-lg ml-1" style={{ color: 'var(--text-muted)' }}>
                            Transform raw data into McKinsey-style narrative presentations.
                        </p>
                    </div>
                </div>

                {/* Configuration Panel */}
                {!story && (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-6 md:p-8 rounded-3xl border shadow-xl"
                        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                    >
                        <div className="max-w-2xl mx-auto">
                            <div className="w-16 h-16 mx-auto bg-indigo-500/10 rounded-2xl flex items-center justify-center mb-6">
                                <Presentation className="w-8 h-8 text-indigo-500" />
                            </div>
                            <h2 className="text-2xl font-bold text-center mb-2" style={{ color: 'var(--text-primary)' }}>Generate a Presentation</h2>
                            <p className="text-center mb-8" style={{ color: 'var(--text-secondary)' }}>
                                Select a dataset and optionally provide a goal. Our AI will analyze the data, extract key insights, and build a slide-by-slide narrative.
                            </p>

                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>1. Select Dataset</label>
                                    <select
                                        value={selectedFile}
                                        onChange={(e) => setSelectedFile(e.target.value)}
                                        className="w-full p-4 rounded-xl border outline-none focus:ring-2 focus:ring-indigo-500/50 appearance-none bg-no-repeat"
                                        style={{ 
                                            backgroundColor: 'var(--bg-surface)', 
                                            borderColor: 'var(--border-color)',
                                            color: 'var(--text-primary)',
                                            backgroundImage: 'url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23666%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E")',
                                            backgroundPosition: 'right 1rem top 50%',
                                            backgroundSize: '0.65em auto'
                                        }}
                                    >
                                        <option value="">Choose a file...</option>
                                        {files.map(f => (
                                            <option key={f.name} value={f.name}>{f.name}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>2. Presentation Goal (Optional)</label>
                                    <input
                                        type="text"
                                        value={topic}
                                        onChange={(e) => setTopic(e.target.value)}
                                        placeholder="e.g., Explain why our Q3 sales dropped..."
                                        className="w-full p-4 rounded-xl border outline-none focus:ring-2 focus:ring-indigo-500/50"
                                        style={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                    />
                                </div>

                                <button
                                    onClick={handleGenerateStory}
                                    disabled={loading || !selectedFile}
                                    className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-lg shadow-lg shadow-indigo-500/25 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none flex justify-center items-center gap-2"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-6 h-6 animate-spin" />
                                            Analyzing Data & Writing Story...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-6 h-6" />
                                            Generate AI Story
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Presentation Viewer */}
                {story && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="rounded-3xl border shadow-2xl overflow-hidden flex flex-col h-[70vh] min-h-[600px]"
                        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                    >
                        {/* Toolbar */}
                        <div className="h-16 border-b flex items-center justify-between px-6" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-surface)' }}>
                            <div className="flex items-center gap-4">
                                <button 
                                    onClick={() => setStory(null)}
                                    className="text-sm font-medium hover:underline flex items-center gap-1"
                                    style={{ color: 'var(--text-secondary)' }}
                                >
                                    <ChevronLeft className="w-4 h-4" /> Exit
                                </button>
                                <div className="h-4 w-px" style={{ backgroundColor: 'var(--border-color)' }} />
                                <span className="text-sm font-semibold truncate max-w-[200px] md:max-w-md" style={{ color: 'var(--text-primary)' }}>
                                    {story.title}
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleSaveStory}
                                    className="p-1.5 rounded-lg transition-all flex items-center gap-1 bg-emerald-100 text-emerald-600 hover:bg-emerald-200 dark:bg-emerald-500/20 dark:text-emerald-400 dark:hover:bg-emerald-500/30"
                                    title="Save to Database"
                                >
                                    <Save className="w-4 h-4" />
                                    <span className="text-xs font-semibold">Save</span>
                                </button>
                                <span className="text-xs font-mono px-3 py-1 rounded-full bg-black/5 dark:bg-white/5 ml-2">
                                    Slide {currentSlide + 1} of {story.slides.length}
                                </span>
                            </div>
                        </div>

                        {/* Slide Content */}
                        <div className="flex-1 relative overflow-hidden bg-black/5 dark:bg-black/20 flex flex-col items-center justify-center p-8 md:p-16">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={currentSlide}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    transition={{ duration: 0.3 }}
                                    className="w-full max-w-5xl bg-white dark:bg-[#1e1e1e] rounded-xl shadow-2xl p-10 md:p-16 border flex flex-col justify-center min-h-[400px]"
                                    style={{ borderColor: 'var(--border-color)' }}
                                >
                                    {currentSlide === 0 ? (
                                        // Title Slide specific formatting if it's the first slide (if the AI generated a true title slide)
                                        <div className="text-center space-y-6">
                                            <h2 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-600 leading-tight">
                                                {story.slides[currentSlide].title || story.title}
                                            </h2>
                                            <p className="text-xl md:text-2xl text-gray-500 dark:text-gray-400 max-w-3xl mx-auto">
                                                {story.slides[currentSlide].narrative || story.subtitle}
                                            </p>
                                            {story.slides[currentSlide].key_metric && (
                                                <div className="inline-block mt-8 px-8 py-4 rounded-2xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800">
                                                    <span className="text-3xl font-black text-indigo-600 dark:text-indigo-400">
                                                        {story.slides[currentSlide].key_metric}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        // Standard Content Slide
                                        <div className="flex flex-col md:flex-row gap-12 h-full">
                                            <div className="flex-1 space-y-6 flex flex-col justify-center">
                                                <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
                                                    {story.slides[currentSlide].title}
                                                </h2>
                                                <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 leading-relaxed">
                                                    {story.slides[currentSlide].narrative}
                                                </p>
                                                {story.slides[currentSlide].key_metric && (
                                                    <div className="mt-4 flex items-center gap-3">
                                                        <div className="w-1.5 h-12 bg-purple-500 rounded-full" />
                                                        <span className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                                                            {story.slides[currentSlide].key_metric}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                            
                                            {/* Visual Placeholder (in a real app, this would render Recharts/Plotly) */}
                                            {story.slides[currentSlide].suggested_chart !== 'none' && (
                                                <div className="flex-1 flex items-center justify-center">
                                                    <div className="w-full aspect-video rounded-xl bg-gray-50 dark:bg-black/20 border border-gray-100 dark:border-gray-800 flex flex-col items-center justify-center p-6 text-center">
                                                        <LayoutDashboard className="w-12 h-12 text-gray-400 mb-4" />
                                                        <span className="text-sm font-semibold text-gray-500">
                                                            {story.slides[currentSlide].suggested_chart.toUpperCase()} CHART PLACEHOLDER
                                                        </span>
                                                        <span className="text-xs text-gray-400 mt-2 font-mono">
                                                            X: {story.slides[currentSlide].chart_x_column} | Y: {story.slides[currentSlide].chart_y_column}
                                                        </span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </motion.div>
                            </AnimatePresence>

                            {/* Navigation Controls */}
                            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-white dark:bg-gray-800 p-2 rounded-full shadow-xl border dark:border-gray-700">
                                <button 
                                    onClick={prevSlide}
                                    disabled={currentSlide === 0}
                                    className="p-3 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 transition-colors"
                                >
                                    <ChevronLeft className="w-6 h-6 text-gray-900 dark:text-white" />
                                </button>
                                <div className="flex gap-1.5 px-2">
                                    {story.slides.map((_: any, idx: number) => (
                                        <button
                                            key={idx}
                                            onClick={() => setCurrentSlide(idx)}
                                            className={`w-2.5 h-2.5 rounded-full transition-all ${idx === currentSlide ? 'bg-indigo-500 w-6' : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400'}`}
                                        />
                                    ))}
                                </div>
                                <button 
                                    onClick={nextSlide}
                                    disabled={currentSlide === story.slides.length - 1}
                                    className="p-3 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 transition-colors"
                                >
                                    <ChevronRight className="w-6 h-6 text-gray-900 dark:text-white" />
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    );
};

export default DataStories;

