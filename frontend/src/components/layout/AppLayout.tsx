/**
 * App Layout - Premium UI matching Landing page design
 * Supports dark/light theme with consistent styling
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
} from 'lucide-react';

const AppLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
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

  // Theme colors - PURE DARK (not blue-ish) with teal accents
  const bgColor = isDark ? '#0a0a0b' : '#F8FAFC';
  const cardBg = isDark ? '#141414' : '#FFFFFF';
  const textPrimary = isDark ? '#F8FAFC' : '#0F172A';
  const textMuted = isDark ? '#9CA3AF' : '#64748B';
  const borderColor = isDark ? '#262626' : '#E2E8F0';
  const sidebarBg = isDark ? 'rgba(10, 10, 11, 0.98)' : 'rgba(255, 255, 255, 0.98)';
  const accentColor = '#14B8A6'; // Teal - matching landing page CTA

  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/overview', label: 'Overview', icon: LayoutDashboard },
    { path: '/data-hub', label: 'Data Hub', icon: Database },
    { path: '/dashboards', label: 'Dashboards', icon: BarChart3 },
    { path: '/reports', label: 'Reports', icon: FileText },
    { path: '/chat', label: 'Analyst', icon: MessageSquare },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex h-screen overflow-hidden transition-colors duration-300" style={{ backgroundColor: bgColor }}>
      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-64 lg:w-60 
          transform transition-transform duration-300 ease-in-out
          lg:transform-none
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          border-r backdrop-blur-xl
        `}
        style={{ backgroundColor: sidebarBg, borderColor }}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b" style={{ borderColor }}>
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <img src="/logo.png" alt="DataVision Logo" className="w-9 h-9 object-contain" />
            <span className="text-lg font-semibold" style={{ color: textPrimary }}>
              DataVision
            </span>
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="lg:hidden p-2 rounded-lg hover:bg-white/10"
          >
            <X className="w-5 h-5" style={{ color: textMuted }} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const active = isActive(item.path);
            return (
              <button
                key={item.path}
                onClick={() => {
                  navigate(item.path);
                  setIsMobileMenuOpen(false);
                }}
                className={`
                  w-full flex items-center gap-3 px-4 py-3 rounded-xl
                  transition-all duration-200 text-sm font-medium
                  ${active
                    ? 'bg-teal-500/10 text-teal-400'
                    : 'hover:bg-white/5'
                  }
                `}
                style={{ color: active ? '#14B8A6' : textMuted }}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsMobileMenuOpen(false)}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Bar */}
        <header
          className="h-16 flex items-center justify-between px-4 lg:px-6 border-b backdrop-blur-md"
          style={{
            backgroundColor: isDark ? 'rgba(15, 23, 42, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            borderColor
          }}
        >
          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="lg:hidden p-2 rounded-lg hover:bg-white/10"
          >
            <Menu className="w-5 h-5" style={{ color: textMuted }} />
          </button>

          {/* Page Title */}
          <div className="hidden lg:block">
            <h1 className="text-lg font-semibold" style={{ color: textPrimary }}>
              {navItems.find(item => isActive(item.path))?.label || 'DataVision'}
            </h1>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg transition-colors"
              style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
            >
              {isDark
                ? <Sun className="w-5 h-5 text-slate-400" />
                : <Moon className="w-5 h-5 text-slate-500" />
              }
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="max-w-7xl mx-auto w-full"
          >
            <Outlet context={{ isDark, bgColor, cardBg, textPrimary, textMuted, borderColor }} />
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
