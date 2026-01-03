import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User,
  Shield,
  Database,
  Trash2,
  Download,
  RefreshCw,
  Save,
  Key,
  Mail,
  Clock,
  Calendar,
  Send,
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabase';



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
  }, [profile.email, profile.name, profile.role, profile.company, profile.avatar, authUser?.id, setStoreUser]);


  // Email Report Preferences (daily/weekly scheduling)
  const [emailPrefs, setEmailPrefs] = useState({
    daily_report_enabled: false,
    daily_report_hour: 8,
    daily_report_minute: 0,
    weekly_report_enabled: true,
    weekly_report_day: 1, // Monday
    weekly_report_hour: 9,
    weekly_report_minute: 0,
    email_address: '',
  });
  const [emailPrefsLoading, setEmailPrefsLoading] = useState(false);
  const [testEmailSending, setTestEmailSending] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);

  // Auto-hide status message after 5 seconds
  useEffect(() => {
    if (statusMessage) {
      const timer = setTimeout(() => setStatusMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [statusMessage]);

  // Load email preferences from backend
  useEffect(() => {
    const loadEmailPrefs = async () => {
      try {
        const userId = authUser?.id || localStorage.getItem('userId') || 'default';
        const response = await fetch(`http://localhost:8000/api/v1/settings/email-prefs`, {
          headers: { 'X-User-ID': userId }
        });
        if (response.ok) {
          const data = await response.json();
          if (data.preferences) {
            setEmailPrefs(data.preferences);
          }
        }
      } catch (error) {
        console.error('Failed to load email preferences:', error);
      }
    };
    loadEmailPrefs();
  }, [authUser?.id]);

  // Save email preferences to backend
  const saveEmailPrefs = async () => {
    setEmailPrefsLoading(true);
    setStatusMessage(null);
    try {
      const userId = authUser?.id || localStorage.getItem('userId') || 'default';
      console.log('Saving email prefs:', emailPrefs);
      const response = await fetch(`http://localhost:8000/api/v1/settings/email-prefs`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(emailPrefs)
      });
      const data = await response.json();
      console.log('Save response:', data);
      if (response.ok) {
        setStatusMessage({
          type: 'success',
          text: 'Email preferences saved successfully. DataVision will send automated reports according to your schedule.'
        });
      } else {
        throw new Error(data.detail || 'Failed to save');
      }
    } catch (error: any) {
      console.error('Failed to save email preferences:', error);
      setStatusMessage({
        type: 'error',
        text: 'Unable to save email preferences: ' + (error.message || 'Please check your connection.')
      });
    } finally {
      setEmailPrefsLoading(false);
    }
  };

  // Send test email
  const sendTestEmail = async () => {
    if (!emailPrefs.email_address) {
      setStatusMessage({ type: 'error', text: 'Please enter your email address first' });
      return;
    }
    setTestEmailSending(true);
    setStatusMessage(null);
    try {
      const userId = authUser?.id || localStorage.getItem('userId') || 'default';
      const response = await fetch(`http://localhost:8000/api/v1/settings/email-prefs/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({ email_address: emailPrefs.email_address })
      });
      if (response.ok) {
        setStatusMessage({
          type: 'success',
          text: 'Test email sent successfully! Please check your inbox for a message from DataVision.'
        });
      } else {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to send');
      }
    } catch (error: any) {
      console.error('Failed to send test email:', error);
      setStatusMessage({
        type: 'error',
        text: 'Unable to send test email: ' + (error.message || 'Please verify your email address and try again.')
      });
    } finally {
      setTestEmailSending(false);
    }
  };

  // State for daily report sending
  const [dailyReportSending, setDailyReportSending] = useState(false);

  // Send daily report NOW (bypasses scheduler for testing)
  const sendDailyReportNow = async () => {
    if (!emailPrefs.email_address) {
      setStatusMessage({ type: 'error', text: 'Please enter your email address first and save preferences' });
      return;
    }
    setDailyReportSending(true);
    setStatusMessage(null);
    try {
      const userId = authUser?.id || localStorage.getItem('userId') || 'default';
      const response = await fetch(`http://localhost:8000/api/v1/settings/email-prefs/send-daily-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({ email_address: emailPrefs.email_address })
      });
      const data = await response.json();
      if (response.ok && data.success) {
        setStatusMessage({
          type: 'success',
          text: 'Daily Data Report sent successfully! Check your inbox for comprehensive insights from DataVision.'
        });
      } else {
        throw new Error(data.detail || data.error?.message || 'Failed to send daily report');
      }
    } catch (error: any) {
      console.error('Failed to send daily report:', error);
      setStatusMessage({
        type: 'error',
        text: 'Unable to send daily report: ' + (error.message || 'Please ensure you have data uploaded and try again.')
      });
    } finally {
      setDailyReportSending(false);
    }
  };

  const dayOptions = [
    { value: 0, label: 'Sunday' },
    { value: 1, label: 'Monday' },
    { value: 2, label: 'Tuesday' },
    { value: 3, label: 'Wednesday' },
    { value: 4, label: 'Thursday' },
    { value: 5, label: 'Friday' },
    { value: 6, label: 'Saturday' },
  ];


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

  const handleSave = async () => {
    const userId = authUser?.id || localStorage.getItem('userId') || 'default';

    // Save profile per user
    localStorage.setItem(`userProfile_${userId}`, JSON.stringify(profile));

    // Save preferences per user
    localStorage.setItem(`userPreferences_${userId}`, JSON.stringify({ preferences }));

    // Also save to global userPreferences for other components to read
    localStorage.setItem('userPreferences', JSON.stringify({ preferences }));

    // Save Email Preferences to Backend
    if (emailPrefs.email_address) {
      // We don't want the individual success message from saveEmailPrefs to be overwritten immediately
      // so we call the API fetch directly or handle it here. 
      // Reusing saveEmailPrefs is easiest but we need to manage the UI feedback.
      await saveEmailPrefs();
    }

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

    // Small delay to let the user see the "Email preferences saved" message if it appeared
    setTimeout(() => {
      alert('Settings saved successfully. DataVision will apply your preferences.');
      window.location.reload();
    }, 1000);
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

  const handleChangePassword = async () => {
    // Get password values from inputs
    const currentPasswordInput = document.getElementById('current-password') as HTMLInputElement;
    const newPasswordInput = document.getElementById('new-password') as HTMLInputElement;
    const confirmPasswordInput = document.getElementById('confirm-password') as HTMLInputElement;

    const newPassword = newPasswordInput?.value || '';
    const confirmPassword = confirmPasswordInput?.value || '';

    // Validation
    if (!newPassword || !confirmPassword) {
      alert('❌ Please enter new password and confirm it.');
      return;
    }

    if (newPassword.length < 6) {
      alert('❌ Password must be at least 6 characters.');
      return;
    }

    if (newPassword !== confirmPassword) {
      alert('❌ Passwords do not match!');
      return;
    }

    try {
      // Update password using Supabase
      const { error } = await supabase.auth.updateUser({
        password: newPassword
      });

      if (error) {
        throw error;
      }

      // Clear inputs
      if (currentPasswordInput) currentPasswordInput.value = '';
      if (newPasswordInput) newPasswordInput.value = '';
      if (confirmPasswordInput) confirmPasswordInput.value = '';

      alert('✅ Password changed successfully!');
    } catch (error: any) {
      console.error('Password change failed:', error);
      alert('❌ Failed to change password: ' + (error.message || 'Unknown error'));
    }
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
    <div className="space-y-8 max-w-5xl mx-auto p-6" style={{ minHeight: '100vh' }}>
      {/* Status Message Toast */}
      <AnimatePresence>
        {statusMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -20, height: 0 }}
            className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-xl shadow-2xl backdrop-blur-md border flex items-center gap-3 ${statusMessage.type === 'success'
              ? 'bg-emerald-900/90 border-emerald-500/50 text-emerald-100'
              : statusMessage.type === 'error'
                ? 'bg-rose-900/90 border-rose-500/50 text-rose-100'
                : 'bg-blue-900/90 border-blue-500/50 text-blue-100'
              }`}
          >
            {statusMessage.type === 'success' && <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />}
            {statusMessage.type === 'error' && <div className="w-2 h-2 rounded-full bg-rose-400 animate-pulse" />}
            <span className="font-medium">{statusMessage.text}</span>
            <button
              onClick={() => setStatusMessage(null)}
              className="ml-4 opacity-70 hover:opacity-100"
            >
              ×
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4 mb-2"
      >
        <img
          src="/logo.png"
          alt="DataVision Logo"
          className="w-12 h-12 object-contain rounded-xl shadow-lg"
        />
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
          <User className="w-6 h-6 text-teal-400" />
          <h2 className="text-2xl font-semibold text-white">Profile</h2>
        </div>

        <div className="space-y-6">
          <div className="flex items-center space-x-6">
            <div className="relative w-24 h-24 rounded-2xl overflow-hidden bg-gradient-to-br from-teal-500 to-amber-600 flex items-center justify-center group">
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
                className="px-4 py-2 bg-teal-600 rounded-xl text-white font-medium hover:bg-orange-700 transition-colors shadow-md"
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
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500"
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
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Role <span className="text-gray-600">(optional)</span></label>
              <input
                type="text"
                placeholder="Your Role"
                value={profile.role}
                onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Company Intelligence */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <svg className="w-6 h-6 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <div>
            <h2 className="text-2xl font-semibold text-white">Company Intelligence</h2>
            <p className="text-sm text-gray-400">AI will adapt terminology and benchmarks to your company</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Company Name */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Company Name</label>
              <input
                type="text"
                placeholder="Your Company Inc"
                value={profile.company}
                onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500"
              />
              <p className="text-xs text-gray-500 mt-1">AI will reference this in responses</p>
            </div>

            {/* Industry */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Industry</label>
              <select
                value={preferences.industry || 'other'}
                onChange={(e) => setPreferences({ ...preferences, industry: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500 appearance-none cursor-pointer"
              >
                <option value="saas">SaaS / Software</option>
                <option value="ecommerce">E-commerce / Retail</option>
                <option value="fintech">Fintech / Banking</option>
                <option value="healthcare">Healthcare</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="consulting">Consulting / Services</option>
                <option value="education">Education</option>
                <option value="other">Other</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">For industry-specific benchmarks</p>
            </div>

            {/* Fiscal Year End */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Fiscal Year End Month</label>
              <select
                value={preferences.fiscalYearEnd || 12}
                onChange={(e) => setPreferences({ ...preferences, fiscalYearEnd: parseInt(e.target.value) })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500 appearance-none cursor-pointer"
              >
                <option value={1}>January</option>
                <option value={2}>February</option>
                <option value={3}>March</option>
                <option value={4}>April</option>
                <option value={5}>May</option>
                <option value={6}>June</option>
                <option value={7}>July</option>
                <option value={8}>August</option>
                <option value={9}>September</option>
                <option value={10}>October</option>
                <option value={11}>November</option>
                <option value={12}>December</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">For accurate Q1-Q4 calculations</p>
            </div>

            {/* User Role */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Your Role</label>
              <select
                value={preferences.userRole || 'analyst'}
                onChange={(e) => setPreferences({ ...preferences, userRole: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500 appearance-none cursor-pointer"
              >
                <option value="executive">Executive (CEO/CFO/VP) - Quick summaries</option>
                <option value="manager">Manager - Actionable insights</option>
                <option value="analyst">Analyst - Detailed data tables</option>
                <option value="operator">Operator - Quick facts</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">AI adapts response format to your role</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Preferences */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <Shield className="w-6 h-6 text-teal-400" />
          <h2 className="text-2xl font-semibold text-white">Preferences</h2>
        </div>

        <div className="space-y-6">
          {/* Theme and Language Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Theme */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Theme</label>
              <select
                value={preferences.theme}
                onChange={(e) => setPreferences({ ...preferences, theme: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500 appearance-none cursor-pointer"
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </select>
              <button
                onClick={handleResetTheme}
                className="text-teal-400 text-sm mt-2 hover:underline"
              >
                Reset to Dark Mode
              </button>
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Language</label>
              <select
                value={preferences.language || 'en'}
                onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500 appearance-none cursor-pointer"
              >
                <option value="en">English (Only)</option>
              </select>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Email Reports Scheduling */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <Mail className="w-6 h-6 text-teal-400" />
          <h2 className="text-2xl font-semibold text-white">Email Reports</h2>
        </div>

        <div className="space-y-6">
          {/* Email Address */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Email Address for Reports</label>
            <input
              type="email"
              placeholder="your@email.com"
              value={emailPrefs.email_address || ''}
              onChange={(e) => setEmailPrefs({ ...emailPrefs, email_address: e.target.value })}
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500"
            />
            <p className="text-xs text-gray-500 mt-1">Leave blank to use your account email</p>
          </div>

          {/* Daily Reports */}
          <div className="p-4 bg-dark-card rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Clock className="w-5 h-5 text-teal-400" />
                <div>
                  <div className="text-white font-medium">Daily Reports</div>
                  <div className="text-sm text-gray-400">Receive daily data insights from DataVision</div>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={emailPrefs.daily_report_enabled}
                  onChange={(e) => setEmailPrefs({ ...emailPrefs, daily_report_enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-teal-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </label>
            </div>

            {emailPrefs.daily_report_enabled && (
              <div className="ml-8 flex items-center space-x-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Hour</label>
                  <select
                    value={emailPrefs.daily_report_hour}
                    onChange={(e) => setEmailPrefs({ ...emailPrefs, daily_report_hour: parseInt(e.target.value) })}
                    className="px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-teal-500"
                  >
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>{i.toString().padStart(2, '0')}</option>
                    ))}
                  </select>
                </div>
                <span className="text-gray-400 mt-6">:</span>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Minute</label>
                  <select
                    value={emailPrefs.daily_report_minute}
                    onChange={(e) => setEmailPrefs({ ...emailPrefs, daily_report_minute: parseInt(e.target.value) })}
                    className="px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-teal-500"
                  >
                    {[0, 15, 30, 45].map((m) => (
                      <option key={m} value={m}>{m.toString().padStart(2, '0')}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Weekly Reports */}
          <div className="p-4 bg-dark-card rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Calendar className="w-5 h-5 text-teal-400" />
                <div>
                  <div className="text-white font-medium">Weekly Reports</div>
                  <div className="text-sm text-gray-400">Comprehensive weekly analysis from DataVision</div>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={emailPrefs.weekly_report_enabled}
                  onChange={(e) => setEmailPrefs({ ...emailPrefs, weekly_report_enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-teal-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </label>
            </div>

            {emailPrefs.weekly_report_enabled && (
              <div className="ml-8 grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Day</label>
                  <select
                    value={emailPrefs.weekly_report_day}
                    onChange={(e) => setEmailPrefs({ ...emailPrefs, weekly_report_day: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-teal-500"
                  >
                    {dayOptions.map((day) => (
                      <option key={day.value} value={day.value}>{day.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Hour</label>
                  <select
                    value={emailPrefs.weekly_report_hour}
                    onChange={(e) => setEmailPrefs({ ...emailPrefs, weekly_report_hour: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-teal-500"
                  >
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>{i.toString().padStart(2, '0')}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Minute</label>
                  <select
                    value={emailPrefs.weekly_report_minute}
                    onChange={(e) => setEmailPrefs({ ...emailPrefs, weekly_report_minute: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-teal-500"
                  >
                    {[0, 15, 30, 45].map((m) => (
                      <option key={m} value={m}>{m.toString().padStart(2, '0')}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={saveEmailPrefs}
              disabled={emailPrefsLoading}
              className="px-6 py-3 bg-gradient-to-r from-teal-500 to-amber-600 rounded-xl text-white font-medium hover:shadow-glow transition-all disabled:opacity-50 flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>{emailPrefsLoading ? 'Saving...' : 'Save Email Preferences'}</span>
            </button>
            <button
              onClick={sendTestEmail}
              disabled={testEmailSending}
              className="px-6 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 font-medium hover:bg-dark-hover transition-colors disabled:opacity-50 flex items-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>{testEmailSending ? 'Sending...' : 'Send Test Email'}</span>
            </button>
            <button
              onClick={sendDailyReportNow}
              disabled={dailyReportSending}
              className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl text-white font-medium hover:shadow-lg transition-all disabled:opacity-50 flex items-center space-x-2"
            >
              <Mail className="w-4 h-4" />
              <span>{dailyReportSending ? 'Sending Report...' : '📊 Send Daily Report Now'}</span>
            </button>
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
          <Database className="w-6 h-6 text-teal-400" />
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
            <span className="text-teal-400 text-sm font-medium">Export</span>
          </button>

          <button
            onClick={handleRebuildIndexes}
            className="w-full p-4 bg-dark-card border border-dark-border rounded-xl text-left hover:bg-dark-hover transition-colors flex items-center justify-between"
          >
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-5 h-5 text-teal-400" />
              <div>
                <div className="text-white font-medium">Rebuild Indexes</div>
                <div className="text-sm text-gray-400">Refresh FAISS and GraphRAG indexes</div>
              </div>
            </div>
            <span className="text-teal-400 text-sm font-medium">Rebuild</span>
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
          <Key className="w-6 h-6 text-teal-400" />
          <h2 className="text-2xl font-semibold text-white">Security</h2>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Current Password</label>
            <input
              id="current-password"
              type="password"
              placeholder="Enter current password (optional)"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500"
            />
            <p className="text-xs text-gray-500 mt-1">For OAuth users, leave this blank</p>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">New Password</label>
            <input
              id="new-password"
              type="password"
              placeholder="Enter new password (min 6 characters)"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Confirm New Password</label>
            <input
              id="confirm-password"
              type="password"
              placeholder="Confirm new password"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-teal-500"
            />
          </div>
          <button
            onClick={handleChangePassword}
            className="px-6 py-3 bg-teal-600 rounded-xl text-white font-medium hover:bg-orange-700 transition-colors shadow-md"
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
          className="px-8 py-3 bg-gradient-to-r from-teal-500 to-amber-600 rounded-xl text-white font-semibold hover:shadow-glow transition-all flex items-center space-x-2"
        >
          <Save className="w-5 h-5" />
          <span>Save Changes</span>
        </button>
      </motion.div>
    </div>
  );
};

export default Settings;
