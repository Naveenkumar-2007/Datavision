/**
 * Forgot Password Page
 * Allows users to request a password reset email
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function ForgotPassword() {
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
            // Use Supabase directly or via auth helper
            const { error } = await supabase.auth.resetPasswordForEmail(email, {
                redirectTo: `${window.location.origin}/auth/update-password`,
            });

            if (error) {
                // Rate limit or other error
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
            <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
                <div className="max-w-md w-full rounded-2xl p-8 text-center bg-white border border-gray-200 shadow-xl dark:bg-gray-800/50 dark:backdrop-blur-xl dark:border-gray-700/50">
                    <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg className="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white">Check your email</h2>
                    <p className="mb-6 text-gray-600 dark:text-gray-400">
                        {message}
                    </p>
                    <Link
                        to="/login"
                        className="text-orange-500 hover:text-orange-600 dark:text-orange-400 dark:hover:text-orange-300 transition-colors"
                    >
                        ← Back to login
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
            <div className="max-w-md w-full">
                {/* Logo/Brand */}
                <div className="text-center mb-8">
                    <Link to="/" className="inline-flex items-center gap-2">
                        <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
                            <span className="text-white font-bold text-xl">AI</span>
                        </div>
                        <span className="text-2xl font-bold text-gray-900 dark:text-white">Business Analyst</span>
                    </Link>
                </div>

                {/* Card */}
                <div className="rounded-2xl p-8 shadow-2xl bg-white border border-gray-200 dark:bg-gray-800/50 dark:backdrop-blur-xl dark:border-gray-700/50">
                    <h2 className="text-2xl font-bold text-center mb-2 text-gray-900 dark:text-white">Reset Password</h2>
                    <p className="text-center mb-8 text-gray-600 dark:text-gray-400">
                        Enter your email to receive a password reset link
                    </p>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 dark:bg-red-500/10 dark:border-red-500/50">
                            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="space-y-4">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                                    Email
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full px-4 py-3 rounded-lg transition-all bg-gray-50 border border-gray-300 text-gray-900 placeholder-gray-400 dark:bg-gray-700/50 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                                    placeholder="you@example.com"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-semibold rounded-lg hover:from-orange-600 hover:to-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Sending...' : 'Send Reset Link'}
                            </button>
                        </div>
                    </form>

                    <div className="mt-6 text-center">
                        <Link to="/login" className="text-gray-500 hover:text-gray-700 dark:text-gray-500 dark:hover:text-gray-400 text-sm transition-colors">
                            ← Back to login
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
