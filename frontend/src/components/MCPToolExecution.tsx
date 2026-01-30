import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Loader2,
    CheckCircle2,
    XCircle,
    ChevronDown,
    ChevronUp,
    Wrench,
    Sparkles,
    Zap
} from 'lucide-react';

interface MCPToolExecutionProps {
    toolName: string;
    toolIcon?: string;
    action: string;
    status: 'pending' | 'running' | 'success' | 'error' | 'permission_required';
    progress?: number;
    details?: string[];
    result?: string;
    error?: string;
    onAllow?: () => void;
    onDeny?: () => void;
    duration?: number;
}

/**
 * Claude-style MCP Tool Execution Component
 * Shows animated tool execution with progress, details, and permission requests
 */
const MCPToolExecution: React.FC<MCPToolExecutionProps> = ({
    toolName,
    toolIcon = '🔧',
    action,
    status,
    progress = 0,
    details = [],
    result,
    error,
    onAllow,
    onDeny,
    duration
}) => {
    const [expanded, setExpanded] = useState(false);
    const [currentDetailIndex, setCurrentDetailIndex] = useState(0);

    // Animate through details when running
    useEffect(() => {
        if (status === 'running' && details.length > 1) {
            const interval = setInterval(() => {
                setCurrentDetailIndex(prev => (prev + 1) % details.length);
            }, 1500);
            return () => clearInterval(interval);
        }
    }, [status, details.length]);

    const getStatusColor = () => {
        switch (status) {
            case 'running': return 'border-green-500 bg-green-500/10';
            case 'success': return 'border-green-500 bg-green-500/10';
            case 'error': return 'border-red-500 bg-red-500/10';
            case 'permission_required': return 'border-amber-500 bg-amber-500/10';
            default: return 'border-gray-600 bg-gray-800/50';
        }
    };

    const getStatusIcon = () => {
        switch (status) {
            case 'running':
                return <Loader2 className="w-4 h-4 text-green-400 animate-spin" />;
            case 'success':
                return <CheckCircle2 className="w-4 h-4 text-green-400" />;
            case 'error':
                return <XCircle className="w-4 h-4 text-red-400" />;
            case 'permission_required':
                return <Sparkles className="w-4 h-4 text-amber-400" />;
            default:
                return <div className="w-4 h-4 rounded-full border-2 border-gray-500" />;
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className={`rounded-lg border p-3 mb-2 ${getStatusColor()} transition-all duration-300`}
        >
            {/* Header */}
            <div className="flex items-center gap-3">
                {/* Tool Icon with animation */}
                <motion.div
                    className="flex-shrink-0 w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center"
                    animate={status === 'running' ? { rotate: [0, 10, -10, 0] } : {}}
                    transition={{ repeat: Infinity, duration: 2 }}
                >
                    <span className="text-lg">{toolIcon}</span>
                </motion.div>

                {/* Main Content */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-gray-200">{toolName}</span>
                        {getStatusIcon()}
                    </div>
                    <motion.p
                        key={currentDetailIndex}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-xs text-gray-400 truncate"
                    >
                        {status === 'running' && details.length > 0
                            ? details[currentDetailIndex]
                            : action}
                    </motion.p>
                </div>

                {/* Duration/Progress */}
                {status === 'success' && duration && (
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Zap className="w-3 h-3" />
                        {(duration / 1000).toFixed(1)}s
                    </div>
                )}

                {/* Expand Button */}
                {(details.length > 0 || result) && (
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="p-1 hover:bg-gray-700 rounded transition-colors"
                    >
                        {expanded ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                    </button>
                )}
            </div>

            {/* Progress Bar */}
            {status === 'running' && (
                <motion.div
                    className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                    <motion.div
                        className="h-full bg-gradient-to-r from-green-500 to-cyan-400"
                        initial={{ width: '0%' }}
                        animate={{ width: progress > 0 ? `${progress}%` : '100%' }}
                        transition={progress > 0 ? { duration: 0.3 } : {
                            duration: 1.5,
                            repeat: Infinity,
                            ease: 'easeInOut'
                        }}
                        style={progress === 0 ? {
                            animation: 'shimmer 1.5s infinite',
                            background: 'linear-gradient(90deg, transparent, rgba(45, 212, 191, 0.5), transparent)',
                            backgroundSize: '200% 100%'
                        } : {}}
                    />
                </motion.div>
            )}

            {/* Permission Request */}
            {status === 'permission_required' && (
                <motion.div
                    className="mt-3 flex items-center gap-2"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                >
                    <button
                        onClick={onAllow}
                        className="flex-1 py-1.5 px-3 bg-green-600 hover:bg-green-500 text-white text-sm font-medium rounded-md transition-colors flex items-center justify-center gap-2"
                    >
                        <CheckCircle2 className="w-4 h-4" />
                        Allow
                    </button>
                    <button
                        onClick={onDeny}
                        className="flex-1 py-1.5 px-3 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm font-medium rounded-md transition-colors flex items-center justify-center gap-2"
                    >
                        <XCircle className="w-4 h-4" />
                        Deny
                    </button>
                </motion.div>
            )}

            {/* Expanded Details */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="mt-3 pt-3 border-t border-gray-700">
                            {/* Details List */}
                            {details.length > 0 && (
                                <div className="space-y-1 mb-2">
                                    {details.map((detail, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center gap-2 text-xs text-gray-400"
                                        >
                                            <div className={`w-1.5 h-1.5 rounded-full ${idx <= currentDetailIndex && status === 'running'
                                                    ? 'bg-green-400'
                                                    : status === 'success'
                                                        ? 'bg-green-400'
                                                        : 'bg-gray-600'
                                                }`} />
                                            {detail}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Result */}
                            {result && (
                                <div className="p-2 bg-gray-800 rounded text-xs text-gray-300 font-mono">
                                    {result}
                                </div>
                            )}

                            {/* Error */}
                            {error && (
                                <div className="p-2 bg-red-900/20 border border-red-800 rounded text-xs text-red-400">
                                    {error}
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

/**
 * MCP Tool Chain Component
 * Shows multiple tools working together in sequence
 */
interface MCPToolChainProps {
    tools: Array<{
        name: string;
        icon: string;
        status: 'pending' | 'running' | 'success' | 'error';
        action: string;
    }>;
    title?: string;
}

export const MCPToolChain: React.FC<MCPToolChainProps> = ({ tools, title }) => {
    return (
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-3 mb-3">
            {title && (
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-700">
                    <Wrench className="w-4 h-4 text-green-400" />
                    <span className="text-sm font-medium text-gray-200">{title}</span>
                </div>
            )}

            <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {tools.map((tool, idx) => (
                    <React.Fragment key={tool.name}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.1 }}
                            className={`flex-shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-full border ${tool.status === 'running'
                                    ? 'border-green-500 bg-green-500/10'
                                    : tool.status === 'success'
                                        ? 'border-green-500 bg-green-500/10'
                                        : tool.status === 'error'
                                            ? 'border-red-500 bg-red-500/10'
                                            : 'border-gray-600 bg-gray-700/50'
                                }`}
                        >
                            <span className="text-sm">{tool.icon}</span>
                            <span className="text-xs text-gray-300">{tool.name}</span>
                            {tool.status === 'running' && (
                                <Loader2 className="w-3 h-3 text-green-400 animate-spin" />
                            )}
                            {tool.status === 'success' && (
                                <CheckCircle2 className="w-3 h-3 text-green-400" />
                            )}
                        </motion.div>

                        {/* Arrow between tools */}
                        {idx < tools.length - 1 && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: idx * 0.1 + 0.05 }}
                                className="text-gray-600"
                            >
                                →
                            </motion.div>
                        )}
                    </React.Fragment>
                ))}
            </div>
        </div>
    );
};

/**
 * MCP Execution Summary
 * Shows after all tools complete
 */
interface MCPSummaryProps {
    toolsUsed: number;
    totalDuration: number;
    results: string[];
}

export const MCPExecutionSummary: React.FC<MCPSummaryProps> = ({
    toolsUsed,
    totalDuration,
    results
}) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border border-green-600/30 bg-green-900/10 p-3 mb-3"
        >
            <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                </div>
                <div>
                    <p className="text-sm font-medium text-green-400">Tools Completed</p>
                    <p className="text-xs text-gray-400">
                        {toolsUsed} tools • {(totalDuration / 1000).toFixed(1)}s total
                    </p>
                </div>
            </div>

            {results.length > 0 && (
                <div className="mt-2 pt-2 border-t border-green-800/30">
                    {results.map((r, idx) => (
                        <p key={idx} className="text-xs text-gray-400 flex items-center gap-2">
                            <span className="text-green-400">✓</span> {r}
                        </p>
                    ))}
                </div>
            )}
        </motion.div>
    );
};

export default MCPToolExecution;
