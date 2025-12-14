/**
 * Supabase Client - PRODUCTION READY
 * DO NOT manually write to localStorage - Supabase handles this
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

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

    // 3. Fallback to Vite build-time replacement (Local Dev)
    // We MUST access these explicitly for Vite to replace them statically
    if (key === 'VITE_SUPABASE_URL') return import.meta.env.VITE_SUPABASE_URL || '';
    if (key === 'VITE_SUPABASE_ANON_KEY') return import.meta.env.VITE_SUPABASE_ANON_KEY || '';

    return '';
};

const SUPABASE_URL = getEnv('VITE_SUPABASE_URL');
const SUPABASE_ANON_KEY = getEnv('VITE_SUPABASE_ANON_KEY');

// Create Supabase client only if credentials are available
let supabase: SupabaseClient;

if (SUPABASE_URL && SUPABASE_ANON_KEY) {
    supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: true
        }
    });
    console.log('✅ Supabase client initialized');
} else {
    // Create a mock/placeholder client that won't crash
    console.warn('⚠️ Supabase credentials not configured - auth features disabled');
    supabase = createClient('https://placeholder.supabase.co', 'placeholder-key', {
        auth: {
            autoRefreshToken: false,
            persistSession: false,
            detectSessionInUrl: false
        }
    });
}

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

export { supabase };
export default supabase;
