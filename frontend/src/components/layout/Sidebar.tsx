import React, { useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  MessageSquare,
  BarChart3,
  FileText,
  Settings,
  LogOut,
  X,
  Boxes,
  Brain,
  TrendingUp,
  TrendingDown,
  Rocket,
  BookOpen,
  Activity,
  Workflow,
} from 'lucide-react';
import { motion } from 'framer-motion';
import Logo from '@/components/Logo';
import { useAuth } from '@/contexts/AuthContext';

const navItems = [

  { path: '/data-hub', icon: Database, label: 'Data Hub' },
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/anomalies', icon: TrendingDown, label: 'Anomaly Monitor' },
  { path: '/lineage', icon: Boxes, label: 'Data Lineage' },
  { path: '/simulator', icon: TrendingUp, label: 'Scenario Simulator' },
  { path: '/reports', icon: FileText, label: 'Reports' },
  { path: '/data-stories', icon: BookOpen, label: 'Data Stories', badge: 'V5' },
  { path: '/ml-predictions', icon: Brain, label: 'ML Predictions' },
  { path: '/model-monitoring', icon: Activity, label: 'Model Monitoring', badge: 'V5' },
  { path: '/pipelines', icon: Workflow, label: 'Pipeline Builder', badge: 'V5' },
  { path: '/chat', icon: MessageSquare, label: 'AI Analyst' },
  { path: '/collaborate', icon: MessageSquare, label: 'Collaborate' },
  { path: '/settings', icon: Settings, label: 'Settings' },
  { path: '/developer', icon: Boxes, label: 'Developer' },
];

interface SidebarProps {
  isMobileMenuOpen?: boolean;
  onClose?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isMobileMenuOpen = false, onClose }) => {
  const { signOut, user } = useAuth();
  const location = useLocation();

  // Close menu on route change
  useEffect(() => {
    if (onClose) onClose();
  }, [location.pathname]);

  const handleLogout = async () => {
    if (confirm('Are you sure you want to sign out?')) {
      await signOut();
    }
  };

  return (
    <motion.aside
      initial={false}
      animate={{ x: 0 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className={`
        w-64 bg-dark-surface border-r border-dark-border flex-col
        fixed lg:relative inset-y-0 left-0 z-50
        ${isMobileMenuOpen ? 'flex' : 'hidden'} lg:flex
      `}
    >
      {/* Mobile close button */}
      <div className="lg:hidden absolute top-4 right-4">
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-dark-card transition-colors"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Logo */}
      <div className="p-4 border-b border-dark-border">
        <Logo size="md" showText={true} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar-item flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${isActive ? 'active bg-primary-500/10' : 'hover:bg-dark-card'}`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-primary-400' : ''}`} />
                <span className="font-medium">{item.label}</span>
                {(item as any).badge && (
                  <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white">
                    {(item as any).badge}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User Info & Logout */}
      <div className="p-4 border-t border-dark-border space-y-3">
        {/* User Email */}
        {user && (
          <div className="px-3 py-2 bg-dark-card rounded-lg">
            <p className="text-xs text-gray-400">Signed in as</p>
            <p className="text-sm text-white truncate" title={user.email || ''}>{user.email}</p>
          </div>
        )}

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-200"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
