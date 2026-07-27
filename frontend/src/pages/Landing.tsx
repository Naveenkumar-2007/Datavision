import React, { useEffect, useState, useRef, useMemo } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  ArrowRight, Zap, Database, LayoutDashboard,
  BrainCircuit, Bot, Activity, Eye, Shield,
  Lock, Globe, BarChart3, FileText, Layers,
  Check, TrendingUp, Boxes, Users,
  Sliders, Sun, Moon, Copy, Server,
  Key, Code, RefreshCw, FileSpreadsheet, Target,
  Sparkles, Rocket, ChevronRight, Gauge
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { getUserIdSync } from '../utils/userId';
import LogoImage from '../components/LogoImage';
import { useUserStore } from '../store/userStore';

/* ═══════════════════════════════════════════════════════════════════════
   ANIMATED COUNTER — Counts up when scrolled into view
   ═══════════════════════════════════════════════════════════════════════ */
function Counter({ to, suffix = '', prefix = '' }: { to: number; suffix?: string; prefix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: '-50px' });
  const [val, setVal] = useState(0);

  useEffect(() => {
    if (!inView) return;
    let cur = 0;
    const step = Math.max(1, Math.ceil(to / 50));
    const id = setInterval(() => {
      cur += step;
      if (cur >= to) { setVal(to); clearInterval(id); }
      else setVal(cur);
    }, 30);
    return () => clearInterval(id);
  }, [inView, to]);

  return <span ref={ref}>{prefix}{val.toLocaleString()}{suffix}</span>;
}

/* ═══════════════════════════════════════════════════════════════════════
   SCROLL REVEAL — Fade-up animation on scroll
   ═══════════════════════════════════════════════════════════════════════ */
function Reveal({ children, delay = 0, className = '' }: { children: React.ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   DATA — Integrations, Modules, Workflow, Metrics
   ═══════════════════════════════════════════════════════════════════════ */
const dataIntegrations = [
  { name: 'DataVision API', category: 'Live Push', icon: Zap, color: '#10b981' },
  { name: 'PostgreSQL', category: 'SQL Database', icon: Database, color: '#336791' },
  { name: 'Snowflake', category: 'Data Warehouse', icon: Server, color: '#29B5E8' },
  { name: 'Google BigQuery', category: 'Analytics', icon: Database, color: '#4285F4' },
  { name: 'Kafka', category: 'Streaming', icon: Activity, color: '#FF9900' },
  { name: 'MongoDB', category: 'NoSQL', icon: Database, color: '#47A248' },
  { name: 'Databricks', category: 'Delta Lake', icon: Server, color: '#FF3621' },
  { name: 'MySQL', category: 'Relational', icon: Database, color: '#00758F' },
  { name: 'Excel', category: 'Spreadsheet', icon: FileSpreadsheet, color: '#107C41' },
  { name: 'CSV & Parquet', category: 'Files', icon: FileText, color: '#059669' },
];

const modules = [
  {
    icon: Activity, title: 'Digital Twin Simulator', badge: 'WHAT-IF',
    desc: 'Run real-time sensitivity analysis with interactive slider controls. Simulate revenue, churn, and budget trade-offs with SHAP-driven insights.',
    gradient: 'from-emerald-500 to-cyan-500',
    tags: ['Scenario Sliders', 'SHAP Analysis', 'Trade-off Matrix']
  },
  {
    icon: LayoutDashboard, title: 'Autonomous Dashboards', badge: 'ZERO-CONFIG',
    desc: 'Auto-generate 15+ chart types from raw data. No drag-and-drop needed — the AI profiles your columns and builds correlation heatmaps, KPI cards, and trends.',
    gradient: 'from-teal-400 to-emerald-600',
    tags: ['Heatmaps', 'Scatter Plots', 'KPI Cards']
  },
  {
    icon: BrainCircuit, title: 'Ultra AutoML Engine', badge: '1-CLICK',
    desc: 'Train XGBoost, LightGBM, Random Forest, Neural Nets & more. Automated hyperparameter tuning, cross-validation, and champion model selection.',
    gradient: 'from-emerald-500 to-teal-600',
    tags: ['XGBoost', 'LightGBM', 'Auto-Tuning']
  },
  {
    icon: Eye, title: 'Computer Vision Studio', badge: 'CV',
    desc: 'Train YOLOv8 object detection and ResNet classifiers with zero code. Monitor epoch loss curves live and export production inference endpoints.',
    gradient: 'from-emerald-500 to-green-600',
    tags: ['Object Detection', 'Classification', 'Segmentation']
  },
  {
    icon: Code, title: 'Developer API & SDK', badge: 'API',
    desc: 'Generate API keys, deploy REST prediction endpoints (<12ms latency). Consume via Python SDK, JavaScript SDK, or cURL.',
    gradient: 'from-cyan-500 to-emerald-600',
    tags: ['REST API', 'Python SDK', 'Webhooks']
  },
  {
    icon: Zap, title: 'Generative AI Analyst', badge: 'LLM',
    desc: 'Ask complex analytical questions in natural language. Powered by Gemini & GPT-4 — auto-generates 6 executive report types and anomaly detection.',
    gradient: 'from-cyan-400 to-teal-500',
    tags: ['Gemini / GPT', 'Natural Language', 'Reports']
  },
  {
    icon: Database, title: 'Data Hub & Smart ETL', badge: 'INGESTION',
    desc: 'Drag-and-drop CSV, Excel, or JSON with 20+ automated quality checks, schema validation, and instant dataset preview.',
    gradient: 'from-green-400 to-emerald-600',
    tags: ['CSV / XLSX', 'Schema Validation', 'Quality Score']
  },
  {
    icon: Bot, title: 'Agentic Autopilot', badge: 'AUTONOMOUS',
    desc: 'Zero human intervention. Pass raw data and watch the AI clean, profile, train 14 models, generate charts, and compile final reports autonomously.',
    gradient: 'from-teal-500 to-emerald-700',
    tags: ['KNN Imputation', 'Auto-Clean', 'End-to-End']
  },
  {
    icon: Users, title: 'Collaboration & Workspaces', badge: 'TEAMS',
    desc: 'Multi-tenant workspaces with role-based access control (Owner, Editor, Viewer). Real-time comments, encrypted channels, and shared insights.',
    gradient: 'from-emerald-500 to-cyan-600',
    tags: ['Multi-Tenant', 'RBAC', 'Shared Workspaces']
  },
  {
    icon: Boxes, title: 'Model Registry & Export', badge: 'DEPLOY',
    desc: 'Manage champion/challenger models with version history. Export to ONNX, Pickle, or PMML, or invoke live REST prediction APIs instantly.',
    gradient: 'from-emerald-400 to-teal-500',
    tags: ['Model Versioning', 'ONNX Export', 'REST APIs']
  },
];

const workflowSteps = [
  { step: '01', title: 'Ingest & Connect', desc: 'Connect PostgreSQL, Snowflake, BigQuery or upload CSV/Excel. 20+ quality checks in <3s.', icon: Database },
  { step: '02', title: 'Auto-Visualize', desc: 'Structural profiling builds 15+ charts, correlation heatmaps, and executive summary cards.', icon: LayoutDashboard },
  { step: '03', title: 'Train AutoML', desc: '14+ algorithms train in parallel with hyperparameter tuning and champion model selection.', icon: BrainCircuit },
  { step: '04', title: 'Deploy & Simulate', desc: 'Run digital twin scenarios, generate LLM reports, and deploy REST APIs (<12ms).', icon: Rocket },
];

const metrics = [
  { value: 15, suffix: '+', label: 'Auto Visualizations', icon: BarChart3 },
  { value: 14, suffix: '+', label: 'ML Algorithms', icon: BrainCircuit },
  { value: 6, label: 'AI Report Types', icon: FileText },
  { value: 12, suffix: 'ms', label: 'API Latency', icon: Zap },
];

/* ═══════════════════════════════════════════════════════════════════════
   CODE SNIPPETS — Developer Section
   ═══════════════════════════════════════════════════════════════════════ */
const codeSnippets: Record<string, string> = {
  python: `import datavision as dv

client = dv.Client(api_key="dv_live_9f83a21b...")

response = client.predict(
    model_id="xgboost_california_v3",
    features={
        "median_income": 8.3252,
        "house_age": 41,
        "total_rooms": 880,
        "population": 322
    }
)

print("Prediction:", response.prediction)
print("Confidence:", response.confidence_range)`,

  curl: `curl -X POST "https://api.datavision.ai/v1/predict" \\
  -H "Authorization: Bearer dv_live_9f83a21b..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "model_id": "xgboost_california_v3",
    "features": {
      "median_income": 8.3252,
      "house_age": 41,
      "total_rooms": 880,
      "population": 322
    }
  }'`,

  javascript: `import { DataVision } from '@datavision/sdk';

const dv = new DataVision({
  apiKey: 'dv_live_9f83a21b...'
});

const result = await dv.predictions.create({
  modelId: 'xgboost_california_v3',
  features: {
    median_income: 8.3252,
    house_age: 41,
    total_rooms: 880,
    population: 322
  }
});

console.log('Prediction:', result.prediction);`,

  webhooks: `// Webhook Payload (POST /your-endpoint)
{
  "event": "model.training.completed",
  "timestamp": "2026-07-27T10:30:00Z",
  "model": {
    "id": "xgboost_california_v3",
    "algorithm": "XGBoost Regressor",
    "accuracy_score": 0.985,
    "status": "CHAMPION_PROMOTED"
  }
}`,
};

/* ═══════════════════════════════════════════════════════════════════════
   MAIN LANDING PAGE COMPONENT
   ═══════════════════════════════════════════════════════════════════════ */
export default function Landing() {
  const userId = getUserIdSync();
  const { isDark, toggleTheme } = useUserStore();

  const [activeCodeLang, setActiveCodeLang] = useState<'python' | 'curl' | 'javascript' | 'webhooks'>('python');
  const [copiedCode, setCopiedCode] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Live AI Sandbox State
  const [marketingBudget, setMarketingBudget] = useState(2500000);
  const [unitPrice, setUnitPrice] = useState(1250);
  const [teamSize, setTeamSize] = useState(120);
  const [isSimulating, setIsSimulating] = useState(false);

  const calculatedImpact = useMemo(() => {
    const budgetFactor = (marketingBudget / 2500000) * 0.45;
    const priceFactor = (unitPrice / 1250) * 0.35;
    const teamFactor = (teamSize / 120) * 0.20;
    const combined = budgetFactor + priceFactor + teamFactor;
    const baseRevenue = 10.5;
    const revenue = (baseRevenue * combined).toFixed(2);
    const revenueGrowth = (((parseFloat(revenue) - 10.5) / 10.5) * 100).toFixed(1);
    const baseProfit = 2.1;
    const profit = (baseProfit * (combined * 1.1)).toFixed(2);
    const profitGrowth = (((parseFloat(profit) - 2.1) / 2.1) * 100).toFixed(1);
    return { revenue, revenueGrowth, profit, profitGrowth, confidence: (92 + combined * 3).toFixed(1) };
  }, [marketingBudget, unitPrice, teamSize]);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  // ─── Theme-aware classes ───
  const pageBg = isDark ? 'bg-[#08090e]' : 'bg-white';
  const textH = isDark ? 'text-white' : 'text-slate-900';
  const textP = isDark ? 'text-slate-400' : 'text-slate-600';
  const textSub = isDark ? 'text-slate-500' : 'text-slate-500';
  const card = isDark
    ? 'bg-white/[0.03] border-white/[0.06] hover:border-emerald-500/30'
    : 'bg-white border-slate-200/80 shadow-sm shadow-slate-100 hover:border-emerald-500/40 hover:shadow-md hover:shadow-emerald-50';
  const navBg = scrolled
    ? isDark ? 'bg-[#08090e]/80 border-white/[0.06] shadow-2xl shadow-black/40' : 'bg-white/80 border-slate-200 shadow-lg shadow-slate-200/40'
    : 'bg-transparent border-transparent';
  const sectionAlt = isDark ? 'bg-white/[0.015]' : 'bg-slate-50/80';
  const codeBg = isDark ? 'bg-[#0c0e14] border-white/[0.06]' : 'bg-slate-50 border-slate-200 shadow-lg shadow-slate-200/40';

  return (
    <div className={`min-h-screen ${pageBg} transition-colors duration-300 overflow-x-hidden relative`}
         style={{ fontFamily: "'Inter', 'Plus Jakarta Sans', system-ui, sans-serif" }}>

      {/* ═══════ CSS AMBIENT GRADIENT ORBS (Lightweight, no canvas) ═══════ */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className={`absolute -top-[30%] -left-[15%] w-[700px] h-[700px] rounded-full blur-[120px] ${
          isDark ? 'bg-emerald-500/[0.07]' : 'bg-emerald-400/[0.12]'
        }`} style={{ animation: 'float-slow 20s ease-in-out infinite' }} />
        <div className={`absolute top-[20%] -right-[10%] w-[600px] h-[600px] rounded-full blur-[120px] ${
          isDark ? 'bg-teal-500/[0.05]' : 'bg-teal-400/[0.08]'
        }`} style={{ animation: 'float-slow 25s ease-in-out infinite reverse' }} />
        <div className={`absolute -bottom-[20%] left-[30%] w-[500px] h-[500px] rounded-full blur-[120px] ${
          isDark ? 'bg-cyan-500/[0.04]' : 'bg-cyan-400/[0.06]'
        }`} style={{ animation: 'float-slow 22s ease-in-out infinite 3s' }} />
      </div>

      <style>{`
        @keyframes float-slow {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(30px, -20px) scale(1.05); }
          66% { transform: translate(-20px, 15px) scale(0.95); }
        }
      `}</style>

      {/* ═══════════════════ NAVIGATION ═══════════════════ */}
      <nav className={`fixed w-full z-[100] top-0 transition-all duration-500 ${navBg} border-b backdrop-blur-2xl`}>
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <LogoImage size={34} className="rounded-xl transition-transform group-hover:scale-105" />
            <div className="flex items-center gap-2.5">
              <span className={`font-bold text-lg tracking-tight ${textH}`}>DataVision</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 tracking-widest uppercase">
                v3.0
              </span>
            </div>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {['Platform', 'Integrations', 'Developer', 'Enterprise'].map(link => (
              <a key={link} href={`#${link.toLowerCase()}`}
                className={`text-[13px] font-medium ${textP} hover:text-emerald-500 transition-colors`}>
                {link}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-2.5">
            <button onClick={toggleTheme}
              className={`p-2 rounded-lg border transition-all ${
                isDark ? 'border-white/[0.06] text-slate-400 hover:text-white hover:bg-white/5'
                       : 'border-slate-200 text-slate-500 hover:text-slate-900 hover:bg-slate-50'
              }`}>
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <Link to="/login"
              className={`text-[13px] font-medium px-4 py-2 rounded-lg transition-colors hidden sm:block ${
                isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900'
              }`}>
              Sign In
            </Link>
            <Link to={`/datahub?user=${userId}`}
              className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-[13px] transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30">
              Get Started
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ═══════════════════ HERO ═══════════════════ */}
      <section className="relative pt-40 pb-28 z-10">
        <div className="max-w-[980px] mx-auto px-6 text-center">
          <Reveal>
            <div className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-xs font-medium mb-8 ${
              isDark ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-emerald-50 border-emerald-200 text-emerald-700'
            }`}>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              DataVision Enterprise v3.0 — Now Live
            </div>
          </Reveal>

          <Reveal delay={0.08}>
            <h1 className={`text-5xl sm:text-6xl lg:text-[72px] font-extrabold tracking-[-0.03em] leading-[1.06] mb-7 ${textH}`}>
              Turn raw data into{' '}
              <span className="bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500 bg-clip-text text-transparent">
                autonomous decisions
              </span>
            </h1>
          </Reveal>

          <Reveal delay={0.14}>
            <p className={`text-lg sm:text-xl leading-relaxed ${textP} max-w-[720px] mx-auto mb-10`}>
              Connect your data warehouse, and DataVision autonomously builds dashboards, trains ML models, 
              simulates business scenarios, and deploys prediction APIs — all without writing code.
            </p>
          </Reveal>

          <Reveal delay={0.2}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5">
              <Link to={`/datahub?user=${userId}`}
                className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-[15px] shadow-xl shadow-emerald-500/25 hover:shadow-emerald-500/40 transition-all flex items-center justify-center gap-2.5 group">
                Start Analyzing Free
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <a href="#sandbox"
                className={`w-full sm:w-auto px-7 py-3.5 rounded-xl font-semibold text-[15px] border transition-all flex items-center justify-center gap-2.5 ${
                  isDark ? 'border-white/[0.08] text-white hover:bg-white/5' : 'border-slate-200 text-slate-800 hover:bg-slate-50'
                }`}>
                <Sliders className="w-4 h-4 text-emerald-500" />
                Try Live Sandbox
              </a>
            </div>
          </Reveal>

          <Reveal delay={0.28}>
            <div className={`flex items-center justify-center gap-5 flex-wrap mt-12 text-xs font-medium ${textSub}`}>
              {[
                { icon: Database, label: 'PostgreSQL · Snowflake · BigQuery' },
                { icon: BrainCircuit, label: '14+ AutoML Models' },
                { icon: Code, label: 'REST APIs <12ms' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <item.icon className="w-3.5 h-3.5 text-emerald-500" />
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════ METRICS TICKER ═══════════════════ */}
      <section className={`relative py-16 border-y z-10 ${isDark ? 'border-white/[0.04] bg-white/[0.01]' : 'border-slate-100 bg-slate-50/50'}`}>
        <div className="max-w-[1100px] mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-10 text-center">
            {metrics.map((m, i) => (
              <Reveal key={i} delay={i * 0.08}>
                <div>
                  <m.icon className={`w-5 h-5 mx-auto mb-2 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                  <p className={`text-4xl font-extrabold tracking-tight ${textH}`}>
                    <Counter to={m.value} suffix={m.suffix} />
                  </p>
                  <p className={`text-xs font-medium mt-1 uppercase tracking-wider ${textSub}`}>{m.label}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ INTERACTIVE AI SANDBOX ═══════════════════ */}
      <section id="sandbox" className="relative py-28 z-10">
        <div className="max-w-[1200px] mx-auto px-6">
          <Reveal className="text-center max-w-2xl mx-auto mb-14">
            <p className={`text-xs font-bold uppercase tracking-widest mb-3 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`}>
              Interactive Sandbox
            </p>
            <h2 className={`text-3xl sm:text-4xl font-extrabold tracking-tight ${textH}`}>
              Test the AI engine <span className="text-emerald-500">live</span>
            </h2>
            <p className={`text-base mt-3 ${textP}`}>
              Adjust business variables and see real-time sensitivity forecasts powered by DataVision's SHAP analysis engine.
            </p>
          </Reveal>

          <Reveal>
            <div className={`rounded-2xl border overflow-hidden ${
              isDark ? 'bg-white/[0.02] border-white/[0.06]' : 'bg-white border-slate-200 shadow-xl shadow-slate-200/40'
            }`}>
              {/* Header bar */}
              <div className={`h-11 flex items-center px-5 border-b gap-3 ${
                isDark ? 'bg-white/[0.02] border-white/[0.05]' : 'bg-slate-50 border-slate-200'
              }`}>
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-400/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/80" />
                </div>
                <span className={`text-xs font-medium ${textSub} flex items-center gap-2`}>
                  <Activity className="w-3.5 h-3.5 text-emerald-500" />
                  DataVision AI Simulation Engine
                </span>
                <div className="ml-auto">
                  <span className="text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-2.5 py-1 rounded-full flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    {calculatedImpact.confidence}% Confidence
                  </span>
                </div>
              </div>

              {/* Content grid */}
              <div className="p-6 md:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left: Sliders */}
                <div className="lg:col-span-5 space-y-5">
                  <div className={`flex items-center justify-between pb-3 border-b ${isDark ? 'border-white/[0.05]' : 'border-slate-100'}`}>
                    <h3 className={`text-sm font-bold ${textH} flex items-center gap-2`}>
                      <Sliders className="w-4 h-4 text-emerald-500" /> Input Variables
                    </h3>
                    <button onClick={() => { setMarketingBudget(2500000); setUnitPrice(1250); setTeamSize(120); }}
                      className={`text-xs font-medium ${textSub} hover:text-emerald-500 flex items-center gap-1`}>
                      <RefreshCw className="w-3 h-3" /> Reset
                    </button>
                  </div>

                  {[
                    { label: 'Marketing Budget', value: `₹${marketingBudget.toLocaleString()}`, min: 500000, max: 10000000, step: 250000, val: marketingBudget, set: setMarketingBudget, lo: '₹5L', hi: '₹1Cr', accent: 'accent-emerald-500' },
                    { label: 'Unit Price', value: `₹${unitPrice.toLocaleString()}`, min: 250, max: 5000, step: 250, val: unitPrice, set: setUnitPrice, lo: '₹250', hi: '₹5,000', accent: 'accent-teal-500' },
                    { label: 'Team Size', value: `${teamSize} employees`, min: 20, max: 500, step: 10, val: teamSize, set: setTeamSize, lo: '20', hi: '500', accent: 'accent-cyan-500' },
                  ].map((s, i) => (
                    <div key={i}>
                      <div className="flex items-center justify-between text-xs font-medium mb-2">
                        <span className={textP}>{s.label}</span>
                        <span className="text-emerald-500 font-mono font-bold">{s.value}</span>
                      </div>
                      <input type="range" min={s.min} max={s.max} step={s.step} value={s.val}
                        onChange={e => s.set(Number(e.target.value))}
                        className={`w-full h-1.5 rounded-full cursor-pointer ${s.accent} ${isDark ? 'bg-white/[0.06]' : 'bg-slate-200'}`} />
                      <div className="flex justify-between text-[10px] mt-1" style={{ color: isDark ? '#475569' : '#94a3b8' }}>
                        <span>{s.lo}</span><span>{s.hi}</span>
                      </div>
                    </div>
                  ))}

                  <button onClick={() => { setIsSimulating(true); setTimeout(() => setIsSimulating(false), 600); }}
                    disabled={isSimulating}
                    className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2">
                    {isSimulating
                      ? <><RefreshCw className="w-4 h-4 animate-spin" /> Computing...</>
                      : <><Zap className="w-4 h-4" /> Run Simulation</>}
                  </button>
                </div>

                {/* Right: Results */}
                <div className="lg:col-span-7 space-y-5 flex flex-col">
                  <div className="grid grid-cols-2 gap-4">
                    {[
                      { label: 'Projected Revenue', value: `₹${calculatedImpact.revenue} Cr`, growth: `+${calculatedImpact.revenueGrowth}%`, color: 'text-emerald-500' },
                      { label: 'Profit Margin', value: `₹${calculatedImpact.profit} Cr`, growth: `+${calculatedImpact.profitGrowth}%`, color: 'text-teal-500' },
                    ].map((r, i) => (
                      <div key={i} className={`p-4 rounded-xl border ${isDark ? 'bg-white/[0.02] border-white/[0.05]' : 'bg-slate-50 border-slate-200'}`}>
                        <p className={`text-[10px] font-bold uppercase tracking-wider ${textSub}`}>{r.label}</p>
                        <p className={`text-2xl md:text-3xl font-extrabold ${textH} mt-1 font-mono tracking-tight`}>{r.value}</p>
                        <div className={`flex items-center gap-1 text-xs font-bold ${r.color} mt-1`}>
                          <TrendingUp className="w-3.5 h-3.5" /> {r.growth} vs baseline
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* SHAP bars */}
                  <div className={`p-4 rounded-xl border space-y-3 ${isDark ? 'bg-white/[0.02] border-white/[0.05]' : 'bg-slate-50 border-slate-200'}`}>
                    <div className="flex justify-between items-center">
                      <span className={`text-xs font-bold ${textH}`}>SHAP Feature Importance</span>
                      <span className="text-[10px] text-emerald-500 font-medium">Live Sensitivity</span>
                    </div>
                    {[
                      { label: 'Marketing Budget', pct: Math.min(100, (marketingBudget / 10000000) * 100), value: '42.8%', color: 'bg-emerald-500' },
                      { label: 'Unit Price', pct: Math.min(100, (unitPrice / 5000) * 100), value: '31.8%', color: 'bg-teal-500' },
                      { label: 'Team Headcount', pct: Math.min(100, (teamSize / 500) * 100), value: '18.2%', color: 'bg-cyan-500' },
                    ].map((bar, i) => (
                      <div key={i}>
                        <div className="flex justify-between text-[11px] font-medium mb-1">
                          <span className={textP}>{bar.label}</span>
                          <span className={bar.color.replace('bg-', 'text-')} style={{ fontWeight: 700 }}>{bar.value}</span>
                        </div>
                        <div className={`w-full h-1.5 rounded-full overflow-hidden ${isDark ? 'bg-white/[0.06]' : 'bg-slate-200'}`}>
                          <motion.div initial={{ width: 0 }} animate={{ width: `${bar.pct}%` }}
                            transition={{ duration: 0.8, ease: 'easeOut' }}
                            className={`h-full rounded-full ${bar.color}`} />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Gemini insight */}
                  <div className="p-4 rounded-xl bg-emerald-500/[0.06] border border-emerald-500/15 flex items-start gap-3 mt-auto">
                    <Sparkles className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs font-bold text-emerald-600 dark:text-emerald-400">Gemini AI Recommendation</p>
                      <p className={`text-xs ${textP} mt-0.5 leading-relaxed`}>
                        Increasing marketing budget by <strong className={textH}>20%</strong> while keeping unit price
                        at <strong className={textH}>₹{unitPrice.toLocaleString()}</strong> yields maximum margin expansion
                        with <strong className={textH}>{calculatedImpact.confidence}%</strong> statistical confidence.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════ DATA INTEGRATIONS ═══════════════════ */}
      <section id="integrations" className={`relative py-24 border-y z-10 ${isDark ? 'border-white/[0.04]' : 'border-slate-100'} ${sectionAlt}`}>
        <div className="max-w-[1100px] mx-auto px-6">
          <Reveal className="text-center max-w-2xl mx-auto mb-14">
            <p className={`text-xs font-bold uppercase tracking-widest mb-3 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`}>
              Universal Connectors
            </p>
            <h2 className={`text-3xl sm:text-4xl font-extrabold tracking-tight ${textH}`}>
              Connect any data source
            </h2>
            <p className={`text-base mt-3 ${textP}`}>
              Native connectors for enterprise data warehouses, SQL/NoSQL databases, and tabular files.
            </p>
          </Reveal>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {dataIntegrations.map((di, idx) => (
              <Reveal key={di.name} delay={idx * 0.04}>
                <div className={`p-4 rounded-xl border text-center transition-all duration-200 ${card}`}>
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center mx-auto mb-2.5 ${
                    isDark ? 'bg-white/[0.04]' : 'bg-slate-50'
                  }`}>
                    <di.icon className="w-4.5 h-4.5" style={{ color: di.color }} />
                  </div>
                  <p className={`text-xs font-bold ${textH}`}>{di.name}</p>
                  <p className={`text-[10px] mt-0.5 ${textSub}`}>{di.category}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ PLATFORM MODULES ═══════════════════ */}
      <section id="platform" className="relative py-28 z-10">
        <div className="max-w-[1200px] mx-auto px-6">
          <Reveal className="text-center max-w-2xl mx-auto mb-16">
            <p className={`text-xs font-bold uppercase tracking-widest mb-3 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`}>
              Complete Enterprise Platform
            </p>
            <h2 className={`text-3xl sm:text-4xl font-extrabold tracking-tight ${textH}`}>
              10 autonomous AI modules
            </h2>
            <p className={`text-base mt-3 ${textP}`}>
              Every tool you need to go from raw dataset to production AI — in one unified workspace.
            </p>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {modules.map((mod, i) => (
              <Reveal key={mod.title} delay={i * 0.04}>
                <div className={`group relative rounded-2xl border p-6 transition-all duration-200 ${card}`}>
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${mod.gradient} flex items-center justify-center shrink-0 shadow-lg shadow-emerald-500/10 group-hover:scale-105 transition-transform`}>
                      <mod.icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        <h3 className={`text-sm font-bold ${textH} group-hover:text-emerald-500 transition-colors`}>
                          {mod.title}
                        </h3>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                          isDark ? 'bg-emerald-500/10 text-emerald-400' : 'bg-emerald-50 text-emerald-600'
                        } tracking-wider`}>
                          {mod.badge}
                        </span>
                      </div>
                      <p className={`text-xs leading-relaxed ${textP}`}>{mod.desc}</p>
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {mod.tags.map(t => (
                          <span key={t} className={`text-[10px] font-medium px-2 py-0.5 rounded-md ${
                            isDark ? 'bg-white/[0.04] text-slate-400' : 'bg-slate-100 text-slate-600'
                          }`}>{t}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ DEVELOPER API ═══════════════════ */}
      <section id="developer" className={`relative py-28 border-y z-10 ${isDark ? 'border-white/[0.04]' : 'border-slate-100'} ${sectionAlt}`}>
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
            {/* Left: Info */}
            <div className="lg:col-span-5">
              <Reveal>
                <p className={`text-xs font-bold uppercase tracking-widest mb-3 ${isDark ? 'text-cyan-400' : 'text-cyan-600'}`}>
                  Developer First
                </p>
                <h2 className={`text-3xl sm:text-4xl font-extrabold tracking-tight ${textH} mb-4`}>
                  Integrate predictions in 3 lines of code
                </h2>
                <p className={`text-base ${textP} mb-8`}>
                  Generate API keys, deploy REST endpoints with sub-12ms latency, and consume via Python, JavaScript, or cURL.
                </p>
              </Reveal>

              <div className="space-y-3">
                {[
                  { icon: Key, title: 'Generate API Keys', desc: 'Create live keys with granular permissions in seconds.' },
                  { icon: Target, title: 'Select Model Endpoint', desc: 'Target any trained AutoML champion or CV pipeline.' },
                  { icon: Zap, title: 'Stream Predictions', desc: 'Sub-12ms inference with 99.99% SLA uptime.' },
                  { icon: RefreshCw, title: 'Webhooks', desc: 'Instant notifications when models finish training.' },
                ].map((s, i) => (
                  <Reveal key={i} delay={i * 0.06}>
                    <div className={`flex items-start gap-3 p-3.5 rounded-xl border transition-all ${card}`}>
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                        isDark ? 'bg-cyan-500/10' : 'bg-cyan-50'
                      }`}>
                        <s.icon className="w-4 h-4 text-cyan-500" />
                      </div>
                      <div>
                        <h4 className={`text-xs font-bold ${textH}`}>{s.title}</h4>
                        <p className={`text-[11px] ${textSub} mt-0.5`}>{s.desc}</p>
                      </div>
                    </div>
                  </Reveal>
                ))}
              </div>
            </div>

            {/* Right: Code block */}
            <div className="lg:col-span-7">
              <Reveal>
                <div className={`rounded-2xl border overflow-hidden ${codeBg}`}>
                  <div className={`flex items-center justify-between px-4 py-2.5 border-b ${
                    isDark ? 'border-white/[0.05] bg-white/[0.02]' : 'border-slate-200 bg-slate-100'
                  }`}>
                    <div className="flex items-center gap-1.5">
                      {[
                        { id: 'python', label: 'Python' },
                        { id: 'curl', label: 'cURL' },
                        { id: 'javascript', label: 'JavaScript' },
                        { id: 'webhooks', label: 'Webhooks' },
                      ].map(lang => (
                        <button key={lang.id} onClick={() => setActiveCodeLang(lang.id as any)}
                          className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                            activeCodeLang === lang.id
                              ? isDark ? 'bg-cyan-500 text-slate-950' : 'bg-emerald-600 text-white'
                              : isDark ? 'text-slate-500 hover:text-white' : 'text-slate-500 hover:text-slate-900'
                          }`}>
                          {lang.label}
                        </button>
                      ))}
                    </div>
                    <button onClick={() => handleCopy(codeSnippets[activeCodeLang])}
                      className={`flex items-center gap-1 text-xs px-2 py-1 rounded-md border ${
                        isDark ? 'text-slate-500 hover:text-white border-white/[0.06]' : 'text-slate-500 hover:text-slate-900 border-slate-200'
                      }`}>
                      {copiedCode ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      {copiedCode ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <div className={`p-5 font-mono text-xs leading-relaxed overflow-x-auto ${
                    isDark ? 'text-emerald-400' : 'text-slate-800'
                  }`}>
                    <pre className="whitespace-pre">{codeSnippets[activeCodeLang]}</pre>
                  </div>
                </div>
              </Reveal>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════ 4-STEP WORKFLOW ═══════════════════ */}
      <section className="relative py-28 z-10">
        <div className="max-w-[1000px] mx-auto px-6">
          <Reveal className="text-center max-w-2xl mx-auto mb-16">
            <p className={`text-xs font-bold uppercase tracking-widest mb-3 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`}>
              How It Works
            </p>
            <h2 className={`text-3xl sm:text-4xl font-extrabold tracking-tight ${textH}`}>
              From raw CSV to deployed AI in 60 seconds
            </h2>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {workflowSteps.map((ws, idx) => (
              <Reveal key={ws.step} delay={idx * 0.08}>
                <div className={`p-5 rounded-2xl border text-center h-full flex flex-col items-center ${card}`}>
                  <span className="text-2xl font-extrabold text-emerald-500 mb-3">{ws.step}</span>
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-3 ${
                    isDark ? 'bg-emerald-500/10' : 'bg-emerald-50'
                  }`}>
                    <ws.icon className="w-5 h-5 text-emerald-500" />
                  </div>
                  <h3 className={`text-sm font-bold ${textH} mb-1.5`}>{ws.title}</h3>
                  <p className={`text-xs leading-relaxed ${textSub}`}>{ws.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ ENTERPRISE SECURITY ═══════════════════ */}
      <section id="enterprise" className={`relative py-20 border-y z-10 ${isDark ? 'border-white/[0.04]' : 'border-slate-100'} ${sectionAlt}`}>
        <div className="max-w-[1000px] mx-auto px-6">
          <Reveal className="text-center mb-12">
            <h2 className={`text-2xl sm:text-3xl font-extrabold tracking-tight ${textH}`}>
              Enterprise-grade security
            </h2>
            <p className={`text-sm mt-2 ${textSub}`}>Built for strict corporate compliance and data isolation.</p>
          </Reveal>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { title: 'SOC 2 Type II', icon: Shield, desc: 'Audited infrastructure' },
              { title: 'AES-256', icon: Lock, desc: 'End-to-end encryption' },
              { title: 'GDPR & HIPAA', icon: Globe, desc: 'Data residency isolation' },
              { title: '99.99% SLA', icon: Gauge, desc: 'High availability' },
            ].map((s, i) => (
              <Reveal key={i} delay={i * 0.06}>
                <div className={`p-5 rounded-xl border text-center ${card}`}>
                  <s.icon className={`w-5 h-5 mx-auto mb-2 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                  <p className={`text-xs font-bold ${textH} mb-0.5`}>{s.title}</p>
                  <p className={`text-[11px] ${textSub}`}>{s.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ FINAL CTA ═══════════════════ */}
      <section className="relative py-32 z-10">
        <div className="max-w-[700px] mx-auto px-6 text-center">
          <Reveal>
            <h2 className={`text-3xl sm:text-5xl font-extrabold tracking-tight ${textH} mb-5`}>
              Ready to supercharge your data?
            </h2>
            <p className={`text-base ${textP} mb-10 max-w-lg mx-auto`}>
              Experience autonomous dashboards, 1-click AutoML, digital twin simulations, and developer APIs — all in one platform.
            </p>
            <Link to={`/datahub?user=${userId}`}
              className="inline-flex items-center gap-2.5 px-8 py-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-base shadow-xl shadow-emerald-500/25 hover:shadow-emerald-500/40 transition-all group">
              Launch Workspace
              <ArrowRight className="w-4.5 h-4.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════ FOOTER ═══════════════════ */}
      <footer className={`border-t relative z-10 py-10 ${isDark ? 'border-white/[0.04] bg-[#06070a]' : 'border-slate-100 bg-white'}`}>
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
            {/* Brand */}
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-2.5 mb-3">
                <LogoImage size={28} className="rounded-lg" />
                <span className={`font-bold ${textH}`}>DataVision</span>
              </div>
              <p className={`text-xs leading-relaxed ${textSub}`}>
                The enterprise AI platform that turns raw data into autonomous decisions.
              </p>
            </div>

            {/* Links */}
            {[
              { title: 'Platform', links: ['AutoML', 'Dashboards', 'CV Studio', 'Simulator', 'Autopilot'] },
              { title: 'Developers', links: ['API Reference', 'Python SDK', 'Webhooks', 'Status'] },
              { title: 'Company', links: ['About', 'Privacy Policy', 'Terms of Service', 'Contact'] },
            ].map(col => (
              <div key={col.title}>
                <h4 className={`text-xs font-bold uppercase tracking-wider mb-3 ${textSub}`}>{col.title}</h4>
                <ul className="space-y-2">
                  {col.links.map(link => (
                    <li key={link}>
                      <a href="#" className={`text-xs ${textP} hover:text-emerald-500 transition-colors`}>{link}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className={`pt-6 border-t flex flex-col sm:flex-row items-center justify-between gap-3 ${
            isDark ? 'border-white/[0.04]' : 'border-slate-100'
          }`}>
            <p className={`text-xs ${textSub}`}>© {new Date().getFullYear()} DataVision Enterprise Inc. All rights reserved.</p>
            <div className={`flex items-center gap-4 text-xs ${textSub}`}>
              <a href="#" className="hover:text-emerald-500 transition-colors">Privacy</a>
              <a href="#" className="hover:text-emerald-500 transition-colors">Terms</a>
              <a href="#" className="hover:text-emerald-500 transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
