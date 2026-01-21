/**
 * Forgot Password Page - Styled to match Landing page
 * Allows users to request a password reset email
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { motion } from 'framer-motion';
import { useUserStore } from '../store/userStore';
import { Sun, Moon } from 'lucide-react';

export default function ForgotPassword() {
    const { isDark, toggleTheme } = useUserStore();
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

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

    const renderBackground = () => (
        <>
            {/* Background Orbs */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full blur-[100px] opacity-20 bg-emerald-500/20" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] rounded-full blur-[120px] opacity-10 bg-teal-500/20" />
            </div>

            {/* Theme Toggle */}
            <button
                onClick={toggleTheme}
                className="absolute top-6 right-6 p-3 rounded-full shadow-lg transition-transform hover:scale-110 active:scale-95 z-50 glass-card border border-border"
                aria-label="Toggle theme"
            >
                {isDark ? (
                    <Sun className="w-6 h-6 text-amber-400" />
                ) : (
                    <Moon className="w-6 h-6 text-slate-500" />
                )}
            </button>
        </>
    );

    if (message) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300 relative overflow-hidden bg-primary text-primary">
                {renderBackground()}

                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full rounded-2xl p-8 text-center glass-card shadow-xl backdrop-blur-xl border border-white/10 relative z-10"
                >
                    <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-500/20">
                        <svg className="w-10 h-10 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                    </div>

                    <h2 className="text-2xl font-bold mb-3" style={{ color: 'var(--text-primary)' }}>Check your email</h2>
                    <p className="mb-8" style={{ color: 'var(--text-muted)' }}>
                        {message}
                    </p>

                    <Link
                        to="/login"
                        className="inline-block px-8 py-3 font-semibold rounded-lg transition-all hover:opacity-90 shadow-lg shadow-emerald-500/20"
                        style={{
                            background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                            color: '#FFFFFF'
                        }}
                    >
                        Return to Login
                    </Link>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300 relative overflow-hidden bg-primary text-primary">
            {renderBackground()}

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-md w-full relative z-10"
            >
                {/* Logo/Brand */}
                <div className="text-center mb-8">
                    <Link to="/" className="inline-flex items-center gap-3 group">
                        <div className="relative">
                            <div className="absolute inset-0 rounded-full blur-lg opacity-50 group-hover:opacity-100 transition-opacity bg-teal-500/30" />
                            <img src="/logo.png" alt="DataVision Logo" className="w-14 h-14 object-contain relative z-10 drop-shadow-lg" />
                        </div>
                        <span className="text-3xl font-bold tracking-tight">
                            <span style={{ color: 'var(--text-primary)' }}>Data</span>
                            <span className="text-emerald-500">Vision</span>
                        </span>
                    </Link>
                    <p className="mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                        Recover your account access
                    </p>
                </div>

                {/* Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="p-8 md:p-10 rounded-3xl shadow-2xl glass-card backdrop-blur-xl border border-white/10"
                >
                    <h2 className="text-2xl font-bold text-center mb-2" style={{ color: 'var(--text-primary)' }}>
                        Reset Password
                    </h2>
                    <p className="text-center mb-8" style={{ color: 'var(--text-muted)' }}>
                        Enter your email to receive a reset link
                    </p>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 rounded-xl flex items-start gap-3 bg-red-500/10 border border-red-500/20">
                            <div className="w-1 h-full bg-red-500 rounded-full" />
                            <p className="text-sm text-red-500">{error}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="space-y-4">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                                    Email
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full px-5 py-3.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-primary-500/50 glass-input"
                                    placeholder="you@example.com"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3.5 rounded-xl font-semibold text-white shadow-lg shadow-green-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
                                style={{
                                    background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                                }}
                            >
                                {loading ? 'Sending...' : 'Send Reset Link'}
                            </button>
                        </div>
                    </form>

                    <div className="mt-8 text-center pt-6 border-t border-border/50">
                        <Link to="/login" className="text-sm transition-colors hover:opacity-100 opacity-80 font-medium" style={{ color: '#22c55e' }}>
                            ← Back to login
                        </Link>
                    </div>
                </motion.div>
            </motion.div>
        </div>
    );
}
