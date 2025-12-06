import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  User,
  Mail,
  Bell,
  Shield,
  Database,
  Trash2,
  Download,
  RefreshCw,
  Save,
  Key,
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';

const Settings: React.FC = () => {
  const user = useUserStore((state) => state.user);
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    reports: true,
    insights: true,
  });

  const [preferences, setPreferences] = useState(() => {
    const saved = localStorage.getItem('userPreferences');
    if (saved) {
      const parsed = JSON.parse(saved);
      return parsed.preferences || {
        theme: 'dark',
        language: 'en',
        timezone: 'Asia/Kolkata',
        currency: 'INR'
      };
    }
    return {
      theme: 'dark',
      language: 'en',
      timezone: 'Asia/Kolkata',
      currency: 'INR'
    };
  });

  const handleSave = () => {
    localStorage.setItem('userPreferences', JSON.stringify({ notifications, preferences }));
    
    // Apply theme
    if (preferences.theme === 'light') {
      document.documentElement.classList.add('light-theme');
    } else {
      document.documentElement.classList.remove('light-theme');
    }
    
    alert('✅ Settings saved successfully! Refresh page to see theme changes.');
  };

  const handleExportData = async () => {
    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`http://localhost:8000/api/v1/files/list/${userId}`);
      const data = await response.json();
      
      const exportData = {
        user: user,
        preferences: preferences,
        files: data.files || [],
        exportedAt: new Date().toISOString()
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `data_export_${Date.now()}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      alert('✅ Data exported successfully!');
    } catch (error: any) {
      console.error('Export failed:', error);
      alert('❌ Failed to export data: ' + error.message);
    }
  };

  const handleRebuildIndexes = async () => {
    if (!confirm('Rebuild all indexes from uploaded files? This may take a few minutes.')) return;
    
    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`http://localhost:8000/api/v1/files/${userId}/rebuild`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();
      
      if (result.success) {
        alert(`✅ ${result.message}\nFiles processed: ${result.files_processed}`);
      } else {
        throw new Error(result.detail || 'Rebuild failed');
      }
    } catch (error: any) {
      console.error('Rebuild failed:', error);
      alert('❌ Failed to rebuild indexes: ' + error.message);
    }
  };

  const handleDeleteAllData = async () => {
    if (!confirm('⚠️ WARNING: This will permanently delete ALL your files, indexes, and data. This cannot be undone!')) return;
    if (!confirm('Are you ABSOLUTELY sure? Type "DELETE" to confirm.') || prompt('Type DELETE to confirm:') !== 'DELETE') {
      alert('Deletion cancelled.');
      return;
    }
    
    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`http://localhost:8000/api/v1/files/${userId}/all`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();
      
      if (result.success) {
        alert('✅ All data deleted successfully. Refreshing...');
        window.location.reload();
      } else {
        throw new Error(result.detail || 'Deletion failed');
      }
    } catch (error: any) {
      console.error('Delete failed:', error);
      alert('❌ Failed to delete data: ' + error.message);
    }
  };

  const handleChangeAvatar = () => {
    alert('📷 Avatar upload feature coming soon!');
  };

  const handleChangePassword = () => {
    alert('🔒 Password change feature coming soon!');
  };

  const handleCancel = () => {
    if (confirm('Discard unsaved changes?')) {
      window.location.reload();
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-bold text-white mb-2">Settings</h1>
        <p className="text-gray-400">Manage your account and preferences</p>
      </motion.div>

      {/* Profile Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <User className="w-6 h-6 text-primary-400" />
          <h2 className="text-2xl font-semibold text-white">Profile</h2>
        </div>

        <div className="space-y-6">
          <div className="flex items-center space-x-6">
            <div className="w-24 h-24 bg-gradient-to-br from-primary-500 to-accent-purple rounded-2xl flex items-center justify-center">
              <User className="w-12 h-12 text-white" />
            </div>
            <div>
              <button 
                onClick={handleChangeAvatar}
                className="px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-xl text-primary-400 font-medium hover:bg-primary-500/20 transition-colors"
              >
                Change Avatar
              </button>
              <p className="text-sm text-gray-400 mt-2">PNG, JPG up to 5MB</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Full Name</label>
              <input
                type="text"
                defaultValue={user?.name}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Email</label>
              <input
                type="email"
                defaultValue={user?.email}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Company</label>
              <input
                type="text"
                placeholder="Your Company"
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Role</label>
              <input
                type="text"
                placeholder="Your Role"
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Notifications */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <Bell className="w-6 h-6 text-primary-400" />
          <h2 className="text-2xl font-semibold text-white">Notifications</h2>
        </div>

        <div className="space-y-4">
          {[
            { key: 'email', label: 'Email Notifications', description: 'Receive updates via email' },
            { key: 'push', label: 'Push Notifications', description: 'Get browser notifications' },
            { key: 'reports', label: 'Weekly Reports', description: 'Automatic weekly business reports' },
            { key: 'insights', label: 'AI Insights', description: 'Get notified about new insights' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between p-4 bg-dark-card rounded-xl">
              <div>
                <div className="text-white font-medium mb-1">{item.label}</div>
                <div className="text-sm text-gray-400">{item.description}</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={notifications[item.key as keyof typeof notifications]}
                  onChange={(e) =>
                    setNotifications({ ...notifications, [item.key]: e.target.checked })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </label>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Preferences */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <Shield className="w-6 h-6 text-primary-400" />
          <h2 className="text-2xl font-semibold text-white">Preferences</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Theme</label>
            <select
              value={preferences.theme}
              onChange={(e) => setPreferences({ ...preferences, theme: e.target.value })}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="auto">Auto</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Language</label>
            <select
              value={preferences.language}
              onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            >
              <option value="en">English (Only)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Currency</label>
            <select
              value={preferences.currency || 'INR'}
              onChange={(e) => setPreferences({ ...preferences, currency: e.target.value })}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            >
              <option value="INR">₹ Indian Rupee (INR)</option>
              <option value="USD">$ US Dollar (USD)</option>
              <option value="EUR">€ Euro (EUR)</option>
              <option value="GBP">£ British Pound (GBP)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Timezone</label>
            <select
              value={preferences.timezone}
              onChange={(e) => setPreferences({ ...preferences, timezone: e.target.value })}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            >
              <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
              <option value="America/New_York">America/New York (EST)</option>
              <option value="Europe/London">Europe/London (GMT)</option>
              <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
            </select>
          </div>
        </div>
      </motion.div>

      {/* Data Management */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <Database className="w-6 h-6 text-primary-400" />
          <h2 className="text-2xl font-semibold text-white">Data Management</h2>
        </div>

        <div className="space-y-4">
          <button 
            onClick={handleExportData}
            className="w-full p-4 bg-dark-card border border-dark-border rounded-xl text-left hover:bg-dark-hover transition-colors flex items-center justify-between"
          >
            <div className="flex items-center space-x-3">
              <Download className="w-5 h-5 text-gray-400" />
              <div>
                <div className="text-white font-medium">Export All Data</div>
                <div className="text-sm text-gray-400">Download your complete data archive</div>
              </div>
            </div>
            <span className="text-primary-400 text-sm font-medium">Export</span>
          </button>

          <button 
            onClick={handleRebuildIndexes}
            className="w-full p-4 bg-dark-card border border-dark-border rounded-xl text-left hover:bg-dark-hover transition-colors flex items-center justify-between"
          >
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-5 h-5 text-gray-400" />
              <div>
                <div className="text-white font-medium">Rebuild Indexes</div>
                <div className="text-sm text-gray-400">Refresh FAISS and GraphRAG indexes</div>
              </div>
            </div>
            <span className="text-primary-400 text-sm font-medium">Rebuild</span>
          </button>

          <button 
            onClick={handleDeleteAllData}
            className="w-full p-4 bg-accent-red/10 border border-accent-red/20 rounded-xl text-left hover:bg-accent-red/20 transition-colors flex items-center justify-between"
          >
            <div className="flex items-center space-x-3">
              <Trash2 className="w-5 h-5 text-accent-red" />
              <div>
                <div className="text-accent-red font-medium">Delete All Data</div>
                <div className="text-sm text-gray-400">Permanently remove all files and indexes</div>
              </div>
            </div>
            <span className="text-accent-red text-sm font-medium">Delete</span>
          </button>
        </div>
      </motion.div>

      {/* Security */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <Key className="w-6 h-6 text-primary-400" />
          <h2 className="text-2xl font-semibold text-white">Security</h2>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Current Password</label>
            <input
              type="password"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">New Password</label>
            <input
              type="password"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Confirm New Password</label>
            <input
              type="password"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            />
          </div>
          <button 
            onClick={handleChangePassword}
            className="px-6 py-3 bg-primary-500/10 border border-primary-500/20 rounded-xl text-primary-400 font-medium hover:bg-primary-500/20 transition-colors"
          >
            Change Password
          </button>
        </div>
      </motion.div>

      {/* Save Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="flex justify-end space-x-4"
      >
        <button 
          onClick={handleCancel}
          className="px-6 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-400 font-medium hover:bg-dark-hover hover:text-gray-200 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="px-8 py-3 bg-gradient-to-r from-primary-500 to-accent-purple rounded-xl text-white font-semibold hover:shadow-glow transition-all flex items-center space-x-2"
        >
          <Save className="w-5 h-5" />
          <span>Save Changes</span>
        </button>
      </motion.div>
    </div>
  );
};

export default Settings;
