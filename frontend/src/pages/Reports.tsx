import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Download,
  TrendingUp,
  Users,
  ShoppingCart,
  Loader,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { apiService } from '@/services/api';
import { formatCurrency, getCurrencySymbol, detectCurrency } from '@/utils/currency';

interface ReportSection {
  title: string;
  content: string;
}

interface GeneratedReport {
  title: string;
  reportType: string;
  generatedAt: string;
  dataSource: string;
  sections: ReportSection[];
  error?: string;
}

const Reports: React.FC = () => {
  const [report, setReport] = useState<GeneratedReport | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('revenue');
  const [analytics, setAnalytics] = useState<any>(null);

  // Auto-detect currency from analytics data
  const currency = analytics ? detectCurrency(analytics) : 'INR';
  const currencySymbol = getCurrencySymbol(currency);
  
  // Currency Icon Component
  const CurrencyIcon = () => (
    <div className="w-8 h-8 flex items-center justify-center font-bold text-current">
      {currencySymbol}
    </div>
  );

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const response = await apiService.getAnalyticsOverview();
      setAnalytics(response.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const response = await apiService.generateReport(selectedType);
      setReport(response.data);
    } catch (err: any) {
      console.error('Generate report failed:', err);
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    
    const content = `
${report.title}
Generated: ${new Date(report.generatedAt).toLocaleString()}
Data Source: ${report.dataSource}

${report.sections.map(section => `
${section.title}
${'='.repeat(section.title.length)}
${section.content}
`).join('\n')}
    `.trim();

    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${report.reportType}_report_${Date.now()}.txt`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const reportTypes = [
    { 
      value: 'revenue', 
      label: 'Revenue Report', 
      description: 'Revenue analysis from uploaded files',
      icon: CurrencyIcon 
    },
    { 
      value: 'customer', 
      label: 'Customer Report', 
      description: 'Customer insights from uploaded files',
      icon: Users 
    },
    { 
      value: 'product', 
      label: 'Product Report', 
      description: 'Product performance from uploaded files',
      icon: ShoppingCart 
    },
    { 
      value: 'executive', 
      label: 'Executive Summary', 
      description: 'High-level overview from uploaded files',
      icon: TrendingUp 
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-bold text-white mb-2">Business Reports</h1>
        <p className="text-gray-400">Real reports generated from your uploaded files</p>
      </motion.div>

      {/* Key Metrics Summary - REAL DATA */}
      {analytics?.hasData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4"
        >
          {[
            { 
              label: 'Total Revenue', 
              value: formatCurrency(analytics.metrics.totalRevenue, currency), 
              icon: CurrencyIcon, 
              color: 'text-accent-green' 
            },
            { 
              label: 'Customers', 
              value: analytics.metrics.uniqueCustomers.toLocaleString(), 
              icon: Users, 
              color: 'text-primary-400' 
            },
            { 
              label: 'Orders', 
              value: analytics.metrics.totalInvoices.toLocaleString(), 
              icon: ShoppingCart, 
              color: 'text-accent-purple' 
            },
            { 
              label: 'Avg Order', 
              value: formatCurrency(analytics.metrics.averageOrderValue, currency), 
              icon: TrendingUp, 
              color: 'text-accent-orange' 
            },
          ].map((metric, i) => (
            <div key={i} className="glass-card p-4">
              <div className="flex items-center space-x-3">
                <metric.icon className={`w-8 h-8 ${metric.color}`} />
                <div>
                  <div className="text-2xl font-bold text-white">{metric.value}</div>
                  <div className="text-sm text-gray-400">{metric.label}</div>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      )}

      {/* Generate Report Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-8"
      >
        <h2 className="text-2xl font-semibold text-white mb-6">Generate New Report</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {reportTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => setSelectedType(type.value)}
              className={`p-4 rounded-xl transition-all text-left ${
                selectedType === type.value
                  ? 'bg-primary-500/20 border-2 border-primary-500'
                  : 'bg-dark-card border border-dark-border hover:bg-dark-hover'
              }`}
            >
              <type.icon className={`w-6 h-6 mb-2 ${selectedType === type.value ? 'text-primary-400' : 'text-gray-400'}`} />
              <div className={`font-semibold mb-1 ${
                selectedType === type.value ? 'text-white' : 'text-gray-300'
              }`}>
                {type.label}
              </div>
              <div className="text-sm text-gray-400">{type.description}</div>
            </button>
          ))}
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full px-6 py-4 bg-primary-500 hover:bg-primary-600 disabled:bg-gray-600 text-white font-semibold rounded-xl transition-colors flex items-center justify-center space-x-2"
        >
          {generating ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              <span>Generating Report from Real Data...</span>
            </>
          ) : (
            <>
              <FileText className="w-5 h-5" />
              <span>Generate {reportTypes.find(t => t.value === selectedType)?.label}</span>
            </>
          )}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-accent-red/10 border border-accent-red/20 rounded-xl flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-accent-red font-semibold">Error</div>
              <div className="text-gray-300 text-sm">{error}</div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Generated Report Display */}
      {report && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-8"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="w-6 h-6 text-accent-green" />
                <h2 className="text-2xl font-semibold text-white">{report.title}</h2>
              </div>
              <div className="text-sm text-gray-400">
                Generated: {new Date(report.generatedAt).toLocaleString()} | 
                Source: {report.dataSource}
              </div>
            </div>
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-xl text-primary-400 font-medium hover:bg-primary-500/20 transition-colors flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          </div>

          {report.error ? (
            <div className="p-4 bg-accent-red/10 border border-accent-red/20 rounded-xl">
              <div className="text-accent-red font-semibold">{report.error}</div>
              <div className="text-gray-400 text-sm mt-2">Please upload files to generate reports with real data.</div>
            </div>
          ) : (
            <div className="space-y-6">
              {report.sections.map((section, i) => (
                <div key={i} className="border-l-2 border-primary-500 pl-4">
                  <h3 className="text-lg font-semibold text-white mb-2">{section.title}</h3>
                  <pre className="text-gray-300 whitespace-pre-wrap font-mono text-sm">
                    {section.content}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Empty State */}
      {!report && !generating && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-12 text-center"
        >
          <FileText className="w-16 h-16 text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Report Generated Yet</h3>
          <p className="text-gray-400 mb-4">
            Select a report type above and click generate to create a report from your uploaded files.
          </p>
          {!analytics?.hasData && (
            <a
              href="/data-hub"
              className="inline-block px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors"
            >
              Upload Files First
            </a>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Reports;
