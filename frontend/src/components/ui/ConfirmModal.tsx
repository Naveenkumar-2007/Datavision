import React, { useEffect, useRef, useCallback, useState, useMemo } from 'react';
import { AlertTriangle, Trash2, X, CheckCircle, Info } from 'lucide-react';

export type ConfirmVariant = 'danger' | 'warning' | 'info' | 'success';

interface ConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    variant?: ConfirmVariant;
    isLoading?: boolean;
    requireTypedConfirmation?: string;
    icon?: React.ReactNode;
}

const variantConfig = {
    danger: {
        icon: Trash2,
        iconBg: 'bg-red-500/10',
        iconColor: 'text-red-500',
        buttonClass: 'bg-red-500 hover:bg-red-600',
        borderColor: 'border-red-500/20',
    },
    warning: {
        icon: AlertTriangle,
        iconBg: 'bg-amber-500/10',
        iconColor: 'text-amber-500',
        buttonClass: 'bg-amber-500 hover:bg-amber-600',
        borderColor: 'border-amber-500/20',
    },
    info: {
        icon: Info,
        iconBg: 'bg-blue-500/10',
        iconColor: 'text-blue-500',
        buttonClass: 'bg-blue-500 hover:bg-blue-600',
        borderColor: 'border-blue-500/20',
    },
    success: {
        icon: CheckCircle,
        iconBg: 'bg-emerald-500/10',
        iconColor: 'text-emerald-500',
        buttonClass: 'bg-emerald-500 hover:bg-emerald-600',
        borderColor: 'border-emerald-500/20',
    },
};

// Memoized Modal Content to prevent re-renders
const ConfirmModalContent = React.memo<{
    title: string;
    message: string;
    confirmText: string;
    cancelText: string;
    variant: ConfirmVariant;
    isLoading: boolean;
    requireTypedConfirmation?: string;
    icon?: React.ReactNode;
    onClose: () => void;
    onConfirm: () => void;
}>(({
    title,
    message,
    confirmText,
    cancelText,
    variant,
    isLoading,
    requireTypedConfirmation,
    icon,
    onClose,
    onConfirm,
}) => {
    const [typedValue, setTypedValue] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);
    const config = variantConfig[variant];
    const IconComponent = config.icon;

    const canConfirm = requireTypedConfirmation 
        ? typedValue.toUpperCase() === requireTypedConfirmation.toUpperCase()
        : true;

    // Focus input on mount
    useEffect(() => {
        if (requireTypedConfirmation && inputRef.current) {
            inputRef.current.focus();
        }
    }, [requireTypedConfirmation]);

    const handleConfirmClick = () => {
        if (canConfirm && !isLoading) {
            onConfirm();
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setTypedValue(e.target.value);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && canConfirm && !isLoading) {
            onConfirm();
        }
    };

    return (
        <div className="rounded-2xl border shadow-2xl overflow-hidden bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700">
            {/* Header */}
            <div className="relative p-6 pb-4">
                <button
                    onClick={onClose}
                    disabled={isLoading}
                    type="button"
                    className="absolute top-4 right-4 p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
                >
                    <X className="w-5 h-5" />
                </button>

                <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-xl ${config.iconBg} ${config.borderColor} border flex-shrink-0`}>
                        {icon ? (
                            <div className={config.iconColor}>{icon}</div>
                        ) : (
                            <IconComponent className={`w-6 h-6 ${config.iconColor}`} />
                        )}
                    </div>
                    <div className="flex-1 min-w-0 pt-1 pr-8">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            {title}
                        </h3>
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                            {message}
                        </p>
                    </div>
                </div>

                {/* Typed Confirmation Input */}
                {requireTypedConfirmation && (
                    <div className="mt-4 ml-16">
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                            Type <span className="font-bold text-gray-900 dark:text-white">{requireTypedConfirmation}</span> to confirm
                        </label>
                        <input
                            ref={inputRef}
                            type="text"
                            value={typedValue}
                            onChange={handleInputChange}
                            onKeyDown={handleKeyDown}
                            placeholder={requireTypedConfirmation}
                            disabled={isLoading}
                            autoComplete="off"
                            spellCheck={false}
                            className="w-full px-4 py-2.5 rounded-xl border text-sm bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors disabled:opacity-50"
                        />
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 p-6 pt-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                <button
                    onClick={onClose}
                    disabled={isLoading}
                    type="button"
                    className="flex-1 px-4 py-2.5 rounded-xl font-medium text-sm bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                    {cancelText}
                </button>
                <button
                    onClick={handleConfirmClick}
                    disabled={isLoading || !canConfirm}
                    type="button"
                    className={`
                        flex-1 px-4 py-2.5 rounded-xl font-medium text-sm text-white
                        ${config.buttonClass}
                        transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                        flex items-center justify-center gap-2
                    `}
                >
                    {isLoading ? (
                        <>
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            <span>Processing...</span>
                        </>
                    ) : (
                        confirmText
                    )}
                </button>
            </div>
        </div>
    );
});

ConfirmModalContent.displayName = 'ConfirmModalContent';

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'danger',
    isLoading = false,
    requireTypedConfirmation,
    icon,
}) => {
    const [isVisible, setIsVisible] = useState(false);
    const [isAnimating, setIsAnimating] = useState(false);

    // Handle open/close with CSS transitions
    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
            // Small delay to trigger animation
            requestAnimationFrame(() => {
                setIsAnimating(true);
            });
            document.body.style.overflow = 'hidden';
        } else {
            setIsAnimating(false);
            const timer = setTimeout(() => {
                setIsVisible(false);
            }, 200);
            document.body.style.overflow = '';
            return () => clearTimeout(timer);
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    // Handle escape key
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && !isLoading && isOpen) {
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, isLoading, onClose]);

    const handleBackdropClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget && !isLoading) {
            onClose();
        }
    };

    if (!isVisible) return null;

    return (
        <div 
            className={`
                fixed inset-0 z-[9999] flex items-center justify-center p-4
                transition-opacity duration-200 ease-out
                ${isAnimating ? 'opacity-100' : 'opacity-0'}
            `}
            onClick={handleBackdropClick}
        >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

            {/* Modal */}
            <div 
                className={`
                    relative z-10 w-full max-w-md
                    transition-all duration-200 ease-out
                    ${isAnimating ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-4'}
                `}
                onClick={(e) => e.stopPropagation()}
            >
                <ConfirmModalContent
                    title={title}
                    message={message}
                    confirmText={confirmText}
                    cancelText={cancelText}
                    variant={variant}
                    isLoading={isLoading}
                    requireTypedConfirmation={requireTypedConfirmation}
                    icon={icon}
                    onClose={onClose}
                    onConfirm={onConfirm}
                />
            </div>
        </div>
    );
};

// Stable hook for confirm modal
interface ModalConfig {
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    variant?: ConfirmVariant;
    requireTypedConfirmation?: string;
    icon?: React.ReactNode;
}

export const useConfirmModal = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [config, setConfig] = useState<ModalConfig>({ title: '', message: '' });
    const resolverRef = useRef<((value: boolean) => void) | null>(null);

    const confirm = useCallback((newConfig: ModalConfig): Promise<boolean> => {
        return new Promise((resolve) => {
            resolverRef.current = resolve;
            setConfig(newConfig);
            setIsOpen(true);
        });
    }, []);

    const handleClose = useCallback(() => {
        setIsOpen(false);
        // Delay resolver call to allow animation
        setTimeout(() => {
            if (resolverRef.current) {
                resolverRef.current(false);
                resolverRef.current = null;
            }
        }, 50);
    }, []);

    const handleConfirm = useCallback(() => {
        setIsOpen(false);
        // Delay resolver call to allow animation
        setTimeout(() => {
            if (resolverRef.current) {
                resolverRef.current(true);
                resolverRef.current = null;
            }
        }, 50);
    }, []);

    // Stable modal component
    const ConfirmModalComponent = useMemo(() => {
        const Modal = () => (
            <ConfirmModal
                isOpen={isOpen}
                onClose={handleClose}
                onConfirm={handleConfirm}
                title={config.title}
                message={config.message}
                confirmText={config.confirmText}
                cancelText={config.cancelText}
                variant={config.variant}
                requireTypedConfirmation={config.requireTypedConfirmation}
                icon={config.icon}
            />
        );
        return Modal;
    }, [isOpen, config, handleClose, handleConfirm]);

    return { confirm, ConfirmModal: ConfirmModalComponent };
};

export default ConfirmModal;
