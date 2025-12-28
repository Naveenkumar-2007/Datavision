/**
 * Email Confirmation Page
 * Verifies the token from confirmation email and redirects to login
 */

import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function EmailConfirm() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [message, setMessage] = useState('');
    const [isDark, setIsDark] = useState(true);

    useEffect(() => {
        const saved = localStorage.getItem('theme');
        setIsDark(saved !== 'light');
    }, []);

    // Theme colors
    const bgColor = isDark ? '#0F172A' : '#F8FAFC';
    const cardBg = isDark ? '#1E293B' : '#FFFFFF';
    const textPrimary = isDark ? '#F8FAFC' : '#0F172A';
    const textMuted = isDark ? '#94A3B8' : '#64748B';
    const borderColor = isDark ? '#334155' : '#E2E8F0';

    useEffect(() => {
        const token = searchParams.get('token');

        if (!token) {
            setStatus('error');
            setMessage('Invalid confirmation link. No token provided.');
            return;
        }

        // Verify the token with backend
        const verifyToken = async () => {
            try {
                const response = await axios.get(`/api/v1/auth/confirm-email?token=${token}`);

                if (response.data.success) {
                    setStatus('success');
                    setMessage('Your email has been confirmed successfully!');

                    // Auto-redirect to login after 3 seconds
                    setTimeout(() => navigate('/login'), 3000);
                } else {
                    setStatus('error');
                    setMessage(response.data.error || 'Failed to confirm email.');
                }
            } catch (err: any) {
                setStatus('error');
                setMessage(err.response?.data?.detail || 'Invalid or expired confirmation link.');
            }
        };

        verifyToken();
    }, [searchParams, navigate]);

    return (
        <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300" style={{ backgroundColor: bgColor }}>
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-md w-full rounded-2xl p-8 text-center border shadow-xl"
                style={{ backgroundColor: cardBg, borderColor }}
            >
                {status === 'loading' && (
                    <>
                        <div className="w-16 h-16 border-4 border-t-teal-500 border-r-teal-500 border-b-transparent border-l-transparent rounded-full animate-spin mx-auto mb-6" />
                        <h2 className="text-xl font-bold mb-2" style={{ color: textPrimary }}>
                            Confirming your email...
                        </h2>
                        <p style={{ color: textMuted }}>Please wait while we verify your account.</p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6 border border-green-500/30">
                            <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold mb-2" style={{ color: textPrimary }}>
                            Email Confirmed! 🎉
                        </h2>
                        <p className="mb-6" style={{ color: textMuted }}>
                            {message}
                        </p>
                        <p className="text-sm mb-6" style={{ color: textMuted }}>
                            Redirecting to login in 3 seconds...
                        </p>
                        <button
                            onClick={() => navigate('/login')}
                            className="px-8 py-3 font-semibold rounded-lg transition-all hover:opacity-90"
                            style={{
                                background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
                                color: '#FFFFFF'
                            }}
                        >
                            Go to Login Now
                        </button>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6 border border-red-500/30">
                            <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold mb-2" style={{ color: textPrimary }}>
                            Confirmation Failed
                        </h2>
                        <p className="mb-6" style={{ color: textMuted }}>
                            {message}
                        </p>
                        <div className="space-y-3">
                            <button
                                onClick={() => navigate('/signup')}
                                className="w-full px-8 py-3 font-semibold rounded-lg transition-all hover:opacity-90"
                                style={{
                                    background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
                                    color: '#FFFFFF'
                                }}
                            >
                                Sign Up Again
                            </button>
                            <button
                                onClick={() => navigate('/login')}
                                className="w-full px-8 py-3 font-medium rounded-lg transition-all"
                                style={{
                                    backgroundColor: isDark ? '#334155' : '#E2E8F0',
                                    color: textPrimary
                                }}
                            >
                                Go to Login
                            </button>
                        </div>
                    </>
                )}
            </motion.div>
        </div>
    );
}
