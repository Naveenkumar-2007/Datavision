/**
 * Auth Callback - PRODUCTION READY
 * Handles OAuth redirects - just waits for Supabase to process
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function AuthCallback() {
    const navigate = useNavigate();
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        let attempts = 0;

        // Check for error in URL
        const params = new URLSearchParams(window.location.search);
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const urlError = params.get('error') || hashParams.get('error');

        if (urlError) {
            const desc = params.get('error_description') || hashParams.get('error_description');
            setError(desc || urlError);
            return;
        }

        // Poll for session - Supabase's detectSessionInUrl will set it
        const checkSession = async () => {
            attempts++;

            const { data: { session } } = await supabase.auth.getSession();

            if (!isMounted) return;

            if (session) {
                // Store userId for API calls (NOT the token - Supabase handles that)
                localStorage.setItem('userId', session.user.id);
                // Navigate to dashboard
                navigate('/overview', { replace: true });
            } else if (attempts < 20) {
                // Keep polling (10 seconds max)
                setTimeout(checkSession, 500);
            } else {
                setError('Authentication timeout. Please try again.');
            }
        };

        // Wait a bit for Supabase to process URL tokens, then start checking
        setTimeout(checkSession, 300);

        return () => { isMounted = false; };
    }, [navigate]);

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
                    <a href="/login" className="px-6 py-2 bg-orange-500 text-white rounded-lg inline-block">
                        Try Again
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900">
            <div className="text-center">
                <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-white">Completing login...</p>
            </div>
        </div>
    );
}
