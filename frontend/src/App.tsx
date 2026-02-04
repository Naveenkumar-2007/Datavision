import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import SplashScreen from './components/SplashScreen';
import Landing from './pages/Landing';
import DataHub from './pages/DataHub';
import AnalystChat from './pages/AnalystChat';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import NotificationSettings from './pages/NotificationSettings';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import UpdatePassword from './pages/UpdatePassword';
import AuthCallback from './pages/AuthCallback';
import EmailConfirm from './pages/EmailConfirm';
import AppLayout from './components/layout/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
// 🏆 Autonomous Dashboard - Power BI-like AI-generated dashboards
import AutonomousDashboard from './pages/AutonomousDashboard';
// 🤖 AutoML - ML Results Visualization
import AutoML from './pages/AutoML';
// 🧠 ML Predictions - Real ML Charts & Predictions
import MLPredictions from './pages/MLPredictions';
// 🎯 Clustering - Unsupervised Learning
import Clustering from './pages/Clustering';
// 📋 Legal & Help Pages
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsOfService from './pages/TermsOfService';
import HelpCenter from './pages/HelpCenter';
import { useUserStore } from './store/userStore';

function App() {
  const [showSplash, setShowSplash] = useState(false); // Splash screen disabled

  const { isDark } = useUserStore();

  // Apply theme on mount & changes
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.remove('light-theme');
      document.documentElement.classList.add('dark');
      document.body.classList.remove('light-theme');
    } else {
      document.documentElement.classList.add('light-theme');
      document.documentElement.classList.remove('dark');
      document.body.classList.add('light-theme');
    }
  }, [isDark]);

  const handleSplashComplete = useCallback(() => {
    setShowSplash(false);
  }, []);

  return (
    <>
      {/* Splash Screen */}
      <AnimatePresence>
        {showSplash && (
          <SplashScreen onComplete={handleSplashComplete} />
        )}
      </AnimatePresence>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/auth/update-password" element={<UpdatePassword />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route path="/auth/confirm" element={<EmailConfirm />} />
              {/* Legal & Help Pages */}
              <Route path="/privacy" element={<PrivacyPolicy />} />
              <Route path="/terms" element={<TermsOfService />} />
              <Route path="/help" element={<HelpCenter />} />

              {/* Redirect /overview to /chat - Overview page removed */}
              <Route path="/overview" element={<Navigate to="/data-hub" replace />} />

              {/* Chat - Full screen without main navigation */}
              <Route path="/chat" element={
                <ProtectedRoute>
                  <AnalystChat />
                </ProtectedRoute>
              } />

              {/* Protected routes with AppLayout (main navigation) */}
              <Route element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }>
                <Route path="/data-hub" element={<DataHub />} />
                <Route path="/datahub" element={<DataHub />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/settings/notifications" element={<NotificationSettings />} />
                {/* 🏆 Autonomous Dashboard - Power BI-like AI-generated */}
                <Route path="/dashboard" element={<AutonomousDashboard />} />
                {/* 🤖 AutoML - ML Results Page */}
                <Route path="/automl" element={<AutoML />} />
                {/* 🧠 ML Predictions - Real
                 ML Charts */}
                <Route path="/ml-predictions" element={<MLPredictions />} />
                {/* 🎯 Clustering - Unsupervised Learning */}
                <Route path="/clustering" element={<Clustering />} />
              </Route>
            </Routes>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </>
  );
}

export default App;



