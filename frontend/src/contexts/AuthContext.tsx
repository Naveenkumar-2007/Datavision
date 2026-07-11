/**
 * Auth Context - PRODUCTION READY
 * Provides auth state throughout the app
 */

import { createContext, useContext, useEffect, useState, ReactNode, useMemo } from 'react';
import { supabase, auth } from '../lib/auth-client';

export interface User {
    id: string;
    email?: string;
    user_metadata?: any;
    app_metadata?: any;
    [key: string]: any;
}

export interface Session {
    access_token: string;
    refresh_token?: string;
    expires_in?: number;
    expires_at?: number;
    token_type?: string;
    user: User;
}

interface AuthState {
    user: User | null;
    session: Session | null;
    loading: boolean;
    isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
    signUp: (email: string, password: string, metadata?: Record<string, any>) => Promise<any>;
    signIn: (email: string, password: string) => Promise<any>;
    signInWithMagicLink: (email: string) => Promise<any>;
    signInWithGoogle: () => Promise<any>;
    signInWithGithub: () => Promise<any>;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<AuthState>({
        user: null,
        session: null,
        loading: true,
        isAuthenticated: false
    });

    useEffect(() => {
        let isMounted = true;

        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }) => {
            if (!isMounted) return;

            if (session) {
                setState({
                    user: session.user,
                    session,
                    loading: false,
                    isAuthenticated: true
                });
                localStorage.setItem('userId', session.user.id);
            } else {
                setState(s => ({ ...s, loading: false }));
            }
        });

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            if (!isMounted) return;

            if (session) {
                setState({
                    user: session.user,
                    session,
                    loading: false,
                    isAuthenticated: true
                });
                localStorage.setItem('userId', session.user.id);
            } else {
                setState({
                    user: null,
                    session: null,
                    loading: false,
                    isAuthenticated: false
                });
                localStorage.removeItem('userId');
            }
        });

        // Timeout
        setTimeout(() => {
            if (isMounted) {
                setState(s => s.loading ? { ...s, loading: false } : s);
            }
        }, 2000);

        return () => {
            isMounted = false;
            subscription.unsubscribe();
        };
    }, []);

    const updateAuthState = async () => {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
            setState({
                user: session.user,
                session,
                loading: false,
                isAuthenticated: true
            });
            localStorage.setItem('userId', session.user.id);
        }
    };

    const signUp = async (email: string, password: string, metadata?: Record<string, any>) => {
        const result = await auth.signUp(email, password, metadata);
        if (!result.error) await updateAuthState();
        return { error: result.error };
    };

    const signIn = async (email: string, password: string) => {
        const result = await auth.signIn(email, password);
        if (!result.error) await updateAuthState();
        return { error: result.error };
    };

    const signInWithMagicLink = async (email: string) => {
        const result = await auth.signInWithMagicLink(email);
        return { error: result.error };
    };

    const signInWithGoogle = async () => {
        const result = await auth.signInWithOAuth('google');
        return { error: result.error };
    };

    const signInWithGithub = async () => {
        const result = await auth.signInWithOAuth('github');
        return { error: result.error };
    };

    const signOut = async () => {
        try {
            // Sign out from auth service
            await auth.signOut();
        } catch (error) {
            console.error('Sign out error:', error);
        }

        // Clear all user-related localStorage
        localStorage.removeItem('userId');
        localStorage.removeItem('ai-analyst-storage-v2'); // Zustand store

        // Clear any user profile data
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith('userProfile_') || key.startsWith('userPreferences_')) {
                localStorage.removeItem(key);
            }
        });

        // Clear session - force clear any auth storage
        const authKeys = keys.filter(key =>
            key.startsWith('sb-') ||
            key.includes('auth')
        );
        authKeys.forEach(key => localStorage.removeItem(key));

        // Redirect to landing page
        window.location.href = '/';
    };

    const value = useMemo(() => ({
        ...state,
        signUp,
        signIn,
        signInWithMagicLink,
        signInWithGoogle,
        signInWithGithub,
        signOut
    }), [state]);

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}

export default AuthContext;
