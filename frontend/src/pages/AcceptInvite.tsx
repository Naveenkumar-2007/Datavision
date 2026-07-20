import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { motion } from 'framer-motion';
import { useUserStore } from '../store/userStore';
import { Sun, Moon } from 'lucide-react';
import { api } from '../services/api';

export default function AcceptInvite() {
    const navigate = useNavigate();
    const location = useLocation();
    const { isDark, toggleTheme } = useUserStore();
    const toast = useToast();

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    
    // Extract token and email from URL
    const params = new URLSearchParams(location.search);
    const token = params.get('token');
    const email = params.get('email');

    useEffect(() => {
        if (!token || !email) {
            setError('Invalid or missing invitation link. Please request a new invite.');
        }
    }, [token, email]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!token || !email) return;
        
        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }
        
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        
        setLoading(true);
        setError('');
        try {
            const res = await api.post('/api/v1/auth/accept-invite', {
                token,
                email,
                password
            });
            
            toast.success(res.data.message || 'Account activated successfully!');
            navigate('/login');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to accept invitation');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 transition-colors duration-300 relative overflow-hidden bg-primary text-primary">
            {/* Background Orbs for Glass Effect */}
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

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-md w-full relative z-10"
            >
                {/* Logo Section */}
                <div className="text-center mb-8">
                    <Link to="/" className="inline-flex items-center gap-3 group">
                        <div className="relative">
                            <div className="absolute inset-0 rounded-full blur-lg opacity-50 group-hover:opacity-100 transition-opacity bg-green-500/30" />
                            <img src={isDark ? '/datavision-logo-dark.jpg' : '/datavision-logo-light.jpg'} alt="DataVision" className="w-14 h-14 object-contain relative z-10 drop-shadow-lg rounded-full" onError={(e) => { (e.target as HTMLImageElement).src = '/logo.svg'; }} />
                        </div>
                        <span className="text-3xl font-bold tracking-tight">
                            <span style={{ color: 'var(--text-primary)' }}>Data</span>
                            <span className="text-emerald-500">Vision</span>
                        </span>
                    </Link>
                </div>

                {/* Accept Invite Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="p-8 md:p-10 rounded-3xl shadow-2xl glass-card backdrop-blur-xl border border-white/10"
                >
                    <div className="text-center mb-8">
                        <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                            Accept Invitation
                        </h2>
                        <p className="" style={{ color: 'var(--text-muted)' }}>
                            Set a password for <span className="font-semibold">{email}</span> to activate your account
                        </p>
                    </div>

                    {error && (
                        <div className="mb-6 p-4 rounded-xl flex items-start gap-3 bg-red-500/10 border border-red-500/20">
                            <div className="flex-1 text-sm font-medium text-red-500">{error}</div>
                        </div>
                    )}

                    {!token || !email ? (
                        <div className="text-center">
                            <Link to="/login" className="inline-flex justify-center rounded-xl text-sm font-semibold py-3 px-4 bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 w-full transition-all active:scale-95">
                                Return to Login
                            </Link>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                                    Create Password
                                </label>
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-4 py-3 rounded-xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all placeholder:text-gray-400 dark:placeholder:text-gray-500"
                                    placeholder="••••••••"
                                    minLength={8}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                                    Confirm Password
                                </label>
                                <input
                                    type="password"
                                    required
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full px-4 py-3 rounded-xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all placeholder:text-gray-400 dark:placeholder:text-gray-500"
                                    placeholder="••••••••"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className={`w-full inline-flex justify-center items-center gap-2 rounded-xl text-sm font-semibold py-3.5 px-4 bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 transition-all ${
                                    loading ? 'opacity-70 cursor-not-allowed' : 'hover:translate-y-[-2px] active:scale-95 active:translate-y-0'
                                }`}
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                ) : (
                                    'Activate Account'
                                )}
                            </button>
                            
                            <div className="text-center mt-4">
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    Already have an account?{' '}
                                    <Link to="/login" className="text-emerald-500 hover:text-emerald-400 font-medium hover:underline transition-colors">
                                        Sign In
                                    </Link>
                                </p>
                            </div>
                        </form>
                    )}
                </motion.div>
            </motion.div>
        </div>
    );
}
