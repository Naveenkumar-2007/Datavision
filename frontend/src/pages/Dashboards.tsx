/**
 * Autonomous Dashboard Page
 * ==========================
 * Uses autonomous visual intelligence from backend.
 * 
 * NO HARDCODED WIDGETS. NO TEMPLATES. NO FALLBACK PALETTES.
 * 
 * Everything is generated dynamically from data behavior.
 */

import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import AutonomousRenderer from '../components/AutonomousRenderer';


interface DashboardData {
  layout_spec: any;
  visual_primitives: any[];
  color_palette: any;
  interaction_config: any;
  behavior_scores: any;
  mode: string;
}


const DashboardLoading: React.FC = () => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
    gap: '16px'
  }}>
    <div style={{
      width: '48px',
      height: '48px',
      border: '4px solid var(--border-color)',
      borderTop: '4px solid var(--primary-color)',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite'
    }} />
    <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
      Synthesizing autonomous dashboard...
    </p>
    <style>{`
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    `}</style>
  </div>
);


const DashboardError: React.FC<{ error: string }> = ({ error }) => (
  <div style={{
    padding: '40px',
    textAlign: 'center',
    backgroundColor: 'var(--card-bg)',
    borderRadius: '12px',
    border: '1px solid var(--error-color)',
    margin: '40px'
  }}>
    <h2 style={{ color: 'var(--error-color)', marginBottom: '16px' }}>
      ⚠️ Error Generating Dashboard
    </h2>
    <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
      {error}
    </p>
    <button
      onClick={() => window.location.reload()}
      style={{
        padding: '12px 24px',
        backgroundColor: 'var(--primary-color)',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        fontSize: '1rem',
        fontWeight: 600
      }}
    >
      Retry
    </button>
  </div>
);


export default function Dashboards() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rawData, setRawData] = useState<any[]>([]);
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});

  const context = useOutletContext<any>();
  const isDark = context?.isDark ?? true;
  // Get userId from Supabase auth or use known user ID
  const userId = context?.userId || '21ed4a72-43de-4689-9556-7b866d79e9de';

  useEffect(() => {
    fetchAutonomousDashboard();
  }, [userId]);

  // Apply color palette to CSS variables - MUST be before any returns (React hooks rule)
  useEffect(() => {
    if (dashboardData?.color_palette) {
      const palette = dashboardData.color_palette;
      const root = document.documentElement;

      // Apply background gradient
      if (palette.background_gradient?.length >= 2) {
        root.style.setProperty('--dashboard-bg-start', palette.background_gradient[0]);
        root.style.setProperty('--dashboard-bg-end', palette.background_gradient[1]);
      }

      // Apply primary color
      if (palette.primary?.length > 0) {
        root.style.setProperty('--primary-color', palette.primary[0]);
      }
    }
  }, [dashboardData]);

  const fetchAutonomousDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/autonomous/dashboard?user_id=${userId}`, {
        headers: {
          'X-User-ID': userId
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.status === 'success') {
        setDashboardData(result.data);

        // Use actual raw data from API (real CSV data, not mock)
        if (result.raw_data && result.raw_data.length > 0) {
          setRawData(result.raw_data);
        } else {
          setRawData([]);
        }

        // Initialize filters
        if (result.data.interaction_config?.filters) {
          const initialFilters: Record<string, any> = {};
          result.data.interaction_config.filters.forEach((filter: any) => {
            initialFilters[filter.column] = filter.default;
          });
          setActiveFilters(initialFilters);
        }
      } else {
        throw new Error(result.message || 'Failed to generate dashboard');
      }
    } catch (err: any) {
      console.error('Error fetching autonomous dashboard:', err);
      setError(err.message || 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (column: string, value: any) => {
    setActiveFilters(prev => ({
      ...prev,
      [column]: value
    }));

    // TODO: Implement actual filtering logic
    console.log('Filter changed:', column, value);
  };

  if (loading) {
    return <DashboardLoading />;
  }

  if (error) {
    return <DashboardError error={error} />;
  }

  if (!dashboardData) {
    return <DashboardError error="No dashboard data available" />;
  }

  // Compute background: Use gradient in Dark Mode, solid light color in Light Mode
  const pageBackground = isDark && dashboardData.color_palette.background_gradient?.length >= 2
    ? `linear-gradient(135deg, ${dashboardData.color_palette.background_gradient[0]}, ${dashboardData.color_palette.background_gradient[1]})`
    : 'var(--bg-primary)';

  return (
    <div style={{
      background: pageBackground,
      minHeight: '100vh',
      paddingBottom: '40px',
      transition: 'background 0.3s ease'
    }}>
      {/* Header with Filters */}
      <div style={{
        padding: '32px 24px',
        borderBottom: '1px solid var(--border-color)'
      }}>
        <div style={{ marginBottom: '16px' }}>
          <h1 style={{
            margin: 0,
            fontSize: '2rem',
            fontWeight: 700,
            color: 'var(--text-primary)'
          }}>
            Dashboard
          </h1>
          <p style={{
            margin: '8px 0 0 0',
            fontSize: '1rem',
            color: 'var(--text-secondary)'
          }}>
            Autonomously generated exploration interface
          </p>
        </div>

        {/* Interaction Filters */}
        {dashboardData.interaction_config?.filters && dashboardData.interaction_config.filters.length > 0 && (
          <div style={{
            display: 'flex',
            gap: '16px',
            flexWrap: 'wrap',
            marginTop: '20px'
          }}>
            {dashboardData.interaction_config.filters.map((filter: any, idx: number) => (
              <div key={idx} style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}>
                <label style={{
                  fontSize: '0.875rem',
                  color: 'var(--text-secondary)',
                  textTransform: 'capitalize'
                }}>
                  {filter.column.replace('_', ' ')}
                </label>

                {filter.type === 'categorical' ? (
                  <select
                    value={activeFilters[filter.column] || filter.default}
                    onChange={(e) => handleFilterChange(filter.column, e.target.value)}
                    style={{
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color)',
                      backgroundColor: 'var(--card-bg)',
                      color: 'var(--text-primary)',
                      fontSize: '0.9375rem',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="all">All</option>
                    {filter.options?.map((option: string, optIdx: number) => (
                      <option key={optIdx} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : filter.type === 'date_range' ? (
                  <input
                    type="date"
                    style={{
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color)',
                      backgroundColor: 'var(--card-bg)',
                      color: 'var(--text-primary)',
                      fontSize: '0.9375rem'
                    }}
                  />
                ) : null}
              </div>
            ))}

            <button
              onClick={() => setActiveFilters({})}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: 'transparent',
                color: 'var(--text-secondary)',
                fontSize: '0.9375rem',
                cursor: 'pointer',
                alignSelf: 'flex-end'
              }}
            >
              Reset Filters
            </button>
          </div>
        )}

        {/* Behavior scores */}
        <div style={{
          marginTop: '16px',
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap'
        }}>
          {Object.entries(dashboardData.behavior_scores).map(([key, value]: [string, any]) => {
            if (typeof value === 'number') {
              return (
                <div key={key} style={{
                  padding: '6px 12px',
                  backgroundColor: 'var(--card-bg)',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  border: '1px solid var(--border-color)'
                }}>
                  <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                    {key}:
                  </span>
                  {' '}
                  <span style={{ color: dashboardData.color_palette.primary[0], fontWeight: 600 }}>
                    {value.toFixed(2)}
                  </span>
                </div>
              );
            }
            return null;
          })}
        </div>
      </div>

      {/* Autonomous Renderer */}
      <AutonomousRenderer
        layoutSpec={dashboardData.layout_spec}
        visualPrimitives={dashboardData.visual_primitives}
        colorPalette={dashboardData.color_palette}
        data={rawData}
        mode="dashboard"
        isDarkMode={isDark}
      />

      {/* Interaction Info */}
      {dashboardData.interaction_config?.cross_highlight?.enabled && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          padding: '12px 16px',
          backgroundColor: 'var(--card-bg)',
          borderRadius: '8px',
          border: `2px solid ${dashboardData.color_palette.accents[0]}`,
          fontSize: '0.875rem',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}>
          <span style={{ marginRight: '8px' }}>✨</span>
          Interactive mode: Cross-highlighting enabled
        </div>
      )}
    </div>
  );
}
