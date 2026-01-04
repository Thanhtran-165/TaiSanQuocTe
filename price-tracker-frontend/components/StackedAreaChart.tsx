/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import dynamic from 'next/dynamic';
import React, { useMemo } from 'react';
import type { Data, Layout } from 'plotly.js';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false }) as any;

export type StackedAreaSeries = {
  name: string;
  color: string;
  values: (number | null)[];
};

export default function StackedAreaChart({
  title,
  x,
  series,
  yTitle,
}: {
  title: string;
  x: string[];
  series: StackedAreaSeries[];
  yTitle: string;
}) {
  const { data, total } = useMemo(() => {
    const n = x.length;
    const totals = new Array<number | null>(n).fill(null);
    for (let i = 0; i < n; i++) {
      let sum = 0;
      let has = false;
      for (const s of series) {
        const v = s.values[i];
        if (typeof v === 'number' && Number.isFinite(v)) {
          sum += v;
          has = true;
        }
      }
      totals[i] = has ? sum : null;
    }

    const stacked: Data[] = series.map((s, idx) => {
      const text = s.values.map((v, i) => {
        const t = totals[i];
        if (!t || !v || t <= 0) return 'N/A';
        const pct = (v / t) * 100;
        return `${pct.toFixed(1)}%`;
      });

      return {
        type: 'scatter',
        mode: 'lines',
        name: s.name,
        x,
        y: s.values,
        stackgroup: 'one',
        line: { width: 1.5, color: s.color },
        fill: idx === 0 ? 'tozeroy' : 'tonexty',
        hovertemplate:
          '%{x}<br>%{y:,.0f} VND<br>Share: %{text}<extra></extra>',
        text,
      } satisfies Data;
    });

    const totalLine: Data = {
      type: 'scatter',
      mode: 'lines',
      name: 'Total',
      x,
      y: totals,
      line: { width: 2.5, color: 'rgba(255,255,255,0.85)' },
      hovertemplate: '%{x}<br>Total: %{y:,.0f} VND<extra></extra>',
    };

    return { data: [...stacked, totalLine], total: totals };
  }, [series, x]);

  const anyPoints = total.some((v) => typeof v === 'number' && Number.isFinite(v));

  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="text-white font-semibold mb-3">{title}</div>
      <Plot
        data={data as Data[]}
        layout={
          {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 110, r: 20, t: 10, b: 65 },
            height: 420,
            legend: { orientation: 'h', y: -0.22, x: 0, font: { color: 'rgba(255,255,255,0.75)' } },
            xaxis: {
              type: 'date',
              showgrid: false,
              tickfont: { color: 'rgba(255,255,255,0.7)' },
              tickformat: '%d/%m/%Y',
              hoverformat: '%d/%m/%Y',
              automargin: true,
            },
            yaxis: {
              title: { text: yTitle, font: { color: 'rgba(255,255,255,0.7)', size: 12 }, standoff: 14 },
              gridcolor: 'rgba(255,255,255,0.08)',
              tickfont: { color: 'rgba(255,255,255,0.7)' },
              tickformat: '~s',
              ticksuffix: ' VND',
              automargin: true,
            },
            font: { color: 'rgba(255,255,255,0.85)' },
          } satisfies Partial<Layout>
        }
        config={{ displayModeBar: false, responsive: true }}
        useResizeHandler
        style={{ width: '100%' }}
      />
      {!anyPoints && <div className="text-white/60 text-sm mt-2">Chưa có dữ liệu.</div>}
    </div>
  );
}

