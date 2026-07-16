import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import React, { useEffect, useState, useCallback, Suspense } from 'react';
import { AnimatePresence } from 'framer-motion';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import { useUserStore } from './store/userStore';
import SplashScreen from './components/SplashScreen';
import { Loader2 } from 'lucide-react';
import Landing from './pages/Landing';
import Login from './pages/Login';
import AuthCallback from './pages/AuthCallback';
import AppLayout from './components/layout/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';

// Lazy load non-critical routes for performance optimization
const DataHub = React.lazy(() => import('./pages/DataHub'));
const AnalystChat = React.lazy(() => import('./pages/AnalystChat'));
const Reports = React.lazy(() => import('./pages/Reports'));
const Settings = React.lazy(() => import('./pages/Settings'));
const NotificationSettings = React.lazy(() => import('./pages/NotificationSettings'));
const Signup = React.lazy(() => import('./pages/Signup'));
const ForgotPassword = React.lazy(() => import('./pages/ForgotPassword'));
const UpdatePassword = React.lazy(() => import('./pages/UpdatePassword'));
const EmailConfirm = React.lazy(() => import('./pages/EmailConfirm'));
const AutonomousDashboard = React.lazy(() => import('./pages/AutonomousDashboard'));
const MLPredictions = React.lazy(() => import('./pages/MLPredictions'));
const Clustering = React.lazy(() => import('./pages/Clustering'));
const ScenarioSimulator = React.lazy(() => import('./pages/ScenarioSimulator'));
const DataLineage = React.lazy(() => import('./pages/DataLineage'));
const Collaborate = React.lazy(() => import('./pages/Collaborate'));
const Developer = React.lazy(() => import('./pages/Developer'));

const PrivacyPolicy = React.lazy(() => import('./pages/PrivacyPolicy'));
const TermsOfService = React.lazy(() => import('./pages/TermsOfService'));
const HelpCenter = React.lazy(() => import('./pages/HelpCenter'));

const DataStories = React.lazy(() => import('./pages/DataStories'));
const PipelineBuilder = React.lazy(() => import('./pages/PipelineBuilder'));
const EmbedWidget = React.lazy(() => import('./pages/EmbedWidget'));


function App() {
  const [showSplash, setShowSplash] = useState(false); // Splash screen disabled

  const { isDark, accentTheme } = useUserStore();

  // Apply theme on mount & changes
  useEffect(() => {
    // 1. Dark/Light Mode
    if (isDark) {
      document.documentElement.classList.remove('light-theme');
      document.documentElement.classList.add('dark');
      document.body.classList.remove('light-theme');
    } else {
      document.documentElement.classList.add('light-theme');
      document.documentElement.classList.remove('dark');
      document.body.classList.add('light-theme');
    }

    // 2. Accent Theme
    // Remove all existing accent themes
    document.documentElement.classList.forEach(className => {
      if (className.startsWith('theme-')) {
        document.documentElement.classList.remove(className);
      }
    });
    // Add new accent theme
    if (accentTheme && accentTheme !== 'default') {
      document.documentElement.classList.add(`theme-${accentTheme}`);
    }
  }, [isDark, accentTheme]);

  const handleSplashComplete = useCallback(() => {
    setShowSplash(false);
  }, []);

  return (
    <>
      <AnimatePresence>
        {showSplash && (
          <SplashScreen onComplete={handleSplashComplete} />
        )}
      </AnimatePresence>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <Suspense fallback={<div className="flex h-screen w-full items-center justify-center bg-[var(--bg-primary)]"><div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div></div>}>
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

                {/* Redirect /overview to /data-hub */}
                <Route path="/overview" element={<Navigate to="/data-hub" replace />} />

                {/* Standalone Embedded Widget */}
                <Route path="/embed/:widgetId" element={<EmbedWidget />} />

                {/* Chat - Full screen without main navigation */}
                <Route path="/chat" element={
                  <ProtectedRoute>
                    <AnalystChat />
                  </ProtectedRoute>
                } />

                {/* Protected routes wrapped in AppLayout */}
                <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                  <Route path="/dashboard" element={<AutonomousDashboard />} />
                  <Route path="/data-hub" element={<DataHub />} />
                  <Route path="/datahub" element={<DataHub />} />
                  <Route path="/ml-predictions" element={<MLPredictions />} />
                  <Route path="/pipelines" element={<PipelineBuilder />} />
                  <Route path="/clustering" element={<Clustering />} />
                  
                  {/* V3 New Pages */}
                  <Route path="/simulator" element={<ScenarioSimulator />} />
                  <Route path="/lineage" element={<DataLineage />} />
                  <Route path="/collaborate" element={<Collaborate />} />
                  <Route path="/developer" element={<Developer />} />
                  
                  {/* MLOps Enterprise Platform Routes */}


                  <Route path="/reports" element={<Reports />} />
                  <Route path="/data-stories" element={<DataStories />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/settings/notifications" element={<NotificationSettings />} />
                  
                  {/* Legacy redirects */}
                  <Route path="/automl" element={<Navigate to="/ml-predictions" replace />} />
                </Route>

                {/* Redirect any unknown route to home */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </>
  );
}

export default App;



