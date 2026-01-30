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
    // Detect theme - app uses light-theme class for light mode, absence = dark mode
    const [isDark, setIsDark] = React.useState(!document.documentElement.classList.contains('light-theme'));
    const containerRef = useRef<HTMLDivElement>(null);

    // Watch for theme changes on html element
    useEffect(() => {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'class') {
                    setIsDark(!document.documentElement.classList.contains('light-theme'));
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class'],
        });

        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        const renderChart = async () => {
            if (!containerRef.current) return;

            try {
                // Dynamic import of Plotly
                const Plotly = await import('plotly.js-dist-min');

                // Define theme colors based on current theme
                const themeColors = isDark ? {
                    text: '#e5e7eb',      // gray-200 - light text for dark mode
                    grid: 'rgba(255,255,255,0.1)',
                    bg: 'rgba(0,0,0,0)'   // transparent
                } : {
                    text: '#1f2937',      // gray-800 - dark text for light mode
                    grid: 'rgba(0,0,0,0.1)',
                    bg: 'rgba(0,0,0,0)'   // transparent
                };

                const defaultConfig = {
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                    displaylogo: false,
                    ...config
                };

                // Merge and override layout for theme compatibility
                const enhancedLayout = {
                    ...layout,
                    autosize: true,
                    paper_bgcolor: themeColors.bg,
                    plot_bgcolor: themeColors.bg,
                    font: {
                        ...layout?.font,
                        color: themeColors.text
                    },
                    xaxis: {
                        ...layout?.xaxis,
                        gridcolor: themeColors.grid,
                        color: themeColors.text,
                        tickfont: { color: themeColors.text }
                    },
                    yaxis: {
                        ...layout?.yaxis,
                        gridcolor: themeColors.grid,
                        color: themeColors.text,
                        tickfont: { color: themeColors.text }
                    },
                    legend: {
                        ...layout?.legend,
                        font: {
                            ...layout?.legend?.font,
                            color: themeColors.text
                        }
                    },
                    title: layout?.title ? {
                        ...layout.title,
                        font: {
                            ...layout.title.font,
                            color: themeColors.text
                        }
                    } : undefined,
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
    }, [data, layout, config, isDark]);

    return (
        <div
            ref={containerRef}
            className="w-full min-h-[300px] rounded-lg overflow-hidden chart-fade-in"
            style={{ background: 'transparent' }}
        />
    );
};

export default PlotlyChart;
