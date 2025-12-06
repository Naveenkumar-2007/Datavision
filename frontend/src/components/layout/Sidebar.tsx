import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Database, 
  MessageSquare, 
  BarChart3, 
  FileText, 
  Settings,
  Sparkles,
} from 'lucide-react';
import { motion } from 'framer-motion';

const navItems = [
  { path: '/overview', icon: LayoutDashboard, label: 'Overview' },
  { path: '/data-hub', icon: Database, label: 'Data Hub' },
  { path: '/chat', icon: MessageSquare, label: 'AI Analyst' },
  { path: '/dashboards', icon: BarChart3, label: 'Dashboards' },
  { path: '/reports', icon: FileText, label: 'Reports' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

const Sidebar: React.FC = () => {
  return (
    <motion.aside
      initial={{ x: -300 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.3 }}
      className="w-64 bg-dark-surface border-r border-dark-border flex flex-col"
    >
      {/* Logo */}
      <div className="p-6 border-b border-dark-border">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-purple rounded-xl flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">AI Analyst</h1>
            <p className="text-xs text-gray-400">Enterprise Edition</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20'
                  : 'text-gray-400 hover:bg-dark-hover hover:text-gray-200'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-5 h-5 ${isActive ? 'text-primary-400' : ''}`} />
                <span className="font-medium">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-dark-border">
        <div className="glass-card p-3 text-center">
          <div className="text-sm font-semibold text-gray-200">Premium Plan</div>
          <div className="text-xs text-gray-400 mt-1">Unlimited Access</div>
          <div className="mt-2 h-1.5 bg-dark-bg rounded-full overflow-hidden">
            <div className="h-full w-4/5 bg-gradient-to-r from-primary-500 to-accent-green" />
          </div>
          <div className="text-xs text-gray-400 mt-1">80% storage used</div>
        </div>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
