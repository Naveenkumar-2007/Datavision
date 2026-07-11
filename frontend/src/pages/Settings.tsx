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
  Sparkles,
  Brain,
  FileText,
  Loader,
  KeyRound,
  MessageSquare
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/auth-client';
import { useConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/services/api';
import LogoImage from '@/components/LogoImage';
import { getAuthHeadersSync } from '@/utils/userId';
import AnalystChat from '@/pages/AnalystChat';



const Settings: React.FC = () => {
  const { confirm, ConfirmModal } = useConfirmModal();
  const toast = useToast();

  const { user: authUser } = useAuth();
  const { isDark, toggleTheme, setTheme, setUser: setStoreUser } = useUserStore();
  const [isChatOpen, setIsChatOpen] = useState(false);

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

  // AI Email Agent State
  const [aiEmailPrompt, setAiEmailPrompt] = useState('');
  const [aiEmailGenerating, setAiEmailGenerating] = useState(false);
  const [aiEmailSending, setAiEmailSending] = useState(false);
  const [generatedEmail, setGeneratedEmail] = useState<{ subject: string; body: string } | null>(null);
  const [dataContextUsed, setDataContextUsed] = useState<string>('');

  // Data Management Stats
  const [dataStats, setDataStats] = useState({
    filesUploaded: 0,
    mlModelsTrained: 0,
    reportsSent: 0,
    dashboards: 0
  });

  // Load data stats on mount
  useEffect(() => {
    const loadDataStats = async () => {
      try {
        const userId = authUser?.id || localStorage.getItem('userId') || 'default';
        console.log('Loading stats for user:', userId);

        // Get files count from correct API endpoint
        let filesCount = 0;
        try {
          const filesRes = await fetch(`/api/v1/files/list/${userId}`, {
            headers: getAuthHeadersSync()
          });
          if (filesRes.ok) {
            const filesData = await filesRes.json();
            filesCount = Array.isArray(filesData) ? filesData.length :
              (filesData.files ? filesData.files.length : 0);
          }
        } catch (e) {
          console.warn('Files API error:', e);
        }

        // Check ML model in localStorage - try multiple keys
        let mlCount = 0;
        const allKeys = Object.keys(localStorage);
        for (const key of allKeys) {
          if (key.includes('automl') || key.includes('ml_result') || key.includes('AutoML')) {
            mlCount = 1;
            break;
          }
        }

        // Check for dashboards in localStorage
        let dashboardCount = 0;
        for (const key of allKeys) {
          if (key.includes('dashboard') || key.includes('Dashboard')) {
            dashboardCount = 1;
            break;
          }
        }

        setDataStats({
          filesUploaded: filesCount,
          mlModelsTrained: mlCount,
          reportsSent: 0,
          dashboards: dashboardCount
        });
      } catch (error) {
        console.error('Failed to load data stats:', error);
      }
    };

    loadDataStats();
  }, [authUser]);

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
        const response = await fetch(`/api/v1/settings/email-prefs`, {
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
      const response = await fetch(`/api/v1/settings/email-prefs`, {
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
      const response = await fetch(`/api/v1/settings/email-prefs/test`, {
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
      const response = await fetch(`/api/v1/settings/email-prefs/send-daily-report`, {
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

  // AI Email Agent - Generate email using LLM with real data
  const handleGenerateAIEmail = async () => {
    if (!aiEmailPrompt || aiEmailPrompt.length < 5) {
      setStatusMessage({ type: 'error', text: 'Please describe what the email should contain' });
      return;
    }
    if (!emailPrefs.email_address) {
      setStatusMessage({ type: 'error', text: 'Please enter your email address first' });
      return;
    }

    setAiEmailGenerating(true);
    setGeneratedEmail(null);
    setStatusMessage(null);

    try {
      const userId = authUser?.id || localStorage.getItem('userId') || 'default';
      const response = await fetch('/api/v1/settings/email-prefs/generate-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          prompt: aiEmailPrompt,
          email_address: emailPrefs.email_address,
          send_immediately: false
        })
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setGeneratedEmail(data.email);
        setDataContextUsed(data.data_context_used || '');
        setStatusMessage({ type: 'success', text: 'Email generated! Review and send when ready.' });
      } else {
        throw new Error(data.detail || 'Failed to generate email');
      }
    } catch (error: any) {
      console.error('AI email generation failed:', error);
      setStatusMessage({ type: 'error', text: 'AI generation failed: ' + error.message });
    } finally {
      setAiEmailGenerating(false);
    }
  };

  // Send the AI-generated email
  const handleSendAIEmail = async () => {
    if (!generatedEmail) return;

    setAiEmailSending(true);
    try {
      const userId = authUser?.id || localStorage.getItem('userId') || 'default';
      const response = await fetch('/api/v1/settings/email-prefs/send-custom-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          email_address: emailPrefs.email_address,
          subject: generatedEmail.subject,
          body: generatedEmail.body
        })
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setStatusMessage({ type: 'success', text: '✅ Email sent successfully!' });
        setGeneratedEmail(null);
        setAiEmailPrompt('');
      } else {
        throw new Error(data.detail || 'Failed to send email');
      }
    } catch (error: any) {
      setStatusMessage({ type: 'error', text: 'Send failed: ' + error.message });
    } finally {
      setAiEmailSending(false);
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
    // Theme is now managed globally by userStore, so we don't need to manually update the DOM here.
    // DOM updates happen in App.tsx via userStore.

    // Small delay to let the user see the "Email preferences saved" message if it appeared
    setTimeout(() => {
      toast.success('Settings saved successfully. Reloading to apply preferences...');
      setTimeout(() => window.location.reload(), 1500);
    }, 500);
  };

  const handleExportData = async () => {
    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`/api/v1/files/list/${userId}`, {
        headers: getAuthHeadersSync()
      });
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
      toast.success('Data exported successfully!');
    } catch (error: any) {
      console.error('Export failed:', error);
      toast.error('Failed to export data: ' + error.message);
    }
  };

  const handleRebuildIndexes = async () => {
    const confirmed = await confirm({
      title: 'Rebuild Indexes',
      message: 'Rebuild all indexes from uploaded files? This may take a few minutes for large datasets.',
      confirmText: 'Rebuild',
      variant: 'warning',
      icon: <RefreshCw className="w-6 h-6" />
    });

    if (!confirmed) return;

    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`/api/v1/files/${userId}/rebuild`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();

      if (result.success) {
        toast.success(`${result.message} - Files processed: ${result.files_processed}`);
      } else {
        throw new Error(result.detail || 'Rebuild failed');
      }
    } catch (error: any) {
      console.error('Rebuild failed:', error);
      toast.error('Failed to rebuild indexes: ' + error.message);
    }
  };

  const handleDeleteAllData = async () => {
    const confirmed = await confirm({
      title: 'Delete All Data',
      message: 'This will permanently delete ALL your files, trained models, indexes, and data. This action cannot be undone and will require re-uploading all your files.',
      confirmText: 'Delete Everything',
      cancelText: 'Cancel',
      variant: 'danger',
      requireTypedConfirmation: 'DELETE',
    });

    if (!confirmed) return;

    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`/api/v1/files/${userId}/all`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();

      if (result.success) {
        toast.deleted('All Data Deleted', 'Your account data has been cleared. Refreshing...');
        setTimeout(() => window.location.reload(), 1500);
      } else {
        throw new Error(result.detail || 'Deletion failed');
      }
    } catch (error: any) {
      console.error('Delete failed:', error);
      toast.error('Delete Failed', error.message);
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
        toast.error('File size exceeds 5MB limit.');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        setProfile({ ...profile, avatar: reader.result as string });
        toast.success('Avatar updated successfully!');
      };
      reader.readAsDataURL(file);
    }
  };

  const [forgotPasswordLoading, setForgotPasswordLoading] = useState(false);

  const handleChangePassword = async () => {
    // Get password values from inputs
    const currentPasswordInput = document.getElementById('current-password') as HTMLInputElement;
    const newPasswordInput = document.getElementById('new-password') as HTMLInputElement;
    const confirmPasswordInput = document.getElementById('confirm-password') as HTMLInputElement;

    const newPassword = newPasswordInput?.value || '';
    const confirmPassword = confirmPasswordInput?.value || '';

    // Validation
    if (!newPassword || !confirmPassword) {
      toast.error('Please enter new password and confirm it.');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters.');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match!');
      return;
    }

    try {
      // Update password
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

      toast.success('Password changed successfully!');
    } catch (error: any) {
      console.error('Password change failed:', error);
      toast.error('Failed to change password: ' + (error.message || 'Unknown error'));
    }
  };

  // Send forgot password email
  const handleForgotPassword = async () => {
    const userEmail = profile.email || authUser?.email;
    if (!userEmail) {
      setStatusMessage({ type: 'error', text: 'No email address found for your account.' });
      return;
    }

    setForgotPasswordLoading(true);
    try {
      // Use custom backend endpoint for branded password reset emails
      const response = await api.post('/api/v1/settings/auth/request-password-reset', {
        email: userEmail.trim().toLowerCase()
      });

      if (response.data.success) {
        setStatusMessage({
          type: 'success',
          text: `Password reset email sent to ${userEmail}. Please check your inbox (and spam folder).`
        });
      } else {
        throw new Error(response.data.message || 'Failed to send reset email');
      }
    } catch (error: any) {
      console.error('Forgot password failed:', error);
      // Still show success for security (don't reveal if email exists)
      setStatusMessage({
        type: 'success',
        text: `If an account exists with ${userEmail}, you will receive a password reset link shortly.`
      });
    } finally {
      setForgotPasswordLoading(false);
    }
  };

  const handleResetTheme = () => {
    // Force reset to dark mode using store
    setTheme(true);
    setPreferences({ ...preferences, theme: 'dark' });
    setStatusMessage({ type: 'success', text: '✅ Theme reset to Dark Mode!' });
  };

  const handleCancel = async () => {
    const confirmed = await confirm({
      title: 'Discard Changes',
      message: 'Are you sure you want to discard your unsaved changes?',
      confirmText: 'Discard',
      cancelText: 'Keep Editing',
      variant: 'warning'
    });
    if (confirmed) {
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
        <div className="mb-2">
          <h1 className="text-4xl font-bold" style={{ color: 'var(--text-primary)' }}>Settings</h1>
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
          <User className="w-6 h-6 text-green-400" />
          <h2 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>Profile</h2>
        </div>

        <div className="space-y-6">
          <div className="flex items-center space-x-6">
            <div className="relative w-24 h-24 rounded-2xl overflow-hidden bg-gradient-to-br from-green-500 to-amber-600 flex items-center justify-center group">
              {profile.avatar ? (
                <img src={profile.avatar} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <User className="w-12 h-12" style={{ color: 'var(--text-primary)' }} />
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
                className="px-4 py-2 bg-primary-600 rounded-xl text-white font-medium hover:bg-amber-700 transition-colors shadow-md"
              >
                Change Avatar
              </button>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">PNG, JPG up to 5MB</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Full Name</label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className="w-full px-4 py-3 glass-input rounded-xl text-gray-200 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Email</label>
              <input
                type="email"
                value={profile.email}
                disabled
                className="w-full px-4 py-3 rounded-xl text-gray-400 cursor-not-allowed border border-[var(--border-color)] bg-[var(--bg-hover)]"
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
                className="w-full px-4 py-3 glass-input rounded-xl text-gray-200 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Role <span className="text-gray-600">(optional)</span></label>
              <input
                type="text"
                placeholder="Your Role"
                value={profile.role}
                onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                className="w-full px-4 py-3 glass-input rounded-xl text-gray-200 focus:outline-none"
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* AI Guardrails & Security */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="glass-card p-8 border border-red-500/20"
      >
        <div className="flex items-center space-x-4 mb-2">
          <Shield className="w-6 h-6 text-red-500" />
          <h2 className="text-2xl font-semibold text-white">Enterprise Security & AI Guardrails</h2>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30 uppercase tracking-wider font-bold">Admin Only</span>
        </div>
        <p className="text-sm text-gray-400 mb-6">Manage data privacy and configure output guardrails for the autonomous Agentic AI.</p>

        <div className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-dark-card rounded-xl border border-gray-800">
            <div>
              <div className="text-white font-medium mb-1">PII Data Masking Vault</div>
              <div className="text-sm text-gray-400">Automatically scrub SSNs, credit cards, and sensitive identifiers before data hits the LLM.</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-red-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-dark-card rounded-xl border border-gray-800">
            <div>
              <div className="text-white font-medium mb-1">NeMo Output Guardrails</div>
              <div className="text-sm text-gray-400">Strictly prevent the AI Analyst from hallucinating metrics or executing unsafe python code.</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-red-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-dark-card rounded-xl border border-gray-800">
            <div>
              <div className="text-white font-medium mb-1">Automated AI Evals</div>
              <div className="text-sm text-gray-400">Run background validation models to score the AI's predictions before presenting to users.</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-red-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
          </div>
        </div>
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-card p-8"
      >
        <div className="flex items-center space-x-4 mb-6">
          <Shield className="w-6 h-6 text-primary-400" />
          <h2 className="text-2xl font-semibold text-white">Preferences</h2>
        </div>

        <div className="space-y-6">
          {/* Theme and Language Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
            {/* Base Theme */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Base Appearance</label>
              <select
                value={isDark ? 'dark' : 'light'}
                onChange={(e) => {
                  const newTheme = e.target.value;
                  setPreferences({ ...preferences, theme: newTheme });
                  setTheme(newTheme === 'dark');
                }}
                className="w-full px-4 py-3 rounded-xl focus:outline-none focus:border-primary-500 appearance-none cursor-pointer"
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderColor: 'var(--border-color)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)'
                }}
              >
                <option value="dark">🌙 Dark Mode</option>
                <option value="light">☀️ Light Mode</option>
              </select>
            </div>

            {/* Custom Theme Builder (Accent) */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Accent Theme</label>
              <select
                value={useUserStore.getState().accentTheme}
                onChange={(e) => {
                  const newAccent = e.target.value;
                  useUserStore.getState().setAccentTheme(newAccent);
                }}
                className="w-full px-4 py-3 rounded-xl focus:outline-none focus:border-primary-500 appearance-none cursor-pointer"
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderColor: 'var(--border-color)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)'
                }}
              >
                <option value="default">🟢 Default (Emerald/Green)</option>
                <option value="obsidian">🌌 Obsidian (Blue/Teal)</option>
                <option value="aurora">✨ Aurora (Purple/Indigo)</option>
                <option value="cyber">🔥 Cyber (Pink/Magenta)</option>
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
          <Mail className="w-6 h-6 text-primary-400" />
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
              className="w-full px-4 py-3 glass-input rounded-xl text-gray-200 focus:outline-none"
            />
            <p className="text-xs text-gray-500 mt-1">Leave blank to use your account email</p>
          </div>

          {/* Daily Reports */}
          <div className="p-4 bg-dark-card rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Clock className="w-5 h-5 text-primary-400" />
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
                <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </label>
            </div>

            {emailPrefs.daily_report_enabled && (
              <div className="ml-8 flex items-center space-x-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Hour</label>
                  <select
                    value={emailPrefs.daily_report_hour}
                    onChange={(e) => setEmailPrefs({ ...emailPrefs, daily_report_hour: parseInt(e.target.value) })}
                    className="px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-primary-500"
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
                    className="px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-primary-500"
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
                <Calendar className="w-5 h-5 text-primary-400" />
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
                <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </label>
            </div>

            {emailPrefs.weekly_report_enabled && (
              <div className="ml-4 sm:ml-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Day</label>
                  <select
                    value={emailPrefs.weekly_report_day}
                    onChange={(e) => setEmailPrefs({ ...emailPrefs, weekly_report_day: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-primary-500"
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
                    className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-primary-500"
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
                    className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:border-primary-500"
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
              className="px-6 py-3 bg-gradient-to-r from-primary-500 to-amber-600 rounded-xl text-white font-medium hover:shadow-glow transition-all disabled:opacity-50 flex items-center space-x-2"
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
            <button
              onClick={async () => {
                setDailyReportSending(true);
                try {
                  const userId = authUser?.id || localStorage.getItem('userId') || 'default';
                  const res = await fetch('/api/v1/settings/email-prefs/send-weekly-report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-User-ID': userId },
                    body: JSON.stringify({ email_address: emailPrefs.email_address })
                  });
                  const data = await res.json();
                  if (res.ok) {
                    setStatusMessage({ type: 'success', text: data.message || 'Weekly report sent!' });
                  } else {
                    setStatusMessage({ type: 'error', text: data.detail || 'Failed to send weekly report' });
                  }
                } catch (e) {
                  setStatusMessage({ type: 'error', text: 'Failed to send weekly report' });
                } finally {
                  setDailyReportSending(false);
                }
              }}
              disabled={dailyReportSending}
              className="px-6 py-3 bg-gradient-to-r from-green-600 to-cyan-600 rounded-xl text-white font-medium hover:shadow-lg hover:shadow-green-500/20 transition-all disabled:opacity-50 flex items-center space-x-2"
            >
              <Mail className="w-4 h-4" />
              <span>{dailyReportSending ? 'Sending...' : '📈 Send Weekly Report Now'}</span>
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
          <Database className="w-6 h-6 text-primary-400" />
          <div>
            <h2 className="text-2xl font-semibold text-white">Data Management</h2>
            <p className="text-sm text-gray-400">Manage your uploaded files and ML models</p>
          </div>
        </div>

        <div className="space-y-4">
          {/* Export All Data */}
          <button
            onClick={handleExportData}
            className="w-full p-4 bg-dark-card border border-dark-border rounded-xl text-left hover:bg-dark-hover hover:border-green-500/30 transition-colors flex items-center justify-between group"
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-green-500/10 group-hover:bg-green-500/20 transition-colors">
                <Download className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <div className="text-white font-medium">Export All Data</div>
                <div className="text-sm text-gray-400">Download files, settings, and ML results as JSON</div>
              </div>
            </div>
            <span className="text-green-400 text-sm font-medium group-hover:translate-x-1 transition-transform">Export →</span>
          </button>

          {/* Clear ML Models */}
          <button
            onClick={async () => {
              const confirmed = await confirm({
                title: 'Reset ML Models',
                message: 'Clear all ML training history and models? Your uploaded files will remain intact.',
                confirmText: 'Reset',
                variant: 'warning',
                icon: <RefreshCw className="w-6 h-6" />
              });
              if (confirmed) {
                try {
                  const userId = localStorage.getItem('userId') || authUser?.id || 'default';

                  // Call backend API to delete models from storage (v2 endpoint)
                  await api.delete(`/api/v2/autonomous/models/${userId}`);

                  // Also clear localStorage cache
                  localStorage.removeItem(`automl_result_${userId}`);
                  localStorage.removeItem(`ml_training_${userId}`);
                  localStorage.removeItem(`model_history_${userId}`);

                  toast.success('ML models cleared! You can train fresh models now.');
                } catch (error: any) {
                  console.error('Failed to reset ML models:', error);
                  toast.error('Failed to reset ML models: ' + (error.message || 'Unknown error'));
                }
              }
            }}
            className="w-full p-4 bg-dark-card border border-dark-border rounded-xl text-left hover:bg-dark-hover hover:border-amber-500/30 transition-colors flex items-center justify-between group"
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-amber-500/10 group-hover:bg-amber-500/20 transition-colors">
                <RefreshCw className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <div className="text-white font-medium">Reset ML Models</div>
                <div className="text-sm text-gray-400">Clear training history to start fresh (keeps your files)</div>
              </div>
            </div>
            <span className="text-amber-400 text-sm font-medium group-hover:translate-x-1 transition-transform">Reset →</span>
          </button>

          {/* Delete All Data - Danger Zone */}
          <div className="pt-4 border-t border-dark-border">
            <p className="text-xs text-gray-500 mb-3 flex items-center gap-1">
              <span className="text-red-400">⚠️</span> Danger Zone
            </p>
            <button
              onClick={handleDeleteAllData}
              className="w-full p-4 bg-red-500/5 border border-red-500/20 rounded-xl text-left hover:bg-red-500/10 hover:border-red-500/40 transition-colors flex items-center justify-between group"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-red-500/10 group-hover:bg-red-500/20 transition-colors">
                  <Trash2 className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <div className="text-red-400 font-medium">Delete All Data</div>
                  <div className="text-sm text-gray-400">Permanently remove all files, models, and settings</div>
                </div>
              </div>
              <span className="text-red-400 text-sm font-medium">Delete</span>
            </button>
          </div>
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
              id="current-password"
              type="password"
              placeholder="Enter current password (optional)"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">For OAuth users, leave this blank</p>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">New Password</label>
            <input
              id="new-password"
              type="password"
              placeholder="Enter new password (min 6 characters)"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Confirm New Password</label>
            <input
              id="confirm-password"
              type="password"
              placeholder="Confirm new password"
              className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
            />
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleChangePassword}
              className="px-6 py-3 bg-primary-600 rounded-xl text-white font-medium hover:bg-amber-700 transition-colors shadow-md flex items-center gap-2"
            >
              <Key className="w-4 h-4" />
              Change Password
            </button>
            <button
              onClick={handleForgotPassword}
              disabled={forgotPasswordLoading}
              className="px-6 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 font-medium hover:bg-dark-hover hover:border-primary-500/30 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <KeyRound className="w-4 h-4" />
              {forgotPasswordLoading ? 'Sending...' : 'Forgot Password? Send Reset Email'}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            💡 Forgot your password? Click the button above to receive a reset link via email.
          </p>
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
          className="btn-secondary"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="btn-primary flex items-center space-x-2"
        >
          <Save className="w-5 h-5" />
          <span>Save Changes</span>
        </button>
      </motion.div>

      {/* Confirm Modal for Delete Operations */}
      <ConfirmModal />
    </div>
  );
};

export default Settings;
