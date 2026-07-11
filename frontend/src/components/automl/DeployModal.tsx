import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Rocket, Copy, CheckCheck, Code2, Globe, Server, Loader2, ArrowRight } from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import apiService, { api } from '@/services/api';

interface DeployModalProps {
    isOpen: boolean;
    onClose: () => void;
    modelName: string;
    taskType: string;
}

const DeployModal: React.FC<DeployModalProps> = ({ isOpen, onClose, modelName, taskType }) => {
    const isDark = useUserStore((state) => state.isDark);
    const [status, setStatus] = useState<'idle' | 'deploying' | 'success' | 'error'>('idle');
    const [deployment, setDeployment] = useState<any>(null);
    const [errorMsg, setErrorMsg] = useState('');
    const [copied, setCopied] = useState(false);
    const [copiedKey, setCopiedKey] = useState(false);

    // Reset when opened
    useEffect(() => {
        if (isOpen) {
            setStatus('idle');
            setDeployment(null);
            setErrorMsg('');
        }
    }, [isOpen]);

    const handleDeploy = async () => {
        setStatus('deploying');
        try {
            const userId = useUserStore.getState().user?.id || 'default';
            const res = await api.post(`/api/v1/deploy/${userId}`, {}, {
                headers: { 'X-User-ID': userId }
            });
            setDeployment(res.data.deployment);
            setStatus('success');
        } catch (err: any) {
            console.error('Deploy error:', err);
            setErrorMsg(err.response?.data?.detail || err.message || 'Failed to deploy model');
            setStatus('error');
        }
    };

    const handleCopyCode = () => {
        if (!deployment) return;
        const code = `import requests

# API Endpoint
url = "${window.location.origin}${deployment.endpoint}"

# Authentication Key
headers = {
    "X-API-Key": "${deployment.api_key}",
    "Content-Type": "application/json"
}

# Example Payload
payload = {
    "data": {
        # Add your feature columns here
        "feature_1": 0.5,
        "feature_2": 1.2
    }
}

# Make Prediction
response = requests.post(url, json=payload, headers=headers)
print(response.json())`;
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleCopyKey = () => {
        if (!deployment) return;
        navigator.clipboard.writeText(deployment.api_key);
        setCopiedKey(true);
        setTimeout(() => setCopiedKey(false), 2000);
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="w-full max-w-2xl rounded-2xl overflow-hidden border shadow-2xl"
                    style={{
                        backgroundColor: 'var(--bg-surface)',
                        borderColor: 'var(--border-color)',
                        color: 'var(--text-primary)'
                    }}
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b" style={{ borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                                <Rocket className="w-5 h-5 text-blue-500" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold">Deploy to Production</h2>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Generate a live API endpoint for {modelName}</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-xl transition-colors hover:bg-white/5"
                        >
                            <X className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-6">
                        {status === 'idle' && (
                            <div className="text-center py-8">
                                <Server className="w-16 h-16 mx-auto mb-4 text-blue-500/50" />
                                <h3 className="text-xl font-semibold mb-2">Ready for deployment</h3>
                                <p className="mb-6 max-w-md mx-auto" style={{ color: 'var(--text-secondary)' }}>
                                    We will package your trained <strong>{modelName}</strong> model into a scalable REST API.
                                    This takes less than 5 seconds and generates integration code automatically.
                                </p>
                                <button
                                    onClick={handleDeploy}
                                    className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold shadow-lg shadow-blue-500/20 transition-all hover:-translate-y-0.5 flex items-center gap-2 mx-auto"
                                >
                                    <Rocket className="w-5 h-5" />
                                    Launch Deployment
                                </button>
                            </div>
                        )}

                        {status === 'deploying' && (
                            <div className="text-center py-12">
                                <Loader2 className="w-12 h-12 mx-auto mb-4 text-blue-500 animate-spin" />
                                <h3 className="text-lg font-semibold animate-pulse">Provisioning API Endpoint...</h3>
                                <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>Packaging {modelName} for scalable inference</p>
                            </div>
                        )}

                        {status === 'error' && (
                            <div className="text-center py-8">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
                                    <X className="w-8 h-8 text-red-500" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2 text-red-400">Deployment Failed</h3>
                                <p className="mb-6" style={{ color: 'var(--text-secondary)' }}>{errorMsg}</p>
                                <button
                                    onClick={() => setStatus('idle')}
                                    className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-xl font-medium transition-colors"
                                >
                                    Try Again
                                </button>
                            </div>
                        )}

                        {status === 'success' && deployment && (
                            <div className="space-y-6">
                                <div className="p-4 rounded-xl border flex items-start gap-4" style={{ backgroundColor: 'rgba(34, 197, 94, 0.05)', borderColor: 'rgba(34, 197, 94, 0.2)' }}>
                                    <div className="p-2 bg-green-500/20 rounded-full mt-0.5">
                                        <CheckCheck className="w-5 h-5 text-green-500" />
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-green-400 mb-1">Deployment Successful</h4>
                                        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                            Your model is now live and accepting predictions.
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>API Endpoint</label>
                                        <div className="flex items-center gap-2 p-3 rounded-lg border font-mono text-sm" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <Globe className="w-4 h-4 text-blue-400" />
                                            <span className="truncate flex-1">{window.location.origin}{deployment.endpoint}</span>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>Authentication Key</label>
                                        <div className="flex items-center gap-2 p-3 rounded-lg border font-mono text-sm" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <span className="truncate flex-1 blur-sm hover:blur-none transition-all cursor-pointer select-all">{deployment.api_key}</span>
                                            <button onClick={handleCopyKey} className="p-1.5 rounded-md hover:bg-white/10 transition-colors" style={{ color: 'var(--text-muted)' }}>
                                                {copiedKey ? <CheckCheck className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Python Integration</label>
                                            <button onClick={handleCopyCode} className="text-xs flex items-center gap-1 hover:text-white transition-colors" style={{ color: 'var(--text-muted)' }}>
                                                {copied ? <CheckCheck className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                                                {copied ? 'Copied!' : 'Copy Code'}
                                            </button>
                                        </div>
                                        <pre className="p-4 rounded-lg border overflow-x-auto text-sm font-mono" style={{ backgroundColor: '#1e1e1e', borderColor: 'var(--border-color)', color: '#d4d4d4' }}>
                                            <code dangerouslySetInnerHTML={{ __html: `import requests\n\nurl = <span style="color:#ce9178">"${window.location.origin}${deployment.endpoint}"</span>\n\nheaders = {\n    <span style="color:#ce9178">"X-API-Key"</span>: <span style="color:#ce9178">"${deployment.api_key}"</span>,\n    <span style="color:#ce9178">"Content-Type"</span>: <span style="color:#ce9178">"application/json"</span>\n}\n\npayload = {\n    <span style="color:#ce9178">"data"</span>: {\n        <span style="color:#6a9955"># Add your features here</span>\n    }\n}\n\nresponse = requests.post(url, json=payload, headers=headers)\n<span style="color:#569cd6">print</span>(response.json())` }} />
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                    
                    {/* Footer */}
                    {status === 'success' && (
                        <div className="p-4 border-t flex justify-end bg-black/10" style={{ borderColor: 'var(--border-color)' }}>
                            <button
                                onClick={onClose}
                                className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors"
                            >
                                Done
                            </button>
                        </div>
                    )}
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

export default DeployModal;
