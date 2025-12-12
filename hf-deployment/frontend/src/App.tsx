import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import Landing from './pages/Landing';
import Overview from './pages/Overview';
import DataHub from './pages/DataHub';
import AnalystChat from './pages/AnalystChat';
import Dashboards from './pages/Dashboards';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import NotificationSettings from './pages/NotificationSettings';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AuthCallback from './pages/AuthCallback';
import AppLayout from './components/layout/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  // Apply theme on mount - DEFAULT IS DARK
  useEffect(() => {
    // By default, ensure dark mode (remove light-theme class)
    const saved = localStorage.getItem('userPreferences');

    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Only add light-theme if EXPLICITLY set to light
        if (parsed.preferences?.theme === 'light') {
          // LIGHT MODE: Add 'light-theme', remove 'dark'
          document.documentElement.classList.add('light-theme');
          document.documentElement.classList.remove('dark');
          document.body.classList.add('light-theme');
        } else {
          // DARK MODE: Remove 'light-theme', add 'dark'
          document.documentElement.classList.remove('light-theme');
          document.documentElement.classList.add('dark');
          document.body.classList.remove('light-theme');
        }
      } catch (error) {
        // On error, default to dark
        document.documentElement.classList.remove('light-theme');
        document.documentElement.classList.add('dark');
        document.body.classList.remove('light-theme');
      }
    } else {
      // No saved preference = DARK MODE (default)
      document.documentElement.classList.remove('light-theme');
      document.documentElement.classList.add('dark');
      document.body.classList.remove('light-theme');
    }
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/auth/callback" element={<AuthCallback />} />

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
            <Route path="/overview" element={<Overview />} />
            <Route path="/data-hub" element={<DataHub />} />
            <Route path="/dashboards" element={<Dashboards />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/settings/notifications" element={<NotificationSettings />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
