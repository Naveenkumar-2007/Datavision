import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  User,
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
import { useAuth } from '@/contexts/AuthContext';

const Settings: React.FC = () => {
  const { user: authUser } = useAuth();
  const setStoreUser = useUserStore((state) => state.setUser);

  // Profile state - synced from auth on mount, saved per user
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    company: '',
    role: '',
    avatar: '',
  });

  // Load profile from localStorage per user
  useEffect(() => {
    if (authUser) {
      const savedProfile = localStorage.getItem(`userProfile_${authUser.id}`);
      if (savedProfile) {
        const parsed = JSON.parse(savedProfile);
        setProfile(parsed);
      } else {
        // Initialize from OAuth user data
        setProfile({
          name: authUser.user_metadata?.full_name || authUser.email?.split('@')[0] || '',
          email: authUser.email || '',
          company: '',
          role: '',
          avatar: authUser.user_metadata?.avatar_url || '',
        });
      }
    }
  }, [authUser]);

  // Sync to userStore when profile changes
  useEffect(() => {
    if (authUser && profile.email) {
      setStoreUser({
        id: authUser.id,
        name: profile.name,
        email: profile.email,
        company: profile.company,
        role: profile.role,
        avatar: profile.avatar,
      });
    }
  }, [profile, authUser, setStoreUser]);

  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    reports: true,
    insights: true,
  });

  const [preferences, setPreferences] = useState(() => {
    const userId = authUser?.id || localStorage.getItem('userId') || 'default';
    const saved = localStorage.getItem(`userPreferences_${userId}`);
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
    const userId = authUser?.id || localStorage.getItem('userId') || 'default';

    // Save profile per user
    localStorage.setItem(`userProfile_${userId}`, JSON.stringify(profile));

    // Save preferences per user
    localStorage.setItem(`userPreferences_${userId}`, JSON.stringify({ notifications, preferences }));

    // Also save to global userPreferences for other components to read
    localStorage.setItem('userPreferences', JSON.stringify({ notifications, preferences }));

    // Apply theme immediately
    if (preferences.theme === 'light') {
      document.documentElement.classList.add('light-theme');
      document.documentElement.classList.remove('dark');
      document.body.classList.add('light-theme');
    } else {
      document.documentElement.classList.remove('light-theme');
      document.documentElement.classList.add('dark');
      document.body.classList.remove('light-theme');
    }

    alert('✅ Settings saved successfully! The page will now reload to apply all theme changes.');
    window.location.reload();
  };

  const handleExportData = async () => {
    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`http://localhost:8000/api/v1/files/list/${userId}`);
      const data = await response.json();

      const exportData = {
        user: profile,
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

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleChangeAvatar = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert('❌ File size exceeds 5MB limit.');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        setProfile({ ...profile, avatar: reader.result as string });
        alert('✅ Avatar updated successfully!');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleChangePassword = () => {
    alert('🔒 Password change feature coming soon!');
  };

  const handleResetTheme = () => {
    // Force reset to dark mode
    localStorage.removeItem('userPreferences');
    document.documentElement.classList.remove('light-theme');
    document.body.classList.remove('light-theme');
    setPreferences({ ...preferences, theme: 'dark' });
    alert('✅ Theme reset to Dark Mode! The page will now reload.');
    window.location.reload();
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
        className="flex items-center gap-4 mb-2"
      >
        <img src="/logo.png" alt="Logo" className="w-12 h-12 rounded-xl shadow-lg shadow-orange-500/20" />
        <div>
          <h1 className="text-4xl font-bold text-white">Settings</h1>
          <p className="text-gray-400">Manage your account and preferences</p>
        </div>
      </motion.div>

      {/* Profile Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <User className="w-6 h-6 text-orange-400" />
          <h2 className="text-2xl font-semibold text-white">Profile</h2>
        </div>

        <div className="space-y-6">
          <div className="flex items-center space-x-6">
            <div className="relative w-24 h-24 rounded-2xl overflow-hidden bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center group">
              {profile.avatar ? (
                <img src={profile.avatar} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <User className="w-12 h-12 text-white" />
              )}
            </div>
            <div>
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept="image/png, image/jpeg, image/jpg"
                onChange={handleFileChange}
              />
              <button
                onClick={handleChangeAvatar}
                className="px-4 py-2 bg-orange-600 rounded-xl text-white font-medium hover:bg-orange-700 transition-colors shadow-md"
              >
                Change Avatar
              </button>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">PNG, JPG up to 5MB</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Full Name</label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Email</label>
              <input
                type="email"
                value={profile.email}
                disabled
                className="w-full px-4 py-3 bg-dark-card/50 border border-dark-border rounded-xl text-gray-400 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Company <span className="text-gray-600">(optional)</span></label>
              <input
                type="text"
                placeholder="Your Company"
                value={profile.company}
                onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Role <span className="text-gray-600">(optional)</span></label>
              <input
                type="text"
                placeholder="Your Role"
                value={profile.role}
                onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
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
          <Bell className="w-6 h-6 text-orange-400" />
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
                <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-orange-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
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
          <Shield className="w-6 h-6 text-orange-400" />
          <h2 className="text-2xl font-semibold text-white">Preferences</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Theme</label>
            <select
              value={preferences.theme}
              onChange={(e) => setPreferences({ ...preferences, theme: e.target.value })}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
            <button
              onClick={handleResetTheme}
              className="mt-2 text-xs text-orange-400 hover:text-orange-300 underline"
            >
              Reset to Dark Mode
            </button>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Language</label>
            <select
              value={preferences.language}
              onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
            >
              <option value="en">English (Only)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Currency (All values will be converted to this)</label>
            <select
              value={preferences.currency || 'INR'}
              onChange={(e) => setPreferences({ ...preferences, currency: e.target.value })}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
            >
              <optgroup label="Major Currencies">
                <option value="USD">$ US Dollar (USD)</option>
                <option value="EUR">€ Euro (EUR)</option>
                <option value="GBP">£ British Pound (GBP)</option>
                <option value="JPY">¥ Japanese Yen (JPY)</option>
                <option value="CHF">Fr Swiss Franc (CHF)</option>
                <option value="CAD">C$ Canadian Dollar (CAD)</option>
                <option value="AUD">A$ Australian Dollar (AUD)</option>
              </optgroup>
              <optgroup label="Asian Currencies">
                <option value="INR">₹ Indian Rupee (INR)</option>
                <option value="CNY">¥ Chinese Yuan (CNY)</option>
                <option value="HKD">HK$ Hong Kong Dollar (HKD)</option>
                <option value="SGD">S$ Singapore Dollar (SGD)</option>
                <option value="KRW">₩ South Korean Won (KRW)</option>
                <option value="THB">฿ Thai Baht (THB)</option>
                <option value="MYR">RM Malaysian Ringgit (MYR)</option>
                <option value="IDR">Rp Indonesian Rupiah (IDR)</option>
                <option value="PHP">₱ Philippine Peso (PHP)</option>
                <option value="VND">₫ Vietnamese Dong (VND)</option>
                <option value="BDT">৳ Bangladeshi Taka (BDT)</option>
                <option value="PKR">₨ Pakistani Rupee (PKR)</option>
              </optgroup>
              <optgroup label="Middle East & Africa">
                <option value="AED">د.إ UAE Dirham (AED)</option>
                <option value="SAR">﷼ Saudi Riyal (SAR)</option>
                <option value="ZAR">R South African Rand (ZAR)</option>
                <option value="EGP">E£ Egyptian Pound (EGP)</option>
                <option value="NGN">₦ Nigerian Naira (NGN)</option>
              </optgroup>
              <optgroup label="Americas">
                <option value="BRL">R$ Brazilian Real (BRL)</option>
                <option value="MXN">Mex$ Mexican Peso (MXN)</option>
                <option value="ARS">AR$ Argentine Peso (ARS)</option>
                <option value="CLP">CLP$ Chilean Peso (CLP)</option>
                <option value="COP">COL$ Colombian Peso (COP)</option>
              </optgroup>
              <optgroup label="Europe">
                <option value="SEK">kr Swedish Krona (SEK)</option>
                <option value="NOK">kr Norwegian Krone (NOK)</option>
                <option value="DKK">kr Danish Krone (DKK)</option>
                <option value="PLN">zł Polish Zloty (PLN)</option>
                <option value="CZK">Kč Czech Koruna (CZK)</option>
                <option value="RUB">₽ Russian Ruble (RUB)</option>
                <option value="TRY">₺ Turkish Lira (TRY)</option>
              </optgroup>
              <optgroup label="Oceania">
                <option value="NZD">NZ$ New Zealand Dollar (NZD)</option>
              </optgroup>
            </select>
            <p className="text-xs text-gray-500 mt-2">Uploaded data in other currencies will be auto-converted</p>
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
          <Database className="w-6 h-6 text-orange-400" />
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
            <span className="text-orange-400 text-sm font-medium">Export</span>
          </button>

          <button
            onClick={handleRebuildIndexes}
            className="w-full p-4 bg-dark-card border border-dark-border rounded-xl text-left hover:bg-dark-hover transition-colors flex items-center justify-between"
          >
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-5 h-5 text-orange-400" />
              <div>
                <div className="text-white font-medium">Rebuild Indexes</div>
                <div className="text-sm text-gray-400">Refresh FAISS and GraphRAG indexes</div>
              </div>
            </div>
            <span className="text-orange-400 text-sm font-medium">Rebuild</span>
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
          <Key className="w-6 h-6 text-orange-400" />
          <h2 className="text-2xl font-semibold text-white">Security</h2>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Current Password</label>
            <input
              type="password"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">New Password</label>
            <input
              type="password"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Confirm New Password</label>
            <input
              type="password"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-orange-500"
            />
          </div>
          <button
            onClick={handleChangePassword}
            className="px-6 py-3 bg-orange-600 rounded-xl text-white font-medium hover:bg-orange-700 transition-colors shadow-md"
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
          className="px-8 py-3 bg-gradient-to-r from-orange-500 to-amber-600 rounded-xl text-white font-semibold hover:shadow-glow transition-all flex items-center space-x-2"
        >
          <Save className="w-5 h-5" />
          <span>Save Changes</span>
        </button>
      </motion.div>
    </div>
  );
};

export default Settings;
