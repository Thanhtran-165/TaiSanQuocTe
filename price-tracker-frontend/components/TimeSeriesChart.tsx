'use client';

import dynamic from 'next/dynamic';
import React from 'react';
import type { Data, Layout } from 'plotly.js';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function TimeSeriesChart({
  title,
  x,
  y,
  yTitle,
  ySuffix,
  color,
  valueType,
}: {
  title: string;
  x: string[];
  y: (number | null)[];
  yTitle: string;
  ySuffix?: string;
  color?: string;
  valueType?: 'vnd' | 'usd' | 'ratio';
}) {
  const filtered = x
    .map((t, i) => ({ t, v: y[i] }))
    .filter((p) => p.v !== null && p.v !== undefined);

  const fx = filtered.map((p) => p.t);
  const fy = filtered.map((p) => p.v as number);

  const mode: 'lines' | 'lines+markers' = fy.length <= 2 ? 'lines+markers' : 'lines';

  const yTickFormat =
    valueType === 'usd' ? ',.2f' : valueType === 'ratio' ? ',.2f' : '~s';

  const hoverNumberFormat =
    valueType === 'usd' ? '%{y:,.2f}' : valueType === 'ratio' ? '%{y:,.2f}' : '%{y:,.0f}';

  const singleXRange = (() => {
    if (fx.length !== 1) return undefined;
    const d = new Date(`${fx[0]}T00:00:00`);
    if (Number.isNaN(d.getTime())) return undefined;
    const ms = d.getTime();
    const pad = 3 * 24 * 60 * 60 * 1000;
    return [new Date(ms - pad).toISOString(), new Date(ms + pad).toISOString()];
  })();

  const singleYRange = (() => {
    if (fy.length !== 1) return undefined;
    const v = fy[0];
    const pad = Math.max(Math.abs(v) * 0.02, valueType === 'usd' ? 1 : valueType === 'ratio' ? 0.5 : 500_000);
    return [v - pad, v + pad];
  })();

  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="text-white font-semibold mb-3">{title}</div>
      <Plot
        data={
          [
            {
              x: fx,
              y: fy,
              type: 'scatter',
              mode,
              line: { color: color || '#60a5fa', width: 2 },
              marker: { size: 5, color: color || '#60a5fa' },
              hovertemplate: `%{x}<br>${hoverNumberFormat}${ySuffix ?? ''}<extra></extra>`,
            } satisfies Data,
          ] as Data[]
        }
        layout={
          {
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          // Give axes extra room to avoid label clipping on large numbers.
          margin: { l: 110, r: 20, t: 10, b: 65 },
          height: 320,
          xaxis: {
            type: 'date',
            showgrid: false,
            tickfont: { color: 'rgba(255,255,255,0.7)' },
            tickformat: '%d/%m/%Y',
            hoverformat: '%d/%m/%Y',
            range: singleXRange,
            automargin: true,
          },
          yaxis: {
            title: {
              text: yTitle,
              font: { color: 'rgba(255,255,255,0.7)', size: 12 },
              standoff: 14,
            },
            gridcolor: 'rgba(255,255,255,0.08)',
            tickfont: { color: 'rgba(255,255,255,0.7)' },
            tickformat: yTickFormat,
            range: singleYRange,
            automargin: true,
          },
          font: { color: 'rgba(255,255,255,0.85)' },
        } satisfies Partial<Layout>
        }
        config={{ displayModeBar: false, responsive: true }}
        useResizeHandler
        style={{ width: '100%' }}
      />
      {filtered.length === 0 && <div className="text-white/60 text-sm mt-2">Chưa có dữ liệu.</div>}
    </div>
  );
}
