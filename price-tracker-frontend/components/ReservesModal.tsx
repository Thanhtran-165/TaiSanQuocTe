/**
 * ReservesModal Component
 * Shows all-time reserves series for a selected country.
 */

'use client';

import React, { useMemo, useState } from 'react';
import { X } from 'lucide-react';
import TimeSeriesChart from '@/components/TimeSeriesChart';
import type { ReservesCountryMeta, ReservesCountryRow, ReservesKind } from '@/lib/api';

function formatCompactUsd(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  const abs = Math.abs(value);
  const fmt = (n: number, suffix: string) => `${n.toFixed(2).replace(/\.00$/, '')}${suffix}`;
  if (abs >= 1e12) return fmt(value / 1e12, 'T');
  if (abs >= 1e9) return fmt(value / 1e9, 'B');
  if (abs >= 1e6) return fmt(value / 1e6, 'M');
  if (abs >= 1e3) return fmt(value / 1e3, 'K');
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
}

export default function ReservesModal({
  isOpen,
  onClose,
  meta,
  rows,
  defaultKind,
}: {
  isOpen: boolean;
  onClose: () => void;
  meta: ReservesCountryMeta | null;
  rows: ReservesCountryRow[];
  defaultKind: ReservesKind;
}) {
  const [kind, setKind] = useState<ReservesKind>(defaultKind);

  const { x, y, title } = useMemo(() => {
    const x = (rows || []).map((r) => String(r.year));
    const y = (rows || []).map((r) => {
      if (kind === 'gold') return r.gold_value_usd_inferred;
      if (kind === 'non_gold') return r.non_gold_reserves_usd;
      return r.total_reserves_usd;
    });
    const title =
      kind === 'gold'
        ? 'Dự trữ vàng (USD)'
        : kind === 'non_gold'
          ? 'Dự trữ không bao gồm vàng (USD)'
          : 'Tổng dự trữ (USD)';
    return { x, y, title };
  }, [rows, kind]);

  if (!isOpen) return null;

  const last = rows && rows.length > 0 ? rows[rows.length - 1] : null;
  const lastValue =
    kind === 'gold'
      ? last?.gold_value_usd_inferred ?? null
      : kind === 'non_gold'
        ? last?.non_gold_reserves_usd ?? null
        : last?.total_reserves_usd ?? null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-panel rounded-2xl max-w-5xl w-full max-h-[85vh] overflow-hidden flex flex-col">
        <div className="flex items-start justify-between p-6 border-b border-white/10 gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-white truncate">
                {meta?.country_name || meta?.iso2 || 'Dự trữ'}
              </h2>
              <span className="text-white/60 text-sm">{meta?.iso2}</span>
            </div>
            {meta?.year_range && (
              <div className="text-white/60 text-sm mt-1">
                {meta.year_range.start} – {meta.year_range.end}
                {meta.note ? <span className="ml-2 text-white/50">• {meta.note}</span> : null}
              </div>
            )}
            <div className="text-white/70 text-sm mt-2">
              Giá trị gần nhất: <span className="text-white font-semibold">{formatCompactUsd(lastValue)} USD</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value as ReservesKind)}
              className="glass-input px-4 py-2 rounded-lg"
            >
              <option value="gold">Dự trữ vàng</option>
              <option value="non_gold">Không bao gồm vàng</option>
              <option value="total">Tổng dự trữ</option>
            </select>

            <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/10 transition-colors">
              <X className="w-5 h-5 icon-arrow" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <TimeSeriesChart
            title={title}
            x={x}
            y={y}
            yTitle="USD"
            ySuffix=" USD"
            valueType="vnd"
          />
          <div className="text-white/50 text-xs mt-3">
            Nguồn: World Bank WDI (FI.RES.TOTL.CD, FI.RES.XGLD.CD) • Vàng suy luận = Tổng − Không bao gồm vàng
          </div>
        </div>
      </div>
    </div>
  );
}

