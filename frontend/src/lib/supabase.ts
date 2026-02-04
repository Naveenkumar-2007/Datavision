/**
 * Supabase Client - PRODUCTION READY
 * DO NOT manually write to localStorage - Supabase handles this
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Vite build-time replacement - must be at module level for static replacement
const VITE_SUPABASE_URL_BUILD = import.meta.env.VITE_SUPABASE_URL || '';
const VITE_SUPABASE_ANON_KEY_BUILD = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Support runtime env injection for Docker (Hugging Face Spaces)
// AND Vite dev mode (import.meta.env)
const getEnv = (key: string): string => {
    const win = window as any;

    // 1. Check runtime injection (Docker/Production) - window._env_
    if (typeof window !== 'undefined' && win._env_ && win._env_[key]) {
        return win._env_[key];
    }

    // 2. Also check window.ENV for backwards compatibility
    if (typeof window !== 'undefined' && win.ENV && win.ENV[key]) {
        return win.ENV[key];
    }

    // 3. Fallback to Vite build-time replacement
    if (key === 'VITE_SUPABASE_URL') return VITE_SUPABASE_URL_BUILD;
    if (key === 'VITE_SUPABASE_ANON_KEY') return VITE_SUPABASE_ANON_KEY_BUILD;

    return '';
};

const SUPABASE_URL = getEnv('VITE_SUPABASE_URL');
const SUPABASE_ANON_KEY = getEnv('VITE_SUPABASE_ANON_KEY');

// Create Supabase client - credentials should be embedded at build time
let supabase: SupabaseClient;

if (SUPABASE_URL && SUPABASE_ANON_KEY && !SUPABASE_URL.includes('placeholder') && !SUPABASE_URL.includes('your-project')) {
    supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: true
        }
    });
    console.log('✅ Supabase client initialized with:', SUPABASE_URL);
} else {
    // Auth disabled - create dummy client that returns empty results
    console.warn('⚠️ Supabase not configured - running in guest mode');
    // Use a minimal mock that won't make network requests
    supabase = {
        auth: {
            getSession: async () => ({ data: { session: null }, error: null }),
            getUser: async () => ({ data: { user: null }, error: null }),
            signInWithPassword: async () => ({ data: { user: null, session: null }, error: { message: 'Auth not configured' } }),
            signUp: async () => ({ data: { user: null, session: null }, error: { message: 'Auth not configured' } }),
            signOut: async () => ({ error: null }),
            onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
            signInWithOtp: async () => ({ data: {}, error: { message: 'Auth not configured' } }),
            signInWithOAuth: async () => ({ data: { url: null, provider: '' }, error: { message: 'Auth not configured' } }),
            resetPasswordForEmail: async () => ({ data: {}, error: { message: 'Auth not configured' } }),
        }
    } as unknown as SupabaseClient;
}
// Helper to get the correct base URL for redirects
const getBaseUrl = (): string => {
    // Always use the current origin - works for any deployment
    return window.location.origin;
};

// Simple auth helpers
export const auth = {
    signUp: async (email: string, password: string, metadata?: Record<string, any>) => {
        const baseUrl = getBaseUrl();

        return supabase.auth.signUp({
            email,
            password,
            options: {
                data: metadata,
                emailRedirectTo: `${baseUrl}/login`
            }
        });
    },

    signIn: async (email: string, password: string) => {
        return supabase.auth.signInWithPassword({ email, password });
    },

    signInWithMagicLink: async (email: string) => {
        const baseUrl = getBaseUrl();
        return supabase.auth.signInWithOtp({
            email,
            options: { emailRedirectTo: `${baseUrl}/auth/callback` }
        });
    },

    signInWithOAuth: async (provider: 'google' | 'github') => {
        const baseUrl = getBaseUrl();
        return supabase.auth.signInWithOAuth({
            provider,
            options: { redirectTo: `${baseUrl}/auth/callback` }
        });
    },

    signOut: async () => {
        return supabase.auth.signOut();
    },

    getSession: async () => {
        return supabase.auth.getSession();
    },

    getUser: async () => {
        return supabase.auth.getUser();
    },

    resetPassword: async (email: string) => {
        const baseUrl = getBaseUrl();
        return supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${baseUrl}/auth/reset-password`
        });
    },

    onAuthStateChange: (callback: (event: string, session: any) => void) => {
        return supabase.auth.onAuthStateChange(callback);
    }
};

export { supabase };
export default supabase;
