/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import dynamic from 'next/dynamic';
import React from 'react';
import type { Data, Layout } from 'plotly.js';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false }) as any;

export default function BarChart({
  title,
  labels,
  values,
  xTitle,
  valueType,
}: {
  title: string;
  labels: string[];
  values: (number | null)[];
  xTitle: string;
  valueType?: 'usd' | 'number';
}) {
  const items = labels
    .map((label, i) => ({ label, v: values[i] }))
    .filter((x) => x.v !== null && x.v !== undefined) as { label: string; v: number }[];

  const y = items.map((x) => x.label).reverse();
  const x = items.map((x) => x.v).reverse();

  const xTickFormat = valueType === 'usd' ? '~s' : ',.0f';
  const hover = valueType === 'usd' ? '%{x:,.2f} USD' : '%{x:,.2f}';

  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="text-white font-semibold mb-3">{title}</div>
      <Plot
        data={
          [
            {
              type: 'bar',
              orientation: 'h',
              x,
              y,
              marker: { color: '#60a5fa' },
              hovertemplate: `%{y}<br>${hover}<extra></extra>`,
            } satisfies Data,
          ] as Data[]
        }
        layout={
          {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 160, r: 20, t: 10, b: 55 },
            height: 520,
            xaxis: {
              title: { text: xTitle, font: { color: 'rgba(255,255,255,0.7)', size: 12 } },
              gridcolor: 'rgba(255,255,255,0.08)',
              tickfont: { color: 'rgba(255,255,255,0.7)' },
              tickformat: xTickFormat,
              automargin: true,
            },
            yaxis: {
              tickfont: { color: 'rgba(255,255,255,0.7)' },
              automargin: true,
            },
            font: { color: 'rgba(255,255,255,0.85)' },
          } satisfies Partial<Layout>
        }
        config={{ displayModeBar: false, responsive: true }}
        useResizeHandler
        style={{ width: '100%' }}
      />
      {items.length === 0 && <div className="text-white/60 text-sm mt-2">Chưa có dữ liệu.</div>}
    </div>
  );
}
