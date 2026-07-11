import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { Play, TrendingUp, TrendingDown, RefreshCcw, Sliders } from 'lucide-react';
import Plot from 'react-plotly.js';
import apiService from '@/services/api';

const ScenarioSimulator: React.FC = () => {
  const { isDark } = useUserStore();
  const [variables, setVariables] = useState<any[]>([]);
  const [values, setValues] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    const fetchVariables = async () => {
      try {
        const response = await apiService.getSimulatorVariables();
        if (response.data) {
          setVariables(response.data);
          
          // Set initial values
          const initialVals: Record<string, number> = {};
          response.data.forEach((v: any) => {
            initialVals[v.name] = v.current_value;
          });
          setValues(initialVals);
        }
      } catch (error) {
        console.error("Failed to load variables", error);
      } finally {
        setLoading(false);
      }
    };
    fetchVariables();
  }, []);

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      const response = await apiService.runSimulation(values);
      setResult(response.data);
    } catch (error) {
      console.error("Simulation failed", error);
    } finally {
      setSimulating(false);
    }
  };

  // Run initial simulation when variables are loaded
  useEffect(() => {
    if (Object.keys(values).length > 0 && !result && !simulating) {
      handleSimulate();
    }
  }, [values, result, simulating]);

  const handleSliderChange = (name: string, value: number) => {
    setValues(prev => ({ ...prev, [name]: value }));
  };

  const getChartData = () => {
    if (!result) return [];

    const x = result.chart_data.map((d: any) => d.month);
    const yBase = result.chart_data.map((d: any) => d['Baseline Revenue']);
    const ySim = result.chart_data.map((d: any) => d['Simulated Revenue']);

    return [
      {
        x,
        y: yBase,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Baseline Revenue',
        line: { color: isDark ? '#64748b' : '#94a3b8', width: 2, dash: 'dot' },
      },
      {
        x,
        y: ySim,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Simulated Revenue',
        line: { color: '#6366f1', width: 3 }, // Indigo
        fill: 'tonexty',
        fillcolor: isDark ? 'rgba(99, 102, 241, 0.1)' : 'rgba(99, 102, 241, 0.05)',
      }
    ];
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto pb-24">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
            <Sliders className="w-6 h-6 text-indigo-500" /> What-If Scenario Simulator
          </h2>
          <p className="text-sm mt-1" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
            Adjust key business drivers to forecast outcomes and optimize your strategy.
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => {
              const resetVals: Record<string, number> = {};
              variables.forEach((v: any) => {
                resetVals[v.name] = v.current_value;
              });
              setValues(resetVals);
            }}
            className={`p-2.5 rounded-xl border flex items-center justify-center gap-2 text-sm font-medium transition-all ${
              isDark ? 'border-white/10 hover:bg-white/5 text-gray-200' : 'border-gray-200 hover:bg-gray-50 text-gray-700'
            }`}
          >
            <RefreshCcw className="w-4 h-4" /> Reset
          </button>
          <button 
            onClick={handleSimulate}
            disabled={simulating}
            className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-indigo-600/20 disabled:opacity-70"
          >
            <Play className="w-4 h-4 fill-white" /> {simulating ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls Panel */}
          <div className={`lg:col-span-4 p-6 rounded-2xl border ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`}>
            <h3 className="text-lg font-semibold mb-6" style={{ color: isDark ? '#f1f5f9' : '#1e293b' }}>
              Variables
            </h3>
            
            <div className="space-y-6">
              {variables.map((v) => (
                <div key={v.name} className="space-y-3">
                  <div className="flex justify-between items-center">
                    <label className="text-sm font-medium" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>
                      {v.name}
                    </label>
                    <span className="text-xs font-bold px-2 py-1 rounded-md bg-indigo-500/10 text-indigo-500">
                      {v.unit === '$' ? '$' : ''}{values[v.name]?.toLocaleString()}{v.unit === '%' ? '%' : ''}
                    </span>
                  </div>
                  <input 
                    type="range"
                    min={v.min_value}
                    max={v.max_value}
                    step={v.step}
                    value={values[v.name] || v.current_value}
                    onChange={(e) => handleSliderChange(v.name, parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 accent-indigo-500"
                  />
                  <div className="flex justify-between text-xs" style={{ color: isDark ? '#64748b' : '#94a3b8' }}>
                    <span>{v.unit === '$' ? '$' : ''}{v.min_value.toLocaleString()}{v.unit === '%' ? '%' : ''}</span>
                    <span>{v.unit === '$' ? '$' : ''}{v.max_value.toLocaleString()}{v.unit === '%' ? '%' : ''}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-8 space-y-6">
            {result && (
              <>
                {/* Impact Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {Object.keys(result.impact_percentage).map((metric) => {
                    const impact = result.impact_percentage[metric];
                    const isPositive = impact >= 0;
                    // For CAC, positive impact is bad (increase in cost). Let's color accordingly
                    const isGood = metric === 'CAC' ? !isPositive : isPositive;
                    
                    return (
                      <div key={metric} className={`p-5 rounded-2xl border ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`}>
                        <div className="text-sm font-medium mb-1" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
                          {metric} Impact
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-bold" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
                            {result.simulated_metrics[metric]}
                          </span>
                        </div>
                        <div className={`mt-2 text-xs font-semibold flex items-center gap-1 ${
                          isGood ? 'text-emerald-500' : 'text-red-500'
                        }`}>
                          {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          {Math.abs(impact)}% vs Baseline
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Chart */}
                <div className={`p-5 rounded-2xl border overflow-hidden ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`}>
                  <h3 className="text-sm font-medium mb-4" style={{ color: isDark ? '#f1f5f9' : '#1e293b' }}>
                    Revenue Forecast (6 Months)
                  </h3>
                  <div className="w-full h-[300px]">
                    <Plot
                      data={getChartData() as any}
                      layout={{
                        autosize: true,
                        margin: { l: 40, r: 20, t: 10, b: 30 },
                        paper_bgcolor: 'transparent',
                        plot_bgcolor: 'transparent',
                        font: { color: isDark ? '#94a3b8' : '#64748b' },
                        xaxis: {
                          gridcolor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                          zerolinecolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
                        },
                        yaxis: {
                          gridcolor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                          zerolinecolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
                        },
                        legend: { orientation: 'h', y: 1.1, font: { color: isDark ? '#f1f5f9' : '#1e293b' } }
                      }}
                      useResizeHandler={true}
                      style={{ width: '100%', height: '100%' }}
                      config={{ displayModeBar: false }}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ScenarioSimulator;
