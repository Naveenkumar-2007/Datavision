import React, { useState, useCallback } from 'react';
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
} from 'lucide-react';
import apiService from '@/services/api';

interface FileItem {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  status: 'processing' | 'completed' | 'failed';
}

const DataHub: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const loadFiles = async () => {
    try {
      const response = await apiService.listFiles();
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Failed to load files:', error);
    }
  };

  // Load files on mount
  React.useEffect(() => {
    loadFiles();
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);
    try {
      const response = await apiService.uploadFiles(acceptedFiles);
      if (response.data.success) {
        alert(`✅ ${response.data.files.length} file(s) uploaded and trained successfully!`);
        // Refresh file list
        await loadFiles();
        // Notify other pages to refresh
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      console.error('Upload failed:', error);
      alert(`❌ Upload failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      // Documents
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/html': ['.html', '.htm'],
      // Spreadsheets
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'text/tab-separated-values': ['.tsv'],
      // Presentations
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      // Data formats
      'application/json': ['.json'],
      // Images
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
    },
  });

  const handleDelete = async (fileId: string) => {
    if (!confirm(`Are you sure you want to delete ${fileId}?`)) return;

    try {
      const response = await apiService.deleteFile(fileId);
      if (response.data.success) {
        setFiles(files.filter(f => f.id !== fileId));
        alert('✅ File deleted and indexes retrained!');
        // Notify other pages to refresh
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      console.error('Delete failed:', error);
      alert(`Failed to delete file: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm('⚠️ WARNING: This will delete ALL your files and indexes. Are you absolutely sure?')) return;

    try {
      const response = await apiService.deleteAllFiles();
      if (response.data.success) {
        setFiles([]);
        alert('All files deleted successfully!');
      }
    } catch (error: any) {
      console.error('Delete all failed:', error);
      alert(`Failed to delete files: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleRebuild = async () => {
    if (!confirm('🎯 RETRAIN: This will rebuild AI training from all files in Data Hub. Continue?')) return;

    setUploading(true);
    try {
      const response = await apiService.rebuildIndex();
      if (response.data.success) {
        const filesList = response.data.files?.join(', ') || 'all files';
        alert(`✅ Retrain Complete!\n\n${response.data.message}\n\nFiles trained: ${response.data.files_processed}\n${filesList}`);
        await loadFiles(); // Refresh list
        // Notify other pages to refresh
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      console.error('Retrain failed:', error);
      alert(`❌ Retrain failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (fileId: string) => {
    try {
      const userId = localStorage.getItem('userId') || 'user_001';
      const response = await fetch(`http://localhost:8000/api/v1/files/${userId}/${fileId}/download`, {
        method: 'GET'
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileId);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Download failed:', error);
      alert(`Failed to download file: ${error.message}`);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (type: string) => {
    // Excel/Spreadsheet files - bright green
    if (type.includes('excel') || type.includes('spreadsheet') || type.includes('xlsx') || type.includes('csv')) {
      return <Database className="w-5 h-5 text-emerald-400" />;
    }
    // PDF files - bright red
    if (type.includes('pdf')) {
      return <FileText className="w-5 h-5 text-red-400" />;
    }
    // Image files - bright orange
    if (type.includes('image') || type.includes('png') || type.includes('jpg')) {
      return <Image className="w-5 h-5 text-orange-400" />;
    }
    // Word/Document files - bright blue
    if (type.includes('word') || type.includes('docx') || type.includes('doc')) {
      return <FileText className="w-5 h-5 text-blue-400" />;
    }
    // Default - gray
    return <File className="w-5 h-5 text-gray-300" />;
  };

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Data Hub</h1>
          <p className="text-gray-400">Upload and manage your business data</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleRebuild}
            className="px-4 py-2 bg-accent-green/10 border border-accent-green/20 rounded-xl text-accent-green font-medium hover:bg-accent-green/20 transition-colors flex items-center space-x-2"
            title="Retrain AI from all uploaded files"
          >
            <RefreshCw className="w-4 h-4" />
            <span>🎯 Retrain</span>
          </button>
          <button
            onClick={handleDeleteAll}
            className="px-4 py-2 bg-accent-red/10 border border-accent-red/20 rounded-xl text-accent-red font-medium hover:bg-accent-red/20 transition-colors flex items-center space-x-2"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete All</span>
          </button>
        </div>
      </motion.div>

      {/* Upload Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div
          {...getRootProps()}
          className={`glass-card p-12 border-2 border-dashed transition-all cursor-pointer ${isDragActive
            ? 'border-primary-500 bg-primary-500/5'
            : 'border-dark-border hover:border-primary-500/50 hover:bg-dark-hover'
            }`}
        >
          <input {...getInputProps()} />
          <div className="text-center">
            {uploading ? (
              <>
                <Loader className="w-16 h-16 text-orange-400 mx-auto mb-4 animate-spin" />
                <p className="text-xl font-semibold text-white mb-2">Uploading files...</p>
              </>
            ) : (
              <>
                <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-xl font-semibold text-white mb-2">
                  {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
                </p>
                <p className="text-gray-400 mb-4">
                  or click to browse • Files auto-train immediately after upload
                </p>
                <div className="mb-4">
                  <p className="text-sm text-primary-400 font-semibold mb-3">Supported Formats:</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {[
                      { name: 'PDF', color: 'bg-red-500' },
                      { name: 'Excel', color: 'bg-emerald-500' },
                      { name: 'CSV', color: 'bg-green-500' },
                      { name: 'Word', color: 'bg-blue-500' },
                      { name: 'Images', color: 'bg-orange-500' },
                    ].map((format) => (
                      <span
                        key={format.name}
                        className={`px-3 py-1.5 ${format.color} rounded-lg text-sm text-white font-semibold shadow-md`}
                      >
                        {format.name}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">✅ Auto-trained • 🧠 Persistent memory • 🔍 RAG + Graph + Hybrid modes</p>
                </div>
              </>
            )}
          </div>
        </div>
      </motion.div>

      {/* Search and Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex items-center space-x-4"
      >
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-200 placeholder-gray-500 focus:outline-none focus:border-primary-500 transition-colors"
          />
        </div>
        <button className="px-4 py-3 bg-dark-card border border-dark-border rounded-xl text-gray-400 hover:text-gray-200 hover:bg-dark-hover transition-colors flex items-center space-x-2">
          <Filter className="w-5 h-5" />
          <span>Filters</span>
        </button>
      </motion.div>

      {/* Files List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-card overflow-hidden"
      >
        <div className="p-6 border-b border-dark-border">
          <h2 className="text-xl font-semibold text-white">
            Uploaded Files ({filteredFiles.length})
          </h2>
        </div>
        <div className="divide-y divide-dark-border">
          {filteredFiles.map((file, i) => (
            <motion.div
              key={file.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 + i * 0.05 }}
              className="data-hub-item p-6 hover:bg-dark-hover active:bg-dark-hover focus:bg-dark-hover transition-colors flex items-center justify-between group cursor-pointer"
            >
              <div className="flex items-center space-x-4 flex-1">
                <div className="w-12 h-12 bg-dark-card rounded-xl flex items-center justify-center">
                  {getFileIcon(file.type)}
                </div>
                <div className="flex-1">
                  <h3 className="text-white font-medium mb-1">{file.name}</h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-400">
                    <span>{formatFileSize(file.size)}</span>
                    <span>•</span>
                    <span>{new Date(file.uploadedAt).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {/* Status */}
                <div className="flex items-center space-x-2">
                  {file.status === 'completed' && (
                    <>
                      <CheckCircle className="w-5 h-5 text-accent-green" />
                      <span className="text-sm text-accent-green font-medium">Indexed</span>
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
                      <XCircle className="w-5 h-5 text-accent-red" />
                      <span className="text-sm text-accent-red font-medium">Failed</span>
                    </>
                  )}
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleDownload(file.id)}
                    className="p-2 hover:bg-dark-card rounded-lg transition-colors"
                    title="Download file"
                  >
                    <Download className="w-5 h-5 text-gray-400 hover:text-gray-200" />
                  </button>
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="p-2 hover:bg-accent-red/10 rounded-lg transition-colors"
                    title="Delete file"
                  >
                    <Trash2 className="w-5 h-5 text-gray-400 hover:text-accent-red" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default DataHub;
