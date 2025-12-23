/**
 * Forgot Password Page - Styled to match Landing page
 * Allows users to request a password reset email
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { motion } from 'framer-motion';

export default function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [isDark, setIsDark] = useState(true);

    useEffect(() => {
        const saved = localStorage.getItem('theme');
        setIsDark(saved !== 'light');
        if (saved === 'light') {
            document.documentElement.classList.add('light-theme');
        }
    }, []);

    // Theme colors matching Landing page
    const bgColor = isDark ? '#0F172A' : '#F8FAFC';
    const cardBg = isDark ? '#1E293B' : '#FFFFFF';
    const textPrimary = isDark ? '#F8FAFC' : '#0F172A';
    const textMuted = isDark ? '#94A3B8' : '#64748B';
    const borderColor = isDark ? '#334155' : '#E2E8F0';

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setMessage('');

        try {
            const { error } = await supabase.auth.resetPasswordForEmail(email, {
                redirectTo: `${window.location.origin}/auth/update-password`,
            });

            if (error) {
                setError(error.message);
            } else {
                setMessage('Check your email for the password reset link.');
            }
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    if (message) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300" style={{ backgroundColor: bgColor }}>
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full rounded-2xl p-8 text-center border shadow-xl"
                    style={{ backgroundColor: cardBg, borderColor }}
                >
                    <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6 border border-blue-500/30">
                        <svg className="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold mb-3" style={{ color: textPrimary }}>Check your email</h2>
                    <p className="mb-6" style={{ color: textMuted }}>
                        {message}
                    </p>
                    <Link
                        to="/login"
                        className="font-semibold transition-all hover:opacity-80"
                        style={{ color: '#14B8A6' }}
                    >
                        ← Back to login
                    </Link>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300" style={{ backgroundColor: bgColor }}>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-md w-full"
            >
                {/* Logo/Brand */}
                <div className="text-center mb-8">
                    <Link to="/" className="inline-flex items-center gap-3">
                        <img
                            src="/logo.png"
                            alt="DataVision Logo"
                            className="w-12 h-12 object-contain"
                        />
                        <span className="text-2xl font-bold" style={{ color: textPrimary }}>
                            DataVision
                        </span>
                    </Link>
                    <p className="mt-2 text-sm" style={{ color: textMuted }}>
                        Recover your account access
                    </p>
                </div>

                {/* Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="rounded-2xl p-8 shadow-xl border"
                    style={{ backgroundColor: cardBg, borderColor }}
                >
                    <h2 className="text-2xl font-bold text-center mb-2" style={{ color: textPrimary }}>
                        Reset Password
                    </h2>
                    <p className="text-center mb-8" style={{ color: textMuted }}>
                        Enter your email to receive a reset link
                    </p>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                            <p className="text-sm text-red-400">{error}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="space-y-4">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium mb-2" style={{ color: textMuted }}>
                                    Email
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full px-4 py-3 rounded-lg transition-all focus:outline-none"
                                    style={{
                                        backgroundColor: isDark ? '#0F172A' : '#F1F5F9',
                                        border: `1px solid ${borderColor}`,
                                        color: textPrimary,
                                    }}
                                    placeholder="you@example.com"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
                                style={{
                                    background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
                                    color: '#FFFFFF',
                                }}
                            >
                                {loading ? 'Sending...' : 'Send Reset Link'}
                            </button>
                        </div>
                    </form>

                    <div className="mt-6 text-center pt-6 border-t" style={{ borderColor }}>
                        <Link to="/login" className="text-sm transition-colors hover:opacity-80 font-medium" style={{ color: '#14B8A6' }}>
                            ← Back to login
                        </Link>
                    </div>
                </motion.div>
            </motion.div>
        </div>
    );
}
