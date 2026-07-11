import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { useLiveStore } from '@/store/liveStore';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Info, Terminal, 
  Key, 
  Copy, 
  Check, 
  RefreshCw,
  Code,
  Globe,
  Settings,
  Shield,
  Eye,
  EyeOff,
  Box,
  Layers,
  Code2,
  Play,
  Loader,
  Sparkles,
  Activity,
  Server,
  Database,
  Zap,
  Trash2,
  TrendingUp,
  AlertTriangle,
  Clock,
  ChevronDown,
  ChevronUp,
  BarChart3
} from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const timeAgo = (dateStr?: string) => {
  if (!dateStr) return 'Never';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins} mins ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hours ago`;
  return `${Math.floor(hours / 24)} days ago`;
};

const Developer: React.FC = () => {
  const { isDark } = useUserStore();
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [reveal, setReveal] = useState<Record<string, boolean>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [snippetLang, setSnippetLang] = useState('python');
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [newWebhook, setNewWebhook] = useState('');

  // Enterprise: Usage Analytics
  const [usageData, setUsageData] = useState<any>(null);
  const [usageLoading, setUsageLoading] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(true);
  const [analyticsView, setAnalyticsView] = useState<'hourly' | 'daily'>('hourly');

  useEffect(() => {
    fetchKeys();
    fetchWebhooks();
    fetchUsageAnalytics();
  }, []);

  const fetchUsageAnalytics = async () => {
    setUsageLoading(true);
    try {
      const res = await fetch('/api/v1/developer/usage-analytics', {
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      if (res.ok) {
        const data = await res.json();
        setUsageData(data);
      }
    } catch (e) {
      console.error('Failed to fetch usage analytics', e);
    } finally {
      setUsageLoading(false);
    }
  };

  const fetchWebhooks = async () => {
    try {
      const res = await fetch('/api/v1/developer/webhooks', {
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      if (res.ok) {
        const data = await res.json();
        setWebhooks(data);
      }
    } catch (e) {
      console.error('Failed to fetch webhooks', e);
    }
  };

  const addWebhook = async () => {
    if (!newWebhook.trim()) return;
    try {
      const res = await fetch('/api/v1/developer/webhooks', {
        method: 'POST',
        headers: { 
          'X-User-ID': useUserStore.getState().user?.id || 'default',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: newWebhook.trim() })
      });
      if (res.ok) {
        await fetchWebhooks();
        setNewWebhook('');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteWebhook = async (webhookId: string) => {
    try {
      const res = await fetch(`/api/v1/developer/webhooks/${webhookId}`, {
        method: 'DELETE',
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      if (res.ok) {
        await fetchWebhooks();
      }
    } catch (e) {
      console.error('Failed to delete webhook', e);
    }
  };

  const [pingingWebhook, setPingingWebhook] = useState<string | null>(null);
  const [pingSuccess, setPingSuccess] = useState<string | null>(null);
  const [deliveryLogs, setDeliveryLogs] = useState<Record<string, any[]>>({});
  const [loadingLogs, setLoadingLogs] = useState<Record<string, boolean>>({});

  const fetchDeliveryLogs = async (webhookId: string) => {
    if (deliveryLogs[webhookId]) {
      const newLogs = { ...deliveryLogs };
      delete newLogs[webhookId];
      setDeliveryLogs(newLogs);
      return;
    }
    setLoadingLogs(prev => ({...prev, [webhookId]: true}));
    try {
      const res = await fetch(`/api/v1/developer/webhooks/${webhookId}/deliveries`, {
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      if (res.ok) {
        const data = await res.json();
        setDeliveryLogs(prev => ({...prev, [webhookId]: data.deliveries || []}));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingLogs(prev => ({...prev, [webhookId]: false}));
    }
  };

  const handleTestWebhook = async (webhookId: string) => {
    setPingingWebhook(webhookId);
    try {
      const res = await fetch(`/api/v1/developer/webhooks/${webhookId}/test`, {
        method: 'POST',
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      const data = await res.json();
      if (data.success) {
        setPingSuccess(webhookId);
        setTimeout(() => setPingSuccess(null), 3000);
      } else {
        alert('Ping Failed: ' + data.message);
      }
    } catch (e) {
      console.error(e);
      alert('Network error while pinging.');
    } finally {
      setPingingWebhook(null);
    }
  };

  const handleDownloadStarterKit = () => {
    const key = apiKeys.length > 0 ? apiKeys[0].key : 'dv_live_your_key_here';
    const code = getSnippetText(snippetLang || 'python');
    const filename = snippetLang === 'python' ? 'datavision_starter.py' : snippetLang === 'js' ? 'datavision_starter.js' : 'datavision_starter.sh';
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/developer/keys', {
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      if (res.ok) {
        const data = await res.json();
        setApiKeys(data);
      }
    } catch (e) {
      console.error('Failed to fetch keys', e);
    } finally {
      setLoading(false);
    }
  };

  // Embed Builder State
  const [embedTheme, setEmbedTheme] = useState('dark');
  const [embedWidget, setEmbedWidget] = useState('full-dashboard');
  const [embedCopied, setEmbedCopied] = useState(false);

  // Playground state
  const [playgroundLoading, setPlaygroundLoading] = useState(false);
  const [playgroundResponse, setPlaygroundResponse] = useState<any>(null);

  const handleCopy = (key: string) => {
    navigator.clipboard.writeText(key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleGenerateNewKey = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch('/api/v1/developer/keys/generate', {
        method: 'POST',
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      if (res.ok) {
        await fetchKeys();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    try {
      const res = await fetch(`/api/v1/developer/keys/${keyId}/revoke`, {
        method: 'POST',
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      if (res.ok) {
        await fetchKeys();
      }
    } catch (e) {
      console.error('Failed to revoke key', e);
    }
  };

  const toggleReveal = (id: string) => {
    setReveal(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const embedCode = `<iframe
  src="${window.location.origin}/embed/${embedWidget}?theme=${embedTheme}&token=${(apiKeys[0]?.key || 'dv_live_...').substring(0, 12)}..."
  width="100%"
  height="600px"
  frameBorder="0"
  style="border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"
  allowTransparency="true">
</iframe>`;

  const handleCopyEmbed = () => {
    navigator.clipboard.writeText(embedCode);
    setEmbedCopied(true);
    setTimeout(() => setEmbedCopied(false), 2000);
  };

  const handleTestApi = async () => {
    setPlaygroundLoading(true);
    try {
      // Simulate real api call by hitting a known endpoint
      const res = await fetch('/api/v1/decisions/stats');
      const data = await res.json();
      setPlaygroundResponse(data);
    } catch (err) {
      setPlaygroundResponse({ error: "Failed to connect to API" });
    } finally {
      setPlaygroundLoading(false);
    }
  };

  const [snippetCopied, setSnippetCopied] = useState(false);
  const [aiSnippetPrompt, setAiSnippetPrompt] = useState('');
  const [isGeneratingAiSnippet, setIsGeneratingAiSnippet] = useState(false);
  const [generatedSnippets, setGeneratedSnippets] = useState<Record<string, string>>({});
  
  // Data-Driven Suggestions State
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [suggestedDatasetName, setSuggestedDatasetName] = useState('YOUR_LOCAL_FILE.csv');
  const [isFetchingSuggestions, setIsFetchingSuggestions] = useState(false);

  const handleSuggestGoals = async () => {
    setIsFetchingSuggestions(true);
    try {
      const res = await fetch('/api/v1/developer/suggest-goals', {
        headers: { 'X-User-ID': useUserStore.getState().user?.id || 'default' }
      });
      const data = await res.json();
      if (data.suggestions) {
        setSuggestions(data.suggestions);
        setSuggestedDatasetName(data.dataset || 'YOUR_LOCAL_FILE.csv');
      }
    } catch (e) {
      console.error('Failed to fetch suggestions', e);
    } finally {
      setIsFetchingSuggestions(false);
    }
  };

  const handleGenerateCode = async () => {
    if (!aiSnippetPrompt.trim()) return;
    setIsGeneratingAiSnippet(true);
    
    const key = apiKeys[0]?.key || 'dv_live_...';
    
    try {
      const res = await fetch('/api/v1/developer/generate-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: aiSnippetPrompt,
          language: snippetLang,
          api_key: key,
          base_url: window.location.origin,
          dataset_name: suggestedDatasetName
        })
      });
      const data = await res.json();
      if (data.code) {
        setGeneratedSnippets(prev => ({...prev, [snippetLang]: data.code}));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsGeneratingAiSnippet(false);
    }
  };

  const getSnippetText = (lang: string) => {
    if (generatedSnippets[lang]) {
      return generatedSnippets[lang];
    }
    const key = apiKeys[0]?.key || 'dv_live_...';
    // Use a clear placeholder so the external developer knows they must point to their own local file
    const datasetName = suggestedDatasetName;
    const baseUrl = window.location.origin;
    
    const userGoal = aiSnippetPrompt || 'Analyze this dataset and give me key insights';

    if (lang === 'python') {
      return `import requests\nimport json\n\nheaders = {\n    "Authorization": "Bearer ${key}"\n}\n\n# 1. Point this to ANY local CSV or Excel file on your server/laptop\nfiles = {'file': open('${datasetName}', 'rb')}\n\ndata = {'goal': '${userGoal}'}\n\n# 2. Send the request (stream=True is required for live AI updates!)\nresponse = requests.post(\n    "${baseUrl}/api/v1/autopilot/run",\n    headers=headers,\n    files=files,\n    data=data,\n    stream=True\n)\n\n# 3. Read the live AI stream\nfor line in response.iter_lines():\n    if line:\n        decoded = line.decode('utf-8')\n        if decoded.startswith('data: '):\n            try:\n                event_data = json.loads(decoded[6:])\n                if event_data.get('type') == 'step_complete':\n                    safe_title = event_data['data']['step']['title'].encode('ascii', 'ignore').decode('ascii').strip()\n                    print(f"[SUCCESS] {safe_title}")\n                elif event_data.get('type') == 'session_complete':\n                    print("\\n[COMPLETE] Analysis finished successfully.")\n            except:\n                pass`;
    }
    if (lang === 'curl') {
      return `curl -N -X POST ${baseUrl}/api/v1/autopilot/run \\\n  -H "Authorization: Bearer ${key}" \\\n  -F "file=@${datasetName}" \\\n  -F "goal=${userGoal}"`;
    }
    if (lang === 'js') {
      return `const formData = new FormData();\nformData.append('file', fileInput.files[0]);\nformData.append('goal', '${userGoal}');\n\nfetch('${baseUrl}/api/v1/autopilot/run', {\n  method: 'POST',\n  headers: { 'Authorization': 'Bearer ${key}' },\n  body: formData\n}).then(async res => {\n  const reader = res.body.getReader();\n  const decoder = new TextDecoder();\n  while (true) {\n    const {done, value} = await reader.read();\n    if (done) break;\n    console.log(decoder.decode(value));\n  }\n});`;
    }
    return '';
  };

  const handleCopySnippet = () => {
    navigator.clipboard.writeText(getSnippetText(snippetLang));
    setSnippetCopied(true);
    setTimeout(() => setSnippetCopied(false), 2000);
  };


  return (
    <div className="p-3 sm:p-6 space-y-4 sm:space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
            🔧 Developer & Embed Center
          </h2>
          <p className="text-sm mt-2" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
            Manage API keys, test endpoints, and configure embedded SDK dashboards.
          </p>
        </div>
      </div>

      {/* Instructions Banner */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-4 sm:p-5 rounded-2xl border flex flex-col sm:flex-row gap-4 items-start sm:items-center ${isDark ? 'bg-indigo-500/10 border-indigo-500/20' : 'bg-indigo-50 border-indigo-100'}`}
      >
        <div className={`p-3 rounded-xl ${isDark ? 'bg-indigo-500/20 text-indigo-400' : 'bg-indigo-100 text-indigo-600'}`}>
          <Info className="w-6 h-6" />
        </div>
        <div>
          <h4 className="font-bold text-sm mb-1" style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}>How to use this page?</h4>
          <p className="text-xs leading-relaxed" style={{ color: isDark ? '#94a3b8' : '#475569' }}>
            This section is designed for your software engineering team. You can generate an <strong>API Key</strong> here and use the <strong>Code Snippets</strong> below to automatically trigger Datavision's AI pipelines from your company's own backend servers. You can also configure Webhooks to receive notifications when long-running AI tasks finish.
          </p>
        </div>
      </motion.div>

      {/* ═══ Enterprise API Usage Analytics ═══ */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`rounded-3xl border shadow-xl overflow-hidden ${isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-100 shadow-gray-200/50'}`}
      >
        {/* Clickable Header */}
        <button
          onClick={() => setShowAnalytics(!showAnalytics)}
          className="w-full px-6 py-5 flex items-center justify-between hover:bg-white/5 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/20">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div className="text-left">
              <h3 className="font-bold text-base" style={{ color: isDark ? 'white' : 'black' }}>API Usage Analytics</h3>
              <p className="text-xs text-gray-500">Real-time performance monitoring & usage metrics</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {usageData && (
              <div className="hidden sm:flex gap-6 mr-4">
                <div className="text-right">
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider">Total Calls</p>
                  <p className="text-lg font-black" style={{ color: isDark ? 'white' : 'black' }}>{usageData.total_calls?.toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider">Avg Latency</p>
                  <p className="text-lg font-black text-emerald-500">{usageData.latency?.avg}ms</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider">Error Rate</p>
                  <p className={`text-lg font-black ${(usageData.errors?.error_rate || 0) > 5 ? 'text-red-500' : 'text-emerald-500'}`}>{usageData.errors?.error_rate}%</p>
                </div>
              </div>
            )}
            {showAnalytics ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </div>
        </button>

        <AnimatePresence>
        {showAnalytics && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className={`px-6 pb-6 border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
              {/* KPI Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 mb-6">
                <div className={`p-4 rounded-2xl border ${isDark ? 'bg-black/30 border-white/5' : 'bg-gray-50 border-gray-100'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Activity className="w-4 h-4 text-indigo-400" />
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Total Calls</p>
                  </div>
                  <p className="text-2xl font-black" style={{ color: isDark ? 'white' : 'black' }}>{usageData?.total_calls?.toLocaleString() || '—'}</p>
                  <p className={`text-[10px] mt-1 font-semibold ${(usageData?.week_change || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                    {(usageData?.week_change || 0) > 0 ? '+' : ''}{usageData?.week_change || 0}% this week
                  </p>
                </div>
                <div className={`p-4 rounded-2xl border ${isDark ? 'bg-black/30 border-white/5' : 'bg-gray-50 border-gray-100'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-4 h-4 text-teal-400" />
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Latency P95</p>
                  </div>
                  <p className="text-2xl font-black" style={{ color: isDark ? 'white' : 'black' }}>{usageData?.latency?.p95 || '—'}ms</p>
                  <p className="text-[10px] text-gray-500 mt-1 font-semibold">P50: {usageData?.latency?.p50}ms · P99: {usageData?.latency?.p99}ms</p>
                </div>
                <div className={`p-4 rounded-2xl border ${isDark ? 'bg-black/30 border-white/5' : 'bg-gray-50 border-gray-100'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Error Rate</p>
                  </div>
                  <p className={`text-2xl font-black ${(usageData?.errors?.error_rate || 0) > 5 ? 'text-red-500' : 'text-emerald-500'}`}>{usageData?.errors?.error_rate || '—'}%</p>
                  <p className="text-[10px] text-gray-500 mt-1 font-semibold">4xx: {usageData?.errors?.total_4xx || 0} · 5xx: {usageData?.errors?.total_5xx || 0}</p>
                </div>
                <div className={`p-4 rounded-2xl border ${isDark ? 'bg-black/30 border-white/5' : 'bg-gray-50 border-gray-100'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Server className="w-4 h-4 text-emerald-400" />
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Rate Limit</p>
                  </div>
                  <p className="text-2xl font-black text-emerald-500">{usageData?.rate_limit?.remaining?.toLocaleString() || '—'}</p>
                  <div className="mt-2">
                    <div className={`w-full h-1.5 rounded-full ${isDark ? 'bg-white/10' : 'bg-gray-200'}`}>
                      <div className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all" style={{ width: `${Math.min(usageData?.rate_limit?.percentage || 0, 100)}%` }} />
                    </div>
                    <p className="text-[10px] text-gray-500 mt-1">{usageData?.rate_limit?.current || 0} / {usageData?.rate_limit?.limit?.toLocaleString() || '1,000'} per min</p>
                  </div>
                </div>
              </div>

              {/* Charts Row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Calls Chart */}
                <div className={`p-5 rounded-2xl border ${isDark ? 'bg-black/20 border-white/5' : 'bg-gray-50/50 border-gray-100'}`}>
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="text-sm font-bold" style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}>API Calls</h4>
                    <div className="flex gap-1">
                      {(['hourly', 'daily'] as const).map(v => (
                        <button
                          key={v}
                          onClick={() => setAnalyticsView(v)}
                          className={`px-2.5 py-1 text-[10px] font-bold rounded-lg transition-colors uppercase ${analyticsView === v ? 'bg-indigo-500 text-white' : isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-200 text-gray-500'}`}
                        >
                          {v}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={analyticsView === 'hourly' ? (usageData?.calls_per_hour || []) : (usageData?.calls_per_day || [])}>
                        <defs>
                          <linearGradient id="callsGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'} />
                        <XAxis dataKey={analyticsView === 'hourly' ? 'hour' : 'day'} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: isDark ? '#18181b' : '#fff', border: isDark ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0', borderRadius: '12px', fontSize: '12px' }}
                          labelStyle={{ color: isDark ? '#fff' : '#000' }}
                        />
                        <Area type="monotone" dataKey="calls" stroke="#6366f1" fill="url(#callsGrad)" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Top Endpoints */}
                <div className={`p-5 rounded-2xl border ${isDark ? 'bg-black/20 border-white/5' : 'bg-gray-50/50 border-gray-100'}`}>
                  <h4 className="text-sm font-bold mb-4" style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}>Top Endpoints</h4>
                  <div className="space-y-3">
                    {(usageData?.top_endpoints || []).map((ep: any, i: number) => {
                      const maxCalls = usageData?.top_endpoints?.[0]?.calls || 1;
                      const pct = (ep.calls / maxCalls) * 100;
                      const colors = ['bg-indigo-500', 'bg-purple-500', 'bg-teal-500', 'bg-amber-500', 'bg-pink-500'];
                      return (
                        <div key={i}>
                          <div className="flex justify-between items-center mb-1">
                            <code className="text-[11px] font-mono" style={{ color: isDark ? '#e2e8f0' : '#334155' }}>{ep.endpoint}</code>
                            <span className="text-xs font-bold" style={{ color: isDark ? '#e2e8f0' : '#334155' }}>{ep.calls.toLocaleString()}</span>
                          </div>
                          <div className={`w-full h-2 rounded-full ${isDark ? 'bg-white/5' : 'bg-gray-200'}`}>
                            <div className={`h-full rounded-full ${colors[i % colors.length]} transition-all duration-500`} style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
        </AnimatePresence>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main developer tools */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* API Key Management */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`p-5 sm:p-8 rounded-3xl border shadow-xl relative overflow-hidden ${
              isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-100 shadow-gray-200/50'
            }`}
          >
            {/* Background Glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />

            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="font-bold text-lg flex items-center gap-2" style={{ color: isDark ? 'white' : 'black' }}>
                  <Key className="w-5 h-5 text-indigo-400" /> Authentication Keys
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  Use this key to securely authenticate requests to the DataVision API. Keep it secret.
                </p>
              </div>
              <div className="flex gap-2 items-center">
                {apiKeys.length > 0 && (
                  <>
                    <span className="text-xs text-gray-500">Last used: {timeAgo(apiKeys[0].last_used || apiKeys[0].created_at)}</span>
                    <div className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5 border ${apiKeys[0].is_active ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${apiKeys[0].is_active ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} /> {apiKeys[0].is_active ? 'Active' : 'Revoked'}
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="space-y-4">
              {loading ? (
                <div className="flex items-center gap-2 text-gray-500">
                  <RefreshCw className="w-4 h-4 animate-spin" /> Loading keys...
                </div>
              ) : Array.isArray(apiKeys) && apiKeys.length === 0 ? (
                <div className="text-gray-500 text-sm">No API keys found.</div>
              ) : Array.isArray(apiKeys) ? (
                apiKeys.map((keyObj) => (
                  <div key={keyObj.id} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                    <div className={`flex-1 px-4 py-3.5 rounded-xl border flex items-center justify-between text-sm transition-all focus-within:ring-2 focus-within:ring-indigo-500/50 ${
                      isDark ? 'bg-black/40 border-white/10' : 'bg-gray-50 border-gray-200'
                    }`}>
                      <code className="font-mono text-sm tracking-widest" style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}>
                        {reveal[keyObj.id] ? keyObj.key : '••••••••••••••••••••••••••••••••••••••••'}
                      </code>
                      <button 
                        onClick={() => toggleReveal(keyObj.id)}
                        className="text-gray-400 hover:text-indigo-400 transition-colors ml-4"
                      >
                        {reveal[keyObj.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleCopy(keyObj.key)}
                        className={`px-5 py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all min-w-[120px] ${
                          copied ? 'bg-emerald-500 text-white' : (isDark ? 'bg-white/10 hover:bg-white/20' : 'bg-gray-100 hover:bg-gray-200 text-gray-700')
                        }`}
                      >
                        {copied ? <><Check className="w-4 h-4" /> Copied</> : <><Copy className="w-4 h-4" /> Copy</>}
                      </button>
                      <button
                        onClick={() => handleRevokeKey(keyObj.id)}
                        className={`px-4 py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
                          isDark ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400' : 'bg-red-50 hover:bg-red-100 text-red-600'
                        }`}
                        title="Revoke Key"
                      >
                        Revoke
                      </button>
                    </div>
                  </div>
                ))
              ) : null}
            </div>

            <div className="mt-6 pt-5 border-t flex justify-between items-center" style={{ borderColor: isDark ? 'rgba(255,255,255,0.05)' : '#f1f5f9' }}>
              <p className="text-xs text-gray-500 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-emerald-400" /> Never share this key in client-side code. Use environment variables.
              </p>
              <button 
                onClick={handleGenerateNewKey}
                disabled={isGenerating}
                className="text-sm font-bold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
                {isGenerating ? 'Generating...' : 'Roll New Key'}
              </button>
            </div>
          </motion.div>

          {/* Code Snippets */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={`p-5 sm:p-8 rounded-3xl border shadow-xl relative overflow-hidden ${
              isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-100 shadow-gray-200/50'
            }`}
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-lg flex items-center gap-2" style={{ color: isDark ? 'white' : 'black' }}>
                <Terminal className="w-5 h-5 text-indigo-400" /> API Integration
              </h3>
              <div className="flex gap-2">
                {['python', 'curl', 'js'].map(lang => (
                  <button 
                    key={lang}
                    onClick={() => setSnippetLang(lang)}
                    className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors uppercase ${
                      snippetLang === lang 
                        ? 'bg-indigo-500 text-white' 
                        : isDark ? 'bg-white/5 text-gray-400 hover:bg-white/10' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                    }`}
                  >
                    {lang}
                  </button>
                ))}
              </div>
            </div>
            
            <p className="text-xs text-gray-500 mb-4">Generate code to programmatically run Agentic Autopilot from your servers.</p>

            <div className={`p-4 rounded-xl border mb-4 flex gap-3 items-start ${isDark ? 'bg-black/30 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
              <div className={`p-2 rounded-lg mt-1 ${isDark ? 'bg-indigo-500/20 text-indigo-400' : 'bg-indigo-100 text-indigo-600'}`}>
                <Code className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <label className="text-xs font-bold mb-1 block" style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}>AI Code Generator</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={aiSnippetPrompt}
                    onChange={(e) => setAiSnippetPrompt(e.target.value)}
                    placeholder="e.g. Write a script to analyze sales.csv and predict revenue"
                    className={`flex-1 px-3 py-2 text-sm rounded-lg border outline-none focus:ring-1 focus:ring-indigo-500 ${isDark ? 'bg-black/50 border-white/10 text-white' : 'bg-white border-gray-300 text-black'}`}
                    onKeyDown={(e) => e.key === 'Enter' && handleGenerateCode()}
                  />
                  <button
                    onClick={handleGenerateCode}
                    disabled={isGeneratingAiSnippet || !aiSnippetPrompt.trim()}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold disabled:opacity-50 transition-colors flex items-center gap-2"
                  >
                    {isGeneratingAiSnippet ? <Loader className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    Generate
                  </button>
                </div>
                {/* Auto-Suggest Pills */}
                <div className="flex gap-2 flex-wrap mt-3">
                  <button 
                    onClick={handleSuggestGoals}
                    disabled={isFetchingSuggestions}
                    className="text-xs px-3 py-1.5 rounded-full border border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/10 transition-colors flex items-center gap-1.5 shadow-sm"
                  >
                    {isFetchingSuggestions ? <Loader className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                    Auto-Suggest based on my data
                  </button>
                  {suggestions.map((s, i) => (
                    <button 
                      key={i}
                      onClick={() => setAiSnippetPrompt(s)}
                      className={`text-[11px] px-3 py-1.5 rounded-full border transition-colors ${isDark ? 'border-gray-700 bg-gray-800 text-gray-300 hover:border-indigo-500' : 'border-gray-200 bg-white text-gray-600 hover:border-indigo-400'}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="relative group">
              <div className="absolute right-3 top-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  onClick={handleCopySnippet}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md transition-colors"
                >
                  {snippetCopied ? <><Check className="w-3.5 h-3.5" /> Copied</> : <><Copy className="w-3.5 h-3.5" /> Copy Code</>}
                </button>
              </div>
              <pre className={`p-4 rounded-xl border font-mono text-sm overflow-x-auto ${isDark ? 'bg-[#0d1117] border-white/5' : 'bg-gray-900 border-gray-200'}`}>
                <code className="text-gray-300">
                  {getSnippetText(snippetLang)}
                </code>
              </pre>
            </div>

            {/* SDK Install Guide */}
            <div className={`mt-6 pt-6 border-t flex flex-col gap-3 ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold flex items-center gap-2" style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}>
                  <Terminal className="w-4 h-4 text-indigo-400" /> Environment Setup
                </h4>
                <button 
                  onClick={handleDownloadStarterKit}
                  className="px-3 py-1.5 text-xs font-bold rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white flex items-center gap-2 transition-colors shadow-sm"
                >
                  <Code className="w-3.5 h-3.5" /> Download Starter Kit
                </button>
              </div>
              <p className="text-xs text-gray-400 mb-2">
                Download the starter script, install the dependencies, and run it locally to see real AI predictions stream to your Webhook.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className={`p-4 rounded-xl border ${isDark ? 'bg-black/30 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
                  <p className="text-xs text-gray-500 font-bold mb-2 uppercase">1. Install Dependencies</p>
                  <code className="text-[11px] font-mono block p-2 rounded bg-black/50 text-green-400 border border-white/5">
                    {snippetLang === 'python' ? 'pip install requests httpx' : snippetLang === 'js' ? 'npm install node-fetch form-data' : 'apt-get install curl'}
                  </code>
                </div>
                <div className={`p-4 rounded-xl border ${isDark ? 'bg-black/30 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
                  <p className="text-xs text-gray-500 font-bold mb-2 uppercase">2. Secure API Key (.env)</p>
                  <code className="text-[11px] font-mono block p-2 rounded bg-black/50 text-indigo-300 border border-white/5">
                    DATAVISION_API_KEY={(apiKeys[0]?.key || 'dv_live_...').substring(0, 16)}...
                  </code>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Embedded Widget Tool */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className={`p-5 sm:p-8 rounded-3xl border shadow-xl relative overflow-hidden ${
              isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-100 shadow-gray-200/50'
            }`}
          >
            {/* Background Glow */}
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 pointer-events-none" />

            <h3 className="font-bold text-lg flex items-center gap-2 mb-6" style={{ color: isDark ? 'white' : 'black' }}>
              <Code2 className="w-5 h-5 text-teal-400" /> Embedded Dashboards
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mb-6 relative z-10">
               <div>
                 <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Widget Target</label>
                 <select 
                   value={embedWidget}
                   onChange={(e) => setEmbedWidget(e.target.value)}
                   className={`w-full p-3 rounded-xl border focus:outline-none focus:ring-1 focus:ring-teal-500 text-sm ${
                     isDark ? 'bg-black/40 border-white/10 text-white' : 'bg-gray-50 border-gray-200 text-black'
                   }`}
                 >
                   <option value="full-dashboard">Full Dashboard</option>
                   <option value="ml-predictions">ML Predictions Chart</option>
                   <option value="anomaly-monitor">Live Anomaly Monitor</option>
                   <option value="data-hub">Data Hub Browser</option>
                 </select>
               </div>
               <div>
                 <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Appearance</label>
                 <select 
                   value={embedTheme}
                   onChange={(e) => setEmbedTheme(e.target.value)}
                   className={`w-full p-3 rounded-xl border focus:outline-none focus:ring-1 focus:ring-teal-500 text-sm ${
                     isDark ? 'bg-black/40 border-white/10 text-white' : 'bg-gray-50 border-gray-200 text-black'
                   }`}
                 >
                   <option value="dark">Dark Theme (Premium)</option>
                   <option value="light">Light Theme (Clean)</option>
                   <option value="system">Auto Match System</option>
                 </select>
               </div>
            </div>

            <div className="relative group z-10">
              <div className="absolute right-3 top-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  onClick={handleCopyEmbed}
                  className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md"
                >
                  {embedCopied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />} 
                  {embedCopied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <pre className={`p-5 rounded-2xl border overflow-x-auto text-sm font-mono leading-relaxed transition-all ${
                isDark ? 'bg-[#0d1117] border-white/5 text-gray-300' : 'bg-gray-900 border-gray-200 text-gray-300'
              }`}>
                <code className="text-teal-400">{"<iframe"}</code>{'\n'}
                <code className="text-indigo-300">  src=</code><code className="text-green-300">"{window.location.origin}/embed/{embedWidget}?theme={embedTheme}&token={apiKeys[0]?.key || 'dv_live_...'}"</code>{'\n'}
                <code className="text-indigo-300">  width=</code><code className="text-green-300">"100%"</code>{'\n'}
                <code className="text-indigo-300">  height=</code><code className="text-green-300">"600px"</code>{'\n'}
                <code className="text-indigo-300">  frameBorder=</code><code className="text-green-300">"0"</code>{'\n'}
                <code className="text-indigo-300">  style=</code><code className="text-green-300">"border-radius: 12px;"</code>{'\n'}
                <code className="text-teal-400">{"></iframe>"}</code>
              </pre>
            </div>
          </motion.div>

        </div>

        {/* Webhooks and Webhooks Sidebar */}
        <div className="space-y-4 sm:space-y-6">
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`p-5 sm:p-6 rounded-3xl border shadow-lg ${isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-200/60 shadow-sm'}`}
          >
            <h3 className="font-bold text-base flex items-center gap-2 mb-4" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
              <Globe className="w-4 h-4 text-indigo-400" /> Webhook Management
            </h3>
            <p className="text-xs text-gray-500 mb-4 pb-4 border-b" style={{ borderColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
              Get real-time HTTP callbacks when async jobs complete.
            </p>

            <div className="space-y-3 mb-4">
              {Array.isArray(webhooks) && webhooks.map(wh => (
                <div key={wh.id} className={`p-3 rounded-xl border text-xs ${isDark ? 'bg-black/40 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="font-semibold" style={{ color: isDark ? 'white' : 'black' }}>{wh.url}</span>
                    <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded-md text-[10px] uppercase font-bold tracking-widest">{wh.status}</span>
                  </div>
                  <div className="flex gap-1 flex-wrap">
                    {Array.isArray(wh.events) && wh.events.map((ev: string) => (
                      <span key={ev} className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 text-[10px]">{ev}</span>
                    ))}
                  </div>
                  <div className="mt-2 pt-2 border-t flex justify-between items-center" style={{ borderColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
                    <button 
                      onClick={() => fetchDeliveryLogs(wh.id)}
                      className="text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      {loadingLogs[wh.id] ? 'Loading...' : deliveryLogs[wh.id] ? 'Hide Logs' : 'View Logs'}
                    </button>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleTestWebhook(wh.id)}
                        disabled={pingingWebhook === wh.id}
                        className={`text-xs font-bold px-3 py-1.5 rounded flex items-center gap-1.5 transition-colors ${
                          pingSuccess === wh.id 
                            ? 'bg-emerald-500 text-white' 
                            : isDark ? 'bg-indigo-600 hover:bg-indigo-500 text-white' : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                        }`}
                      >
                        {pingingWebhook === wh.id ? <Loader className="w-3.5 h-3.5 animate-spin" /> : pingSuccess === wh.id ? <Check className="w-3.5 h-3.5" /> : <Zap className="w-3.5 h-3.5" />}
                        {pingSuccess === wh.id ? 'PING SENT' : 'PING TEST'}
                      </button>
                      <button
                        onClick={() => deleteWebhook(wh.id)}
                        className={`px-2 py-1.5 rounded-lg transition-all ${
                          isDark ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400' : 'bg-red-50 hover:bg-red-100 text-red-600'
                        }`}
                        title="Delete Webhook"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  {deliveryLogs[wh.id] && (
                    <div className={`mt-2 p-2 rounded max-h-40 overflow-y-auto border ${isDark ? 'bg-black/40 border-white/5' : 'bg-white border-gray-100'}`}>
                      {deliveryLogs[wh.id].length === 0 ? (
                         <div className="text-[10px] text-gray-500 text-center">No deliveries yet.</div>
                      ) : (
                         deliveryLogs[wh.id].map((log: any) => (
                           <div key={log.id} className={`flex justify-between items-center text-[10px] py-1.5 border-b last:border-0 ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                             <div className="flex items-center gap-2">
                               <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${log.success ? 'bg-emerald-500/20 text-emerald-500' : 'bg-red-500/20 text-red-500'}`}>
                                 {log.status_code || (log.success ? '200' : 'ERR')}
                               </span>
                               <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>{log.event}</span>
                             </div>
                             <div className="text-gray-500">{timeAgo(log.timestamp)}</div>
                           </div>
                         ))
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t" style={{ borderColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
              <input 
                type="text" 
                value={newWebhook}
                onChange={(e) => setNewWebhook(e.target.value)}
                placeholder="https://your-domain.com/webhook"
                className={`w-full px-3 py-2 text-xs rounded-lg border mb-2 outline-none focus:ring-1 focus:ring-indigo-500 ${isDark ? 'bg-black/50 border-white/10 text-white' : 'bg-white border-gray-300 text-black'}`}
              />
              <button 
                onClick={addWebhook}
                disabled={!newWebhook.trim()}
                className="w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold disabled:opacity-50 transition-colors"
              >
                Add Endpoint
              </button>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className={`p-5 sm:p-6 rounded-3xl border shadow-lg ${isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-200/60 shadow-sm'}`}
          >
            <h3 className="font-bold text-base flex items-center gap-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
              <Code className="w-4 h-4 text-indigo-400" /> Interactive API Docs
            </h3>
            <p className="text-xs text-gray-500 mt-2 mb-4 pb-4 border-b" style={{ borderColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
              Explore the full OpenAPI 3.0 specification.
            </p>
            
            <div className="space-y-3">
              <a 
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer group transition-colors ${isDark ? 'bg-black/40 border-white/10 hover:border-indigo-500/50' : 'bg-gray-50 border-gray-200 hover:border-indigo-300'}`}
              >
                <div className="flex items-center gap-2">
                  <Box className="w-4 h-4 text-purple-400" />
                  <span className="text-sm font-semibold" style={{ color: isDark ? 'white' : 'black' }}>Autopilot API</span>
                </div>
                <span className="text-xs text-gray-400 group-hover:text-indigo-400">View →</span>
              </a>
              <a 
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer group transition-colors ${isDark ? 'bg-black/40 border-white/10 hover:border-indigo-500/50' : 'bg-gray-50 border-gray-200 hover:border-indigo-300'}`}
              >
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-semibold" style={{ color: isDark ? 'white' : 'black' }}>Decision Swarm</span>
                </div>
                <span className="text-xs text-gray-400 group-hover:text-indigo-400">View →</span>
              </a>
            </div>
            
            <a 
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full mt-6 py-2.5 rounded-xl border border-indigo-500/30 text-indigo-400 text-xs font-semibold hover:bg-indigo-500/10 transition-colors flex items-center justify-center block text-center"
            >
              Open Swagger UI
            </a>
          </motion.div>

        </div>

      </div>
    </div>
  );
};

export default Developer;
