import React, { useState, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import {
  Send,
  FileText,
  TrendingUp,
  Network,
  Image as ImageIcon,
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
  RotateCcw,
  Database,
  Eye,
  Layers,
} from 'lucide-react';
import apiService from '@/services/api';
import { useUserStore } from '@/store/userStore';

// Lazy load PlotlyChart for performance
const PlotlyChart = React.lazy(() => import('@/components/PlotlyChart'));

// Helper function to format inline text (bold, italic, code)
const formatInlineText = (text: string): string => {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="bg-dark-surface px-1.5 py-0.5 rounded text-orange-300 text-sm font-mono">$1</code>');
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
        className="max-w-full rounded-xl border border-dark-border shadow-lg transition-transform duration-300 group-hover:scale-[1.02]"
        style={{ maxHeight: '450px' }}
      />
      <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={handleDownload}
          className="p-2 bg-dark-surface/90 hover:bg-orange-600 rounded-lg text-white text-xs flex items-center gap-1 backdrop-blur-sm border border-dark-border"
          title="Download Chart"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download
        </button>
        <button
          onClick={handleCopy}
          className="p-2 bg-dark-surface/90 hover:bg-orange-600 rounded-lg text-white text-xs flex items-center gap-1 backdrop-blur-sm border border-dark-border"
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
      <div className="animate-pulse bg-dark-surface rounded-xl h-64 flex items-center justify-center">
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
      <div className="animate-pulse bg-dark-surface rounded-xl h-64 flex items-center justify-center">
        <span className="text-gray-500">Loading interactive chart...</span>
      </div>
    }>
      <div className="my-4 p-4 bg-dark-surface/50 rounded-xl border border-dark-border">
        <PlotlyChart data={data} layout={layout} />
      </div>
    </React.Suspense>
  );
};

// Component to format markdown-like responses
const FormattedMessage: React.FC<{ content: string }> = ({ content }) => {
  const formatContent = (text: string) => {
    const normalizedText = text.replace(/\r\n/g, '\n');
    const blocks: string[] = [];
    let currentBlock = '';
    const lines = normalizedText.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const isEmptyLine = line.trim() === '';

      if (isEmptyLine && currentBlock.trim()) {
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
      if (para.startsWith('```')) {
        // Check if it's a forecast chart - handle variations with whitespace
        const isForecastChart = /^```\s*forecast_chart/i.test(para);

        if (isForecastChart) {
          // Extract JSON with improved regex that handles whitespace
          const match = para.match(/^```\s*forecast_chart\s*([\s\S]*?)```\s*$/);

          if (match) {
            const chartJson = match[1].trim();

            // Skip if empty
            if (!chartJson) {
              return null;
            }

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
              console.error('Chart JSON parse error:', e);
              // Show user-friendly error instead of raw JSON
              return (
                <div key={idx} className="my-3 p-4 bg-red-900/20 border border-red-500/50 rounded-xl">
                  <p className="text-red-400 text-sm">⚠️ Chart rendering failed. The data is available but couldn't be visualized.</p>
                </div>
              );
            }
          }
        }

        // Check if it's a Plotly chart
        const isPlotlyChart = /^```\s*plotly_chart/i.test(para);
        if (isPlotlyChart) {
          const match = para.match(/^```\s*plotly_chart\s*([\s\S]*?)```\s*$/);
          if (match) {
            const chartJson = match[1].trim();
            if (!chartJson) return null;

            try {
              const plotlyData = JSON.parse(chartJson);
              if (plotlyData && plotlyData.data && plotlyData.layout) {
                return (
                  <div key={idx} className="my-4 animate-fade-in">
                    <PlotlyChartBlock data={plotlyData.data} layout={plotlyData.layout} />
                  </div>
                );
              }
            } catch (e) {
              console.error('Plotly chart parse error:', e);
              return (
                <div key={idx} className="my-3 p-4 bg-red-900/20 border border-red-500/50 rounded-xl">
                  <p className="text-red-400 text-sm">⚠️ Interactive chart rendering failed.</p>
                </div>
              );
            }
          }
        }

        // Regular code block
        const codeContent = para.replace(/^```\w*\n?/, '').replace(/```$/, '');
        return (
          <pre key={idx} className="my-3 p-4 bg-dark-surface rounded-xl overflow-x-auto border border-dark-border">
            <code className="text-sm text-gray-100 font-mono">{codeContent}</code>
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
                <thead className="bg-dark-surface/50">
                  <tr>
                    {headers.map((header, i) => (
                      <th key={i} className="px-4 py-3 text-left text-sm font-semibold text-white border-b border-dark-border">
                        <InlineFormattedText text={header} />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border">
                  {rows.map((row, i) => (
                    <tr key={i} className="hover:bg-dark-hover/50 transition-colors">
                      {row.map((cell, j) => (
                        <td key={j} className="px-4 py-3 text-sm text-gray-300">
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
                    <span className="text-orange-400 mt-0.5">•</span>
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
                    <span className="text-orange-400 font-semibold min-w-[1.5rem]">{match[1]}.</span>
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

// Premium ChatGPT-style Typing Indicator
const TypingIndicator: React.FC = () => (
  <div className="flex items-start gap-3 max-w-3xl slide-up">
    <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 shadow-lg shadow-orange-500/10">
      <img src="/logo.png" alt="AI" className="w-full h-full object-cover" />
    </div>
    <div className="flex items-center gap-2 px-4 py-3 bg-dark-card rounded-2xl border border-dark-border">
      <div className="typing-dot"></div>
      <div className="typing-dot"></div>
      <div className="typing-dot"></div>
      <span className="text-xs text-gray-500 ml-2">Analyzing...</span>
    </div>
  </div>
);

// Premium Enterprise Welcome Screen
const WelcomeScreen: React.FC<{ onSuggestionClick: (text: string) => void }> = ({ onSuggestionClick }) => {
  const suggestions = [
    { icon: TrendingUp, text: "Analyze revenue trends", description: "Get insights on performance" },
    { icon: FileText, text: "Summarize my reports", description: "Extract key points" },
    { icon: Network, text: "Find data connections", description: "Discover relationships" },
    { icon: Sparkles, text: "Generate insights", description: "AI recommendations" },
  ];

  const quickPrompts = [
    "Why did revenue drop last month?",
    "Compare product performance",
    "Find anomalies in data",
    "Forecast next quarter",
    "Show customer segments",
    "Predict churn risk",
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      {/* Logo with premium animation */}
      <div className="w-20 h-20 rounded-2xl overflow-hidden mb-6 shadow-2xl shadow-orange-500/30 float-animation">
        <img src="/logo.png" alt="AI Analyst" className="w-full h-full object-cover" />
      </div>

      {/* Title with slide-up */}
      <h1 className="text-3xl font-bold text-gray-100 mb-2 slide-up">
        Your AI Business Analyst
      </h1>
      <p className="text-gray-400 mb-8 text-sm slide-up slide-up-delay-1">
        Enterprise Intelligence • ₹40 Lakh/Year Value
      </p>

      {/* Suggestion Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-xl w-full px-4 mb-8 stagger-children">
        {suggestions.map((suggestion, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick(suggestion.text)}
            className="premium-card flex items-start gap-3 p-4 text-left group"
          >
            <div className="p-2 rounded-lg bg-orange-500/10 group-hover:bg-orange-500/20 transition-colors">
              <suggestion.icon className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <p className="font-medium text-gray-200 text-sm group-hover:text-white">{suggestion.text}</p>
              <p className="text-xs text-gray-500 mt-0.5">{suggestion.description}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Quick Prompt Chips */}
      <div className="flex flex-wrap gap-2 justify-center max-w-2xl px-4 slide-up slide-up-delay-3">
        {quickPrompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick(prompt)}
            className="suggestion-chip"
          >
            {prompt}
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
  const [mode, setMode] = useState<string>('rag');
  const [isRecording, setIsRecording] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [messageImages, setMessageImages] = useState<Record<string, string>>({});
  const [modeDropdownOpen, setModeDropdownOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mcpDropdownOpen, setMcpDropdownOpen] = useState(false);
  const [plusMenuOpen, setPlusMenuOpen] = useState(false); // Plus menu state
  const [enabledMcps, setEnabledMcps] = useState<Record<string, boolean>>({
    'data_cleaner': true,
    'vectorizer': true,
    'graph_builder': true,
    'sql_executor': true,
    'vision_ocr': true,
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // MCP server definitions
  const mcpServers = [
    { id: 'data_cleaner', name: 'Data Cleaner', icon: '🧹', description: 'Clean and format data' },
    { id: 'vectorizer', name: 'Vectorizer', icon: '📊', description: 'Text embeddings' },
    { id: 'graph_builder', name: 'Graph Builder', icon: '🔗', description: 'Knowledge graph' },
    { id: 'sql_executor', name: 'SQL Executor', icon: '🗃️', description: 'Database queries' },
    { id: 'vision_ocr', name: 'Vision OCR', icon: '👁️', description: 'Image analysis' },
  ];

  // Mode definitions - RAG modes + AI Models via OpenRouter
  const modes = [
    // RAG Modes
    { id: 'rag', label: 'RAG', icon: FileText, description: 'Document-based retrieval', badge: null, isAI: false },
    { id: 'graphrag', label: 'GraphRAG', icon: Network, description: 'Knowledge graph analysis', badge: null, isAI: false },
    { id: 'hybrid', label: 'Hybrid', icon: Layers, description: 'Best of both worlds', badge: null, isAI: false },
    { id: 'vision', label: 'Vision', icon: Eye, description: 'Image and chart analysis', badge: 'New', isAI: false },
    { id: 'prediction', label: 'Prediction', icon: TrendingUp, description: 'Forecasts and trends', badge: 'New', isAI: false },

    // AI Models - TESTED & VERIFIED WORKING (3 models)
    { id: 'deepseek-chat', label: 'DeepSeek Chat', icon: Sparkles, description: 'PRIMARY • Revenue, KPIs', badge: 'Best', isAI: true, logo: 'https://avatars.githubusercontent.com/u/145310065' },
    { id: 'mistral-7b', label: 'Mistral 7B', icon: Sparkles, description: 'Fast • Decision Analysis', badge: null, isAI: true, logo: 'https://avatars.githubusercontent.com/u/132372032' },
    { id: 'llama-70b', label: 'Llama 70B', icon: Sparkles, description: 'Meta AI • Comprehensive', badge: null, isAI: true, logo: 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Meta-Logo.png' },
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

  // Auto-scroll ONLY when user is near bottom (doesn't interrupt reading)
  useEffect(() => {
    if (isNearBottom()) {
      // Small delay to ensure DOM has rendered
      setTimeout(() => scrollToBottom('smooth'), 50);
    }
  }, [messages]);

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
      setMode('vision');
      setInput(prev => prev || 'Analyze this image');
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
          setMode('vision');
          setInput(prev => prev || 'Analyze this image');
        }
        break;
      }
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
      imageData: null as string | null, // Will be set if image attached
    };

    // If image selected, read as base64 BEFORE adding to conversation
    if (selectedImage) {
      const base64Content = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(selectedImage);
      });

      // Store base64 in message for persistence
      userMessage.imageData = base64Content;
      // Also set in messageImages state for immediate display
      setMessageImages(prev => ({ ...prev, [userMessage.id]: base64Content }));
    }

    addMessageToConversation(convId, userMessage);

    const messageToSend = input.trim();
    const filesToCompare = attachedFiles.map(f => f.name);
    setInput('');
    setSelectedImage(null);
    setAttachedFiles([]);
    setIsLoading(true);

    try {
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

      if (attachedFiles.length > 0) {
        await apiService.uploadFiles(attachedFiles);
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }

      const response = await apiService.sendMessage(
        messageToSend,
        mode,
        convId,
        filesToCompare.length > 0 ? filesToCompare : undefined,
        visionAttachments.length > 0 ? visionAttachments : undefined,
        enabledMcps
      );

      const responseContent = response.data?.message || response.data?.answer || 'No response received';
      const responseSources = response.data?.sources || [];

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: String(responseContent),
        timestamp: new Date().toISOString(),
        sources: Array.isArray(responseSources) ? responseSources.map(s => String(s)) : [],
      };

      addMessageToConversation(convId, assistantMessage);
    } catch (error: any) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      };
      addMessageToConversation(convId, errorMessage);
    } finally {
      setIsLoading(false);
    }
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
    setIsLoading(true);

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: messageToSend,
      timestamp: new Date().toISOString(),
    };
    addMessageToConversation(convId, userMessage);

    try {
      const response = await apiService.sendMessage(
        messageToSend,
        mode,
        convId,
        undefined,
        undefined,
        enabledMcps
      );

      const responseContent = response.data?.message || response.data?.answer || 'No response received';
      const responseSources = response.data?.sources || [];

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: String(responseContent),
        timestamp: new Date().toISOString(),
        sources: Array.isArray(responseSources) ? responseSources.map(s => String(s)) : [],
      };

      addMessageToConversation(convId, assistantMessage);
    } catch (error: any) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      };
      addMessageToConversation(convId, errorMessage);
    } finally {
      setIsLoading(false);
    }
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

  const currentMode = modes.find(m => m.id === mode)!;

  return (
    <div className="flex h-screen bg-dark-bg overflow-hidden" {...getRootProps()}>
      <input {...getInputProps()} />

      {/* Left Sidebar - Chat History */}
      <aside className={`
        w-64 flex-shrink-0 bg-dark-surface border-r border-dark-border flex flex-col transition-all duration-300
        fixed lg:relative inset-y-0 left-0 z-50
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0
      `}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-dark-border flex items-center justify-between min-w-[256px]">
          <h2 className="text-lg font-semibold text-white">Chat History</h2>
          {/* Mobile close button */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 hover:bg-dark-hover rounded-lg transition-colors"
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
                <MessageSquare className={`w-4 h-4 flex-shrink-0 ${currentConversationId === conv.id ? 'text-orange-400' : 'text-gray-500'}`} />
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
        <div className="p-3 border-t border-dark-border space-y-1">
          <button
            onClick={() => navigate('/settings')}
            className="flex items-center gap-2 w-full p-2 rounded-lg hover:bg-dark-hover text-gray-400 hover:text-gray-200 transition-colors text-sm"
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
          <button
            onClick={() => navigate('/overview')}
            className="flex items-center gap-2 w-full p-2 rounded-lg hover:bg-dark-hover text-gray-400 hover:text-gray-200 transition-colors text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </button>
        </div>
      </aside>

      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-dark-bg overflow-hidden">

        {/* Mobile hamburger menu button */}
        <button
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden absolute top-4 left-4 z-30 p-2 bg-dark-card hover:bg-dark-hover border border-dark-border rounded-lg transition-colors"
          title="Open menu"
        >
          <Menu className="w-5 h-5 text-gray-400" />
        </button>

        {/* Messages Container - Scrollable */}
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto scroll-smooth">
          <div className="max-w-3xl mx-auto px-4 py-6">
            {messages.length === 0 ? (
              <WelcomeScreen onSuggestionClick={handleSuggestionClick} />
            ) : (
              <div className="space-y-6">
                {messages.filter(msg => msg && msg.id && msg.content).map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in group`}
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
                              className="w-full p-4 bg-dark-card border border-accent-primary rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-accent-primary text-gray-100"
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
                                className="px-4 py-1.5 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded-lg disabled:opacity-50"
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
                              <button onClick={() => handleCopyMessage(message.id, message.content)} className="p-1 hover:bg-dark-hover rounded text-gray-500 hover:text-gray-300">
                                {copiedMessageId === message.id ? <CheckCheck className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                              </button>
                              <button onClick={() => handleEditMessage(message.id, message.content)} className="p-1 hover:bg-dark-hover rounded text-gray-500 hover:text-gray-300">
                                <Pencil className="w-4 h-4" />
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      // Bot Message - Left side with logo, full width response
                      <div className="flex items-start gap-3 w-full max-w-full">
                        <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 mt-1">
                          <img src="/logo.png" alt="AI" className="w-full h-full object-cover" />
                        </div>
                        <div className="flex-1">
                          <div className="prose prose-invert max-w-none">
                            <FormattedMessage content={message.content || 'No content'} />

                            {message.sources && Array.isArray(message.sources) && message.sources.length > 0 && (
                              <div className="mt-4 pt-4 border-t border-dark-border">
                                <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
                                  <FileText className="w-3 h-3" /> Sources
                                </p>
                                <div className="flex flex-wrap gap-2">
                                  {message.sources.map((source, i) => (
                                    <span key={i} className="px-2 py-1 bg-orange-500/20 text-orange-300 rounded-lg text-xs">
                                      {String(source)}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                          <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => handleCopyMessage(message.id, message.content)} className="p-1.5 hover:bg-dark-hover rounded-lg text-gray-500 hover:text-gray-300" title="Copy">
                              {copiedMessageId === message.id ? <CheckCheck className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                            </button>
                            <button className="p-1.5 hover:bg-dark-hover rounded-lg text-gray-500 hover:text-gray-300" title="Thumbs up">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-1.53a2 2 0 01-1.271-.453L11 19.5a3 3 0 01-1-2.236V13a3 3 0 011-2.236L14 8.5V10z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 10h-.5a2 2 0 00-2 2v6a2 2 0 002 2h.5" />
                              </svg>
                            </button>
                            <button className="p-1.5 hover:bg-dark-hover rounded-lg text-gray-500 hover:text-gray-300" title="Thumbs down">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.737 3h1.53a2 2 0 011.271.453L13 4.5a3 3 0 011 2.236V11a3 3 0 01-1 2.236L10 15.5V14z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 14h.5a2 2 0 002-2V6a2 2 0 00-2-2h-.5" />
                              </svg>
                            </button>
                            <button className="p-1.5 hover:bg-dark-hover rounded-lg text-gray-500 hover:text-gray-300" title="Regenerate">
                              <RotateCcw className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {isLoading && <TypingIndicator />}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Claude-style Input Bar */}
        {/* Claude-style Input Bar - FIXED AT BOTTOM */}
        <div className="flex-shrink-0 border-t border-dark-border bg-dark-bg p-4">
          <div className="max-w-3xl mx-auto">
            {/* Attached Files Preview */}
            {attachedFiles.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2">
                {attachedFiles.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 px-3 py-2 bg-dark-card border border-dark-border rounded-lg text-sm">
                    <FileText className="w-4 h-4 text-orange-400" />
                    <span className="text-gray-300 truncate max-w-[200px]">{file.name}</span>
                    <button
                      onClick={() => removeAttachedFile(index)} className="text-gray-500 hover:text-red-400">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                {selectedImage && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-dark-card border border-dark-border rounded-lg text-sm text-gray-300">
                    <ImageIcon className="w-4 h-4 text-orange-400" />
                    <span className="truncate max-w-[150px]">{selectedImage.name}</span>
                    <button onClick={() => setSelectedImage(null)} className="text-gray-500 hover:text-red-400">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Input Bar Container */}
            <div className="flex items-end gap-2 sm:gap-3 p-2 sm:p-3 bg-dark-card border border-dark-border rounded-2xl sm:rounded-2xl focus-within:border-orange-500/50 transition-colors">

              {/* Left side buttons - Hidden on mobile, shown on desktop */}
              <div className="hidden sm:flex items-center gap-2">
                {/* MCP Servers Toggle */}
                <div className="relative">
                  {mcpDropdownOpen && (
                    <>
                      <div className="fixed inset-0 z-40" onClick={() => setMcpDropdownOpen(false)} />
                      <div className="absolute bottom-full mb-2 left-0 w-64 bg-dark-card border border-dark-border rounded-xl shadow-xl overflow-hidden z-50">
                        <div className="p-2 border-b border-dark-border flex items-center justify-between">
                          <p className="text-xs font-semibold text-gray-500 px-2">MCP SERVERS</p>
                          <span className="text-xs text-orange-400">{Object.values(enabledMcps).filter(Boolean).length}/{mcpServers.length}</span>
                        </div>
                        {mcpServers.map((mcp) => (
                          <button
                            key={mcp.id}
                            onClick={() => setEnabledMcps(prev => ({ ...prev, [mcp.id]: !prev[mcp.id] }))}
                            className="flex items-center gap-3 w-full p-3 hover:bg-dark-hover transition-colors"
                          >
                            <span className="text-lg">{mcp.icon}</span>
                            <div className="flex-1 text-left">
                              <p className={`text-sm ${enabledMcps[mcp.id] ? 'text-gray-200' : 'text-gray-500'}`}>{mcp.name}</p>
                              <p className="text-xs text-gray-500">{mcp.description}</p>
                            </div>
                            <div className={`w-8 h-4 rounded-full transition-colors ${enabledMcps[mcp.id] ? 'bg-orange-500' : 'bg-gray-700'}`}>
                              <div className={`w-3 h-3 rounded-full bg-white mt-0.5 transition-transform ${enabledMcps[mcp.id] ? 'translate-x-4 ml-0.5' : 'translate-x-0.5'}`} />
                            </div>
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                  <button
                    onClick={() => setMcpDropdownOpen(!mcpDropdownOpen)}
                    className="p-2 hover:bg-dark-hover rounded-lg transition-colors text-gray-400 hover:text-gray-200 relative"
                    title="MCP Servers"
                  >
                    <Database className="w-5 h-5" />
                    <span className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ${Object.values(enabledMcps).every(Boolean) ? 'bg-green-500' : 'bg-yellow-500'}`} />
                  </button>
                </div>

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

              {/* MCP Dropdown - Now works on mobile too */}
              {mcpDropdownOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setMcpDropdownOpen(false)} />
                  <div className="fixed bottom-20 left-4 right-4 sm:absolute sm:bottom-full sm:left-0 sm:right-auto sm:mb-2 w-auto sm:w-64 bg-dark-card border border-dark-border rounded-xl shadow-xl overflow-hidden z-50">
                    <div className="p-3 border-b border-dark-border flex items-center justify-between">
                      <p className="text-xs font-semibold text-gray-500">MCP SERVERS</p>
                      <span className="text-xs text-orange-400">{Object.values(enabledMcps).filter(Boolean).length}/{mcpServers.length}</span>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      {mcpServers.map((mcp) => (
                        <button
                          key={mcp.id}
                          onClick={() => setEnabledMcps(prev => ({ ...prev, [mcp.id]: !prev[mcp.id] }))}
                          className="flex items-center gap-3 w-full p-3 hover:bg-dark-hover transition-colors"
                        >
                          <span className="text-lg">{mcp.icon}</span>
                          <div className="flex-1 text-left">
                            <p className={`text-sm ${enabledMcps[mcp.id] ? 'text-gray-200' : 'text-gray-500'}`}>{mcp.name}</p>
                            <p className="text-xs text-gray-500">{mcp.description}</p>
                          </div>
                          <div className={`w-8 h-4 rounded-full transition-colors ${enabledMcps[mcp.id] ? 'bg-orange-500' : 'bg-gray-700'}`}>
                            <div className={`w-3 h-3 rounded-full bg-white mt-0.5 transition-transform ${enabledMcps[mcp.id] ? 'translate-x-4 ml-0.5' : 'translate-x-0.5'}`} />
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

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
              <input ref={fileInputRef} type="file" accept="image/*,.pdf,.xlsx,.xls,.csv" onChange={handleImageSelect} className="hidden" />

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
                  {modeDropdownOpen && (
                    <>
                      <div className="fixed inset-0 z-40" onClick={() => setModeDropdownOpen(false)} />
                      <div className="fixed bottom-20 left-4 right-4 sm:absolute sm:bottom-full sm:left-auto sm:right-0 sm:mb-2 w-auto sm:w-72 bg-dark-card border border-dark-border rounded-xl shadow-xl overflow-hidden z-50 max-h-[70vh] overflow-y-auto">
                        {/* RAG Modes */}
                        <div className="p-2 border-b border-dark-border">
                          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2">RAG Modes</span>
                        </div>
                        {modes.filter(m => !m.isAI).map((m) => (
                          <button
                            key={m.id}
                            onClick={() => { setMode(m.id); setModeDropdownOpen(false); }}
                            className={`flex items-center gap-3 w-full p-3 hover:bg-dark-hover transition-colors ${mode === m.id ? 'bg-dark-hover' : ''}`}
                          >
                            <div className="flex-1 text-left">
                              <div className="flex items-center gap-2">
                                <p className={`text-sm font-medium ${mode === m.id ? 'text-white' : 'text-gray-200'}`}>{m.label}</p>
                                {m.badge && (
                                  <span className="px-1.5 py-0.5 text-[10px] font-medium bg-orange-500/20 text-orange-400 rounded">
                                    {m.badge}
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-gray-500">{m.description}</p>
                            </div>
                            {mode === m.id && <Check className="w-4 h-4 text-orange-400" />}
                          </button>
                        ))}

                        {/* AI Models Divider */}
                        <div className="p-2 border-t border-b border-dark-border bg-dark-surface/50">
                          <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider px-2">🤖 AI Models</span>
                        </div>
                        {modes.filter(m => m.isAI).map((m: any) => (
                          <button
                            key={m.id}
                            onClick={() => { setMode(m.id); setModeDropdownOpen(false); }}
                            className={`flex items-center gap-3 w-full p-3 hover:bg-dark-hover transition-colors ${mode === m.id ? 'bg-dark-hover' : ''}`}
                          >
                            {/* Company Logo */}
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
                                  <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${m.badge === 'New' ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'
                                    }`}>
                                    {m.badge}
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-gray-500">{m.description}</p>
                            </div>
                            {mode === m.id && <Check className="w-4 h-4 text-green-400" />}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                  <button
                    onClick={() => setModeDropdownOpen(!modeDropdownOpen)}
                    className="hidden sm:flex items-center gap-1.5 px-3 py-2 bg-dark-hover hover:bg-dark-surface rounded-lg transition-colors text-gray-200 text-sm font-medium whitespace-nowrap"
                  >
                    {currentMode.label}
                    <ChevronDown className={`w-4 h-4 transition-transform ${modeDropdownOpen ? 'rotate-180' : ''}`} />
                  </button>
                </div>

                {/* Send Button - Large and prominent */}
                <button
                  onClick={handleSend}
                  disabled={(!input.trim() && !selectedImage && attachedFiles.length === 0) || isLoading}
                  className="p-3 sm:p-2.5 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl transition-colors disabled:cursor-not-allowed"
                >
                  <Send className="w-6 h-6 sm:w-5 sm:h-5" />
                </button>
              </div>
            </div>

            {/* Disclaimer */}
            <p className="text-center text-xs text-gray-500 mt-3">
              AI Business Analyst can make mistakes. Please double-check responses.
            </p>
          </div>
        </div >
      </div >
    </div >
  );
};

export default AnalystChat;
