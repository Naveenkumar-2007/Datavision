import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
  Send,
  Sparkles,
  User,
  FileText,
  TrendingUp,
  Network,
  Image as ImageIcon,
  Loader,
  Mic,
  Paperclip,
  X,
  Upload,
  Calendar,
} from 'lucide-react';
import apiService from '@/services/api';
import GraphVisualization from '@/components/GraphVisualization';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
}

// Component to format markdown-like responses
const FormattedMessage: React.FC<{ content: string }> = ({ content }) => {
  // Split content into paragraphs and format
  const formatContent = (text: string) => {
    // Split by double newlines for paragraphs
    const paragraphs = text.split('\n\n');
    
    return paragraphs.map((para, idx) => {
      // Check for headers
      if (para.startsWith('###')) {
        return <h3 key={idx} className="text-lg font-bold text-white mt-4 mb-2">{para.replace(/^###\s*/, '')}</h3>;
      }
      if (para.startsWith('##')) {
        return <h2 key={idx} className="text-xl font-bold text-white mt-4 mb-2">{para.replace(/^##\s*/, '')}</h2>;
      }
      if (para.startsWith('#')) {
        return <h1 key={idx} className="text-2xl font-bold text-white mt-4 mb-2">{para.replace(/^#\s*/, '')}</h1>;
      }
      
      // Check for lists
      if (para.includes('\n-') || para.includes('\n•') || para.includes('\n*')) {
        const items = para.split('\n').filter(line => line.trim().match(/^[-•*]\s/));
        if (items.length > 0) {
          return (
            <ul key={idx} className="list-disc list-inside space-y-1 my-2">
              {items.map((item, i) => (
                <li key={i} className="text-gray-200">{item.replace(/^[-•*]\s*/, '')}</li>
              ))}
            </ul>
          );
        }
      }
      
      // Check for numbered lists
      if (para.match(/^\d+\./m)) {
        const items = para.split('\n').filter(line => line.trim().match(/^\d+\./));
        if (items.length > 0) {
          return (
            <ol key={idx} className="list-decimal list-inside space-y-1 my-2">
              {items.map((item, i) => (
                <li key={i} className="text-gray-200">{item.replace(/^\d+\.\s*/, '')}</li>
              ))}
            </ol>
          );
        }
      }
      
      // Check for tables (simple markdown tables)
      if (para.includes('|')) {
        const lines = para.trim().split('\n');
        if (lines.length >= 2 && lines[0].includes('|') && lines[1].includes('|')) {
          const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
          const rows = lines.slice(2).map(row => 
            row.split('|').map(cell => cell.trim()).filter(cell => cell)
          );
          
          return (
            <div key={idx} className="my-4 overflow-x-auto">
              <table className="min-w-full border border-dark-border rounded-lg overflow-hidden">
                <thead className="bg-primary-500/10">
                  <tr>
                    {headers.map((header, i) => (
                      <th key={i} className="px-4 py-2 text-left text-sm font-semibold text-white border-b border-dark-border">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i} className="border-b border-dark-border/50 hover:bg-dark-hover/30">
                      {row.map((cell, j) => (
                        <td key={j} className="px-4 py-2 text-sm text-gray-300">
                          {cell}
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
      
      // Regular paragraph with bold/italic support
      const formattedPara = para
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code class="bg-dark-bg px-1 rounded">$1</code>');
      
      return (
        <p key={idx} className="mb-2 text-gray-200" dangerouslySetInnerHTML={{ __html: formattedPara }} />
      );
    });
  };
  
  return <div className="space-y-2">{formatContent(content)}</div>;
};

const AnalystChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI Business Analyst. I can help you analyze your data using RAG, GraphRAG, or Vision mode. What would you like to know?',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'rag' | 'graphrag' | 'hybrid' | 'vision'>('rag');
  const [isRecording, setIsRecording] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [conversationId, setConversationId] = useState<string>(`conv_${Date.now()}`);
  const [graphStats, setGraphStats] = useState({ nodes: 0, relationships: 0 });
  const [queryStats, setQueryStats] = useState({ totalQueries: 0, avgResponseTime: 0 });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadUploadedFiles();
    loadAnalytics();
    
    // Listen for file updates from other pages
    const handleFilesUpdated = () => {
      console.log('Files updated event received, refreshing list...');
      loadUploadedFiles();
      loadAnalytics();
    };
    
    window.addEventListener('filesUpdated', handleFilesUpdated);
    
    return () => {
      window.removeEventListener('filesUpdated', handleFilesUpdated);
    };
  }, []);

  const loadUploadedFiles = async () => {
    try {
      const response = await apiService.listFiles();
      setUploadedFiles(response.data.files || []);
    } catch (error) {
      console.error('Failed to load files:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await apiService.getAnalyticsOverview();
      const data = response.data;
      
      // Update graph statistics
      if (data.graphStats) {
        setGraphStats({
          nodes: data.graphStats.nodes || 0,
          relationships: data.graphStats.relationships || 0
        });
      }
      
      // Update query statistics
      if (data.queryStats) {
        setQueryStats({
          totalQueries: data.queryStats.totalQueries || 0,
          avgResponseTime: data.queryStats.avgResponseTime || 0
        });
      }
      
      console.log('📊 Loaded analytics:', { graphStats, queryStats });
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles: File[]) => {
      setAttachedFiles(prev => [...prev, ...acceptedFiles]);
      if (acceptedFiles.length > 0) {
        setInput(prev => prev || `Compare these files: ${acceptedFiles.map(f => f.name).join(', ')}`);
      }
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
      alert(`Speech recognition error: ${event.error}`);
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

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);
  };

  const handleFileDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;

    const file = files[0];
    
    // Check if it's an image for vision mode
    if (file.type.startsWith('image/')) {
      setSelectedImage(file);
      setMode('vision');
      setInput(prev => prev || 'Analyze this image');
    } else {
      // For other files, add to attached files for training
      setAttachedFiles(prev => [...prev, file]);
      setInput(prev => prev || `Analyze ${file.name}`);
    }
  };

  const handleSend = async () => {
    // Check if there's actual content to send
    const hasContent = input.trim().length > 0 || selectedImage || attachedFiles.length > 0;
    
    if (!hasContent || isLoading) {
      console.log('No content to send or already loading');
      return;
    }

    let messageContent = input.trim();
    if (selectedImage) {
      messageContent += ` [Image: ${selectedImage.name}]`;
    }
    if (attachedFiles.length > 0) {
      messageContent += ` [Attached: ${attachedFiles.map(f => f.name).join(', ')}]`;
    }

    // Don't proceed if message is empty after processing
    if (!messageContent && !selectedImage && attachedFiles.length === 0) {
      console.log('Empty message content');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageContent,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const messageToSend = input.trim();
    const filesToCompare = attachedFiles.map(f => f.name);
    setInput('');
    setSelectedImage(null);
    setAttachedFiles([]);
    setIsLoading(true);

    try {
      // Prepare attached files info for vision mode
      let visionAttachments: any[] = [];
      
      // Handle image upload for vision mode - convert to base64
      if (selectedImage) {
        // Read file as base64
        const base64Content = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(selectedImage);
        });
        
        visionAttachments.push({
          name: selectedImage.name,
          type: selectedImage.type,
          size: selectedImage.size,
          content: base64Content // Add base64 content for backend
        });
        
        console.log('📷 Image converted to base64, size:', base64Content.length);
      }
      
      // Upload attached files first if any (for training)
      if (attachedFiles.length > 0) {
        await apiService.uploadFiles(attachedFiles);
        await loadUploadedFiles(); // Refresh file list in chat
        // Trigger refresh event for other pages
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }

      console.log('Sending message:', messageToSend);
      console.log('Mode:', mode);
      console.log('Vision attachments:', visionAttachments);
      
      // Send message with conversation ID, file comparison, and vision attachments
      const response = await apiService.sendMessage(
        messageToSend, 
        mode, 
        conversationId,
        filesToCompare.length > 0 ? filesToCompare : undefined,
        visionAttachments.length > 0 ? visionAttachments : undefined
      );
      
      console.log('Received response:', response.data);
      
      // Update conversation ID from response
      if (response.data.conversationId) {
        setConversationId(response.data.conversationId);
      }

      // Safely extract response content
      const responseContent = response.data?.message || response.data?.answer || 'No response received';
      const responseSources = response.data?.sources || [];
      
      console.log('Response content:', responseContent);
      console.log('Response sources:', responseSources);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: String(responseContent), // Ensure it's always a string
        timestamp: new Date(),
        sources: Array.isArray(responseSources) ? responseSources.map(s => String(s)) : [],
      };
      
      console.log('Adding assistant message:', assistantMessage);
      setMessages(prev => {
        const newMessages = [...prev, assistantMessage];
        console.log('New messages array:', newMessages);
        return newMessages;
      });
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message || 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestedQuestions = [
    'What are the top 3 revenue-generating products?',
    'Show me customer segmentation analysis',
    'What trends do you see in sales data?',
    'Analyze my business expenses breakdown',
  ];

  const modes = [
    { id: 'rag', label: 'RAG', icon: FileText, description: 'Document-based retrieval' },
    { id: 'graphrag', label: 'GraphRAG', icon: Network, description: 'Knowledge graph reasoning' },
    { id: 'hybrid', label: 'Hybrid', icon: TrendingUp, description: 'Best of both worlds' },
    { id: 'vision', label: 'Vision', icon: ImageIcon, description: 'Image & chart analysis' },
  ];

  return (
    <div className="h-[calc(100vh-12rem)] flex space-x-6">
      {/* Mode Selector - Left Panel */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-64 glass-card p-4 space-y-3 overflow-y-auto"
      >
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Analysis Mode
        </h3>
        {modes.map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id as any)}
            className={`w-full p-4 rounded-xl transition-all text-left ${
              mode === m.id
                ? 'bg-primary-500/20 border-2 border-primary-500'
                : 'bg-dark-card border border-dark-border hover:bg-dark-hover'
            }`}
          >
            <div className="flex items-center space-x-3 mb-2">
              <m.icon className={`w-5 h-5 ${mode === m.id ? 'text-primary-400' : 'text-gray-400'}`} />
              <span className={`font-semibold ${mode === m.id ? 'text-white' : 'text-gray-300'}`}>
                {m.label}
              </span>
            </div>
            <p className="text-xs text-gray-400">{m.description}</p>
          </button>
        ))}

        {/* Suggested Questions */}
        <div className="mt-8">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
            Suggested
          </h3>
          <div className="space-y-2">
            {suggestedQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => setInput(q)}
                className="w-full p-3 bg-dark-card border border-dark-border rounded-lg text-left text-sm text-gray-300 hover:bg-dark-hover hover:text-white transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Chat Area - Middle Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex-1 glass-card flex flex-col"
      >
        {/* Header */}
        <div className="p-6 border-b border-dark-border flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-purple rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">AI Business Analyst</h2>
              <p className="text-sm text-gray-400">Mode: {mode.toUpperCase()}</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <AnimatePresence>
            {messages.filter(msg => msg && msg.id && msg.content).map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`flex space-x-3 max-w-3xl ${
                    message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      message.role === 'user'
                        ? 'bg-primary-500/20'
                        : 'bg-gradient-to-br from-primary-500 to-accent-purple'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <User className="w-5 h-5 text-primary-400" />
                    ) : (
                      <Sparkles className="w-5 h-5 text-white" />
                    )}
                  </div>

                  {/* Content */}
                  <div
                    className={`rounded-2xl p-4 ${
                      message.role === 'user'
                        ? 'bg-primary-500/20 border border-primary-500/30'
                        : 'bg-dark-card border border-dark-border'
                    }`}
                  >
                    <div className="text-gray-200 leading-relaxed prose prose-invert max-w-none">
                      {message.role === 'assistant' ? (
                        <FormattedMessage content={message.content || 'No content'} />
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content || 'No content'}</p>
                      )}
                    </div>
                    
                    {/* Show Graph Visualization for GraphRAG mode responses */}
                    {message.role === 'assistant' && mode === 'graphrag' && message.content && message.content.length > 500 && (
                      <div className="mt-4">
                        <GraphVisualization userId="user_001" maxNodes={150} />
                      </div>
                    )}
                    
                    {message.sources && Array.isArray(message.sources) && message.sources.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-dark-border/50">
                        <p className="text-xs font-semibold text-gray-400 mb-2 flex items-center">
                          <FileText className="w-3 h-3 mr-1" />
                          Sources
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {message.sources.map((source, i) => (
                            <span
                              key={i}
                              className="px-3 py-1.5 bg-primary-500/10 border border-primary-500/20 rounded-lg text-xs text-primary-300 font-medium"
                            >
                              {String(source)}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    <p className="text-xs text-gray-500 mt-2">
                      {message.timestamp instanceof Date ? message.timestamp.toLocaleTimeString() : new Date().toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center space-x-3"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-purple rounded-xl flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="bg-dark-card border border-dark-border rounded-2xl p-4">
                <div className="flex items-center space-x-2">
                  <Loader className="w-4 h-4 text-primary-400 animate-spin" />
                  <span className="text-gray-400">Analyzing...</span>
                </div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-6 border-t border-dark-border">
          {/* Drag & Drop Zone */}
          <div
            {...getRootProps()}
            className={`mb-4 border-2 border-dashed rounded-xl p-4 transition-all ${
              isDragActive
                ? 'border-accent-orange bg-accent-orange/10'
                : 'border-dark-border bg-dark-card/50'
            }`}
          >
            <input {...getInputProps()} />
            <div className="text-center">
              <Upload className="w-6 h-6 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-400">
                {isDragActive
                  ? 'Drop files here to attach...'
                  : '⚠️ Drag files for COMPARISON only (not trained)'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                These files won't be in training data. Upload in Data Hub to train.
              </p>
            </div>
          </div>

          {/* Attached Files Display */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 space-y-2">
              <p className="text-xs text-gray-400 font-semibold">Attached Files:</p>
              {attachedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center space-x-2 text-sm bg-primary-500/10 border border-primary-500/20 rounded-lg px-3 py-2"
                >
                  <FileText className="w-4 h-4 text-primary-400" />
                  <span className="text-gray-300 flex-1">{file.name}</span>
                  <span className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                  <button
                    onClick={() => removeAttachedFile(index)}
                    className="text-accent-red hover:text-accent-red/80"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Selected Image Display */}
          {selectedImage && (
            <div className="mb-3 flex items-center space-x-2 text-sm bg-accent-purple/10 border border-accent-purple/20 rounded-lg px-3 py-2">
              <ImageIcon className="w-4 h-4 text-accent-purple" />
              <span className="text-gray-300">{selectedImage.name}</span>
              <button
                onClick={() => setSelectedImage(null)}
                className="text-accent-red hover:text-accent-red/80 ml-auto"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          <div className="flex items-end space-x-2">
            {/* Mic Button */}
            <button
              onClick={handleVoiceInput}
              disabled={isLoading}
              className={`p-3 rounded-xl transition-all ${
                isRecording
                  ? 'bg-accent-red text-white animate-pulse'
                  : 'bg-dark-card border border-dark-border text-gray-400 hover:text-white hover:bg-dark-hover'
              }`}
              title="Voice input"
            >
              <Mic className="w-5 h-5" />
            </button>

            {/* Image Upload Button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="p-3 bg-dark-card border border-dark-border rounded-xl text-gray-400 hover:text-white hover:bg-dark-hover transition-all disabled:opacity-50"
              title="Upload image"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              className="hidden"
            />

            {/* Text Input with Drag & Drop */}
            <div 
              className="flex-1 relative"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleFileDrop}
            >
              {isDraggingOver && (
                <div className="absolute inset-0 bg-primary-500/20 border-2 border-primary-500 border-dashed rounded-xl z-10 flex items-center justify-center">
                  <div className="text-center">
                    <Paperclip className="w-8 h-8 text-primary-400 mx-auto mb-2" />
                    <p className="text-primary-300 font-semibold">Drop files here</p>
                    <p className="text-xs text-gray-400 mt-1">Images for Vision mode • Documents for training</p>
                  </div>
                </div>
              )}
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask anything about your business data... (or drag & drop files here)"
                rows={2}
                className="w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 placeholder-gray-500 focus:outline-none focus:border-primary-500 transition-colors resize-none"
              />
            </div>

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={(!input.trim() && !selectedImage) || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-purple rounded-xl text-white font-semibold hover:shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <span>Send</span>
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Context Panel - Right Side */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-80 glass-card p-6 space-y-6 overflow-y-auto"
      >
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Context & Sources
        </h3>

        <div className="space-y-4">
          <div className="bg-dark-card rounded-xl p-4">
            <h4 className="text-white font-medium mb-2 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4" />
                <span>Trained Files ({uploadedFiles.length})</span>
              </div>
              <span className="text-xs text-accent-green font-semibold">✓ In Training Data</span>
            </h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {uploadedFiles.length > 0 ? (
                uploadedFiles.map((file: any, index: number) => (
                  <div key={index} className="flex items-start space-x-2 text-sm bg-accent-green/5 rounded-lg p-2">
                    <FileText className="w-4 h-4 text-accent-green mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-300 truncate font-medium" title={file.name}>{file.name}</p>
                      <p className="text-xs text-gray-500 flex items-center space-x-1 mt-0.5">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(file.uploadedAt).toLocaleDateString()}</span>
                        <span className="text-gray-600">•</span>
                        <span>{new Date(file.uploadedAt).toLocaleTimeString()}</span>
                      </p>
                    </div>
                    <span className="text-xs text-accent-green">✓</span>
                  </div>
                ))
              ) : (
                <div className="text-center py-4">
                  <p className="text-xs text-gray-500 italic mb-2">No trained files yet.</p>
                  <a href="/data-hub" className="text-xs text-primary-400 hover:text-primary-300">
                    Upload files in Data Hub →
                  </a>
                </div>
              )}
            </div>
          </div>

          <div className="bg-dark-card rounded-xl p-4">
            <h4 className="text-white font-medium mb-2">Knowledge Graph</h4>
            <div className="space-y-2 text-sm text-gray-400">
              <div className="flex justify-between">
                <span>Nodes:</span>
                <span className="text-white font-medium">{graphStats.nodes.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Relationships:</span>
                <span className="text-white font-medium">{graphStats.relationships.toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="bg-dark-card rounded-xl p-4">
            <h4 className="text-white font-medium mb-2">Statistics</h4>
            <div className="space-y-2 text-sm text-gray-400">
              <div className="flex justify-between">
                <span>Total Queries:</span>
                <span className="text-white font-medium">{queryStats.totalQueries}</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Response:</span>
                <span className="text-white font-medium">{queryStats.avgResponseTime.toFixed(1)}s</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AnalystChat;
