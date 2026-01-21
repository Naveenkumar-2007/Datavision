/**
 * Signup Page - Styled to match Landing page
 * Uses new logo and teal/blue theme
 * Supports both light and dark mode
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';
import { useUserStore } from '../store/userStore';
import { Sun, Moon } from 'lucide-react';

export default function Signup() {
    const { signUp, signInWithGoogle, signInWithGithub } = useAuth();
    const { isDark, toggleTheme } = useUserStore();

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        fullName: '',
        companyName: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    // Theme colors matching Landing page (using global vars)
    // Legacy theme logic removed - handled by App.tsx / userStore

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        if (formData.password.length < 8) {
            setError('Password must be at least 8 characters');
            setLoading(false);
            return;
        }

        try {
            const { error } = await signUp(formData.email, formData.password, {
                full_name: formData.fullName,
                company_name: formData.companyName
            });

            if (error) {
                setError(error.message || 'Signup failed');
            } else {
                setSuccess(true);
            }
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSignup = async () => {
        setLoading(true);
        setError('');
        try {
            const { error } = await signInWithGoogle();
            if (error) throw error;
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleGithubSignup = async () => {
        setLoading(true);
        setError('');
        try {
            const { error } = await signInWithGithub();
            if (error) throw error;
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300 relative overflow-hidden bg-primary text-primary">
                {/* Background Orbs */}
                <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                    <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full blur-[100px] opacity-20 bg-emerald-500/20" />
                    <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] rounded-full blur-[120px] opacity-10 bg-teal-500/20" />
                </div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full rounded-2xl p-8 text-center glass-card shadow-2xl backdrop-blur-xl border border-white/10 relative z-10"
                >
                    {/* Email Icon */}
                    <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-500/20">
                        <svg className="w-10 h-10 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                    </div>

                    <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Account Created!</h2>

                    {/* Check Your Inbox - Prominent */}
                    <div className="py-4 px-6 rounded-xl mb-4 glass-panel border border-emerald-500/20 bg-emerald-500/5">
                        <p className="text-xl font-bold mb-1 text-emerald-500">
                            📧 Check your inbox
                        </p>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                            We've sent a confirmation email to:
                        </p>
                        <p className="font-medium mt-1" style={{ color: 'var(--text-primary)' }}>
                            {formData.email}
                        </p>
                    </div>

                    <div className="space-y-3 text-sm mb-8 text-left bg-white/5 p-4 rounded-xl border border-white/5">
                        <p className="flex items-center gap-3">
                            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-500 text-xs">✓</span>
                            <span style={{ color: 'var(--text-muted)' }}>Click the link in the email to verify</span>
                        </p>
                        <p className="flex items-center gap-3">
                            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-500 text-xs">✓</span>
                            <span style={{ color: 'var(--text-muted)' }}>Sign in to access your dashboard</span>
                        </p>
                    </div>

                    <Link
                        to="/login"
                        className="block w-full px-8 py-3.5 font-semibold rounded-xl transition-all hover:scale-[1.02] shadow-lg shadow-emerald-500/20"
                        style={{
                            background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                            color: '#FFFFFF'
                        }}
                    >
                        Go to Login
                    </Link>

                    <button
                        onClick={() => setSuccess(false)}
                        className="mt-4 text-sm hover:underline"
                        style={{ color: 'var(--text-muted)' }}
                    >
                        Back to signup
                    </button>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300 relative overflow-hidden bg-primary text-primary">
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

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-md w-full relative z-10"
            >
                {/* Logo Section */}
                <div className="text-center mb-8">
                    <Link to="/" className="inline-flex items-center gap-3 group">
                        <div className="relative">
                            <div className="absolute inset-0 rounded-full blur-lg opacity-50 group-hover:opacity-100 transition-opacity bg-teal-500/30" />
                            <img src="/logo.png" alt="DataVision" className="w-14 h-14 object-contain relative z-10 drop-shadow-lg" />
                        </div>
                        <span className="text-3xl font-bold tracking-tight">
                            <span style={{ color: 'var(--text-primary)' }}>Data</span>
                            <span className="text-emerald-500">Vision</span>
                        </span>
                    </Link>
                </div>

                {/* Signup Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="p-8 md:p-10 rounded-3xl shadow-2xl glass-card backdrop-blur-xl border border-white/10"
                >
                    <div className="text-center mb-8">
                        <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                            Create an account
                        </h2>
                        <p style={{ color: 'var(--text-muted)' }}>
                            Start your journey with DataVision
                        </p>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 rounded-xl flex items-start gap-3 bg-red-500/10 border border-red-500/20">
                            <div className="w-1 h-full bg-red-500 rounded-full" />
                            <p className="text-sm text-red-500">{error}</p>
                        </div>
                    )}

                    {/* Signup Form */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div className="space-y-1.5">
                            <label className="text-sm font-medium ml-1" style={{ color: 'var(--text-secondary)' }}>
                                Full Name
                            </label>
                            <input
                                name="fullName"
                                type="text"
                                value={formData.fullName}
                                onChange={handleChange}
                                className="w-full px-5 py-3.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-primary-500/50 glass-input"
                                placeholder="John Doe"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium ml-1" style={{ color: 'var(--text-secondary)' }}>
                                Email
                            </label>
                            <input
                                name="email"
                                type="email"
                                value={formData.email}
                                onChange={handleChange}
                                required
                                className="w-full px-5 py-3.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-primary-500/50 glass-input"
                                placeholder="you@example.com"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium ml-1" style={{ color: 'var(--text-secondary)' }}>
                                Password
                            </label>
                            <input
                                name="password"
                                type="password"
                                value={formData.password}
                                onChange={handleChange}
                                required
                                className="w-full px-5 py-3.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-primary-500/50 glass-input"
                                placeholder="••••••••"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium ml-1" style={{ color: 'var(--text-secondary)' }}>
                                Confirm Password
                            </label>
                            <input
                                name="confirmPassword"
                                type="password"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                required
                                className="w-full px-5 py-3.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-primary-500/50 glass-input"
                                placeholder="••••••••"
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
                            {loading ? 'Creating account...' : 'Create Account'}
                        </button>
                    </form>

                    <div className="my-8 flex items-center gap-4">
                        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" style={{ backgroundColor: 'var(--border-color)', opacity: 0.3 }} />
                        <span className="text-xs font-medium uppercase tracking-wider opacity-60" style={{ color: 'var(--text-muted)' }}>Or continue with</span>
                        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" style={{ backgroundColor: 'var(--border-color)', opacity: 0.3 }} />
                    </div>


                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={handleGoogleSignup}
                            disabled={loading}
                            type="button"
                            className="flex items-center justify-center gap-2 py-3 px-4 font-medium rounded-lg transition-all disabled:opacity-50 hover:opacity-90 shadow-sm"
                            style={{
                                backgroundColor: '#FFFFFF',
                                color: '#374151',
                                border: '1px solid #E5E7EB',
                            }}
                        >
                            <svg className="w-5 h-5" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                            </svg>
                            Google
                        </button>
                        <button
                            onClick={handleGithubSignup}
                            disabled={loading}
                            type="button"
                            className="flex items-center justify-center gap-2 py-3 px-4 font-medium rounded-lg transition-all disabled:opacity-50 hover:opacity-90"
                            style={{
                                backgroundColor: '#1F2937',
                                color: '#FFFFFF',
                            }}
                        >
                            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                            </svg>
                            GitHub
                        </button>
                    </div>

                    <p className="mt-8 text-xs text-center" style={{ color: 'var(--text-muted)' }}>
                        By creating an account, you agree to our{' '}
                        <Link to="/terms" style={{ color: '#22c55e' }} className="hover:underline">Terms of Service</Link>
                        {' '}and{' '}
                        <Link to="/privacy" style={{ color: '#22c55e' }} className="hover:underline">Privacy Policy</Link>
                    </p>

                    {/* Footer Links */}
                    <div className="mt-6 flex justify-center gap-6 text-xs" style={{ color: 'var(--text-muted)' }}>
                        <Link to="/privacy" className="hover:text-emerald-400 transition-colors">Privacy Policy</Link>
                        <Link to="/terms" className="hover:text-emerald-400 transition-colors">Terms of Service</Link>
                        <Link to="/help" className="hover:text-emerald-400 transition-colors">Help Center</Link>
                    </div>

                    <div className="mt-6 text-center pt-6 border-t" style={{ borderColor: 'var(--border-color)' }}>
                        <p style={{ color: 'var(--text-muted)' }}>
                            Already have an account?{' '}
                            <Link to="/login" className="font-medium transition-colors hover:opacity-80" style={{ color: '#22c55e' }}>
                                Sign in
                            </Link>
                        </p>
                    </div>
                </motion.div>

                {/* Back to Home */}
                <div className="mt-6 text-center">
                    <Link to="/" className="text-sm transition-colors hover:opacity-80" style={{ color: 'var(--text-muted)' }}>
                        ← Back to home
                    </Link>
                </div>
            </motion.div>
        </div>
    );

}
