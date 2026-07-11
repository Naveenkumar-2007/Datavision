/**
 * Auth Callback - PRODUCTION READY
 * Handles OAuth redirects and email confirmations
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/auth-client';

export default function AuthCallback() {
    const navigate = useNavigate();
    const [error, setError] = useState<string | null>(null);
    const [isEmailConfirm, setIsEmailConfirm] = useState(false);

    useEffect(() => {
        let isMounted = true;
        let attempts = 0;

        // Check for error in URL
        const params = new URLSearchParams(window.location.search);
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const urlError = params.get('error') || hashParams.get('error');

        // Check if this is an email confirmation callback
        const type = hashParams.get('type') || params.get('type');
        if (type === 'signup' || type === 'email_confirmation' || type === 'recovery') {
            setIsEmailConfirm(true);
        }

        if (urlError) {
            const desc = params.get('error_description') || hashParams.get('error_description');
            setError(desc || urlError);
            return;
        }

        // Native OAuth token from FastAPI
        const customToken = params.get('token');
        if (customToken) {
            localStorage.setItem('auth_token', customToken);
            fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/auth/me`, {
                headers: { 'Authorization': `Bearer ${customToken}` }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && isMounted) {
                    localStorage.setItem('auth_user', JSON.stringify(data.user));
                    localStorage.setItem('userId', data.user.id);
                    navigate('/data-hub', { replace: true });
                } else if (isMounted) {
                    setError('Failed to fetch user profile');
                }
            })
            .catch(() => {
                if (isMounted) setError('Authentication error');
            });
            return;
        }

        // Poll for session (Legacy fallback)
        const checkSession = async () => {
            attempts++;

            const { data: { session } } = await supabase.auth.getSession();

            if (!isMounted) return;

            if (session) {
                // Store userId for API calls
                localStorage.setItem('userId', session.user.id);

                // If email confirmation, show success briefly then redirect to data-hub
                if (isEmailConfirm) {
                    setTimeout(() => navigate('/data-hub', { replace: true }), 1500);
                } else {
                    // OAuth login - go directly to data-hub
                    navigate('/data-hub', { replace: true });
                }
            } else if (attempts < 20) {
                // Keep polling (10 seconds max)
                setTimeout(checkSession, 500);
            } else {
                // No session - might be just email confirmation without auto-login
                if (isEmailConfirm) {
                    setTimeout(() => navigate('/login', { replace: true }), 2000);
                } else {
                    setError('Authentication timeout. Please try again.');
                }
            }
        };

        // Wait a bit for URL tokens to be processed, then start checking
        setTimeout(checkSession, 300);

        return () => { isMounted = false; };
    }, [navigate, isEmailConfirm]);

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-900 p-4">
                <div className="bg-gray-800 rounded-2xl p-8 max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-white mb-2">Login Failed</h2>
                    <p className="text-gray-400 mb-6">{error}</p>
                    <a href="/login" className="px-6 py-2 bg-green-500 text-white rounded-lg inline-block">
                        Try Again
                    </a>
                </div>
            </div>
        );
    }

    // Email confirmation success view
    if (isEmailConfirm) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-900 p-4">
                <div className="bg-gray-800 rounded-2xl p-8 max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-white mb-2">Email Confirmed! 🎉</h2>
                    <p className="text-gray-400 mb-4">Your account is now verified.</p>
                    <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                    <p className="text-gray-500 text-sm mt-2">Redirecting...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900">
            <div className="text-center">
                <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-white">Completing login...</p>
            </div>
        </div>
    );
}
