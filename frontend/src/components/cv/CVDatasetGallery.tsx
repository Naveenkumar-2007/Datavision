import React, { useState } from 'react';
import { Search, Filter, Settings, Image as ImageIcon, CheckCircle2, AlertCircle, LayoutGrid, List, Trash2 } from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { useCVStore } from '@/store/cvStore';
import { CVDataset } from '@/types/cv';

const CVDatasetGallery: React.FC = () => {
  const { isDark } = useUserStore();
  const { activeDatasetId, datasets, setActiveDatasetId, deleteDataset } = useCVStore();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [isDeleting, setIsDeleting] = useState(false);
  const [visibleCount, setVisibleCount] = useState(12);
  
  const dataset = datasets.find(d => d.id === activeDatasetId);

  if (!dataset) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <ImageIcon className="w-16 h-16 mb-4 text-slate-300 dark:text-slate-700" />
        <h3 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>No Dataset Selected</h3>
        <p className="mt-2 text-sm max-w-md" style={{ color: 'var(--text-muted)' }}>
          Please select a dataset from the overview or upload a new one to view its gallery.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Search images or classes..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl border focus:ring-2 focus:ring-emerald-500/50 outline-none transition-all"
            style={{ 
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-color)',
              color: 'var(--text-primary)'
            }}
          />
        </div>
        
        <div className="flex items-center gap-2">
          <button className="p-2 rounded-xl border hover:bg-black/5 dark:hover:bg-white/5 transition-colors" style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}>
            <Filter className="w-4 h-4" />
          </button>
          <div className="flex bg-black/5 dark:bg-white/5 rounded-xl p-1 border" style={{ borderColor: 'var(--border-color)' }}>
            <button 
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-white dark:bg-slate-800 shadow-sm' : 'hover:bg-black/5 dark:hover:bg-white/5'}`}
              style={{ color: viewMode === 'grid' ? 'var(--text-primary)' : 'var(--text-muted)' }}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-white dark:bg-slate-800 shadow-sm' : 'hover:bg-black/5 dark:hover:bg-white/5'}`}
              style={{ color: viewMode === 'list' ? 'var(--text-primary)' : 'var(--text-muted)' }}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Dataset Info Bar */}
      <div className="flex flex-wrap items-center gap-4 p-4 rounded-xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Dataset:</span>
          <span className="text-sm font-bold px-2 py-1 rounded-md" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)' }}>
            {dataset.name}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Images:</span>
          <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{dataset.numImages}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Classes:</span>
          <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{dataset.numClasses}</span>
        </div>
        
        {(() => {
          const healthVal = typeof dataset.healthScore === 'object' 
            ? (dataset.healthScore?.score ?? 100) 
            : (dataset.healthScore ?? 100);
          return (
            <div className="ml-auto flex items-center gap-2">
              <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Health:</span>
              <div className="flex items-center gap-1">
                {healthVal > 80 ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                ) : healthVal > 50 ? (
                  <AlertCircle className="w-4 h-4 text-amber-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
                <span className={`text-sm font-bold ${
                  healthVal > 80 ? 'text-emerald-500' : 
                  healthVal > 50 ? 'text-amber-500' : 'text-red-500'
                }`}>
                  {healthVal}%
                </span>
              </div>
            </div>
          );
        })()}
        
        <div className="ml-auto flex items-center">
          <button 
            onClick={async () => {
              if (window.confirm(`Are you sure you want to permanently delete "${dataset.name}"? This action cannot be undone.`)) {
                setIsDeleting(true);
                await deleteDataset(dataset.id);
                setIsDeleting(false);
              }
            }}
            disabled={isDeleting}
            className={`px-4 py-2 rounded-xl border border-red-500/20 bg-red-500/10 transition-colors flex items-center gap-2 ${isDeleting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-red-500 hover:text-white text-red-500'}`} 
            title="Delete Dataset"
          >
            <Trash2 className="w-4 h-4" />
            <span className="text-sm font-bold">Delete Dataset</span>
          </button>
        </div>
      </div>

      {/* Simulated Image Grid */}
      <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-2 md:grid-cols-3 xl:grid-cols-4' : 'grid-cols-1'}`}>
        {Array.from({ length: Math.min(visibleCount, dataset.numImages) }).map((_, i) => (
          <div 
            key={i} 
            className="group relative rounded-xl overflow-hidden border aspect-square flex items-center justify-center bg-slate-100 dark:bg-slate-800 transition-all hover:border-emerald-500/50"
            style={{ borderColor: 'var(--border-color)' }}
          >
            {/* Actual dataset image */}
            <img 
              src={`/api/v1/cv/datasets/${dataset.id}/images/${i}`}
              alt={`Dataset Image ${i}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                // Fallback to placeholder if image fails to load
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement?.querySelector('.fallback-icon')?.classList.remove('hidden');
                e.currentTarget.parentElement?.querySelector('.fallback-icon')?.classList.add('flex');
              }}
            />
            
            {/* Fallback icon */}
            <div className="fallback-icon hidden absolute inset-0 items-center justify-center bg-black/5 dark:bg-white/5">
              <ImageIcon className="w-10 h-10 text-emerald-500/20" />
            </div>
            
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="absolute bottom-3 left-3 right-3 flex justify-between items-end">
                <div>
                  <span className="text-xs font-medium text-white/70">Sample_{i + 1}</span>
                  <p className="text-sm font-bold text-white truncate">
                    {dataset.classes[i % Math.max(1, dataset.classes.length)] || 'Unknown'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {dataset.numImages > visibleCount && (
        <div className="text-center pt-4">
          <button 
            onClick={() => setVisibleCount(prev => prev + 12)}
            className="px-5 py-2.5 rounded-xl border text-sm font-semibold hover:bg-emerald-500/10 hover:border-emerald-500/30 hover:text-emerald-500 transition-all flex items-center gap-2 mx-auto" 
            style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
          >
            Load More Images ({dataset.numImages - visibleCount} remaining)
          </button>
        </div>
      )}
    </div>
  );
};

export default CVDatasetGallery;
