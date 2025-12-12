/**
 * Login Page
 * Supports email/password, magic link, and OAuth login
 * THEME: Supports both light and dark mode
 */

import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
    const navigate = useNavigate();
    const location = useLocation();
    const { signIn, signInWithMagicLink, signInWithGoogle, signInWithGithub } = useAuth();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [magicLinkSent, setMagicLinkSent] = useState(false);
    const [loginMethod, setLoginMethod] = useState<'password' | 'magic-link'>('password');

    // Get redirect path from location state
    const from = (location.state as any)?.from?.pathname || '/overview';

    const handlePasswordLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const { error } = await signIn(email, password);

            if (error) {
                // Handle specific error for email not confirmed
                if (error.message?.toLowerCase().includes('email not confirmed')) {
                    setError('Please confirm your email first. Check your inbox for a confirmation link, or click "Use Magic Link" to get a new login link.');
                } else if (error.message?.toLowerCase().includes('invalid login credentials')) {
                    setError('Invalid email or password. Please try again.');
                } else {
                    setError(error.message || 'Login failed');
                }
            } else {
                navigate(from, { replace: true });
            }
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleMagicLink = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const { error } = await signInWithMagicLink(email);

            if (error) {
                setError(error.message || 'Failed to send magic link');
            } else {
                setMagicLinkSent(true);
            }
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        setLoading(true);
        setError('');

        try {
            const { error } = await signInWithGoogle();
            if (error) {
                setError(error.message || 'Google login failed');
            }
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleGithubLogin = async () => {
        setLoading(true);
        setError('');

        try {
            const { error } = await signInWithGithub();
            if (error) {
                setError(error.message || 'GitHub login failed');
            }
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    if (magicLinkSent) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 
                bg-gradient-to-br from-gray-50 to-gray-100 
                dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
                <div className="max-w-md w-full rounded-2xl p-8 text-center
                    bg-white border border-gray-200 shadow-xl
                    dark:bg-gray-800/50 dark:backdrop-blur-xl dark:border-gray-700/50">
                    <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white">Check your email</h2>
                    <p className="mb-6 text-gray-600 dark:text-gray-400">
                        We've sent a magic link to <span className="text-orange-500 dark:text-orange-400">{email}</span>.
                        Click the link in your email to sign in.
                    </p>
                    <button
                        onClick={() => setMagicLinkSent(false)}
                        className="text-orange-500 hover:text-orange-600 dark:text-orange-400 dark:hover:text-orange-300 transition-colors"
                    >
                        ← Back to login
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4
            bg-gradient-to-br from-gray-50 to-gray-100 
            dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
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

                {/* Login Card */}
                <div className="rounded-2xl p-8 shadow-2xl
                    bg-white border border-gray-200
                    dark:bg-gray-800/50 dark:backdrop-blur-xl dark:border-gray-700/50">
                    <h2 className="text-2xl font-bold text-center mb-2 text-gray-900 dark:text-white">Welcome back</h2>
                    <p className="text-center mb-8 text-gray-600 dark:text-gray-400">Sign in to continue to your dashboard</p>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 dark:bg-red-500/10 dark:border-red-500/50 rounded-lg">
                            <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    {/* Login Method Toggle */}
                    <div className="flex gap-2 mb-6 p-1 rounded-lg bg-gray-100 dark:bg-gray-700/50">
                        <button
                            onClick={() => setLoginMethod('password')}
                            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${loginMethod === 'password'
                                ? 'bg-orange-500 text-white'
                                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
                                }`}
                        >
                            Password
                        </button>
                        <button
                            onClick={() => setLoginMethod('magic-link')}
                            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${loginMethod === 'magic-link'
                                ? 'bg-orange-500 text-white'
                                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
                                }`}
                        >
                            Magic Link
                        </button>
                    </div>

                    {/* Login Form */}
                    <form onSubmit={loginMethod === 'password' ? handlePasswordLogin : handleMagicLink}>
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
                                    className="w-full px-4 py-3 rounded-lg transition-all
                                        bg-gray-50 border border-gray-300 text-gray-900 placeholder-gray-400
                                        dark:bg-gray-700/50 dark:border-gray-600 dark:text-white dark:placeholder-gray-400
                                        focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                                    placeholder="you@example.com"
                                />
                            </div>

                            {loginMethod === 'password' && (
                                <div>
                                    <label htmlFor="password" className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                                        Password
                                    </label>
                                    <input
                                        id="password"
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        className="w-full px-4 py-3 rounded-lg transition-all
                                            bg-gray-50 border border-gray-300 text-gray-900 placeholder-gray-400
                                            dark:bg-gray-700/50 dark:border-gray-600 dark:text-white dark:placeholder-gray-400
                                            focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                                        placeholder="••••••••"
                                    />
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-semibold rounded-lg hover:from-orange-600 hover:to-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Signing in...
                                    </span>
                                ) : loginMethod === 'password' ? (
                                    'Sign in'
                                ) : (
                                    'Send Magic Link'
                                )}
                            </button>
                        </div>
                    </form>

                    {/* Divider */}
                    <div className="relative my-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-200 dark:border-gray-700"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-4 bg-white dark:bg-gray-800/50 text-gray-500 dark:text-gray-400">Or continue with</span>
                        </div>
                    </div>

                    {/* OAuth Buttons */}
                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={handleGoogleLogin}
                            disabled={loading}
                            className="flex items-center justify-center gap-2 py-3 px-4 font-medium rounded-lg transition-all disabled:opacity-50
                                bg-white border border-gray-300 text-gray-800 hover:bg-gray-50
                                dark:bg-white dark:text-gray-800 dark:hover:bg-gray-100"
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
                            onClick={handleGithubLogin}
                            disabled={loading}
                            className="flex items-center justify-center gap-2 py-3 px-4 font-medium rounded-lg transition-all disabled:opacity-50
                                bg-gray-100 border border-gray-300 text-gray-900 hover:bg-gray-200
                                dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:hover:bg-gray-600"
                        >
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                            </svg>
                            GitHub
                        </button>
                    </div>

                    {/* Forgot Password */}
                    {loginMethod === 'password' && (
                        <div className="mt-4 text-center">
                            <Link to="/forgot-password" className="text-sm text-orange-500 hover:text-orange-600 dark:text-orange-400 dark:hover:text-orange-300 transition-colors">
                                Forgot your password?
                            </Link>
                        </div>
                    )}

                    {/* Sign Up Link */}
                    <div className="mt-6 text-center">
                        <p className="text-gray-600 dark:text-gray-400">
                            Don't have an account?{' '}
                            <Link to="/signup" className="text-orange-500 hover:text-orange-600 dark:text-orange-400 dark:hover:text-orange-300 font-medium transition-colors">
                                Sign up
                            </Link>
                        </p>
                    </div>
                </div>

                {/* Back to Home */}
                <div className="mt-6 text-center">
                    <Link to="/" className="text-gray-500 hover:text-gray-700 dark:text-gray-500 dark:hover:text-gray-400 text-sm transition-colors">
                        ← Back to home
                    </Link>
                </div>
            </div>
        </div>
    );
}
