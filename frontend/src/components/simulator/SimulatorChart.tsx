import React from 'react';
import { useUserStore } from '@/store/userStore';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

interface SimulatorChartProps {
  data: any[];
  type?: 'line' | 'area' | 'bar';
  height?: number;
  lines?: Array<{
    dataKey: string;
    color: string;
    name?: string;
    strokeDasharray?: string;
    type?: 'monotone' | 'linear';
    dot?: boolean;
    fill?: boolean;
  }>;
  xDataKey?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  referenceLineY?: number;
  referenceLabel?: string;
  formatY?: (v: any) => string;
  formatX?: (v: any) => string;
}

const SimulatorChart: React.FC<SimulatorChartProps> = ({
  data,
  type = 'area',
  height = 300,
  lines = [],
  xDataKey = 'period',
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  referenceLineY,
  referenceLabel,
  formatY,
  formatX,
}) => {
  const { isDark } = useUserStore();

  const gridColor = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)';
  const axisColor = isDark ? '#64748b' : '#94a3b8';
  const tooltipBg = isDark ? '#1e1e2e' : '#ffffff';
  const tooltipBorder = isDark ? '#2e2e3e' : '#e2e8f0';

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div
        className="rounded-xl border p-3 shadow-xl backdrop-blur-sm"
        style={{
          background: tooltipBg,
          borderColor: tooltipBorder,
        }}
      >
        <p className="text-xs font-semibold mb-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
          {label}
        </p>
        {payload.map((entry: any, i: number) => (
          <div key={i} className="flex items-center gap-2 text-xs mb-1">
            <div className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
            <span style={{ color: isDark ? '#94a3b8' : '#64748b' }}>{entry.name}:</span>
            <span className="font-semibold" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
              {formatY ? formatY(entry.value) : entry.value?.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    );
  };

  const commonProps = {
    data,
    margin: { top: 5, right: 10, left: 5, bottom: 5 },
  };

  const commonAxisProps = {
    xAxis: (
      <XAxis
        dataKey={xDataKey}
        tick={{ fill: axisColor, fontSize: 11 }}
        axisLine={{ stroke: gridColor }}
        tickLine={false}
        tickFormatter={formatX}
      />
    ),
    yAxis: (
      <YAxis
        tick={{ fill: axisColor, fontSize: 11 }}
        axisLine={false}
        tickLine={false}
        tickFormatter={formatY || ((v: number) => v >= 10000000 ? `${(v / 10000000).toFixed(0)} Cr` : v >= 100000 ? `${(v / 100000).toFixed(0)} L` : v.toLocaleString())}
        width={55}
      />
    ),
  };

  const renderLines = () =>
    lines.map((line, i) => {
      if (type === 'area' || line.fill) {
        return (
          <Area
            key={i}
            type={line.type || 'monotone'}
            dataKey={line.dataKey}
            name={line.name || line.dataKey}
            stroke={line.color}
            fill={line.color}
            fillOpacity={0.08}
            strokeWidth={line.strokeDasharray ? 1.5 : 2.5}
            strokeDasharray={line.strokeDasharray}
            dot={line.dot !== false ? { r: 3, fill: line.color, strokeWidth: 0 } : false}
            activeDot={{ r: 5, fill: line.color, stroke: '#fff', strokeWidth: 2 }}
          />
        );
      }
      return (
        <Line
          key={i}
          type={line.type || 'monotone'}
          dataKey={line.dataKey}
          name={line.name || line.dataKey}
          stroke={line.color}
          strokeWidth={line.strokeDasharray ? 1.5 : 2.5}
          strokeDasharray={line.strokeDasharray}
          dot={line.dot !== false ? { r: 3, fill: line.color, strokeWidth: 0 } : false}
          activeDot={{ r: 5, fill: line.color, stroke: '#fff', strokeWidth: 2 }}
        />
      );
    });

  if (type === 'bar') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart {...commonProps}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />}
          {commonAxisProps.xAxis}
          {commonAxisProps.yAxis}
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          {showLegend && <Legend iconSize={8} wrapperStyle={{ fontSize: 11, color: axisColor }} />}
          {lines.map((line, i) => (
            <Bar key={i} dataKey={line.dataKey} name={line.name || line.dataKey} fill={line.color} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart {...commonProps}>
        <defs>
          {lines.map((line, i) => (
            <linearGradient key={i} id={`gradient-${line.dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={line.color} stopOpacity={0.15} />
              <stop offset="95%" stopColor={line.color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />}
        {commonAxisProps.xAxis}
        {commonAxisProps.yAxis}
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend iconSize={8} wrapperStyle={{ fontSize: 11, color: axisColor }} />}
        {referenceLineY !== undefined && (
          <ReferenceLine y={referenceLineY} stroke={isDark ? '#475569' : '#94a3b8'} strokeDasharray="5 5" label={referenceLabel} />
        )}
        {renderLines()}
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default SimulatorChart;
