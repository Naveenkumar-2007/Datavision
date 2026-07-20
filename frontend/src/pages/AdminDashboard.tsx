import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Users, FileText, MessageSquare, Activity, Database,
  Server, Trash2, Search, LogOut, BarChart3, Globe, Cpu,
  HardDrive, Clock, RefreshCw, UserX, UserCheck, ChevronDown,
  Megaphone, X, AlertTriangle, CheckCircle2, Zap, Wifi, Code
} from 'lucide-react';
import { api } from '@/services/api';

// Admin API helper
const adminApi = {
  get: (url: string) => api.get(url, { headers: { Authorization: `Bearer ${sessionStorage.getItem('admin_token')}` } }),
  post: (url: string, data?: any) => api.post(url, data, { headers: { Authorization: `Bearer ${sessionStorage.getItem('admin_token')}` } }),
  put: (url: string, data?: any) => api.put(url, data, { headers: { Authorization: `Bearer ${sessionStorage.getItem('admin_token')}` } }),
  delete: (url: string) => api.delete(url, { headers: { Authorization: `Bearer ${sessionStorage.getItem('admin_token')}` } }),
};

const AnimatedCounter = ({ value, suffix = '' }: { value: number; suffix?: string }) => {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const steps = 30;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) { setDisplay(value); clearInterval(timer); }
      else { setDisplay(Math.floor(current)); }
    }, 30);
    return () => clearInterval(timer);
  }, [value]);
  return <>{display.toLocaleString()}{suffix}</>;
};

const DialRing = ({ percentage, label, icon: Icon, colorClass, gradientFrom, gradientTo }: any) => {
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-[#11111a]/80 backdrop-blur-xl border border-gray-800/60 rounded-3xl shadow-2xl relative overflow-hidden group">
      <div className={`absolute inset-0 bg-gradient-to-br ${gradientFrom} ${gradientTo} opacity-[0.02] group-hover:opacity-[0.05] transition-opacity`} />
      
      <div className="relative flex items-center justify-center">
        <svg className="w-24 h-24 transform -rotate-90">
          <circle
            cx="48" cy="48" r={radius}
            className="stroke-gray-800/50" strokeWidth="6" fill="transparent"
          />
          <circle
            cx="48" cy="48" r={radius}
            className={`stroke-current ${colorClass} transition-all duration-1000 ease-out`}
            strokeWidth="6" fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <Icon className={`w-5 h-5 mb-1 ${colorClass}`} />
          <span className="text-white font-bold text-sm">{Math.round(percentage)}%</span>
        </div>
      </div>
      <span className="mt-3 text-xs font-semibold tracking-wider text-gray-500 uppercase">{label}</span>
    </div>
  );
};

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'system' | 'activity'>('overview');
  
  // Real-time State
  const [stats, setStats] = useState<any>(null);
  const [system, setSystem] = useState<any>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Normal State
  const [users, setUsers] = useState<any[]>([]);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // UI State
  const [searchQuery, setSearchQuery] = useState('');
  const [showBroadcast, setShowBroadcast] = useState(false);
  const [broadcastTitle, setBroadcastTitle] = useState('');
  const [broadcastMsg, setBroadcastMsg] = useState('');
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    const token = sessionStorage.getItem('admin_token');
    if (!token) { navigate('/admin', { replace: true }); return; }
    
    loadData();
    connectWebSocket(token);

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const connectWebSocket = (token: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/admin/ws?token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => setWsConnected(true);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'metrics_update') {
          setStats(data.metrics);
          setSystem(data.metrics.system);
        } else if (data.system) {
          // Fallback if initial payload structure differs
          setStats(data.metrics || data);
          setSystem(data.system);
        }
      } catch (e) {
        console.error("Failed to parse admin ws message", e);
      }
    };
    
    ws.onclose = () => {
      setWsConnected(false);
      setTimeout(() => connectWebSocket(token), 3000); // auto-reconnect
    };
    
    wsRef.current = ws;
  };

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersRes, actRes] = await Promise.all([
        adminApi.get('/api/v1/admin/users'),
        adminApi.get('/api/v1/admin/activity?limit=50'),
      ]);
      setUsers(usersRes.data.users || []);
      setActivity(actRes.data.activities || []);
    } catch (err: any) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        sessionStorage.removeItem('admin_token');
        navigate('/admin', { replace: true });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: string, email: string) => {
    if (!confirm(`Are you sure you want to permanently delete ${email}? This cannot be undone.`)) return;
    try {
      await adminApi.delete(`/api/v1/admin/users/${userId}`);
      setUsers(prev => prev.filter(u => u.id !== userId));
      showToast(`Deleted ${email}`);
    } catch { showToast('Failed to delete user', 'error'); }
  };

  const handleRoleChange = async (userId: string, role: string) => {
    try {
      await adminApi.put(`/api/v1/admin/users/${userId}/role`, { role });
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role } : u));
      showToast(`Role updated to ${role}`);
    } catch { showToast('Failed to update role', 'error'); }
  };

  const handleBroadcast = async () => {
    if (!broadcastTitle.trim() || !broadcastMsg.trim()) return;
    try {
      await adminApi.post('/api/v1/admin/broadcast', { title: broadcastTitle, message: broadcastMsg });
      showToast('Broadcast sent!');
      setShowBroadcast(false);
      setBroadcastTitle('');
      setBroadcastMsg('');
    } catch { showToast('Failed to send broadcast', 'error'); }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('admin_token');
    if (wsRef.current) wsRef.current.close();
    navigate('/admin', { replace: true });
  };

  const filteredUsers = users.filter(u =>
    u.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.full_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: BarChart3 },
    { id: 'users' as const, label: 'Users', icon: Users },
    { id: 'system' as const, label: 'System', icon: Server },
    { id: 'activity' as const, label: 'Activity', icon: Activity },
  ];

  const getActionIcon = (action: string) => {
    const map: Record<string, string> = {
      file_upload: '📁', message: '💬', model_train: '🤖', anomaly: '⚠️',
      report: '📊', join: '👋', reply: '💬', pin: '📌', broadcast: '📢',
    };
    return map[action] || '🔵';
  };

  if (loading && !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#05050A]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-sm font-medium tracking-wide">Initializing Enterprise Hub...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[#05050A] text-white selection:bg-red-500/30 font-sans">
      
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-red-900/10 blur-[150px] rounded-full mix-blend-screen" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-indigo-900/10 blur-[150px] rounded-full mix-blend-screen" />
      </div>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div initial={{ opacity: 0, y: -20, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -20, scale: 0.9 }}
            className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-4 rounded-2xl border backdrop-blur-xl shadow-2xl font-medium ${
              toast.type === 'success' 
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300' 
                : 'bg-red-500/10 border-red-500/20 text-red-300'
            }`}
          >
            {toast.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <div className="w-64 border-r border-gray-800/40 flex flex-col bg-[#0A0A10]/80 backdrop-blur-3xl relative z-10">
        <div className="p-6 border-b border-gray-800/40">
          <div className="flex items-center gap-4">
            <div className="p-2.5 rounded-2xl bg-gradient-to-br from-red-600 to-orange-600 shadow-[0_0_20px_rgba(220,38,38,0.3)]">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white tracking-wide">DataVision</h1>
              <p className="text-xs text-gray-400 font-medium">Enterprise Admin</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-red-500/10 to-transparent text-red-400 border border-red-500/20 shadow-[inset_0_0_20px_rgba(239,68,68,0.05)]'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <tab.icon className={`w-5 h-5 ${activeTab === tab.id ? 'text-red-400' : 'text-gray-500'}`} />
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800/40 space-y-2 bg-black/20">
          <div className="flex items-center gap-2 px-4 mb-4">
            <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]' : 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]'}`} />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              {wsConnected ? 'Live Connection' : 'Disconnected'}
            </span>
          </div>
          <button onClick={() => setShowBroadcast(true)}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium text-orange-400 hover:bg-orange-500/10 transition-all border border-orange-500/10">
            <div className="flex items-center gap-3"><Megaphone className="w-4 h-4" /> Broadcast</div>
          </button>
          <button onClick={handleLogout}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:text-white hover:bg-red-500/10 hover:border-red-500/20 transition-all border border-transparent">
            <div className="flex items-center gap-3"><LogOut className="w-4 h-4 text-red-400" /> Logout</div>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto relative z-10 scroll-smooth">
        <div className="p-10 max-w-[1600px] mx-auto">

          {/* ═══ OVERVIEW ═══ */}
          {activeTab === 'overview' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
              <div className="flex items-end justify-between">
                <div>
                  <h2 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">Enterprise Metrics</h2>
                  <p className="text-gray-400 mt-2 font-medium tracking-wide">Real-time pulse of your entire platform infrastructure.</p>
                </div>
                {wsConnected && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-sm font-semibold shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                    <Wifi className="w-4 h-4 animate-pulse" /> Live Streaming Active
                  </div>
                )}
              </div>

              {/* Top Dial Metrics */}
              {system && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <DialRing percentage={system.cpu} label="CPU Load" icon={Cpu} colorClass="text-blue-500" gradientFrom="from-blue-600" gradientTo="to-cyan-600" />
                  <DialRing percentage={system.ram} label="RAM Usage" icon={HardDrive} colorClass="text-purple-500" gradientFrom="from-purple-600" gradientTo="to-fuchsia-600" />
                  <DialRing percentage={system.disk} label="Storage" icon={Database} colorClass="text-emerald-500" gradientFrom="from-emerald-600" gradientTo="to-teal-600" />
                </div>
              )}

              {/* Modular Stats Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Module 1: Users & Collaboration */}
                <div className="bg-[#11111a]/80 backdrop-blur-xl border border-gray-800/60 rounded-3xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400"><Users className="w-5 h-5" /></div>
                    <h3 className="text-lg font-bold text-white">Users & Collaboration</h3>
                  </div>
                  <div className="space-y-5">
                    <div className="flex justify-between items-center border-b border-gray-800/40 pb-4">
                      <span className="text-gray-400 font-medium">Total Users</span>
                      <span className="text-2xl font-bold text-white"><AnimatedCounter value={stats?.users || 0} /></span>
                    </div>
                    <div className="flex justify-between items-center border-b border-gray-800/40 pb-4">
                      <span className="text-gray-400 font-medium">Total Conversations</span>
                      <span className="text-2xl font-bold text-white"><AnimatedCounter value={stats?.conversations || 0} /></span>
                    </div>
                    <div className="flex justify-between items-center pb-2">
                      <span className="text-gray-400 font-medium">Messages Sent</span>
                      <span className="text-2xl font-bold text-indigo-400"><AnimatedCounter value={stats?.messages || 0} /></span>
                    </div>
                  </div>
                </div>

                {/* Module 2: Data Intelligence */}
                <div className="bg-[#11111a]/80 backdrop-blur-xl border border-gray-800/60 rounded-3xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400"><BarChart3 className="w-5 h-5" /></div>
                    <h3 className="text-lg font-bold text-white">Data Intelligence</h3>
                  </div>
                  <div className="space-y-5">
                    <div className="flex justify-between items-center border-b border-gray-800/40 pb-4">
                      <span className="text-gray-400 font-medium">Files Processed</span>
                      <span className="text-2xl font-bold text-white"><AnimatedCounter value={stats?.files || 0} /></span>
                    </div>
                    <div className="flex justify-between items-center border-b border-gray-800/40 pb-4">
                      <span className="text-gray-400 font-medium">Data Pipelines</span>
                      <span className="text-2xl font-bold text-white"><AnimatedCounter value={stats?.data_connections || 0} /></span>
                    </div>
                    <div className="flex justify-between items-center pb-2">
                      <span className="text-gray-400 font-medium">Active Dashboards</span>
                      <span className="text-2xl font-bold text-emerald-400"><AnimatedCounter value={stats?.dashboards || 0} /></span>
                    </div>
                  </div>
                </div>

                {/* Module 3: Developer & APIs */}
                <div className="bg-[#11111a]/80 backdrop-blur-xl border border-gray-800/60 rounded-3xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-orange-500/10 rounded-xl text-orange-400"><Code className="w-5 h-5" /></div>
                    <h3 className="text-lg font-bold text-white">Developer Platform</h3>
                  </div>
                  <div className="space-y-5">
                    <div className="flex justify-between items-center border-b border-gray-800/40 pb-4">
                      <span className="text-gray-400 font-medium">AI Queries</span>
                      <span className="text-2xl font-bold text-white"><AnimatedCounter value={stats?.queries || 0} /></span>
                    </div>
                    <div className="flex justify-between items-center border-b border-gray-800/40 pb-4">
                      <span className="text-gray-400 font-medium">Active Webhooks</span>
                      <span className="text-2xl font-bold text-white"><AnimatedCounter value={stats?.active_webhooks || 0} /></span>
                    </div>
                    <div className="flex justify-between items-center pb-2">
                      <span className="text-gray-400 font-medium">API Requests/sec</span>
                      <span className="text-2xl font-bold text-orange-400">{stats?.api_requests_sec || '0.0'}</span>
                    </div>
                  </div>
                </div>

              </div>
            </motion.div>
          )}

          {/* ═══ USERS ═══ */}
          {activeTab === 'users' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-extrabold text-white">User Management</h2>
                  <p className="text-sm text-gray-400 mt-1">{users.length} registered users across the platform.</p>
                </div>
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                  <input
                    type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search by name or email..."
                    className="pl-12 pr-4 py-3 rounded-2xl bg-[#11111a]/80 backdrop-blur-xl border border-gray-800/60 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500/50 w-80 shadow-xl transition-all"
                  />
                </div>
              </div>

              <div className="bg-[#11111a]/80 backdrop-blur-xl border border-gray-800/60 rounded-3xl overflow-hidden shadow-2xl">
                <div className="grid grid-cols-[1fr_2fr_1fr_80px_80px_100px_80px] gap-4 px-6 py-4 border-b border-gray-800/60 text-xs font-bold text-gray-500 uppercase tracking-widest bg-black/20">
                  <span>Name</span><span>Email</span><span>Role</span><span className="text-center">Files</span><span className="text-center">Chats</span><span>Joined</span><span>Actions</span>
                </div>
                <div className="divide-y divide-gray-800/40 max-h-[600px] overflow-y-auto custom-scrollbar">
                  {filteredUsers.map((u, i) => (
                    <motion.div 
                      key={u.id} 
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}
                      className="grid grid-cols-[1fr_2fr_1fr_80px_80px_100px_80px] gap-4 px-6 py-4 items-center hover:bg-white/[0.03] transition-colors group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold shrink-0 shadow-lg">
                          {u.avatar}
                        </div>
                        <span className="text-sm text-gray-200 font-semibold truncate">{u.full_name || '—'}</span>
                      </div>
                      <span className="text-sm text-gray-400 font-medium truncate">{u.email}</span>
                      <div>
                        <select
                          value={u.role || 'authenticated'}
                          onChange={e => handleRoleChange(u.id, e.target.value)}
                          className="text-xs px-3 py-1.5 rounded-lg bg-black/40 border border-gray-700/50 text-gray-300 font-semibold focus:outline-none focus:border-indigo-500/50 cursor-pointer hover:bg-black/60 transition-colors"
                        >
                          <option value="authenticated">User</option>
                          <option value="admin">Admin</option>
                          <option value="banned">Banned</option>
                        </select>
                      </div>
                      <span className="text-sm text-gray-400 font-medium text-center">{u.file_count}</span>
                      <span className="text-sm text-gray-400 font-medium text-center">{u.conversation_count}</span>
                      <span className="text-xs text-gray-500 font-medium">{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</span>
                      <button
                        onClick={() => handleDeleteUser(u.id, u.email)}
                        className="opacity-0 group-hover:opacity-100 p-2 rounded-xl text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all ml-auto"
                        title="Delete user"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </motion.div>
                  ))}
                </div>
                {filteredUsers.length === 0 && (
                  <div className="p-16 text-center">
                    <UserX className="w-12 h-12 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500 font-medium">No users found matching your search.</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* ═══ SYSTEM ═══ */}
          {activeTab === 'system' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <div>
                <h2 className="text-3xl font-extrabold text-white">System Diagnostics</h2>
                <p className="text-sm text-gray-400 mt-1">Detailed infrastructure and database telemetry.</p>
              </div>

              <div className="bg-[#11111a]/80 backdrop-blur-xl border border-gray-800/60 rounded-3xl p-8 shadow-2xl">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                  {[
                    { label: 'CPU Cores', value: 'Live', icon: Cpu, color: 'text-indigo-400' },
                    { label: 'Platform OS', value: system?.platform?.split('-')[0] || 'Unknown', icon: Server, color: 'text-emerald-400' },
                    { label: 'Python Engine', value: system?.python_version || 'Unknown', icon: Code, color: 'text-blue-400' },
                    { label: 'Database Node', value: system?.db_status || 'Unknown', icon: Database, color: 'text-orange-400' },
                  ].map((item, i) => (
                    <div key={item.label} className="flex flex-col border-l border-gray-800/60 pl-6 first:border-0 first:pl-0">
                      <div className="flex items-center gap-2 mb-2">
                        <item.icon className={`w-4 h-4 ${item.color}`} />
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">{item.label}</span>
                      </div>
                      <span className="text-xl font-bold text-white tracking-wide">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* ═══ ACTIVITY ═══ */}
          {activeTab === 'activity' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <div>
                <h2 className="text-3xl font-extrabold text-white">Global Event Stream</h2>
                <p className="text-sm text-gray-400 mt-1">Live tracking of actions across the entire platform.</p>
              </div>

              <div className="bg-[#11111a]/80 backdrop-blur-xl border border-gray-800/60 rounded-3xl p-6 shadow-2xl">
                <div className="space-y-3">
                  {activity.map((a, i) => (
                    <motion.div
                      key={a.id || i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.02 }}
                      className="flex items-start gap-4 p-4 rounded-2xl bg-black/20 border border-gray-800/30 hover:border-gray-700/50 hover:bg-white/[0.02] transition-all group"
                    >
                      <div className="w-10 h-10 rounded-xl bg-gray-800/50 flex items-center justify-center text-lg shadow-inner group-hover:scale-110 transition-transform">
                        {getActionIcon(a.action)}
                      </div>
                      <div className="flex-1 min-w-0 pt-0.5">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-bold text-white">{a.user_name}</span>
                          {a.user_email && <span className="text-xs font-medium text-gray-500 px-2 py-0.5 rounded-md bg-white/5">{a.user_email}</span>}
                        </div>
                        <p className="text-sm text-gray-400 truncate font-medium">{a.detail}</p>
                      </div>
                      <span className="text-xs font-bold text-gray-600 bg-black/40 px-3 py-1 rounded-full border border-gray-800/50 mt-1">
                        {new Date(a.timestamp).toLocaleString()}
                      </span>
                    </motion.div>
                  ))}
                  {activity.length === 0 && (
                    <div className="p-16 text-center">
                      <Activity className="w-12 h-12 mx-auto mb-4 text-gray-700" />
                      <p className="text-gray-500 font-medium">No system events recorded yet.</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

        </div>
      </div>

      {/* Broadcast Modal */}
      <AnimatePresence>
        {showBroadcast && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center backdrop-blur-md bg-black/60 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-lg bg-[#11111a] border border-gray-800/60 rounded-3xl overflow-hidden shadow-2xl"
            >
              <div className="flex items-center justify-between p-6 border-b border-gray-800/60 bg-white/[0.01]">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-500/10 rounded-xl text-orange-400">
                    <Megaphone className="w-5 h-5" />
                  </div>
                  <h3 className="font-bold text-white text-lg tracking-wide">System Broadcast</h3>
                </div>
                <button onClick={() => setShowBroadcast(false)} className="p-2 rounded-xl hover:bg-white/10 text-gray-500 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-5">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Announcement Title</label>
                  <input value={broadcastTitle} onChange={e => setBroadcastTitle(e.target.value)} placeholder="e.g. Scheduled Maintenance"
                    className="w-full px-5 py-3 rounded-xl bg-black/40 border border-gray-700/50 text-white font-medium placeholder-gray-600 focus:outline-none focus:border-orange-500/50 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Message Body</label>
                  <textarea value={broadcastMsg} onChange={e => setBroadcastMsg(e.target.value)} placeholder="Type your broadcast message here..."
                    rows={4}
                    className="w-full px-5 py-3 rounded-xl bg-black/40 border border-gray-700/50 text-white font-medium placeholder-gray-600 focus:outline-none focus:border-orange-500/50 resize-none transition-colors"
                  />
                </div>
                <div className="pt-2">
                  <button onClick={handleBroadcast} disabled={!broadcastTitle.trim() || !broadcastMsg.trim()}
                    className="w-full py-4 rounded-xl font-bold text-white bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 disabled:opacity-50 disabled:grayscale transition-all shadow-[0_0_20px_rgba(249,115,22,0.3)] hover:shadow-[0_0_30px_rgba(249,115,22,0.5)]"
                  >
                    Send Platform Broadcast
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
