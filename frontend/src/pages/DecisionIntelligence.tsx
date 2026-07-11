import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BrainCircuit,
  Activity,
  Network,
  TrendingUp,
  ShieldCheck,
  Cpu,
  RefreshCw,
  Zap,
  LineChart,
  BarChart3,
  Bot,
  DatabaseZap,
  Globe2,
  Target
} from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const DecisionIntelligence: React.FC = () => {
  const { isDark } = useUserStore();
  const toast = useToast();
  const [isSwarmActive, setIsSwarmActive] = useState(false);
  
  // Agent States
  const [agents, setAgents] = useState([
    { id: 'data-cleaner', name: 'Data Integrity Agent', role: 'Cleanses & imputes missing data', icon: DatabaseZap, status: 'idle', progress: 0 },
    { id: 'market-researcher', name: 'Macro-Context Agent', role: 'Real-time market trend analysis', icon: Globe2, status: 'idle', progress: 0 },
    { id: 'forecaster', name: 'Predictive Forecaster', role: 'Monte Carlo Simulations', icon: TrendingUp, status: 'idle', progress: 0 },
    { id: 'causal-engine', name: 'Causal Inference Engine', role: 'Multivariate root-cause analysis', icon: Network, status: 'idle', progress: 0 }
  ]);
  const [swarmData, setSwarmData] = useState<any>(null);
  const [goal, setGoal] = useState('');
  
  const triggerSwarm = async () => {
    if (!goal.trim()) {
        toast.error("Please enter a strategic business question first.");
        return;
    }
    
    setIsSwarmActive(true);
    toast.success("Autonomous Agent Swarm Deployed!");
    
    // Set all agents to processing
    setAgents(prev => prev.map(a => ({ ...a, status: 'processing', progress: 20 })));
    
    try {
      const response = await fetch('/api/v1/decisions/swarm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': useUserStore.getState().user?.id || 'default'
        },
        body: JSON.stringify({ goal })
      });
      
      if (!response.ok) {
        throw new Error('Swarm execution failed');
      }
      
      const data = await response.json();
      setSwarmData(data.agents);
      
      // Animate completion
      setAgents(prev => prev.map(a => ({ ...a, status: 'completed', progress: 100 })));
      toast.success("Swarm Analysis Complete. New insights generated.");
      
    } catch (err: any) {
      toast.error(err.message || "Failed to deploy swarm.");
      setAgents(prev => prev.map(a => ({ ...a, status: 'idle', progress: 0 })));
    } finally {
      setIsSwarmActive(false);
    }
  };

  return (
    <div className="p-4 sm:p-8 space-y-8 max-w-7xl mx-auto min-h-screen">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 relative z-10">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight flex items-center gap-3 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
            <BrainCircuit className="w-10 h-10 text-indigo-400" />
            Agentic Swarm Command Center
          </h2>
          <p className="text-sm mt-2" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
            30-Year BI Veteran Intelligence. Deploy parallel AI agents for autonomous root-cause and causal analysis.
          </p>
        </div>
      </div>

      {/* Strategic Goal Input */}
      <div className={`p-2 rounded-2xl border flex items-center gap-2 backdrop-blur-md relative z-10 ${isDark ? 'bg-black/40 border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]' : 'bg-white/80 border-indigo-200 shadow-xl'}`}>
        <div className="pl-4">
            <Target className={`w-6 h-6 ${isDark ? 'text-indigo-400' : 'text-indigo-500'}`} />
        </div>
        <input 
            type="text" 
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Ask a strategic question (e.g., 'Why did churn spike last month?' or 'How to maximize Q4 revenue?')"
            className="flex-1 bg-transparent border-none outline-none px-2 py-4 font-medium text-lg placeholder:text-gray-500"
            style={{ color: isDark ? 'white' : 'black' }}
            disabled={isSwarmActive}
            onKeyDown={(e) => e.key === 'Enter' && triggerSwarm()}
        />
        <button 
          onClick={triggerSwarm}
          disabled={isSwarmActive}
          className={`px-8 py-4 rounded-xl font-bold flex items-center gap-2 transition-all mr-1 ${
            isSwarmActive ? 'bg-indigo-500/50 cursor-not-allowed' : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:scale-105 text-white shadow-lg shadow-indigo-500/30'
          }`}
        >
          {isSwarmActive ? (
            <><RefreshCw className="w-5 h-5 animate-spin" /> Swarm Computing...</>
          ) : (
            <><Zap className="w-5 h-5 text-yellow-300" /> Deploy Swarm</>
          )}
        </button>
      </div>

      {/* Agents Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
        {agents.map((agent, idx) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className={`p-6 rounded-2xl border backdrop-blur-md relative overflow-hidden transition-colors ${
              agent.status === 'completed' ? (isDark ? 'border-green-500/30 bg-green-500/5' : 'border-green-200 bg-green-50') :
              agent.status === 'processing' ? (isDark ? 'border-indigo-500/50 bg-indigo-500/10' : 'border-indigo-200 bg-indigo-50') :
              (isDark ? 'border-gray-800 bg-[#111]' : 'border-gray-200 bg-white')
            }`}
          >
            {/* Background processing animation */}
            {agent.status === 'processing' && (
              <motion.div 
                className={`absolute inset-0 bg-gradient-to-r ${isDark ? 'from-indigo-500/0 via-indigo-500/10 to-indigo-500/0' : 'from-indigo-100/0 via-indigo-100/50 to-indigo-100/0'}`}
                animate={{ x: ['-100%', '100%'] }}
                transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
              />
            )}

            <div className="flex justify-between items-start mb-4 relative z-10">
              <div className={`p-3 rounded-xl ${
                agent.status === 'completed' ? (isDark ? 'bg-green-500/20 text-green-400' : 'bg-green-100 text-green-600') :
                agent.status === 'processing' ? (isDark ? 'bg-indigo-500/20 text-indigo-400 animate-pulse' : 'bg-indigo-100 text-indigo-600 animate-pulse') :
                (isDark ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-500')
              }`}>
                <agent.icon className="w-6 h-6" />
              </div>
              <div className={`text-xs font-bold uppercase tracking-widest ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                {agent.status}
              </div>
            </div>
            
            <h3 className={`font-bold relative z-10 text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>{agent.name}</h3>
            <p className={`text-xs relative z-10 mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{agent.role}</p>
            
            <div className={`w-full h-1.5 rounded-full mt-4 relative z-10 overflow-hidden ${isDark ? 'bg-gray-800' : 'bg-gray-200'}`}>
              <motion.div 
                className={`h-full rounded-full ${agent.status === 'completed' ? 'bg-green-500' : 'bg-indigo-500'}`}
                initial={{ width: 0 }}
                animate={{ width: `${agent.progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Advanced BI Dashboards Placeholder (Only shows after run) */}
      <AnimatePresence>
        {agents[3].status === 'completed' && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-8 relative z-10 mt-12"
          >
            {/* Causal Analysis */}
            <div className={`p-6 rounded-2xl border backdrop-blur-md ${isDark ? 'border-gray-800 bg-[#111]' : 'border-gray-200 bg-white'}`}>
              <div className="flex items-center gap-3 mb-6">
                <Network className="w-6 h-6 text-purple-400" />
                <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Multi-Variate Causal Analysis</h3>
              </div>
              <div className={`h-64 flex items-center justify-center border rounded-xl relative overflow-hidden ${isDark ? 'border-gray-800 bg-black/50' : 'border-gray-200 bg-gray-50'}`}>
                 {/* Fake Heatmap/Node Graph Simulation */}
                 <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(circle at 50% 50%, #8b5cf6 0%, transparent 50%)' }}></div>
                 <div className="text-center z-10">
                   <Network className="w-12 h-12 text-purple-500 mx-auto mb-2 opacity-50" />
                   <p className={`font-mono text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Causal Nodes Generated</p>
                   <p className={`font-bold text-lg mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                     {swarmData?.causal?.node_a || 'Variable A'} → {swarmData?.causal?.node_b || 'Variable B'} (r = {swarmData?.causal?.r || '0'})
                   </p>
                 </div>
              </div>
              <div className={`mt-4 p-4 rounded-xl border text-sm ${isDark ? 'bg-purple-500/10 border-purple-500/20 text-purple-200' : 'bg-purple-50 border-purple-200 text-purple-800'}`}>
                <span className="font-bold">Agent Insight:</span> {swarmData?.causal?.insight || 'Causal analysis completed.'}
              </div>
            </div>

            {/* Monte Carlo Simulation */}
            <div className={`p-6 rounded-2xl border backdrop-blur-md ${isDark ? 'border-gray-800 bg-[#111]' : 'border-gray-200 bg-white'}`}>
              <div className="flex items-center gap-3 mb-6">
                <LineChart className="w-6 h-6 text-emerald-400" />
                <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Monte Carlo Scenarios (10,000 runs)</h3>
              </div>
              <div className={`h-64 border rounded-xl relative overflow-hidden ${isDark ? 'border-gray-800 bg-black/50' : 'border-gray-200 bg-gray-50'}`}>
                 {swarmData?.forecaster?.chart_data ? (
                    <div className="w-full h-full p-4 pb-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <RechartsLineChart data={swarmData.forecaster.chart_data}>
                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#333' : '#e5e7eb'} vertical={false} />
                                <XAxis dataKey="month" stroke={isDark ? '#6b7280' : '#9ca3af'} fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke={isDark ? '#6b7280' : '#9ca3af'} fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip 
                                    contentStyle={{ backgroundColor: isDark ? '#1f2937' : '#fff', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                    itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
                                />
                                <Line 
                                    type="monotone" 
                                    dataKey="forecast" 
                                    stroke="#10b981" 
                                    strokeWidth={3}
                                    dot={{ fill: '#10b981', r: 4, strokeWidth: 0 }}
                                    activeDot={{ r: 6, fill: '#34d399', stroke: '#fff', strokeWidth: 2 }}
                                />
                            </RechartsLineChart>
                        </ResponsiveContainer>
                    </div>
                 ) : (
                     <div className="flex items-center justify-center w-full h-full">
                       <div className="text-center z-10">
                         <Activity className="w-12 h-12 text-emerald-500 mx-auto mb-2 opacity-50" />
                         <p className={`font-mono text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>P10 - P90 {swarmData?.forecaster?.target || 'Forecast'}</p>
                         <p className={`font-bold text-lg mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                           {swarmData?.forecaster?.p10 || 'N/A'} - {swarmData?.forecaster?.p90 || 'N/A'}
                         </p>
                       </div>
                     </div>
                 )}
              </div>
              <div className={`mt-4 p-4 rounded-xl border text-sm ${isDark ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200' : 'bg-emerald-50 border-emerald-200 text-emerald-800'}`}>
                <span className="font-bold">Agent Insight:</span> {swarmData?.forecaster?.insight || 'Simulation completed.'}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};

export default DecisionIntelligence;
