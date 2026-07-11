import React, { useState, useCallback } from 'react';
import { ReactFlow, MiniMap, Controls, Background, useNodesState, useEdgesState, addEdge, Connection, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Play, Save, Plus, Database, Wand2, Calculator, Settings, Code, Activity, Trash2 } from 'lucide-react';
import apiService, { api } from '@/services/api';
import { useToast } from '@/contexts/ToastContext';
import { motion } from 'framer-motion';

// Custom Nodes Components
const CustomNode = ({ data, icon: Icon, title, color }: any) => (
    <div className={`px-4 py-3 shadow-lg rounded-xl bg-white dark:bg-[#1e1e1e] border-2 border-transparent hover:border-${color}-500 transition-colors`}>
        <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-${color}-50 dark:bg-${color}-500/10 text-${color}-500`}>
                <Icon className="w-5 h-5" />
            </div>
            <div>
                <h4 className="font-bold text-sm text-gray-900 dark:text-gray-100">{title}</h4>
                <p className="text-xs text-gray-500">{data.label || 'Configure node...'}</p>
            </div>
        </div>
    </div>
);

const nodeTypes = {
    dataSource: (props: any) => <CustomNode {...props} icon={Database} title="Data Source" color="blue" />,
    cleanData: (props: any) => <CustomNode {...props} icon={Wand2} title="Clean Data" color="purple" />,
    transform: (props: any) => <CustomNode {...props} icon={Calculator} title="Transform" color="green" />,
    trainModel: (props: any) => <CustomNode {...props} icon={Activity} title="Train Model" color="red" />
};

const initialNodes = [
    { id: '1', type: 'dataSource', position: { x: 100, y: 100 }, data: { label: 'sales_data.csv' } },
];
const initialEdges: Edge[] = [];

export const PipelineBuilder: React.FC = () => {
    const { addToast } = useToast();
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const [isExecuting, setIsExecuting] = useState(false);
    const [executionLog, setExecutionLog] = useState<string[]>([]);

    const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)), [setEdges]);

    const addNode = (type: string, label: string) => {
        const newNode = {
            id: Date.now().toString(),
            type,
            position: { x: Math.random() * 200 + 200, y: Math.random() * 200 + 200 },
            data: { label }
        };
        setNodes((nds) => [...nds, newNode]);
    };

    const handleExecute = async () => {
        setIsExecuting(true);
        setExecutionLog(['Starting pipeline execution...']);
        try {
            const req = {
                nodes: nodes.map(n => ({ id: n.id, type: n.type || 'default', data: n.data })),
                edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target }))
            };
            
            const res = await api.post('/api/v1/pipelines/execute', req);
            
            if (res.data.success) {
                setExecutionLog(prev => [...prev, ...res.data.log, 'Pipeline finished successfully.']);
                addToast('success', 'Pipeline Executed', `Finished pipeline execution: ${res.data.pipeline_id}`);
            }
        } catch (e: any) {
            setExecutionLog(prev => [...prev, `Error: ${e.response?.data?.detail || e.message}`]);
            addToast('error', 'Execution Failed', e.response?.data?.detail || e.message);
        } finally {
            setIsExecuting(false);
        }
    };

    const handleSavePipeline = async () => {
        try {
            const req = {
                nodes: nodes.map(n => ({ id: n.id, type: n.type || 'default', data: n.data })),
                edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target }))
            };
            const res = await api.post('/api/v1/pipelines/save?name=My+Saved+Pipeline', req);
            if (res.data.success) {
                addToast('success', 'Pipeline Saved', 'Visual pipeline successfully saved to PostgreSQL database.');
            } else {
                addToast('error', 'Failed to Save', res.data.error);
            }
        } catch (e: any) {
            addToast('error', 'Save Error', e.response?.data?.detail || e.message);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-full" style={{ backgroundColor: 'var(--bg-main)' }}>
            
            {/* Toolbar */}
            <div className="h-16 border-b flex items-center justify-between px-6 z-10 bg-white/50 dark:bg-black/20 backdrop-blur-md" style={{ borderColor: 'var(--border-color)' }}>
                <div className="flex items-center gap-4">
                    <h1 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                        <Settings className="w-6 h-6 text-indigo-500" />
                        Pipeline Builder
                    </h1>
                </div>
                
                <div className="flex items-center gap-3">
                    <button onClick={() => setNodes([])} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 transition-colors">
                        <Trash2 className="w-5 h-5" />
                    </button>
                    <button 
                        onClick={handleSavePipeline}
                        className="px-4 py-2 bg-emerald-100 text-emerald-600 hover:bg-emerald-200 dark:bg-emerald-500/20 dark:text-emerald-400 dark:hover:bg-emerald-500/30 rounded-lg text-sm font-bold transition-colors flex items-center gap-2"
                    >
                        <Save className="w-4 h-4" /> Save to DB
                    </button>
                    <button 
                        onClick={handleExecute}
                        disabled={isExecuting || nodes.length === 0}
                        className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-bold shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
                    >
                        {isExecuting ? <Activity className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        Execute Pipeline
                    </button>
                </div>
            </div>

            <div className="flex-1 flex flex-col md:flex-row h-[calc(100vh-4rem)]">
                
                {/* Canvas */}
                <div className="flex-1 h-full relative">
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        nodeTypes={nodeTypes}
                        fitView
                        className="bg-gray-50 dark:bg-[#121212]"
                    >
                        <Background color="#ccc" gap={16} size={1} />
                        <Controls className="bg-white dark:bg-gray-800 border-none shadow-xl" />
                        <MiniMap 
                            nodeColor={(node) => {
                                switch (node.type) {
                                    case 'dataSource': return '#3b82f6';
                                    case 'cleanData': return '#a855f7';
                                    case 'transform': return '#22c55e';
                                    case 'trainModel': return '#ef4444';
                                    default: return '#eee';
                                }
                            }}
                            className="bg-white dark:bg-gray-800 border dark:border-gray-700"
                        />
                    </ReactFlow>

                    {/* Nodes Palette Overlay */}
                    <motion.div 
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="absolute top-4 left-4 p-4 rounded-2xl shadow-2xl border w-64 bg-white/90 dark:bg-black/80 backdrop-blur-xl"
                        style={{ borderColor: 'var(--border-color)' }}
                    >
                        <h3 className="font-bold text-sm uppercase tracking-wider mb-4" style={{ color: 'var(--text-muted)' }}>Nodes Palette</h3>
                        <div className="space-y-2">
                            <button onClick={() => addNode('dataSource', 'New Dataset')} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-blue-50 dark:hover:bg-blue-900/20 text-left transition-colors border border-transparent hover:border-blue-200 dark:hover:border-blue-800 group">
                                <Database className="w-5 h-5 text-blue-500 group-hover:scale-110 transition-transform" />
                                <span className="font-medium text-sm">Data Source</span>
                            </button>
                            <button onClick={() => addNode('cleanData', 'Auto Clean')} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-purple-50 dark:hover:bg-purple-900/20 text-left transition-colors border border-transparent hover:border-purple-200 dark:hover:border-purple-800 group">
                                <Wand2 className="w-5 h-5 text-purple-500 group-hover:scale-110 transition-transform" />
                                <span className="font-medium text-sm">Clean Data</span>
                            </button>
                            <button onClick={() => addNode('transform', 'Feature Engineering')} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-green-50 dark:hover:bg-green-900/20 text-left transition-colors border border-transparent hover:border-green-200 dark:hover:border-green-800 group">
                                <Calculator className="w-5 h-5 text-green-500 group-hover:scale-110 transition-transform" />
                                <span className="font-medium text-sm">Transform</span>
                            </button>
                            <button onClick={() => addNode('trainModel', 'AutoML Engine')} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 text-left transition-colors border border-transparent hover:border-red-200 dark:hover:border-red-800 group">
                                <Activity className="w-5 h-5 text-red-500 group-hover:scale-110 transition-transform" />
                                <span className="font-medium text-sm">Train Model</span>
                            </button>
                        </div>
                    </motion.div>
                </div>

                {/* Execution Log Sidebar */}
                <div className="w-full md:w-80 border-l bg-gray-50 dark:bg-[#181818] flex flex-col" style={{ borderColor: 'var(--border-color)' }}>
                    <div className="p-4 border-b" style={{ borderColor: 'var(--border-color)' }}>
                        <h3 className="font-bold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                            <Code className="w-5 h-5 text-indigo-500" />
                            Execution Logs
                        </h3>
                    </div>
                    <div className="flex-1 p-4 overflow-y-auto font-mono text-xs space-y-2">
                        {executionLog.length === 0 ? (
                            <div className="h-full flex items-center justify-center text-gray-400 dark:text-gray-600">
                                No logs yet. Execute a pipeline.
                            </div>
                        ) : (
                            executionLog.map((log, i) => (
                                <div key={i} className={`p-2 rounded bg-white dark:bg-black/50 border dark:border-white/5 ${log.includes('Error') ? 'text-red-500' : 'text-green-600 dark:text-green-400'}`}>
                                    {log}
                                </div>
                            ))
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default PipelineBuilder;

