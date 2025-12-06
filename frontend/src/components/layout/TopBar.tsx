import React from 'react';
import { Bell, Search, User } from 'lucide-react';
import { useUserStore } from '@/store/userStore';

const TopBar: React.FC = () => {
  const user = useUserStore((state) => state.user);

  return (
    <header className="h-16 border-b border-dark-border bg-dark-surface/50 backdrop-blur-xl flex items-center justify-between px-8">
      {/* Search */}
      <div className="flex-1 max-w-xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search anything..."
            className="w-full pl-10 pr-4 py-2 bg-dark-card border border-dark-border rounded-xl text-gray-200 placeholder-gray-500 focus:outline-none focus:border-primary-500 transition-colors"
          />
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <button className="relative p-2 hover:bg-dark-hover rounded-xl transition-colors">
          <Bell className="w-5 h-5 text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-accent-red rounded-full" />
        </button>

        {/* User */}
        <div className="flex items-center space-x-3 pl-4 border-l border-dark-border">
          <div className="text-right">
            <div className="text-sm font-medium text-gray-200">{user?.name}</div>
            <div className="text-xs text-gray-400">{user?.email}</div>
          </div>
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-purple rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopBar;
