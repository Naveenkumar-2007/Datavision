import React, { useState, useEffect, useRef } from 'react';
import { useUserStore } from '@/store/userStore';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Users, 
  MessageSquare, 
  Send, 
  Share2, 
  Sparkles,
  Link,
  Plus,
  Paperclip,
  CheckCircle2,
  Brain,
  Hash,
  X,
  Copy,
  Mail,
  BarChart3,
  Database,
  TrendingUp,
  LineChart,
  Activity,
  Smile,
  Reply,
  MoreVertical,
  ShieldAlert,
  ChevronRight,
  Pin
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

import { api } from '@/services/api';
import { ChatCrypto } from '@/utils/crypto';
import { Lock, Unlock, Search, Image as ImageIcon, FileAudio } from 'lucide-react';

const DecryptedMessage = ({ msg, channelKey }: { msg: any, channelKey: string }) => {
  const [decrypted, setDecrypted] = useState(msg.is_encrypted ? 'Decrypting...' : msg.message);
  
  useEffect(() => {
    if (msg.is_encrypted) {
      ChatCrypto.decryptMessage(msg.message, channelKey).then(setDecrypted);
    } else {
      setDecrypted(msg.message);
    }
  }, [msg, channelKey]);

  return <span>{decrypted}</span>;
};

const Collaborate: React.FC = () => {
  const { isDark } = useUserStore();
  const { user } = useAuth();
  const [channels, setChannels] = useState<any[]>([]);
  const [activeChannel, setActiveChannel] = useState('default');
  const [comments, setComments] = useState<any[]>([]);
  const [members, setMembers] = useState<any[]>([]);
  const [newComment, setNewComment] = useState('');
  
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [isSecureMode, setIsSecureMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Modals state
  const [showChannelModal, setShowChannelModal] = useState(false);
  const [newChannelName, setNewChannelName] = useState('');
  
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteName, setInviteName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Viewer');
  
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Enterprise Features State
  const [activeTab, setActiveTab] = useState<'members' | 'activity'>('members');
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [reactions, setReactions] = useState<Record<string, Record<string, string[]>>>({});
  const [replies, setReplies] = useState<Record<string, any[]>>({});
  const [replyingTo, setReplyingTo] = useState<any>(null);
  const [showEmojiPicker, setShowEmojiPicker] = useState<string | null>(null);

  const triggerToast = (msg: string) => {
    setToastMessage(msg);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  // Initial Data Fetch
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [channelsRes, membersRes, rolesRes, activityRes] = await Promise.all([
          api.get('/api/v1/collaboration/channels'),
          api.get('/api/v1/collaboration/members'),
          api.get('/api/v1/collaboration/roles'),
          api.get('/api/v1/collaboration/activity-feed')
        ]);
        setChannels(channelsRes.data?.channels || []);
        setMembers(membersRes.data?.members || []);
        setRoles(rolesRes.data?.roles || []);
        setActivityFeed(activityRes.data?.activities || []);
      } catch (err) {
        console.error("Failed to load initial data", err);
      }
    };
    fetchData();
  }, []);

  // Fetch threads when active channel changes
  useEffect(() => {
    const fetchThreads = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/api/v1/collaboration/threads?channel_id=${activeChannel}`);
        setComments(res.data?.threads || []);
      } catch (err) {
        console.error("Failed to load threads", err);
      } finally {
        setLoading(false);
      }
    };
    fetchThreads();
    
    // Connect WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/collaboration/ws/${activeChannel}?user_name=${user?.full_name || 'Anonymous'}&user_id=${user?.id || 'default'}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.message) {
          // It's a structured message from our backend
          const msg = {
            id: data.id || Date.now() + Math.random(),
            user: data.user || 'Unknown',
            avatar: data.avatar || (data.user ? data.user.charAt(0).toUpperCase() : 'U'),
            message: data.message,
            time: data.time || 'Just now',
            isAi: data.isAi || false,
            chart_data: data.chart_data || null,
            chart_type: data.chart_type || null
          };
          setComments(prev => {
            if (prev.find(p => p.id === msg.id)) return prev;
            return [...prev, msg];
          });
        }
      } catch (e) {
        console.error('Failed to parse WS msg', e);
      }
    };

    return () => {
      ws.close();
    };
  }, [activeChannel]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [comments, posting]);

  const handlePostComment = async () => {
    if (!newComment.trim() || posting) return;
    setPosting(true);
    
    const inputVal = newComment.trim();
    
    let finalMessage = inputVal;
    let isEncrypted = false;
    
    // Auto-bypass E2E for @ai mentions so the backend can process it
    const shouldEncrypt = isSecureMode && !inputVal.toLowerCase().includes('@ai');
    
    if (shouldEncrypt) {
      finalMessage = await ChatCrypto.encryptMessage(inputVal, activeChannel);
      isEncrypted = true;
    }

    if (replyingTo) {
      try {
        const res = await api.post(`/api/v1/collaboration/threads/${replyingTo.id}/reply`, {
          message: finalMessage,
          user: user?.full_name || (user?.full_name || 'Anonymous'),
          is_encrypted: isEncrypted
        });
        if (res.data.success) {
          setReplies(prev => ({
            ...prev,
            [replyingTo.id]: [...(prev[replyingTo.id] || []), res.data.reply]
          }));
        }
      } catch (e) { console.error('Failed to reply', e); }
      setReplyingTo(null);
    } else {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ 
          message: finalMessage, 
          user: user?.full_name || (user?.full_name || 'Anonymous'),
          is_encrypted: isEncrypted
        }));
      }
    }
    
    setNewComment('');
    setPosting(false);
  };

  const handleReact = async (msgId: string, emoji: string) => {
    try {
      const res = await api.post(`/api/v1/collaboration/threads/${msgId}/react`, {
        emoji,
        user: user?.full_name || (user?.full_name || 'Anonymous')
      });
      if (res.data.success) {
        setReactions(prev => ({ ...prev, [msgId]: res.data.reactions }));
      }
    } catch (e) { console.error('Reaction failed', e); }
    setShowEmojiPicker(null);
  };

  const handleChangeRole = async (email: string, role: string) => {
    try {
      const res = await api.put('/api/v1/collaboration/members/role', { email, role });
      if (res.data.success) {
        setMembers(prev => prev.map(m => m.email === email ? { ...m, role } : m));
        triggerToast(`Role updated to ${role}`);
      }
    } catch (e) { console.error('Failed to update role', e); }
  };

  const handleCreateChannel = async () => {
    if (!newChannelName.trim()) return;
    try {
      const res = await api.post('/api/v1/collaboration/channels', { name: newChannelName.trim() });
      const data = res.data;
      if (data.success) {
        setChannels(prev => [...prev, data.channel]);
        setActiveChannel(data.channel.id);
        setShowChannelModal(false);
        setNewChannelName('');
        triggerToast(`Channel #${data.channel.name} created successfully.`);
      } else {
        triggerToast(data.detail || "Error creating channel.");
      }
    } catch (err) {
      console.error("Error creating channel", err);
    }
  };

  const handleCopyLink = async () => {
    try {
      const res = await api.post('/api/v1/collaboration/invite');
      const data = res.data;
      if (data.success) {
        const fullLink = `${window.location.origin}${data.link}`;
        navigator.clipboard.writeText(fullLink);
        triggerToast("Secure invite link copied to clipboard!");
      }
    } catch (err) {
      console.error("Error generating link", err);
    }
  };

  const handleAddMember = async () => {
    if (!inviteName.trim() || !inviteEmail.trim()) return;
    try {
      const res = await api.post('/api/v1/collaboration/members', { name: inviteName, email: inviteEmail, role: inviteRole });
      const data = res.data;
      if (data.success) {
        setMembers(prev => [...prev, data.member]);
        setShowInviteModal(false);
        setInviteName('');
        setInviteEmail('');
        triggerToast(data.message);
      }
    } catch (err) {
      console.error("Error adding member", err);
    }
  };

  const activeChannelName = channels.find(c => c.id === activeChannel)?.name || 'general';

  return (
    <div className="p-3 sm:p-6 space-y-4 sm:space-y-6 max-w-7xl mx-auto min-h-[calc(100vh-80px)] flex flex-col relative">
      
      {/* Toast Notification */}
      <AnimatePresence>
        {showToast && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-0 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl bg-emerald-500 text-white font-semibold text-sm shadow-xl flex items-center gap-2"
          >
            <CheckCircle2 className="w-4 h-4" /> {toastMessage}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shrink-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
            👥 Collaboration Hub
          </h2>
          <p className="text-sm mt-1" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
            Coordinate with your team, and tag <span className="text-indigo-400 font-semibold">@ai</span> for real automated insights from your data.
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => setShowChannelModal(true)}
            className={`px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 border transition-all ${
            isDark ? 'border-white/10 hover:bg-white/5 text-gray-200' : 'border-gray-200 hover:bg-gray-50 text-gray-700'
          }`}>
            <Plus className="w-4 h-4" /> New Channel
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
        
        {/* Discussion Area */}
        <div className={`lg:col-span-3 rounded-3xl border flex flex-col overflow-hidden relative shadow-lg ${
          isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-200/60'
        }`}>
          {/* Chat Header */}
          <div className="p-4 border-b flex items-center justify-between shrink-0" style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
             <div className="flex items-center gap-2">
               <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
               <h3 className="font-semibold text-sm flex items-center gap-1">
                 <Hash className="w-4 h-4 text-gray-400" /> {activeChannelName}
               </h3>
             </div>
             <div className="flex gap-2">
               {channels.map(c => (
                 <button 
                   key={c.id}
                   onClick={() => setActiveChannel(c.id)}
                   className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                     activeChannel === c.id 
                       ? 'bg-indigo-600 text-white' 
                       : isDark ? 'bg-white/5 text-gray-400 hover:text-gray-200' : 'bg-gray-100 text-gray-500 hover:text-gray-700'
                   }`}
                 >
                   #{c.name}
                 </button>
               ))}
             </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4 sm:space-y-6">
            {loading ? (
               <div className="flex justify-center items-center h-full">
                 <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
               </div>
            ) : (
              <AnimatePresence initial={false}>
                {comments.map((c, i) => (
                  <motion.div 
                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.3 }}
                    key={c.id} 
                    className={`flex items-start gap-3 sm:gap-4 max-w-full sm:max-w-[85%] ${c.user === (user?.full_name || 'Anonymous') ? 'ml-auto flex-row-reverse' : ''}`}
                  >
                    <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-xl sm:rounded-2xl flex items-center justify-center font-bold text-xs sm:text-sm shrink-0 shadow-md ${
                      c.isAi ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white' : 
                      c.user === (user?.full_name || 'Anonymous') ? 'bg-gradient-to-br from-emerald-400 to-teal-500 text-white' : 
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {c.isAi ? <Brain className="w-5 h-5"/> : c.avatar}
                    </div>
                    
                    <div className={`space-y-1.5 ${c.user === (user?.full_name || 'Anonymous') ? 'items-end flex flex-col' : ''}`}>
                      <div className={`flex items-center gap-2 ${c.user === (user?.full_name || 'Anonymous') ? 'flex-row-reverse' : ''}`}>
                        <span className="text-xs font-bold" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>{c.user}</span>
                        <span className="text-[10px] text-gray-500">{c.time === 'Just now' ? c.time : new Date(c.time || c.id).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                      </div>
                      
                      <div className="relative group">
                        <div className={`p-4 rounded-2xl shadow-sm text-sm whitespace-pre-wrap ${
                          c.user === (user?.full_name || 'Anonymous') 
                            ? 'bg-indigo-600 text-white rounded-tr-sm' 
                            : isDark 
                              ? 'bg-white/5 border border-white/10 text-gray-200 rounded-tl-sm' 
                              : 'bg-gray-50 border border-gray-100 text-gray-800 rounded-tl-sm'
                        }`}>
                          {c.message}
                        </div>
                        
                        {/* Message Actions Hover */}
                        <div className={`absolute ${c.user === (user?.full_name || 'Anonymous') ? '-left-16' : '-right-16'} top-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1`}>
                          <button onClick={() => setReplyingTo(c)} className="p-1.5 rounded-lg bg-gray-500/20 hover:bg-gray-500/40 text-gray-400 transition-colors" title="Reply">
                            <Reply className="w-3.5 h-3.5" />
                          </button>
                          <div className="relative">
                            <button onClick={() => setShowEmojiPicker(showEmojiPicker === c.id ? null : c.id)} className="p-1.5 rounded-lg bg-gray-500/20 hover:bg-gray-500/40 text-gray-400 transition-colors" title="React">
                              <Smile className="w-3.5 h-3.5" />
                            </button>
                            {showEmojiPicker === c.id && (
                              <div className="absolute top-8 left-0 flex bg-white dark:bg-zinc-800 border dark:border-white/10 rounded-xl shadow-xl p-1 z-10">
                                {['👍', '🔥', '🚀', '👀', '✅'].map(emoji => (
                                  <button key={emoji} onClick={() => handleReact(c.id, emoji)} className="p-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg text-base">
                                    {emoji}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Reactions Display */}
                      {reactions[c.id] && Object.keys(reactions[c.id]).length > 0 && (
                        <div className={`flex flex-wrap gap-1 mt-1 ${c.user === (user?.full_name || 'Anonymous') ? 'justify-end' : ''}`}>
                          {Object.entries(reactions[c.id]).map(([emoji, users]) => (
                            <button key={emoji} onClick={() => handleReact(c.id, emoji)} className={`px-2 py-0.5 rounded-full text-[11px] border flex items-center gap-1 ${
                              users.includes((user?.full_name || 'Anonymous')) 
                                ? 'bg-indigo-500/20 border-indigo-500/30 text-indigo-400' 
                                : isDark ? 'bg-white/5 border-white/10 text-gray-400' : 'bg-gray-100 border-gray-200 text-gray-500'
                            }`}>
                              <span>{emoji}</span> <span>{users.length}</span>
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Replies Display */}
                      {replies[c.id] && replies[c.id].length > 0 && (
                        <div className={`mt-2 pl-4 border-l-2 ${isDark ? 'border-indigo-500/30' : 'border-indigo-200'} space-y-2 w-full`}>
                          {replies[c.id].map(r => (
                            <div key={r.id} className="flex gap-2 text-sm">
                              <div className="w-5 h-5 rounded-md bg-gradient-to-br from-emerald-400 to-teal-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                                {r.avatar}
                              </div>
                              <div className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                                <span className="font-bold text-[11px] mr-2" style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}>{r.user}</span>
                                <span className="text-[13px]">{r.message}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Rich Media Charts (Inline) */}
                      {c.chart_data && (
                        <div className={`mt-2 p-4 rounded-2xl border shadow-lg ${isDark ? 'bg-black/40 border-indigo-500/30' : 'bg-white border-indigo-200'}`} style={{ width: '100%', minWidth: '300px', height: '250px' }}>
                          <h4 className="text-xs font-bold mb-2 flex items-center gap-1" style={{ color: isDark ? '#a5b4fc' : '#4f46e5' }}>
                            <BarChart3 className="w-4 h-4" /> Data Visualization
                          </h4>
                          <ResponsiveContainer width="100%" height="100%">
                            {c.chart_type === 'bar' ? (
                              <BarChart data={c.chart_data}>
                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#333' : '#e5e7eb'} vertical={false} />
                                <XAxis dataKey="name" stroke={isDark ? '#6b7280' : '#9ca3af'} fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke={isDark ? '#6b7280' : '#9ca3af'} fontSize={10} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{ backgroundColor: isDark ? '#1f2937' : '#fff', borderRadius: '8px', border: 'none' }} />
                                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                              </BarChart>
                            ) : (
                              <RechartsLineChart data={c.chart_data}>
                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#333' : '#e5e7eb'} vertical={false} />
                                <XAxis dataKey="name" stroke={isDark ? '#6b7280' : '#9ca3af'} fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke={isDark ? '#6b7280' : '#9ca3af'} fontSize={10} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{ backgroundColor: isDark ? '#1f2937' : '#fff', borderRadius: '8px', border: 'none' }} />
                                <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={3} dot={{ r: 4 }} />
                              </RechartsLineChart>
                            )}
                          </ResponsiveContainer>
                        </div>
                      )}

                      {c.chartRef && (
                        <div className={`flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-lg border w-fit ${
                          isDark ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-300' : 'bg-indigo-50 border-indigo-100 text-indigo-600'
                        }`}>
                          <Link className="w-3 h-3" /> Referenced System
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
            
            {posting && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start gap-4 max-w-[85%] ml-auto flex-row-reverse">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 text-white flex items-center justify-center font-bold text-sm shrink-0 opacity-50 shadow-md">N</div>
                <div className="bg-indigo-600/50 p-4 rounded-2xl rounded-tr-sm h-12 w-16 animate-pulse"></div>
              </motion.div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* New comment input */}
          <div className="p-4 border-t bg-black/5 shrink-0" style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
            <div className={`flex items-center gap-2 p-2 rounded-2xl border transition-shadow focus-within:shadow-lg focus-within:shadow-indigo-500/10 ${
              isDark ? 'bg-zinc-900 border-white/10' : 'bg-white border-gray-200'
            }`}>
              <button className="p-2 text-gray-400 hover:text-indigo-400 transition-colors">
                <Paperclip className="w-5 h-5" />
              </button>
              {replyingTo && (
                <div className={`absolute bottom-full left-0 w-full p-2 border-t flex justify-between items-center text-xs ${isDark ? 'bg-zinc-800 border-white/10 text-gray-300' : 'bg-gray-100 border-gray-200 text-gray-600'}`}>
                  <span>Replying to <span className="font-bold">{replyingTo.user}</span>: {replyingTo.message.substring(0, 30)}...</span>
                  <button onClick={() => setReplyingTo(null)} className="p-1 hover:bg-black/10 rounded"><X className="w-4 h-4"/></button>
                </div>
              )}
              <input 
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handlePostComment()}
                placeholder={replyingTo ? "Write a reply..." : "Message team or tag @ai for insights from your data..."}
                className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-sm px-2"
                style={{ color: isDark ? 'white' : 'black' }}
              />
              <button 
                onClick={handlePostComment}
                disabled={!newComment.trim() || posting}
                className="p-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50 disabled:hover:bg-indigo-600 transition-all shadow-md"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <div className="text-[10px] text-gray-500 mt-2 px-4 flex justify-between">
              <span>Pro tip: Tag <strong className="text-indigo-400">@ai</strong> and ask "what are the top trends?" to analyze your uploaded data.</span>
              <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-500"/> E2E Encrypted</span>
            </div>
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6 flex flex-col">
          <div className={`p-6 rounded-3xl border ${isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-200/60 shadow-sm'}`}>
            <h3 className="font-semibold text-sm flex items-center gap-2 mb-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
              <Database className="w-4 h-4 text-teal-400" /> Active Dataset Context
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              Current dataset analyzed by the AI Swarm.
            </p>
            <div className={`p-3 rounded-xl border mb-4 text-xs font-mono space-y-2 ${isDark ? 'bg-black/50 border-white/10 text-gray-300' : 'bg-gray-50 border-gray-200 text-gray-600'}`}>
              <div className="flex justify-between items-center"><span className="text-indigo-400">customer_id</span> <span className="text-gray-500">string</span></div>
              <div className="flex justify-between items-center"><span className="text-emerald-400">monthly_charges</span> <span className="text-gray-500">float64</span></div>
              <div className="flex justify-between items-center"><span className="text-purple-400">churn_status</span> <span className="text-gray-500">boolean</span></div>
              <div className="flex justify-between items-center"><span className="text-amber-400">tenure_months</span> <span className="text-gray-500">int64</span></div>
              <div className="pt-2 mt-2 border-t border-dashed border-gray-500/30 text-center text-[10px]">14 more columns...</div>
            </div>
            <div className="space-y-2">
              <button 
                onClick={handleCopyLink}
                className={`w-full py-2.5 px-4 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                isDark ? 'border-white/10 hover:bg-white/5 text-gray-200' : 'border-gray-200 hover:bg-gray-50 text-gray-700'
              }`}>
                <Copy className="w-4 h-4" /> Share Workspace Link
              </button>
            </div>
          </div>

          <div className={`rounded-3xl border flex flex-col flex-1 overflow-hidden ${isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-200/60 shadow-sm'}`}>
            <div className={`flex border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
              <button 
                onClick={() => setActiveTab('members')}
                className={`flex-1 py-3 text-xs font-bold uppercase tracking-widest ${activeTab === 'members' ? (isDark ? 'text-white border-b-2 border-indigo-500' : 'text-indigo-600 border-b-2 border-indigo-500') : 'text-gray-500 hover:bg-white/5'}`}
              >
                Members ({members.length})
              </button>
              <button 
                onClick={() => setActiveTab('activity')}
                className={`flex-1 py-3 text-xs font-bold uppercase tracking-widest ${activeTab === 'activity' ? (isDark ? 'text-white border-b-2 border-indigo-500' : 'text-indigo-600 border-b-2 border-indigo-500') : 'text-gray-500 hover:bg-white/5'}`}
              >
                Activity
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === 'members' ? (
                <div className="space-y-3">
                  {members.map((m, i) => (
                    <div key={i} className={`flex items-center gap-3 p-2.5 rounded-xl border transition-colors ${isDark ? 'bg-black/20 border-white/5 hover:border-white/10' : 'bg-gray-50 border-gray-100 hover:border-gray-200'}`}>
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold shadow-md text-white shrink-0 ${
                        m.name === 'DataVision AI' ? 'bg-gradient-to-br from-indigo-500 to-purple-600' : 'bg-gradient-to-br from-emerald-400 to-teal-500'
                      }`}>
                        {m.name === 'DataVision AI' ? <Sparkles className="w-5 h-5"/> : m.avatar}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm truncate" style={{ color: isDark ? 'white' : 'black' }}>
                          {m.name} {m.name === (user?.full_name || 'Anonymous') && <span className="text-gray-500 font-normal">(You)</span>}
                        </p>
                        <p className={`text-[11px] font-medium ${m.status === 'Online' || m.status === 'Active' ? 'text-emerald-500' : 'text-gray-400'}`}>
                          {m.status}
                        </p>
                      </div>
                      {/* RBAC Role Selector */}
                      {m.name !== 'DataVision AI' && (
                        <select 
                          value={m.role}
                          onChange={(e) => handleChangeRole(m.email, e.target.value)}
                          className={`text-[10px] font-bold px-2 py-1 rounded-lg border outline-none ${
                            isDark ? 'bg-black/50 border-white/10 text-gray-300' : 'bg-white border-gray-200 text-gray-700'
                          }`}
                        >
                          {roles.map(r => (
                            <option key={r.name} value={r.name}>{r.name}</option>
                          ))}
                        </select>
                      )}
                      {m.name === 'DataVision AI' && (
                        <div className="text-[10px] font-bold px-2 py-1 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">Agent</div>
                      )}
                    </div>
                  ))}
                  <button 
                    onClick={() => setShowInviteModal(true)}
                    className="w-full mt-4 py-2 rounded-xl border border-dashed border-indigo-500/50 text-indigo-400 text-xs font-bold hover:bg-indigo-500/10 transition-colors"
                  >
                    + Invite Member
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="text-xs text-gray-500 mb-2 font-bold uppercase tracking-wider pl-2">Platform Activity Feed</div>
                  <div className="relative border-l border-gray-200 dark:border-white/10 ml-4 space-y-6 pb-4">
                    {activityFeed.map((activity, idx) => (
                      <div key={idx} className="relative pl-6">
                        <div className="absolute -left-1.5 top-1 w-3 h-3 rounded-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)] border-2 border-white dark:border-zinc-900" />
                        <div className="text-xs">
                          <p className="font-bold" style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}>{activity.user_name} <span className="font-normal text-gray-500">{activity.action.replace('_', ' ')}</span></p>
                          <p className="text-gray-500 mt-1">{activity.detail}</p>
                          <p className="text-[10px] text-gray-400 mt-1.5">{new Date(activity.timestamp).toLocaleString()}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* New Channel Modal */}
      {showChannelModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className={`w-full max-w-md p-6 rounded-3xl shadow-2xl ${isDark ? 'bg-zinc-900 border border-white/10' : 'bg-white'}`}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold" style={{ color: isDark ? 'white' : 'black' }}>Create Channel</h3>
              <button onClick={() => setShowChannelModal(false)} className="p-2 text-gray-500 hover:text-gray-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-400">Channel Name</label>
                <div className={`flex items-center px-3 py-2.5 rounded-xl border ${isDark ? 'bg-black/50 border-white/10 text-white' : 'bg-gray-50 border-gray-300 text-black'}`}>
                  <Hash className="w-5 h-5 text-gray-500 mr-2" />
                  <input 
                    type="text" 
                    value={newChannelName}
                    onChange={(e) => setNewChannelName(e.target.value)}
                    placeholder="e.g. q3-sales-planning"
                    className="flex-1 bg-transparent border-none outline-none text-sm"
                  />
                </div>
              </div>
              <button 
                onClick={handleCreateChannel}
                disabled={!newChannelName.trim()}
                className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold disabled:opacity-50 transition-all"
              >
                Create Channel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className={`w-full max-w-md p-6 rounded-3xl shadow-2xl ${isDark ? 'bg-zinc-900 border border-white/10' : 'bg-white'}`}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold" style={{ color: isDark ? 'white' : 'black' }}>Invite Team Member</h3>
              <button onClick={() => setShowInviteModal(false)} className="p-2 text-gray-500 hover:text-gray-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-400">Full Name</label>
                <input 
                  type="text" 
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  placeholder="John Doe"
                  className={`w-full px-4 py-2.5 rounded-xl border text-sm ${isDark ? 'bg-black/50 border-white/10 text-white' : 'bg-gray-50 border-gray-300 text-black'}`}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-400">Email Address</label>
                <div className={`flex items-center px-4 py-2.5 rounded-xl border ${isDark ? 'bg-black/50 border-white/10 text-white' : 'bg-gray-50 border-gray-300 text-black'}`}>
                  <Mail className="w-4 h-4 text-gray-500 mr-2" />
                  <input 
                    type="email" 
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="john@company.com"
                    className="flex-1 bg-transparent border-none outline-none text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-400">Role</label>
                <select 
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className={`w-full px-4 py-2.5 rounded-xl border text-sm outline-none ${isDark ? 'bg-black/50 border-white/10 text-white' : 'bg-gray-50 border-gray-300 text-black'}`}
                >
                  <option value="Owner">Owner</option>
                  <option value="Admin">Admin</option>
                  <option value="Analyst">Analyst</option>
                  <option value="Viewer">Viewer</option>
                </select>
                <p className="text-[10px] text-gray-500 mt-1 pl-1">Role defines permissions across DataVision.</p>
              </div>
              <button 
                onClick={handleAddMember}
                disabled={!inviteName.trim() || !inviteEmail.trim()}
                className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold disabled:opacity-50 transition-all mt-4"
              >
                Send Invitation
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Collaborate;
