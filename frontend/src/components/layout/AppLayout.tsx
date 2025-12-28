/**
 * App Layout - Premium UI v2.0 - ChatGPT Level Design
 * Features: Glassmorphism, smooth animations, enhanced mobile UX
 */

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
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const AppLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem('theme');
    const prefersDark = saved !== 'light';
    setIsDark(prefersDark);
    if (!prefersDark) {
      document.documentElement.classList.add('light-theme');
    }
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  const toggleTheme = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);
    if (newIsDark) {
      document.documentElement.classList.remove('light-theme');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.add('light-theme');
      localStorage.setItem('theme', 'light');
    }
  };

  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/overview', label: 'Overview', icon: LayoutDashboard },
    { path: '/data-hub', label: 'Data Hub', icon: Database },
    { path: '/dashboards', label: 'Dashboards', icon: BarChart3 },
    { path: '/reports', label: 'Reports', icon: FileText },
    { path: '/chat', label: 'AI Analyst', icon: MessageSquare },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

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
        animate={{
          x: isMobileMenuOpen ? 0 : (typeof window !== 'undefined' && window.innerWidth < 1024 ? -280 : 0)
        }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-[280px] lg:w-64
          flex flex-col
          ${isDark ? 'glass-premium' : 'bg-white/95 backdrop-blur-xl'}
          border-r
        `}
        style={{
          borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
          boxShadow: isDark ? '4px 0 24px rgba(0,0,0,0.3)' : '4px 0 24px rgba(0,0,0,0.05)'
        }}
      >
        {/* Logo Section */}
        <div
          className="h-16 flex items-center justify-between px-5 border-b"
          style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}
        >
          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => navigate('/')}
          >
            <div className="relative">
              <img src="/logo.png" alt="DataVision" className="w-9 h-9 object-contain" />
              <div className="absolute inset-0 bg-teal-400/20 rounded-full blur-lg opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <span
              className="text-lg font-semibold tracking-tight"
              style={{ color: isDark ? '#f8fafc' : '#0f172a' }}
            >
              DataVision
            </span>
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="lg:hidden p-2 rounded-xl hover:bg-white/10 transition-colors touch-target"
          >
            <X className="w-5 h-5" style={{ color: isDark ? '#9ca3af' : '#64748b' }} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const active = isActive(item.path);
            return (
              <motion.button
                key={item.path}
                onClick={() => navigate(item.path)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`
                  nav-item-premium w-full flex items-center gap-3 px-4 py-3
                  ${active ? 'active' : ''}
                `}
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
                <span className="font-medium">{item.label}</span>
                {item.path === '/chat' && (
                  <Sparkles className="w-3.5 h-3.5 ml-auto text-teal-400 opacity-60" />
                )}
              </motion.button>
            );
          })}
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
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 hover:bg-red-500/10 group"
            style={{ color: isDark ? '#9ca3af' : '#64748b' }}
          >
            <LogOut className="w-5 h-5 group-hover:text-red-400 transition-colors" />
            <span className="font-medium group-hover:text-red-400 transition-colors">Sign Out</span>
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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
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

          {/* Page Title with Breadcrumb feel */}
          <div className="flex items-center gap-2">
            <motion.h1
              key={location.pathname}
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-lg font-semibold"
              style={{ color: isDark ? '#f8fafc' : '#0f172a' }}
            >
              {navItems.find(item => isActive(item.path))?.label || 'DataVision'}
            </motion.h1>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            {/* Theme toggle visible on desktop in header */}
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
          </div>
        </header>

        {/* Page Content with Smooth Transitions */}
        <main className="flex-1 overflow-auto">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
            className="w-full h-full p-4 lg:p-6"
          >
            <Outlet context={{ isDark, cardBg: isDark ? '#141414' : '#ffffff', textPrimary: isDark ? '#f8fafc' : '#0f172a', textMuted: isDark ? '#9ca3af' : '#64748b', borderColor: isDark ? '#262626' : '#e2e8f0' }} />
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
