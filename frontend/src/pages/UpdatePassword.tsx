/**
 * Update Password Page - For users who clicked the reset link from email
 * This page is shown after clicking the password reset link
 * Supports both native auth flow and custom token-based flow
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../lib/auth-client';
import { motion } from 'framer-motion';
import { useUserStore } from '../store/userStore';
import { Sun, Moon, Lock, CheckCircle, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { api } from '../services/api';

export default function UpdatePassword() {
    const { isDark, toggleTheme } = useUserStore();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [validSession, setValidSession] = useState<boolean | null>(null);
    
    // Custom token-based flow parameters - read directly from URL
    const customToken = searchParams.get('token');
    const customEmail = searchParams.get('email');
    const isCustomFlow = !!(customToken && customEmail);

    // Debug logging
    useEffect(() => {
        console.log('UpdatePassword: URL params check', {
            token: customToken ? 'present' : 'missing',
            email: customEmail,
            isCustomFlow,
            fullUrl: window.location.href
        });
    }, [customToken, customEmail, isCustomFlow]);

    // Check if user has a valid recovery session
    useEffect(() => {
        const checkSession = async () => {
            console.log('UpdatePassword: Checking session, isCustomFlow:', isCustomFlow);
            
            // If we have custom token and email from our custom flow, it's valid
            if (customToken && customEmail) {
                console.log('UpdatePassword: Custom flow detected, setting validSession to true');
                setValidSession(true);
                return;
            }
            
            try {
                const { data: { session }, error } = await supabase.auth.getSession();
                
                if (error) {
                    console.error('Session error:', error);
                    setValidSession(false);
                    return;
                }

                // Check if this is a recovery session (from email link)
                if (session?.user) {
                    setValidSession(true);
                } else {
                    // Try to get session from URL hash (recovery flow)
                    const hashParams = new URLSearchParams(window.location.hash.substring(1));
                    const accessToken = hashParams.get('access_token');
                    const type = hashParams.get('type');
                    
                    if (accessToken && type === 'recovery') {
                        // Set session from recovery token
                        const { error: setSessionError } = await supabase.auth.setSession({
                            access_token: accessToken,
                            refresh_token: hashParams.get('refresh_token') || ''
                        });
                        
                        if (setSessionError) {
                            console.error('Set session error:', setSessionError);
                            setValidSession(false);
                        } else {
                            setValidSession(true);
                        }
                    } else {
                        setValidSession(false);
                    }
                }
            } catch (err) {
                console.error('Check session error:', err);
                setValidSession(false);
            }
        };

        checkSession();

        // Listen for auth state changes (handles recovery flow)
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
            if (event === 'PASSWORD_RECOVERY') {
                setValidSession(true);
            }
        });

        return () => subscription.unsubscribe();
    }, [customToken, customEmail]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validation
        if (password.length < 6) {
            setError('Password must be at least 6 characters long');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setLoading(true);

        try {
            if (isCustomFlow) {
                // Use our custom backend endpoint for token-based password reset
                const response = await api.post('/api/v1/settings/auth/update-password-with-token', {
                    token: customToken,
                    email: customEmail,
                    new_password: password
                });

                if (response.data.success) {
                    setSuccess(true);
                    // Redirect to login after 3 seconds
                    setTimeout(() => {
                        navigate('/login');
                    }, 3000);
                } else {
                    setError(response.data.message || 'Failed to update password');
                }
            } else {
                // Use native auth flow
                const { error } = await supabase.auth.updateUser({
                    password: password
                });

                if (error) {
                    setError(error.message);
                } else {
                    setSuccess(true);
                    // Redirect to login after 3 seconds
                    setTimeout(() => {
                        navigate('/login');
                    }, 3000);
                }
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const renderBackground = () => (
        <>
            {/* Background Orbs */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full blur-[100px] opacity-20 bg-emerald-500/20" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] rounded-full blur-[120px] opacity-10 bg-green-500/20" />
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

    // Success state
    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300 relative overflow-hidden bg-primary text-primary">
                {renderBackground()}

                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full rounded-2xl p-8 text-center glass-card shadow-xl backdrop-blur-xl border border-white/10 relative z-10"
                >
                    <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-500/20">
                        <CheckCircle className="w-10 h-10 text-emerald-500" />
                    </div>

                    <h2 className="text-2xl font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Password Updated!
                    </h2>
                    <p className="mb-8" style={{ color: 'var(--text-muted)' }}>
                        Your password has been successfully reset. You will be redirected to login shortly.
                    </p>

                    <Link
                        to="/login"
                        className="inline-block px-8 py-3 font-semibold rounded-lg transition-all hover:opacity-90 shadow-lg shadow-emerald-500/20"
                        style={{
                            background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                            color: '#FFFFFF'
                        }}
                    >
                        Go to Login
                    </Link>
                </motion.div>
            </div>
        );
    }

    // Invalid/expired link state
    if (validSession === false) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300 relative overflow-hidden bg-primary text-primary">
                {renderBackground()}

                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full rounded-2xl p-8 text-center glass-card shadow-xl backdrop-blur-xl border border-white/10 relative z-10"
                >
                    <div className="w-20 h-20 bg-amber-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-amber-500/20">
                        <AlertTriangle className="w-10 h-10 text-amber-500" />
                    </div>

                    <h2 className="text-2xl font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Invalid or Expired Link
                    </h2>
                    <p className="mb-8" style={{ color: 'var(--text-muted)' }}>
                        This password reset link is invalid or has expired. Please request a new one.
                    </p>

                    <div className="flex flex-col gap-3">
                        <Link
                            to="/forgot-password"
                            className="inline-block px-8 py-3 font-semibold rounded-lg transition-all hover:opacity-90 shadow-lg shadow-emerald-500/20"
                            style={{
                                background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                                color: '#FFFFFF'
                            }}
                        >
                            Request New Link
                        </Link>
                        <Link
                            to="/login"
                            className="text-sm transition-colors hover:opacity-100 opacity-80 font-medium"
                            style={{ color: '#22c55e' }}
                        >
                            ← Back to Login
                        </Link>
                    </div>
                </motion.div>
            </div>
        );
    }

    // Loading/checking session
    if (validSession === null) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300 relative overflow-hidden bg-primary text-primary">
                {renderBackground()}
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4" />
                    <p style={{ color: 'var(--text-muted)' }}>Verifying reset link...</p>
                </div>
            </div>
        );
    }

    // Main reset form
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
                            <div className="absolute inset-0 rounded-full blur-lg opacity-50 group-hover:opacity-100 transition-opacity bg-green-500/30" />
                            <img src={isDark ? '/datavision-logo-dark.jpg' : '/datavision-logo-light.jpg'} alt="DataVision Logo" className="w-14 h-14 object-contain relative z-10 drop-shadow-lg rounded-full" onError={(e) => { (e.target as HTMLImageElement).src = '/logo.svg'; }} />
                        </div>
                        <span className="text-3xl font-bold tracking-tight">
                            <span style={{ color: 'var(--text-primary)' }}>Data</span>
                            <span className="text-emerald-500">Vision</span>
                        </span>
                    </Link>
                    <p className="mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                        Create a new password
                    </p>
                </div>

                {/* Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="p-8 md:p-10 rounded-3xl shadow-2xl glass-card backdrop-blur-xl border border-white/10"
                >
                    <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-500/20">
                        <Lock className="w-8 h-8 text-emerald-500" />
                    </div>

                    <h2 className="text-2xl font-bold text-center mb-2" style={{ color: 'var(--text-primary)' }}>
                        Set New Password
                    </h2>
                    <p className="text-center mb-8" style={{ color: 'var(--text-muted)' }}>
                        Enter your new password below
                    </p>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 rounded-xl flex items-start gap-3 bg-red-500/10 border border-red-500/20">
                            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-red-500">{error}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="space-y-4">
                            <div>
                                <label htmlFor="password" className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                                    New Password
                                </label>
                                <div className="relative">
                                    <input
                                        id="password"
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={6}
                                        className="w-full px-5 py-3.5 pr-12 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-primary-500/50 glass-input"
                                        placeholder="Min 6 characters"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 opacity-60 hover:opacity-100 transition-opacity"
                                    >
                                        {showPassword ? (
                                            <EyeOff className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                                        ) : (
                                            <Eye className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                                        )}
                                    </button>
                                </div>
                            </div>

                            <div>
                                <label htmlFor="confirmPassword" className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                                    Confirm Password
                                </label>
                                <div className="relative">
                                    <input
                                        id="confirmPassword"
                                        type={showConfirmPassword ? 'text' : 'password'}
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        required
                                        minLength={6}
                                        className="w-full px-5 py-3.5 pr-12 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-primary-500/50 glass-input"
                                        placeholder="Re-enter password"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 opacity-60 hover:opacity-100 transition-opacity"
                                    >
                                        {showConfirmPassword ? (
                                            <EyeOff className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                                        ) : (
                                            <Eye className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* Password match indicator */}
                            {confirmPassword && (
                                <div className={`flex items-center gap-2 text-sm ${password === confirmPassword ? 'text-emerald-500' : 'text-amber-500'}`}>
                                    {password === confirmPassword ? (
                                        <>
                                            <CheckCircle className="w-4 h-4" />
                                            Passwords match
                                        </>
                                    ) : (
                                        <>
                                            <AlertTriangle className="w-4 h-4" />
                                            Passwords do not match
                                        </>
                                    )}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading || password !== confirmPassword || password.length < 6}
                                className="w-full py-3.5 rounded-xl font-semibold text-white shadow-lg shadow-green-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:scale-100"
                                style={{
                                    background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                                }}
                            >
                                {loading ? 'Updating Password...' : 'Update Password'}
                            </button>
                        </div>
                    </form>

                    <div className="mt-8 text-center pt-6 border-t border-border/50">
                        <Link to="/login" className="text-sm transition-colors hover:opacity-100 opacity-80 font-medium" style={{ color: '#22c55e' }}>
                            ← Back to Login
                        </Link>
                    </div>
                </motion.div>
            </motion.div>
        </div>
    );
}
