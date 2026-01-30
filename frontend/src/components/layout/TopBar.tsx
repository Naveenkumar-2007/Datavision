import React from 'react';
import { Bell, User, Menu } from 'lucide-react';
import { useUserStore } from '@/store/userStore';

interface TopBarProps {
  onMenuClick?: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ onMenuClick }) => {
  const user = useUserStore((state) => state.user);

  return (
    <header className="h-16 sm:h-14 lg:h-16 border-b border-dark-border bg-dark-surface flex items-center justify-between px-4">
      {/* Left section - Mobile menu button */}
      <div className="lg:hidden">
        <button
          onClick={onMenuClick}
          className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
          aria-label="Toggle menu"
        >
          <Menu className="w-6 h-6 text-gray-400" />
        </button>
      </div>

      {/* Center - Empty on mobile, can add breadcrumbs */}
      <div className="hidden lg:block flex-1"></div>

      {/* Right section */}
      <div className="flex items-center space-x-3">
        {/* Notifications */}
        <button className="relative p-2 hover:bg-dark-hover rounded-lg transition-colors">
          <Bell className="w-5 h-5 text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* User */}
        <div className="hidden sm:flex items-center space-x-2 pl-3 border-l border-dark-border">
          <div className="text-right">
            <div className="text-xs font-medium text-gray-200">{user?.name}</div>
            <div className="text-xs text-gray-500">{user?.email}</div>
          </div>
          <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
            <User className="w-5 h-5 text-white" />
          </div>
        </div>

        {/* Mobile user avatar only */}
        <div className="sm:hidden w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
          <User className="w-5 h-5 text-white" />
        </div>
      </div>
    </header>
  );
};

export default TopBar;
