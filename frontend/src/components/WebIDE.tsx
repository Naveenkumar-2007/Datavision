import React, { useState, useEffect, useRef, Component, ErrorInfo, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

class WebIDEErrorBoundary extends Component<{children: ReactNode}, {hasError: boolean, error: Error | null}> {
    constructor(props: {children: ReactNode}) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }
    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("WebIDE Error:", error, errorInfo);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div className="fixed inset-0 z-[9999] bg-black text-red-500 p-10 flex flex-col font-mono">
                    <h1 className="text-2xl font-bold mb-4">WebIDE Crashed</h1>
                    <pre className="whitespace-pre-wrap">{this.state.error?.toString()}</pre>
                    <pre className="whitespace-pre-wrap mt-4">{this.state.error?.stack}</pre>
                    <button onClick={() => window.location.reload()} className="mt-8 px-4 py-2 bg-red-600 text-white rounded w-fit">Reload Page</button>
                </div>
            );
        }
        return this.props.children;
    }
}
import Editor from '@monaco-editor/react';
import { 
    Play, Square, MessageSquare, Terminal as TerminalIcon, Loader2, Send, 
    FileCode2, Folder, FolderOpen, ExternalLink, Files, Search, GitBranch, PlaySquare, 
    Blocks, Settings, UserCircle, ChevronDown, ChevronRight, Plus, Trash2, X, MoreHorizontal, Check, Download, Edit3, FilePlus, ImagePlus, Mic
} from 'lucide-react';
import { api } from '../services/api';
import { getUserIdSync } from '../utils/userId';

// Memoize editor options to prevent re-renders
const EDITOR_OPTIONS = { 
    minimap: { enabled: true, scale: 2 }, 
    fontSize: 14, 
    fontFamily: "'Consolas', 'Courier New', monospace", 
    scrollBeyondLastLine: false, 
    padding: { top: 16 }, 
    wordWrap: 'on' as const, 
    bracketPairColorization: { enabled: true } 
};

interface WebIDEProps {
    initialFiles: Record<string, string>;
    onClose?: () => void;
}

const VSCodeIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" className="w-5 h-5">
        <path fill="#0065A9" d="M188.8 11.5l61.5 43.5c2.3 1.6 3.7 4.3 3.7 7.1v131.8c0 2.8-1.4 5.5-3.7 7.1l-61.5 43.5c-4.4 3.1-10.4 2.5-14.1-1.3l-67.9-67.9-49.9 41.9c-2.4 2-5.9 2-8.3 0l-45.7-38C.9 177.3 0 174.6 0 171.7V84.3c0-2.9.9-5.6 2.9-7.5l45.7-38c2.4-2 5.9-2 8.3 0l49.9 41.9 67.9-67.9c4.4-3.1 10.4-2.5 14.1 1.3z"/>
        <path fill="#007ACC" d="M189 11.7c-4.4-3.1-10.4-2.5-14.1 1.3l-67.9 67.9-49.9-41.9c-2.4-2-5.9-2-8.3 0l-45.7 38C.9 78.9 0 81.6 0 84.5v87c0 2.9.9 5.6 2.9 7.5l45.7 38c2.4 2 5.9 2 8.3 0l49.9-41.9 67.9 67.9c3.7 3.8 9.7 4.4 14.1 1.3l61.5-43.5c2.3-1.6 3.7-4.3 3.7-7.1V62.1c0-2.8-1.4-5.5-3.7-7.1L189 11.7z"/>
        <path fill="#1F9CF0" d="M174.8 244.5L107 176.7l43.2-36.2 39.5 39.4c1.2 1.2 3.1 1.2 4.3 0l49.4-49.3c.7-.7.7-1.7 0-2.4l-49.4-49.3c-1.2-1.2-3.1-1.2-4.3 0l-39.5 39.4-43.2-36.2 67.9-67.9c3.7-3.8 9.7-4.4 14.1-1.3l61.5 43.5c2.3 1.6 3.7 4.3 3.7 7.1v131.8c0 2.8-1.4 5.5-3.7 7.1l-61.5 43.5c-3.6 3.8-9.6 4.4-14.1 1.3z"/>
    </svg>
);

const CursorIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" className="w-5 h-5">
        <polygon points="50,10 90,30 90,70 50,90 10,70 10,30" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeWidth="4" />
        <polygon points="50,10 90,30 50,55 10,30" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="4" />
        <polygon points="10,30 50,55 50,90 10,70" fill="currentColor" fillOpacity="0.3" stroke="currentColor" strokeWidth="4" />
        <polygon points="90,30 50,55 50,90 90,70" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeWidth="4" />
    </svg>
);

const AntigravityIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" className="w-6 h-6">
        <defs>
            <linearGradient id="agGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4ADE80" />
                <stop offset="50%" stopColor="#3B82F6" />
                <stop offset="100%" stopColor="#EC4899" />
            </linearGradient>
        </defs>
        <path fill="url(#agGrad)" d="M50 160 Q80 130 100 60 Q120 130 150 160 Q130 140 100 140 Q70 140 50 160 Z" />
    </svg>
);

export const WebIDE: React.FC<WebIDEProps> = ({ initialFiles, onClose }) => {
    const [files, setFiles] = useState<Record<string, string>>(initialFiles);
    const [activeFile, setActiveFile] = useState<string>(Object.keys(initialFiles)[0] || '');
    
    const [pid, setPid] = useState<string | null>(null);
    const [workspacePath, setWorkspacePath] = useState<string>('');
    const [logs, setLogs] = useState<string>('');
    const [isRunning, setIsRunning] = useState(false);
    const [runningUrl, setRunningUrl] = useState<string | null>(null);
    const hasOpenedUrlRef = useRef(false);
    
    // Chat state
    const [chatMessages, setChatMessages] = useState<{role: 'user'|'ai', content: string, is_plan?: boolean, isStreaming?: boolean, thoughts?: string[], status?: string}[]>([
        { role: 'ai', content: 'Hello! I am your Silicon Valley AI Architect. I have access to your full codebase. How would you like to upgrade your app today?' }
    ]);
    const [chatHistory, setChatHistory] = useState<{id: string, title: string, messages: {role: 'user'|'ai', content: string, is_plan?: boolean, isStreaming?: boolean, thoughts?: string[], status?: string}[]}[]>([
        { id: '1', title: 'Current Session', messages: [
            { role: 'ai', content: 'Hello! I am your Silicon Valley AI Architect. I have access to your full codebase. How would you like to upgrade your app today?' }
        ]}
    ]);
    const [activeChatId, setActiveChatId] = useState<string>('1');
    const [chatSearchQuery, setChatSearchQuery] = useState('');
    const [showChatHistoryPanel, setShowChatHistoryPanel] = useState(false);
    
    const [chatInput, setChatInput] = useState('');
    const [lastPrompt, setLastPrompt] = useState('');
    const [isPlanningMode, setIsPlanningMode] = useState(true);
    const [isChatting, setIsChatting] = useState(false);
    const [llm, setLlm] = useState<string>('llama'); // LLM Selection state
    const [modifiedFiles, setModifiedFiles] = useState<Set<string>>(new Set());
    const [newFileInput, setNewFileInput] = useState<string | null>(null);
    const [collapsedFolders, setCollapsedFolders] = useState<Set<string>>(new Set());
    
    // Multimodal state
    const [chatImages, setChatImages] = useState<string[]>([]);
    const [isRecording, setIsRecording] = useState(false);
    
    // UI state
    const [activeSidebar, setActiveSidebar] = useState<'explorer' | 'search' | 'git' | 'run' | 'extensions' | null>('explorer');
    const [rightPanelOpen, setRightPanelOpen] = useState(true);
    const [terminalOpen, setTerminalOpen] = useState(true);
    const [activeTerminalTab, setActiveTerminalTab] = useState<'problems' | 'output' | 'debug' | 'terminal' | 'ports'>('terminal');
    const [activeTerminalType, setActiveTerminalType] = useState<'powershell' | 'cmd' | 'python' | null>('powershell');
    const [terminals, setTerminals] = useState<Array<{id: string, type: 'powershell' | 'cmd', logsLen: number}>>([]);
    const [activeTerminalId, setActiveTerminalId] = useState<string | null>(null);
    const [terminalHeight, setTerminalHeight] = useState(300);
    const [isDraggingTerminal, setIsDraggingTerminal] = useState(false);
    const [showTerminalDropdown, setShowTerminalDropdown] = useState(false);
    const [isDarkMode, setIsDarkMode] = useState(true);
    const [showCloseModal, setShowCloseModal] = useState(false);
    
    const logsEndRef = useRef<HTMLDivElement>(null);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const terminalContainerRef = useRef<HTMLDivElement>(null);
    const xtermRef = useRef<Terminal | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);
    
    // Refs for terminal state closure
    const activeTerminalIdRef = useRef(activeTerminalId);
    const activeTerminalTypeRef = useRef(activeTerminalType);
    const pidRef = useRef(pid);
    const inputBufferRef = useRef('');
    
    useEffect(() => { activeTerminalIdRef.current = activeTerminalId; }, [activeTerminalId]);
    useEffect(() => { activeTerminalTypeRef.current = activeTerminalType; }, [activeTerminalType]);
    useEffect(() => { pidRef.current = pid; }, [pid]);
    
    // Initialize xterm
    useEffect(() => {
        if (!terminalContainerRef.current || !terminalOpen || activeTerminalTab !== 'terminal') return;
        
        if (!xtermRef.current) {
            const term = new Terminal({
                theme: isDarkMode ? { background: '#1e1e1e', foreground: '#cccccc' } : { background: '#ffffff', foreground: '#333333' },
                fontFamily: "'Consolas', 'Courier New', monospace",
                fontSize: 13,
                cursorBlink: true,
                disableStdin: false
            });
            const fitAddon = new FitAddon();
            term.loadAddon(fitAddon);
            
            term.open(terminalContainerRef.current);
            fitAddon.fit();
            
            xtermRef.current = term;
            fitAddonRef.current = fitAddon;
            
            // Handle user input in terminal (Line buffered for Windows Pipe compatibility)
            term.onData(async (data) => {
                const targetPid = (activeTerminalTypeRef.current === 'python') ? pidRef.current : activeTerminalIdRef.current;
                if (!targetPid) return;
                
                if (data === '\r') {
                    // Enter key pressed: send the buffered line
                    try {
                        term.write('\r\n');
                        const lineToSend = inputBufferRef.current + '\n';
                        inputBufferRef.current = '';
                        await api.post(`/api/v1/ide/terminal/input/${targetPid}`, { input: lineToSend });
                    } catch (e) {
                        console.error("Failed to send terminal input", e);
                    }
                } else if (data === '\x7f' || data === '\b') {
                    // Backspace pressed
                    if (inputBufferRef.current.length > 0) {
                        inputBufferRef.current = inputBufferRef.current.slice(0, -1);
                        term.write('\b \b'); // Erase character visually
                    }
                } else if (data === '\u0003') {
                    // Ctrl+C pressed
                    inputBufferRef.current = '';
                    term.write('^C\r\n');
                    try {
                        await api.post(`/api/v1/ide/terminal/input/${targetPid}`, { input: '\x03' });
                    } catch (e) {
                        console.error("Failed to send Ctrl+C", e);
                    }
                } else {
                    // Normal character typed
                    inputBufferRef.current += data;
                    term.write(data);
                }
            });
            
            // Initial write
            if (logs) {
                term.write(logs.replace(/\n/g, '\r\n'));
            } else {
                term.write('Welcome to DataVision Terminal.\r\nType "python api_server.py" to start manually.\r\n\r\n> ');
            }
        }
        
        const handleResize = () => {
            if (fitAddonRef.current) fitAddonRef.current.fit();
        };
        window.addEventListener('resize', handleResize);
        
        return () => {
            window.removeEventListener('resize', handleResize);
            if (xtermRef.current) {
                xtermRef.current.dispose();
                xtermRef.current = null;
            }
        };
    }, [terminalOpen, activeTerminalTab, isDarkMode]);
    
    // Terminal Dragging
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isDraggingTerminal) return;
            // Calculate new height (window height - mouse Y - status bar approx height)
            const newHeight = window.innerHeight - e.clientY - 24;
            setTerminalHeight(Math.max(100, Math.min(newHeight, window.innerHeight - 200)));
            // Trigger xterm fit on drag
            if (fitAddonRef.current) fitAddonRef.current.fit();
        };
        const handleMouseUp = () => setIsDraggingTerminal(false);
        
        if (isDraggingTerminal) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            // Disable text selection while dragging
            document.body.style.userSelect = 'none';
        } else {
            document.body.style.userSelect = '';
        }
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDraggingTerminal]);

    // Theme observer
    useEffect(() => {
        const checkDarkMode = () => setIsDarkMode(document.documentElement.classList.contains('dark'));
        checkDarkMode();
        const observer = new MutationObserver(checkDarkMode);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        if (logsEndRef.current) logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }, [logs, activeTerminalTab]);

    useEffect(() => {
        if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }, [chatMessages]);

    useEffect(() => {
        const fetchPath = async () => {
            try {
                const res = await api.get(`/api/v1/ide/workspace-path/${getUserIdSync()}`);
                if (res.data.success) {
                    setWorkspacePath(res.data.path);
                }
            } catch (e) {}
        };
        fetchPath();
    }, []);

    // Load persisted files and check for running process on mount
    useEffect(() => {
        const userId = getUserIdSync();
        
        // 1. Load persisted files from localStorage
        const stored = localStorage.getItem(`ide_files_${userId}`);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (Object.keys(parsed).length > 0) {
                    setFiles(prev => ({ ...prev, ...parsed }));
                }
            } catch (e) {}
        }
        
        // Removed checkStatus to prevent reconnecting to old powershell terminals
    }, []);

    // Persist files to localStorage when they change
    useEffect(() => {
        if (Object.keys(files).length > 0) {
            localStorage.setItem(`ide_files_${getUserIdSync()}`, JSON.stringify(files));
        }
    }, [files]);
    const spawnTerminal = async (type: 'powershell' | 'cmd') => {
        try {
            const res = await api.post('/api/v1/ide/terminal/spawn', { user_id: getUserIdSync(), shell: type });
            if (res.data.success) {
                const newTerminal = { id: res.data.pid, type, logsLen: 0 };
                setTerminals(prev => [...prev, newTerminal]);
                setActiveTerminalId(newTerminal.id);
                setActiveTerminalType(type);
                if (xtermRef.current) xtermRef.current.reset();
            }
        } catch (e) {
            console.error("Failed to spawn terminal", e);
        }
    };

    const deleteTerminal = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await api.post(`/api/v1/ide/stop/${id}`);
            setTerminals(prev => {
                const next = prev.filter(t => t.id !== id);
                if (activeTerminalId === id) {
                    if (next.length > 0) {
                        setActiveTerminalId(next[next.length - 1].id);
                        setActiveTerminalType(next[next.length - 1].type);
                    } else {
                        setActiveTerminalId(null);
                        // fallback to python if running, else cmd
                        setActiveTerminalType(isRunning ? 'python' : null);
                    }
                }
                return next;
            });
        } catch (err) {
            console.error("Failed to delete terminal", err);
        }
    };

    // Auto-spawn raw terminal when tab opens and no terminals exist
    useEffect(() => {
        if (terminalOpen && activeTerminalTab === 'terminal' && terminals.length === 0 && (activeTerminalType === 'powershell' || activeTerminalType === 'cmd' || activeTerminalType === null)) {
            spawnTerminal('powershell');
        }
    }, [terminalOpen, activeTerminalTab, terminals.length, activeTerminalType]);

    // Handle switching between existing terminals
    useEffect(() => {
        if (activeTerminalTab === 'terminal') {
            if (xtermRef.current) xtermRef.current.reset();
            
            if (activeTerminalType === 'python' && pid) {
                // we will fetch logs in the python polling effect
            } else if (activeTerminalId) {
                // Reset length so it fetches full history of switched terminal
                setTerminals(prev => prev.map(t => t.id === activeTerminalId ? { ...t, logsLen: 0 } : t));
            }
        }
    }, [activeTerminalId, activeTerminalType, activeTerminalTab]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (pid && isRunning) {
            interval = setInterval(async () => {
                try {
                    const res = await api.get(`/api/v1/ide/logs/${pid}`);
                    if (res.data.success) {
                        if (xtermRef.current && res.data.logs && activeTerminalType === 'python') {
                            const newLogs = res.data.logs.slice(logs.length);
                            if (newLogs) xtermRef.current.write(newLogs.replace(/\n/g, '\r\n'));
                        }
                        
                        setLogs(res.data.logs);
                        
                        if (res.data.url) {
                            setRunningUrl(res.data.url);
                            if (!hasOpenedUrlRef.current) {
                                hasOpenedUrlRef.current = true;
                                window.open(res.data.url, '_blank');
                            }
                        }
                        if (res.data.status !== 'running') {
                            setIsRunning(false);
                        }
                    }
                } catch (err) {}
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [pid, isRunning, logs, activeTerminalType]);

    // Polling for Standalone Terminal
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (activeTerminalId && (activeTerminalType === 'powershell' || activeTerminalType === 'cmd')) {
            interval = setInterval(async () => {
                try {
                    const res = await api.get(`/api/v1/ide/logs/${activeTerminalId}`);
                    if (res.data.success && res.data.logs) {
                        const allLogs = res.data.logs;
                        
                        setTerminals(prev => {
                            const activeTerm = prev.find(t => t.id === activeTerminalId);
                            if (activeTerm && allLogs.length > activeTerm.logsLen) {
                                const newChunk = allLogs.slice(activeTerm.logsLen);
                                if (xtermRef.current) xtermRef.current.write(newChunk.replace(/\n/g, '\r\n'));
                                return prev.map(t => t.id === activeTerminalId ? { ...t, logsLen: allLogs.length } : t);
                            }
                            return prev;
                        });
                    }
                } catch (err) {}
            }, 200); // Poll faster for responsiveness
        }
        return () => clearInterval(interval);
    }, [activeTerminalId, activeTerminalType]);

    const handleRun = async () => {
        try {
            setIsRunning(true);
            setRunningUrl(null);
            hasOpenedUrlRef.current = false;
            setLogs('[System] Instructing backend to auto-detect and run project...\\n');
            const res = await api.post(`/api/v1/ide/run`, {
                user_id: getUserIdSync(),
                command: "python api_server.py", // Or allow auto-detect by passing empty/null if backend supports it
                files: files
            });
            
            if (res.data.success) {
                setPid(res.data.pid);
            }
        } catch (err: any) {
            setLogs(prev => prev + `
[System Error]: ${err.message}`);
            setIsRunning(false);
        }
    };
    const handleStop = async () => {
        if (!pid) {
            setLogs('');
            setTerminalOpen(false);
            return;
        }
        try {
            await api.post(`/api/v1/ide/stop/${pid}`);
            setLogs(prev => prev + '\n[Process stopped by user.]\n');
        } catch (err) {
            console.error("Failed to stop cleanly", err);
        } finally {
            setIsRunning(false);
            setPid(null);
        }
    };

    const handleDownload = async () => {
        try {
            const res = await api.post('/api/v1/ide/download', { user_id: getUserIdSync(), files }, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'workspace.zip');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Failed to download workspace", err);
        }
    };

    const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64String = reader.result as string;
                setChatImages(prev => [...prev, base64String]);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleVoiceRecord = () => {
        // Use browser SpeechRecognition API
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Voice recording is not supported in your browser.");
            return;
        }
        
        if (isRecording) return; // Prevent multiple instances
        
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = () => {
            setIsRecording(true);
        };
        
        recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript;
            setChatInput(prev => prev ? prev + ' ' + transcript : transcript);
            setIsRecording(false);
        };
        
        recognition.onerror = (event: any) => {
            console.error("Speech recognition error", event.error);
            setIsRecording(false);
        };
        
        recognition.onend = () => {
            setIsRecording(false);
        };
        
        recognition.start();
    };

    const handleChat = async (overrideMsg?: string, forceMode?: 'plan' | 'execute') => {
        const userMsg = overrideMsg || chatInput;
        if (!userMsg.trim() || isChatting) return;
        
        if (!overrideMsg) {
            setChatInput('');
            setLastPrompt(userMsg);
            setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        }
        
        setIsChatting(true);
        // Add a placeholder AI message that we will stream into
        setChatMessages(prev => [...prev, { role: 'ai', content: '', isStreaming: true, thoughts: [] }]);
        
        try {
            const currentMode = forceMode || (isPlanningMode ? 'plan' : 'execute');
            
            // Build the body for fetch
            const body = {
                user_id: getUserIdSync(),
                files: files,
                prompt: userMsg,
                model: llm,
                chat_history: chatMessages.map(msg => ({ role: msg.role, content: msg.content })),
                images: chatImages.length > 0 ? chatImages : undefined,
                mode: currentMode
            };
            
            // Clear attached images after sending
            setChatImages([]);
            
            const token = localStorage.getItem('token');
            const response = await fetch('/api/v1/ide/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : ''
                },
                body: JSON.stringify(body)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const reader = response.body?.getReader();
            if (!reader) throw new Error("No reader available");
            
            const decoder = new TextDecoder("utf-8");
            let buffer = "";
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || "";
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        try {
                            const data = JSON.parse(dataStr);
                            
                            setChatMessages(prev => {
                                const newMsgs = [...prev];
                                if (newMsgs.length === 0) return prev;
                                
                                const lastIndex = newMsgs.length - 1;
                                if (newMsgs[lastIndex].role !== 'ai') return prev;
                                
                                // Must clone the last message object to avoid mutating state
                                const lastMsg = { ...newMsgs[lastIndex] };
                                
                                if (data.type === 'status') {
                                    lastMsg.status = data.content;
                                } else if (data.type === 'thought') {
                                    lastMsg.thoughts = lastMsg.thoughts ? [...lastMsg.thoughts, data.content] : [data.content];
                                } else if (data.type === 'tool_call') {
                                    lastMsg.content = (lastMsg.content || "") + `\n> 🛠️ Running Tool: ${data.tool}\n\`\`\`json\n${JSON.stringify(data.args, null, 2)}\n\`\`\`\n`;
                                } else if (data.type === 'tool_result') {
                                    lastMsg.content = (lastMsg.content || "") + `\n*✅ Tool Complete*\n`;
                                } else if (data.type === 'message') {
                                    lastMsg.content = (lastMsg.content ? lastMsg.content + "\n\n" : "") + data.content;
                                } else if (data.type === 'done') {
                                    lastMsg.isStreaming = false;
                                } else if (data.type === 'error') {
                                    lastMsg.content = (lastMsg.content || "") + `\n\n**Error:** ${data.content}`;
                                    lastMsg.isStreaming = false;
                                }
                                
                                newMsgs[lastIndex] = lastMsg;
                                return newMsgs;
                            });
                            
                            if (data.type === 'sync_files' && data.files) {
                                setFiles(prev => ({ ...prev, ...data.files }));
                                setModifiedFiles(prev => {
                                    const next = new Set(prev);
                                    Object.keys(data.files).forEach(f => next.add(f));
                                    return next;
                                });
                            }
                        } catch (e) {
                            console.error("Failed to parse SSE JSON", e, dataStr);
                        }
                    }
                }
            }
            
        } catch (error: any) {
            setChatMessages(prev => [...prev, { role: 'ai', content: `Error: ${error.message}` }]);
        } finally {
            setIsChatting(false);
            setChatMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                if (lastMsg.role === 'ai') lastMsg.isStreaming = false;
                return newMsgs;
            });
        }
    };

    // Sync chat messages to history whenever they change
    useEffect(() => {
        setChatHistory(prev => prev.map(chat => 
            chat.id === activeChatId ? { ...chat, messages: chatMessages } : chat
        ));
    }, [chatMessages, activeChatId]);

    const createNewChat = () => {
        const newId = Date.now().toString();
        const initialMsg = { role: 'ai' as const, content: 'Hello! I am your Silicon Valley AI Architect. I have access to your full codebase. How would you like to upgrade your app today?' };
        setChatHistory(prev => [{ id: newId, title: 'New Session', messages: [initialMsg] }, ...prev]);
        setActiveChatId(newId);
        setChatMessages([initialMsg]);
        setShowChatHistoryPanel(false);
    };

    const switchChat = (id: string) => {
        const chat = chatHistory.find(c => c.id === id);
        if (chat) {
            setActiveChatId(id);
            setChatMessages(chat.messages);
            setShowChatHistoryPanel(false);
        }
    };

    const fileList = Object.keys(files).sort((a, b) => {
        const aDepth = a.split('/').length;
        const bDepth = b.split('/').length;
        if (aDepth !== bDepth) return aDepth - bDepth;
        return a.localeCompare(b);
    });

    // Build folder tree structure
    const getFolders = (): string[] => {
        const folders = new Set<string>();
        fileList.forEach(f => {
            const parts = f.split('/');
            if (parts.length > 1) {
                for (let i = 1; i < parts.length; i++) {
                    folders.add(parts.slice(0, i).join('/'));
                }
            }
        });
        return Array.from(folders).sort();
    };
    const folders = getFolders();

    const toggleFolder = (folder: string) => {
        setCollapsedFolders(prev => {
            const next = new Set(prev);
            if (next.has(folder)) next.delete(folder); else next.add(folder);
            return next;
        });
    };

    const isFileVisible = (filename: string): boolean => {
        const parts = filename.split('/');
        if (parts.length <= 1) return true;
        for (let i = 1; i < parts.length; i++) {
            const parentFolder = parts.slice(0, i).join('/');
            if (collapsedFolders.has(parentFolder)) return false;
        }
        return true;
    };

    const handleCreateFile = (filename: string) => {
        if (!filename.trim()) return;
        setFiles(prev => ({ ...prev, [filename.trim()]: '' }));
        setActiveFile(filename.trim());
        setNewFileInput(null);
    };

    const handleDeleteFile = (filename: string) => {
        setFiles(prev => {
            const next = { ...prev };
            delete next[filename];
            return next;
        });
        if (activeFile === filename) {
            const remaining = Object.keys(files).filter(f => f !== filename);
            setActiveFile(remaining[0] || '');
        }
    };

    const getFileIcon = (filename: string) => {
        if (filename.endsWith('.py')) return 'text-blue-500 dark:text-[#4fc1ff]';
        if (filename.endsWith('.html')) return 'text-orange-500 dark:text-[#e37933]';
        if (filename.endsWith('.css')) return 'text-purple-500 dark:text-[#a855f7]';
        if (filename.endsWith('.js') || filename.endsWith('.jsx')) return 'text-yellow-500 dark:text-[#cbcb41]';
        if (filename.endsWith('.ts') || filename.endsWith('.tsx')) return 'text-blue-600 dark:text-[#3178c6]';
        if (filename.endsWith('.json')) return 'text-yellow-600 dark:text-[#cbcb41]';
        if (filename.endsWith('.md')) return 'text-blue-400 dark:text-[#519aba]';
        if (filename.endsWith('.csv')) return 'text-green-600 dark:text-[#89d185]';
        if (filename.endsWith('.txt') || filename.endsWith('.yml') || filename.endsWith('.yaml')) return 'text-slate-500 dark:text-[#cccccc]';
        return 'text-slate-600 dark:text-[#cccccc]';
    };

    const getMonacoLanguage = (filename: string) => {
        if (filename.endsWith('.py')) return 'python';
        if (filename.endsWith('.js') || filename.endsWith('.jsx')) return 'javascript';
        if (filename.endsWith('.ts') || filename.endsWith('.tsx')) return 'typescript';
        if (filename.endsWith('.html')) return 'html';
        if (filename.endsWith('.css')) return 'css';
        if (filename.endsWith('.json')) return 'json';
        if (filename.endsWith('.md')) return 'markdown';
        if (filename.endsWith('.yml') || filename.endsWith('.yaml')) return 'yaml';
        if (filename.endsWith('.sh') || filename.endsWith('.bash')) return 'shell';
        if (filename.endsWith('.dockerfile') || filename === 'Dockerfile') return 'dockerfile';
        return 'plaintext';
    };

    // Simple markdown-like renderer for chat messages
    const renderChatContent = (content: string) => {
        const parts = content.split(/(```[\s\S]*?```|`[^`]+`|\*\*[^*]+\*\*|\n)/g);
        return parts.map((part, i) => {
            if (part.startsWith('```') && part.endsWith('```')) {
                const code = part.slice(3, -3).replace(/^\w+\n/, '');
                return <pre key={i} className="bg-slate-900 text-green-400 text-[11px] p-2 rounded my-1 overflow-x-auto font-mono whitespace-pre-wrap">{code}</pre>;
            }
            if (part.startsWith('`') && part.endsWith('`')) {
                return <code key={i} className="bg-slate-200 dark:bg-[#1e1e1e] text-pink-600 dark:text-[#ce9178] px-1 rounded text-[12px] font-mono">{part.slice(1, -1)}</code>;
            }
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
            }
            if (part === '\n') return <br key={i} />;
            return <span key={i}>{part}</span>;
        });
    };

    const modalContent = (
        <div className="fixed inset-0 z-[9999] flex flex-col bg-white dark:bg-[#1e1e1e] text-slate-800 dark:text-[#cccccc] font-sans h-screen w-screen overflow-hidden selection:bg-blue-200 dark:selection:bg-[#264f78]">
            {/* VSCode Custom Titlebar */}
            <div className="h-[30px] flex items-center justify-between bg-slate-100 dark:bg-[#333333] border-b border-slate-300 dark:border-[#2b2b2b] select-none px-3 shrink-0">
                <div className="flex items-center gap-4 h-full">
                    <img src="/favicon.ico" alt="Logo" className="w-4 h-4 opacity-80" onError={(e) => e.currentTarget.style.display = 'none'} />
                    <div className="flex gap-4 text-[13px] text-slate-600 dark:text-[#cccccc]">
                        <span className="hover:text-black dark:hover:text-white cursor-pointer">File</span>
                        <span className="hover:text-black dark:hover:text-white cursor-pointer">Edit</span>
                        <span className="hover:text-black dark:hover:text-white cursor-pointer">Selection</span>
                        <span className="hover:text-black dark:hover:text-white cursor-pointer">View</span>
                        <span className="hover:text-black dark:hover:text-white cursor-pointer">Go</span>
                        <span className="hover:text-black dark:hover:text-white cursor-pointer" onClick={() => handleRun()}>Run</span>
                        <span className="hover:text-black dark:hover:text-white cursor-pointer">Help</span>
                    </div>
                </div>
                <div className="text-[12px] text-slate-500 dark:text-[#999999] absolute left-1/2 -translate-x-1/2 font-bold">
                    DataVision IDE Orchestrator
                </div>
                <div className="flex gap-2">
                    <button className="w-3.5 h-3.5 rounded-full bg-red-500 hover:bg-red-400" onClick={() => setShowCloseModal(true)} />
                    <div className="w-3.5 h-3.5 rounded-full bg-yellow-500" />
                    <div className="w-3.5 h-3.5 rounded-full bg-green-500" />
                </div>
            </div>

            <div className="flex flex-1 min-h-0 relative">
                
                {/* Orchestrator Hub (Center) */}
                <div className="flex-1 flex flex-col items-center justify-center bg-[#f9f9f9] dark:bg-[#1e1e1e] p-8 text-slate-800 dark:text-[#cccccc]">
                    <img src="/favicon.ico" alt="DataVision" className="w-24 h-24 opacity-20 grayscale mb-8" onError={(e) => e.currentTarget.style.display = 'none'} />
                    <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">DataVision IDE Orchestrator</h2>
                    <p className="text-slate-700 dark:text-slate-300 mb-8 text-center max-w-2xl text-base leading-relaxed">
                        DataVision is now a <strong className="text-blue-600 dark:text-blue-400">Local Project Orchestrator</strong>. <br/><br/>
                        Here is how it works:<br/>
                        1. The <strong className="text-slate-900 dark:text-white">DataVision Agent</strong> on the right writes the code and plans your architecture.<br/>
                        2. You click <strong className="text-slate-900 dark:text-white">"Open in [IDE]"</strong> below to view or edit the code in your preferred local environment.<br/>
                        3. You click <strong className="text-slate-900 dark:text-white">"RUN PROJECT"</strong> below to automatically detect frameworks, install dependencies, and start the local server.
                        <br/><br/>
                        <span className="text-[14px] text-slate-500 dark:text-slate-400 italic bg-slate-100 dark:bg-[#252526] px-4 py-2 rounded-lg border border-slate-200 dark:border-[#333] inline-block mt-2">
                            Prefer your own terminal? Click <strong>Copy Path</strong> below and run the project manually in your local laptop terminal!
                        </span>
                    </p>
                    
                    <div className="flex flex-wrap justify-center gap-4 mb-8">
                        <a 
                            href={`vscode://file/${workspacePath}`}
                            className="flex items-center gap-2 px-6 py-3 bg-[#007acc] hover:bg-[#005a9e] text-white rounded-lg font-semibold shadow-lg transition-colors"
                            style={{ color: '#ffffff' }}
                        >
                            <VSCodeIcon /> Open in VS Code
                        </a>
                        <a 
                            href={`cursor://file/${workspacePath}`}
                            className="flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-black text-white rounded-lg font-semibold shadow-lg border border-slate-700 transition-colors"
                            style={{ color: '#ffffff' }}
                        >
                            <CursorIcon /> Open in Cursor
                        </a>
                        <a 
                            href={`antigravity://file/${workspacePath}`}
                            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold shadow-lg transition-colors"
                            style={{ color: '#ffffff' }}
                        >
                            <AntigravityIcon /> Open in Antigravity
                        </a>
                        <button 
                            onClick={() => {
                                navigator.clipboard.writeText(workspacePath);
                                alert('Workspace path copied to clipboard!');
                            }}
                            className="flex items-center gap-2 px-6 py-3 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-white rounded-lg font-semibold shadow-lg transition-colors"
                        >
                            <FolderOpen className="w-5 h-5" /> Copy Path
                        </button>
                    </div>
                    
                    {/* Console & Execution Area */}
                    <div className="w-full max-w-3xl bg-white dark:bg-[#252526] rounded-xl border border-slate-200 dark:border-[#333] overflow-hidden flex flex-col shadow-lg">
                        <div className="px-4 py-3 border-b border-slate-200 dark:border-[#333] flex justify-between items-center bg-slate-50 dark:bg-[#2d2d2d]">
                            <div className="flex items-center gap-2 font-semibold text-slate-700 dark:text-[#ccc]">
                                <PlaySquare className="w-4 h-4 text-emerald-500" /> Local Server Orchestration
                            </div>
                            <div className="flex gap-2">
                                {!isRunning ? (
                                    <button onClick={() => handleRun()} className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-bold flex items-center gap-2 shadow transition-colors text-sm">
                                        <Play className="w-4 h-4 fill-white" /> RUN PROJECT
                                    </button>
                                ) : (
                                    <>
                                        {runningUrl && (
                                            <a href={runningUrl} target="_blank" rel="noopener noreferrer" className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded font-bold flex items-center gap-2 shadow transition-colors text-sm">
                                                <ExternalLink className="w-4 h-4" /> OPEN APP
                                            </a>
                                        )}
                                        <button onClick={handleStop} className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded font-bold flex items-center gap-2 shadow transition-colors text-sm">
                                            <Square className="w-4 h-4 fill-white" /> STOP
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                        <div className="h-64 p-4 font-mono text-[13px] overflow-y-auto bg-slate-50 dark:bg-[#0d0d0d] text-slate-800 dark:text-emerald-400 whitespace-pre-wrap leading-relaxed shadow-inner border-t border-slate-200 dark:border-transparent">
                            {logs || "[Standby] Ready to orchestrate local project...\\nClick 'RUN PROJECT' to automatically detect frameworks and start the server."}
                            <div ref={logsEndRef} />
                        </div>
                    </div>
                </div>

                {/* Right Panel: AI Architect (Unchanged) */}
                <div className={`border-l border-slate-300 dark:border-[#333333] bg-[#f3f3f3] dark:bg-[#252526] flex flex-col transition-all duration-300 ease-in-out shrink-0 overflow-hidden ${rightPanelOpen ? 'w-[350px] opacity-100' : 'w-0 opacity-0 border-l-0'}`}>
                    <div className="px-4 flex justify-between items-center shrink-0 h-[40px] border-b border-slate-300 dark:border-[#333333]">
                        <div className="flex items-center gap-2">
                            <span className="text-[11px] font-bold text-slate-600 dark:text-[#cccccc] uppercase tracking-widest flex items-center gap-2">
                                <MessageSquare className="w-3.5 h-3.5" /> DataVision Agent
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            <select
                                value={llm}
                                onChange={(e) => setLlm(e.target.value)}
                                className="bg-transparent text-[10px] text-slate-500 dark:text-[#858585] outline-none cursor-pointer hover:text-slate-800 dark:hover:text-[#ccc]"
                                title="Select AI Model"
                            >
                                <option value="llama">Llama 3.3 70B</option>
                                <option value="deepseek">DeepSeek V4</option>
                                <option value="nemotron">Nemotron Ultra</option>
                                <option value="glm">GLM 5.1</option>
                                <option value="kimi">Kimi 2.6</option>
                            </select>
                            <button onClick={() => setShowChatHistoryPanel(!showChatHistoryPanel)} className="text-slate-500 hover:text-blue-500 dark:text-[#858585] dark:hover:text-[#007acc] transition-colors" title="Chat History">
                                <Files className="w-4 h-4" />
                            </button>
                            <button onClick={createNewChat} className="text-slate-500 hover:text-emerald-500 dark:text-[#858585] dark:hover:text-emerald-400 transition-colors" title="New Chat">
                                <Plus className="w-4 h-4" />
                            </button>
                            <div className="w-px h-3 bg-slate-300 dark:bg-[#444] mx-1"></div>
                            <X className="w-4 h-4 text-slate-500 dark:text-[#858585] hover:text-black dark:hover:text-[#cccccc] cursor-pointer transition-colors" onClick={() => setRightPanelOpen(false)}/>
                        </div>
                    </div>
                    
                    {showChatHistoryPanel ? (
                        <div className="flex-1 flex flex-col bg-white dark:bg-[#1e1e1e] border-b border-slate-200 dark:border-[#333]">
                            <div className="p-3 border-b border-slate-200 dark:border-[#333]">
                                <div className="relative">
                                    <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                                    <input 
                                        type="text" 
                                        placeholder="Search history..." 
                                        value={chatSearchQuery}
                                        onChange={e => setChatSearchQuery(e.target.value)}
                                        className="w-full bg-slate-100 dark:bg-[#2d2d2d] text-[12px] text-slate-800 dark:text-[#ccc] pl-8 pr-3 py-1.5 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                    />
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-[#424242]">
                                {chatHistory.filter(c => c.title.toLowerCase().includes(chatSearchQuery.toLowerCase())).map(chat => (
                                    <div 
                                        key={chat.id}
                                        onClick={() => switchChat(chat.id)}
                                        className={`p-2.5 rounded cursor-pointer text-[12px] transition-colors ${activeChatId === chat.id ? 'bg-blue-50 dark:bg-[#2d2d30] text-blue-600 dark:text-[#fff]' : 'text-slate-600 dark:text-[#ccc] hover:bg-slate-50 dark:hover:bg-[#2d2d2d]'}`}
                                    >
                                        <div className="font-medium truncate mb-1">{chat.title}</div>
                                        <div className="text-[10px] text-slate-400 dark:text-[#858585] truncate">
                                            {chat.messages.length > 0 ? chat.messages[chat.messages.length - 1].content : 'Empty session'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 overflow-y-auto p-4 space-y-5 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-[#424242]">
                            {chatMessages.map((msg, i) => (
                                <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                    <div className={`text-[11px] font-semibold text-slate-500 dark:text-[#858585] mb-1.5 flex items-center gap-1.5`}>
                                        {msg.role === 'user' ? <UserCircle className="w-3.5 h-3.5" /> : <div className="w-4 h-4 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"><Loader2 className="w-2.5 h-2.5 text-white" /></div>}
                                        {msg.role === 'user' ? 'You' : 'DataVision Agent'}
                                        {msg.role === 'user' && (
                                            <button onClick={() => setChatInput(msg.content)} className="ml-2 p-0.5 hover:bg-slate-200 dark:hover:bg-[#444] rounded text-blue-500 transition-colors" title="Edit Query">
                                                <Edit3 className="w-3 h-3" />
                                            </button>
                                        )}
                                    </div>
                                    <div className={`text-[13px] leading-relaxed max-w-[95%] p-3 rounded-xl shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white dark:bg-[#333333] text-slate-800 dark:text-[#cccccc] rounded-bl-none border border-slate-200 dark:border-transparent'}`}>
                                        
                                        {msg.role === 'ai' && msg.thoughts && msg.thoughts.length > 0 && (
                                            <details className="mb-3 text-[11px] bg-slate-50 dark:bg-[#252526] rounded border border-slate-200 dark:border-[#444]">
                                                <summary className="cursor-pointer font-semibold text-slate-500 dark:text-[#888] px-2 py-1.5 hover:bg-slate-100 dark:hover:bg-[#2d2d2d] rounded">
                                                    Agent Thoughts ({msg.thoughts.length})
                                                </summary>
                                                <div className="p-2 pt-0 text-slate-600 dark:text-[#aaa] border-t border-slate-200 dark:border-[#444] space-y-2 font-mono whitespace-pre-wrap">
                                                    {msg.thoughts.map((t, idx) => <div key={idx}>{t}</div>)}
                                                </div>
                                            </details>
                                        )}
                                        
                                        {msg.role === 'ai' && msg.status && (
                                            <div className="text-[11px] font-mono text-blue-500 dark:text-[#4fc1ff] mb-2 animate-pulse flex items-center gap-1.5">
                                                <Loader2 className="w-3 h-3 animate-spin" /> {msg.status}
                                            </div>
                                        )}

                                        {msg.role === 'ai' ? renderChatContent(msg.content) : msg.content}
                                        {msg.role === 'ai' && msg.is_plan && (
                                             <div className="mt-3 pt-3 border-t border-slate-200 dark:border-[#555] flex justify-end">
                                                 <button onClick={() => handleChat(lastPrompt, 'execute')} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-[12px] font-semibold rounded shadow-sm flex items-center gap-1.5 transition-colors">
                                                     <PlaySquare className="w-3.5 h-3.5" /> Build It
                                                 </button>
                                             </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            <div ref={chatEndRef} />
                        </div>
                    )}

                    <div className="p-3 bg-white dark:bg-[#252526] shrink-0 border-t border-slate-200 dark:border-transparent">
                        <form onSubmit={(e) => { e.preventDefault(); handleChat(); }} className="relative flex flex-col border border-slate-300 dark:border-[#3c3c3c] bg-white dark:bg-[#3c3c3c] rounded focus-within:border-blue-600 dark:focus-within:border-[#007acc] transition-colors shadow-sm dark:shadow-none">
                            {chatImages.length > 0 && (
                                <div className="flex gap-2 p-2 border-b border-slate-200 dark:border-[#555] overflow-x-auto">
                                    {chatImages.map((img, i) => (
                                        <div key={i} className="relative w-12 h-12 shrink-0">
                                            <img src={img} alt={`attachment-${i}`} className="w-full h-full object-cover rounded" />
                                            <button 
                                                type="button"
                                                onClick={() => setChatImages(prev => prev.filter((_, index) => index !== i))}
                                                className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-0.5 hover:bg-red-600"
                                            >
                                                <X className="w-2 h-2" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                            <textarea
                                value={chatInput}
                                onChange={(e) => setChatInput(e.target.value)}
                                placeholder="Ask AI to modify code..."
                                disabled={isChatting}
                                rows={2}
                                className="w-full bg-transparent text-[13px] text-slate-800 dark:text-[#cccccc] pl-3 pr-24 py-2 focus:outline-none disabled:opacity-50 resize-none"
                                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleChat(); } }}
                            />
                            <div className="absolute right-2 bottom-2 flex items-center gap-1">
                                <label className="p-1 hover:bg-slate-100 dark:hover:bg-[#505050] text-slate-600 dark:text-[#cccccc] rounded cursor-pointer transition-colors" title="Attach Image">
                                    <ImagePlus className="w-3.5 h-3.5" />
                                    <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
                                </label>
                                <button 
                                    type="button" 
                                    onClick={handleVoiceRecord}
                                    className={`p-1 hover:bg-slate-100 dark:hover:bg-[#505050] rounded transition-colors ${isRecording ? 'text-red-500 animate-pulse bg-red-50 dark:bg-red-900/30' : 'text-slate-600 dark:text-[#cccccc]'}`}
                                    title="Voice Dictation"
                                >
                                    <Mic className="w-3.5 h-3.5" />
                                </button>
                                <button type="submit" disabled={!chatInput.trim() || isChatting} className="p-1 hover:bg-slate-100 dark:hover:bg-[#505050] text-slate-600 dark:text-[#cccccc] rounded disabled:opacity-50 transition-colors">
                                    <Send className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            {/* Close Modal */}
            {showCloseModal && (
                <div className="fixed inset-0 z-[10000] bg-black/50 flex items-center justify-center">
                    <div className="bg-white dark:bg-[#252526] p-6 rounded-lg shadow-xl max-w-md w-full mx-4 border border-slate-200 dark:border-[#333333]">
                        <h3 className="text-lg font-semibold mb-4 text-slate-800 dark:text-white">Session Management</h3>
                        <p className="text-slate-600 dark:text-[#cccccc] mb-6 text-sm leading-relaxed">
                            How would you like to handle your current workspace?
                            {isRunning && <><br/><br/><strong className="text-emerald-600 dark:text-emerald-400">Note:</strong> You have a server process currently running.</>}
                        </p>
                        <div className="flex flex-col gap-3">
                            <button 
                                onClick={() => { 
                                    setShowCloseModal(false); 
                                    if (onClose) onClose(); 
                                }} 
                                className="w-full px-4 py-2.5 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors text-left flex items-center justify-between"
                            >
                                <span>Keep Session Running in Background</span>
                                <span className="text-[10px] opacity-75 font-normal uppercase tracking-wider border border-white/30 px-1.5 rounded">Recommended</span>
                            </button>
                            
                            <button 
                                onClick={async () => { 
                                    setShowCloseModal(false); 
                                    await handleStop(); 
                                    if (onClose) onClose(); 
                                }} 
                                className="w-full px-4 py-2.5 text-sm font-semibold bg-red-600 hover:bg-red-700 text-white rounded transition-colors text-left flex items-center justify-between"
                            >
                                <span>End Session & Close IDE</span>
                                <span className="text-[10px] opacity-75 font-normal uppercase tracking-wider border border-white/30 px-1.5 rounded">Kills Process</span>
                            </button>
                            
                            <button 
                                onClick={() => setShowCloseModal(false)} 
                                className="w-full px-4 py-2 text-sm text-slate-600 dark:text-[#cccccc] hover:bg-slate-100 dark:hover:bg-[#333333] rounded transition-colors mt-2"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

    if (typeof document !== 'undefined') {
        return createPortal(
            <WebIDEErrorBoundary>
                {modalContent}
            </WebIDEErrorBoundary>,
            document.body
        );
    }
    return null;
};
