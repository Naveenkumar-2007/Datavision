import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Database, Plus, Trash2, Settings, Download, Loader,
  Type, Hash, Calendar, ToggleLeft, ArrowRight
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { getUserIdSync } from '@/utils/userId';

interface ColumnDef {
  id: string;
  name: string;
  type: string;
  categories?: string;
  min_val?: number;
  max_val?: number;
  missing_pct?: number;
}

export const SyntheticDataGenerator: React.FC<{ onGenerated?: () => void }> = ({ onGenerated }) => {
  const { isDark } = useUserStore();
  const [datasetName, setDatasetName] = useState('synthetic_dataset');
  const [numRows, setNumRows] = useState<number>(1000);
  const [columns, setColumns] = useState<ColumnDef[]>([
    { id: '1', name: 'id', type: 'numerical', min_val: 1, max_val: 1000 },
    { id: '2', name: 'category', type: 'categorical', categories: 'A, B, C' },
    { id: '3', name: 'amount', type: 'numerical', min_val: 10.5, max_val: 500.0 }
  ]);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [expanded, setExpanded] = useState(false);

  const addColumn = () => {
    setColumns([...columns, { 
      id: Math.random().toString(36).substr(2, 9), 
      name: `column_${columns.length + 1}`, 
      type: 'numerical',
      min_val: 0,
      max_val: 100
    }]);
  };

  const removeColumn = (id: string) => {
    setColumns(columns.filter(c => c.id !== id));
  };

  const updateColumn = (id: string, field: string, value: any) => {
    setColumns(columns.map(c => c.id === id ? { ...c, [field]: value } : c));
  };

  const handleGenerate = async () => {
    if (columns.length === 0) return;
    setGenerating(true);
    setResult(null);

    const payload = {
      dataset_name: datasetName,
      num_rows: numRows,
      columns: columns.map(c => ({
        ...c,
        categories: c.categories ? c.categories.split(',').map(s => s.trim()) : undefined
      }))
    };

    try {
      const res = await fetch('/api/v1/synthetic/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': getUserIdSync()
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setResult(data);
        if (onGenerated) onGenerated();
      } else {
        alert(data.detail || 'Failed to generate');
      }
    } catch (err) {
      console.error(err);
      alert('Network error');
    } finally {
      setGenerating(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'categorical': return <Type className="w-4 h-4 text-purple-400" />;
      case 'numerical': return <Hash className="w-4 h-4 text-blue-400" />;
      case 'date': return <Calendar className="w-4 h-4 text-emerald-400" />;
      case 'boolean': return <ToggleLeft className="w-4 h-4 text-amber-400" />;
      default: return <Database className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className={`rounded-2xl border transition-all ${
      isDark ? 'bg-zinc-900/50 border-white/5 backdrop-blur-xl' : 'bg-white border-gray-100 shadow-sm'
    }`}>
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full p-6 flex items-center justify-between text-left focus:outline-none"
      >
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl ${isDark ? 'bg-indigo-500/20' : 'bg-indigo-50'}`}>
            <Settings className="w-6 h-6 text-indigo-500" />
          </div>
          <div>
            <h3 className="font-bold text-lg" style={{ color: isDark ? 'white' : 'black' }}>
              Synthetic Data Generator
            </h3>
            <p className="text-sm" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
              Create realistic mock datasets for testing and simulations.
            </p>
          </div>
        </div>
        <div className={`px-3 py-1.5 rounded-full text-xs font-semibold ${
          expanded ? 'bg-indigo-500 text-white' : isDark ? 'bg-white/10 text-gray-300' : 'bg-gray-100 text-gray-600'
        }`}>
          {expanded ? 'Close Builder' : 'Open Builder'}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t overflow-hidden"
            style={{ borderColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
          >
            <div className="p-6 space-y-6">
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>Dataset Name</label>
                  <input 
                    type="text" 
                    value={datasetName}
                    onChange={e => setDatasetName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                    style={{ 
                      backgroundColor: isDark ? 'rgba(0,0,0,0.2)' : 'white',
                      borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0',
                      color: isDark ? 'white' : 'black'
                    }}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>Number of Rows</label>
                  <input 
                    type="number" 
                    value={numRows}
                    onChange={e => setNumRows(parseInt(e.target.value) || 100)}
                    min="1" max="100000"
                    className="w-full px-4 py-2.5 rounded-xl border focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                    style={{ 
                      backgroundColor: isDark ? 'rgba(0,0,0,0.2)' : 'white',
                      borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0',
                      color: isDark ? 'white' : 'black'
                    }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-4">
                  <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>Columns Configuration</label>
                  <button onClick={addColumn} className="text-xs font-semibold text-indigo-500 hover:text-indigo-400 flex items-center gap-1">
                    <Plus className="w-3 h-3"/> Add Column
                  </button>
                </div>
                
                <div className="space-y-3">
                  {columns.map((col, index) => (
                    <div key={col.id} className={`p-4 rounded-xl border flex flex-col sm:flex-row gap-4 items-start sm:items-center ${isDark ? 'bg-black/20 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
                      <div className="w-full sm:w-1/4">
                        <input 
                          type="text" 
                          value={col.name}
                          onChange={e => updateColumn(col.id, 'name', e.target.value)}
                          placeholder="Column Name"
                          className="w-full px-3 py-2 rounded-lg text-sm border-transparent focus:border-indigo-500/50 bg-transparent focus:bg-white/5 transition-all outline-none"
                          style={{ color: isDark ? 'white' : 'black' }}
                        />
                      </div>
                      
                      <div className="w-full sm:w-1/4 relative">
                        <select
                          value={col.type}
                          onChange={e => updateColumn(col.id, 'type', e.target.value)}
                          className="w-full pl-9 pr-3 py-2 rounded-lg text-sm appearance-none outline-none transition-all border"
                          style={{ 
                            backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'white',
                            borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0',
                            color: isDark ? 'white' : 'black'
                          }}
                        >
                          <option value="numerical" style={{ color: 'black' }}>Numerical</option>
                          <option value="categorical" style={{ color: 'black' }}>Categorical</option>
                          <option value="date" style={{ color: 'black' }}>Date</option>
                          <option value="boolean" style={{ color: 'black' }}>Boolean</option>
                        </select>
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                          {getTypeIcon(col.type)}
                        </div>
                      </div>

                      <div className="w-full sm:flex-1 flex gap-2">
                        {col.type === 'numerical' && (
                          <>
                            <input type="number" value={col.min_val} onChange={e => updateColumn(col.id, 'min_val', parseFloat(e.target.value))} placeholder="Min" className="w-1/2 px-3 py-2 rounded-lg text-sm outline-none border bg-transparent" style={{ borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0', color: isDark?'white':'black' }} />
                            <input type="number" value={col.max_val} onChange={e => updateColumn(col.id, 'max_val', parseFloat(e.target.value))} placeholder="Max" className="w-1/2 px-3 py-2 rounded-lg text-sm outline-none border bg-transparent" style={{ borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0', color: isDark?'white':'black' }} />
                          </>
                        )}
                        {col.type === 'categorical' && (
                          <input type="text" value={col.categories} onChange={e => updateColumn(col.id, 'categories', e.target.value)} placeholder="Comma separated (e.g. A, B, C)" className="w-full px-3 py-2 rounded-lg text-sm outline-none border bg-transparent" style={{ borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0', color: isDark?'white':'black' }} />
                        )}
                        {(col.type === 'date' || col.type === 'boolean') && (
                          <div className="w-full px-3 py-2 text-sm text-gray-500">Auto-generated bounds</div>
                        )}
                      </div>

                      <button onClick={() => removeColumn(col.id)} className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t flex justify-end" style={{ borderColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
                <button
                  onClick={handleGenerate}
                  disabled={generating || columns.length === 0}
                  className="px-6 py-2.5 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/25 flex items-center gap-2 transition-all disabled:opacity-50"
                >
                  {generating ? (
                    <><Loader className="w-4 h-4 animate-spin"/> Generating...</>
                  ) : (
                    <><Database className="w-4 h-4"/> Generate {numRows} Rows</>
                  )}
                </button>
              </div>

              {result && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-sm flex items-center justify-between">
                  <div>
                    <strong>Success!</strong> {result.file.name} saved to your workspace.
                  </div>
                  <button className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 font-semibold flex items-center gap-2 transition-colors">
                    View in Hub <ArrowRight className="w-3 h-3" />
                  </button>
                </motion.div>
              )}

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
