import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect, useRef, useMemo } from 'react';
import { X, CheckCircle, AlertTriangle, Info, AlertCircle, Trash2 } from 'lucide-react';

// Toast Types
export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'delete';

export interface Toast {
    id: string;
    type: ToastType;
    message: string;
    description?: string;
    duration?: number;
}

interface ToastContextType {
    toasts: Toast[];
    showToast: (type: ToastType, message: string, description?: string, duration?: number) => void;
    removeToast: (id: string) => void;
    success: (message: string, description?: string) => void;
    error: (message: string, description?: string) => void;
    warning: (message: string, description?: string) => void;
    info: (message: string, description?: string) => void;
    deleted: (message: string, description?: string) => void;
    addToast: (type: string, title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
};

// Toast Component - DataVision Styled (Stable - No Blinking)
const ToastItem = React.memo(({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) => {
    const [animationState, setAnimationState] = useState<'entering' | 'visible' | 'exiting'>('entering');
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isMountedRef = useRef(true);

    useEffect(() => {
        isMountedRef.current = true;
        
        // Enter animation - use requestAnimationFrame for smoother transition
        requestAnimationFrame(() => {
            if (isMountedRef.current) {
                setAnimationState('visible');
            }
        });
        
        // Auto-remove after duration
        if (toast.duration && toast.duration > 0) {
            timerRef.current = setTimeout(() => {
                if (isMountedRef.current) {
                    setAnimationState('exiting');
                    setTimeout(() => {
                        if (isMountedRef.current) {
                            onRemove(toast.id);
                        }
                    }, 200);
                }
            }, toast.duration);
        }

        return () => {
            isMountedRef.current = false;
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, []); // Empty deps - only run on mount

    const handleRemove = useCallback(() => {
        if (timerRef.current) clearTimeout(timerRef.current);
        setAnimationState('exiting');
        setTimeout(() => onRemove(toast.id), 200);
    }, [toast.id, onRemove]);

    const configs = {
        success: {
            icon: <CheckCircle className="w-5 h-5" />,
            bg: 'bg-emerald-500/10',
            border: 'border-emerald-500/30',
            iconColor: 'text-emerald-400',
        },
        error: {
            icon: <AlertCircle className="w-5 h-5" />,
            bg: 'bg-red-500/10',
            border: 'border-red-500/30',
            iconColor: 'text-red-400',
        },
        warning: {
            icon: <AlertTriangle className="w-5 h-5" />,
            bg: 'bg-amber-500/10',
            border: 'border-amber-500/30',
            iconColor: 'text-amber-400',
        },
        info: {
            icon: <Info className="w-5 h-5" />,
            bg: 'bg-blue-500/10',
            border: 'border-blue-500/30',
            iconColor: 'text-blue-400',
        },
        delete: {
            icon: <Trash2 className="w-5 h-5" />,
            bg: 'bg-red-500/10',
            border: 'border-red-500/30',
            iconColor: 'text-red-400',
        },
    };

    const config = configs[toast.type];

    const getAnimationClasses = () => {
        switch (animationState) {
            case 'entering':
                return 'opacity-0 translate-y-4 scale-95';
            case 'exiting':
                return 'opacity-0 translate-x-8 scale-95';
            default:
                return 'opacity-100 translate-y-0 translate-x-0 scale-100';
        }
    };

    return (
        <div
            className={`
                flex items-start gap-3 p-4 rounded-xl border 
                backdrop-blur-xl shadow-lg w-full max-w-sm pointer-events-auto
                ${config.bg} ${config.border} bg-[var(--bg-card)]/95
                transition-all duration-200 ease-out
                ${getAnimationClasses()}
            `}
        >
            <div className={`flex-shrink-0 mt-0.5 ${config.iconColor}`}>
                {config.icon}
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
                    {toast.message}
                </p>
                {toast.description && (
                    <p className="mt-1 text-xs text-[var(--text-secondary)] line-clamp-2">
                        {toast.description}
                    </p>
                )}
            </div>
            <button
                onClick={handleRemove}
                type="button"
                className="flex-shrink-0 p-1.5 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
});

ToastItem.displayName = 'ToastItem';

export const ToastProvider = ({ children }: { children: ReactNode }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);
    const toastIdCounter = useRef(0);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const showToast = useCallback((type: ToastType, message: string, description?: string, duration = 5000) => {
        const id = `toast-${++toastIdCounter.current}-${Date.now()}`;
        const newToast: Toast = { id, type, message, description, duration };
        setToasts((prev) => [...prev, newToast]);
    }, []);

    const success = useCallback((message: string, description?: string) => showToast('success', message, description), [showToast]);
    const error = useCallback((message: string, description?: string) => showToast('error', message, description), [showToast]);
    const warning = useCallback((message: string, description?: string) => showToast('warning', message, description), [showToast]);
    const info = useCallback((message: string, description?: string) => showToast('info', message, description), [showToast]);
    const deleted = useCallback((message: string, description?: string) => showToast('delete', message, description, 4000), [showToast]);
    const addToast = useCallback((type: string, title: string, message?: string) => showToast((type as ToastType) || 'info', title, message), [showToast]);

    const contextValue = useMemo(() => ({
        toasts,
        showToast,
        removeToast,
        success,
        error,
        warning,
        info,
        deleted,
        addToast
    }), [toasts, showToast, removeToast, success, error, warning, info, deleted, addToast]);

    return (
        <ToastContext.Provider value={contextValue}>
            {children}
            {/* Toast Container - Bottom Right with DataVision styling */}
            <div className="fixed bottom-0 right-0 z-[9998] p-4 sm:p-6 w-full max-w-sm flex flex-col gap-3 pointer-events-none">
                {toasts.map((toast) => (
                    <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
                ))}
            </div>
        </ToastContext.Provider>
    );
};
