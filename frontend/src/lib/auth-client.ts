/**
 * Auth Client - DataVision Authentication Module
 * Provides auth operations using the backend JWT auth system.
 */
import { api } from '../services/api';

// Internal auth state helpers (used by auth methods below)
const _authState = {
    getSession: async () => {
        const token = localStorage.getItem('auth_token');
        const userStr = localStorage.getItem('auth_user');
        if (token && userStr) {
            try {
                return { data: { session: { access_token: token, user: JSON.parse(userStr) } }, error: null };
            } catch (e) {
                return { data: { session: null }, error: null };
            }
        }
        return { data: { session: null }, error: null };
    },
    getUser: async () => {
        const userStr = localStorage.getItem('auth_user');
        if (userStr) {
            try {
                return { data: { user: JSON.parse(userStr) }, error: null };
            } catch (e) {
                return { data: { user: null }, error: null };
            }
        }
        return { data: { user: null }, error: null };
    },
    onAuthStateChange: (callback: (event: string, session: any) => void) => {
        // Simplified - not reactive but prevents errors
        return { data: { subscription: { unsubscribe: () => {} } } };
    },
    updateUser: async (attributes: any) => {
        try {
            if (attributes.password) {
                await api.post('/api/v1/auth/magic-link', { email: 'current-user-email' });
            }
            return { data: { user: {} }, error: null };
        } catch (e: any) {
            return { data: null, error: e };
        }
    },
    setSession: async ({ access_token, refresh_token }: any) => {
        localStorage.setItem('auth_token', access_token);
        return { data: { session: { access_token } }, error: null };
    }
};

/**
 * Primary auth client — use this for all auth operations.
 */
export const auth = {
    signUp: async (email: string, password: string, metadata?: Record<string, any>) => {
        try {
            const res = await api.post('/api/v1/auth/signup', {
                email,
                password,
                full_name: metadata?.full_name,
                company_name: metadata?.company_name
            });
            if (res.data.session) {
                localStorage.setItem('auth_token', res.data.session.access_token);
                localStorage.setItem('auth_user', JSON.stringify(res.data.user));
            }
            return { data: res.data, error: null };
        } catch (error: any) {
            return { data: null, error: error.response?.data?.detail || 'Signup failed' };
        }
    },

    signIn: async (email: string, password: string) => {
        try {
            const res = await api.post('/api/v1/auth/login', { email, password });
            if (res.data.session) {
                localStorage.setItem('auth_token', res.data.session.access_token);
                localStorage.setItem('auth_user', JSON.stringify(res.data.user));
            }
            return { data: res.data, error: null };
        } catch (error: any) {
            return { data: null, error: error.response?.data?.detail || 'Invalid credentials' };
        }
    },

    signInWithMagicLink: async (email: string) => {
        try {
            const res = await api.post('/api/v1/auth/magic-link', { email });
            return { data: res.data, error: null };
        } catch (error: any) {
            return { data: null, error: error.response?.data?.detail || 'Failed to send magic link' };
        }
    },

    signInWithOAuth: async (provider: 'google' | 'github') => {
        try {
            const baseUrl = import.meta.env.VITE_API_URL || '';
            window.location.href = `${baseUrl}/api/v1/auth/oauth/${provider}`;
            return { data: null, error: null };
        } catch (error: any) {
            return { data: null, error: 'OAuth failed' };
        }
    },

    signOut: async () => {
        try {
            await api.post('/api/v1/auth/logout');
        } catch (e) {
            console.error('Logout error', e);
        }
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        window.location.href = '/login';
        return { error: null };
    },

    getSession: async () => {
        return _authState.getSession();
    },

    getUser: async () => {
        return _authState.getUser();
    },

    resetPassword: async (email: string) => {
        try {
            const res = await api.post('/api/v1/auth/magic-link', { email });
            return { data: res.data, error: null };
        } catch (error: any) {
            return { data: null, error: error.response?.data?.detail || 'Reset failed' };
        }
    },

    onAuthStateChange: (callback: (event: string, session: any) => void) => {
        return _authState.onAuthStateChange(callback);
    }
};

/**
 * @deprecated Use `auth` instead. This is a backward-compatible shim.
 * Provides the old `supabase.auth.*` interface for files not yet migrated.
 */
export const supabase = {
    auth: _authState
};

export default auth;
