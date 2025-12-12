import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Network, ZoomIn, ZoomOut, Maximize2, Download, X, Minimize2 } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: any;
}

interface GraphEdge {
  source: string;
  target: string;
  relation: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    displayed_nodes: number;
    displayed_edges: number;
    customers?: number;
    products?: number;
    invoices?: number;
  };
}

interface GraphVisualizationProps {
  userId: string;
  maxNodes?: number;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({ userId, maxNodes = 100 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fullscreenCanvasRef = useRef<HTMLCanvasElement>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [fullscreenZoom, setFullscreenZoom] = useState(1);
  const [fullscreenOffset, setFullscreenOffset] = useState({ x: 0, y: 0 });

  // Node positions for force simulation
  const nodePositions = useRef<Map<string, { x: number; y: number; vx: number; vy: number }>>(new Map());
  const fullscreenPositions = useRef<Map<string, { x: number; y: number; vx: number; vy: number }>>(new Map());

  useEffect(() => {
    fetchGraphData();
  }, [userId, maxNodes]);

  useEffect(() => {
    // Set canvas size on mount and resize
    const updateCanvasSize = () => {
      const canvas = canvasRef.current;
      if (canvas) {
        const container = canvas.parentElement;
        if (container) {
          const rect = container.getBoundingClientRect();
          canvas.width = rect.width || container.clientWidth;
          canvas.height = rect.height || Math.min(container.clientHeight, 200);

          // Redraw if we have data
          if (graphData && nodePositions.current.size > 0) {
            drawGraph(canvas, nodePositions.current, zoom, offset);
          }
        }
      }
    };

    updateCanvasSize();

    // Use ResizeObserver for dynamic resize
    const canvas = canvasRef.current;
    if (canvas?.parentElement) {
      const observer = new ResizeObserver(updateCanvasSize);
      observer.observe(canvas.parentElement);
      return () => observer.disconnect();
    }
  }, [graphData, zoom, offset]);

  const fetchGraphData = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`http://localhost:8000/api/v1/graph/${userId}/visualization?max_nodes=${maxNodes}`);
      if (!response.ok) throw new Error('Failed to fetch graph data');
      const data: GraphData = await response.json();
      setGraphData(data);
      initializeNodePositions(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      console.error('Graph fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const initializeNodePositions = (data: GraphData) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 3;

    // Initialize positions in a circle
    data.nodes.forEach((node, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      nodePositions.current.set(node.id, {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        vx: 0,
        vy: 0,
      });
    });

    startSimulation(data);
  };

  const startSimulation = (data: GraphData) => {
    let animationId: number;
    let iterations = 0;
    const maxIterations = 300;

    const simulate = () => {
      if (iterations++ > maxIterations) {
        cancelAnimationFrame(animationId);
        return;
      }

      // Force-directed layout simulation
      const nodes = data.nodes;
      const edges = data.edges;
      const k = 50; // Spring constant
      const repulsion = 5000; // Repulsion force
      const damping = 0.8;

      // Reset forces
      nodePositions.current.forEach((pos) => {
        pos.vx *= damping;
        pos.vy *= damping;
      });

      // Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const pos1 = nodePositions.current.get(nodes[i].id)!;
          const pos2 = nodePositions.current.get(nodes[j].id)!;

          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          const force = repulsion / (distance * distance);
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;

          pos1.vx -= fx;
          pos1.vy -= fy;
          pos2.vx += fx;
          pos2.vy += fy;
        }
      }

      // Attraction along edges
      edges.forEach((edge) => {
        const pos1 = nodePositions.current.get(edge.source);
        const pos2 = nodePositions.current.get(edge.target);

        if (pos1 && pos2) {
          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          const force = (distance - k) * 0.1;
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;

          pos1.vx += fx;
          pos1.vy += fy;
          pos2.vx -= fx;
          pos2.vy -= fy;
        }
      });

      // Update positions
      nodePositions.current.forEach((pos) => {
        pos.x += pos.vx;
        pos.y += pos.vy;
      });

      const canvas = canvasRef.current;
      if (canvas) {
        drawGraph(canvas, nodePositions.current, zoom, offset);
      }
      animationId = requestAnimationFrame(simulate);
    };

    simulate();
  };

  const drawGraph = (
    canvas: HTMLCanvasElement,
    positions: Map<string, { x: number; y: number; vx?: number; vy?: number }>,
    currentZoom: number,
    currentOffset: { x: number; y: number }
  ) => {
    if (!canvas || !graphData) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();

    // Apply zoom and pan
    ctx.translate(currentOffset.x, currentOffset.y);
    ctx.scale(currentZoom, currentZoom);

    // Draw edges
    ctx.strokeStyle = 'rgba(100, 116, 139, 0.3)';
    ctx.lineWidth = 1;
    graphData.edges.forEach((edge) => {
      const source = positions.get(edge.source);
      const target = positions.get(edge.target);

      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    graphData.nodes.forEach((node) => {
      const pos = positions.get(node.id);
      if (!pos) return;

      // Color by type
      let color = '#f97316'; // Default orange
      if (node.type === 'customer') color = '#3b82f6'; // Blue
      else if (node.type === 'product') color = '#10b981'; // Green
      else if (node.type === 'invoice') color = '#f59e0b'; // Orange
      else if (node.type === 'date') color = '#6b7280'; // Gray

      // Draw node circle with border
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
      ctx.fill();

      // White border for visibility
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw label with background for visibility
      const label = node.label.substring(0, 12);
      ctx.font = 'bold 11px Inter, sans-serif';
      const textWidth = ctx.measureText(label).width;

      // Label background (semi-transparent white)
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fillRect(pos.x - textWidth / 2 - 3, pos.y - 24, textWidth + 6, 14);

      // Label border
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.strokeRect(pos.x - textWidth / 2 - 3, pos.y - 24, textWidth + 6, 14);

      // Label text (dark color for visibility)
      ctx.fillStyle = '#1f2937';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(label, pos.x, pos.y - 17);
    });

    ctx.restore();
  };

  useEffect(() => {
    if (graphData && nodePositions.current.size > 0) {
      const canvas = canvasRef.current;
      if (canvas && canvas.width > 0) {
        drawGraph(canvas, nodePositions.current, zoom, offset);
      }
    }
  }, [graphData, zoom, offset]);

  // Draw fullscreen canvas when open
  useEffect(() => {
    if (isFullscreen && graphData && fullscreenPositions.current.size > 0) {
      const canvas = fullscreenCanvasRef.current;
      if (canvas && canvas.width > 0) {
        drawGraph(canvas, fullscreenPositions.current, fullscreenZoom, fullscreenOffset);
      }
    }
  }, [isFullscreen, graphData, fullscreenZoom, fullscreenOffset]);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    if (isFullscreen) {
      setFullscreenZoom((prev) => Math.max(0.1, Math.min(prev * delta, 5)));
    } else {
      setZoom((prev) => Math.max(0.1, Math.min(prev * delta, 3)));
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    if (isFullscreen) {
      setDragStart({ x: e.clientX - fullscreenOffset.x, y: e.clientY - fullscreenOffset.y });
    } else {
      setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      if (isFullscreen) {
        setFullscreenOffset({
          x: e.clientX - dragStart.x,
          y: e.clientY - dragStart.y,
        });
      } else {
        setOffset({
          x: e.clientX - dragStart.x,
          y: e.clientY - dragStart.y,
        });
      }
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => {
    if (isFullscreen) {
      setFullscreenZoom((prev) => Math.min(prev * 1.2, 5));
    } else {
      setZoom((prev) => Math.min(prev * 1.2, 3));
    }
  };

  const handleZoomOut = () => {
    if (isFullscreen) {
      setFullscreenZoom((prev) => Math.max(prev / 1.2, 0.1));
    } else {
      setZoom((prev) => Math.max(prev / 1.2, 0.1));
    }
  };

  const handleReset = () => {
    if (isFullscreen) {
      setFullscreenZoom(1);
      setFullscreenOffset({ x: 0, y: 0 });
    } else {
      setZoom(1);
      setOffset({ x: 0, y: 0 });
    }
  };

  // Open fullscreen modal
  const handleFullscreen = () => {
    setIsFullscreen(true);
    setFullscreenZoom(1);
    setFullscreenOffset({ x: 0, y: 0 });
  };

  // Initialize fullscreen canvas when modal opens
  useEffect(() => {
    if (isFullscreen && graphData) {
      // Small delay to ensure canvas is mounted
      const timer = setTimeout(() => {
        initializeFullscreenPositions(graphData);
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [isFullscreen, graphData]);

  const initializeFullscreenPositions = (data: GraphData) => {
    const canvas = fullscreenCanvasRef.current;
    if (!canvas) {
      return;
    }

    // Set canvas to full window size
    const width = window.innerWidth - 48;
    const height = window.innerHeight - 180;
    canvas.width = width;
    canvas.height = height;

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 3;

    // Clear and initialize positions
    fullscreenPositions.current.clear();

    // Initialize positions in a circle with more spread
    data.nodes.forEach((node, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      fullscreenPositions.current.set(node.id, {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        vx: 0,
        vy: 0,
      });
    });

    // Run simulation
    runFullscreenSimulation(data);
  };

  const runFullscreenSimulation = (data: GraphData) => {
    let iterations = 0;
    const maxIterations = 200;

    const simulate = () => {
      const canvas = fullscreenCanvasRef.current;

      if (iterations++ > maxIterations || !canvas) {
        // Final draw
        if (canvas) {
          drawGraph(canvas, fullscreenPositions.current, fullscreenZoom, fullscreenOffset);
        }
        return;
      }

      const nodes = data.nodes;
      const edges = data.edges;
      const k = 100;
      const repulsion = 20000;
      const damping = 0.85;

      fullscreenPositions.current.forEach((pos) => {
        pos.vx *= damping;
        pos.vy *= damping;
      });

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const pos1 = fullscreenPositions.current.get(nodes[i].id)!;
          const pos2 = fullscreenPositions.current.get(nodes[j].id)!;

          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          const force = repulsion / (distance * distance);
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;

          pos1.vx -= fx;
          pos1.vy -= fy;
          pos2.vx += fx;
          pos2.vy += fy;
        }
      }

      edges.forEach((edge) => {
        const pos1 = fullscreenPositions.current.get(edge.source);
        const pos2 = fullscreenPositions.current.get(edge.target);

        if (pos1 && pos2) {
          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          const force = (distance - k) * 0.1;
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;

          pos1.vx += fx;
          pos1.vy += fy;
          pos2.vx -= fx;
          pos2.vy -= fy;
        }
      });

      fullscreenPositions.current.forEach((pos) => {
        pos.x += pos.vx;
        pos.y += pos.vy;
      });

      drawGraph(canvas, fullscreenPositions.current, fullscreenZoom, fullscreenOffset);
      requestAnimationFrame(simulate);
    };

    simulate();
  };

  const handleCloseFullscreen = () => {
    setIsFullscreen(false);
    fullscreenPositions.current.clear();
  };

  // ESC key to close fullscreen
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen) {
        handleCloseFullscreen();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  // Download high-quality image
  const handleDownload = () => {
    if (!graphData) return;

    // Create a high-res canvas for download (1920x1080)
    const downloadCanvas = document.createElement('canvas');
    downloadCanvas.width = 1920;
    downloadCanvas.height = 1080;

    const ctx = downloadCanvas.getContext('2d');
    if (!ctx) return;

    // White background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, downloadCanvas.width, downloadCanvas.height);

    // Create positions for download canvas
    const downloadPositions = new Map<string, { x: number; y: number }>();
    const centerX = downloadCanvas.width / 2;
    const centerY = downloadCanvas.height / 2;
    const radius = Math.min(downloadCanvas.width, downloadCanvas.height) / 2.5;

    graphData.nodes.forEach((node, i) => {
      const angle = (i / graphData.nodes.length) * 2 * Math.PI;
      downloadPositions.set(node.id, {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      });
    });

    // Run quick simulation
    for (let iter = 0; iter < 100; iter++) {
      const k = 100;
      const repulsion = 20000;

      for (let i = 0; i < graphData.nodes.length; i++) {
        for (let j = i + 1; j < graphData.nodes.length; j++) {
          const pos1 = downloadPositions.get(graphData.nodes[i].id)!;
          const pos2 = downloadPositions.get(graphData.nodes[j].id)!;

          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          const force = repulsion / (distance * distance);
          pos1.x -= (dx / distance) * force * 0.01;
          pos1.y -= (dy / distance) * force * 0.01;
          pos2.x += (dx / distance) * force * 0.01;
          pos2.y += (dy / distance) * force * 0.01;
        }
      }

      graphData.edges.forEach((edge) => {
        const pos1 = downloadPositions.get(edge.source);
        const pos2 = downloadPositions.get(edge.target);

        if (pos1 && pos2) {
          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          const force = (distance - k) * 0.005;
          pos1.x += (dx / distance) * force;
          pos1.y += (dy / distance) * force;
          pos2.x -= (dx / distance) * force;
          pos2.y -= (dy / distance) * force;
        }
      });
    }

    // Draw edges
    ctx.strokeStyle = 'rgba(100, 116, 139, 0.4)';
    ctx.lineWidth = 2;
    graphData.edges.forEach((edge) => {
      const source = downloadPositions.get(edge.source);
      const target = downloadPositions.get(edge.target);

      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    graphData.nodes.forEach((node) => {
      const pos = downloadPositions.get(node.id);
      if (!pos) return;

      let color = '#8b5cf6';
      if (node.type === 'customer') color = '#3b82f6';
      else if (node.type === 'product') color = '#10b981';
      else if (node.type === 'invoice') color = '#f59e0b';
      else if (node.type === 'date') color = '#6b7280';

      // Node circle
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 16, 0, 2 * Math.PI);
      ctx.fill();

      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Label
      const label = node.label.substring(0, 15);
      ctx.font = 'bold 14px Inter, sans-serif';
      const textWidth = ctx.measureText(label).width;

      ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
      ctx.fillRect(pos.x - textWidth / 2 - 6, pos.y - 40, textWidth + 12, 22);

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(pos.x - textWidth / 2 - 6, pos.y - 40, textWidth + 12, 22);

      ctx.fillStyle = '#1f2937';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(label, pos.x, pos.y - 29);
    });

    // Add title
    ctx.fillStyle = '#1f2937';
    ctx.font = 'bold 24px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Knowledge Graph', 30, 40);

    ctx.font = '16px Inter, sans-serif';
    ctx.fillStyle = '#6b7280';
    ctx.fillText(`${graphData.stats.total_nodes} nodes • ${graphData.stats.total_edges} relationships`, 30, 70);

    // Add legend
    const legendY = downloadCanvas.height - 40;
    const legendItems = [
      { color: '#3b82f6', label: `Customers (${graphData.stats.customers || 0})` },
      { color: '#10b981', label: `Products (${graphData.stats.products || 0})` },
      { color: '#f59e0b', label: `Invoices (${graphData.stats.invoices || 0})` },
      { color: '#6b7280', label: 'Other' },
    ];

    let legendX = 30;
    legendItems.forEach((item) => {
      ctx.fillStyle = item.color;
      ctx.beginPath();
      ctx.arc(legendX, legendY, 8, 0, 2 * Math.PI);
      ctx.fill();

      ctx.fillStyle = '#374151';
      ctx.font = '14px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(item.label, legendX + 15, legendY + 5);
      legendX += ctx.measureText(item.label).width + 50;
    });

    // Download
    const link = document.createElement('a');
    link.download = `knowledge-graph-${userId}-${new Date().toISOString().split('T')[0]}.png`;
    link.href = downloadCanvas.toDataURL('image/png', 1.0);
    link.click();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 bg-white rounded-xl border border-gray-200">
        <div className="text-center">
          <Network className="w-12 h-12 text-primary-500 animate-pulse mx-auto mb-3" />
          <p className="text-gray-500">Loading knowledge graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-white rounded-xl border border-gray-200">
        <div className="text-center">
          <Network className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-red-500">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
          <div className="flex items-center space-x-3">
            <Network className="w-5 h-5 text-primary-500" />
            <div>
              <h3 className="text-gray-800 font-semibold">Knowledge Graph Network</h3>
              <p className="text-xs text-gray-500">
                {graphData?.stats.displayed_nodes} nodes, {graphData?.stats.displayed_edges} edges
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleZoomIn}
              className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 hover:text-gray-800 transition-all"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 hover:text-gray-800 transition-all"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={handleFullscreen}
              className="p-2 bg-primary-500 hover:bg-primary-600 rounded-lg text-white transition-all"
              title="Full Screen View"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleDownload}
              className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 hover:text-gray-800 transition-all"
              title="Download High-Quality PNG"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Canvas */}
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={800}
            height={500}
            className="w-full bg-white cursor-move"
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
        </div>

        {/* Legend */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-gray-600">Customers ({graphData?.stats.customers || 0})</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="text-gray-600">Products ({graphData?.stats.products || 0})</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                <span className="text-gray-600">Invoices ({graphData?.stats.invoices || 0})</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                <span className="text-gray-600">Other</span>
              </div>
            </div>
            <span className="text-gray-500">Scroll to zoom • Drag to pan</span>
          </div>
        </div>
      </motion.div>

      {/* Fullscreen Modal */}
      <AnimatePresence>
        {isFullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm"
            onClick={(e) => e.target === e.currentTarget && handleCloseFullscreen()}
          >
            <div className="w-full h-full flex flex-col p-6">
              {/* Fullscreen Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <Network className="w-8 h-8 text-primary-400" />
                  <div>
                    <h2 className="text-2xl font-bold text-white">Knowledge Graph</h2>
                    <p className="text-gray-400">
                      {graphData?.stats.total_nodes} nodes • {graphData?.stats.total_edges} relationships
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleZoomIn}
                    className="p-3 bg-white/10 hover:bg-white/20 rounded-xl text-white transition-all"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-5 h-5" />
                  </button>
                  <button
                    onClick={handleZoomOut}
                    className="p-3 bg-white/10 hover:bg-white/20 rounded-xl text-white transition-all"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-5 h-5" />
                  </button>
                  <button
                    onClick={handleReset}
                    className="p-3 bg-white/10 hover:bg-white/20 rounded-xl text-white transition-all"
                    title="Reset View"
                  >
                    <Minimize2 className="w-5 h-5" />
                  </button>
                  <button
                    onClick={handleDownload}
                    className="p-3 bg-primary-500 hover:bg-primary-600 rounded-xl text-white transition-all flex items-center space-x-2"
                    title="Download High-Quality PNG"
                  >
                    <Download className="w-5 h-5" />
                    <span>Download</span>
                  </button>
                  <button
                    onClick={handleCloseFullscreen}
                    className="p-3 bg-red-500/80 hover:bg-red-500 rounded-xl text-white transition-all"
                    title="Close"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Fullscreen Canvas */}
              <div className="flex-1 bg-white rounded-2xl overflow-hidden shadow-2xl">
                <canvas
                  ref={fullscreenCanvasRef}
                  className="w-full h-full cursor-move"
                  onWheel={handleWheel}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                />
              </div>

              {/* Fullscreen Legend */}
              <div className="mt-4 flex items-center justify-center space-x-8 text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full bg-blue-500"></div>
                  <span className="text-white">Customers ({graphData?.stats.customers || 0})</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full bg-green-500"></div>
                  <span className="text-white">Products ({graphData?.stats.products || 0})</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full bg-orange-500"></div>
                  <span className="text-white">Invoices ({graphData?.stats.invoices || 0})</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full bg-gray-500"></div>
                  <span className="text-white">Other</span>
                </div>
                <span className="text-gray-400 ml-4">Scroll to zoom • Drag to pan • ESC to close</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default GraphVisualization;
