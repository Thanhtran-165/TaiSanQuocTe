/**
 * WgcReservesModal Component
 * Shows WGC latest snapshot and (optional) WDI all-time series for the mapped ISO2 country.
 */

'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { X } from 'lucide-react';
import TimeSeriesChart from '@/components/TimeSeriesChart';
import { api, ReservesCountryMeta, ReservesCountryRow, WgcGoldRow } from '@/lib/api';
import { formatCompactUsd, formatPercent, formatTonnes } from '@/lib/format';

export default function WgcReservesModal({
  isOpen,
  onClose,
  row,
}: {
  isOpen: boolean;
  onClose: () => void;
  row: WgcGoldRow | null;
}) {
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState<ReservesCountryMeta | null>(null);
  const [series, setSeries] = useState<ReservesCountryRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setError(null);
    setMeta(null);
    setSeries([]);

    const iso2 = row?.iso2 || null;
    if (!iso2) return;

    setLoading(true);
    api
      .getReservesCountry(iso2)
      .then((resp) => {
        if (resp.success) {
          setMeta(resp.country);
          setSeries(resp.data || []);
        }
      })
      .catch((e) => {
        console.error(e);
        setError('Không thể tải lịch sử (WDI) cho quốc gia này.');
      })
      .finally(() => setLoading(false));
  }, [isOpen, row?.iso2]);

  const chart = useMemo(() => {
    const x = (series || []).map((r) => String(r.year));
    const y = (series || []).map((r) => r.gold_value_usd_inferred);
    return { x, y };
  }, [series]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-panel rounded-2xl max-w-5xl w-full max-h-[85vh] overflow-hidden flex flex-col">
        <div className="flex items-start justify-between p-6 border-b border-white/10 gap-4">
          <div className="min-w-0">
            <h2 className="text-2xl font-bold text-white truncate">{row?.country_name || 'WGC Gold Reserves'}</h2>
            <div className="text-white/60 text-sm mt-1 flex flex-wrap gap-x-3 gap-y-1">
              {row?.holdings_as_of ? <span>As of: {row.holdings_as_of}</span> : null}
              {row?.retrieved_at_utc ? <span>Retrieved: {row.retrieved_at_utc}</span> : null}
              {row?.iso2 ? <span>ISO2: {row.iso2}</span> : <span className="text-white/50">Không map được ISO2</span>}
            </div>
          </div>

          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/10 transition-colors">
            <X className="w-5 h-5 icon-arrow" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="glass-card rounded-xl p-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-white">
              <div>
                <div className="text-white/60 text-sm">Tonnes</div>
                <div className="text-2xl font-bold">{formatTonnes(row?.tonnes)}</div>
              </div>
              <div>
                <div className="text-white/60 text-sm">% of reserves</div>
                <div className="text-2xl font-bold">
                  {formatPercent(row?.pct_of_reserves, 2)}
                </div>
              </div>
              <div>
                <div className="text-white/60 text-sm">Value (USD)</div>
                <div className="text-2xl font-bold">{formatCompactUsd(row?.value_usd)} USD</div>
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-5">
            <div className="text-white font-semibold mb-2">📈 Lịch sử (WDI) – Gold inferred value (USD)</div>
            {row?.iso2 ? (
              loading ? (
                <div className="text-white/70">Loading...</div>
              ) : error ? (
                <div className="text-white/70">{error}</div>
              ) : series.length === 0 ? (
                <div className="text-white/70">Không có dữ liệu lịch sử.</div>
              ) : (
                <>
                  {meta?.note ? <div className="text-white/50 text-xs mb-3">{meta.note}</div> : null}
                  <TimeSeriesChart title="Gold (WDI) – USD" x={chart.x} y={chart.y} yTitle="USD" ySuffix=" USD" valueType="usd" />
                </>
              )
            ) : (
              <div className="text-white/70">Không thể tải lịch sử vì không map được ISO2.</div>
            )}
          </div>

          <div className="text-white/50 text-xs">
            Nguồn WGC cung cấp snapshot (tonnes/%/USD). Lịch sử dùng WDI và chỉ mang tính tham khảo.
          </div>
        </div>
      </div>
    </div>
  );
}
