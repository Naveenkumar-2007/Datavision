import React, { useEffect, useRef } from 'react';
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
    const [typedValue, setTypedValue] = React.useState('');
    const [isVisible, setIsVisible] = React.useState(false);
    const modalRef = useRef<HTMLDivElement>(null);
    const config = variantConfig[variant];
    const IconComponent = config.icon;

    const canConfirm = requireTypedConfirmation 
        ? typedValue.toUpperCase() === requireTypedConfirmation.toUpperCase()
        : true;

    // Handle open/close with CSS transitions
    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
            document.body.style.overflow = 'hidden';
        } else {
            const timer = setTimeout(() => setIsVisible(false), 200);
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
            if (e.key === 'Escape' && !isLoading) {
                handleClose();
            }
        };
        if (isOpen) {
            window.addEventListener('keydown', handleKeyDown);
            return () => window.removeEventListener('keydown', handleKeyDown);
        }
    }, [isOpen, isLoading]);

    const handleConfirm = () => {
        if (canConfirm && !isLoading) {
            onConfirm();
            setTypedValue('');
        }
    };

    const handleClose = () => {
        if (!isLoading) {
            onClose();
            setTypedValue('');
        }
    };

    const handleBackdropClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget && !isLoading) {
            handleClose();
        }
    };

    if (!isVisible) return null;

    return (
        <div 
            className={`
                fixed inset-0 z-[9999] flex items-center justify-center p-4
                transition-opacity duration-200 ease-out
                ${isOpen ? 'opacity-100' : 'opacity-0'}
            `}
            onClick={handleBackdropClick}
        >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

            {/* Modal */}
            <div 
                ref={modalRef}
                className={`
                    relative z-10 w-full max-w-md
                    transition-all duration-200 ease-out
                    ${isOpen ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}
                `}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="rounded-2xl border shadow-2xl overflow-hidden bg-[var(--bg-card)] border-[var(--border-color)]">
                    {/* Header */}
                    <div className="relative p-6 pb-4">
                        <button
                            onClick={handleClose}
                            disabled={isLoading}
                            className="absolute top-4 right-4 p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>

                        <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-xl ${config.iconBg} ${config.borderColor} border`}>
                                {icon ? (
                                    <div className={config.iconColor}>{icon}</div>
                                ) : (
                                    <IconComponent className={`w-6 h-6 ${config.iconColor}`} />
                                )}
                            </div>
                            <div className="flex-1 min-w-0 pt-1">
                                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                                    {title}
                                </h3>
                                <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
                                    {message}
                                </p>
                            </div>
                        </div>

                        {/* Typed Confirmation Input */}
                        {requireTypedConfirmation && (
                            <div className="mt-4 ml-16">
                                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
                                    Type <span className="font-bold text-[var(--text-primary)]">{requireTypedConfirmation}</span> to confirm
                                </label>
                                <input
                                    type="text"
                                    value={typedValue}
                                    onChange={(e) => setTypedValue(e.target.value)}
                                    placeholder={requireTypedConfirmation}
                                    disabled={isLoading}
                                    className="w-full px-4 py-2.5 rounded-xl border text-sm bg-[var(--bg-primary)] border-[var(--border-color)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--text-secondary)] transition-colors"
                                    autoFocus
                                />
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 p-6 pt-4 border-t border-[var(--border-color)] bg-[var(--bg-secondary)]">
                        <button
                            onClick={handleClose}
                            disabled={isLoading}
                            className="flex-1 px-4 py-2.5 rounded-xl font-medium text-sm bg-[var(--bg-hover)] text-[var(--text-primary)] hover:bg-[var(--bg-card)] transition-colors disabled:opacity-50"
                        >
                            {cancelText}
                        </button>
                        <button
                            onClick={handleConfirm}
                            disabled={isLoading || !canConfirm}
                            className={`
                                flex-1 px-4 py-2.5 rounded-xl font-medium text-sm text-white
                                ${config.buttonClass}
                                transition-colors disabled:opacity-50
                                flex items-center justify-center gap-2
                            `}
                        >
                            {isLoading ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                confirmText
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Hook for easy usage
export const useConfirmModal = () => {
    const [modalState, setModalState] = React.useState<{
        isOpen: boolean;
        config: Omit<ConfirmModalProps, 'isOpen' | 'onClose' | 'onConfirm'>;
        resolver: ((value: boolean) => void) | null;
    }>({
        isOpen: false,
        config: { title: '', message: '' },
        resolver: null,
    });

    const confirm = (config: Omit<ConfirmModalProps, 'isOpen' | 'onClose' | 'onConfirm'>): Promise<boolean> => {
        return new Promise((resolve) => {
            setModalState({
                isOpen: true,
                config,
                resolver: resolve,
            });
        });
    };

    const handleClose = () => {
        modalState.resolver?.(false);
        setModalState((prev) => ({ ...prev, isOpen: false, resolver: null }));
    };

    const handleConfirm = () => {
        modalState.resolver?.(true);
        setModalState((prev) => ({ ...prev, isOpen: false, resolver: null }));
    };

    const ConfirmModalComponent = () => (
        <ConfirmModal
            isOpen={modalState.isOpen}
            onClose={handleClose}
            onConfirm={handleConfirm}
            {...modalState.config}
        />
    );

    return { confirm, ConfirmModal: ConfirmModalComponent };
};

export default ConfirmModal;
