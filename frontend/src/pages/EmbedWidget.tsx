import React, { useEffect, Suspense } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import AutonomousDashboard from './AutonomousDashboard';
import MLPredictions from './MLPredictions';
import DataHub from './DataHub';
import AnomalyMonitor from './AnomalyMonitor';
import { useUserStore } from '@/store/userStore';

const EmbedWidget: React.FC = () => {
  const { widgetId } = useParams<{ widgetId: string }>();
  const [searchParams] = useSearchParams();
  const theme = searchParams.get('theme') || 'dark';
  
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light-theme');
      document.body.style.backgroundColor = '#0f172a';
      useUserStore.setState({ isDark: true });
    } else if (theme === 'light') {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light-theme');
      document.body.style.backgroundColor = '#f8fafc';
      useUserStore.setState({ isDark: false });
    }
    // No overflow hidden so the dashboard can scroll
    return () => {
      document.body.style.backgroundColor = '';
    };
  }, [theme]);

  // The api.ts interceptor automatically extracts ?token= from the URL and applies it!
  
  if (widgetId === 'full-dashboard') {
    return (
      <div className="w-full h-screen overflow-auto bg-transparent">
        <Suspense fallback={<div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-indigo-500 w-8 h-8" /></div>}>
          <AutonomousDashboard />
        </Suspense>
      </div>
    );
  }

  if (widgetId === 'ml-predictions') {
    return (
      <div className="w-full h-screen overflow-auto bg-transparent">
        <Suspense fallback={<div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-indigo-500 w-8 h-8" /></div>}>
          <MLPredictions />
        </Suspense>
      </div>
    );
  }

  if (widgetId === 'data-hub') {
    return (
      <div className="w-full h-screen overflow-auto bg-transparent">
        <Suspense fallback={<div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-indigo-500 w-8 h-8" /></div>}>
          <DataHub />
        </Suspense>
      </div>
    );
  }

  if (widgetId === 'anomaly-monitor') {
    return (
      <div className="w-full h-screen overflow-auto bg-transparent">
        <Suspense fallback={<div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-indigo-500 w-8 h-8" /></div>}>
          <AnomalyMonitor />
        </Suspense>
      </div>
    );
  }

  const isDark = theme === 'dark';

  return (
    <div className={`w-full h-screen p-6 flex flex-col items-center justify-center font-sans ${isDark ? 'text-white' : 'text-slate-900'}`}>
      <div className={`p-8 rounded-2xl border text-center max-w-md ${isDark ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-white shadow-xl'}`}>
        <h2 className="text-2xl font-bold mb-2">DataVision Embed</h2>
        <p className="opacity-70 text-sm mb-6">Connected securely via API Token.</p>
        <div className={`inline-block px-4 py-2 rounded-lg font-mono text-xs ${isDark ? 'bg-indigo-500/20 text-indigo-400' : 'bg-indigo-50 text-indigo-700'}`}>
          Widget: {widgetId} not natively supported.
        </div>
      </div>
    </div>
  );
};

export default EmbedWidget;
