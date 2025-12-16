import React, { useEffect, useRef } from 'react';

interface PlotlyChartProps {
    data: any[];
    layout: any;
    config?: any;
}

/**
 * PlotlyChart component - Renders interactive Plotly charts
 * Uses dynamic import to avoid SSR issues
 */
const PlotlyChart: React.FC<PlotlyChartProps> = ({ data, layout, config }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const renderChart = async () => {
            if (!containerRef.current) return;

            try {
                // Dynamic import of Plotly
                const Plotly = await import('plotly.js-dist-min');

                const defaultConfig = {
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                    displaylogo: false,
                    ...config
                };

                const enhancedLayout = {
                    ...layout,
                    autosize: true,
                    margin: { l: 50, r: 30, t: 40, b: 40, ...layout?.margin },
                };

                Plotly.default.newPlot(
                    containerRef.current,
                    data,
                    enhancedLayout,
                    defaultConfig
                );

                // Cleanup on unmount
                return () => {
                    if (containerRef.current) {
                        Plotly.default.purge(containerRef.current);
                    }
                };
            } catch (error) {
                console.error('Failed to render Plotly chart:', error);
            }
        };

        renderChart();
    }, [data, layout, config]);

    return (
        <div
            ref={containerRef}
            className="w-full min-h-[300px] rounded-lg overflow-hidden"
            style={{ background: 'transparent' }}
        />
    );
};

export default PlotlyChart;
