/**
 * Overview Page - Visual Intelligence Dashboard
 * Uses autonomous visual intelligence from backend.
 */

import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { AutonomousRenderer } from '../components/AutonomousRenderer';
import { Loader2, AlertCircle, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface OverviewData {
  layout_spec: any;
  visual_primitives: any[];
  color_palette: any;
  narrative_elements?: any[];
  data_sample?: any[];
}

const Overview: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [engineOutput, setEngineOutput] = useState<OverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const context = useOutletContext<any>();
  const isDark = context?.isDark ?? true;
  const userId = context?.userId || localStorage.getItem('userId');

  useEffect(() => {
    fetchData();
  }, [userId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Build URL with user_id
      const params = new URLSearchParams();
      if (userId) {
        params.append('user_id', userId);
      }

      const response = await fetch(`/api/v1/autonomous/overview?${params.toString()}`, {
        headers: {
          'X-User-ID': userId || ''
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Check if we have valid data
      if (data.visual_primitives && data.visual_primitives.length > 0) {
        setEngineOutput(data);
      } else if (data.narrative_elements && data.narrative_elements.length > 0) {
        // Check for "no data" message
        const noDataMsg = data.narrative_elements.find((n: any) =>
          n.content?.toLowerCase().includes('no data') ||
          n.content?.toLowerCase().includes('upload')
        );
        if (noDataMsg) {
          setError('no_data');
        } else {
          setEngineOutput(data);
        }
      } else {
        setError('no_data');
      }
    } catch (err: any) {
      console.error('Error fetching overview:', err);
      setError(err.message || 'Failed to load overview');
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        gap: '16px',
        background: isDark
          ? 'linear-gradient(135deg, #0f172a 0%, #134e4a 60%, #064e3b 100%)'
          : 'var(--bg-primary)'
      }}>
        <Loader2 className="animate-spin" size={48} style={{ color: '#14b8a6' }} />
        <p style={{ color: isDark ? '#94a3b8' : '#64748b', fontSize: '1rem' }}>
          Initializing Visual Intelligence Engine...
        </p>
      </div>
    );
  }

  // No data state
  if (error === 'no_data') {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        gap: '24px',
        padding: '40px',
        background: isDark
          ? 'linear-gradient(135deg, #0f172a 0%, #134e4a 60%, #064e3b 100%)'
          : 'var(--bg-primary)'
      }}>
        <div style={{
          padding: '24px',
          borderRadius: '16px',
          background: isDark ? 'rgba(15, 23, 42, 0.8)' : 'white',
          border: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0'}`,
          textAlign: 'center',
          maxWidth: '400px'
        }}>
          <Upload size={48} style={{ color: '#14b8a6', marginBottom: '16px' }} />
          <h2 style={{
            color: isDark ? '#f1f5f9' : '#0f172a',
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '12px'
          }}>
            No Data Found
          </h2>
          <p style={{
            color: isDark ? '#94a3b8' : '#64748b',
            marginBottom: '24px',
            lineHeight: 1.6
          }}>
            Upload your data files to see intelligent visualizations and insights.
          </p>
          <button
            onClick={() => navigate('/data-hub')}
            style={{
              padding: '12px 24px',
              backgroundColor: '#14b8a6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              margin: '0 auto'
            }}
          >
            <Upload size={18} />
            Upload Data
          </button>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        gap: '16px',
        padding: '40px',
        background: isDark
          ? 'linear-gradient(135deg, #0f172a 0%, #134e4a 60%, #064e3b 100%)'
          : 'var(--bg-primary)'
      }}>
        <div style={{
          padding: '24px',
          borderRadius: '12px',
          background: isDark ? 'rgba(239, 68, 68, 0.1)' : '#fef2f2',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          textAlign: 'center',
          maxWidth: '400px'
        }}>
          <AlertCircle size={48} style={{ color: '#ef4444', marginBottom: '16px' }} />
          <h3 style={{ color: '#ef4444', marginBottom: '8px' }}>Error Loading Overview</h3>
          <p style={{ color: isDark ? '#94a3b8' : '#64748b', marginBottom: '16px' }}>{error}</p>
          <button
            onClick={fetchData}
            style={{
              padding: '10px 20px',
              backgroundColor: '#14b8a6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // No engine output
  if (!engineOutput) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        color: isDark ? '#94a3b8' : '#64748b'
      }}>
        No data available. Please upload a dataset.
      </div>
    );
  }

  // Render the autonomous visualization
  return (
    <div style={{ minHeight: '100vh' }}>
      <AutonomousRenderer
        layoutSpec={engineOutput.layout_spec}
        visualPrimitives={engineOutput.visual_primitives}
        colorPalette={engineOutput.color_palette}
        narrativeElements={engineOutput.narrative_elements}
        data={engineOutput.data_sample || []}
        mode="overview"
        isDarkMode={isDark}
      />
    </div>
  );
};

export default Overview;
