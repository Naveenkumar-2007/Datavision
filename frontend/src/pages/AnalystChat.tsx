import React, { useState, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  FileText,
  TrendingUp,
  Network,
  Mic,
  Paperclip,
  X,
  Plus,
  Trash2,
  MessageSquare,
  Pencil,
  Check,
  Copy,
  CheckCheck,
  Sparkles,
  ChevronDown,
  ArrowLeft,
  Settings,
  Menu,
  Database,
  Eye,
  Layers,
  RefreshCw,
  Square,
  Zap,
  Bot,
} from 'lucide-react';
import apiService from '@/services/api';
import { useUserStore } from '@/store/userStore';

// Lazy load PlotlyChart for performance
const PlotlyChart = React.lazy(() => import('@/components/PlotlyChart'));

// ============================================================================
// 🛡️ USER-FRIENDLY ERROR MESSAGE FORMATTER
// Shows nice messages like Claude/ChatGPT instead of raw API errors
// ============================================================================
const formatUserFriendlyError = (error: string | any): string => {
  const errorStr = typeof error === 'string' ? error.toLowerCase() : 
    (error?.message || error?.response?.data?.detail || String(error)).toLowerCase();
  
  // Rate limit / Service busy errors
  if (errorStr.includes('rate') || errorStr.includes('limit') || errorStr.includes('429') || 
      errorStr.includes('quota') || errorStr.includes('too many requests')) {
    return `⏳ **Service Temporarily Busy**

Our AI service is experiencing high demand. Please wait a moment and try again.

💡 **Tips:**
• Wait 30 seconds before retrying
• Try asking a simpler question
• Your data is safe and ready`;
  }
  
  // API Key / Auth errors
  if (errorStr.includes('api_key') || errorStr.includes('unauthorized') || 
      errorStr.includes('authentication') || errorStr.includes('401') || errorStr.includes('invalid key')) {
    return `🔑 **Configuration Required**

The AI service needs to be configured. Please contact your administrator.

_This is a server-side configuration issue._`;
  }
  
  // Connection / Timeout errors
  if (errorStr.includes('timeout') || errorStr.includes('connection') || 
      errorStr.includes('network') || errorStr.includes('fetch') || errorStr.includes('econnrefused')) {
    return `🌐 **Connection Issue**

Unable to reach the AI service. Please check your internet connection and try again.

💡 **Tips:**
• Check your internet connection
• Refresh the page
• Try again in a few moments`;
  }
  
  // Context too large
  if (errorStr.includes('context') || errorStr.includes('too large') || 
      errorStr.includes('token') || errorStr.includes('length') || errorStr.includes('maximum')) {
    return `📏 **Request Too Large**

Your question or data exceeds the model's capacity.

💡 **Tips:**
• Try asking a more specific question
• Break down complex queries into smaller parts
• Focus on specific columns or time periods`;
  }
  
  // Server errors
  if (errorStr.includes('500') || errorStr.includes('502') || errorStr.includes('503') || 
      errorStr.includes('504') || errorStr.includes('internal server')) {
    return `🔧 **Service Maintenance**

Our AI service is temporarily unavailable. We're working on it!

Please try again in a few minutes.`;
  }
  
  // Model not found
  if (errorStr.includes('model') && (errorStr.includes('not found') || errorStr.includes('unavailable'))) {
    return `🤖 **AI Model Unavailable**

The requested AI model is temporarily unavailable. Trying alternative models...

Please try again in a moment.`;
  }
  
  // Generic fallback - don't show raw technical errors
  if (errorStr.includes('error') || errorStr.includes('exception') || errorStr.includes('failed')) {
    return `⚠️ **Something Went Wrong**

I encountered an issue processing your request. Please try again.

💡 **Tips:**
• Rephrase your question
• Try a simpler query
• If the problem persists, refresh the page`;
  }
  
  // If nothing matches, return a clean generic message
  return `⚠️ **Unable to Process Request**

Please try again in a moment. If the issue persists, try refreshing the page.`;
};

// Helper function to format inline text (bold, italic, code)
const formatInlineText = (text: string): string => {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="inline-code-highlight">$1</code>');
};

// Component to render formatted text with inline styles
const InlineFormattedText: React.FC<{ text: string; className?: string }> = ({ text, className = '' }) => {
  const formatted = formatInlineText(text);
  return <span className={className} dangerouslySetInnerHTML={{ __html: formatted }} />;
};

// Image with download/copy buttons
const ChartImage: React.FC<{ src: string; alt: string }> = ({ src, alt }) => {
  const [copied, setCopied] = React.useState(false);

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = src;
    link.download = `chart_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCopy = async () => {
    try {
      if (src.startsWith('data:image')) {
        const response = await fetch(src);
        const blob = await response.blob();
        await navigator.clipboard.write([
          new ClipboardItem({ [blob.type]: blob })
        ]);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy image:', err);
    }
  };

  return (
    <div className="my-4 relative group chart-fade-in">
      <img
        src={src}
        alt={alt}
        className="max-w-full rounded-xl border border-[var(--border-color)] shadow-lg transition-transform duration-300 group-hover:scale-[1.02]"
        style={{ maxHeight: '450px' }}
      />
      <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={handleDownload}
          className="p-2 bg-[var(--bg-card)]/90 hover:bg-green-600 rounded-lg text-white text-xs flex items-center gap-1 backdrop-blur-sm border border-[var(--border-color)]"
          title="Download Chart"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download
        </button>
        <button
          onClick={handleCopy}
          className="p-2 bg-[var(--bg-card)]/90 hover:bg-green-600 rounded-lg text-white text-xs flex items-center gap-1 backdrop-blur-sm border border-[var(--border-color)]"
          title="Copy Chart"
        >
          {copied ? (
            <>
              <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy
            </>
          )}
        </button>
      </div>
      {alt && <p className="text-xs text-gray-500 text-center mt-2">{alt}</p>}
    </div>
  );
};

// Lazy-loaded ForecastChartBlock for rendering prediction charts
const ForecastChartBlock: React.FC<{ payload: Record<string, unknown> }> = ({ payload }) => {
  const PredictionChart = React.lazy(() =>
    import('@/components/PredictionChartRenderer').then(m => ({ default: m.PredictionChartRenderer }))
  );

  return (
    <React.Suspense fallback={
      <div className="animate-pulse bg-[var(--bg-card)] rounded-xl h-64 flex items-center justify-center">
        <span className="text-gray-500">Loading chart...</span>
      </div>
    }>
      <PredictionChart payload={payload as unknown as string} />
    </React.Suspense>
  );
};

// PlotlyChartBlock for rendering interactive Plotly charts
const PlotlyChartBlock: React.FC<{ data: any[]; layout: any }> = ({ data, layout }) => {
  return (
    <React.Suspense fallback={
      <div className="animate-pulse bg-[var(--bg-card)] rounded-xl h-64 flex items-center justify-center">
        <span className="text-gray-500">Loading interactive chart...</span>
      </div>
    }>
      <div className="my-4 p-4 glass-card rounded-xl border border-[var(--border-color)]">
        <PlotlyChart data={data} layout={layout} />
      </div>
    </React.Suspense>
  );
};

// MLChartBlock - Renders matplotlib/seaborn charts from Predict mode (base64 PNG)
const MLChartBlock: React.FC<{
  chart: { type: string; image: string; title?: string }
}> = ({ chart }) => {
  const typeIcons: Record<string, string> = {
    'ml_forecast': '📈',
    'ml_importance': '🔑',
    'ml_correlation': '🔗',
    'ml_distribution': '📊',
    'ml_residual': '📉',
    'ml_summary': '🤖'
  };

  const icon = typeIcons[chart.type] || '📊';

  if (!chart.image) return null;

  return (
    <div className="my-4 p-4 glass-card rounded-xl border border-[var(--border-color)] shadow-lg">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">{icon}</span>
        <span className="text-sm font-medium text-green-400">
          {chart.title || 'ML Visualization'}
        </span>
        <span className="text-xs text-gray-500 ml-auto">
          Powered by scikit-learn + matplotlib
        </span>
      </div>
      <ChartImage src={chart.image} alt={chart.title || 'ML Chart'} />
    </div>
  );
};

// MLChartsContainer - Renders multiple ML charts from response
const MLChartsContainer: React.FC<{
  charts: Array<{ type: string; image: string; title?: string }>
}> = ({ charts }) => {
  if (!charts || charts.length === 0) return null;

  return (
    <div className="space-y-4 mt-4">
      <div className="flex items-center gap-2 text-sm text-green-400">
        <Zap className="w-4 h-4" />
        <span>ML Visualizations • Real scikit-learn analysis</span>
      </div>
      {charts.map((chart, index) => (
        <MLChartBlock key={index} chart={chart} />
      ))}
    </div>
  );
};

// Typewriter Animation Component - ChatGPT-like word-by-word reveal
const TypewriterText: React.FC<{
  content: string;
  isNew?: boolean;
  onComplete?: () => void;
}> = ({ content, isNew = false, onComplete }) => {
  const [displayedContent, setDisplayedContent] = useState(isNew ? '' : content);
  const [isComplete, setIsComplete] = useState(!isNew);
  const hasAnimatedRef = useRef(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const onCompleteRef = useRef(onComplete);

  // Keep onComplete ref updated without causing re-renders
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // If not a new message OR already animated, show full content immediately
    if (!isNew || hasAnimatedRef.current) {
      setDisplayedContent(content);
      setIsComplete(true);
      return;
    }

    // Mark as animating
    hasAnimatedRef.current = true;

    // Reset for new content
    setDisplayedContent('');
    setIsComplete(false);

    // Split content into words for word-by-word animation
    const words = content.split(/(\s+)/);
    let currentIndex = 0;

    intervalRef.current = setInterval(() => {
      if (currentIndex < words.length) {
        // Add 4 words at a time for faster animation
        const nextIndex = Math.min(currentIndex + 4, words.length);
        const wordsToAdd = words.slice(currentIndex, nextIndex).join('');
        setDisplayedContent(prev => prev + wordsToAdd);
        currentIndex = nextIndex;
      } else {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        setIsComplete(true);
        onCompleteRef.current?.();
      }
    }, 25); // 25ms per chunk for smooth animation

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [content, isNew]); // Removed onComplete from deps - using ref instead

  return (
    <>
      <FormattedMessage content={displayedContent} />
      {!isComplete && <span className="typing-cursor"></span>}
    </>
  );
};

// Component to format markdown-like responses
const FormattedMessage: React.FC<{ content: string }> = ({ content }) => {
  const formatContent = (text: string) => {
    let normalizedText = text.replace(/\r\n/g, '\n');

    // PRE-PROCESS: Compact any pretty-printed JSON in chart blocks
    // This fixes the issue where JSON gets split across paragraphs
    normalizedText = normalizedText.replace(
      /```plotly_chart\s*([\s\S]*?)```/gi,
      (match, jsonContent) => {
        try {
          // Try to parse and re-stringify as compact JSON
          const parsed = JSON.parse(jsonContent.trim());
          return '```plotly_chart\n' + JSON.stringify(parsed) + '\n```';
        } catch (e) {
          // If parsing fails, try to compact manually (remove newlines/spaces in JSON)
          const compacted = jsonContent.replace(/\n\s*/g, '').replace(/\s{2,}/g, ' ').trim();
          return '```plotly_chart\n' + compacted + '\n```';
        }
      }
    );

    // Also handle JSON blocks that might have "type":"plotly"
    normalizedText = normalizedText.replace(
      /(\{[^{}]*"type"\s*:\s*"plotly"[^{}]*"data"[\s\S]*?"layout"[\s\S]*?\}(?:\s*\})*)/gi,
      (match) => {
        try {
          // Find complete JSON by brace matching
          let braceCount = 0;
          let startIdx = match.indexOf('{');
          let endIdx = startIdx;
          for (let i = startIdx; i < match.length; i++) {
            if (match[i] === '{') braceCount++;
            if (match[i] === '}') braceCount--;
            if (braceCount === 0) {
              endIdx = i + 1;
              break;
            }
          }
          const jsonStr = match.substring(startIdx, endIdx);
          const parsed = JSON.parse(jsonStr);
          return '```plotly_chart\n' + JSON.stringify(parsed) + '\n```';
        } catch (e) {
          return match;
        }
      }
    );

    const blocks: string[] = [];
    let currentBlock = '';
    let insideCodeBlock = false;
    const lines = normalizedText.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const isEmptyLine = line.trim() === '';

      // Track if we're inside a code block (``` markers)
      if (line.trim().startsWith('```')) {
        insideCodeBlock = !insideCodeBlock;
      }

      // Don't split inside code blocks - keep them together
      if (insideCodeBlock) {
        currentBlock += (currentBlock ? '\n' : '') + line;
      } else if (isEmptyLine && currentBlock.trim()) {
        blocks.push(currentBlock.trim());
        currentBlock = '';
      } else {
        currentBlock += (currentBlock ? '\n' : '') + line;
      }
    }
    if (currentBlock.trim()) {
      blocks.push(currentBlock.trim());
    }

    return blocks.map((para, idx) => {
      if (!para.trim()) return null;

      // Headers
      if (para.startsWith('###')) {
        const headerText = para.replace(/^###\s*/, '');
        return <h3 key={idx} className="text-base font-semibold text-white mt-4 mb-2"><InlineFormattedText text={headerText} /></h3>;
      }
      if (para.startsWith('##')) {
        const headerText = para.replace(/^##\s*/, '');
        return <h2 key={idx} className="text-lg font-semibold text-white mt-5 mb-2"><InlineFormattedText text={headerText} /></h2>;
      }
      if (para.startsWith('#')) {
        const headerText = para.replace(/^#\s*/, '');
        return <h1 key={idx} className="text-xl font-bold text-white mt-5 mb-3"><InlineFormattedText text={headerText} /></h1>;
      }

      // Code blocks - special handling for forecast_chart
      // Handle BOTH proper (```) and malformed (``) backticks
      const isForecastChartBlock = /^`{2,3}\s*forecast_chart/i.test(para);
      const hasChartTypeJson = para.includes('"chart_type"') && para.includes('"forecast');

      if (para.startsWith('```') || para.startsWith('``') || isForecastChartBlock || hasChartTypeJson) {
        // Check if it's a forecast chart - handle variations with whitespace and malformed backticks
        const isForecastChart = /^`{2,3}\s*forecast_chart/i.test(para) || hasChartTypeJson;

        if (isForecastChart) {
          // Extract JSON with improved regex that handles both ``` and `` backticks
          let chartJson = '';

          // Try triple backticks first
          let match = para.match(/^`{2,3}\s*forecast_chart\s*([\s\S]*?)`{2,3}\s*$/);
          if (match) {
            chartJson = match[1].trim();
          } else {
            // Fallback: try to find JSON object directly
            const jsonMatch = para.match(/\{[\s\S]*"chart_type"[\s\S]*\}/);
            if (jsonMatch) {
              chartJson = jsonMatch[0].trim();
            }
          }

          // Skip if empty
          if (!chartJson) {
            // Check if the paragraph IS the JSON (no backticks at all)
            if (para.trim().startsWith('{') && para.includes('"chart_type"')) {
              chartJson = para.trim();
            }
          }

          if (chartJson) {
            try {
              const chartPayload = JSON.parse(chartJson);

              // Validate it has required chart properties
              if (chartPayload && chartPayload.chart_type) {
                return (
                  <div key={idx} className="my-4 animate-fade-in">
                    <ForecastChartBlock payload={chartPayload} />
                  </div>
                );
              }
            } catch (e) {
              console.error('Chart JSON parse error:', e, 'JSON:', chartJson.substring(0, 200));
              // Show user-friendly error instead of raw JSON
              return (
                <div key={idx} className="my-3 p-4 bg-red-900/20 border border-red-500/50 rounded-xl">
                  <p className="text-red-400 text-sm">⚠️ Chart rendering failed. The data is available but couldn't be visualized.</p>
                </div>
              );
            }
          }
        }

        // Check if it's a Plotly chart - improved detection
        const isPlotlyChart = /^`{2,3}\s*plotly_chart/i.test(para) || para.includes('"type":"plotly"') || (para.includes('"data"') && para.includes('"layout"'));
        if (isPlotlyChart) {
          console.log('[CHART DEBUG] Detected plotly_chart block:', para.substring(0, 100));

          // Try multiple patterns to extract JSON - BRACE COUNTING IS MOST RELIABLE
          let chartJson = '';

          // PATTERN 1 (PRIMARY): Use brace-counting for complete JSON extraction
          // This is the most reliable method for nested JSON
          if (para.includes('{') && (para.includes('"data"') || para.includes('"type"'))) {
            const startIdx = para.indexOf('{');
            if (startIdx !== -1) {
              let braceCount = 0;
              let endIdx = para.length;
              for (let i = startIdx; i < para.length; i++) {
                if (para[i] === '{') braceCount++;
                if (para[i] === '}') braceCount--;
                if (braceCount === 0) {
                  endIdx = i + 1;
                  break;
                }
              }
              chartJson = para.substring(startIdx, endIdx);
              console.log('[CHART] Brace-counting extracted', chartJson.length, 'chars');
            }
          }

          // PATTERN 2 (FALLBACK): Regex for plotly_chart code block
          if (!chartJson) {
            const match = para.match(/`{2,3}\s*plotly_chart\s*\n?([\s\S]+?)\n?`{2,3}/);
            if (match) {
              chartJson = match[1].trim();
              console.log('[CHART] Regex extracted', chartJson.length, 'chars');
            }
          }

          console.log('[CHART DEBUG] Extracted JSON length:', chartJson.length, 'First 100 chars:', chartJson.substring(0, 100));

          if (chartJson) {
            try {
              const plotlyData = JSON.parse(chartJson);
              console.log('[CHART DEBUG] Parsed plotly data:', {
                hasData: !!plotlyData.data,
                hasLayout: !!plotlyData.layout,
                chartType: plotlyData.chart_type,
                dataLength: Array.isArray(plotlyData.data) ? plotlyData.data.length : 0
              });

              if (plotlyData && plotlyData.data && plotlyData.layout) {
                return (
                  <div key={idx} className="my-4 animate-fade-in">
                    <PlotlyChartBlock data={plotlyData.data} layout={plotlyData.layout} />
                  </div>
                );
              } else {
                console.error('[CHART DEBUG] Missing data or layout:', {
                  hasData: !!plotlyData.data,
                  hasLayout: !!plotlyData.layout,
                  keys: Object.keys(plotlyData)
                });
              }
            } catch (e) {
              console.error('Plotly chart parse error:', e, 'JSON sample:', chartJson.substring(0, 200));
              return (
                <div key={idx} className="my-3 p-4 bg-red-500/10 border border-red-500/50 rounded-xl">
                  <p className="text-red-400 text-sm">⚠️ Interactive chart rendering failed. Check console for details.</p>
                </div>
              );
            }
          }
        }

        // Regular code block
        const codeContent = para.replace(/^```\w*\n?/, '').replace(/```$/, '');
        return (
          <pre key={idx} className="my-3 p-4 glass-panel rounded-xl overflow-x-auto border border-[var(--border-color)]">
            <code className="text-sm font-mono" style={{ color: 'var(--text-secondary)' }}>{codeContent}</code>
          </pre>
        );
      }

      // Images (base64 charts)
      const imageMatch = para.match(/!\[([^\]]*)\]\(([^)]+)\)/);
      if (imageMatch) {
        return <ChartImage key={idx} alt={imageMatch[1]} src={imageMatch[2]} />;
      }

      // Tables
      const tableLines = para.split('\n').filter(l => l.trim().startsWith('|') || l.includes('|'));
      if (tableLines.length >= 2) {
        const isSeparatorLine = (line: string) => /^[\s|:\-]+$/.test(line.replace(/\|/g, ''));
        const hasSeparator = tableLines.length > 1 && isSeparatorLine(tableLines[1]);

        const headers = tableLines[0].split('|').map(h => h.trim()).filter(h => h);
        const dataStartIndex = hasSeparator ? 2 : 1;
        const rows = tableLines.slice(dataStartIndex)
          .filter(row => !isSeparatorLine(row))
          .map(row => row.split('|').map(cell => cell.trim()).filter(cell => cell))
          .filter(row => row.length > 0);

        if (headers.length > 0 && rows.length > 0) {
          return (
            <div key={idx} className="my-4 overflow-x-auto rounded-xl border border-dark-border animate-fade-in">
              <table className="min-w-full">
                <thead className="bg-[var(--bg-secondary)]/50">
                  <tr>
                    {headers.map((header, i) => (
                      <th key={i} className="px-4 py-3 text-left text-sm font-semibold border-b border-[var(--border-color)]" style={{ color: 'var(--text-primary)' }}>
                        <InlineFormattedText text={header} />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-color)]">
                  {rows.map((row, i) => (
                    <tr key={i} className="hover:bg-[var(--bg-hover)]/50 transition-colors">
                      {row.map((cell, j) => (
                        <td key={j} className="px-4 py-3 text-sm" style={{ color: 'var(--text-secondary)' }}>
                          <InlineFormattedText text={cell} />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
      }

      // Lists
      const paraLines = para.split('\n');
      const bulletLines = paraLines.filter(line => line.trim().match(/^[-•*]\s/) || line.trim().match(/^[•●]\s?/));
      const numberedLines = paraLines.filter(line => line.trim().match(/^\d+[\.\\)]\s/));

      if (bulletLines.length > 0 && bulletLines.length >= paraLines.length * 0.4) {
        return (
          <ul key={idx} className="space-y-2 my-3">
            {paraLines.map((line, i) => {
              const cleanLine = line.trim();
              if (cleanLine.match(/^[-•*●]\s?/) || cleanLine.match(/^[•●]/)) {
                const text = cleanLine.replace(/^[-•*●]\s*/, '');
                return (
                  <li key={i} className="flex items-start gap-2 text-gray-300">
                    <span className="text-green-400 mt-0.5">•</span>
                    <span><InlineFormattedText text={text} /></span>
                  </li>
                );
              }
              return cleanLine ? <p key={i} className="text-gray-300 ml-5"><InlineFormattedText text={cleanLine} /></p> : null;
            })}
          </ul>
        );
      }

      if (numberedLines.length > 0 && numberedLines.length >= paraLines.length * 0.4) {
        return (
          <ol key={idx} className="space-y-2 my-3">
            {paraLines.map((line, i) => {
              const cleanLine = line.trim();
              const match = cleanLine.match(/^(\d+)[\.\\)]\s*(.*)$/);
              if (match) {
                return (
                  <li key={i} className="flex items-start gap-3 text-gray-300">
                    <span className="text-green-400 font-semibold min-w-[1.5rem]">{match[1]}.</span>
                    <span><InlineFormattedText text={match[2]} /></span>
                  </li>
                );
              }
              return cleanLine ? <p key={i} className="text-gray-300 ml-7"><InlineFormattedText text={cleanLine} /></p> : null;
            })}
          </ol>
        );
      }

      // Regular paragraph
      const formattedHtml = formatInlineText(para).replace(/\n/g, '<br/>');
      return (
        <p key={idx} className="mb-3 text-gray-300 leading-relaxed" dangerouslySetInnerHTML={{ __html: formattedHtml }} />
      );
    });
  };

  return <div className="space-y-1">{formatContent(content)}</div>;
};

// Animated Logo for AI Assistant - Uses actual DataVision logo with subtle animation
const AnimatedBotIcon: React.FC<{ size?: number }> = ({ size = 28 }) => (
  <div
    className="relative flex items-center justify-center flex-shrink-0"
    style={{ width: size, height: size, minWidth: size, minHeight: size }}
  >
    <img
      src="/datavision_icon_v3.png"
      alt="DataVision"
      className="w-full h-full object-contain"
      style={{
        animation: 'pulse-glow 2s ease-in-out infinite',
      }}
    />
    <style>{`
      @keyframes pulse-glow {
        0%, 100% { 
          filter: drop-shadow(0 0 2px rgba(20, 184, 166, 0.4));
          opacity: 1;
        }
        50% { 
          filter: drop-shadow(0 0 6px rgba(20, 184, 166, 0.5));
          opacity: 0.9;
        }
      }
    `}</style>
  </div>
);

// Mode-specific thinking messages (Clean & Simple)
const getModeThinkingText = (modeId: string): string => {
  const thinkingTexts: Record<string, string> = {
    'analyst': 'Analyzing data...',
    'deep': 'Thinking deeply...',
    'vision': 'Analyzing image...',
    'predict': 'Running prediction...',
    'agent': 'Taking action...',
  };
  return thinkingTexts[modeId] || 'Processing...';
};

// Typing Indicator - ChatGPT Style with mode-specific thinking
const TypingIndicator: React.FC<{ mode?: string }> = ({ mode = 'rag' }) => (
  <div className="flex items-start gap-3 max-w-3xl message-slide-up">
    <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
      <AnimatedBotIcon size={24} />
    </div>
    <div className="flex flex-col gap-1 py-2">
      <div className="flex items-center gap-2">
        <div className="streaming-indicator flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-400"></span>
          <span className="w-2 h-2 rounded-full bg-green-400"></span>
          <span className="w-2 h-2 rounded-full bg-green-400"></span>
        </div>
        <span className="text-sm text-gray-400 italic">{getModeThinkingText(mode)}</span>
      </div>
    </div>
  </div>
);

// ChatGPT-Style Welcome Screen with Centered Input (includes Mode & MCP controls)
interface WelcomeScreenProps {
  onSuggestionClick: (text: string) => void;
  input: string;
  setInput: (val: string) => void;
  onSend: () => void;
  isLoading: boolean;
  onFileClick: () => void;
  currentMode: { id: string; label: string; icon: any };
  onModeClick: () => void;
  onMcpClick: () => void;
  mcpCount: { active: number; total: number };
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onSuggestionClick,
  input,
  setInput,
  onSend,
  isLoading,
  onFileClick,
  currentMode,
  onModeClick,
  onMcpClick,
  mcpCount
}) => {
  const suggestions = [
    { icon: TrendingUp, text: "Analyze trends in my data" },
    { icon: FileText, text: "Summarize my uploaded data" },
    { icon: Sparkles, text: "What insights can you find?" },
    { icon: Network, text: "Find patterns and correlations" },
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      {/* Logo */}
      <div className="w-14 h-14 mb-4">
        <img src="/logo.png" alt="DataVision" className="w-full h-full object-contain" />
      </div>

      {/* Title - ChatGPT style */}
      <h1 className="text-2xl md:text-3xl font-semibold text-white mb-8 text-center">
        How can I help you today?
      </h1>

      {/* Centered Search Box - ChatGPT Style with Mode & MCP */}
      <div className="w-full max-w-3xl mb-10">
        <div className="relative flex items-center glass-input rounded-2xl transition-colors">
          {/* MCP Button */}
          <button
            onClick={onMcpClick}
            className="p-3 text-gray-400 hover:text-gray-200 transition-colors relative"
            title="MCP Servers"
          >
            <Database className="w-5 h-5" />
            <span className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ${mcpCount.active === mcpCount.total ? 'bg-green-500' : 'bg-yellow-500'}`} />
          </button>

          {/* File Attach Button */}
          <button
            onClick={onFileClick}
            className="p-3 text-gray-400 hover:text-gray-200 transition-colors"
            title="Attach file"
          >
            <Paperclip className="w-5 h-5" />
          </button>

          {/* Input Field */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend(); } }}
            placeholder="Ask anything about your data..."
            className="flex-1 bg-transparent text-white placeholder-gray-500 py-4 px-2 outline-none text-base"
          />

          {/* Mode Selector Button */}
          <button
            onClick={onModeClick}
            className="flex items-center gap-1.5 px-3 py-2 bg-[var(--bg-hover)] hover:bg-[var(--bg-secondary)] rounded-lg transition-colors text-sm font-medium whitespace-nowrap mr-1"
            style={{ color: 'var(--text-secondary)' }}
          >
            {currentMode.label}
            <ChevronDown className="w-4 h-4" />
          </button>

          {/* Send Button */}
          <button
            onClick={onSend}
            disabled={!input.trim() || isLoading}
            className={`m-2 p-3 rounded-xl transition-all ${input.trim() && !isLoading
              ? 'bg-green-500 hover:bg-green-600 text-white'
              : 'bg-[var(--bg-hover)] text-gray-400 cursor-not-allowed'
              }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Suggestion Cards - 2x2 Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full">
        {suggestions.map((suggestion, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick(suggestion.text)}
            className="flex items-center gap-3 p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)]/30 hover:bg-[var(--bg-hover)] hover:border-gray-500 transition-all duration-200 text-left group"
          >
            <div className="p-2 rounded-lg bg-green-500/10 group-hover:bg-green-500/20 transition-colors">
              <suggestion.icon className="w-5 h-5 text-green-400" />
            </div>
            <span className="text-sm transition-colors group-hover:text-[var(--text-primary)]" style={{ color: 'var(--text-secondary)' }}>
              {suggestion.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

const AnalystChat: React.FC = () => {
  const navigate = useNavigate();
  const {
    conversations,
    currentConversationId,
    createConversation,
    deleteConversation,
    selectConversation,
    addMessageToConversation,
    updateConversationMessages,
    getCurrentConversation,
    clearAllChats,
  } = useUserStore();

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<string>('analyst');
  const [isRecording, setIsRecording] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [messageImages, setMessageImages] = useState<Record<string, string>>({});
  const [modeDropdownOpen, setModeDropdownOpen] = useState(false);
  const [animatingMessageId, setAnimatingMessageId] = useState<string | null>(null); // Track which message is animating
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mcpDropdownOpen, setMcpDropdownOpen] = useState(false);
  const [plusMenuOpen, setPlusMenuOpen] = useState(false); // Plus menu state
  // 🏆 8 Powerful MCPs - all enabled by default
  const [enabledMcps, setEnabledMcps] = useState<Record<string, boolean>>({
    'data_analyzer': true,
    'pattern_finder': true,
    'forecaster': true,          // NEW: ML predictions
    'anomaly_detector': true,    // NEW: Outlier detection
    'chart_executor': true,      // NEW: Auto-visualization
    'report_generator': true,
    'insight_extractor': true,
    'comparison_engine': true,
  });

  // MCP execution state for Claude-style animations
  const [mcpExecutionStatus, setMcpExecutionStatus] = useState<{
    isRunning: boolean;
    currentTools: Array<{ name: string; icon: string; status: 'pending' | 'running' | 'success' }>;
    startTime: number | null;
  }>({
    isRunning: false,
    currentTools: [],
    startTime: null,
  });

  // MCP Permission Dialog state (Claude-style Allow/Deny)
  const [mcpPermissionDialog, setMcpPermissionDialog] = useState<{
    isOpen: boolean;
    pendingTools: Array<{ name: string; icon: string; description: string }>;
    pendingMessage: string;
    onAllow: (() => void) | null;
    onDeny: (() => void) | null;
  }>({
    isOpen: false,
    pendingTools: [],
    pendingMessage: '',
    onAllow: null,
    onDeny: null,
  });

  // Streaming state for ChatGPT-like word-by-word responses
  const [useStreaming, setUseStreaming] = useState(false); // Disabled - use reliable non-streaming mode
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Feedback state for thumbs up/down
  const [messageFeedback, setMessageFeedback] = useState<Record<string, 'up' | 'down' | null>>({});

  // Handle stop generation (ChatGPT-style stop button in input area)
  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
  };

  // Handle thumbs up/down feedback
  const handleFeedback = (messageId: string, type: 'up' | 'down') => {
    setMessageFeedback(prev => ({
      ...prev,
      [messageId]: prev[messageId] === type ? null : type
    }));
    // You could also send this to the backend for analytics
    console.log(`Feedback ${type} for message ${messageId}`);
  };

  // 🏆 5 POWERFUL MCPs - Competition-Winning Tools
  // Each MCP is a unique powerhouse that works autonomously
  const mcpServers = [
    {
      id: 'data_analyzer',
      name: '📊 Data Analyzer',
      icon: '📊',
      description: 'Deep data exploration • Schema analysis • Quality checks',
      power: 'Explores any dataset structure autonomously'
    },
    {
      id: 'pattern_finder',
      name: '🔎 Pattern Finder',
      icon: '🔎',
      description: 'Anomaly detection • Trends • Correlations',
      power: 'Discovers hidden patterns you never noticed'
    },
    {
      id: 'forecaster',
      name: '🔮 Forecaster',
      icon: '🔮',
      description: 'ML predictions • Confidence intervals • Trend projection',
      power: 'Predicts future with scikit-learn algorithms'
    },
    {
      id: 'anomaly_detector',
      name: '⚠️ Anomaly Detector',
      icon: '⚠️',
      description: 'Outlier detection • Z-score analysis • Risk alerts',
      power: 'Finds statistical anomalies automatically'
    },
    {
      id: 'chart_executor',
      name: '📈 Chart Generator',
      icon: '📈',
      description: 'Auto-visualization • Intent detection • Dynamic colors',
      power: 'Creates perfect charts from natural language'
    },
    {
      id: 'report_generator',
      name: '📄 Report Generator',
      icon: '📄',
      description: 'Executive summaries • Key metrics • Recommendations',
      power: 'Creates professional reports in seconds'
    },
    {
      id: 'insight_extractor',
      name: '💡 Insight Extractor',
      icon: '💡',
      description: 'Business opportunities • Pareto analysis • Growth potential',
      power: 'Mines the most valuable insights from your data'
    },
    {
      id: 'comparison_engine',
      name: '⚖️ Comparison Engine',
      icon: '⚖️',
      description: 'Category comparison • Segment analysis • Benchmarks',
      power: 'Compares data across any dimension'
    },
  ];

  // Mode definitions - 5 CORE MODES (Clean & Professional)
  // Each mode has a specific purpose
  const modes = [
    // 📊 ANALYST - Default mode, smart data analysis
    {
      id: 'analyst',
      label: '📊 Analyst',
      icon: FileText,
      description: 'Smart data analysis with charts & insights',
      fullDescription: 'Upload data and ask questions - get instant analysis with visualizations',
      features: ['Data Analysis', 'Auto Charts', 'Insights', 'Summaries'],
      badge: null,
      isAI: false,
      category: 'core',
      supportsText: true,
      supportsCharts: true,
      color: 'from-blue-500 to-cyan-500'
    },
    // 🧠 DEEP THINK - Complex reasoning
    {
      id: 'deep',
      label: '🧠 Deep Think',
      icon: Sparkles,
      description: 'Multi-step reasoning for complex questions',
      fullDescription: 'Think deeper - breaks down complex problems step by step',
      features: ['Deep Research', 'Multi-Step', 'Reasoning', 'Analysis'],
      badge: 'Pro',
      isAI: true,
      category: 'core',
      supportsText: true,
      supportsCharts: true,
      color: 'from-purple-500 to-pink-500'
    },
    // 👁️ VISION - Image analysis
    {
      id: 'vision',
      label: '👁️ Vision',
      icon: Eye,
      description: 'Analyze images, charts, documents & screenshots',
      fullDescription: 'Upload any image and ask questions about it',
      features: ['Image Analysis', 'Chart Reading', 'OCR', 'Document Scan'],
      badge: null,
      isAI: false,
      category: 'core',
      supportsText: true,
      supportsCharts: true,
      supportsImages: true,
      color: 'from-green-500 to-emerald-500'
    },
    // 📈 PREDICT - ML forecasting
    {
      id: 'predict',
      label: '📈 Predict',
      icon: TrendingUp,
      description: 'ML predictions, forecasts & trend analysis',
      fullDescription: 'Predict future trends using machine learning',
      features: ['ML Forecasts', 'Trends', 'Predictions', 'Confidence'],
      badge: 'ML',
      isAI: true,
      category: 'core',
      supportsText: true,
      supportsCharts: true,
      color: 'from-amber-500 to-orange-500'
    },
    // 🤖 AGENT - Autonomous AI
    {
      id: 'agent',
      label: '🤖 Agent',
      icon: Bot,
      description: 'Autonomous AI that takes actions on your data',
      fullDescription: 'Let AI plan and execute multi-step data tasks',
      features: ['Auto Actions', 'Multi-Step', 'Tools', 'Planning'],
      badge: 'Pro',
      isAI: true,
      category: 'core',
      supportsText: true,
      supportsCharts: true,
      color: 'from-red-500 to-rose-500'
    },
  ];

  const currentConversation = getCurrentConversation();
  const messages = currentConversation?.messages.map(m => ({
    ...m,
    timestamp: new Date(m.timestamp)
  })) || [];

  useEffect(() => {
    if (!currentConversationId && conversations.length > 0) {
      selectConversation(conversations[0].id);
    }
  }, [currentConversationId, conversations]);

  useEffect(() => {
    if (currentConversation) {
      setMode(currentConversation.mode);

      // Restore images from stored imageData in messages
      const restoredImages: Record<string, string> = {};
      currentConversation.messages.forEach((msg: any) => {
        if (msg.imageData) {
          restoredImages[msg.id] = msg.imageData;
        }
      });
      if (Object.keys(restoredImages).length > 0) {
        setMessageImages(prev => ({ ...prev, ...restoredImages }));
      }
    }
  }, [currentConversation?.id]);

  // Listen for file updates from DataHub - notify user when new files are available
  useEffect(() => {
    const handleFilesUpdated = () => {
      console.log('📁 Files updated in chat context');
      // Add a system notification message to let user know data has been refreshed
      if (currentConversationId) {
        const systemMessage = {
          id: `system_${Date.now()}`,
          role: 'assistant' as const,
          content: '📁 **Data Updated!** New files have been uploaded. Your data context has been refreshed. Feel free to ask questions about your updated dataset.',
          timestamp: new Date().toISOString(),
        };
        addMessageToConversation(currentConversationId, systemMessage);
      }
    };

    window.addEventListener('filesUpdated', handleFilesUpdated);
    return () => window.removeEventListener('filesUpdated', handleFilesUpdated);
  }, [currentConversationId, addMessageToConversation]);

  // =========================================================================
  // CHATGPT-STYLE SCROLL LOGIC
  // =========================================================================

  // Check if user is near the bottom of the chat (within 150px)
  const isNearBottom = (): boolean => {
    const container = chatContainerRef.current;
    if (!container) return true;
    return container.scrollHeight - container.scrollTop - container.clientHeight < 150;
  };

  // Scroll to bottom using anchor element
  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior, block: 'end' });
  };

  // Auto-scroll ONLY when user is near bottom OR when loading (doesn't interrupt reading)
  useEffect(() => {
    if (isNearBottom() || isLoading) {
      // Small delay to ensure DOM has rendered
      setTimeout(() => scrollToBottom('smooth'), 50);
    }
  }, [messages, isLoading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop: (acceptedFiles: File[]) => {
      setAttachedFiles(prev => [...prev, ...acceptedFiles]);
    },
    noClick: true,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'text/plain': ['.txt'],
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
  });

  const removeAttachedFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleVoiceInput = async () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in your browser.');
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;

    recognition.onstart = () => setIsRecording(true);
    recognition.onend = () => setIsRecording(false);

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(prev => prev + ' ' + transcript);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
    };

    recognition.start();
  };

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      // Create preview URL for thumbnail display
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreviewUrl(e.target?.result as string);
      };
      reader.readAsDataURL(file);
      // Claude-style: Keep current mode, don't auto-switch
      setInput(prev => prev || 'What can you see in this image?');
    }
  };

  const handlePaste = (event: React.ClipboardEvent) => {
    const items = event.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.startsWith('image/')) {
        event.preventDefault();
        const blob = item.getAsFile();
        if (blob) {
          const file = new File([blob], `pasted_image_${Date.now()}.png`, { type: blob.type });
          setSelectedImage(file);
          // Create preview URL for thumbnail display
          const reader = new FileReader();
          reader.onload = (e) => {
            setImagePreviewUrl(e.target?.result as string);
          };
          reader.readAsDataURL(file);
          // Claude-style: Keep current mode, don't auto-switch
          setInput(prev => prev || 'What can you see in this image?');
        }
        break;
      }
    }
  };

  // Reusable function to process user message (MCPs, API, Animation)
  const processUserMessage = async (
    messageText: string,
    convId: string,
    visionAttachments: any[] = [],
    filesToCompare?: string[]
  ) => {
    setIsLoading(true);

    try {
      // Check if we should use streaming (for RAG modes without images)
      const canStream = useStreaming && !visionAttachments.length &&
        ['rag', 'hybrid'].includes(mode);

      if (canStream) {
        // STREAMING MODE - Word by word like ChatGPT
        const assistantMsgId = (Date.now() + 1).toString();

        // Create placeholder message that will be updated
        const streamingAssistantMessage = {
          id: assistantMsgId,
          role: 'assistant' as const,
          content: '',
          timestamp: new Date().toISOString(),
          sources: [] as string[],
        };

        addMessageToConversation(convId, streamingAssistantMessage);
        setStreamingMessageId(assistantMsgId);
        setStreamingContent('');

        let fullContent = '';

        // Get model based on mode
        const modelMap: Record<string, string> = {
          'rag': 'deepseek',
          'hybrid': 'deepseek',
          'mistral-7b': 'mistral',
          'llama-70b': 'llama',
        };
        const model = modelMap[mode] || 'deepseek';

        await apiService.streamMessage(
          messageText,
          model,
          // onChunk - update message word by word
          (chunk: string) => {
            fullContent += chunk;
            setStreamingContent(fullContent);

            // Update the message in conversation
            const currentConv = getCurrentConversation();
            if (currentConv) {
              const updatedMessages = currentConv.messages.map(m =>
                m.id === assistantMsgId
                  ? { ...m, content: fullContent }
                  : m
              );
              updateConversationMessages(convId, updatedMessages);
            }
          },
          // onDone
          () => {
            setStreamingMessageId(null);
            setStreamingContent('');
            setIsLoading(false);
          },
          // onError
          (error: string) => {
            console.error('Streaming error:', error);
            const currentConv = getCurrentConversation();
            if (currentConv) {
              // Format error as user-friendly message
              const friendlyError = formatUserFriendlyError(error);
              const updatedMessages = currentConv.messages.map(m =>
                m.id === assistantMsgId
                  ? { ...m, content: fullContent || friendlyError }
                  : m
              );
              updateConversationMessages(convId, updatedMessages);
            }
            setStreamingMessageId(null);
            setIsLoading(false);
          }
        );
      } else {
        // NON-STREAMING MODE - Regular API call with MCP animation
        let mcpsToUse = enabledMcps;

        // Detect which MCPs might be triggered based on query (EXPANDED keyword matching)
        const queryLower = messageText.toLowerCase();
        const potentialTools: Array<{ name: string; icon: string; status: 'pending' | 'running' | 'success'; description: string }> = [];

        // Helper function for partial keyword matching
        const matchesAny = (keywords: string[]) => keywords.some(kw => queryLower.includes(kw));

        // 🏆 DETECT 5 POWERFUL MCPs based on query
        if (enabledMcps.data_analyzer && matchesAny(['analyz', 'explore', 'schema', 'structure', 'columns', 'data type', 'overview', 'describe', 'what data', 'statistics', 'stats'])) {
          potentialTools.push({ name: '🔍 Data Analyzer', icon: '🔍', status: 'pending', description: 'Deep data exploration & schema analysis' });
        }
        if (enabledMcps.pattern_finder && matchesAny(['pattern', 'anomal', 'outlier', 'trend', 'unusual', 'spike', 'drop', 'correlation', 'detect', 'discover', 'hidden'])) {
          potentialTools.push({ name: '🔎 Pattern Finder', icon: '🔎', status: 'pending', description: 'Finds patterns, anomalies & correlations' });
        }
        if (enabledMcps.report_generator && matchesAny(['report', 'summary', 'executive', 'document', 'presentation', 'findings', 'conclusion', 'recommend'])) {
          potentialTools.push({ name: '📄 Report Generator', icon: '📄', status: 'pending', description: 'Creates professional reports' });
        }
        if (enabledMcps.insight_extractor && matchesAny(['insight', 'key', 'important', 'valuable', 'business', 'opportunit', 'risk', 'growth', 'potential', 'learn'])) {
          potentialTools.push({ name: '💡 Insight Extractor', icon: '💡', status: 'pending', description: 'Mines valuable insights from data' });
        }
        if (enabledMcps.comparison_engine && matchesAny(['compare', 'versus', 'vs', 'difference', 'between', 'segment', 'category', 'breakdown', 'by', 'top', 'bottom', 'best', 'worst'])) {
          potentialTools.push({ name: '⚖️ Comparison Engine', icon: '⚖️', status: 'pending', description: 'Compares across dimensions' });
        }

        // Show permission dialog if tools detected
        if (potentialTools.length > 0) {
          // Show Claude-style permission dialog with Allow/Deny
          const toolsToRun = [...potentialTools];

          // Create a promise that resolves when user clicks Allow or Deny
          const userChoice = await new Promise<'allow' | 'deny'>((resolve) => {
            setMcpPermissionDialog({
              isOpen: true,
              pendingTools: toolsToRun.map(t => ({ name: t.name, icon: t.icon, description: t.description })),
              pendingMessage: messageText,
              onAllow: () => {
                setMcpPermissionDialog(prev => ({ ...prev, isOpen: false }));
                resolve('allow');
              },
              onDeny: () => {
                setMcpPermissionDialog(prev => ({ ...prev, isOpen: false }));
                resolve('deny');
              }
            });
          });

          if (userChoice === 'allow') {
            // User allowed - show MCP execution animation
            setMcpExecutionStatus({
              isRunning: true,
              currentTools: toolsToRun.map((t, idx) => ({
                name: t.name,
                icon: t.icon,
                status: idx === 0 ? 'running' : 'pending'
              })),
              startTime: Date.now(),
            });

            // Animate through tools
            let toolIndex = 0;
            const animationInterval = setInterval(() => {
              toolIndex++;
              if (toolIndex < toolsToRun.length) {
                setMcpExecutionStatus(prev => ({
                  ...prev,
                  currentTools: prev.currentTools.map((t, idx) => ({
                    ...t,
                    status: idx < toolIndex ? 'success' : idx === toolIndex ? 'running' : 'pending'
                  }))
                }));
              } else {
                setMcpExecutionStatus(prev => ({
                  ...prev,
                  currentTools: prev.currentTools.map(t => ({ ...t, status: 'success' }))
                }));
                clearInterval(animationInterval);
              }
            }, 400);

            // Wait for animation to show
            await new Promise(resolve => setTimeout(resolve, 300));
          } else {
            // User denied - disable MCPs for this request
            mcpsToUse = {};
          }
        }

        const response = await apiService.sendMessage(
          messageText,
          mode,
          convId,
          filesToCompare && filesToCompare.length > 0 ? filesToCompare : undefined,
          visionAttachments.length > 0 ? visionAttachments : undefined,
          mcpsToUse
        );

        // Clear MCP animation
        setMcpExecutionStatus({ isRunning: false, currentTools: [], startTime: null });

        const responseContent = response.data?.message || response.data?.answer || 'No response received';
        const responseSources = response.data?.sources || [];
        const responseSuggestions = response.data?.suggestions || [];
        const responseConfidence = response.data?.confidence;

        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content: String(responseContent),
          timestamp: new Date().toISOString(),

          sources: Array.isArray(responseSources) ? responseSources.map(s => String(s)) : [],
          // 🏆 Competition-winning features
          suggestions: responseSuggestions,
          confidence: responseConfidence,
          mode: mode,
        };

        addMessageToConversation(convId, assistantMessage);
        setAnimatingMessageId(assistantMessage.id); // Trigger typewriter animation
        setIsLoading(false);
      }
    } catch (error: any) {
      console.error('Error processing message:', error);
      // Format error as user-friendly message
      const rawError = error.response?.data?.detail || error.message || 'Unknown error';
      const friendlyError = formatUserFriendlyError(rawError);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: friendlyError,
        timestamp: new Date().toISOString(),
      };
      addMessageToConversation(convId, errorMessage);
      setIsLoading(false);
      setMcpExecutionStatus({ isRunning: false, currentTools: [], startTime: null });
    }
  };

  const handleSend = async () => {
    const hasContent = input.trim().length > 0 || selectedImage || attachedFiles.length > 0;
    if (!hasContent || isLoading) return;

    let convId = currentConversationId;
    if (!convId) {
      convId = createConversation(mode);
    }

    const userMessage: any = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input.trim(),
      timestamp: new Date().toISOString(),
      imageData: null,
    };

    // If image selected, read as base64 BEFORE adding to conversation
    if (selectedImage) {
      const base64Content = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(selectedImage);
      });

      // Store base64 in message for persistence
      userMessage.imageData = base64Content;
      // Also set in messageImages state for immediate display
      setMessageImages(prev => ({ ...prev, [userMessage.id]: base64Content }));
    }

    addMessageToConversation(convId, userMessage);

    // Scroll to bottom immediately after sending message (ChatGPT behavior)
    setTimeout(() => scrollToBottom('smooth'), 100);

    const messageToSend = input.trim();
    const filesToCompare = attachedFiles.map(f => f.name);

    // Create vision attachments
    let visionAttachments: any[] = [];
    // Use the already-stored imageData from userMessage
    if (userMessage.imageData) {
      visionAttachments.push({
        name: 'uploaded_image',
        type: 'image/png',
        size: 0,
        content: userMessage.imageData
      });
    }

    // Upload files
    if (attachedFiles.length > 0) {
      await apiService.uploadFiles(attachedFiles);
      window.dispatchEvent(new CustomEvent('filesUpdated'));
    }

    // Reset Input
    setInput('');
    setSelectedImage(null);
    setImagePreviewUrl(null);
    setAttachedFiles([]);

    // Process Message
    await processUserMessage(messageToSend, convId, visionAttachments, filesToCompare);
  };

  const handleEditMessage = (messageId: string, content: string) => {
    setEditingMessageId(messageId);
    setEditingContent(content);
  };

  const handleCancelEdit = () => {
    setEditingMessageId(null);
    setEditingContent('');
  };

  const handleSaveAndResend = async (messageId: string) => {
    if (!editingContent.trim() || isLoading) return;

    const messageIndex = messages.findIndex(m => m.id === messageId);
    if (messageIndex === -1) return;

    let convId = currentConversationId || createConversation(mode);

    const messagesToKeep = messages.slice(0, messageIndex).map(m => ({
      ...m,
      timestamp: m.timestamp instanceof Date ? m.timestamp.toISOString() : m.timestamp
    }));

    updateConversationMessages(convId, messagesToKeep);

    const messageToSend = editingContent.trim();

    setEditingMessageId(null);
    setEditingContent('');

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: messageToSend,
      timestamp: new Date().toISOString(),
    };
    addMessageToConversation(convId, userMessage);

    await processUserMessage(messageToSend, convId);
  };

  const handleCopyMessage = async (messageId: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  // Handle export message to PDF/PPTX/Email
  const handleExportMessage = async (content: string, format: 'pdf' | 'pptx' | 'email') => {
    try {
      const response = await fetch('/api/v1/exports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'Business Analyst Report',
          content: content,
          format: format,
          workspace_id: localStorage.getItem('userId') || 'default'
        })
      });

      if (!response.ok) throw new Error('Export failed');

      const data = await response.json();

      // Decode base64 and download
      const binaryString = atob(data.content_base64);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: data.content_type });
      const url = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Export failed:', error);
      alert('Export failed: ' + (error.message || 'Unknown error'));
    }
  };

  // Handle regenerate response - find the previous user message and resend it
  const handleRegenerate = async (messageId: string) => {
    const currentConv = getCurrentConversation();
    if (!currentConv) return;

    // Find the assistant message index
    const msgIndex = currentConv.messages.findIndex(m => m.id === messageId);
    if (msgIndex <= 0) return;

    // Find the previous user message
    let userMsgIndex = msgIndex - 1;
    while (userMsgIndex >= 0 && currentConv.messages[userMsgIndex].role !== 'user') {
      userMsgIndex--;
    }
    if (userMsgIndex < 0) return;

    const userMessage = currentConv.messages[userMsgIndex] as any;

    // Remove the assistant message we're regenerating
    const updatedMessages = currentConv.messages.filter((_, i) => i !== msgIndex);
    updateConversationMessages(currentConv.id, updatedMessages);

    // Prepare vision attachments if image existed
    let visionAttachments: any[] = [];
    if (userMessage.imageData) {
      visionAttachments.push({
        name: 'uploaded_image',
        type: 'image/png',
        size: 0,
        content: userMessage.imageData
      });
    }

    // Call processUserMessage
    await processUserMessage(userMessage.content, currentConv.id, visionAttachments);
  };

  const handleNewChat = () => {
    createConversation(mode);
  };

  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this conversation?')) {
      deleteConversation(id);
    }
  };

  const handleSuggestionClick = (text: string) => {
    setInput(text);
    textareaRef.current?.focus();
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const currentMode = modes.find(m => m.id === mode) || modes[0]; // Safe fallback to analyst

  // Refs for click-outside detection
  const mcpMenuRef = useRef<HTMLDivElement>(null);
  const modeMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (mcpDropdownOpen && mcpMenuRef.current && !mcpMenuRef.current.contains(event.target as Node)) {
        // Check if the click was on the toggle button - if so, let the button handle it
        const target = event.target as Element;
        if (!target.closest('button[title="MCP Servers"]')) {
          setMcpDropdownOpen(false);
        }
      }
      if (modeDropdownOpen && modeMenuRef.current && !modeMenuRef.current.contains(event.target as Node)) {
        // Check if the click was on the toggle button
        const target = event.target as Element;
        if (
          !target.closest('button[title="Analysis Modes"]') &&
          !target.closest('.mode-selector-btn') // Add class to mode buttons to be safe
        ) {
          setModeDropdownOpen(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [mcpDropdownOpen, modeDropdownOpen]);

  return (
    <div className="flex h-screen sm:h-[100dvh] overflow-hidden bg-[var(--bg-primary)] w-full" {...getRootProps()}>
      <input {...getInputProps()} />

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="md:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      {/* Sidebar - Desktop Fixed / Mobile Drawer */}
      <aside className={`
        fixed md:static inset-y-0 left-0 z-50 w-[260px] bg-[var(--bg-card)] border-r border-[var(--border-color)] flex flex-col transition-transform duration-300 transform
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0 md:w-0 md:border-none md:overflow-hidden'}
      `}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-[var(--border-color)] flex items-center justify-between min-w-[256px]">
          <h2 className="text-lg font-semibold text-white">Chat History</h2>
          {/* Mobile close button */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 hover:bg-[var(--bg-hover)] rounded-lg transition-colors"
            title="Close"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 btn-new-chat rounded-xl text-sm font-medium shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto p-2">
          <div className="flex items-center justify-between px-2 py-2 mb-2">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Recent</span>
            {conversations.length > 1 && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (window.confirm('Clear all chat history?')) {
                    clearAllChats();
                  }
                }}
                className="text-xs text-gray-500 hover:text-red-400 transition-colors"
              >
                Clear all
              </button>
            )}
          </div>

          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={`group flex items-center gap-2 p-3 rounded-lg cursor-pointer chat-item ${currentConversationId === conv.id ? 'active' : ''}`}
              >
                <MessageSquare className={`w-4 h-4 flex-shrink-0 ${currentConversationId === conv.id ? 'text-green-400' : 'text-gray-500'}`} />
                <div className="flex-1 min-w-0">
                  <p className={`text-sm truncate ${currentConversationId === conv.id ? 'text-gray-100' : 'text-gray-300'}`}>
                    {conv.title}
                  </p>
                  <p className="text-xs text-gray-500">{formatDate(conv.updatedAt)}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleDeleteConversation(conv.id, e);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded-lg transition-all"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-red-400" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-[var(--border-color)] space-y-1">
          <button
            onClick={() => navigate('/settings')}
            className="flex items-center gap-2 w-full p-2 rounded-lg hover:bg-[var(--bg-hover)] text-gray-400 hover:text-gray-200 transition-colors text-sm"
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
          <button
            onClick={() => navigate('/datahub')}
            className="flex items-center gap-2 w-full p-2 rounded-lg hover:bg-[var(--bg-hover)] text-gray-400 hover:text-gray-200 transition-colors text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to DataHub
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative min-w-0 bg-[var(--bg-primary)]">

        {/* Top Navigation Bar - Now visible on Desktop too */}
        <div className="h-16 border-b border-[var(--border-color)] flex items-center justify-between px-4 bg-[var(--bg-card)]/50 backdrop-blur-sm sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-[var(--bg-hover)] rounded-lg transition-colors text-gray-400 hover:text-white"
              title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
            >
              <Menu className="w-5 h-5" />
            </button>
            {/* Only show title when there are messages */}
            {messages.length > 0 && (
              <div className="flex flex-col">
                <h1 className="text-base font-semibold text-white leading-tight">Analyst Chat</h1>
                <p className="text-xs text-gray-500">
                  {currentMode.label} Mode • {Object.values(enabledMcps).filter(Boolean).length} Active Tools
                </p>
              </div>
            )}
          </div>

          {/* Top Right Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setUseStreaming(!useStreaming)}
              className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${useStreaming ? 'bg-green-500/10 text-green-400' : 'bg-[var(--bg-hover)] text-gray-500'
                }`}
              title="Toggle Streaming"
            >
              <Zap className={`w-3 h-3 ${useStreaming ? 'fill-current' : ''}`} />
              {useStreaming ? 'Fast' : 'Standard'}
            </button>
          </div>
        </div>

        {/* Messages Container - Scrollable with ChatGPT-like experience */}
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto custom-scrollbar">
          <div className={`max-w-3xl mx-auto px-4 ${messages.length === 0 ? 'h-full flex flex-col justify-center py-8' : 'py-6 pb-40'}`}>
            {messages.length === 0 ? (
              <WelcomeScreen
                onSuggestionClick={handleSuggestionClick}
                input={input}
                setInput={setInput}
                onSend={handleSend}
                isLoading={isLoading}
                onFileClick={() => fileInputRef.current?.click()}
                currentMode={currentMode}
                onModeClick={() => setModeDropdownOpen(true)}
                onMcpClick={() => setMcpDropdownOpen(true)}
                mcpCount={{ active: Object.values(enabledMcps).filter(Boolean).length, total: mcpServers.length }}
              />
            ) : (
              <div className="space-y-4">
                {messages.filter(msg => msg && msg.id && msg.content).map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} group`}
                  >
                    {message.role === 'user' ? (
                      // User Message - Right side, contained bubble
                      <div className="flex flex-col items-end max-w-[85%]">
                        {editingMessageId === message.id ? (
                          <div className="w-full">
                            <textarea
                              value={editingContent}
                              onChange={(e) => setEditingContent(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                  e.preventDefault();
                                  if (editingContent.trim()) {
                                    handleSaveAndResend(message.id);
                                  }
                                }
                                if (e.key === 'Escape') {
                                  handleCancelEdit();
                                }
                              }}
                              className="w-full p-4 bg-[var(--bg-card)] border border-accent-primary rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-accent-primary text-gray-100"
                              rows={3}
                              autoFocus
                            />
                            <div className="flex justify-end gap-2 mt-2">
                              <button onClick={handleCancelEdit} className="px-3 py-1.5 text-sm text-gray-400 hover:text-white">
                                Cancel
                              </button>
                              <button
                                onClick={() => handleSaveAndResend(message.id)}
                                disabled={!editingContent.trim()}
                                className="px-4 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg disabled:opacity-50"
                              >
                                Save & Resend
                              </button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="px-4 py-3 chat-bubble-user rounded-2xl rounded-br-md shadow-lg">
                              <p className="whitespace-pre-wrap">{message.content}</p>
                              {messageImages[message.id] && (
                                <img src={messageImages[message.id]} alt="Uploaded" className="mt-3 max-w-full rounded-lg" />
                              )}
                            </div>
                            <div className="flex gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button onClick={() => handleCopyMessage(message.id, message.content)} className="p-1 hover:bg-[var(--bg-hover)] rounded text-gray-500 hover:text-gray-300">
                                {copiedMessageId === message.id ? <CheckCheck className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                              </button>
                              <button onClick={() => handleEditMessage(message.id, message.content)} className="p-1 hover:bg-[var(--bg-hover)] rounded text-gray-500 hover:text-gray-300">
                                <Pencil className="w-4 h-4" />
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      // Bot Message - Left side with logo, full width response
                      <div className="flex items-start gap-3 w-full max-w-full bot-message-animate">
                        {/* DataVision Logo with animation */}
                        <div className="w-8 h-8 flex-shrink-0 mt-1 flex items-center justify-center">
                          <AnimatedBotIcon size={24} />
                        </div>
                        <div className="flex-1">
                          <div className="prose prose-invert max-w-none">
                            <TypewriterText
                              content={message.content || 'No content'}
                              isNew={message.id === animatingMessageId}
                              onComplete={() => setAnimatingMessageId(null)}
                            />

                            {message.sources && Array.isArray(message.sources) && message.sources.length > 0 && (
                              <div className="mt-4 pt-4 border-t border-[var(--border-color)]">
                                <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
                                  <FileText className="w-3 h-3" /> Sources
                                </p>
                                <div className="flex flex-wrap gap-2">
                                  {message.sources.map((source, i) => (
                                    <span key={i} className="px-2 py-1 bg-green-500/20 text-green-300 rounded-lg text-xs">
                                      {String(source)}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                          <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => handleCopyMessage(message.id, message.content)} className="p-1.5 hover:bg-[var(--bg-hover)] rounded-lg text-gray-500 hover:text-gray-300 transition-colors" title="Copy">
                              {copiedMessageId === message.id ? <CheckCheck className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                            </button>
                            <button
                              onClick={() => handleFeedback(message.id, 'up')}
                              className={`p-1.5 hover:bg-[var(--bg-hover)] rounded-lg transition-colors ${messageFeedback[message.id] === 'up'
                                ? 'text-green-400 bg-green-400/10'
                                : 'text-gray-500 hover:text-green-400'
                                }`}
                              title="Good response"
                            >
                              <svg className="w-4 h-4" fill={messageFeedback[message.id] === 'up' ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-1.53a2 2 0 01-1.271-.453L11 19.5a3 3 0 01-1-2.236V13a3 3 0 011-2.236L14 8.5V10z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 10h-.5a2 2 0 00-2 2v6a2 2 0 002 2h.5" />
                              </svg>
                            </button>
                            <button
                              onClick={() => handleFeedback(message.id, 'down')}
                              className={`p-1.5 hover:bg-[var(--bg-hover)] rounded-lg transition-colors ${messageFeedback[message.id] === 'down'
                                ? 'text-red-400 bg-red-400/10'
                                : 'text-gray-500 hover:text-red-400'
                                }`}
                              title="Bad response"
                            >
                              <svg className="w-4 h-4" fill={messageFeedback[message.id] === 'down' ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.737 3h1.53a2 2 0 011.271.453L13 4.5a3 3 0 011 2.236V11a3 3 0 01-1 2.236L10 15.5V14z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 14h.5a2 2 0 002-2V6a2 2 0 00-2-2h-.5" />
                              </svg>
                            </button>
                            <button
                              onClick={() => handleRegenerate(message.id)}
                              className="p-1.5 hover:bg-[var(--bg-hover)] rounded-lg text-gray-500 hover:text-green-400 transition-colors"
                              title="Regenerate response"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                          </div>

                          {/* 🏆 Dynamic Follow-up Suggestions - Competition Winner Feature */}
                          {message.suggestions && message.suggestions.length > 0 && (
                            <div className="mt-4 pt-3 border-t border-[var(--border-color)]/50 animate-fadeIn">
                              <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                                <Sparkles className="w-3 h-3 text-green-400" /> Follow-up questions
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {message.suggestions.map((suggestion: string, i: number) => (
                                  <button
                                    key={i}
                                    onClick={() => {
                                      setInput(suggestion);
                                      const inputEl = document.querySelector('textarea');
                                      inputEl?.focus();
                                    }}
                                    className="px-3 py-1.5 bg-green-50 dark:bg-green-500/10 hover:bg-green-100 dark:hover:bg-green-500/20 border border-green-200 dark:border-green-500/30 rounded-full text-xs text-green-700 dark:text-green-300 transition-colors duration-200"
                                  >
                                    {suggestion}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* 🏆 Confidence Indicator - Shows data grounding quality */}
                          {message.confidence !== undefined && (
                            <div className="mt-3 flex items-center gap-2 text-xs">
                              <span className="text-gray-500">Data Confidence:</span>
                              <div className="flex items-center gap-1">
                                <div className={`w-2 h-2 rounded-full ${message.confidence > 0.8 ? 'bg-green-500' :
                                  message.confidence > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`} />
                                <span className={`${message.confidence > 0.8 ? 'text-green-400' :
                                  message.confidence > 0.5 ? 'text-yellow-400' : 'text-red-400'
                                  }`}>
                                  {message.confidence > 0.8 ? 'High - grounded in data' :
                                    message.confidence > 0.5 ? 'Medium' : 'Low - limited data'}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* 🤖 ML Charts - Matplotlib/Seaborn Visualizations from Predict Mode */}
                          {(message as any).mlCharts && Array.isArray((message as any).mlCharts) && (message as any).mlCharts.length > 0 && (
                            <div className="mt-4 space-y-4">
                              <div className="flex items-center gap-2 text-sm text-green-400 border-t border-[var(--border-color)] pt-3">
                                <Zap className="w-4 h-4" />
                                <span>ML Visualizations • Real scikit-learn analysis</span>
                              </div>
                              {(message as any).mlCharts.map((chart: { type: string; image: string; title?: string }, i: number) => (
                                chart.image && (
                                  <div key={i} className="p-4 bg-gradient-to-br from-[var(--bg-secondary)] to-[var(--bg-primary)] rounded-xl border border-[var(--border-color)] shadow-lg">
                                    <div className="flex items-center gap-2 mb-3">
                                      <span className="text-lg">
                                        {chart.type === 'ml_forecast' ? '📈' :
                                          chart.type === 'ml_importance' ? '🔑' :
                                            chart.type === 'ml_correlation' ? '🔗' :
                                              chart.type === 'ml_distribution' ? '📊' :
                                                chart.type === 'ml_summary' ? '🤖' : '📊'}
                                      </span>
                                      <span className="text-sm font-medium text-green-400">
                                        {chart.title || 'ML Visualization'}
                                      </span>
                                      <span className="text-xs text-gray-500 ml-auto">
                                        scikit-learn + matplotlib
                                      </span>
                                    </div>
                                    <ChartImage src={chart.image} alt={chart.title || 'ML Chart'} />
                                  </div>
                                )
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* MCP Permission Dialog - Claude Style Allow/Deny */}
                {mcpPermissionDialog.isOpen && (
                  <div className="flex items-start gap-3 w-full max-w-full animate-fadeIn">
                    <div className="w-8 h-8 flex-shrink-0 mt-1 flex items-center justify-center">
                      <span className="text-xl">🔧</span>
                    </div>
                    <div className="flex-1 bg-[var(--bg-card)] border border-amber-500/50 rounded-xl p-4 shadow-xl">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></div>
                        <span className="text-sm text-amber-500 font-medium">Permission Required</span>
                      </div>
                      <p className="text-gray-300 dark:text-gray-300 text-sm mb-3">
                        DataVision wants to use the following tools:
                      </p>
                      <div className="space-y-2 mb-4">
                        {mcpPermissionDialog.pendingTools.map((tool) => (
                          <div
                            key={tool.name}
                            className="flex items-center gap-3 px-3 py-2 bg-[var(--bg-hover)]/50 border border-[var(--border-color)] rounded-lg"
                          >
                            <span className="text-lg">{tool.icon}</span>
                            <div className="flex-1">
                              <span className="text-sm font-medium text-gray-200">{tool.name}</span>
                              <p className="text-xs text-gray-500">{tool.description}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => mcpPermissionDialog.onDeny?.()}
                          className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 bg-[var(--bg-hover)] hover:bg-[var(--border-color)] rounded-lg transition-colors border border-transparent hover:border-[var(--border-color)]"
                        >
                          Deny
                        </button>
                        <button
                          onClick={() => mcpPermissionDialog.onAllow?.()}
                          className="px-4 py-2 text-sm text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors shadow-lg shadow-green-900/20"
                        >
                          Allow
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {isLoading && (
                  <div className="space-y-3">
                    {/* MCP Tool Execution Animation - Claude Style */}
                    {mcpExecutionStatus.isRunning && mcpExecutionStatus.currentTools.length > 0 && (
                      <div className="flex items-start gap-3 w-full max-w-full animate-fadeIn">
                        <div className="w-8 h-8 flex-shrink-0 mt-1 flex items-center justify-center">
                          <div className="animate-spin text-xl">⚙️</div>
                        </div>
                        <div className="flex-1 bg-[var(--bg-card)]/80 backdrop-blur-sm border border-accent-primary/30 rounded-xl p-4">
                          <div className="flex items-center gap-2 mb-3">
                            <div className="w-2 h-2 bg-accent-primary rounded-full animate-pulse"></div>
                            <span className="text-sm text-accent-primary font-medium">Running MCP Tools</span>
                          </div>
                          <div className="space-y-2">
                            {mcpExecutionStatus.currentTools.map((tool) => (
                              <div
                                key={tool.name}
                                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-300 ${tool.status === 'running'
                                  ? 'bg-accent-primary/20 border border-accent-primary/40'
                                  : tool.status === 'success'
                                    ? 'bg-green-500/20 border border-green-500/40'
                                    : 'bg-[var(--bg-hover)]/50 border border-[var(--border-color)]'
                                  }`}
                              >
                                <span className={`text-lg ${tool.status === 'running' ? 'animate-bounce' : ''}`}>
                                  {tool.status === 'success' ? '✓' : tool.icon}
                                </span>
                                <span className={`text-sm ${tool.status === 'running' ? 'text-accent-primary' :
                                  tool.status === 'success' ? 'text-green-400' : 'text-gray-400'
                                  }`}>
                                  {tool.name}
                                </span>
                                {tool.status === 'running' && (
                                  <div className="ml-auto flex items-center gap-1">
                                    <div className="w-1 h-1 bg-accent-primary rounded-full animate-ping"></div>
                                    <span className="text-xs text-accent-primary">Running...</span>
                                  </div>
                                )}
                                {tool.status === 'success' && (
                                  <span className="ml-auto text-xs text-green-400">Done</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Regular Typing Indicator with mode-specific text */}
                    <TypingIndicator mode={mode} />
                  </div>
                )}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* ========== GLOBAL DROPDOWNS - Both appear CENTERED below search box ========== */}

        {/* Global MCP Dropdown */}
        <AnimatePresence>
          {mcpDropdownOpen && (
            <motion.div
              ref={mcpMenuRef}
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.2 }}
              className={`fixed z-50 left-4 md:left-[calc(50%-384px)] w-80 max-w-[calc(100vw-2rem)] bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl shadow-2xl overflow-hidden ${messages.length === 0 ? 'top-1/2 mt-16' : 'bottom-28'}`}
            >
              <div className="p-3 border-b border-[var(--border-color)] flex items-center justify-between bg-[var(--bg-secondary)]/50">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">MCP Servers</p>
                <span className="text-xs text-green-400 font-medium">{Object.values(enabledMcps).filter(Boolean).length}/{mcpServers.length} active</span>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {mcpServers.map((mcp) => (
                  <button
                    key={mcp.id}
                    onClick={() => setEnabledMcps(prev => ({ ...prev, [mcp.id]: !prev[mcp.id] }))}
                    className="flex items-center gap-3 w-full p-3 hover:bg-[var(--bg-hover)] transition-colors"
                  >
                    <span className="text-lg">{mcp.icon}</span>
                    <div className="flex-1 text-left">
                      <p className={`text-sm font-medium ${enabledMcps[mcp.id] ? 'text-gray-200' : 'text-gray-500'}`}>{mcp.name}</p>
                      <p className="text-xs text-gray-500 line-clamp-1">{mcp.description}</p>
                    </div>
                    <div className={`w-9 h-5 rounded-full transition-all duration-200 ${enabledMcps[mcp.id] ? 'bg-green-500' : 'bg-gray-700'} flex items-center`}>
                      <div className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform duration-200 ${enabledMcps[mcp.id] ? 'translate-x-4' : 'translate-x-0.5'}`} />
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Global Mode Dropdown */}
        <AnimatePresence>
          {modeDropdownOpen && (
            <motion.div
              ref={modeMenuRef}
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.2 }}
              className={`fixed z-50 right-4 md:right-[calc(50%-384px)] w-80 max-w-[calc(100vw-2rem)] bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl shadow-2xl overflow-hidden max-h-[60vh] overflow-y-auto ${messages.length === 0 ? 'top-1/2 mt-16' : 'bottom-28'}`}
            >
              {/* RAG Modes */}
              <div className="p-2 border-b border-[var(--border-color)] bg-[var(--bg-secondary)]/50">
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-2">📊 Data Modes</span>
              </div>
              {modes.filter(m => !m.isAI).map((m) => (
                <button
                  key={m.id}
                  onClick={() => { setMode(m.id); setModeDropdownOpen(false); }}
                  className={`flex items-center gap-3 w-full p-3 hover:bg-[var(--bg-hover)] transition-colors ${mode === m.id ? 'bg-[var(--bg-hover)]' : ''}`}
                >
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2">
                      <p className={`text-sm font-medium ${mode === m.id ? 'text-white' : 'text-gray-200'}`}>{m.label}</p>
                      {m.badge && (
                        <span className="px-1.5 py-0.5 text-[10px] font-medium bg-green-500/20 text-green-400 rounded">
                          {m.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500">{m.description}</p>
                  </div>
                  {mode === m.id && <Check className="w-4 h-4 text-green-400" />}
                </button>
              ))}

              {/* AI Models Divider */}
              <div className="p-2 border-t border-b border-[var(--border-color)] bg-[var(--bg-secondary)]/50">
                <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider px-2">� AI Models</span>
              </div>
              {modes.filter(m => m.isAI).map((m: any) => (
                <button
                  key={m.id}
                  onClick={() => { setMode(m.id); setModeDropdownOpen(false); }}
                  className={`flex items-center gap-3 w-full p-3 hover:bg-[var(--bg-hover)] transition-colors ${mode === m.id ? 'bg-[var(--bg-hover)]' : ''}`}
                >
                  {m.logo && (
                    <img
                      src={m.logo}
                      alt={m.label}
                      className="w-6 h-6 rounded object-contain bg-white/10 p-0.5"
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  )}
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2">
                      <p className={`text-sm font-medium ${mode === m.id ? 'text-white' : 'text-gray-200'}`}>{m.label}</p>
                      {m.badge && (
                        <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${m.badge === 'New' ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'}`}>
                          {m.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500">{m.description}</p>
                  </div>
                  {mode === m.id && <Check className="w-4 h-4 text-green-400" />}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Global Hidden File Input - Always in DOM for WelcomeScreen and bottom input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf,.xlsx,.xls,.csv"
          onChange={handleImageSelect}
          className="hidden"
        />

        {/* Claude-style Input Bar - Only show when there are messages */}
        {/* Floating Input Area - Fixed at Bottom Center (hidden on empty state) */}
        {
          messages.length > 0 && (
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-dark-bg via-dark-bg to-transparent pt-10 pb-6 px-4 z-20">
              <div className="max-w-3xl mx-auto">
                {/* Attached Files Preview */}
                {attachedFiles.length > 0 && (
                  <div className="mb-3 flex flex-wrap gap-2">
                    {attachedFiles.map((file, index) => (
                      <div key={index} className="flex items-center gap-2 px-3 py-2 bg-dark-card border border-dark-border rounded-lg text-sm">
                        <FileText className="w-4 h-4 text-green-400" />
                        <span className="text-gray-300 truncate max-w-[200px]">{file.name}</span>
                        <button
                          onClick={() => removeAttachedFile(index)} className="text-gray-500 hover:text-red-400">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Image Preview - Shows separately from attached files */}
                {selectedImage && imagePreviewUrl && (
                  <div className="mb-3 flex flex-wrap gap-2">
                    <div className="relative group inline-block">
                      {/* ChatGPT-style Image Preview Thumbnail */}
                      <div className="relative w-32 h-24 rounded-xl overflow-hidden border-2 border-indigo-500/50 shadow-lg bg-dark-card transition-all duration-200 hover:border-indigo-400">
                        <img
                          src={imagePreviewUrl}
                          alt="Preview"
                          className="w-full h-full object-cover"
                        />
                        {/* Overlay with actions */}
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all duration-200 flex items-center justify-center">
                          {/* Edit/View button - top left */}
                          <button
                            className="absolute top-1 left-1 p-1 bg-black/50 hover:bg-black/70 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
                            title="View image"
                          >
                            <Pencil className="w-3 h-3 text-white" />
                          </button>
                        </div>
                        {/* Dismiss button - top right */}
                        <button
                          onClick={() => {
                            setSelectedImage(null);
                            setImagePreviewUrl(null);
                          }}
                          className="absolute top-1 right-1 p-1 bg-gray-800/80 hover:bg-red-600 rounded-md text-white transition-colors"
                          title="Remove image"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Input Bar Container - Premium ChatGPT Style */}
                <div className="glass-input w-full flex items-end gap-2 sm:gap-3 p-3 sm:p-4 rounded-2xl transition-all">

                  {/* Left side buttons - Hidden on mobile, shown on desktop */}
                  <div className="hidden sm:flex items-center gap-2">
                    {/* MCP Servers Toggle - Uses unified dropdown below */}
                    <button
                      onClick={() => setMcpDropdownOpen(!mcpDropdownOpen)}
                      className="p-2 hover:bg-dark-hover rounded-lg transition-colors text-gray-400 hover:text-gray-200 relative"
                      title="MCP Servers"
                    >
                      <Database className="w-5 h-5" />
                      <span className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ${Object.values(enabledMcps).every(Boolean) ? 'bg-green-500' : 'bg-yellow-500'}`} />
                    </button>

                    {/* File Upload */}
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="p-2 hover:bg-dark-hover rounded-lg transition-colors text-gray-400 hover:text-gray-200"
                      title="Attach File"
                    >
                      <Paperclip className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Mobile: Plus button with menu */}
                  <div className="relative sm:hidden">
                    {plusMenuOpen && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={() => setPlusMenuOpen(false)} />
                        <div className="absolute bottom-full mb-2 left-0 w-64 bg-dark-card border border-dark-border rounded-xl shadow-xl overflow-hidden z-50">
                          {/* Upload Files */}
                          <button
                            onClick={() => {
                              fileInputRef.current?.click();
                              setPlusMenuOpen(false);
                            }}
                            className="flex items-center gap-3 w-full p-4 hover:bg-dark-hover transition-colors text-left"
                          >
                            <div className="p-2 bg-blue-500/10 rounded-lg">
                              <Paperclip className="w-5 h-5 text-blue-400" />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-200">Add photos & files</p>
                              <p className="text-xs text-gray-500">Upload documents or images</p>
                            </div>
                          </button>

                          {/* MCPs Submenu */}
                          <button
                            onClick={() => {
                              setMcpDropdownOpen(true);
                              setPlusMenuOpen(false);
                            }}
                            className="flex items-center gap-3 w-full p-4 hover:bg-dark-hover transition-colors text-left border-t border-dark-border"
                          >
                            <div className="p-2 bg-green-500/10 rounded-lg">
                              <Database className="w-5 h-5 text-green-400" />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-200">MCP Servers</p>
                              <p className="text-xs text-gray-500">{Object.values(enabledMcps).filter(Boolean).length}/{mcpServers.length} active</p>
                            </div>
                            <ChevronDown className="w-4 h-4 text-gray-500 -rotate-90" />
                          </button>

                          {/* Modes Submenu */}
                          <button
                            onClick={() => {
                              setModeDropdownOpen(true);
                              setPlusMenuOpen(false);
                            }}
                            className="flex items-center gap-3 w-full p-4 hover:bg-dark-hover transition-colors text-left border-t border-dark-border"
                          >
                            <div className="p-2 bg-purple-500/10 rounded-lg">
                              <Sparkles className="w-5 h-5 text-purple-400" />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-200">AI Modes</p>
                              <p className="text-xs text-gray-500">Current: {currentMode.label}</p>
                            </div>
                            <ChevronDown className="w-4 h-4 text-gray-500 -rotate-90" />
                          </button>
                        </div>
                      </>
                    )}
                    <button
                      onClick={() => setPlusMenuOpen(!plusMenuOpen)}
                      className="p-3 hover:bg-dark-hover rounded-xl transition-colors text-gray-400 hover:text-gray-200"
                      title="More options"
                    >
                      <Plus className="w-6 h-6" />
                    </button>
                  </div>



                  {/* Text Input - Large and prominent */}
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                    onPaste={handlePaste}
                    placeholder="Ask anything..."
                    rows={1}
                    className="flex-1 min-w-0 bg-transparent border-none outline-none resize-none text-base text-gray-100 placeholder-gray-400 py-3 px-3 sm:py-2 sm:px-2 max-h-32 min-h-[44px]"
                    style={{ lineHeight: '1.5' }}
                  />

                  {/* Hidden file input */}

                  {/* Right side: Voice + Mode + Send */}
                  <div className="flex items-center gap-2">
                    {/* Voice Input */}
                    <button
                      onClick={handleVoiceInput}
                      className={`p-3 sm:p-2 rounded-xl sm:rounded-lg transition-colors ${isRecording ? 'bg-red-500 text-white animate-pulse' : 'hover:bg-dark-hover text-gray-400 hover:text-gray-200'}`}
                      title="Voice Input"
                    >
                      <Mic className="w-6 h-6 sm:w-5 sm:h-5" />
                    </button>

                    {/* Mode Selector - Works on mobile and desktop */}
                    <div className="relative">

                      <button
                        onClick={() => setModeDropdownOpen(!modeDropdownOpen)}
                        className="hidden sm:flex items-center gap-1.5 px-3 py-2 bg-dark-hover hover:bg-dark-surface rounded-lg transition-colors text-gray-200 text-sm font-medium whitespace-nowrap"
                      >
                        {currentMode.label}
                        <ChevronDown className={`w-4 h-4 transition-transform ${modeDropdownOpen ? 'rotate-180' : ''}`} />
                      </button>
                    </div>

                    {/* Send/Stop Button - Transforms like ChatGPT */}
                    {isLoading ? (
                      <button
                        onClick={handleStopGeneration}
                        className="p-3 sm:p-2.5 bg-gray-600 hover:bg-red-600 text-white rounded-xl transition-all duration-200"
                        title="Stop generating"
                      >
                        <Square className="w-5 h-5 sm:w-4 sm:h-4 fill-current" />
                      </button>
                    ) : (
                      <button
                        onClick={handleSend}
                        disabled={!input.trim() && !selectedImage && attachedFiles.length === 0}
                        className="chat-send-btn touch-target"
                      >
                        <Send className="w-5 h-5 text-gray-900" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Disclaimer */}
                <p className="text-center text-xs text-gray-500 mt-3">
                  DataVision can make mistakes. Please double-check responses.
                </p>
              </div>
            </div >
          )
        }
      </div >
    </div >
  );
};

export default AnalystChat;
