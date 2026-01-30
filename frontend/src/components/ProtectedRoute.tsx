/**
 * Protected Route - PRODUCTION READY
 * Uses shared AuthContext - no independent session checks
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface Props {
    children: React.ReactNode;
    requireAdmin?: boolean;
}

export default function ProtectedRoute({ children, requireAdmin = false }: Props) {
    const location = useLocation();
    const { isAuthenticated, loading, user } = useAuth();

    // Show loading while AuthContext is checking session
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-900">
                <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    // Not authenticated - redirect to login
    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Admin check if required
    if (requireAdmin) {
        const role = user?.user_metadata?.role;
        const isAdmin = role === 'admin' || role === 'super_admin';

        if (!isAdmin) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
                    <div className="text-center">
                        <h1 className="text-2xl font-bold text-red-500 mb-4">Access Denied</h1>
                        <a href="/overview" className="text-orange-400 hover:underline">Go to Dashboard</a>
                    </div>
                </div>
            );
        }
    }

    // Authenticated - render content
    return <>{children}</>;
}
