import React, { useState, useCallback, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  File,
  Trash2,
  Download,
  Search,
  Filter,
  RefreshCw,
  FileText,
  Image,
  Database,
  CheckCircle,
  XCircle,
  Loader,
  Table,
  Link2,
  ExternalLink,
  Brain,
  Sparkles,
} from 'lucide-react';
import apiService from '@/services/api';

interface ThemeContext {
  isDark: boolean;
  bgColor: string;
  cardBg: string;
  textPrimary: string;
  textMuted: string;
  borderColor: string;
}

interface FileItem {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  status: 'processing' | 'completed' | 'failed';
}

const DataHub: React.FC = () => {
  const theme = useOutletContext<ThemeContext>() || {
    isDark: true,
    bgColor: '#0F172A',
    cardBg: '#1E293B',
    textPrimary: '#F8FAFC',
    textMuted: '#94A3B8',
    borderColor: '#334155',
  };

  const navigate = useNavigate();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [automlRunning, setAutomlRunning] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sheetUrl, setSheetUrl] = useState('');
  const [importingSheet, setImportingSheet] = useState(false);
  const [sheetPreview, setSheetPreview] = useState<any>(null);

  const loadFiles = async () => {
    try {
      const response = await apiService.listFiles();
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Failed to load files:', error);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);
    try {
      const response = await apiService.uploadFiles(acceptedFiles);
      if (response.data.success) {
        alert(`✅ ${response.data.files.length} file(s) uploaded successfully!`);
        await loadFiles();
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      console.error('Upload failed:', error);
      alert(`❌ Upload failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  }, []);

  // Run AutoML Training
  const handleRunAutoML = async () => {
    // Find CSV/Excel files
    const dataFiles = files.filter(f =>
      f.name.endsWith('.csv') || f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
    );

    if (dataFiles.length === 0) {
      alert('❌ No data files found. Please upload a CSV or Excel file first.');
      return;
    }

    setAutomlRunning(true);
    try {
      // Get the file from server and send to AutoML
      const userId = localStorage.getItem('userId') || 'default';
      const fileResponse = await fetch(`/api/v1/files/${userId}/${dataFiles[0].name}/download`);

      if (!fileResponse.ok) throw new Error('Failed to get file');

      const fileBlob = await fileResponse.blob();
      const formData = new FormData();
      formData.append('file', fileBlob, dataFiles[0].name);
      formData.append('user_id', userId);

      const automlResponse = await fetch('/api/v2/automl/train', {
        method: 'POST',
        body: formData,
      });

      const automlResult = await automlResponse.json();

      if (automlResult.success) {
        // Save to localStorage for persistence
        localStorage.setItem('mlResults', JSON.stringify(automlResult));
        localStorage.setItem('hasMLResults', 'true');

        // Navigate to ML Predictions page
        navigate('/ml-predictions', { state: { automlResult } });
      } else {
        alert(`❌ AutoML failed: ${automlResult.detail || 'Unknown error'}`);
      }
    } catch (error: any) {
      console.error('AutoML error:', error);
      alert(`❌ AutoML error: ${error.message}`);
    } finally {
      setAutomlRunning(false);
    }
  };

  // Check if data files exist
  const hasDataFiles = files.some(f =>
    f.name.endsWith('.csv') || f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
    },
  });

  const handleDelete = async (fileId: string) => {
    if (!confirm(`Are you sure you want to delete ${fileId}?`)) return;
    try {
      const response = await apiService.deleteFile(fileId);
      if (response.data.success) {
        setFiles(files.filter(f => f.id !== fileId));
        alert('✅ File deleted and indexes retrained!');
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      alert(`Failed to delete file: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm('⚠️ WARNING: This will delete ALL your files. Are you sure?')) return;
    try {
      const response = await apiService.deleteAllFiles();
      if (response.data.success) {
        setFiles([]);
        alert('All files deleted successfully!');
      }
    } catch (error: any) {
      alert(`Failed to delete files: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleRebuild = async () => {
    if (!confirm('🎯 RETRAIN: Rebuild AI training from all files?')) return;
    setUploading(true);
    try {
      const response = await apiService.rebuildIndex();
      if (response.data.success) {
        alert(`✅ Retrain Complete!\n\n${response.data.message}`);
        await loadFiles();
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      alert(`❌ Retrain failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (fileId: string) => {
    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`/api/v1/files/${userId}/${fileId}/download`);
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileId);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error: any) {
      alert(`Failed to download: ${error.message}`);
    }
  };

  const handlePreviewSheet = async () => {
    if (!sheetUrl.trim()) return alert('Please enter a Google Sheets URL');
    setImportingSheet(true);
    try {
      const response = await apiService.previewGoogleSheet(sheetUrl);
      setSheetPreview(response.data);
    } catch (error: any) {
      alert(`Preview failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setImportingSheet(false);
    }
  };

  const handleImportSheet = async () => {
    if (!sheetUrl.trim()) return alert('Please enter a Google Sheets URL');
    setImportingSheet(true);
    try {
      const response = await apiService.importGoogleSheet(sheetUrl);
      if (response.data.success) {
        alert(`✅ Google Sheet imported!`);
        setSheetUrl('');
        setSheetPreview(null);
        await loadFiles();
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      alert(`Import failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setImportingSheet(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (type: string) => {
    if (type.includes('excel') || type.includes('spreadsheet') || type.includes('xlsx') || type.includes('csv')) {
      return <Database className="w-5 h-5 text-emerald-400" />;
    }
    if (type.includes('pdf')) return <FileText className="w-5 h-5 text-red-400" />;
    if (type.includes('image')) return <Image className="w-5 h-5 text-orange-400" />;
    if (type.includes('word')) return <FileText className="w-5 h-5 text-blue-400" />;
    return <File className="w-5 h-5" style={{ color: theme.textMuted }} />;
  };

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const inputStyle = {
    backgroundColor: theme.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
    borderColor: theme.borderColor,
    color: theme.textPrimary,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: theme.textPrimary }}>Data Hub</h1>
          <p className="text-sm" style={{ color: theme.textMuted }}>Upload and manage your business data</p>
        </div>
        <div className="flex gap-3">
          {/* 🤖 ML Train Button - Shows when data files exist */}
          {hasDataFiles && (
            <button
              onClick={handleRunAutoML}
              disabled={automlRunning}
              className={`px-6 py-2 rounded-full font-semibold transition-all flex items-center gap-2 ${automlRunning
                ? 'bg-teal-500/30 text-teal-300 cursor-wait'
                : 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white hover:opacity-90 shadow-lg shadow-teal-500/25'
                }`}
            >
              {automlRunning ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  <span>Training ML Models...</span>
                </>
              ) : (
                <>
                  <Brain className="w-5 h-5" />
                  <span>🤖 Auto ML Train</span>
                </>
              )}
            </button>
          )}
          <button
            onClick={handleRebuild}
            className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 font-medium hover:bg-emerald-500/20 transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>🎯 Retrain</span>
          </button>
          <button
            onClick={handleDeleteAll}
            className="px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-full text-red-400 font-medium hover:bg-red-500/20 transition-colors flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete All</span>
          </button>
        </div>
      </motion.div>

      {/* Upload Area */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <div
          {...getRootProps()}
          className={`p-12 border-2 border-dashed rounded-2xl transition-all cursor-pointer ${isDragActive ? 'border-blue-500 bg-blue-500/5' : 'hover:border-blue-500/50'
            }`}
          style={{ backgroundColor: theme.cardBg, borderColor: isDragActive ? '#3B82F6' : theme.borderColor }}
        >
          <input {...getInputProps()} />
          <div className="text-center">
            {uploading ? (
              <>
                <Loader className="w-16 h-16 text-blue-500 mx-auto mb-4 animate-spin" />
                <p className="text-xl font-semibold mb-2" style={{ color: theme.textPrimary }}>Uploading files...</p>
              </>
            ) : (
              <>
                <Upload className="w-16 h-16 mx-auto mb-4" style={{ color: theme.textMuted }} />
                <p className="text-xl font-semibold mb-2" style={{ color: theme.textPrimary }}>
                  {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
                </p>
                <p className="mb-4" style={{ color: theme.textMuted }}>
                  or click to browse • Files auto-train immediately after upload
                </p>
                <div className="mb-4">
                  <p className="text-sm text-blue-500 font-semibold mb-3">Supported Formats:</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {[
                      { name: 'PDF', color: 'bg-red-500' },
                      { name: 'Excel', color: 'bg-emerald-500' },
                      { name: 'CSV', color: 'bg-green-500' },
                      { name: 'Images', color: 'bg-orange-500' },
                    ].map((format) => (
                      <span key={format.name} className={`px-3 py-1.5 ${format.color} rounded-lg text-sm text-white font-semibold`}>
                        {format.name}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs mt-3" style={{ color: theme.textMuted }}>
                    ✅ Auto-trained • 🧠 Persistent memory • 🔍 RAG + Graph + Hybrid modes
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </motion.div>

      {/* Google Sheets Import */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="p-6 rounded-2xl border"
        style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
      >
        <div className="flex items-center gap-3 mb-4">
          <Table className="w-6 h-6 text-green-500" />
          <h2 className="text-lg font-semibold" style={{ color: theme.textPrimary }}>Import from Google Sheets</h2>
        </div>
        <div className="flex gap-3 mb-4">
          <div className="flex-1 relative">
            <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: theme.textMuted }} />
            <input
              type="text"
              placeholder="Paste Google Sheets URL (must be public or 'Anyone with link')"
              value={sheetUrl}
              onChange={(e) => setSheetUrl(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl border focus:outline-none focus:border-green-500 transition-colors"
              style={inputStyle}
            />
          </div>
          <button
            onClick={handlePreviewSheet}
            disabled={importingSheet || !sheetUrl.trim()}
            className="px-4 py-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 font-medium hover:bg-blue-500/20 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {importingSheet ? <Loader className="w-4 h-4 animate-spin" /> : <ExternalLink className="w-4 h-4" />}
            Preview
          </button>
          <button
            onClick={handleImportSheet}
            disabled={importingSheet || !sheetUrl.trim()}
            className="px-6 py-3 bg-green-500 hover:bg-green-600 rounded-xl text-white font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {importingSheet ? <Loader className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Import
          </button>
        </div>
        {sheetPreview?.success && (
          <div className="p-4 rounded-xl border" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', borderColor: theme.borderColor }}>
            <div className="flex items-center justify-between mb-3">
              <span style={{ color: theme.textPrimary }} className="font-medium">Preview</span>
              <span className="text-sm" style={{ color: theme.textMuted }}>{sheetPreview.rowCount} rows × {sheetPreview.columnCount} columns</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {sheetPreview.columns?.slice(0, 8).map((col: string, i: number) => (
                <span key={i} className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-medium">{col}</span>
              ))}
            </div>
          </div>
        )}
        <p className="text-xs mt-3" style={{ color: theme.textMuted }}>💡 Sheet must be accessible: File → Share → "Anyone with the link can view"</p>
      </motion.div>

      {/* Search */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: theme.textMuted }} />
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-xl border focus:outline-none focus:border-blue-500 transition-colors"
            style={inputStyle}
          />
        </div>
        <button
          className="px-4 py-3 rounded-xl border transition-colors flex items-center gap-2"
          style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor, color: theme.textMuted }}
        >
          <Filter className="w-5 h-5" />
          <span>Filters</span>
        </button>
      </motion.div>

      {/* Files List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="rounded-2xl border overflow-hidden"
        style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
      >
        <div className="p-6 border-b" style={{ borderColor: theme.borderColor }}>
          <h2 className="text-lg font-semibold" style={{ color: theme.textPrimary }}>
            Uploaded Files ({filteredFiles.length})
          </h2>
        </div>
        <div className="divide-y" style={{ borderColor: theme.borderColor }}>
          {filteredFiles.map((file, i) => (
            <motion.div
              key={file.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 + i * 0.05 }}
              className="p-6 flex items-center justify-between transition-colors hover:bg-white/5"
            >
              <div className="flex items-center gap-4 flex-1">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
                  {getFileIcon(file.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium mb-1 truncate" style={{ color: theme.textPrimary }}>{file.name}</h3>
                  <div className="flex items-center gap-4 text-sm" style={{ color: theme.textMuted }}>
                    <span>{formatFileSize(file.size)}</span>
                    <span>•</span>
                    <span>{new Date(file.uploadedAt).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  {file.status === 'completed' && (
                    <>
                      <CheckCircle className="w-5 h-5 text-emerald-400" />
                      <span className="text-sm text-emerald-400 font-medium">Indexed</span>
                    </>
                  )}
                  {file.status === 'processing' && (
                    <>
                      <Loader className="w-5 h-5 text-orange-400 animate-spin" />
                      <span className="text-sm text-orange-400 font-medium">Processing</span>
                    </>
                  )}
                  {file.status === 'failed' && (
                    <>
                      <XCircle className="w-5 h-5 text-red-400" />
                      <span className="text-sm text-red-400 font-medium">Failed</span>
                    </>
                  )}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleDownload(file.id)} className="p-2 rounded-lg hover:bg-white/10 transition-colors" title="Download">
                    <Download className="w-5 h-5" style={{ color: theme.textMuted }} />
                  </button>
                  <button onClick={() => handleDelete(file.id)} className="p-2 rounded-lg hover:bg-red-500/10 transition-colors" title="Delete">
                    <Trash2 className="w-5 h-5" style={{ color: theme.textMuted }} />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
          {filteredFiles.length === 0 && (
            <div className="p-12 text-center" style={{ color: theme.textMuted }}>
              <Upload className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No files uploaded yet</p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default DataHub;
