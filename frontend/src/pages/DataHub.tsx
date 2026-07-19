import React, { useState, useCallback, useEffect, useRef } from 'react';
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
  Wrench,
  BarChart2,
  Zap,
  Layers,
  Network
} from 'lucide-react';
import apiService from '@/services/api';
import MultiFileUpload from '@/components/automl/MultiFileUpload';
import MultiDatasetJoiner from '@/components/automl/MultiDatasetJoiner';
import { LiveStreamingDashboard } from '@/components/LiveStreamingDashboard';
import { ConnectionSetupModal } from '@/components/ui/ConnectionSetupModal';
import { useConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/contexts/ToastContext';
import { getUserIdSync, getAuthHeadersSync } from '@/utils/userId';

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

import { useUserStore } from '@/store/userStore';

const DataHub: React.FC = () => {
  const { isDark } = useUserStore();
  const { confirm, ConfirmModal } = useConfirmModal();
  const toast = useToast();

  // Derived theme object removed - using global CSS variables


  const navigate = useNavigate();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [automlRunning, setAutomlRunning] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sheetUrl, setSheetUrl] = useState('');
  const [importingSheet, setImportingSheet] = useState(false);
  const [sheetPreview, setSheetPreview] = useState<any>(null);
  const [autoFixEnabled, setAutoFixEnabled] = useState(false); // OFF by default - enable to clean data before upload
  const [fixingData, setFixingData] = useState(false);
  const [lastFixReport, setLastFixReport] = useState<any>(null);
  const [ultraMode, setUltraMode] = useState(true); // Ultra AutoML (maximum accuracy) is default
  const [showMultiFile, setShowMultiFile] = useState(false); // Multi-file training toggle
  const [showJoiner, setShowJoiner] = useState(false);
  const [targetColumn, setTargetColumn] = useState<string>(''); // User-selected target column
  const [availableColumns, setAvailableColumns] = useState<string[]>([]); // Columns from uploaded file
  const [activeStreamSource, setActiveStreamSource] = useState<string | null>(null); // Live stream source
  const [activeConnectionId, setActiveConnectionId] = useState<string | null>(null); // Live connection ID
  const [showConnectionModal, setShowConnectionModal] = useState<string | null>(null); // Connection Setup Modal state
  const [activeConnections, setActiveConnections] = useState<any[]>([]); // Saved live pipelines
  const [fetchingConnections, setFetchingConnections] = useState(false);

  // Training UX State
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  const [progressMessage, setProgressMessage] = useState('Initializing...');

  // Upload Cancel State - using refs to avoid stale closures in cancel handler
  const [uploadAbortController, setUploadAbortController] = useState<AbortController | null>(null);
  const [uploadingFileNames, setUploadingFileNames] = useState<string[]>([]); // Track files being uploaded for cancellation
  const uploadAbortControllerRef = useRef<AbortController | null>(null);
  const uploadingFileNamesRef = useRef<string[]>([]);

  // Delete State
  const [deletingFileId, setDeletingFileId] = useState<string | null>(null);
  const [deleteAbortController, setDeleteAbortController] = useState<AbortController | null>(null);

  // Animation loop for training messages
  useEffect(() => {
    if (!automlRunning) return;
    const messages = ultraMode ? [
      '?? Initializing Ultra AutoML...',
      '?? Analyzing Dataset Profile...',
      '?? Meta-Learning Recommendations...',
      '?? Synthesizing 50+ Features...',
      '?? Training Classical Models...',
      '?? Training Neural Networks...',
      '?? Optimizing Hyperparameters...',
      '?? Building Ultra Ensemble...',
      '?? Generating Explainability...',
    ] : [
      '?? Cleaning Data (Phase 1/4)...',
      '??? Engineering Features (Phase 2/4)...',
      '?? Training 15+ Models (Phase 3/4)...',
      '?? Optimizing Hyperparameters...',
      '?? Building Ensembles...',
      '?? Generating High-Res Charts...'
    ];
    let i = 0;
    const interval = setInterval(() => {
      setProgressMessage(messages[i % messages.length]);
      i++;
    }, 3500);
    return () => clearInterval(interval);
  }, [automlRunning]);

  const loadFiles = async () => {
    try {
      const response = await apiService.listFiles();
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Failed to load files:', error);
    }
  };

  // Parse CSV to extract column names
  const parseCSVColumns = (file: File): Promise<string[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        const firstLine = text.split('\n')[0];
        const columns = firstLine.split(',').map(col => col.trim().replace(/"/g, ''));
        resolve(columns);
      };
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  // Smart target column detection - looks for common patterns
  const detectTargetColumn = (columns: string[]): string => {
    const targetPatterns = [
      'target', 'label', 'class', 'y', 'output', 'result', 'prediction',
      'price_range', 'price', 'category', 'status', 'type', 'outcome',
      'fraud', 'churn', 'default', 'survived', 'approved', 'purchased'
    ];

    // Check for exact/partial matches
    for (const pattern of targetPatterns) {
      for (const col of columns) {
        if (col.toLowerCase().includes(pattern)) {
          return col;
        }
      }
    }

    // Default: last column (common ML convention)
    return columns[columns.length - 1];
  };

  const handleDirectApiPush = async () => {
    try {
      const response = await fetch('/api/v1/connections', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeadersSync()
        },
        body: JSON.stringify({
          source_type: 'api_push',
          host: 'datavision',
          database_name: 'push',
          target_table: 'push',
          credentials: 'none'
        })
      });
      const data = await response.json();
      const connectionId = data.connection_id;
      
      // Persist guest connections
      if (data.is_guest && data.connection) {
        const stored = JSON.parse(localStorage.getItem('guest_live_connections') || '[]');
        stored.unshift(data.connection); // Add to top
        localStorage.setItem('guest_live_connections', JSON.stringify(stored));
      }
      
      setActiveConnectionId(connectionId);
      setActiveStreamSource('DataVision API Push');
      loadConnections();
    } catch (err) {
      console.error('Failed to create API Push:', err);
    }
  };

  const loadConnections = async () => {
    try {
      setFetchingConnections(true);
      let conns: any[] = [];
      
      try {
        const response = await apiService.getLiveConnections();
        conns = response.data.connections || [];
      } catch {
        // API may fail for guest users — that's OK
      }
      
      // Auto-adopt guest connections from localStorage when a real user is logged in
      const currentUserId = getUserIdSync();
      const isRealUser = currentUserId && !currentUserId.startsWith('guest_');
      const stored = JSON.parse(localStorage.getItem('guest_live_connections') || '[]');
      
      if (isRealUser && stored.length > 0) {
        // Try to adopt each guest connection into the DB
        for (const guestConn of stored) {
          try {
            const existingIds = new Set(conns.map((c: any) => c.id));
            // Skip if already adopted (same table/host exists in DB connections)
            const alreadyAdopted = conns.some((c: any) => 
              c.target_table === guestConn.target_table && 
              c.host === guestConn.host &&
              c.database_name === guestConn.database_name
            );
            
            if (!alreadyAdopted && !existingIds.has(guestConn.id)) {
              await apiService.adoptGuestConnection(guestConn.id, guestConn);
              console.log(`✅ Adopted guest connection: ${guestConn.id}`);
            }
          } catch (err: any) {
            // 409 = already has different data, just skip
            console.log(`⚠️ Could not adopt guest connection: ${err?.response?.data?.detail || err.message}`);
          }
        }
        
        // Clear localStorage after adoption attempt
        localStorage.removeItem('guest_live_connections');
        
        // Re-fetch from DB to get the adopted connections with clean IDs
        try {
          const response = await apiService.getLiveConnections();
          conns = response.data.connections || [];
        } catch { /* ignore */ }
      } else if (stored.length > 0) {
        // Guest user — merge localStorage connections as before
        const existingIds = new Set(conns.map((c: any) => c.id));
        const uniqueStored = stored.filter((c: any) => !existingIds.has(c.id));
        conns = [...uniqueStored, ...conns];
      }
      
      setActiveConnections(conns);
    } finally {
      setFetchingConnections(false);
    }
  };

  useEffect(() => {
    // Process any pending workspace invite from auth redirect
    const pendingInvite = localStorage.getItem('pending_invite');
    if (pendingInvite && getUserIdSync() && !getUserIdSync().startsWith('guest_')) {
      apiService.acceptInvite(pendingInvite)
        .then(() => {
          localStorage.removeItem('pending_invite');
          toast.success('Successfully joined the workspace!');
        })
        .catch(err => {
          localStorage.removeItem('pending_invite');
          console.error('Failed to accept invite:', err);
        });
    }

    // Clean stale/duplicate localStorage connections on mount
    try {
      const stored = JSON.parse(localStorage.getItem('guest_live_connections') || '[]');
      if (stored.length > 0) {
        // Deduplicate by id, keep only unique entries
        const seen = new Set();
        const cleaned = stored.filter((c: any) => {
          if (!c.id || seen.has(c.id)) return false;
          seen.add(c.id);
          return true;
        });
        localStorage.setItem('guest_live_connections', JSON.stringify(cleaned));
      }
    } catch { /* ignore */ }
    
    // Load connections first (may trigger adoption), then load files
    const init = async () => {
      await loadConnections();
      await loadFiles();
    };
    init();
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Create abort controller for cancel functionality
    const controller = new AbortController();
    setUploadAbortController(controller);
    uploadAbortControllerRef.current = controller; // Store in ref for cancel handler

    // Track filenames for cancellation cleanup
    const fileNames = acceptedFiles.map(f => f.name);
    setUploadingFileNames(fileNames);
    uploadingFileNamesRef.current = fileNames; // Store in ref for cancel handler

    setUploading(true);
    setLastFixReport(null);
    try {
      // Separate data files from other files
      const dataFiles = acceptedFiles.filter(f =>
        f.name.endsWith('.csv') || f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
      );
      const otherFiles = acceptedFiles.filter(f =>
        !f.name.endsWith('.csv') && !f.name.endsWith('.xlsx') && !f.name.endsWith('.xls')
      );

      // Extract columns from first CSV file for target selection
      if (dataFiles.length > 0 && dataFiles[0].name.endsWith('.csv')) {
        try {
          const columns = await parseCSVColumns(dataFiles[0]);
          setAvailableColumns(columns);
          const detected = detectTargetColumn(columns);
          setTargetColumn(detected);
          console.log(`?? Detected columns: ${columns.length}, Target: ${detected}`);
        } catch (e) {
          console.warn('Could not parse columns from CSV:', e);
        }
      }

      let filesToUpload = [...otherFiles];

      // If auto-fix is enabled and we have data files, fix them first
      if (autoFixEnabled && dataFiles.length > 0) {
        setFixingData(true);

        for (const dataFile of dataFiles) {
          const formData = new FormData();
          formData.append('file', dataFile);
          formData.append('user_id', getUserIdSync());
          formData.append('fix_missing', 'true');
          formData.append('fix_outliers', 'true');
          formData.append('fix_duplicates', 'true');
          formData.append('fix_types', 'true');
          formData.append('enrich_dates', 'true');

          try {
            const fixResponse = await fetch('/api/v2/autonomous/auto-fix', {
              method: 'POST',
              body: formData,
              signal: controller.signal,
              headers: {
                'X-User-ID': getUserIdSync()
              }
            });
            const fixData = await fixResponse.json();

            if (fixData.success && fixData.report) {
              setLastFixReport(fixData.report);
              const improvement = fixData.report.quality_improvement;
              console.log(`? Fixed ${dataFile.name}: ${(improvement.before * 100).toFixed(0)}% ? ${(improvement.after * 100).toFixed(0)}%`);
            }
          } catch (e: any) {
            if (e.name === 'AbortError') throw e; // Re-throw abort to outer catch
            console.warn('Auto-fix failed, using original file:', e);
          }
        }
        setFixingData(false);
        // Note: Fixed file is saved server-side, original still uploads but training uses fixed version
      }

      // Upload all accepted files (server will handle them) - pass abort signal
      const response = await apiService.uploadFiles(acceptedFiles, controller.signal);
      if (response.data.success) {
        toast.success(`${response.data.files.length} file(s) uploaded${autoFixEnabled && dataFiles.length > 0 ? ' (data quality auto-fixed)' : ''}!`);
        await loadFiles();
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      // Handle user cancel - silent exit
      if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
        console.log('?? Upload cancelled by user');
        return;
      }
      console.error('Upload failed:', error);
      toast.error(`Upload failed: ${error.response?.data?.detail || error.message}`);
      setFixingData(false);
    } finally {
      setUploading(false);
      setUploadAbortController(null);
      uploadAbortControllerRef.current = null;
      uploadingFileNamesRef.current = [];
    }
  }, [autoFixEnabled]);

  // Cancel Upload Handler - uses refs to avoid stale closure issues
  const handleCancelUpload = useCallback(async () => {
    console.log('?? Cancel upload initiated');

    // Get current values from refs (avoids stale closure)
    const currentController = uploadAbortControllerRef.current;
    const currentFileNames = uploadingFileNamesRef.current;

    // 1. Abort the HTTP request (stops file transmission if still in progress)
    if (currentController) {
      currentController.abort();
      console.log('?? HTTP request aborted');
    }

    const userId = getUserIdSync();

    // 2. Notify backend to stop processing (sets cancellation flag)
    try {
      await fetch(`/api/v1/files/cancel-upload/${userId}`, {
        method: 'POST',
        headers: getAuthHeadersSync()
      });
      console.log('?? Backend cancellation flag set');
    } catch (e) {
      console.warn('Could not notify backend of cancellation:', e);
    }

    // 3. EXPLICITLY DELETE any files that may have been uploaded
    // This is the key fix - delete each file we were trying to upload
    if (currentFileNames.length > 0) {
      console.log(`??? Deleting ${currentFileNames.length} cancelled files:`, currentFileNames);

      for (const fileName of currentFileNames) {
        try {
          await fetch(`/api/v1/files/${userId}/${encodeURIComponent(fileName)}`, {
            method: 'DELETE',
            headers: getAuthHeadersSync()
          });
          console.log(`??? Deleted cancelled file: ${fileName}`);
        } catch (e) {
          // File might not exist yet if upload was aborted early - that's fine
          console.log(`?? Could not delete ${fileName} (may not have been uploaded yet)`);
        }
      }
    }

    // 4. Reset all upload state
    setUploading(false);
    setFixingData(false);
    setUploadAbortController(null);
    setUploadingFileNames([]);
    uploadAbortControllerRef.current = null;
    uploadingFileNamesRef.current = [];

    // 5. Refresh file list to show correct state
    await loadFiles();
    console.log('? Cancel complete - file list refreshed');
  }, []);

  // Run AutoML Training
  const handleRunAutoML = async () => {
    // Find CSV/Excel files
    const dataFiles = files.filter(f =>
      f.name.endsWith('.csv') || f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
    );

    if (dataFiles.length === 0) {
      toast.error('No data files found. Please upload a CSV or Excel file first.');
      return;
    }

    setAutomlRunning(true);

    // Create abort controller for "Stop" functionality
    const controller = new AbortController();
    setAbortController(controller);

    try {
      // Get the file from server and send to AutoML
      const userId = getUserIdSync();
      const fileResponse = await fetch(`/api/v1/files/${userId}/${dataFiles[0].name}/download`, {
        signal: controller.signal,
        headers: getAuthHeadersSync()
      });

      if (!fileResponse.ok) throw new Error('Failed to get file');

      const fileBlob = await fileResponse.blob();
      const formData = new FormData();
      formData.append('file', fileBlob, dataFiles[0].name);
      formData.append('user_id', userId);

      // Add target column if selected/detected
      if (targetColumn) {
        formData.append('target_column', targetColumn);
      }

      // Send to Training API with abort signal
      // Use Ultra AutoML endpoint for maximum accuracy
      const endpoint = ultraMode ? '/api/v2/automl/ultra_train' : '/api/v2/automl/train';
      if (ultraMode) {
        formData.append('mode', 'maximum_accuracy');
      }
      const automlResponse = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
        headers: {
          'X-User-ID': userId
        }
      });

      const automlResult = await automlResponse.json();

      if (automlResult.success) {
        // Save to localStorage with USER-SPECIFIC key for data isolation
        const userId = getUserIdSync();

        try {
          // Save full result including charts to localStorage
          // Charts are base64 encoded images, can be large but important for display
          localStorage.setItem(`mlResults_${userId}`, JSON.stringify(automlResult));
          localStorage.setItem(`hasMLResults_${userId}`, 'true');

          // Also save charts to sessionStorage as backup (in case localStorage fails due to size)
          if (automlResult.charts) {
            try {
              sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(automlResult.charts));
            } catch (chartErr) {
              console.warn("Charts too large for sessionStorage");
            }
          }
        } catch (e) {
          console.warn("Storage quota full, saving result without charts");
          // Fallback: save without charts
          const { charts, ...lightResult } = automlResult;
          localStorage.setItem(`mlResults_${userId}`, JSON.stringify(lightResult));
          localStorage.setItem(`hasMLResults_${userId}`, 'true');
        }

        // Navigate to predictions page with clean data tab
        navigate('/ml-predictions', {
          state: {
            automlResult: automlResult,
            activeTab: 'data' // Direct to "Cleaned Data" tab
          }
        });
      } else {
        toast.error(`AutoML failed: ${automlResult.detail || 'Unknown error'}`);
      }
    } catch (error: any) {
      // Handle User Stop
      if (error.name === 'AbortError') {
        return; // Silent exit on stop
      }
      console.error('AutoML error:', error);
      toast.error(`AutoML error: ${error.message}`);
    } finally {
      setAutomlRunning(false);
      setAbortController(null);
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
    const fileToDelete = files.find(f => f.id === fileId);
    const confirmed = await confirm({
      title: 'Delete File',
      message: `Are you sure you want to delete "${fileToDelete?.name || fileId}"? This will also remove it from the AI training data.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      variant: 'danger',
    });

    if (!confirmed) return;

    // Set deleting state
    setDeletingFileId(fileId);
    const controller = new AbortController();
    setDeleteAbortController(controller);

    try {
      const response = await apiService.deleteFile(fileId);
      if (response.data.success) {
        setFiles(files.filter(f => f.id !== fileId));

        // Clear cached ML results since the model may have been trained on this file
        const userId = getUserIdSync();
        localStorage.removeItem(`mlResults_${userId}`);
        localStorage.removeItem(`hasMLResults_${userId}`);
        sessionStorage.removeItem(`mlCharts_${userId}`);

        toast.deleted('File Deleted', `${fileToDelete?.name || fileId} has been removed successfully`);
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        toast.error('Delete Failed', error.response?.data?.detail || error.message);
      }
    } finally {
      setDeletingFileId(null);
      setDeleteAbortController(null);
    }
  };

  // Cancel Delete Handler
  const handleCancelDelete = () => {
    if (deleteAbortController) {
      deleteAbortController.abort();
    }
    setDeletingFileId(null);
    setDeleteAbortController(null);
  };

  const handleDeleteAll = async () => {
    const confirmed = await confirm({
      title: 'Delete All Files',
      message: 'This will permanently delete ALL your files and remove them from AI training. This action cannot be undone.',
      confirmText: 'Delete All',
      cancelText: 'Cancel',
      variant: 'danger',
      requireTypedConfirmation: 'DELETE',
    });

    if (!confirmed) return;

    try {
      const response = await apiService.deleteAllFiles();
      if (response.data.success) {
        setFiles([]);
        // Clear cached ML results when files are deleted
        const userId = getUserIdSync();
        localStorage.removeItem(`mlResults_${userId}`);
        localStorage.removeItem(`hasMLResults_${userId}`);
        sessionStorage.removeItem(`mlCharts_${userId}`);

        toast.deleted('All Files Deleted', 'Your data has been cleared successfully');
        // Dispatch event so all pages refresh their data
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      toast.error('Delete Failed', error.response?.data?.detail || error.message);
    }
  };

  const handleRebuild = async () => {
    const confirmed = await confirm({
      title: 'Retrain AI',
      message: 'This will rebuild the AI training from all your uploaded files. This may take a few minutes.',
      confirmText: 'Retrain',
      cancelText: 'Cancel',
      variant: 'info',
    });

    if (!confirmed) return;

    setUploading(true);
    try {
      const response = await apiService.rebuildIndex();
      if (response.data.success) {
        toast.success('Retrain Complete', response.data.message || 'AI has been retrained successfully');
        await loadFiles();
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      toast.error('Retrain Failed', error.response?.data?.detail || error.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (fileId: string) => {
    try {
      const userId = getUserIdSync();
      const response = await fetch(`/api/v1/files/${userId}/${fileId}/download`, {
        headers: getAuthHeadersSync()
      });
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
      toast.error(`Failed to download: ${error.message}`);
    }
  };

  const handlePreviewSheet = async () => {
    if (!sheetUrl.trim()) {
      toast.warning('Please enter a Google Sheets URL');
      return;
    }
    setImportingSheet(true);
    try {
      const response = await apiService.previewGoogleSheet(sheetUrl);
      setSheetPreview(response.data);
    } catch (error: any) {
      toast.error(`Preview failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setImportingSheet(false);
    }
  };

  const handleImportSheet = async () => {
    if (!sheetUrl.trim()) {
      toast.warning('Please enter a Google Sheets URL');
      return;
    }
    setImportingSheet(true);
    try {
      const response = await apiService.importGoogleSheet(sheetUrl);
      if (response.data.success) {
        toast.success('Google Sheet imported successfully!');
        setSheetUrl('');
        setSheetPreview(null);
        await loadFiles();
        window.dispatchEvent(new CustomEvent('filesUpdated'));
      }
    } catch (error: any) {
      toast.error(`Import failed: ${error.response?.data?.detail || error.message}`);
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
    return <File className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />;
  };

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const inputStyle = {
    backgroundColor: 'var(--glass-bg)',
    borderColor: 'var(--border-color)',
    color: 'var(--text-primary)',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Data Hub</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Upload and manage your data files</p>
        </div>
        <div className="flex flex-wrap gap-2 md:gap-3">

          {/* ?? ML Train Button - Shows when data files exist */}
          {hasDataFiles && (
            <div className="flex items-center gap-2 w-full md:w-auto">
              {/* Fast/Ultra Mode Toggle - Pill Style (matches ML Predictions) */}
              <div className="inline-flex p-1 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <button
                  onClick={() => setUltraMode(false)}
                  disabled={automlRunning}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2 ${!ultraMode
                    ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg'
                    : 'text-gray-400 hover:text-gray-200'
                    }`}
                  title="Fast Mode: 10 models, ~5-10min training (up to 500k rows)"
                >
                  <Zap className="w-4 h-4" />
                  Fast
                </button>
                <button
                  onClick={() => setUltraMode(true)}
                  disabled={automlRunning}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2 ${ultraMode
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
                    : 'text-gray-400 hover:text-gray-200'
                    }`}
                  title="Ultra Mode: 25+ models with ensembles, ~15-30min training (up to 1M rows)"
                >
                  <Sparkles className="w-4 h-4" />
                  Ultra
                </button>
              </div>

              {/* Train Button - Mode Aware */}
              <button
                onClick={handleRunAutoML}
                disabled={automlRunning}
                className={`btn-primary flex-1 md:flex-none rounded-full flex items-center justify-center gap-2 ${ultraMode
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500'
                  : 'bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500'
                  } ${automlRunning ? 'opacity-60 cursor-wait' : ''}`}
              >
                {automlRunning ? (
                  <>
                    <div className="loading-spinner" />
                    <span className="whitespace-nowrap">{ultraMode ? 'Ultra Training...' : 'Training...'}</span>
                  </>
                ) : (
                  <>
                    <Brain className="w-5 h-5" />
                    <span className="whitespace-nowrap">{ultraMode ? '?? Ultra ML' : '?? Fast ML'}</span>
                  </>
                )}
              </button>
            </div>
          )}
          <div className="flex gap-2 w-full md:w-auto">
            <button
              onClick={handleRebuild}
              className="flex-1 md:flex-none px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 font-medium hover:bg-emerald-500/20 transition-colors flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="whitespace-nowrap">?? Retrain</span>
            </button>
            <button
              onClick={handleDeleteAll}
              className="flex-1 md:flex-none px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-full text-red-400 font-medium hover:bg-red-500/20 transition-colors flex items-center justify-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              <span className="whitespace-nowrap">Delete All</span>
            </button>
          </div>
        </div>
      </motion.div >

      {/* Upload Area */}
      < motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <div
          {...getRootProps()}
          className={`card-premium hover-glow p-6 md:p-12 border-2 border-dashed transition-all cursor-pointer glass-panel ${isDragActive ? 'border-green-500 bg-green-500/5' : ''
            }`}
          style={{ borderColor: isDragActive ? '#14b8a6' : 'var(--border-color)' }}
        >
          <input {...getInputProps()} />
          <div className="text-center">
            {uploading ? (
              <>
                <Loader className="w-16 h-16 text-blue-500 mx-auto mb-4 animate-spin" />
                <p className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Uploading files...</p>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCancelUpload();
                  }}
                  className="px-6 py-2 bg-red-500/10 border border-red-500/30 rounded-full text-red-400 font-medium hover:bg-red-500/20 transition-colors flex items-center gap-2 mx-auto mt-4"
                >
                  <XCircle className="w-4 h-4" />
                  Cancel Upload
                </button>
              </>
            ) : (
              <>
                <Upload className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
                <p className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                  {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
                </p>
                <p className="mb-4" style={{ color: 'var(--text-muted)' }}>
                  or click to browse  AutoML trains automatically after upload
                </p>
                <div className="mb-4">
                  <p className="text-sm text-green-500 font-semibold mb-3">Supported Formats:</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {[
                      { name: 'CSV', color: 'bg-orange-500' },
                      { name: 'Excel (.xlsx)', color: 'bg-emerald-500' },
                    ].map((format) => (
                      <span key={format.name} className={`px-3 py-1.5 ${format.color} rounded-lg text-sm text-white font-semibold`}>
                        {format.name}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
                    ? One-click ML training  ?? 15+ auto-generated charts  ?? LLM-powered analyst
                  </p>

                  {/* Auto-Fix Toggle */}
                  <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--border-color)' }}>
                    <label className="flex items-center justify-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={autoFixEnabled}
                        onChange={(e) => setAutoFixEnabled(e.target.checked)}
                        className="w-5 h-5 rounded border-gray-600 bg-gray-700 text-amber-500 focus:ring-amber-500 cursor-pointer"
                      />
                      <span style={{ color: 'var(--text-primary)' }} className="font-medium flex items-center gap-2">
                        <Wrench className="w-4 h-4 text-amber-400" />
                        ?? Auto-Fix Data Quality
                      </span>
                      <span className="text-xs px-2 py-1 rounded-full bg-amber-500/20 text-amber-400">
                        {autoFixEnabled ? 'ON' : 'OFF'}
                      </span>
                    </label>
                    <p className="text-xs mt-2 text-center" style={{ color: 'var(--text-muted)' }}>
                      Automatically fix missing values, outliers & duplicates before upload
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </motion.div >

      {/* ?? Target Column Selection - Shows when columns detected */}
      {availableColumns.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.11 }}
          className="p-4 rounded-2xl border glass-card"
          style={{ borderColor: 'var(--border-color)' }}
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-xl bg-purple-500/20">
              <Sparkles className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                ?? Target Column (What to predict)
              </p>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                Auto-detected: <span className="text-purple-400">{targetColumn}</span>  Change if needed
              </p>
            </div>
          </div>

          <select
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            className="w-full p-3 rounded-xl border bg-transparent outline-none focus:border-purple-500 transition-all"
            style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
          >
            {availableColumns.map((col) => (
              <option key={col} value={col} style={{ backgroundColor: 'var(--bg-card)' }}>
                {col}
              </option>
            ))}
          </select>

          <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
            ?? Tip: Select the column you want the model to predict (e.g., price, category, fraud)
          </p>
        </motion.div>
      )}

      {/* ??? Multi-File Training Toggle */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12 }}
      >
        <button
          onClick={() => setShowMultiFile(!showMultiFile)}
          className={`w-full p-4 rounded-2xl border flex items-center justify-between transition-all glass-card ${showMultiFile ? 'border-emerald-500/30 bg-emerald-500/5' : 'hover:border-emerald-500/20'
            }`}
          style={{ borderColor: showMultiFile ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-color)' }}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-500/20">
              <Layers className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-left">
              <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>Multi-File Training</p>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Upload separate train and test files</p>
            </div>
          </div>
          <div className={`px-3 py-1.5 rounded-full text-sm font-medium ${showMultiFile ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-500/10 text-gray-400'
            }`}>
            {showMultiFile ? '? Expanded' : '? Click to expand'}
          </div>
        </button>

        {/* Multi-File Upload Section */}
        {showMultiFile && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4"
          >
            <MultiFileUpload
              ultraMode={ultraMode}
              onUltraModeChange={setUltraMode}
              onTrainingComplete={(result) => {
                // Navigate to ML predictions page with result
                navigate('/ml-predictions', {
                  state: { automlResult: result }
                });
              }}
            />
          </motion.div>
        )}
      </motion.div>

      {/* Google Sheets Import */}
      < motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="p-6 rounded-2xl border glass-panel"
        style={{ borderColor: 'var(--border-color)' }}
      >
        <div className="flex items-center gap-3 mb-4">
          <Table className="w-6 h-6 text-green-500" />
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Import from Google Sheets</h2>
        </div>
        <div className="flex flex-col md:flex-row gap-3 mb-4">
          <div className="flex-1 relative">
            <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Paste Google Sheets URL"
              value={sheetUrl}
              onChange={(e) => setSheetUrl(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl border focus:outline-none focus:border-green-500 transition-colors"
              style={inputStyle}
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handlePreviewSheet}
              disabled={importingSheet || !sheetUrl.trim()}
              className="flex-1 md:flex-none px-4 py-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 font-medium hover:bg-blue-500/20 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {importingSheet ? <Loader className="w-4 h-4 animate-spin" /> : <ExternalLink className="w-4 h-4" />}
              Preview
            </button>
            <button
              onClick={handleImportSheet}
              disabled={importingSheet || !sheetUrl.trim()}
              className="flex-1 md:flex-none px-6 py-3 bg-green-500 hover:bg-green-600 rounded-xl text-white font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {importingSheet ? <Loader className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              Import
            </button>
          </div>
        </div>
        {
          sheetPreview?.success && (
            <div className="p-4 rounded-xl border" style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', borderColor: 'var(--border-color)' }}>
              <div className="flex items-center justify-between mb-3">
                <span style={{ color: 'var(--text-primary)' }} className="font-medium">Preview</span>
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{sheetPreview.rowCount} rows  {sheetPreview.columnCount} columns</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {sheetPreview.columns?.slice(0, 8).map((col: string, i: number) => (
                  <span key={i} className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-medium">{col}</span>
                ))}
              </div>
            </div>
          )
        }
        <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>?? Sheet must be accessible: File ? Share ? "Anyone with the link can view"</p>
      </motion.div >

      {/* Live Streaming Connectors */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.17 }}
        className="p-6 rounded-2xl border glass-panel mb-4"
        style={{ borderColor: 'var(--border-color)' }}
      >
        <div className="flex items-center gap-3 mb-4">
          <Zap className="w-6 h-6 text-yellow-500" />
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Live Data Connections</h2>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 uppercase tracking-wider font-bold">Enterprise Beta</span>
        </div>
        <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>Connect directly to live data warehouses and streaming platforms for real-time Agentic AI analytics.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { name: 'DataVision API Push', icon: '🚀', status: 'Easiest', color: 'bg-green-500/10 text-green-400 border-green-500/20 cursor-pointer hover:bg-green-500/20', desc: 'Local/Firewalled DBs' },
              { name: 'Snowflake', icon: '❄️', status: 'Connect Live', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20 cursor-pointer hover:bg-blue-500/20', desc: 'Cloud-to-Cloud' },
              { name: 'PostgreSQL', icon: '🐘', status: 'Connect Live', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20 cursor-pointer hover:bg-indigo-500/20', desc: 'Cloud-to-Cloud' },
              { name: 'Kafka', icon: '⚡', status: 'Connect Live', color: 'bg-gray-500/10 text-gray-400 border-gray-500/20 cursor-pointer hover:bg-gray-500/20', desc: 'Cloud-to-Cloud' }
            ].map((connector) => (
              <button 
                key={connector.name} 
                onClick={() => {
                  if (connector.name === 'DataVision API Push') {
                    handleDirectApiPush();
                  } else {
                    setShowConnectionModal(connector.name);
                  }
                }}
              className={`p-4 rounded-xl border flex flex-col items-center justify-center gap-2 transition-all hover:scale-105 ${connector.color}`}
            >
              <div className="text-3xl mb-1">{connector.icon}</div>
              <div className="font-semibold text-center leading-tight">{connector.name}</div>
              <div className="text-[10px] opacity-70 mb-1">{connector.desc}</div>
              <div className="text-[10px] px-2 py-0.5 rounded bg-black/20 font-bold">{connector.status}</div>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Connection Guide Documentation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18 }}
        className="p-6 rounded-2xl border glass-panel mb-4"
        style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-card)' }}
      >
        <div className="flex items-center gap-3 mb-6 border-b pb-4" style={{ borderColor: 'var(--border-color)' }}>
          <FileText className="w-6 h-6 text-blue-500" />
          <div>
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>How to Connect Live Data</h2>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Step-by-step guide for each connector</p>
          </div>
        </div>
        
        <div className="space-y-5 text-sm" style={{ color: 'var(--text-muted)' }}>
          {/* API Push */}
          <div className="p-4 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
            <h3 className="font-bold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <span className="text-xl">🚀</span> DataVision API Push
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-600 font-bold">RECOMMENDED</span>
            </h3>
            <p className="mb-3" style={{ color: 'var(--text-muted)' }}>Stream any data to the cloud instantly. No database setup required.</p>
            <ol className="list-decimal list-inside space-y-2 ml-1">
              <li>Click the <strong style={{ color: 'var(--text-primary)' }}>DataVision API Push</strong> button above.</li>
              <li>A Live Dashboard opens with a unique Python script and your <strong style={{ color: 'var(--text-primary)' }}>secure Push URL</strong>.</li>
              <li>Copy the script, run it on your machine: <code className="px-1.5 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">python script.py</code></li>
              <li>Data streams to the dashboard in real-time. Charts and KPIs update live.</li>
            </ol>
            <p className="mt-3 text-xs italic" style={{ color: 'var(--text-muted)' }}>Best for: Quick demos, custom data sources, IoT sensors, any Python script.</p>
          </div>

          {/* PostgreSQL */}
          <div className="p-4 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
            <h3 className="font-bold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <span className="text-xl">🐘</span> PostgreSQL
            </h3>
            <ol className="list-decimal list-inside space-y-2 ml-1">
              <li>Click <strong style={{ color: 'var(--text-primary)' }}>PostgreSQL</strong> above.</li>
              <li>Enter your <strong>Host</strong> (e.g., <code className="px-1 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">localhost</code>), <strong>Database Name</strong>, <strong>Table Name</strong>, and <strong>Username</strong>.</li>
              <li>Click <strong style={{ color: 'var(--text-primary)' }}>"Generate Streaming Client"</strong>.</li>
              <li>A Python script appears with your exact details pre-filled. Copy it.</li>
              <li>Add your <strong>password</strong> to the script (line 10). Your password <em>never</em> leaves your machine.</li>
              <li>Run: <code className="px-1.5 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">python datavision_postgresql_push.py</code></li>
              <li>Click <strong style={{ color: 'var(--text-primary)' }}>"Launch Live Dashboard"</strong> to see your data streaming.</li>
            </ol>
          </div>

          {/* Snowflake */}
          <div className="p-4 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
            <h3 className="font-bold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <span className="text-xl">❄️</span> Snowflake
            </h3>
            <ol className="list-decimal list-inside space-y-2 ml-1">
              <li>Click <strong style={{ color: 'var(--text-primary)' }}>Snowflake</strong> above.</li>
              <li>Enter your <strong>Account Identifier</strong> (e.g., <code className="px-1 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">xy12345.us-east-1</code>), <strong>Database</strong>, <strong>Table</strong>, and <strong>Username</strong>.</li>
              <li>Click <strong style={{ color: 'var(--text-primary)' }}>"Generate Streaming Client"</strong>.</li>
              <li>A Python script with <code className="px-1 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">snowflake.connector</code> appears. Copy it.</li>
              <li>Add your Snowflake <strong>password</strong> locally (line 10). It never reaches the cloud.</li>
              <li>Run: <code className="px-1.5 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">python datavision_snowflake_push.py</code></li>
              <li>Click <strong style={{ color: 'var(--text-primary)' }}>"Launch Live Dashboard"</strong>.</li>
            </ol>
          </div>

          {/* Kafka */}
          <div className="p-4 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
            <h3 className="font-bold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <span className="text-xl">⚡</span> Kafka
            </h3>
            <ol className="list-decimal list-inside space-y-2 ml-1">
              <li>Click <strong style={{ color: 'var(--text-primary)' }}>Kafka</strong> above.</li>
              <li>Enter your <strong>Bootstrap Server</strong> (e.g., <code className="px-1 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">localhost:9092</code>) and <strong>Topic Name</strong>.</li>
              <li>Click <strong style={{ color: 'var(--text-primary)' }}>"Generate Streaming Client"</strong>.</li>
              <li>A Python script using <code className="px-1 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">confluent_kafka</code> appears. Copy it.</li>
              <li>Run: <code className="px-1.5 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600">python datavision_kafka_push.py</code></li>
              <li>Messages from your Kafka topic stream directly to the Live Dashboard.</li>
            </ol>
          </div>

          <div className="p-3 rounded-lg text-xs" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)' }}>
            <strong style={{ color: 'var(--text-primary)' }}>🔒 Security Note:</strong> All connectors use the API Push architecture. Your database credentials stay on your local machine — only aggregated metrics (row counts, velocity) are sent to the cloud. No raw data or passwords are transmitted.
          </div>
        </div>
      </motion.div>


      {/* Render Live Streaming Dashboard if active */}
      {activeStreamSource && activeConnectionId && (
        <LiveStreamingDashboard 
          source={activeStreamSource} 
          connectionId={activeConnectionId}
          onClose={() => {
            setActiveStreamSource(null);
            setActiveConnectionId(null);
            loadConnections();
          }} 
        />
      )}

      {/* Active Data Pipelines */}
      {activeConnections.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18 }}
          className="rounded-2xl border overflow-hidden mb-8"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
        >
          <div className="p-6 border-b flex items-center justify-between" style={{ borderColor: 'var(--border-color)' }}>
            <div className="flex items-center gap-3">
              <Zap className="w-6 h-6 text-yellow-500" />
              <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                Active Data Pipelines ({activeConnections.length})
              </h2>
            </div>
            {fetchingConnections && <Loader className="w-4 h-4 animate-spin text-gray-400" />}
          </div>
          <div className="divide-y" style={{ borderColor: 'var(--border-color)' }}>
            {activeConnections.map((conn, i) => {
              // Map source type to icon and display name
                let icon = '🐘';
                let displayName = 'PostgreSQL';
                if (conn.source_type.toLowerCase() === 'snowflake') {
                  icon = '❄️';
                  displayName = 'Snowflake';
                } else if (conn.source_type.toLowerCase() === 'kafka') {
                  icon = '⚡';
                  displayName = 'Kafka';
                } else if (conn.source_type.toLowerCase() === 'api_push') {
                  icon = '🚀';
                  displayName = 'API Push';
                }

              return (
                <motion.div
                  key={conn.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + i * 0.05 }}
                  className="p-6 flex flex-col md:flex-row md:items-center justify-between transition-colors hover:bg-white/5 gap-4"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl bg-black/20">
                      {icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-lg" style={{ color: 'var(--text-primary)' }}>
                          {conn.target_table || conn.database_name}
                        </h3>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 border border-green-500/30 font-bold flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                          LIVE
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                        <span>{displayName} Connector</span>
                        <span></span>
                        <span>DB: {conn.database_name}</span>
                        <span></span>
                        <span>Host: {conn.host}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 w-full md:w-auto">
                    <button
                      onClick={() => {
                        setActiveConnectionId(conn.id);
                        setActiveStreamSource(displayName);
                      }}
                      className="flex-1 md:flex-none px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white font-medium transition-colors flex items-center justify-center gap-2"
                    >
                      <Zap className="w-4 h-4" />
                      Re-Open Dashboard
                    </button>
                    <button
                      onClick={async () => {
                        try {
                          // Always try to remove from localStorage in case it's a legacy guest connection
                          const stored = JSON.parse(localStorage.getItem('guest_live_connections') || '[]');
                          const updated = stored.filter((c: any) => c.id !== conn.id);
                          localStorage.setItem('guest_live_connections', JSON.stringify(updated));
                          
                          try {
                            await apiService.deleteLiveConnection(conn.id);
                          } catch (apiErr: any) {
                            // If it's a 404, it just means it wasn't in the DB (e.g. it was only in localStorage)
                            if (!apiErr.response || apiErr.response.status !== 404) {
                              throw apiErr;
                            }
                          }
                          
                          toast.success('Pipeline disconnected successfully');
                          loadConnections();
                        } catch (err: any) {
                          toast.error('Failed to disconnect: ' + err.message);
                        }
                      }}
                      className="p-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors border border-red-500/20"
                      title="Disconnect Pipeline"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}


      {/* Search */}
      < motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="flex flex-col md:flex-row items-center gap-4" >
        <div className="flex-1 relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--text-muted)' }} />
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
          className="w-full md:w-auto px-4 py-3 rounded-xl border transition-colors flex items-center justify-center gap-2"
          style={{ backgroundColor: 'var(--glass-bg)', borderColor: 'var(--border-color)', color: 'var(--text-muted)' }}
        >
          <Filter className="w-5 h-5" />
          <span>Filters</span>
        </button>
      </motion.div >

      {/* Files List */}
      < motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="rounded-2xl border overflow-hidden"
        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
      >
        <div className="p-6 border-b flex items-center justify-between" style={{ borderColor: 'var(--border-color)' }}>
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            Uploaded Files ({filteredFiles.length})
          </h2>
          {files.length >= 2 && (
            <button
              onClick={() => setShowJoiner(true)}
              className="px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-all shadow-sm"
              style={{ backgroundColor: 'var(--glass-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
            >
              <Network className="w-4 h-4 text-purple-500" />
              Merge Datasets
            </button>
          )}
        </div>
        <div className="divide-y" style={{ borderColor: 'var(--border-color)' }}>
          {filteredFiles.map((file, i) => (
            <motion.div
              key={file.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 + i * 0.05 }}
              className="p-6 flex items-center justify-between transition-colors hover:bg-white/5"
            >
              <div className="flex items-center gap-4 flex-1">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
                  {getFileIcon(file.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium mb-1 truncate" style={{ color: 'var(--text-primary)' }}>{file.name}</h3>
                  <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                    <span>{formatFileSize(file.size)}</span>
                    <span></span>
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
                    <Download className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                  </button>
                  {deletingFileId === file.id ? (
                    <button
                      onClick={handleCancelDelete}
                      className="px-3 py-1 rounded-lg bg-red-500/20 border border-red-500/30 flex items-center gap-2 transition-colors hover:bg-red-500/30"
                      title="Cancel Delete"
                    >
                      <Loader className="w-4 h-4 text-red-400 animate-spin" />
                      <span className="text-sm text-red-400 font-medium">Deleting...</span>
                      <XCircle className="w-4 h-4 text-red-400" />
                    </button>
                  ) : (
                    <button onClick={() => handleDelete(file.id)} className="p-2 rounded-lg hover:bg-red-500/10 transition-colors" title="Delete">
                      <Trash2 className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
          {filteredFiles.length === 0 && (
            <div className="p-12 text-center" style={{ color: 'var(--text-muted)' }}>
              <Upload className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No files uploaded yet</p>
            </div>
          )}
        </div>
      </motion.div >

      {/* TRAINING OVERLAY - BIG ANIMATION & STOP BUTTON */}
      {
        automlRunning && (
          <div
            className="fixed inset-0 z-[100] flex items-center justify-center transition-all duration-500"
            style={{ backgroundColor: 'var(--glass-overlay)' }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              className="flex flex-col items-center max-w-lg w-full p-8 text-center"
            >
              {/* Big Animated Icon - Mode Aware Colors */}
              <div className="relative w-40 h-40 mb-8 flex items-center justify-center">
                <div className={`absolute inset-0 blur-2xl rounded-full animate-pulse ${ultraMode ? 'bg-purple-500/20' : 'bg-green-500/20'}`}></div>
                <div className={`absolute inset-0 border-4 rounded-full animate-spin ${ultraMode
                  ? 'border-t-purple-400 border-r-purple-400/50 border-b-purple-400/20 border-l-purple-400/50'
                  : 'border-t-green-400 border-r-green-400/50 border-b-green-400/20 border-l-green-400/50'
                  }`}></div>
                <div className={`absolute inset-4 border-4 rounded-full animate-spin ${ultraMode
                  ? 'border-b-pink-400 border-l-pink-400/50 border-t-pink-400/20 border-r-pink-400/50'
                  : 'border-b-blue-400 border-l-blue-400/50 border-t-blue-400/20 border-r-blue-400/50'
                  }`} style={{ animationDirection: 'reverse', animationDuration: '3s' }}></div>
                <Brain className="w-16 h-16 relative z-10 animate-pulse" style={{ color: 'var(--text-primary)' }} />
              </div>

              {/* Title - Mode Aware */}
              <h2 className={`text-4xl font-bold bg-clip-text text-transparent mb-4 ${ultraMode
                ? 'bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400'
                : 'bg-gradient-to-r from-emerald-400 via-green-400 to-cyan-400'
                }`}>
                {ultraMode ? '?? Ultra AutoML Training' : '?? Fast ML Training'}
              </h2>

              {/* Mode Details */}
              <div className={`flex items-center gap-2 mb-4 px-4 py-2 rounded-full ${ultraMode ? 'bg-purple-500/20 text-purple-300' : 'bg-green-500/20 text-green-300'
                }`}>
                {ultraMode ? (
                  <>
                    <span className="text-sm font-medium">15+ Algorithms</span>
                    <span className="opacity-50"></span>
                    <span className="text-sm font-medium">Ensembles</span>
                    <span className="opacity-50"></span>
                    <span className="text-sm font-medium">Auto-Tuning</span>
                  </>
                ) : (
                  <>
                    <span className="text-sm font-medium">10 Core Algorithms</span>
                    <span className="opacity-50"></span>
                    <span className="text-sm font-medium">Quick Training</span>
                  </>
                )}
              </div>

              {/* Progress Card */}
              <div
                className={`backdrop-blur border rounded-2xl p-6 w-full mb-8 shadow-2xl ${ultraMode ? 'border-purple-500/30' : 'border-green-500/30'
                  }`}
                style={{ backgroundColor: 'var(--bg-card)' }}
              >
                <p className="text-xl font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                  {progressMessage}
                </p>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {ultraMode
                    ? '?? Ultra mode: 3-8 minutes for maximum accuracy.'
                    : '?? Fast mode: 1-3 minutes for quick results.'
                  }
                </p>
              </div>

              <button
                onClick={async () => {
                  if (abortController) abortController.abort();
                  setAutomlRunning(false);

                  // Signal Backend to Stop Permanently
                  try {
                    const userId = getUserIdSync();
                    const formData = new FormData();
                    formData.append('user_id', userId);
                    await fetch('/api/v2/automl/stop_training', {
                      method: 'POST',
                      body: formData,
                      headers: {
                        'X-User-ID': userId
                      }
                    });
                  } catch (e) {
                    console.error("Failed to signal stop to backend", e);
                  }
                }}
                className="group px-8 py-4 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400 font-bold hover:bg-red-500/20 hover:border-red-500/50 transition-all flex items-center gap-3"
              >
                <XCircle className="w-6 h-6 group-hover:scale-110 transition-transform" />
                STOP TRAINING
              </button>
            </motion.div>
          </div>
        )
      }

      {/* Confirm Modal for Delete Operations */}
      <ConfirmModal />
      
      {/* Connection Setup Modal */}
      {showConnectionModal && (
        <ConnectionSetupModal 
          source={showConnectionModal} 
          onClose={() => setShowConnectionModal(null)} 
          onConnect={(connectionId) => {
            setShowConnectionModal(null);
            setActiveConnectionId(connectionId);
            setActiveStreamSource('DataVision API Push');
            loadConnections();
          }}
        />
      )}

      {/* Multi-Dataset Joiner Modal */}
      <MultiDatasetJoiner
        isOpen={showJoiner}
        onClose={() => setShowJoiner(false)}
        files={files}
        onSuccess={(newFileName) => {
          loadFiles();
        }}
      />

    </div>
  );
};

export default DataHub;

