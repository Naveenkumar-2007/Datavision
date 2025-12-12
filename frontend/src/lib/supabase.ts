/**
 * Supabase Client - PRODUCTION READY
 * DO NOT manually write to localStorage - Supabase handles this
 */

import { createClient } from '@supabase/supabase-js';

// Support runtime env injection for Docker (Hugging Face Spaces)
// AND Vite dev mode (import.meta.env)
const getEnv = (key: string) => {
    // 1. Check runtime injection (Docker/Production)
    if (typeof window !== 'undefined' && window._env_ && window._env_[key]) {
        return window._env_[key];
    }

    // 2. Fallback to Vite build-time replacement (Local Dev)
    // We MUST access these explicitly for Vite to replace them statically
    if (key === 'VITE_SUPABASE_URL') return import.meta.env.VITE_SUPABASE_URL;
    if (key === 'VITE_SUPABASE_ANON_KEY') return import.meta.env.VITE_SUPABASE_ANON_KEY;

    return '';
};

const SUPABASE_URL = getEnv('VITE_SUPABASE_URL');
const SUPABASE_ANON_KEY = getEnv('VITE_SUPABASE_ANON_KEY');

// Create Supabase client - handles all session storage automatically
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true
    }
});

// Simple auth helpers
export const auth = {
    signUp: async (email: string, password: string, metadata?: Record<string, any>) => {
        return supabase.auth.signUp({
            email,
            password,
            options: { data: metadata }
        });
    },

    signIn: async (email: string, password: string) => {
        return supabase.auth.signInWithPassword({ email, password });
    },

    signInWithMagicLink: async (email: string) => {
        return supabase.auth.signInWithOtp({
            email,
            options: { emailRedirectTo: `${window.location.origin}/auth/callback` }
        });
    },

    signInWithOAuth: async (provider: 'google' | 'github') => {
        return supabase.auth.signInWithOAuth({
            provider,
            options: { redirectTo: `${window.location.origin}/auth/callback` }
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
        return supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/auth/reset-password`
        });
    },

    onAuthStateChange: (callback: (event: string, session: any) => void) => {
        return supabase.auth.onAuthStateChange(callback);
    }
};

export default supabase;
