import React, { useState } from 'react';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import { FileText, Download, FileSpreadsheet, Presentation, CheckCircle2 } from 'lucide-react';

const ReportsTab: React.FC = () => {
  const { isDark } = useUserStore();
  const [reportType, setReportType] = useState('executive_summary');
  const [format, setFormat] = useState('pdf');
  const [generating, setGenerating] = useState(false);
  const [report, setReport] = useState<any>(null);

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await apiService.generateSimulatorReport({
        title: 'Scenario Simulator Report',
        report_type: reportType,
        format,
      });
      setReport(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      {/* Left Config */}
      <div className="lg:col-span-5 space-y-4">
        <div className="rounded-2xl border p-5 space-y-4" style={{ background: cardBg, borderColor: cardBorder }}>
          <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: textPrimary }}>
            <FileText className="w-4 h-4 text-indigo-400" /> Export & Executive Reports
          </h3>

          <div>
            <label className="text-xs font-semibold mb-1.5 block" style={{ color: textMuted }}>Report Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 rounded-xl text-xs border outline-none cursor-pointer"
              style={{ background: cardBg, borderColor: cardBorder, color: textPrimary }}
            >
              <option value="executive_summary">Executive Summary</option>
              <option value="detailed_simulation">Detailed Simulation Analysis</option>
              <option value="scenario_comparison">Scenario Trade-off Comparison</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold mb-1.5 block" style={{ color: textMuted }}>Export Format</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'pdf', label: 'PDF Document', icon: FileText },
                { id: 'excel', label: 'Excel (XLSX)', icon: FileSpreadsheet },
                { id: 'pptx', label: 'PowerPoint', icon: Presentation },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setFormat(item.id)}
                  className={`flex flex-col items-center gap-1.5 py-3 rounded-xl border text-xs font-semibold transition-all ${
                    format === item.id ? 'bg-indigo-500/10 text-indigo-500 border-indigo-500/30' : ''
                  }`}
                  style={format !== item.id ? { borderColor: cardBorder, color: textMuted } : undefined}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="text-[10px]">{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition-all"
          >
            {generating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Generating Document...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" /> Generate Report
              </>
            )}
          </button>
        </div>
      </div>

      {/* Right Result Preview */}
      <div className="lg:col-span-7">
        {report ? (
          <div className="rounded-2xl border p-6 space-y-4" style={{ background: cardBg, borderColor: cardBorder }}>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: textPrimary }}>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Report Ready
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 uppercase">
                {report.format}
              </span>
            </div>

            <div className="p-4 rounded-xl border space-y-2" style={{ borderColor: cardBorder }}>
              <p className="text-sm font-bold" style={{ color: textPrimary }}>{report.title}</p>
              <p className="text-xs" style={{ color: textMuted }}>Generated at: {new Date(report.created_at).toLocaleString()}</p>
            </div>

            <a
              href={report.download_url}
              download
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-all shadow-md shadow-emerald-600/20"
            >
              <Download className="w-4 h-4" /> Download {report.format.toUpperCase()} File
            </a>
          </div>
        ) : (
          <div className="rounded-2xl border p-12 flex flex-col items-center justify-center gap-3 h-full" style={{ background: cardBg, borderColor: cardBorder }}>
            <FileText className="w-10 h-10" style={{ color: textMuted }} />
            <p className="text-sm font-semibold" style={{ color: textPrimary }}>Generate Executive Report</p>
            <p className="text-xs text-center max-w-xs" style={{ color: textMuted }}>
              Select a report type and format to generate a ready-to-share executive report.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportsTab;
