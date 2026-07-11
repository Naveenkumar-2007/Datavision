import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3,
  LayoutDashboard,
  Database,
  FileText,
  MessageSquare,
  Settings,
  Sun,
  Moon,
  Menu,
  X,
  Home,
  Sparkles,
  LogOut,
  Brain,
  PanelLeftClose,
  PanelLeftOpen,
  Activity,
  GitBranch,
  Users,
  Terminal,
  Command,
  Lightbulb,
  ChevronRight,
  TrendingDown,
  Wifi,
  WifiOff,
  Cpu,
  Search,
  Rocket,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useUserStore } from '@/store/userStore';
import LogoImage from '@/components/LogoImage';
import { ContextualHelp } from '../ContextualHelp';
import apiService from '@/services/api';

const AppLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { isDark, toggleTheme } = useUserStore();

  // V3: Command Palette State
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [paletteSearch, setPaletteSearch] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // WebSocket State
  const [wsConnected, setWsConnected] = useState(false);
  const [liveMetrics, setLiveMetrics] = useState<any>(null);

  useEffect(() => {
    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // When running locally, Vite proxies /api, but for WS it's better to use direct or proxied path
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws`;
    
    let ws: WebSocket;
    let reconnectTimer: NodeJS.Timeout;

    const connectWs = () => {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
        console.log("WebSocket connected!");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'REALTIME_METRICS') {
            setLiveMetrics(data.payload);
          }
        } catch (e) {
          // ignore
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        // Attempt to reconnect after 3 seconds
        reconnectTimer = setTimeout(connectWs, 3000);
      };

      ws.onerror = (err) => {
        ws.close();
      };
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  // Debounced search
  useEffect(() => {
    if (paletteSearch.length < 2) {
      setSearchResults([]);
      return;
    }

    const delayDebounceFn = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await apiService.globalSearch(paletteSearch);
        if (res.data && res.data.results) {
          setSearchResults(res.data.results);
        }
      } catch (error) {
        console.error("Global search error:", error);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [paletteSearch]);

  useEffect(() => {
    // Sync class with store state
    if (!isDark) {
      document.documentElement.classList.add('light-theme');
    } else {
      document.documentElement.classList.remove('light-theme');
    }
  }, [isDark]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        setIsCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);



  // Check if ML results exist
  const hasMLResults = typeof window !== 'undefined' && localStorage.getItem('hasMLResults') === 'true';

  const navGroups = [
    {
      title: 'Data Foundation',
      items: [
        { path: '/', label: 'Home', icon: Home },
        { path: '/data-hub', label: 'Data Hub', icon: Database },
        { path: '/lineage', label: 'Data Lineage', icon: GitBranch },
      ]
    },
    {
      title: 'Intelligence & Analytics',
      items: [
        { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }, 
        { path: '/anomalies', label: 'Anomaly Monitor', icon: Activity },
      ]
    },
    {
      title: 'Advanced AI Lab',
      items: [
        { path: '/chat', label: 'AI Analyst', icon: MessageSquare },
        { path: '/ml-predictions', label: 'AutoML & Predict', icon: Brain }, 
      ]
    },
    {
      title: 'Output & Admin',
      items: [
        { path: '/reports', label: 'Reports', icon: FileText },
        { path: '/collaborate', label: 'Collaborate', icon: Users },
        { path: '/developer', label: 'Developer', icon: Terminal },
        { path: '/settings', label: 'Settings', icon: Settings },
      ]
    }
  ];

  const navItems = navGroups.flatMap(group => group.items);

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div
      className="flex h-screen overflow-hidden transition-colors duration-300"
      style={{
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-primary)'
      }}
    >
      {/* Premium Sidebar */}
      <motion.aside
        initial={false}
        className={`
          fixed inset-y-0 left-0 z-50 flex flex-col border-r transition-all duration-300
          ${isDark ? 'glass-premium' : 'bg-white/95 backdrop-blur-xl'}
          md:static 
          /* Slide logic handled by classes */
          ${isMobileMenuOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0'}
          /* Widths */
          w-[280px] md:w-20 
          ${isSidebarCollapsed ? 'lg:w-20' : 'lg:w-64'}
        `}
        style={{
          borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
          boxShadow: isDark && isMobileMenuOpen ? '4px 0 24px rgba(0,0,0,0.5)' : (isDark ? '4px 0 24px rgba(0,0,0,0.3)' : '4px 0 24px rgba(0,0,0,0.05)')
        }}
      >
        {/* Logo Section */}
        <div
          className={`h-16 flex items-center justify-between px-5 border-b transition-all duration-300
            md:justify-center 
            ${isSidebarCollapsed ? 'lg:justify-center' : 'lg:justify-start'}
          `}
          style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}
        >
          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => navigate('/')}
          >
            <div className="relative shrink-0">
              <LogoImage size={36} className="rounded-lg" />
              <div className="absolute inset-0 bg-green-400/20 rounded-full blur-lg opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <span
              className={`text-lg font-semibold tracking-tight md:hidden whitespace-nowrap
                ${isSidebarCollapsed ? 'lg:hidden' : 'lg:block'}
              `}
              style={{ color: isDark ? '#f8fafc' : '#0f172a' }}
            >
              DataVision
            </span>
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="md:hidden p-2 rounded-xl hover:bg-white/10 transition-colors touch-target"
          >
            <X className="w-5 h-5" style={{ color: isDark ? '#9ca3af' : '#64748b' }} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-4 overflow-y-auto overflow-x-hidden">
          {navGroups.map((group, groupIndex) => (
            <div key={groupIndex} className="space-y-1.5">
              <div className={`text-[10px] font-bold tracking-wider uppercase pl-4 mb-2 md:hidden ${isSidebarCollapsed ? 'lg:hidden' : 'lg:block'}`} style={{ color: isDark ? '#64748b' : '#94a3b8' }}>
                {group.title}
              </div>
              {group.items.map((item) => {
                const active = isActive(item.path);
                return (
                  <motion.button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`
                      nav-item-premium w-full flex items-center gap-3 px-4 py-3
                      md:justify-center md:px-0
                      ${isSidebarCollapsed ? 'lg:justify-center lg:px-0' : 'lg:justify-start lg:px-4'}
                      ${active ? 'active' : ''}
                    `}
                    title={item.label} // Tooltip for tablet/collapsed
                    style={{
                      color: active
                        ? '#2dd4bf'
                        : (isDark ? '#9ca3af' : '#64748b'),
                      background: active
                        ? (isDark ? 'rgba(45, 212, 191, 0.1)' : 'rgba(20, 184, 166, 0.08)')
                        : 'transparent',
                      borderColor: active ? 'rgba(45, 212, 191, 0.2)' : 'transparent',
                    }}
                  >
                    <item.icon className="w-5 h-5 flex-shrink-0" />
                    <span className={`font-medium md:hidden whitespace-nowrap
                      ${isSidebarCollapsed ? 'lg:hidden' : 'lg:block'}
                    `}>{item.label}</span>
                    {item.path === '/chat' && (
                      <Sparkles className={`w-3.5 h-3.5 ml-auto text-green-400 opacity-60 md:hidden
                        ${isSidebarCollapsed ? 'lg:hidden' : 'lg:inline-block'}
                      `} />
                    )}
                    {(item as any).badge && (
                      <span className={`ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white md:hidden
                        ${isSidebarCollapsed ? 'lg:hidden' : 'lg:inline-block'}
                      `}>{(item as any).badge}</span>
                    )}
                  </motion.button>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Footer - Sign Out Button */}
        <div
          className="p-4 border-t"
          style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}
        >
          <button
            onClick={() => {
              if (confirm('Are you sure you want to sign out?')) {
                signOut();
              }
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 hover:bg-red-500/10 group
              md:justify-center md:px-0 
              ${isSidebarCollapsed ? 'lg:justify-center lg:px-0' : 'lg:justify-start lg:px-4'}
            `}
            style={{ color: isDark ? '#9ca3af' : '#64748b' }}
            title="Sign Out"
          >
            <LogOut className="w-5 h-5 group-hover:text-red-400 transition-colors shrink-0" />
            <span className={`font-medium group-hover:text-red-400 transition-colors md:hidden whitespace-nowrap
              ${isSidebarCollapsed ? 'lg:hidden' : 'lg:block'}
            `}>Sign Out</span>
          </button>
        </div>
      </motion.aside>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setIsMobileMenuOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          />
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Premium Header */}
        <header
          className={`
            h-14 lg:h-16 flex items-center justify-between px-4 lg:px-6
            border-b backdrop-blur-xl sticky top-0 z-30
            ${isDark ? 'glass-premium' : 'bg-white/80'}
          `}
          style={{
            borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
          }}
        >
          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="lg:hidden p-2.5 rounded-xl hover:bg-white/10 transition-colors touch-target"
          >
            <Menu className="w-5 h-5" style={{ color: isDark ? '#9ca3af' : '#64748b' }} />
          </button>

          {/* Page Title with Breadcrumb feel + Desktop Toggle */}
          <div className="flex items-center gap-2 lg:gap-3">
            {/* Desktop Toggle Button */}
            <button
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              className="hidden lg:flex p-2 rounded-xl hover:bg-white/5 transition-colors"
              style={{ color: isDark ? '#9ca3af' : '#64748b' }}
              title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            >
              {isSidebarCollapsed ? <PanelLeftOpen className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
            </button>

            <div className="flex items-center gap-1.5 text-sm lg:text-base font-medium">
              <span className="opacity-40" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>DataVision</span>
              <span className="opacity-20 text-xs" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>/</span>
              <motion.span
                key={location.pathname}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                className="font-semibold text-sm lg:text-base"
                style={{ color: isDark ? '#f8fafc' : '#0f172a' }}
              >
                {navItems.find(item => isActive(item.path))?.label || 'Overview'}
              </motion.span>
            </div>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            {/* Search Trigger Button */}
            <button
              onClick={() => setIsCommandPaletteOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs transition-all duration-200 border"
              style={{
                backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
                color: isDark ? '#94a3b8' : '#64748b'
              }}
            >
              <Search className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Search...</span>
              <kbd className="hidden sm:inline-flex px-1.5 py-0.5 rounded bg-white/10 font-mono text-[10px] leading-none shrink-0">⌘K</kbd>
            </button>

            {/* Live Metrics Widget */}
            <div 
              className="hidden md:flex items-center gap-3 px-3 py-1.5 rounded-xl border text-xs"
              style={{
                backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
                color: isDark ? '#94a3b8' : '#64748b'
              }}
              title={wsConnected ? "Connected to Live Data Stream" : "Reconnecting..."}
            >
              {wsConnected ? <Wifi className="w-3.5 h-3.5 text-emerald-400" /> : <WifiOff className="w-3.5 h-3.5 text-rose-400" />}
              {liveMetrics && wsConnected ? (
                <div className="flex gap-3 text-[10px] sm:text-xs">
                  <span className="flex items-center gap-1">
                    <Users className="w-3 h-3 text-blue-400" />
                    {liveMetrics.active_users}
                  </span>
                  <span className="flex items-center gap-1">
                    <Cpu className="w-3 h-3 text-orange-400" />
                    {liveMetrics.cpu_load}%
                  </span>
                </div>
              ) : (
                <span className="text-[10px]">Connecting...</span>
              )}
            </div>

            {/* Theme toggle visible on desktop in header (Hidden on Dashboard due to AI Themes) */}
            {location.pathname !== '/dashboard' && (
              <button
                onClick={toggleTheme}
                className="hidden lg:flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200"
                style={{
                  backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                }}
              >
                {isDark
                  ? <Sun className="w-5 h-5 text-amber-400" />
                  : <Moon className="w-5 h-5 text-slate-500" />
                }
              </button>
            )}
          </div>
        </header>

        {/* Page Content with Smooth Transitions */}
        <main className="flex-1 overflow-auto">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
            className="w-full h-full p-2 lg:p-4"
          >
            <Outlet context={{ isDark, cardBg: isDark ? '#141414' : '#ffffff', textPrimary: isDark ? '#f8fafc' : '#0f172a', textMuted: isDark ? '#9ca3af' : '#64748b', borderColor: isDark ? '#262626' : '#e2e8f0' }} />
          </motion.div>
        </main>
      </div>

      {/* V3 Command Palette Modal */}
      <AnimatePresence>
        {isCommandPaletteOpen && (
          <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsCommandPaletteOpen(false)}
              className="fixed inset-0 bg-black/70 backdrop-blur-md"
            />

            {/* Palette Container */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ type: 'spring', duration: 0.3 }}
              className={`w-full max-w-xl rounded-2xl border shadow-2xl overflow-hidden relative z-10 flex flex-col ${
                isDark ? 'bg-zinc-900/90 border-white/10 text-white' : 'bg-white border-gray-200 text-gray-800'
              }`}
            >
              {/* Search Bar */}
              <div className="flex items-center gap-3 px-4 border-b border-white/5" style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
                <Search className="w-5 h-5 text-gray-400 shrink-0" />
                <input
                  autoFocus
                  type="text"
                  placeholder="Search pages or shortcuts (e.g. 'Toggle Theme')..."
                  value={paletteSearch}
                  onChange={(e) => setPaletteSearch(e.target.value)}
                  className="w-full py-4 text-sm bg-transparent focus:outline-none placeholder-gray-500"
                />
                <button 
                  onClick={() => setIsCommandPaletteOpen(false)}
                  className="px-2 py-1 text-[10px] rounded bg-white/10 text-gray-400 font-semibold"
                >
                  ESC
                </button>
              </div>

              {/* Items List */}
              <div className="max-h-[300px] overflow-y-auto p-2 space-y-1">
                {/* Navigation Items */}
                <div className="px-3 py-1.5 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  Pages & Navigation
                </div>
                {navItems
                  .filter(item => item.label.toLowerCase().includes(paletteSearch.toLowerCase()))
                  .map((item) => (
                    <button
                      key={item.path}
                      onClick={() => {
                        navigate(item.path);
                        setIsCommandPaletteOpen(false);
                        setPaletteSearch('');
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-left transition-all ${
                        isDark ? 'hover:bg-white/5 hover:text-white' : 'hover:bg-gray-50'
                      }`}
                      style={{ color: isDark ? '#9ca3af' : undefined }}
                    >
                      <div className="flex items-center gap-3">
                        <item.icon className="w-4 h-4 text-teal-400" />
                        <span>{item.label}</span>
                      </div>
                      <ChevronRight className="w-3.5 h-3.5 opacity-40" />
                    </button>
                  ))}

                {/* Global Search Results from API */}
                {searchResults.length > 0 && (
                  <>
                    <div className="px-3 py-1.5 text-[10px] font-bold text-gray-500 uppercase tracking-wider pt-3">
                      Global Search Results
                    </div>
                    {searchResults.map((result: any) => (
                      <button
                        key={result.id}
                        onClick={() => {
                          navigate(result.link);
                          setIsCommandPaletteOpen(false);
                          setPaletteSearch('');
                        }}
                        className={`w-full flex flex-col px-3 py-2.5 rounded-lg text-sm text-left transition-all ${
                          isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {result.type === 'anomaly' && <TrendingDown className="w-4 h-4 text-red-400" />}
                          {result.type === 'dataset' && <Database className="w-4 h-4 text-blue-400" />}
                          {result.type === 'report' && <FileText className="w-4 h-4 text-purple-400" />}
                          <span className={isDark ? 'text-white' : 'text-gray-800 font-medium'}>{result.title}</span>
                        </div>
                        <span className="text-xs mt-1 ml-7 opacity-60" style={{ color: isDark ? '#9ca3af' : '#64748b' }}>
                          {result.description}
                        </span>
                      </button>
                    ))}
                  </>
                )}

                {/* Custom Action Shortcuts */}
                {paletteSearch.trim() !== '' && (
                  <>
                    <div className="px-3 py-1.5 text-[10px] font-bold text-gray-500 uppercase tracking-wider pt-3">
                      Actions
                    </div>
                    {/* Toggle Theme Action */}
                    {"toggle theme".includes(paletteSearch.toLowerCase()) && (
                      <button
                        onClick={() => {
                          toggleTheme();
                          setIsCommandPaletteOpen(false);
                          setPaletteSearch('');
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-left transition-all ${
                          isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Command className="w-4 h-4 text-emerald-400" />
                          <span>Toggle Theme (Dark/Light)</span>
                        </div>
                        <ChevronRight className="w-3.5 h-3.5 opacity-40" />
                      </button>
                    )}
                    {/* Sign Out Action */}
                    {"sign out logout".includes(paletteSearch.toLowerCase()) && (
                      <button
                        onClick={() => {
                          if (confirm('Are you sure you want to sign out?')) {
                            signOut();
                          }
                          setIsCommandPaletteOpen(false);
                          setPaletteSearch('');
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-left transition-all ${
                          isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Command className="w-4 h-4 text-red-400" />
                          <span>Sign Out</span>
                        </div>
                        <ChevronRight className="w-3.5 h-3.5 opacity-40" />
                      </button>
                    )}
                  </>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
      <ContextualHelp />
    </div>
  );
};

export default AppLayout;
