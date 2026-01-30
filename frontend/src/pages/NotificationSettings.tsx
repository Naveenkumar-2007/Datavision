import React, { useState, useEffect } from 'react';
import { useUserStore } from '../store/userStore';
import { supabase } from '../lib/supabase';
import { Bell, Mail, MessageSquare, TrendingUp, Moon } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';

interface NotificationSettings {
    email_notifications: boolean;
    push_notifications: boolean;
    weekly_reports: boolean;
    ai_insights: boolean;
    severity_threshold: 'low' | 'medium' | 'high';
    dnd_start: string | null;
    dnd_end: string | null;
}

export default function NotificationSettings() {
    const { user } = useUserStore();
    const toast = useToast();
    const [settings, setSettings] = useState<NotificationSettings>({
        email_notifications: true,
        push_notifications: false,
        weekly_reports: true,
        ai_insights: true,
        severity_threshold: 'medium',
        dnd_start: null,
        dnd_end: null,
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadSettings();
    }, [user]);

    async function loadSettings() {
        if (!user) return;

        try {
            // FIRST: Try to load from localStorage (fastest and most reliable)
            const localStorageKey = `notification_settings_${user.id}`;
            const savedSettings = localStorage.getItem(localStorageKey);

            if (savedSettings) {
                const parsed = JSON.parse(savedSettings);
                setSettings(parsed);
                console.log('✓ Loaded settings from localStorage:', parsed);
                setLoading(false);
                return;
            }

            // SECOND: Try to load from API
            const workspaceId = user.id;
            const session = await supabase.auth.getSession();
            const token = session.data.session?.access_token;

            if (!token) {
                console.warn('No auth token, using default settings');
                setLoading(false);
                return;
            }

            const response = await fetch(
                `/api/settings/${workspaceId}/${user.id}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (response.ok) {
                const data = await response.json();
                if (data) {
                    setSettings(data);
                    // Save to localStorage as backup
                    localStorage.setItem(localStorageKey, JSON.stringify(data));
                    console.log('✓ Loaded settings from API and saved to localStorage');
                }
            } else if (response.status === 404) {
                console.log('No saved settings found, using defaults');
            } else {
                console.error('Failed to load settings:', response.statusText);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        } finally {
            setLoading(false);
        }
    }

    async function updateSetting(key: keyof NotificationSettings, value: any) {
        if (!user) return;

        // Optimistic update
        const newSettings = { ...settings, [key]: value };
        setSettings(newSettings);

        // IMMEDIATELY save to localStorage (guaranteed to work)
        const localStorageKey = `notification_settings_${user.id}`;
        localStorage.setItem(localStorageKey, JSON.stringify(newSettings));
        console.log(`✓ Setting saved to localStorage: ${key} = ${value}`);

        setSaving(true);

        try {
            // Also try to save to API (best effort)
            const workspaceId = user.id;
            const session = await supabase.auth.getSession();
            const token = session.data.session?.access_token;

            if (!token) {
                console.warn('No auth token, settings saved locally only');
                setSaving(false);
                return;
            }

            const response = await fetch(`/api/settings/${workspaceId}/${user.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ [key]: value }),
            });

            if (response.ok) {
                console.log(`✓ Setting also saved to API: ${key} = ${value}`);
            } else {
                console.warn('API save failed, but localStorage save succeeded');
            }

            // Handle push notification registration
            if (key === 'push_notifications' && value === true) {
                await registerPushNotifications(workspaceId);
            }
        } catch (error) {
            console.error('Failed to update setting in API:', error);
            console.log('Settings still saved in localStorage');
        } finally {
            setSaving(false);
        }
    }

    async function registerPushNotifications(workspaceId: string) {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            toast.warning('Push notifications are not supported in this browser');
            setSettings((prev) => ({ ...prev, push_notifications: false }));
            return;
        }

        try {
            // Register service worker
            const registration = await navigator.serviceWorker.register('/sw.js');

            // Wait for service worker to be ready
            await navigator.serviceWorker.ready;

            // Subscribe to push notifications
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(
                    import.meta.env.VITE_VAPID_PUBLIC_KEY || ''
                ),
            });

            // Send subscription to backend
            const session = await supabase.auth.getSession();
            const token = session.data.session?.access_token;

            await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    workspace_id: workspaceId,
                    user_id: user?.id,
                    token: JSON.stringify(subscription),
                    platform: 'web',
                }),
            });

            toast.success('Push notifications enabled successfully');
            console.log('Push notifications registered successfully');
        } catch (error) {
            console.error('Failed to register push notifications:', error);
            toast.error('Failed to enable push notifications. Please try again.');
            setSettings((prev) => ({ ...prev, push_notifications: false }));
        }
    }

    function urlBase64ToUint8Array(base64String: string) {
        const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto p-4 sm:p-6">
            {/* Header */}
            <div className="mb-6 sm:mb-8">
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2 sm:gap-3">
                    <Bell className="h-6 w-6 sm:h-8 sm:w-8 text-orange-500" />
                    Notifications
                </h1>
                <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400 mt-2">
                    Manage how you receive updates from DataVision
                </p>
            </div>

            {/* Settings List */}
            <div className="space-y-3 sm:space-y-4">
                {/* Email Notifications */}
                <SettingCard
                    icon={Mail}
                    title="Email Notifications"
                    description="Receive updates via email"
                    checked={settings.email_notifications}
                    onChange={(checked) => updateSetting('email_notifications', checked)}
                    disabled={saving}
                />

                {/* Push Notifications */}
                <SettingCard
                    icon={MessageSquare}
                    title="Push Notifications"
                    description="Get browser notifications"
                    checked={settings.push_notifications}
                    onChange={(checked) => updateSetting('push_notifications', checked)}
                    disabled={saving}
                />

                {/* Weekly Reports */}
                <SettingCard
                    icon={TrendingUp}
                    title="Weekly Reports"
                    description="Automatic weekly business reports"
                    checked={settings.weekly_reports}
                    onChange={(checked) => updateSetting('weekly_reports', checked)}
                    disabled={saving}
                />

                {/* AI Insights */}
                <SettingCard
                    icon={Bell}
                    title="AI Insights"
                    description="Get notified about new insights"
                    checked={settings.ai_insights}
                    onChange={(checked) => updateSetting('ai_insights', checked)}
                    disabled={saving}
                />
            </div>

            {/* Advanced Settings */}
            <div className="mt-6 sm:mt-8 p-4 sm:p-6 bg-gray-50 dark:bg-dark-surface rounded-xl border border-gray-200 dark:border-dark-border">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Advanced Settings
                </h3>

                {/* Severity Threshold */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Notification Severity Threshold
                    </label>
                    <select
                        value={settings.severity_threshold}
                        onChange={(e) =>
                            updateSetting(
                                'severity_threshold',
                                e.target.value as 'low' | 'medium' | 'high'
                            )
                        }
                        className="w-full px-4 py-3 sm:py-2 text-base bg-white dark:bg-dark-bg border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                        disabled={saving}
                    >
                        <option value="low">All Insights (Low, Medium, High)</option>
                        <option value="medium">Important Only (Medium, High)</option>
                        <option value="high">Critical Only (High)</option>
                    </select>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Only receive notifications for insights at or above this severity level
                    </p>
                </div>

                {/* Do Not Disturb */}
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Moon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Do Not Disturb Window
                        </label>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <input
                                type="time"
                                value={settings.dnd_start || ''}
                                onChange={(e) => updateSetting('dnd_start', e.target.value)}
                                className="w-full px-4 py-3 sm:py-2 text-base bg-white dark:bg-dark-bg border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                                placeholder="Start time"
                                disabled={saving}
                            />
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Start time
                            </p>
                        </div>
                        <div>
                            <input
                                type="time"
                                value={settings.dnd_end || ''}
                                onChange={(e) => updateSetting('dnd_end', e.target.value)}
                                className="w-full px-4 py-3 sm:py-2 text-base bg-white dark:bg-dark-bg border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                                placeholder="End time"
                                disabled={saving}
                            />
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                End time
                            </p>
                        </div>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        No notifications will be sent during this time window
                    </p>
                </div>
            </div>

            {/* Save Indicator */}
            {saving && (
                <div className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                    Saving...
                </div>
            )}
        </div>
    );
}

interface SettingCardProps {
    icon: React.ElementType;
    title: string;
    description: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
    disabled?: boolean;
}

function SettingCard({
    icon: Icon,
    title,
    description,
    checked,
    onChange,
    disabled,
}: SettingCardProps) {
    return (
        <div className="flex items-center justify-between p-4 sm:p-5 bg-white dark:bg-dark-surface rounded-xl border border-gray-200 dark:border-dark-border hover:border-orange-300 dark:hover:border-orange-700 transition-colors">
            <div className="flex items-center gap-3 sm:gap-4 flex-1 min-w-0">
                <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg flex-shrink-0">
                    <Icon className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                </div>
                <div className="min-w-0 flex-1">
                    <h3 className="font-medium text-gray-900 dark:text-white text-sm sm:text-base">{title}</h3>
                    <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 truncate">
                        {description}
                    </p>
                </div>
            </div>

            {/* Toggle Switch */}
            <label className="relative inline-flex items-center cursor-pointer flex-shrink-0 ml-3">
                <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={checked}
                    onChange={(e) => onChange(e.target.checked)}
                    disabled={disabled}
                />
                <div
                    className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 dark:peer-focus:ring-orange-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-orange-500 disabled:opacity-50 disabled:cursor-not-allowed"
                ></div>
            </label>
        </div>
    );
}
