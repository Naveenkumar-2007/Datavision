/**
 * Premium Charts Component
 * ========================
 * Advanced chart types using D3.js and Plotly.
 * 
 * Chart Types:
 * - Sankey diagrams (flow visualization)
 * - Treemaps (hierarchical data)
 * - Sunburst (multi-level pie)
 * - Network graphs (relationships)
 * - Waterfall (cumulative effect)
 * - Funnel (conversion flows)
 * - Radar/Spider (multi-dimensional)
 * - Heatmaps (density)
 * - Bubble charts (3D scatter)
 */

import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Data, Layout } from 'plotly.js';

// Theme colors for dark/light mode
const getThemeColors = (isDark: boolean) => ({
    background: isDark ? 'rgba(0,0,0,0)' : 'rgba(255,255,255,0)',
    text: isDark ? '#e2e8f0' : '#2d3748',
    grid: isDark ? '#2d3748' : '#e2e8f0',
    primary: ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'],
    accent: ['#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6'],
});

interface PremiumChartProps {
    type: string;
    data: any[];
    title?: string;
    isDark?: boolean;
    width?: number;
    height?: number;
    config?: Record<string, any>;
}

export const PremiumChart: React.FC<PremiumChartProps> = ({
    type,
    data,
    title = '',
    isDark = true,
    width = 400,
    height = 300,
    config = {}
}) => {
    const theme = getThemeColors(isDark);

    const { plotData, layout } = useMemo(() => {
        switch (type) {
            case 'sankey':
                return createSankeyChart(data, theme, config);
            case 'treemap':
                return createTreemapChart(data, theme, config);
            case 'sunburst':
                return createSunburstChart(data, theme, config);
            case 'waterfall':
                return createWaterfallChart(data, theme, config);
            case 'funnel':
                return createFunnelChart(data, theme, config);
            case 'radar':
                return createRadarChart(data, theme, config);
            case 'heatmap':
                return createHeatmapChart(data, theme, config);
            case 'bubble':
                return createBubbleChart(data, theme, config);
            case 'network':
                return createNetworkChart(data, theme, config);
            default:
                return createDefaultChart(data, theme, config);
        }
    }, [type, data, isDark, config]);

    const baseLayout: Partial<Layout> = {
        title: {
            text: title,
            font: { color: theme.text, size: 14, family: 'Inter, sans-serif' }
        },
        paper_bgcolor: theme.background,
        plot_bgcolor: theme.background,
        font: { color: theme.text, family: 'Inter, sans-serif' },
        margin: { t: 40, r: 20, b: 40, l: 40 },
        showlegend: true,
        legend: { font: { color: theme.text } },
        ...layout
    };

    return (
        <Plot
            data={plotData}
            layout={baseLayout as Layout}
            config={{
                displayModeBar: false,
                responsive: true
            }}
            style={{ width: '100%', height: '100%' }}
        />
    );
};


// ============ SANKEY DIAGRAM ============
function createSankeyChart(data: any[], theme: any, config: any) {
    // Extract nodes and links from data
    const nodes = config.nodes || extractSankeyNodes(data);
    const links = config.links || extractSankeyLinks(data);

    const plotData: Data[] = [{
        type: 'sankey',
        orientation: 'h',
        node: {
            pad: 15,
            thickness: 20,
            line: { color: theme.grid, width: 0.5 },
            label: nodes.map((n: any) => n.name),
            color: theme.primary
        },
        link: {
            source: links.map((l: any) => l.source),
            target: links.map((l: any) => l.target),
            value: links.map((l: any) => l.value),
            color: links.map((_: any, i: number) =>
                `rgba(${hexToRgb(theme.accent[i % 5])}, 0.4)`
            )
        }
    }];

    return { plotData, layout: {} };
}


// ============ TREEMAP ============
function createTreemapChart(data: any[], theme: any, config: any) {
    const { labels, parents, values } = extractTreemapData(data, config);

    const plotData: Data[] = [{
        type: 'treemap',
        labels,
        parents,
        values,
        textinfo: 'label+value+percent parent',
        marker: {
            colors: values.map((_: any, i: number) => theme.primary[i % 5]),
            line: { width: 2, color: theme.background }
        },
        pathbar: { visible: true }
    }];

    return { plotData, layout: {} };
}


// ============ SUNBURST ============
function createSunburstChart(data: any[], theme: any, config: any) {
    const { labels, parents, values } = extractTreemapData(data, config);

    const plotData: Data[] = [{
        type: 'sunburst',
        labels,
        parents,
        values,
        branchvalues: 'total',
        marker: {
            colors: values.map((_: any, i: number) => theme.accent[i % 5]),
            line: { width: 1, color: theme.background }
        }
    }];

    return { plotData, layout: {} };
}


// ============ WATERFALL ============
function createWaterfallChart(data: any[], theme: any, config: any) {
    const xKey = config.x || Object.keys(data[0])[0];
    const yKey = config.y || Object.keys(data[0])[1];

    const plotData: Data[] = [{
        type: 'waterfall',
        orientation: 'v',
        x: data.map(d => d[xKey]),
        y: data.map(d => d[yKey]),
        textposition: 'outside',
        connector: {
            line: { color: theme.grid, width: 2, dash: 'dot' }
        },
        increasing: { marker: { color: '#10b981' } },
        decreasing: { marker: { color: '#ef4444' } },
        totals: { marker: { color: theme.primary[0] } }
    }];

    return {
        plotData,
        layout: {
            xaxis: { tickfont: { color: theme.text } },
            yaxis: { tickfont: { color: theme.text } }
        }
    };
}


// ============ FUNNEL ============
function createFunnelChart(data: any[], theme: any, config: any) {
    const xKey = config.x || Object.keys(data[0])[0];
    const yKey = config.y || Object.keys(data[0])[1];

    const plotData: Data[] = [{
        type: 'funnel',
        y: data.map(d => d[xKey]),
        x: data.map(d => d[yKey]),
        textinfo: 'value+percent initial',
        marker: {
            color: data.map((_, i) => theme.primary[i % 5]),
            line: { color: theme.background, width: 2 }
        },
        connector: { line: { color: theme.grid, width: 2 } }
    }];

    return { plotData, layout: {} };
}


// ============ RADAR / SPIDER ============
function createRadarChart(data: any[], theme: any, config: any) {
    const categories = config.categories || Object.keys(data[0]).filter(k => typeof data[0][k] === 'number');

    const plotData: Data[] = data.slice(0, 3).map((row, idx) => ({
        type: 'scatterpolar',
        r: categories.map((cat: string) => row[cat] || 0),
        theta: categories,
        fill: 'toself',
        name: row.name || `Series ${idx + 1}`,
        line: { color: theme.primary[idx % 5] },
        fillcolor: `rgba(${hexToRgb(theme.primary[idx % 5])}, 0.2)`
    }));

    return {
        plotData,
        layout: {
            polar: {
                radialaxis: {
                    visible: true,
                    tickfont: { color: theme.text }
                },
                angularaxis: {
                    tickfont: { color: theme.text }
                },
                bgcolor: theme.background
            }
        }
    };
}


// ============ HEATMAP ============
function createHeatmapChart(data: any[], theme: any, config: any) {
    const xKey = config.x || Object.keys(data[0])[0];
    const yKey = config.y || Object.keys(data[0])[1];
    const zKey = config.z || Object.keys(data[0])[2];

    // Create z matrix
    const xVals = [...new Set(data.map(d => d[xKey]))];
    const yVals = [...new Set(data.map(d => d[yKey]))];

    const zMatrix = yVals.map(y =>
        xVals.map(x => {
            const point = data.find(d => d[xKey] === x && d[yKey] === y);
            return point ? point[zKey] : 0;
        })
    );

    const plotData: Data[] = [{
        type: 'heatmap',
        z: zMatrix,
        x: xVals,
        y: yVals,
        colorscale: [
            [0, theme.primary[4]],
            [0.5, theme.primary[2]],
            [1, theme.primary[0]]
        ],
        showscale: true
    }];

    return {
        plotData,
        layout: {
            xaxis: { tickfont: { color: theme.text } },
            yaxis: { tickfont: { color: theme.text } }
        }
    };
}


// ============ BUBBLE CHART ============
function createBubbleChart(data: any[], theme: any, config: any) {
    const xKey = config.x || Object.keys(data[0])[0];
    const yKey = config.y || Object.keys(data[0])[1];
    const sizeKey = config.size || Object.keys(data[0])[2];

    const plotData: Data[] = [{
        type: 'scatter',
        mode: 'markers',
        x: data.map(d => d[xKey]),
        y: data.map(d => d[yKey]),
        marker: {
            size: data.map(d => Math.sqrt(d[sizeKey] || 10) * 3),
            color: data.map((_, i) => theme.primary[i % 5]),
            opacity: 0.7,
            line: { color: theme.text, width: 1 }
        },
        text: data.map(d => d.name || d[xKey])
    }];

    return {
        plotData,
        layout: {
            xaxis: { tickfont: { color: theme.text }, gridcolor: theme.grid },
            yaxis: { tickfont: { color: theme.text }, gridcolor: theme.grid }
        }
    };
}


// ============ NETWORK GRAPH ============
function createNetworkChart(data: any[], theme: any, config: any) {
    const nodes = config.nodes || data;
    const edges = config.edges || [];

    // Simple force layout simulation
    const nodePositions = nodes.map((_: any, i: number) => ({
        x: Math.cos(2 * Math.PI * i / nodes.length) * 0.8,
        y: Math.sin(2 * Math.PI * i / nodes.length) * 0.8
    }));

    // Edge traces
    const edgeTraces: Data = {
        type: 'scatter',
        mode: 'lines',
        x: [],
        y: [],
        line: { color: theme.grid, width: 1 },
        hoverinfo: 'none'
    };

    edges.forEach((edge: any) => {
        const src = nodePositions[edge.source];
        const tgt = nodePositions[edge.target];
        (edgeTraces.x as number[]).push(src.x, tgt.x, null);
        (edgeTraces.y as number[]).push(src.y, tgt.y, null);
    });

    // Node trace
    const nodeTrace: Data = {
        type: 'scatter',
        mode: 'markers+text',
        x: nodePositions.map((p: any) => p.x),
        y: nodePositions.map((p: any) => p.y),
        text: nodes.map((n: any) => n.name || n.id),
        textposition: 'top center',
        marker: {
            size: nodes.map((n: any) => (n.size || 10) + 10),
            color: theme.primary,
            line: { color: theme.text, width: 2 }
        }
    };

    return {
        plotData: [edgeTraces, nodeTrace],
        layout: {
            xaxis: { showgrid: false, zeroline: false, showticklabels: false },
            yaxis: { showgrid: false, zeroline: false, showticklabels: false }
        }
    };
}


// ============ DEFAULT CHART ============
function createDefaultChart(data: any[], theme: any, config: any) {
    const xKey = config.x || Object.keys(data[0])[0];
    const yKey = config.y || Object.keys(data[0])[1];

    const plotData: Data[] = [{
        type: 'bar',
        x: data.map(d => d[xKey]),
        y: data.map(d => d[yKey]),
        marker: { color: theme.primary[0] }
    }];

    return { plotData, layout: {} };
}


// ============ HELPER FUNCTIONS ============

function extractSankeyNodes(data: any[]) {
    const nodeSet = new Set<string>();
    data.forEach(d => {
        if (d.source) nodeSet.add(d.source);
        if (d.target) nodeSet.add(d.target);
    });
    return Array.from(nodeSet).map(name => ({ name }));
}

function extractSankeyLinks(data: any[]) {
    const nodes = extractSankeyNodes(data);
    const nodeIndex = new Map(nodes.map((n, i) => [n.name, i]));

    return data
        .filter(d => d.source && d.target && d.value)
        .map(d => ({
            source: nodeIndex.get(d.source),
            target: nodeIndex.get(d.target),
            value: d.value
        }));
}

function extractTreemapData(data: any[], config: any) {
    const labelKey = config.label || Object.keys(data[0])[0];
    const valueKey = config.value || Object.keys(data[0])[1];
    const parentKey = config.parent || 'parent';

    const labels = ['All', ...data.map(d => d[labelKey])];
    const parents = ['', ...data.map(d => d[parentKey] || 'All')];
    const values = [0, ...data.map(d => d[valueKey])];

    return { labels, parents, values };
}

function hexToRgb(hex: string): string {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (result) {
        return `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`;
    }
    return '99, 102, 241'; // Default indigo
}

export default PremiumChart;
