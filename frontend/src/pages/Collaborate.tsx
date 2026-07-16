import React, { useState, useEffect, useRef } from 'react';
import { useUserStore } from '@/store/userStore';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Users, MessageSquare, Send, Share2, Plus, CheckCircle2,
  Hash, X, Copy, Mail, Activity, Smile, Reply, Pin, Search,
  UserPlus, Trash2, ChevronDown, Lock, Unlock, MoreHorizontal
} from 'lucide-react';
import { api } from '@/services/api';
import { ChatCrypto } from '@/utils/crypto';
import { useToast } from '@/contexts/ToastContext';

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

const EMOJI_LIST = ['👍', '❤️', '😂', '🎉', '🤔', '👀', '🔥', '✅'];

const Collaborate: React.FC = () => {
  const { isDark } = useUserStore();
  const { user } = useAuth();
  const toast = useToast();

  // Data
  const [channels, setChannels] = useState<any[]>([]);
  const [activeChannel, setActiveChannel] = useState('default');
  const [comments, setComments] = useState<any[]>([]);
  const [members, setMembers] = useState<any[]>([]);
  const [activityFeed, setActivityFeed] = useState<any[]>([]);

  // UI
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [isSecureMode, setIsSecureMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [showChannelModal, setShowChannelModal] = useState(false);
  const [newChannelName, setNewChannelName] = useState('');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteName, setInviteName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Viewer');

  // Message features
  const [reactions, setReactions] = useState<Record<string, Record<string, string[]>>>({});
  const [replies, setReplies] = useState<Record<string, any[]>>({});
  const [replyingTo, setReplyingTo] = useState<any>(null);
  const [showEmojiPicker, setShowEmojiPicker] = useState<string | null>(null);
  const [rightPanel, setRightPanel] = useState<'members' | 'activity'>('members');

  const chatEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Theme helpers
  const bg = isDark ? 'bg-[#0a0a0a]' : 'bg-white';
  const bgCard = isDark ? 'bg-[#111]' : 'bg-gray-50';
  const bgHover = isDark ? 'hover:bg-white/5' : 'hover:bg-gray-100';
  const border = isDark ? 'border-gray-800' : 'border-gray-200';
  const textPrimary = isDark ? 'text-white' : 'text-gray-900';
  const textSecondary = isDark ? 'text-gray-400' : 'text-gray-600';
  const textMuted = isDark ? 'text-gray-500' : 'text-gray-400';
  const inputBg = isDark ? 'bg-[#1a1a1a] border-gray-700 text-white placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400';

  // ─── DATA FETCHING ───
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [channelsRes, membersRes, activityRes] = await Promise.all([
          api.get('/api/v1/collaboration/channels'),
          api.get('/api/v1/collaboration/members'),
          api.get('/api/v1/collaboration/activity-feed')
        ]);
        setChannels(channelsRes.data?.channels || []);
        setMembers(membersRes.data?.members || []);
        setActivityFeed(activityRes.data?.activities || []);
      } catch (err) {
        console.error("Failed to load initial data", err);
      }
    };
    fetchData();
  }, []);

  // Fetch threads + WebSocket on channel change
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

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/collaboration/ws/${activeChannel}?user_name=${user?.full_name || 'Anonymous'}&user_id=${user?.id || 'default'}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.message) {
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

    return () => { ws.close(); };
  }, [activeChannel]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [comments]);

  // ─── HANDLERS ───
  const handlePostComment = async () => {
    if (!newComment.trim() || posting) return;
    setPosting(true);
    const inputVal = newComment.trim();
    let finalMessage = inputVal;
    let isEncrypted = false;
    const shouldEncrypt = isSecureMode && !inputVal.toLowerCase().includes('@ai');
    if (shouldEncrypt) {
      finalMessage = await ChatCrypto.encryptMessage(inputVal, activeChannel);
      isEncrypted = true;
    }

    if (replyingTo) {
      try {
        const res = await api.post(`/api/v1/collaboration/threads/${replyingTo.id}/reply`, {
          message: finalMessage, user: user?.full_name || 'Anonymous', is_encrypted: isEncrypted
        });
        if (res.data.success) {
          setReplies(prev => ({ ...prev, [replyingTo.id]: [...(prev[replyingTo.id] || []), res.data.reply] }));
        }
      } catch (e) { console.error('Failed to reply', e); }
      setReplyingTo(null);
    } else {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ message: finalMessage, user: user?.full_name || 'Anonymous', is_encrypted: isEncrypted }));
      }
    }
    setNewComment('');
    setPosting(false);
  };

  const handleReact = async (msgId: string, emoji: string) => {
    try {
      const res = await api.post(`/api/v1/collaboration/threads/${msgId}/react`, { emoji, user: user?.full_name || 'Anonymous' });
      if (res.data.success) setReactions(prev => ({ ...prev, [msgId]: res.data.reactions }));
    } catch (e) { console.error('Reaction failed', e); }
    setShowEmojiPicker(null);
  };

  const handleCreateChannel = async () => {
    if (!newChannelName.trim()) return;
    try {
      const res = await api.post('/api/v1/collaboration/channels', { name: newChannelName.trim() });
      if (res.data.success) {
        setChannels(prev => [...prev, res.data.channel]);
        setActiveChannel(res.data.channel.id);
        setShowChannelModal(false);
        setNewChannelName('');
        toast.success(`Channel #${res.data.channel.name} created!`);
      }
    } catch (err) { console.error("Error creating channel", err); }
  };

  const handleAddMember = async () => {
    if (!inviteName.trim() || !inviteEmail.trim()) return;
    try {
      const res = await api.post('/api/v1/collaboration/members', { name: inviteName, email: inviteEmail, role: inviteRole });
      if (res.data.success) {
        setMembers(prev => [...prev, res.data.member]);
        setShowInviteModal(false);
        setInviteName('');
        setInviteEmail('');
        toast.success(res.data.message || `Invitation sent to ${inviteEmail}!`);
      }
    } catch (err) { console.error("Error adding member", err); }
  };

  const handleChangeRole = async (email: string, role: string) => {
    try {
      const res = await api.put('/api/v1/collaboration/members/role', { email, role });
      if (res.data.success) {
        setMembers(prev => prev.map(m => m.email === email ? { ...m, role } : m));
        toast.success(`Role updated to ${role}`);
      }
    } catch (e) { console.error('Failed to update role', e); }
  };

  const handleRemoveMember = async (email: string) => {
    try {
      const res = await api.delete('/api/v1/collaboration/members', { data: { email } });
      if (res.data.success) {
        setMembers(prev => prev.filter(m => m.email !== email));
        toast.success('Member removed');
      }
    } catch (e) { console.error('Failed to remove member', e); }
  };

  const handleCopyLink = async () => {
    try {
      const res = await api.post('/api/v1/collaboration/invite');
      if (res.data.success) {
        navigator.clipboard.writeText(`${window.location.origin}${res.data.link}`);
        toast.success('Invite link copied!');
      }
    } catch (err) { console.error("Error generating link", err); }
  };

  const activeChannelName = channels.find(c => c.id === activeChannel)?.name || 'general';

  // ─── RENDER ───
  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden" style={{ backgroundColor: isDark ? '#0a0a0a' : '#f8fafc' }}>
      
      {/* ─── LEFT SIDEBAR: Channels ─── */}
      <div className={`w-64 shrink-0 border-r ${border} flex flex-col ${bgCard}`}>
        <div className={`p-4 border-b ${border}`}>
          <h2 className={`font-bold text-lg ${textPrimary}`}>💬 Channels</h2>
          <p className={`text-xs mt-0.5 ${textMuted}`}>Team workspaces</p>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {channels.map(ch => (
            <button
              key={ch.id}
              onClick={() => setActiveChannel(ch.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
                activeChannel === ch.id 
                  ? (isDark ? 'bg-indigo-500/20 text-indigo-400' : 'bg-indigo-50 text-indigo-700')
                  : `${textSecondary} ${bgHover}`
              }`}
            >
              <Hash className="w-4 h-4 shrink-0" />
              {ch.name}
            </button>
          ))}
          {channels.length === 0 && (
            <p className={`text-xs px-3 py-4 ${textMuted}`}>No channels yet.</p>
          )}
        </div>

        <div className={`p-3 border-t ${border} space-y-2`}>
          <button 
            onClick={() => setShowChannelModal(true)}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isDark ? 'bg-white/5 text-gray-300 hover:bg-white/10' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
          >
            <Plus className="w-4 h-4" /> New Channel
          </button>
          <button 
            onClick={handleCopyLink}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isDark ? 'bg-white/5 text-gray-300 hover:bg-white/10' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
          >
            <Copy className="w-4 h-4" /> Copy Invite Link
          </button>
        </div>
      </div>

      {/* ─── CENTER: Chat Area ─── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Channel Header */}
        <div className={`px-6 py-3 border-b ${border} flex items-center justify-between shrink-0 ${bgCard}`}>
          <div className="flex items-center gap-3">
            <Hash className={`w-5 h-5 ${textMuted}`} />
            <h3 className={`font-bold text-lg ${textPrimary}`}>{activeChannelName}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-100 text-gray-500'}`}>
              {members.length} member{members.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsSecureMode(!isSecureMode)}
              className={`p-2 rounded-lg transition-colors ${isSecureMode ? 'bg-green-500/20 text-green-400' : isDark ? 'bg-white/5 text-gray-400 hover:bg-white/10' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
              title={isSecureMode ? 'E2E Encryption ON' : 'E2E Encryption OFF'}
            >
              {isSecureMode ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setShowInviteModal(true)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${isDark ? 'bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
            >
              <UserPlus className="w-4 h-4" /> Invite
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-1">
          {loading ? (
            <div className={`flex items-center justify-center h-full ${textMuted}`}>
              <Activity className="w-5 h-5 animate-spin mr-2" /> Loading messages...
            </div>
          ) : comments.length === 0 ? (
            <div className={`flex flex-col items-center justify-center h-full ${textMuted}`}>
              <MessageSquare className="w-12 h-12 mb-3 opacity-30" />
              <p className="font-medium">No messages yet</p>
              <p className="text-xs mt-1">Start the conversation or type <span className="text-indigo-400 font-mono">@ai</span> for data insights</p>
            </div>
          ) : (
            comments.map((msg) => (
              <div 
                key={msg.id} 
                className={`group flex items-start gap-3 p-3 rounded-xl transition-colors ${bgHover} ${msg.isAi ? (isDark ? 'bg-indigo-500/5 border border-indigo-500/20' : 'bg-indigo-50/50 border border-indigo-100') : ''}`}
              >
                {/* Avatar */}
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 text-sm font-bold ${
                  msg.isAi 
                    ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white' 
                    : isDark ? 'bg-gray-800 text-gray-300' : 'bg-gray-200 text-gray-600'
                }`}>
                  {msg.isAi ? '🤖' : (msg.avatar || msg.user?.charAt(0)?.toUpperCase() || '?')}
                </div>

                {/* Message Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2">
                    <span className={`font-semibold text-sm ${msg.isAi ? 'text-indigo-400' : textPrimary}`}>
                      {msg.isAi ? 'DataVision AI' : msg.user}
                    </span>
                    <span className={`text-[10px] ${textMuted}`}>{msg.time}</span>
                    {msg.is_encrypted && <Lock className="w-3 h-3 text-green-500" />}
                  </div>
                  <div className={`text-sm mt-0.5 leading-relaxed ${textSecondary}`}>
                    <DecryptedMessage msg={msg} channelKey={activeChannel} />
                  </div>

                  {/* Reactions */}
                  {reactions[msg.id] && Object.keys(reactions[msg.id]).length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {Object.entries(reactions[msg.id]).map(([emoji, users]) => (
                        <span key={emoji} className={`px-2 py-0.5 rounded-full text-xs flex items-center gap-1 ${isDark ? 'bg-white/5 text-gray-300' : 'bg-gray-100 text-gray-600'}`}>
                          {emoji} {(users as string[]).length}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Replies */}
                  {replies[msg.id] && replies[msg.id].length > 0 && (
                    <div className={`mt-2 pl-3 border-l-2 space-y-1 ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                      {replies[msg.id].map((r: any, i: number) => (
                        <div key={i} className={`text-xs ${textSecondary}`}>
                          <span className={`font-semibold ${textPrimary}`}>{r.user}</span>: {r.message}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action buttons (on hover) */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 shrink-0">
                  <button onClick={() => setShowEmojiPicker(showEmojiPicker === msg.id ? null : msg.id)} className={`p-1.5 rounded-lg ${bgHover} ${textMuted}`}>
                    <Smile className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => { setReplyingTo(msg); inputRef.current?.focus(); }} className={`p-1.5 rounded-lg ${bgHover} ${textMuted}`}>
                    <Reply className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Emoji picker popover */}
                {showEmojiPicker === msg.id && (
                  <div className={`absolute z-20 mt-8 p-2 rounded-xl border shadow-xl ${isDark ? 'bg-[#1a1a1a] border-gray-700' : 'bg-white border-gray-200'}`}>
                    <div className="flex gap-1 flex-wrap w-48">
                      {EMOJI_LIST.map(e => (
                        <button key={e} onClick={() => handleReact(msg.id, e)} className={`p-1.5 rounded-lg text-lg ${bgHover}`}>{e}</button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Reply indicator */}
        <AnimatePresence>
          {replyingTo && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
              className={`px-6 py-2 border-t ${border} flex items-center justify-between ${bgCard}`}
            >
              <span className={`text-xs ${textMuted}`}>Replying to <strong className={textPrimary}>{replyingTo.user}</strong></span>
              <button onClick={() => setReplyingTo(null)} className={`p-1 rounded ${bgHover} ${textMuted}`}><X className="w-3.5 h-3.5" /></button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Message Input */}
        <div className={`px-6 py-3 border-t ${border} ${bgCard}`}>
          <div className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border ${isDark ? 'bg-[#1a1a1a] border-gray-700' : 'bg-white border-gray-300'}`}>
            <input
              ref={inputRef}
              type="text"
              value={newComment}
              onChange={e => setNewComment(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handlePostComment(); } }}
              placeholder={replyingTo ? `Reply to ${replyingTo.user}...` : `Message #${activeChannelName}... (type @ai for insights)`}
              className={`flex-1 bg-transparent border-none outline-none text-sm ${textPrimary}`}
            />
            {isSecureMode && <Lock className="w-4 h-4 text-green-500 shrink-0" />}
            <button 
              onClick={handlePostComment} 
              disabled={!newComment.trim() || posting}
              className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-40 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ─── RIGHT PANEL: Members & Activity ─── */}
      <div className={`w-72 shrink-0 border-l ${border} flex flex-col ${bgCard}`}>
        {/* Panel Tabs */}
        <div className={`flex border-b ${border}`}>
          {['members', 'activity'].map(tab => (
            <button
              key={tab}
              onClick={() => setRightPanel(tab as any)}
              className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider transition-colors ${
                rightPanel === tab 
                  ? (isDark ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-indigo-600 border-b-2 border-indigo-600')
                  : `${textMuted} ${bgHover}`
              }`}
            >
              {tab === 'members' ? '👥 Team' : '📋 Activity'}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {rightPanel === 'members' ? (
            <>
              {members.map((m, i) => (
                <div key={i} className={`flex items-center gap-3 p-2.5 rounded-xl ${bgHover} group`}>
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shrink-0 ${isDark ? 'bg-gray-800 text-gray-300' : 'bg-gray-200 text-gray-600'}`}>
                    {m.avatar || '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${textPrimary}`}>{m.name}</p>
                    <p className={`text-[10px] truncate ${textMuted}`}>{m.email}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <select
                      value={m.role}
                      onChange={e => handleChangeRole(m.email, e.target.value)}
                      className={`text-[10px] px-1.5 py-0.5 rounded border outline-none ${isDark ? 'bg-transparent border-gray-700 text-gray-400' : 'bg-transparent border-gray-200 text-gray-500'}`}
                    >
                      <option>Owner</option>
                      <option>Admin</option>
                      <option>Analyst</option>
                      <option>Viewer</option>
                    </select>
                    <button 
                      onClick={() => handleRemoveMember(m.email)} 
                      className="opacity-0 group-hover:opacity-100 p-1 rounded text-red-400 hover:bg-red-500/10 transition-all"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
              {members.length === 0 && (
                <p className={`text-xs text-center py-6 ${textMuted}`}>No team members yet.</p>
              )}
              <button 
                onClick={() => setShowInviteModal(true)}
                className={`w-full mt-2 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${isDark ? 'bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 border border-indigo-500/20' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-100'}`}
              >
                <UserPlus className="w-4 h-4" /> Invite Member
              </button>
            </>
          ) : (
            <>
              {activityFeed.length === 0 ? (
                <p className={`text-xs text-center py-6 ${textMuted}`}>No recent activity.</p>
              ) : activityFeed.map((act, i) => (
                <div key={i} className={`flex items-start gap-2 p-2 rounded-lg text-xs ${bgHover}`}>
                  <Activity className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${textMuted}`} />
                  <div>
                    <p className={textSecondary}>{act.message || act.action}</p>
                    <p className={`text-[10px] mt-0.5 ${textMuted}`}>{act.timestamp || act.time}</p>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* ─── MODALS ─── */}

      {/* Create Channel Modal */}
      <AnimatePresence>
        {showChannelModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm bg-black/50 p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className={`w-full max-w-md rounded-2xl border overflow-hidden shadow-2xl ${isDark ? 'bg-[#111] border-gray-800' : 'bg-white border-gray-200'}`}
            >
              <div className={`p-4 border-b ${border} flex items-center justify-between`}>
                <h3 className={`font-bold ${textPrimary}`}>Create New Channel</h3>
                <button onClick={() => setShowChannelModal(false)} className={`p-1.5 rounded-lg ${bgHover} ${textMuted}`}><X className="w-4 h-4" /></button>
              </div>
              <div className="p-5 space-y-4">
                <div>
                  <label className={`text-sm font-medium block mb-1.5 ${textSecondary}`}>Channel Name</label>
                  <div className={`flex items-center px-3 py-2.5 rounded-xl border ${inputBg}`}>
                    <Hash className={`w-4 h-4 mr-2 ${textMuted}`} />
                    <input
                      type="text"
                      value={newChannelName}
                      onChange={e => setNewChannelName(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') handleCreateChannel(); }}
                      placeholder="e.g. analytics-team"
                      className="flex-1 bg-transparent border-none outline-none text-sm"
                    />
                  </div>
                </div>
                <button 
                  onClick={handleCreateChannel}
                  disabled={!newChannelName.trim()}
                  className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm disabled:opacity-50 transition-colors"
                >
                  Create Channel
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Invite Member Modal */}
      <AnimatePresence>
        {showInviteModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm bg-black/50 p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className={`w-full max-w-md rounded-2xl border overflow-hidden shadow-2xl ${isDark ? 'bg-[#111] border-gray-800' : 'bg-white border-gray-200'}`}
            >
              <div className={`p-4 border-b ${border} flex items-center justify-between`}>
                <div>
                  <h3 className={`font-bold ${textPrimary}`}>Invite Team Member</h3>
                  <p className={`text-xs mt-0.5 ${textMuted}`}>They'll receive an email invitation</p>
                </div>
                <button onClick={() => setShowInviteModal(false)} className={`p-1.5 rounded-lg ${bgHover} ${textMuted}`}><X className="w-4 h-4" /></button>
              </div>
              <div className="p-5 space-y-4">
                <div>
                  <label className={`text-sm font-medium block mb-1.5 ${textSecondary}`}>Full Name</label>
                  <input 
                    type="text" value={inviteName} onChange={e => setInviteName(e.target.value)} placeholder="John Doe"
                    className={`w-full px-4 py-2.5 rounded-xl border text-sm ${inputBg}`}
                  />
                </div>
                <div>
                  <label className={`text-sm font-medium block mb-1.5 ${textSecondary}`}>Email Address</label>
                  <div className={`flex items-center px-4 py-2.5 rounded-xl border ${inputBg}`}>
                    <Mail className={`w-4 h-4 mr-2 ${textMuted}`} />
                    <input type="email" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} placeholder="john@company.com" className="flex-1 bg-transparent border-none outline-none text-sm" />
                  </div>
                </div>
                <div>
                  <label className={`text-sm font-medium block mb-1.5 ${textSecondary}`}>Role</label>
                  <select value={inviteRole} onChange={e => setInviteRole(e.target.value)} className={`w-full px-4 py-2.5 rounded-xl border text-sm outline-none ${inputBg}`}>
                    <option value="Owner">Owner — Full access</option>
                    <option value="Admin">Admin — Manage team</option>
                    <option value="Analyst">Analyst — View & analyze</option>
                    <option value="Viewer">Viewer — Read only</option>
                  </select>
                </div>
                <button 
                  onClick={handleAddMember}
                  disabled={!inviteName.trim() || !inviteEmail.trim()}
                  className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                >
                  <Send className="w-4 h-4" /> Send Invitation
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Collaborate;
