import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowRight, Database, LayoutDashboard, BrainCircuit,
  Eye, Sliders, Server, Search, Check, ShieldCheck,
  Zap, Code, ChevronRight, Activity, Terminal, ChevronDown,
  Layers, Lock, Play, Cpu, Sparkles, CheckCircle2,
  FileSpreadsheet, Share2, Workflow, Globe, Shield, RefreshCw,
  Sun, Moon, ExternalLink, Network, Gauge, Calculator, CheckCircle,
  TrendingUp, BarChart3, PieChart, HelpCircle
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { getUserIdSync } from '../utils/userId';
import LogoImage from '../components/LogoImage';
import { useUserStore } from '../store/userStore';

/* ═══════════════════════════════════════════════════════════════════════
   AUTHENTIC CONNECTOR SVG LOGOS
   ═══════════════════════════════════════════════════════════════════════ */
const SnowflakeLogo = () => (
  <svg className="h-5 w-auto" viewBox="0 0 24 24" fill="#29B5E8">
    <path d="M12 0l1.8 4.2L16 2.5l-1 3.5 4.3-.8-2.5 3.3 4.2 1.8-4.2 1.8 2.5 3.3-4.3-.8 1 3.5-2.2-1.7L12 24l-1.8-4.2L8 21.5l1-3.5-4.3.8 2.5-3.3L3 13.7l4.2-1.8-2.5-3.3 4.3.8-1-3.5 2.2 1.7z"/>
  </svg>
);

const DatabricksLogo = () => (
  <svg className="h-5 w-auto" viewBox="0 0 24 24" fill="#FF3621">
    <path d="M12 2L1 8l11 6 11-6-11-6zm0 8.5L4.5 7 12 3.5l7.5 3.5-7.5 3.5zm0 4.5L1 9v6l11 6 11-6V9l-11 6z"/>
  </svg>
);

const PostgresLogo = () => (
  <svg className="h-5 w-auto" viewBox="0 0 24 24" fill="#336791">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
  </svg>
);

const KafkaLogo = () => (
  <svg className="h-5 w-auto text-current" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l7 4.5-7 4.5z"/>
  </svg>
);

const BigQueryLogo = () => (
  <svg className="h-5 w-auto" viewBox="0 0 24 24" fill="#4285F4">
    <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
  </svg>
);

const MongoDbLogo = () => (
  <svg className="h-5 w-auto" viewBox="0 0 24 24" fill="#13AA52">
    <path d="M12 0C11.5 2.5 10 6 7 9c-3 3-5 7-5 10.5C2 22.5 6.5 24 12 24s10-1.5 10-4.5c0-3.5-2-7.5-5-10.5-3-3-4.5-6.5-5-9z"/>
  </svg>
);

const RedshiftLogo = () => (
  <svg className="h-5 w-auto" viewBox="0 0 24 24" fill="#CC292B">
    <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.8L19.2 8 12 11.2 4.8 8 12 4.8zM4 9.6l7 3.5v7.2l-7-3.5V9.6zm16 7.2l-7 3.5v-7.2l7-3.5v7.2z"/>
  </svg>
);

const MySqlLogo = () => (
  <svg className="h-5 w-auto" viewBox="0 0 24 24" fill="#00758F">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
  </svg>
);

export default function Landing() {
  const navigate = useNavigate();
  const userId = getUserIdSync();
  const { isDark, toggleTheme } = useUserStore();

  // Active Product Tab (8 Full Core Modules)
  const [activeTab, setActiveTab] = useState<
    'dashboard' | 'automl' | 'cv' | 'simulator' | 'analyst' | 'datahub' | 'vector' | 'developer'
  >('dashboard');

  // Simulator Sliders State
  const [price, setPrice] = useState(85);
  const [marketing, setMarketing] = useState(30000);
  const [churnRate, setChurnRate] = useState(2.0);
  const [headcount, setHeadcount] = useState(45);

  // FAQ Accordion State
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  // Interactive ROI Calculator State
  const [monthlyRows, setMonthlyRows] = useState(5); // Millions
  const [teamSize, setTeamSize] = useState(8); // Analysts/Engineers

  // Calculated Metrics
  const calculatedRev = Math.round((price * 950) + (marketing * 0.24) - (churnRate * 35000) + (headcount * 1200));
  const calculatedRoi = Math.round(((calculatedRev - marketing) / marketing) * 100);

  const hoursSavedPerWeek = Math.round(teamSize * 14);
  const annualSavingsDollars = Math.round((monthlyRows * 18000) + (teamSize * 12500));

  // Dedicated Screenshot Image Mapping per Tab for both Dark and Light mode
  const darkDemoImages: Record<string, string> = {
    dashboard: '/dashboard-dark.png',
    automl: '/automl-dark.png',
    cv: '/cv-demo.png',
    simulator: '/simulator-dark.png',
    analyst: '/developer-demo.png',
    datahub: '/datahub-light.png',
    vector: '/vector-dark.png',
    developer: '/developer-demo.png'
  };

  const lightDemoImages: Record<string, string> = {
    dashboard: '/dashboard-demo.png',
    automl: '/automl-demo.png',
    cv: '/cv-light.png',
    simulator: '/simulator-demo.png',
    analyst: '/developer-light.png',
    datahub: '/datahub-light.png',
    vector: '/vector-light.png',
    developer: '/developer-light.png'
  };

  const currentTabImage = isDark ? darkDemoImages[activeTab] : lightDemoImages[activeTab];

  // Dynamic Theme Styling Tokens
  const bgMain = isDark ? 'bg-[#05060A] text-white' : 'bg-[#FFFFFF] text-[#111827]';
  const bgCard = isDark ? 'bg-[#0B0D14]/95 border-white/[0.08]' : 'bg-[#FFFFFF] border-[#E5E7EB] shadow-sm';
  const bgNav = isDark ? 'bg-[#05060A]/85 border-white/[0.08]' : 'bg-[#FFFFFF]/95 border-[#E5E7EB]';
  const bgSecondary = isDark ? 'bg-[#080A10] border-white/[0.06]' : 'bg-[#F8FAFC] border-[#E5E7EB]';
  const textMuted = isDark ? 'text-slate-400' : 'text-[#6B7280]';
  const textTitle = isDark ? 'text-white' : 'text-[#111827]';
  const borderClean = isDark ? 'border-white/[0.08]' : 'border-[#E5E7EB]';

  return (
    <div className={`min-h-screen font-sans antialiased selection:bg-[#16A34A]/20 selection:text-[#16A34A] transition-colors duration-300 ${bgMain}`}>

      {/* ═══════════════════ NAVBAR ═══════════════════ */}
      <header className={`sticky top-0 z-50 border-b backdrop-blur-md transition-colors ${bgNav}`}>
        <div className="max-w-[1280px] mx-auto px-6 h-16 flex items-center justify-between">
          
          {/* User's Authentic DataVision Eye & Globe Startup Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <LogoImage isDark={isDark} size={38} showText={true} />
          </Link>

          {/* Navigation Links */}
          <nav className={`hidden lg:flex items-center gap-8 text-xs font-semibold ${textMuted}`}>
            <a href="#workflow" className="hover:text-[#16A34A] transition-colors">Workflow</a>
            <a href="#preview" className="hover:text-[#16A34A] transition-colors">Live Studio</a>
            <a href="#services" className="hover:text-[#16A34A] transition-colors">Services</a>
            <a href="#benchmarks" className="hover:text-[#16A34A] transition-colors">Benchmarks</a>
            <a href="#calculator" className="hover:text-[#16A34A] transition-colors">ROI Calculator</a>
            <a href="#faq" className="hover:text-[#16A34A] transition-colors">FAQ</a>
            <a href="#security" className="hover:text-[#16A34A] transition-colors">Security</a>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            {/* Dark / Light Theme Switcher */}
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg border transition-colors ${
                isDark ? 'border-white/10 text-amber-400 hover:bg-white/5' : 'border-[#E5E7EB] text-[#6B7280] hover:bg-[#F8FAFC]'
              }`}
              title="Toggle Light / Dark Mode"
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <Link
              to="/login"
              className={`hidden sm:inline-flex px-3.5 py-2 text-xs font-semibold rounded-lg border transition-colors ${
                isDark ? 'border-white/10 text-white hover:bg-white/5' : 'border-[#E5E7EB] text-[#111827] hover:bg-[#F8FAFC]'
              }`}
            >
              Sign In
            </Link>

            <Link
              to={`/datahub?user=${userId}`}
              className="px-4 py-2 bg-[#16A34A] hover:bg-[#15803D] text-white text-xs font-bold rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
            >
              Launch Workspace
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* ═══════════════════ HERO SECTION ═══════════════════ */}
      <section className={`pt-14 pb-20 border-b transition-colors ${bgMain} ${borderClean}`}>
        <div className="max-w-[1280px] mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* LEFT COLUMN: HEADLINE & CTAS */}
          <div className="lg:col-span-5 space-y-6">
            
            {/* Release Badge */}
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-medium ${
              isDark ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-[#F8FAFC] border-[#E5E7EB] text-[#111827]'
            }`}>
              <span className="w-2 h-2 rounded-full bg-[#16A34A]" />
              <span className="font-bold text-[#16A34A]">NEW</span>
              <span className={textMuted}>•</span>
              <span className={textMuted}>Enterprise AI Lakehouse v2.5</span>
            </div>

            {/* Large Headline */}
            <h1 className={`text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] ${textTitle}`}>
              Transform Enterprise{' '}
              <span className="text-[#16A34A]">Data</span>{' '}
              Into Intelligent Decisions.
            </h1>

            {/* Paragraph */}
            <p className={`text-base leading-relaxed font-normal ${textMuted}`}>
              DataVision unifies Business Intelligence, Ultra AutoML, Multi-Task Computer Vision, Vector RAG Search, and AI Agents into one platform. Streamline data engineering to production inference without infrastructure overhead.
            </p>

            {/* Button CTA Group */}
            <div className="flex items-center gap-3 pt-2">
              <Link
                to={`/datahub?user=${userId}`}
                className="px-6 py-3.5 bg-[#16A34A] hover:bg-[#15803D] text-white text-xs font-bold rounded-lg shadow-sm transition-colors flex items-center gap-2"
              >
                Launch Workspace
                <ArrowRight className="w-4 h-4" />
              </Link>

              <button
                onClick={() => navigate('/chat')}
                className={`px-6 py-3.5 text-xs font-bold rounded-lg border transition-colors ${
                  isDark ? 'border-white/15 text-white hover:bg-white/5' : 'bg-[#FFFFFF] border-[#E5E7EB] text-[#111827] hover:bg-[#F8FAFC]'
                }`}
              >
                Book Demo
              </button>
            </div>

            {/* Customer Trust Text */}
            <div className={`pt-4 border-t ${borderClean}`}>
              <p className={`text-xs font-semibold ${textMuted}`}>
                Native database connectors: Snowflake, Postgres, Databricks, Kafka, BigQuery & MongoDB.
              </p>
            </div>

          </div>

          {/* RIGHT COLUMN: MACOS PRODUCT SHOWCASE WINDOW WITH DATAVISION LOGO */}
          <div className="lg:col-span-7" id="preview">
            <div className={`rounded-xl border shadow-xl overflow-hidden ${bgCard}`}>
              
              {/* MacOS Window Top Bar */}
              <div className={`px-4 py-3 border-b flex items-center justify-between ${
                isDark ? 'bg-[#0E111A] border-white/10' : 'bg-[#F8FAFC] border-[#E5E7EB]'
              }`}>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-full bg-[#EF4444]" />
                    <span className="w-3 h-3 rounded-full bg-[#F59E0B]" />
                    <span className="w-3 h-3 rounded-full bg-[#10B981]" />
                  </div>
                  {/* Official DataVision Eye Logo in Window Header */}
                  <div className="border-l pl-3 border-white/10">
                    <LogoImage isDark={isDark} size={22} showText={true} />
                  </div>
                </div>

                <div className={`px-4 py-1 rounded border text-[11px] font-mono flex items-center gap-2 ${
                  isDark ? 'bg-black/50 border-white/10 text-emerald-400' : 'bg-[#FFFFFF] border-[#E5E7EB] text-[#6B7280]'
                }`}>
                  <ShieldCheck className="w-3.5 h-3.5 text-[#16A34A]" />
                  https://datavision.ai/app/{activeTab}
                </div>

                <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#16A34A]">
                  <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-ping" />
                  {isDark ? 'DARK MODE UI' : 'LIGHT MODE UI'}
                </div>
              </div>

              {/* 8 Product Tabs Navigation */}
              <div className={`flex border-b px-3 gap-1 overflow-x-auto scrollbar-none ${
                isDark ? 'bg-[#080A10] border-white/10' : 'bg-[#FFFFFF] border-[#E5E7EB]'
              }`}>
                {[
                  { id: 'dashboard', label: 'Dashboard', color: 'text-emerald-500' },
                  { id: 'automl', label: 'AutoML Studio', color: 'text-indigo-500' },
                  { id: 'cv', label: 'Computer Vision', color: 'text-cyan-500' },
                  { id: 'simulator', label: 'Simulator', color: 'text-amber-500' },
                  { id: 'analyst', label: 'AI Analyst', color: 'text-rose-500' },
                  { id: 'datahub', label: 'DataHub ETL', color: 'text-sky-500' },
                  { id: 'vector', label: 'Vector AI', color: 'text-purple-500' },
                  { id: 'developer', label: 'Developer API', color: 'text-teal-500' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`px-3.5 py-2.5 text-xs font-semibold border-b-2 transition-colors shrink-0 ${
                      activeTab === tab.id
                        ? `border-[#16A34A] ${tab.color} ${isDark ? 'bg-white/5' : 'bg-[#F8FAFC]'}`
                        : `border-transparent ${textMuted} hover:text-[#16A34A]`
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* PERFECT FULL-BLEED SCREENSHOT DISPLAY */}
              <div className={`relative ${isDark ? 'bg-[#05060A]' : 'bg-[#F8FAFC]'}`}>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab + (isDark ? '-dark' : '-light')}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-4"
                  >
                    {/* Full-Bleed High-Res Image Showcase */}
                    <div className="w-full overflow-hidden bg-center bg-cover">
                      <img 
                        src={currentTabImage} 
                        alt={`DataVision ${activeTab} Enterprise Platform`} 
                        className="w-full h-auto max-h-[420px] object-cover block"
                      />
                    </div>

                    {/* Interactive Simulator Controls Overlay */}
                    {activeTab === 'simulator' && (
                      <div className="p-4">
                        <div className={`p-4 rounded-lg border grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs ${bgCard}`}>
                          <div className="space-y-2">
                            <div className="flex justify-between font-semibold"><span>Price ($)</span><span className="font-bold text-amber-500">${price}</span></div>
                            <input type="range" min="30" max="200" value={price} onChange={(e)=>setPrice(Number(e.target.value))} className="w-full accent-amber-500" />
                            
                            <div className="flex justify-between font-semibold pt-1"><span>Marketing ($)</span><span className="font-bold text-amber-500">${marketing.toLocaleString()}</span></div>
                            <input type="range" min="5000" max="100000" step="5000" value={marketing} onChange={(e)=>setMarketing(Number(e.target.value))} className="w-full accent-amber-500" />
                          </div>

                          <div className={`p-3.5 rounded border flex flex-col justify-between ${
                            isDark ? 'bg-amber-950/20 border-amber-500/30' : 'bg-amber-50/90 border-amber-200'
                          }`}>
                            <div>
                              <span className="text-[11px] font-bold text-amber-600 uppercase">Simulated Revenue</span>
                              <div className="text-2xl font-extrabold text-amber-600 mt-0.5">₹{(calculatedRev / 100000).toFixed(2)} Lakhs</div>
                            </div>
                            <div className="pt-2 border-t border-amber-300/40 flex justify-between text-xs font-bold text-amber-700">
                              <span>Marketing ROI</span>
                              <span className="text-emerald-600 font-extrabold">{calculatedRoi}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* ═══════════════════ REAL LOGO CONNECTOR STRIP ═══════════════════ */}
      <section className={`py-10 border-b transition-colors ${bgSecondary}`}>
        <div className="max-w-[1280px] mx-auto px-6">
          <p className={`text-center text-xs font-bold uppercase tracking-wider mb-6 ${textMuted}`}>
            SUPPORTED DATA ENGINE & WAREHOUSE CONNECTORS
          </p>

          <div className="flex items-center justify-center gap-8 md:gap-14 flex-wrap">
            <div className="flex items-center gap-2"><SnowflakeLogo /><span className="font-bold text-xs">Snowflake</span></div>
            <div className="flex items-center gap-2"><DatabricksLogo /><span className="font-bold text-xs">Databricks</span></div>
            <div className="flex items-center gap-2"><PostgresLogo /><span className="font-bold text-xs">PostgreSQL</span></div>
            <div className="flex items-center gap-2"><KafkaLogo /><span className="font-bold text-xs">Apache Kafka</span></div>
            <div className="flex items-center gap-2"><BigQueryLogo /><span className="font-bold text-xs">Google BigQuery</span></div>
            <div className="flex items-center gap-2"><MongoDbLogo /><span className="font-bold text-xs">MongoDB</span></div>
            <div className="flex items-center gap-2"><RedshiftLogo /><span className="font-bold text-xs">Amazon Redshift</span></div>
            <div className="flex items-center gap-2"><MySqlLogo /><span className="font-bold text-xs">MySQL</span></div>
          </div>
        </div>
      </section>

      {/* ═══════════════════ MIDDLE SECTION A: 3-STEP AUTONOMOUS WORKFLOW ═══════════════════ */}
      <section id="workflow" className={`py-20 border-b transition-colors ${bgMain} ${borderClean}`}>
        <div className="max-w-[1280px] mx-auto px-6 space-y-12">
          
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-xs font-bold">
              <Workflow className="w-3.5 h-3.5" />
              END-TO-END AUTOMATION PIPELINE
            </div>
            <h2 className={`text-3xl font-bold tracking-tight ${textTitle}`}>
              How DataVision Automates Business Data
            </h2>
            <p className={`text-sm ${textMuted}`}>
              From raw data streams to production REST endpoints and interactive simulations in 3 seamless steps.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className={`p-8 rounded-xl border relative space-y-4 ${bgCard}`}>
              <div className="w-8 h-8 rounded-lg bg-emerald-500 text-white font-extrabold flex items-center justify-center text-sm">1</div>
              <h3 className={`text-lg font-bold ${textTitle}`}>Connect Data Lakes & Streams</h3>
              <p className={`text-xs leading-relaxed ${textMuted}`}>
                Stream raw event telemetry via live API Push or connect Snowflake, Postgres, Kafka, and CSV files with 20+ automated quality checks.
              </p>
            </div>

            <div className={`p-8 rounded-xl border relative space-y-4 ${bgCard}`}>
              <div className="w-8 h-8 rounded-lg bg-indigo-500 text-white font-extrabold flex items-center justify-center text-sm">2</div>
              <h3 className={`text-lg font-bold ${textTitle}`}>Concurrent Multi-Engine AI</h3>
              <p className={`text-xs leading-relaxed ${textMuted}`}>
                DataVision auto-profiles columns, cleans missing values, trains 6 SOTA models simultaneously, and indexes metadata in Qdrant Vector DB.
              </p>
            </div>

            <div className={`p-8 rounded-xl border relative space-y-4 ${bgCard}`}>
              <div className="w-8 h-8 rounded-lg bg-amber-500 text-white font-extrabold flex items-center justify-center text-sm">3</div>
              <h3 className={`text-lg font-bold ${textTitle}`}>Deploy & Simulate</h3>
              <p className={`text-xs leading-relaxed ${textMuted}`}>
                Deploy &lt;11ms REST prediction endpoints, run interactive scenario sensitivity sliders, and auto-generate executive report artifacts.
              </p>
            </div>
          </div>

        </div>
      </section>

      {/* ═══════════════════ DISTINCT COLOR CODED ENTERPRISE SERVICES ═══════════════════ */}
      <section id="services" className={`py-20 border-b transition-colors ${bgSecondary}`}>
        <div className="max-w-[1280px] mx-auto px-6 space-y-12">
          
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className={`text-3xl font-bold tracking-tight ${textTitle}`}>
              Enterprise AI Lakehouse Services
            </h2>
            <p className={`text-sm ${textMuted}`}>
              8 dedicated platform services engineered for enterprise intelligence, predictive modeling, and vector analytics.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: 'Autonomous BI & Profiling',
                desc: 'Auto-engineer 15+ chart types, correlation heatmaps, and KPI cards with zero drag-and-drop manual work.',
                icon: LayoutDashboard,
                colorBg: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
                accentColor: 'text-emerald-500',
                route: '/dashboard'
              },
              {
                title: 'Ultra AutoML & Model Hub',
                desc: 'Train 6 SOTA engines (XGBoost, LightGBM, CatBoost, PyTorch NN) with SHAP explainability and 1-click model registry.',
                icon: BrainCircuit,
                colorBg: 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
                accentColor: 'text-indigo-500',
                route: '/ml-predictions'
              },
              {
                title: 'Multi-Task Vision Studio',
                desc: 'YOLOv8 & ResNet studio for Object Detection, Instance Segmentation, Pose Keypoints, and OCR Text Extraction.',
                icon: Eye,
                colorBg: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
                accentColor: 'text-cyan-500',
                route: '/computer-vision'
              },
              {
                title: 'Digital Twin Simulator',
                desc: 'Interactive sensitivity sliders for revenue, churn, and budget trade-offs with Monte Carlo confidence intervals.',
                icon: Sliders,
                colorBg: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
                accentColor: 'text-amber-500',
                route: '/simulator'
              },
              {
                title: 'Embedded Qdrant Vector AI',
                desc: '384d MiniLM-L6 vector embeddings for natural language semantic search and AI analyst context memory.',
                icon: Database,
                colorBg: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
                accentColor: 'text-purple-500',
                route: '/lineage'
              },
              {
                title: 'Generative AI Analyst (RAG)',
                desc: 'Gemini 1.5 & GPT-4 LLM chat assistant generating interactive smart charts, SQL queries, and executive reports.',
                icon: Zap,
                colorBg: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
                accentColor: 'text-rose-500',
                route: '/chat'
              },
              {
                title: 'Live API Telemetry Push',
                desc: 'Stream raw telemetry from Snowflake, Kafka, or Python scripts with live event log counters.',
                icon: Activity,
                colorBg: 'bg-sky-500/10 text-sky-500 border-sky-500/20',
                accentColor: 'text-sky-500',
                route: '/datahub'
              },
              {
                title: 'Developer REST API & SDK',
                desc: 'Serve predictions with <11ms latency, generate API keys, stream webhooks, and execute code in Web IDE.',
                icon: Code,
                colorBg: 'bg-teal-500/10 text-teal-500 border-teal-500/20',
                accentColor: 'text-teal-500',
                route: '/developer'
              }
            ].map((service) => (
              <div
                key={service.title}
                onClick={() => navigate(service.route)}
                className={`p-6 rounded-xl border transition-all cursor-pointer group shadow-2xs hover:shadow-md flex flex-col justify-between ${bgCard} hover:border-[#16A34A]/50`}
              >
                <div className="space-y-3">
                  <div className={`w-10 h-10 rounded-lg border flex items-center justify-center transition-colors ${service.colorBg}`}>
                    <service.icon className="w-5 h-5" />
                  </div>
                  <h3 className={`text-base font-bold transition-colors ${textTitle}`}>
                    {service.title}
                  </h3>
                  <p className={`text-xs leading-relaxed ${textMuted}`}>
                    {service.desc}
                  </p>
                </div>

                <div className={`pt-4 border-t flex items-center justify-between text-xs font-bold ${service.accentColor} mt-4 ${borderClean}`}>
                  <span>Explore service</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            ))}
          </div>

        </div>
      </section>

      {/* ═══════════════════ BENCHMARK TABLE ═══════════════════ */}
      <section id="benchmarks" className={`py-20 border-b transition-colors ${bgMain} ${borderClean}`}>
        <div className="max-w-[1280px] mx-auto px-6 space-y-10">
          
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className={`text-3xl font-bold tracking-tight ${textTitle}`}>
              Verified Capability Benchmarks
            </h2>
            <p className={`text-sm ${textMuted}`}>
              Compare DataVision against traditional BI software and legacy AutoML frameworks.
            </p>
          </div>

          <div className={`rounded-xl border overflow-hidden shadow-2xs ${bgCard}`}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className={`border-b uppercase font-semibold text-[11px] ${
                  isDark ? 'bg-white/5 border-white/10 text-slate-400' : 'bg-[#F8FAFC] border-[#E5E7EB] text-[#6B7280]'
                }`}>
                  <tr>
                    <th className="p-4">Enterprise Metric / Capability</th>
                    <th className="p-4 text-[#16A34A] font-bold">DataVision 2.5</th>
                    <th className="p-4">Traditional BI</th>
                    <th className="p-4">Legacy AutoML</th>
                  </tr>
                </thead>
                <tbody className={`divide-y text-xs ${isDark ? 'divide-white/5 text-slate-200' : 'divide-[#E5E7EB] text-[#111827]'}`}>
                  {[
                    { cap: 'Inference Latency', dv: '< 11ms Global Edge', bi: '120ms Batch', legacy: '450ms Server' },
                    { cap: 'Concurrent SOTA AutoML Engines', dv: '6 Engines (XGBoost, LightGBM, CatBoost, NN)', bi: 'None', legacy: '1 Model' },
                    { cap: 'Interactive Scenario Sliders + SHAP', dv: 'Realtime SHAP Sliders', bi: 'Static PDF', legacy: 'Manual Python' },
                    { cap: 'Computer Vision Studio', dv: 'YOLOv8 + ResNet (Object, Seg, Pose, OCR)', bi: 'Not Supported', legacy: 'Third-Party Tool' },
                    { cap: 'Vector Database RAG Memory', dv: 'Embedded Qdrant (384d MiniLM-L6)', bi: 'None', legacy: 'Custom Setup' },
                    { cap: 'Realtime Live Telemetry Push', dv: 'WebSocket Accumulator', bi: 'Batch Only', legacy: 'Batch Only' },
                    { cap: 'Model Export Package', dv: '1-Click ONNX / Docker / Python ZIP', bi: 'PDF Export Only', legacy: 'Manual Export' }
                  ].map((row, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? (isDark ? 'bg-white/[0.01]' : 'bg-[#FFFFFF]') : (isDark ? 'bg-white/[0.03]' : 'bg-[#F8FAFC]')}>
                      <td className="p-4 font-bold">{row.cap}</td>
                      <td className="p-4 font-bold text-[#16A34A] flex items-center gap-1.5">
                        <Check className="w-4 h-4 text-[#16A34A] shrink-0" />
                        {row.dv}
                      </td>
                      <td className={`p-4 ${textMuted}`}>{row.bi}</td>
                      <td className={`p-4 ${textMuted}`}>{row.legacy}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </section>

      {/* ═══════════════════ INTERACTIVE ENTERPRISE ROI CALCULATOR ═══════════════════ */}
      <section id="calculator" className={`py-20 border-b transition-colors ${bgSecondary}`}>
        <div className="max-w-[1280px] mx-auto px-6 space-y-10">
          
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-xs font-bold">
              <Calculator className="w-3.5 h-3.5" />
              INTERACTIVE ROI & TIME SAVINGS CALCULATOR
            </div>
            <h2 className={`text-3xl font-bold tracking-tight ${textTitle}`}>
              Calculate Your Enterprise ROI
            </h2>
            <p className={`text-sm ${textMuted}`}>
              See how much time and operational budget DataVision saves your engineering team.
            </p>
          </div>

          <div className={`p-8 rounded-xl border grid grid-cols-1 lg:grid-cols-12 gap-8 items-center ${bgCard}`}>
            
            {/* Controls */}
            <div className="lg:col-span-7 space-y-6 text-xs">
              <div>
                <div className="flex justify-between font-bold text-sm mb-2">
                  <span className={textTitle}>Monthly Data Ingestion (Millions of Rows)</span>
                  <span className="text-[#16A34A]">{monthlyRows}M Rows/mo</span>
                </div>
                <input
                  type="range" min="1" max="50" value={monthlyRows}
                  onChange={(e) => setMonthlyRows(Number(e.target.value))}
                  className="w-full accent-[#16A34A]"
                />
              </div>

              <div>
                <div className="flex justify-between font-bold text-sm mb-2">
                  <span className={textTitle}>Data & ML Team Size (Analysts/Engineers)</span>
                  <span className="text-[#16A34A]">{teamSize} Members</span>
                </div>
                <input
                  type="range" min="2" max="50" value={teamSize}
                  onChange={(e) => setTeamSize(Number(e.target.value))}
                  className="w-full accent-[#16A34A]"
                />
              </div>
            </div>

            {/* Calculated Output Display */}
            <div className="lg:col-span-5 p-6 rounded-lg bg-[#16A34A] text-white space-y-4 text-center shadow-lg">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-100 block">Estimated Annual Savings</span>
                <div className="text-4xl font-extrabold mt-1 font-mono">${annualSavingsDollars.toLocaleString()} / yr</div>
              </div>
              <div className="pt-3 border-t border-emerald-400/40 flex justify-between text-xs font-semibold">
                <span>Engineering Hours Saved:</span>
                <span className="font-bold">{hoursSavedPerWeek} hrs / wk</span>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* ═══════════════════ FAQ SECTION ═══════════════════ */}
      <section id="faq" className={`py-20 border-b transition-colors ${bgMain} ${borderClean}`}>
        <div className="max-w-[1280px] mx-auto px-6 space-y-10">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className={`text-3xl font-bold tracking-tight ${textTitle}`}>
              Frequently Asked Questions
            </h2>
            <p className={`text-sm ${textMuted}`}>
              Everything you need to know about DataVision Enterprise AI Lakehouse.
            </p>
          </div>

          <div className="max-w-3xl mx-auto space-y-4 text-xs">
            {[
              {
                q: 'How does DataVision connect to my existing database?',
                a: 'DataVision provides native, zero-copy read connectors for Snowflake, Databricks, PostgreSQL, Apache Kafka, Google BigQuery, and MongoDB. Connect with 1-click credentials or stream via our live API Push endpoint.'
              },
              {
                q: 'Where are vector embeddings stored for semantic search?',
                a: 'All vector embeddings are generated using the MiniLM-L6 transformer model (384 dimensions) and stored in an embedded Qdrant vector database instance for ultra-fast cosine similarity retrieval.'
              },
              {
                q: 'Can I deploy DataVision in a private cloud or on-premise?',
                a: 'Yes. DataVision offers single-tenant Docker container configurations and AWS EC2 / GCP / Azure ARM templates for total data isolation and SOC2 Type II compliance.'
              },
              {
                q: 'What model export formats are supported?',
                a: 'Trained models can be exported in 1-click as ONNX runtime binaries, standalone Python ZIP packages with inference scripts, or pre-built Docker containers.'
              }
            ].map((faq, idx) => (
              <div key={idx} className={`rounded-xl border transition-all ${bgCard}`}>
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full p-5 text-left font-bold text-sm flex items-center justify-between gap-4"
                >
                  <span className={textTitle}>{faq.q}</span>
                  <ChevronDown className={`w-4 h-4 text-[#16A34A] transition-transform ${openFaq === idx ? 'rotate-180' : ''}`} />
                </button>
                {openFaq === idx && (
                  <div className={`px-5 pb-5 pt-1 border-t text-xs leading-relaxed ${borderClean} ${textMuted}`}>
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ ENTERPRISE SECURITY & DEPLOYMENT STACK ═══════════════════ */}
      <section id="security" className={`py-20 border-b transition-colors ${bgSecondary}`}>
        <div className="max-w-[1280px] mx-auto px-6 space-y-10">
          
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className={`text-3xl font-bold tracking-tight ${textTitle}`}>
              Enterprise Security & Deployment Isolation
            </h2>
            <p className={`text-sm ${textMuted}`}>
              Deploy on private cloud infrastructure or sync automatically via GitHub Actions CI/CD to Hugging Face Spaces.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-xs">
            <div className={`p-6 rounded-xl border space-y-3 ${bgCard}`}>
              <div className="w-8 h-8 rounded bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold"><ShieldCheck className="w-4 h-4" /></div>
              <h4 className={`font-bold text-sm ${textTitle}`}>SOC2 Type II Certified</h4>
              <p className={textMuted}>End-to-end payload encryption at rest and in transit via Fernet AES-256 keys.</p>
            </div>

            <div className={`p-6 rounded-xl border space-y-3 ${bgCard}`}>
              <div className="w-8 h-8 rounded bg-indigo-500/10 text-indigo-500 flex items-center justify-center font-bold"><Lock className="w-4 h-4" /></div>
              <h4 className={`font-bold text-sm ${textTitle}`}>Role-Based Access Control</h4>
              <p className={textMuted}>Workspace roles (Owner, Admin, Analyst, Viewer) with JWT session isolation.</p>
            </div>

            <div className={`p-6 rounded-xl border space-y-3 ${bgCard}`}>
              <div className="w-8 h-8 rounded bg-amber-500/10 text-amber-500 flex items-center justify-center font-bold"><Server className="w-4 h-4" /></div>
              <h4 className={`font-bold text-sm ${textTitle}`}>Private Cloud & Docker</h4>
              <p className={textMuted}>Deploy on AWS EC2, GCP, Azure, or single-tenant Docker container setups.</p>
            </div>

            <div className={`p-6 rounded-xl border space-y-3 ${bgCard}`}>
              <div className="w-8 h-8 rounded bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold"><RefreshCw className="w-4 h-4" /></div>
              <h4 className={`font-bold text-sm ${textTitle}`}>GitHub Actions CI/CD</h4>
              <p className={textMuted}>Automated Hugging Face Spaces deployment pipeline with zero downtime updates.</p>
            </div>
          </div>

        </div>
      </section>

      {/* ═══════════════════ FOOTER ═══════════════════ */}
      <footer id="footer" className={`py-16 border-t transition-colors ${bgMain}`}>
        <div className="max-w-[1280px] mx-auto px-6 space-y-12">
          
          {/* 5-Column Grid Layout */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 text-xs">
            
            <div className="col-span-2 space-y-3">
              <LogoImage isDark={isDark} size={36} showText={true} />
              <p className={`leading-relaxed max-w-sm ${textMuted}`}>
                The Unified Data & AI Lakehouse Platform for Autonomous Business Intelligence.
              </p>
            </div>

            <div>
              <h4 className={`font-bold uppercase tracking-wider mb-3 ${textTitle}`}>Documentation</h4>
              <ul className={`space-y-2 ${textMuted}`}>
                <li><Link to="/dashboard" className="hover:text-[#16A34A] transition-colors">Quickstart</Link></li>
                <li><Link to="/simulator" className="hover:text-[#16A34A] transition-colors">Simulator Guide</Link></li>
                <li><Link to="/ml-predictions" className="hover:text-[#16A34A] transition-colors">AutoML Docs</Link></li>
                <li><Link to="/computer-vision" className="hover:text-[#16A34A] transition-colors">Vision SDK</Link></li>
              </ul>
            </div>

            <div>
              <h4 className={`font-bold uppercase tracking-wider mb-3 ${textTitle}`}>Developers</h4>
              <ul className={`space-y-2 ${textMuted}`}>
                <li><Link to="/developer" className="hover:text-[#16A34A] transition-colors">API Keys</Link></li>
                <li><Link to="/developer" className="hover:text-[#16A34A] transition-colors">REST Reference</Link></li>
                <li><Link to="/developer" className="hover:text-[#16A34A] transition-colors">Python SDK</Link></li>
                <li><Link to="/developer" className="hover:text-[#16A34A] transition-colors">Webhooks</Link></li>
              </ul>
            </div>

            <div>
              <h4 className={`font-bold uppercase tracking-wider mb-3 ${textTitle}`}>Company</h4>
              <ul className={`space-y-2 ${textMuted}`}>
                <li><a href="#" className="hover:text-[#16A34A] transition-colors">About Us</a></li>
                <li><a href="#" className="hover:text-[#16A34A] transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-[#16A34A] transition-colors">Terms of Service</a></li>
                <li><a href="#" className="hover:text-[#16A34A] transition-colors">Security</a></li>
              </ul>
            </div>

          </div>

          {/* Bottom Bar & Status */}
          <div className={`pt-6 border-t flex flex-col sm:flex-row items-center justify-between gap-4 text-xs ${borderClean} ${textMuted}`}>
            <p>© {new Date().getFullYear()} DataVision Enterprise Inc. All rights reserved.</p>

            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#16A34A]" />
              <span className={`font-semibold ${textTitle}`}>All Systems Operational</span>
            </div>
          </div>

        </div>
      </footer>

    </div>
  );
}
