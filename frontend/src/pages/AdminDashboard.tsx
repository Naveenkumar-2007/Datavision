import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Users, FileText, MessageSquare, Activity, Database,
  Server, Trash2, Search, LogOut, BarChart3, Globe, Cpu,
  HardDrive, Clock, RefreshCw, UserX, UserCheck, ChevronDown,
  Megaphone, X, AlertTriangle, CheckCircle2
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

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'system' | 'activity'>('overview');
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [system, setSystem] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showBroadcast, setShowBroadcast] = useState(false);
  const [broadcastTitle, setBroadcastTitle] = useState('');
  const [broadcastMsg, setBroadcastMsg] = useState('');
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    const token = sessionStorage.getItem('admin_token');
    if (!token) { navigate('/admin', { replace: true }); return; }
    loadData();
  }, []);

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes, systemRes, actRes] = await Promise.all([
        adminApi.get('/api/v1/admin/stats'),
        adminApi.get('/api/v1/admin/users'),
        adminApi.get('/api/v1/admin/system'),
        adminApi.get('/api/v1/admin/activity?limit=50'),
      ]);
      setStats(statsRes.data.stats);
      setUsers(usersRes.data.users || []);
      setSystem(systemRes.data.system);
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

  const statCards = stats ? [
    { label: 'Total Users', value: stats.total_users, icon: Users, color: 'from-blue-600 to-indigo-700', border: 'border-blue-500/20' },
    { label: 'Total Files', value: stats.total_files, icon: FileText, color: 'from-emerald-600 to-teal-700', border: 'border-emerald-500/20' },
    { label: 'Conversations', value: stats.total_conversations, icon: MessageSquare, color: 'from-purple-600 to-violet-700', border: 'border-purple-500/20' },
    { label: 'AI Queries', value: stats.total_queries, icon: Activity, color: 'from-orange-600 to-amber-700', border: 'border-orange-500/20' },
    { label: 'Active Today', value: stats.active_today, icon: Globe, color: 'from-cyan-600 to-sky-700', border: 'border-cyan-500/20' },
    { label: 'New This Week', value: stats.new_users_this_week, icon: UserCheck, color: 'from-pink-600 to-rose-700', border: 'border-pink-500/20' },
    { label: 'Data Pipelines', value: stats.data_connections, icon: Database, color: 'from-red-600 to-rose-700', border: 'border-red-500/20' },
    { label: 'Dashboards', value: stats.dashboards, icon: BarChart3, color: 'from-yellow-600 to-amber-700', border: 'border-yellow-500/20' },
  ] : [];

  const getActionIcon = (action: string) => {
    const map: Record<string, string> = {
      file_upload: '📁', message: '💬', model_train: '🤖', anomaly: '⚠️',
      report: '📊', join: '👋', reply: '💬', pin: '📌', broadcast: '📢',
    };
    return map[action] || '🔵';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#080810' }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-sm">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex" style={{ background: '#080810' }}>
      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
            className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium shadow-2xl ${
              toast.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'
            }`}
          >
            {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <div className="w-64 border-r border-gray-800/50 flex flex-col bg-[#0a0a12]">
        <div className="p-5 border-b border-gray-800/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-red-600/20 to-orange-600/20 border border-red-500/20">
              <Shield className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <h1 className="font-bold text-white text-sm">Admin Panel</h1>
              <p className="text-[11px] text-gray-500">DataVision Platform</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-800/50 space-y-1">
          <button onClick={() => setShowBroadcast(true)}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-gray-400 hover:text-orange-400 hover:bg-orange-500/5 transition-all">
            <Megaphone className="w-4 h-4" /> Broadcast
          </button>
          <button onClick={loadData}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-gray-400 hover:text-blue-400 hover:bg-blue-500/5 transition-all">
            <RefreshCw className="w-4 h-4" /> Refresh Data
          </button>
          <button onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-gray-400 hover:text-red-400 hover:bg-red-500/5 transition-all">
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-8 max-w-7xl mx-auto">

          {/* ═══ OVERVIEW ═══ */}
          {activeTab === 'overview' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Platform Overview</h2>
                <p className="text-sm text-gray-500 mt-1">Real-time platform analytics and metrics</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {statCards.map((card, i) => (
                  <motion.div
                    key={card.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className={`p-5 rounded-2xl border ${card.border} bg-[#0d0d15] relative overflow-hidden group hover:border-opacity-50 transition-all`}
                  >
                    <div className={`absolute inset-0 bg-gradient-to-br ${card.color} opacity-[0.03] group-hover:opacity-[0.06] transition-opacity`} />
                    <div className="relative z-10">
                      <div className="flex items-center justify-between mb-3">
                        <card.icon className="w-5 h-5 text-gray-500" />
                      </div>
                      <div className="text-3xl font-bold text-white">
                        <AnimatedCounter value={card.value} />
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{card.label}</div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Recent Activity Preview */}
              <div className="bg-[#0d0d15] border border-gray-800/50 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
                <div className="space-y-3">
                  {activity.slice(0, 5).map((a, i) => (
                    <div key={a.id || i} className="flex items-center gap-3 text-sm">
                      <span className="text-lg">{getActionIcon(a.action)}</span>
                      <span className="text-gray-300 font-medium">{a.user_name}</span>
                      <span className="text-gray-500">—</span>
                      <span className="text-gray-400 flex-1 truncate">{a.detail}</span>
                      <span className="text-gray-600 text-xs shrink-0">{new Date(a.timestamp).toLocaleTimeString()}</span>
                    </div>
                  ))}
                  {activity.length === 0 && <p className="text-gray-600 text-sm">No activity recorded yet.</p>}
                </div>
              </div>
            </motion.div>
          )}

          {/* ═══ USERS ═══ */}
          {activeTab === 'users' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">User Management</h2>
                  <p className="text-sm text-gray-500 mt-1">{users.length} registered users</p>
                </div>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                  <input
                    type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search users..."
                    className="pl-10 pr-4 py-2.5 rounded-xl bg-[#0d0d15] border border-gray-800/50 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-red-500/30 w-72"
                  />
                </div>
              </div>

              <div className="bg-[#0d0d15] border border-gray-800/50 rounded-2xl overflow-hidden">
                <div className="grid grid-cols-[1fr_2fr_1fr_80px_80px_100px_80px] gap-4 px-5 py-3 border-b border-gray-800/50 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <span>Name</span><span>Email</span><span>Role</span><span>Files</span><span>Chats</span><span>Joined</span><span>Actions</span>
                </div>
                <div className="divide-y divide-gray-800/30 max-h-[600px] overflow-y-auto">
                  {filteredUsers.map(u => (
                    <div key={u.id} className="grid grid-cols-[1fr_2fr_1fr_80px_80px_100px_80px] gap-4 px-5 py-3 items-center hover:bg-white/[0.02] transition-colors group">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center text-white text-xs font-bold shrink-0">
                          {u.avatar}
                        </div>
                        <span className="text-sm text-white font-medium truncate">{u.full_name || '—'}</span>
                      </div>
                      <span className="text-sm text-gray-400 truncate">{u.email}</span>
                      <div>
                        <select
                          value={u.role || 'authenticated'}
                          onChange={e => handleRoleChange(u.id, e.target.value)}
                          className="text-xs px-2 py-1 rounded-lg bg-transparent border border-gray-700/50 text-gray-300 focus:outline-none focus:border-red-500/30 cursor-pointer"
                        >
                          <option value="authenticated">User</option>
                          <option value="admin">Admin</option>
                          <option value="banned">Banned</option>
                        </select>
                      </div>
                      <span className="text-sm text-gray-500 text-center">{u.file_count}</span>
                      <span className="text-sm text-gray-500 text-center">{u.conversation_count}</span>
                      <span className="text-xs text-gray-600">{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</span>
                      <button
                        onClick={() => handleDeleteUser(u.id, u.email)}
                        className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
                        title="Delete user"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
                {filteredUsers.length === 0 && (
                  <div className="p-12 text-center text-gray-600">
                    <UserX className="w-10 h-10 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No users found.</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* ═══ SYSTEM ═══ */}
          {activeTab === 'system' && system && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white">System Health</h2>
                <p className="text-sm text-gray-500 mt-1">Infrastructure monitoring and diagnostics</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  { label: 'CPU Usage', value: `${system.cpu_usage_percent}%`, icon: Cpu, color: system.cpu_usage_percent > 80 ? 'text-red-400' : 'text-emerald-400' },
                  { label: 'Memory', value: `${system.memory_used_gb}/${system.memory_total_gb} GB (${system.memory_percent}%)`, icon: HardDrive, color: system.memory_percent > 80 ? 'text-red-400' : 'text-emerald-400' },
                  { label: 'Disk', value: `${system.disk_used_gb}/${system.disk_total_gb} GB (${system.disk_percent}%)`, icon: Database, color: system.disk_percent > 80 ? 'text-red-400' : 'text-emerald-400' },
                  { label: 'Database', value: system.db_status, icon: Server, color: system.db_status === 'connected' ? 'text-emerald-400' : 'text-red-400' },
                  { label: 'Python', value: system.python_version, icon: Globe, color: 'text-blue-400' },
                  { label: 'Environment', value: system.environment, icon: Clock, color: system.environment === 'production' ? 'text-orange-400' : 'text-blue-400' },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="p-5 rounded-2xl bg-[#0d0d15] border border-gray-800/50"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <item.icon className={`w-5 h-5 ${item.color}`} />
                      <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">{item.label}</span>
                    </div>
                    <p className={`text-lg font-semibold ${item.color}`}>{item.value}</p>
                  </motion.div>
                ))}
              </div>

              <div className="bg-[#0d0d15] border border-gray-800/50 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Platform Info</h3>
                <p className="text-sm text-gray-400">{system.platform}</p>
                <p className="text-sm text-gray-500 mt-1">Status: <span className="text-emerald-400">{system.uptime}</span></p>
              </div>
            </motion.div>
          )}

          {/* ═══ ACTIVITY ═══ */}
          {activeTab === 'activity' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Global Activity Feed</h2>
                <p className="text-sm text-gray-500 mt-1">All actions across the entire platform</p>
              </div>

              <div className="bg-[#0d0d15] border border-gray-800/50 rounded-2xl p-6">
                <div className="space-y-2">
                  {activity.map((a, i) => (
                    <motion.div
                      key={a.id || i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.02 }}
                      className="flex items-start gap-3 p-3 rounded-xl hover:bg-white/[0.02] transition-colors"
                    >
                      <span className="text-lg mt-0.5">{getActionIcon(a.action)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-white">{a.user_name}</span>
                          {a.user_email && <span className="text-xs text-gray-600">({a.user_email})</span>}
                        </div>
                        <p className="text-sm text-gray-400 mt-0.5 truncate">{a.detail}</p>
                      </div>
                      <span className="text-xs text-gray-600 shrink-0 mt-1">
                        {new Date(a.timestamp).toLocaleString()}
                      </span>
                    </motion.div>
                  ))}
                  {activity.length === 0 && (
                    <div className="p-12 text-center text-gray-600">
                      <Activity className="w-10 h-10 mx-auto mb-3 opacity-30" />
                      <p className="text-sm">No activity recorded yet.</p>
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
          <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm bg-black/60 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-[#0d0d15] border border-gray-800/50 rounded-2xl overflow-hidden shadow-2xl"
            >
              <div className="flex items-center justify-between p-5 border-b border-gray-800/50">
                <div className="flex items-center gap-2">
                  <Megaphone className="w-5 h-5 text-orange-400" />
                  <h3 className="font-bold text-white">System Broadcast</h3>
                </div>
                <button onClick={() => setShowBroadcast(false)} className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500"><X className="w-4 h-4" /></button>
              </div>
              <div className="p-5 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5">Title</label>
                  <input value={broadcastTitle} onChange={e => setBroadcastTitle(e.target.value)} placeholder="Scheduled Maintenance"
                    className="w-full px-4 py-2.5 rounded-xl bg-[#1a1a2e] border border-gray-700/50 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-orange-500/30"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5">Message</label>
                  <textarea value={broadcastMsg} onChange={e => setBroadcastMsg(e.target.value)} placeholder="We'll be performing maintenance at..."
                    rows={3}
                    className="w-full px-4 py-2.5 rounded-xl bg-[#1a1a2e] border border-gray-700/50 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-orange-500/30 resize-none"
                  />
                </div>
                <button onClick={handleBroadcast} disabled={!broadcastTitle.trim() || !broadcastMsg.trim()}
                  className="w-full py-3 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 disabled:opacity-50 transition-all"
                >
                  Send Broadcast
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
