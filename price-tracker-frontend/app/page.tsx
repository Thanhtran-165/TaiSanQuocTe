'use client';

/**
 * Price Tracker Dashboard
 * Main dashboard with liquid glass UI
 */

import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { ArrowUpRight, BarChart3, LineChart, PieChart, RefreshCw } from 'lucide-react';
import Tabs from '@/components/Tabs';
import PriceCard from '@/components/PriceCard';
import DetailModal from '@/components/DetailModal';
import TimeSeriesChart from '@/components/TimeSeriesChart';
import ReservesModal from '@/components/ReservesModal';
import WgcReservesModal from '@/components/WgcReservesModal';
import BarChart from '@/components/BarChart';
import StackedAreaChart from '@/components/StackedAreaChart';
import { api, PriceData, HistoryData, ReservesCountryMeta, ReservesCountryRow, ReservesKind, ReservesTopRow, WgcGoldRow, WgcMeta } from '@/lib/api';
import { formatCompactNumber, formatCompactUsd, formatPercent, formatTonnes } from '@/lib/format';

const tabs = [
  { id: 'today', label: 'Today', icon: <ArrowUpRight className="w-4 h-4 icon-arrow" /> },
  { id: 'history', label: 'History', icon: <LineChart className="w-4 h-4 icon-arrow" /> },
  { id: 'comparison', label: 'Comparison', icon: <BarChart3 className="w-4 h-4 icon-arrow" /> },
  { id: 'portfolio', label: 'Portfolio', icon: <PieChart className="w-4 h-4 icon-arrow" /> },
  { id: 'reserves', label: 'Dự trữ', icon: <ArrowUpRight className="w-4 h-4 icon-arrow" /> },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState('today');
  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [historyData, setHistoryData] = useState<HistoryData[]>([]);
  const [longHistoryData, setLongHistoryData] = useState<HistoryData[] | null>(null);
  const [longHistoryLoading, setLongHistoryLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval] = useState(60);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState<{
    type: 'sjc' | 'phuquy' | 'intl-gold' | 'intl-silver' | 'paxg' | 'xaut';
    title: string;
    price: number | null;
  } | null>(null);

  // Reserves modal state
  const [reservesOpen, setReservesOpen] = useState(false);
  const [reservesKind, setReservesKind] = useState<ReservesKind>('gold');
  const [reservesCountry, setReservesCountry] = useState<ReservesCountryMeta | null>(null);
  const [reservesRows, setReservesRows] = useState<ReservesCountryRow[]>([]);

  const [wgcOpen, setWgcOpen] = useState(false);
  const [wgcSelected, setWgcSelected] = useState<WgcGoldRow | null>(null);

  // Fetch today's prices
  const fetchTodayPrices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getTodayPrices();
      if (response.success) {
        setPriceData(response.data);
      }
    } catch (err) {
      setError('Failed to fetch prices. Please check if the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch history data
  const fetchHistory = useCallback(async (days: number = 7) => {
    try {
      setError(null);
      const response = await api.getPriceHistory(days);
      if (response.success) {
        setHistoryData(response.data);
      }
    } catch (err) {
      setError('Failed to fetch history data.');
      console.error(err);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchTodayPrices();
    fetchHistory(7);
  }, [fetchHistory, fetchTodayPrices]);

  // Load long history for intl charts/ratio (2y)
  useEffect(() => {
    if (activeTab !== 'comparison' && activeTab !== 'portfolio') return;
    if (longHistoryData !== null || longHistoryLoading) return;
    setLongHistoryLoading(true);
    api
      .getPriceHistory(730)
      .then((resp) => {
        if (resp.success) setLongHistoryData(resp.data);
      })
      .catch((err) => console.error(err))
      .finally(() => setLongHistoryLoading(false));
  }, [activeTab, longHistoryData, longHistoryLoading]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchTodayPrices();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchTodayPrices]);

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN');
  };

  // Handle card click
  const handleCardClick = (
    type: 'sjc' | 'phuquy' | 'intl-gold' | 'intl-silver' | 'paxg' | 'xaut',
    title: string,
    price: number | null
  ) => {
    setSelectedCard({ type, title, price });
    setModalOpen(true);
  };

  // Close modal
  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedCard(null);
  };

  const handleOpenReserves = (kind: ReservesKind, country: ReservesCountryMeta, rows: ReservesCountryRow[]) => {
    setReservesKind(kind);
    setReservesCountry(country);
    setReservesRows(rows);
    setReservesOpen(true);
  };

  const handleOpenWgc = (row: WgcGoldRow) => {
    setWgcSelected(row);
    setWgcOpen(true);
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="glass-card rounded-3xl p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-2 flex items-center gap-3">
                <ArrowUpRight className="w-10 h-10 icon-arrow icon-glow" />
                Price Tracker
              </h1>
              <p className="text-white/70 text-lg">
                Vàng & Bạc - Real-time prices
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={fetchTodayPrices}
                disabled={loading}
                className="glass-card px-4 py-2 rounded-xl text-white font-medium hover:bg-white/10 transition-all disabled:opacity-50 flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 icon-arrow icon-glow ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>

              <label className="flex items-center gap-2 glass-panel px-4 py-2 rounded-xl cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-white/90 text-sm">Auto-refresh</span>
              </label>
            </div>
          </div>

          {priceData && (
            <div className="mt-4 text-sm text-white/60">
              Last updated: {formatDate(priceData.update_time)}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto">
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
      </div>

      {/* Error message */}
      {error && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="bg-red-500/20 border border-red-500/30 backdrop-blur-md rounded-xl p-4 text-red-200">
            {error}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {activeTab === 'today' && (
          <TodayTab data={priceData} loading={loading} onCardClick={handleCardClick} />
        )}

        {activeTab === 'history' && (
          <HistoryTab data={historyData} loading={loading} onRefresh={fetchHistory} />
        )}

        {activeTab === 'comparison' && (
          <ComparisonTab
            data={priceData}
            loading={loading}
            ratioHistory={longHistoryData || historyData}
            ratioLoading={longHistoryLoading}
          />
        )}

        {activeTab === 'portfolio' && <PortfolioTab priceData={priceData} longHistory={longHistoryData} />}

        {activeTab === 'reserves' && <ReservesTab onOpenCountry={handleOpenReserves} onOpenWgc={handleOpenWgc} />}
      </div>

      {/* Footer */}
      <div className="max-w-7xl mx-auto mt-12 text-center text-white/50 text-sm">
        <p>💡 Dữ liệu chỉ mang tính tham khảo. Vui lòng xác nhận với nguồn chính thức trước khi giao dịch.</p>
        <p className="mt-1">🔄 Powered by FastAPI + Next.js with Liquid Glass UI</p>
      </div>

      {/* Detail Modal */}
      {selectedCard && (
        <DetailModal
          isOpen={modalOpen}
          onClose={handleCloseModal}
          type={selectedCard.type}
          title={selectedCard.title}
          currentPrice={selectedCard.price}
        />
      )}

      <ReservesModal
        isOpen={reservesOpen}
        onClose={() => setReservesOpen(false)}
        meta={reservesCountry}
        rows={reservesRows}
        defaultKind={reservesKind}
      />

      <WgcReservesModal isOpen={wgcOpen} onClose={() => setWgcOpen(false)} row={wgcSelected} />
    </div>
  );
}

// Today Tab Component
function TodayTab({
  data,
  loading,
  onCardClick
}: {
  data: PriceData | null;
  loading: boolean;
  onCardClick: (type: 'sjc' | 'phuquy' | 'intl-gold' | 'intl-silver' | 'paxg' | 'xaut', title: string, price: number | null) => void;
}) {
  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center">
        <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-white/70" />
        <p className="text-white/70">Loading prices...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center">
        <p className="text-white/70">No data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Spread Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <ArrowUpRight className="w-5 h-5 icon-arrow icon-glow" />
            Gold Spread (VN vs World)
          </h3>
          {data.gold_spread.spread_vnd !== null ? (
            <div className="space-y-3">
              <div>
                {(() => {
                  const pct = data.gold_spread.spread_percent;
                  const pctClass =
                    pct === null || pct === undefined
                      ? 'text-white/60'
                      : pct >= 0
                        ? 'text-green-400'
                        : 'text-red-400';
                  return (
                    <>
                <div className="text-white/60 text-sm">Chênh lệch</div>
                <div className="text-2xl font-bold text-white">
                  {formatNumber(data.gold_spread.spread_vnd)} VND/lượng
                </div>
                <div className={`text-sm font-semibold ${pctClass}`}>
                  ({pct !== null && pct !== undefined ? (pct >= 0 ? '+' : '') : ''}
                  {formatNumber(pct ?? null)}%)
                </div>
                    </>
                  );
                })()}
              </div>
              <div className="text-white/70 text-sm">
                <div>International: {formatNumber(data.gold_spread.intl_in_vnd)} VND/oz</div>
                <div>Per lượng: {formatNumber(data.gold_spread.intl_per_luong)} VND</div>
              </div>
            </div>
          ) : (
            <p className="text-white/60">Không có dữ liệu</p>
          )}
        </div>

        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <ArrowUpRight className="w-5 h-5 icon-arrow icon-glow" />
            Silver Spread (VN vs World)
          </h3>
          {data.silver_spread.spread_vnd !== null ? (
            <div className="space-y-3">
              <div>
                {(() => {
                  const pct = data.silver_spread.spread_percent;
                  const pctClass =
                    pct === null || pct === undefined
                      ? 'text-white/60'
                      : pct >= 0
                        ? 'text-green-400'
                        : 'text-red-400';
                  return (
                    <>
                <div className="text-white/60 text-sm">Chênh lệch</div>
                <div className="text-2xl font-bold text-white">
                  {formatNumber(data.silver_spread.spread_vnd)} VND{data.silver_spread.unit.replace('VND', '')}
                </div>
                <div className={`text-sm font-semibold ${pctClass}`}>
                  ({pct !== null && pct !== undefined ? (pct >= 0 ? '+' : '') : ''}
                  {formatNumber(pct ?? null)}%)
                </div>
                    </>
                  );
                })()}
              </div>
              <div className="text-white/70 text-sm">
                <div>International: {formatNumber(data.silver_spread.intl_in_vnd)} VND/oz</div>
              </div>
            </div>
          ) : (
            <p className="text-white/60">Không có dữ liệu</p>
          )}
        </div>
      </div>

      {/* VN Prices */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <PriceCard
          icon={ArrowUpRight}
          title="🇻🇳 Vàng SJC"
          price={formatNumber(data.sjc_gold.price) + ' VND'}
          subtitle="Giá bán / lượng"
          iconClass="icon-arrow"
          onClick={() => onCardClick('sjc', '🇻🇳 Vàng SJC', data.sjc_gold.price)}
        />

        <PriceCard
          icon={ArrowUpRight}
          title="🥈 Bạc Phú Quý"
          price={formatNumber(data.phuquy_silver.price) + ' VND'}
          subtitle={`Giá bán (${data.phuquy_silver.unit})`}
          iconClass="icon-arrow"
          onClick={() => onCardClick('phuquy', '🥈 Bạc Phú Quý', data.phuquy_silver.price)}
        />
      </div>

      {/* International + Tokenized (compact) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <PriceCard
          icon={ArrowUpRight}
          title="🌎 Gold International"
          price={`$${formatNumber(data.intl_gold.price)}`}
          subtitle="USD/oz"
          change={
            data.intl_gold.change !== null
              ? { value: data.intl_gold.change, percent: data.intl_gold.change_percent || 0 }
              : undefined
          }
          iconClass="icon-arrow"
          size="sm"
          onClick={() => onCardClick('intl-gold', '🌎 Gold International', data.intl_gold.price)}
        />

        <PriceCard
          icon={ArrowUpRight}
          title="🌎 Silver International"
          price={`$${formatNumber(data.intl_silver.price)}`}
          subtitle="USD/oz"
          change={
            data.intl_silver.change !== null
              ? { value: data.intl_silver.change, percent: data.intl_silver.change_percent || 0 }
              : undefined
          }
          iconClass="icon-arrow"
          size="sm"
          onClick={() => onCardClick('intl-silver', '🌎 Silver International', data.intl_silver.price)}
        />

        <PriceCard
          icon={ArrowUpRight}
          title="🪙 PAXG"
          price={`$${formatNumber(data.paxg?.price ?? null)}`}
          subtitle="USD/oz"
          change={
            (data.paxg?.change ?? null) !== null
              ? { value: data.paxg?.change ?? 0, percent: data.paxg?.change_percent || 0 }
              : undefined
          }
          iconClass="icon-arrow"
          size="sm"
          onClick={() => onCardClick('paxg', '🪙 PAXG', data.paxg?.price ?? null)}
        />

        <PriceCard
          icon={ArrowUpRight}
          title="🪙 XAUT"
          price={`$${formatNumber(data.xaut?.price ?? null)}`}
          subtitle="USD/oz"
          change={
            (data.xaut?.change ?? null) !== null
              ? { value: data.xaut?.change ?? 0, percent: data.xaut?.change_percent || 0 }
              : undefined
          }
          iconClass="icon-arrow"
          size="sm"
          onClick={() => onCardClick('xaut', '🪙 XAUT', data.xaut?.price ?? null)}
        />
      </div>

      {/* Additional Info */}
      <div className="glass-panel rounded-2xl p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="text-white/60 text-sm mb-1">💵 Tỷ giá USD/VND</div>
            <div className="text-2xl font-bold text-white">
              {formatNumber(data.usd_vnd)} VND
            </div>
          </div>
          <div>
            <div className="text-white/60 text-sm mb-1">📈 Conversion</div>
            <div className="text-white text-sm">
              <div>1 Oz = 31.1035g = 0.8294 lượng</div>
              <div>1 Lượng = 37.5g</div>
            </div>
          </div>
          <div>
            <div className="text-white/60 text-sm mb-1">🔗 Sources</div>
            <div className="text-white text-sm">
              <div>Vàng SJC: vnstock</div>
              <div>International: {data.intl_gold.source || 'MSN Money'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// History Tab Component
function HistoryTab({
  data,
  loading,
  onRefresh,
}: {
  data: HistoryData[];
  loading: boolean;
  onRefresh: (days: number) => void;
}) {
  const [days, setDays] = useState(30);
  const [asset, setAsset] = useState<'sjc' | 'phuquy' | 'xau' | 'xag' | 'paxg' | 'xaut'>('sjc');

  useEffect(() => {
    onRefresh(days);
  }, [days, onRefresh]);

  const x = data.map((d) => (d.ts || '').slice(0, 10));
  const y = data.map((d) => {
    if (asset === 'sjc') return d.sjc_vnd_luong;
    if (asset === 'phuquy') return d.phuquy_silver_vnd;
    if (asset === 'xau') return d.intl_gold_usd_oz;
    if (asset === 'xag') return d.intl_silver_usd_oz;
    if (asset === 'paxg') return d.paxg_usd_oz ?? null;
    return d.xaut_usd_oz ?? null;
  });

  const title =
    asset === 'sjc'
      ? '🇻🇳 Vàng SJC (VND/lượng)'
      : asset === 'phuquy'
        ? '🥈 Bạc Phú Quý (VND/lượng)'
        : asset === 'xau'
          ? '🌎 XAU (USD/oz)'
          : asset === 'xag'
            ? '🌎 XAG (USD/oz)'
            : asset === 'paxg'
              ? '🪙 PAXG (USD/oz)'
              : '🪙 XAUT (USD/oz)';

  const isUsd = asset === 'xau' || asset === 'xag' || asset === 'paxg' || asset === 'xaut';
  const yTitle = isUsd ? 'USD/oz' : 'VND/lượng';
  const ySuffix = isUsd ? ' USD' : ' VND';
  const valueType = isUsd ? 'usd' : 'vnd';

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h3 className="text-xl font-bold text-white">📈 Price History</h3>
          <div className="flex items-center gap-3">
            <label className="text-white/70 text-sm">Asset:</label>
            <select
              value={asset}
              onChange={(e) => setAsset(e.target.value as 'sjc' | 'phuquy' | 'xau' | 'xag' | 'paxg' | 'xaut')}
              className="glass-input px-4 py-2 rounded-lg"
            >
              <option value="sjc">Vàng SJC</option>
              <option value="phuquy">Bạc Phú Quý</option>
              <option value="xau">XAU (Gold Intl)</option>
              <option value="xag">XAG (Silver Intl)</option>
              <option value="paxg">PAXG</option>
              <option value="xaut">XAUT</option>
            </select>
            <label className="text-white/70 text-sm">Days:</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="glass-input px-4 py-2 rounded-lg"
            >
              <option value={7}>7</option>
              <option value={30}>30</option>
              <option value={90}>90</option>
              <option value={180}>180</option>
              <option value={365}>365</option>
              <option value={730}>730</option>
            </select>
          </div>
        </div>

        {data.length > 0 && (
          <p className="text-white/60 text-sm mt-2">
            {data.length} data points • {new Date(data[0].ts).toLocaleDateString()} to{' '}
            {new Date(data[data.length - 1].ts).toLocaleDateString()}
          </p>
        )}
      </div>

      {loading ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-white/70" />
          <p className="text-white/70">Loading history...</p>
        </div>
      ) : data.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <p className="text-white/70">No history data available</p>
        </div>
      ) : (
        <>
          <TimeSeriesChart title={title} x={x} y={y} yTitle={yTitle} ySuffix={ySuffix} valueType={valueType} />
        </>
      )}
    </div>
  );
}

// Comparison Tab Component
function ComparisonTab({
  data,
  loading,
  ratioHistory,
  ratioLoading,
}: {
  data: PriceData | null;
  loading: boolean;
  ratioHistory: HistoryData[];
  ratioLoading: boolean;
}) {
  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center">
        <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-white/70" />
        <p className="text-white/70">Loading comparison...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center">
        <p className="text-white/70">No data available</p>
      </div>
    );
  }

  const ratio =
    data.intl_gold.price && data.intl_silver.price
      ? data.intl_gold.price / data.intl_silver.price
      : null;

  const ratioPoints = (ratioHistory || [])
    .filter((h) => h.intl_gold_usd_oz !== null && h.intl_silver_usd_oz !== null)
    .map((h) => ({
      day: (h.ts || '').slice(0, 10),
      ratio: (h.intl_gold_usd_oz as number) / (h.intl_silver_usd_oz as number),
    }));
  const ratioX = ratioPoints.map((p) => p.day);
  const ratioY = ratioPoints.map((p) => p.ratio);

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-2xl p-6">
        <h3 className="text-xl font-bold text-white mb-6">📊 Price Comparison</h3>

        <div className="overflow-x-auto">
          <table className="w-full text-white">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4">Type</th>
                <th className="text-right py-3 px-4">Price</th>
                <th className="text-right py-3 px-4">Change</th>
                <th className="text-left py-3 px-4">Source</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 font-semibold">🇻🇳 Vàng SJC</td>
                <td className="text-right py-3 px-4">{formatNumber(data.sjc_gold.price)} VND/lượng</td>
                <td className="text-right py-3 px-4 text-white/40">-</td>
                <td className="py-3 px-4">{data.sjc_gold.source}</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 font-semibold">🥈 Bạc Phú Quý</td>
                <td className="text-right py-3 px-4">
                  {formatNumber(data.phuquy_silver.price)} VND{data.phuquy_silver.unit.replace('VND', '')}
                </td>
                <td className="text-right py-3 px-4 text-white/40">-</td>
                <td className="py-3 px-4">{data.phuquy_silver.source}</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 font-semibold">🌎 Gold International</td>
                <td className="text-right py-3 px-4">${formatNumber(data.intl_gold.price)}/oz</td>
                <td className="text-right py-3 px-4">
                  {data.intl_gold.change !== null ? (
                    <span className={data.intl_gold.change >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {data.intl_gold.change >= 0 ? '+' : ''}
                      {formatNumber(data.intl_gold.change)} ({formatNumber(data.intl_gold.change_percent)}%)
                    </span>
                  ) : (
                    'N/A'
                  )}
                </td>
                <td className="py-3 px-4">{data.intl_gold.source || 'MSN Money'}</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 font-semibold">🌎 Silver International</td>
                <td className="text-right py-3 px-4">${formatNumber(data.intl_silver.price)}/oz</td>
                <td className="text-right py-3 px-4">
                  {data.intl_silver.change !== null ? (
                    <span className={data.intl_silver.change >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {data.intl_silver.change >= 0 ? '+' : ''}
                      {formatNumber(data.intl_silver.change)} ({formatNumber(data.intl_silver.change_percent)}%)
                    </span>
                  ) : (
                    'N/A'
                  )}
                </td>
                <td className="py-3 px-4">{data.intl_silver.source || 'MSN Money'}</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 font-semibold">🪙 PAXG</td>
                <td className="text-right py-3 px-4">${formatNumber(data.paxg?.price ?? null)}/oz</td>
                <td className="text-right py-3 px-4">
                  {(data.paxg?.change ?? null) !== null ? (
                    <span className={(data.paxg?.change ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {(data.paxg?.change ?? 0) >= 0 ? '+' : ''}
                      {formatNumber(data.paxg?.change ?? null)} ({formatNumber(data.paxg?.change_percent ?? null)}%)
                    </span>
                  ) : (
                    'N/A'
                  )}
                </td>
                <td className="py-3 px-4">{data.paxg?.source || 'CryptoCompare'}</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 font-semibold">🪙 XAUT</td>
                <td className="text-right py-3 px-4">${formatNumber(data.xaut?.price ?? null)}/oz</td>
                <td className="text-right py-3 px-4">
                  {(data.xaut?.change ?? null) !== null ? (
                    <span className={(data.xaut?.change ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {(data.xaut?.change ?? 0) >= 0 ? '+' : ''}
                      {formatNumber(data.xaut?.change ?? null)} ({formatNumber(data.xaut?.change_percent ?? null)}%)
                    </span>
                  ) : (
                    'N/A'
                  )}
                </td>
                <td className="py-3 px-4">{data.xaut?.source || 'CryptoCompare'}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {ratio !== null && (
          <div className="mt-6 glass-card rounded-xl p-4 text-center">
            <div className="text-white/70 text-sm mb-1">📊 Gold/Silver Ratio</div>
            <div className="text-3xl font-bold text-white">{ratio.toFixed(2)}:1</div>
          </div>
        )}

        <div className="mt-6">
          {ratioLoading ? (
            <div className="glass-card rounded-2xl p-8 text-center text-white/70">Loading ratio history...</div>
          ) : (
            <TimeSeriesChart
              title="📊 Gold/Silver Ratio (history)"
              x={ratioX}
              y={ratioY}
              yTitle="Ratio"
              ySuffix=":1"
              valueType="ratio"
            />
          )}
        </div>
      </div>
    </div>
  );
}

function formatNumber(num: number | null): string {
  if (num === null) return 'N/A';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(num);
}

function formatInteger(num: number | null | undefined): string {
  if (num === null || num === undefined) return 'N/A';
  if (!Number.isFinite(num)) return 'N/A';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(num);
}

type PortfolioHoldings = {
  sjc_luong: number;
  phuquy_luong: number;
  xau_oz: number;
  xag_oz: number;
  paxg_oz: number;
  xaut_oz: number;
};

function normalizeHoldingValue(v: string): number {
  const n = Number(v);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, n);
}

function forwardFill(values: (number | null | undefined)[]): (number | null)[] {
  let last: number | null = null;
  return values.map((v) => {
    if (typeof v === 'number' && Number.isFinite(v)) {
      last = v;
      return v;
    }
    return last;
  });
}

function PortfolioTab({ priceData, longHistory }: { priceData: PriceData | null; longHistory: HistoryData[] | null }) {
  const STORAGE_KEY = 'portfolio_holdings_v1';
  const STORAGE_HIDE_ZERO_KEY = 'portfolio_hide_zero_v1';
  const [holdings, setHoldings] = useState<PortfolioHoldings>({
    sjc_luong: 0,
    phuquy_luong: 0,
    xau_oz: 0,
    xag_oz: 0,
    paxg_oz: 0,
    xaut_oz: 0,
  });
  const [hideZeroAssets, setHideZeroAssets] = useState(true);
  const [days, setDays] = useState(90);
  const [series, setSeries] = useState<HistoryData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<PortfolioHoldings>;
      setHoldings((prev) => ({
        ...prev,
        ...Object.fromEntries(
          Object.entries(parsed || {}).map(([k, v]) => [k, typeof v === 'number' && Number.isFinite(v) ? Math.max(0, v) : 0])
        ),
      }));
    } catch {
      // ignore
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    try {
      const v = localStorage.getItem(STORAGE_HIDE_ZERO_KEY);
      if (v === null) return;
      setHideZeroAssets(v === '1');
    } catch {
      // ignore
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(holdings));
    } catch {
      // ignore
    }
  }, [holdings]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_HIDE_ZERO_KEY, hideZeroAssets ? '1' : '0');
    } catch {
      // ignore
    }
  }, [hideZeroAssets]);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const useCached = days === 730 && Array.isArray(longHistory) && longHistory.length > 0;
    if (useCached) {
      setSeries(longHistory);
      setLoading(false);
      return;
    }

    api
      .getPriceHistory(days)
      .then((resp) => {
        if (resp.success) setSeries(resp.data || []);
      })
      .catch((e) => {
        console.error(e);
        setError('Không thể tải lịch sử để tính portfolio.');
      })
      .finally(() => setLoading(false));
  }, [days, longHistory]);

  const computed = useMemo(() => {
    const x = (series || []).map((d) => (d.ts || '').slice(0, 10));
    const usdVnd = forwardFill((series || []).map((d) => d.usd_vnd));

    const sjc = forwardFill((series || []).map((d) => d.sjc_vnd_luong)).map((p) =>
      p === null ? null : p * holdings.sjc_luong
    );
    const phuquy = forwardFill((series || []).map((d) => d.phuquy_silver_vnd)).map((p) =>
      p === null ? null : p * holdings.phuquy_luong
    );

    const toVnd = (usd: (number | null | undefined)[], qty: number) =>
      forwardFill(usd).map((p, i) => (p === null || usdVnd[i] === null ? null : p * (usdVnd[i] as number) * qty));

    const xau = toVnd((series || []).map((d) => d.intl_gold_usd_oz), holdings.xau_oz);
    const xag = toVnd((series || []).map((d) => d.intl_silver_usd_oz), holdings.xag_oz);
    const paxg = toVnd((series || []).map((d) => d.paxg_usd_oz ?? null), holdings.paxg_oz);
    const xaut = toVnd((series || []).map((d) => d.xaut_usd_oz ?? null), holdings.xaut_oz);

    const total = x.map((_, i) => {
      const parts = [sjc[i], phuquy[i], xau[i], xag[i], paxg[i], xaut[i]];
      let sum = 0;
      let has = false;
      for (const v of parts) {
        if (typeof v === 'number' && Number.isFinite(v)) {
          sum += v;
          has = true;
        }
      }
      return has ? sum : null;
    });

    return { x, sjc, phuquy, xau, xag, paxg, xaut, total, usdVndLast: usdVnd[usdVnd.length - 1] ?? null };
  }, [holdings, series]);

  const latestIdx = (() => {
    for (let i = computed.x.length - 1; i >= 0; i--) {
      if (typeof computed.total[i] === 'number' && Number.isFinite(computed.total[i] as number)) return i;
    }
    return -1;
  })();

  const prevIdx = latestIdx > 0 ? latestIdx - 1 : -1;

  const now = useMemo(() => {
    const usdVnd = priceData?.usd_vnd ?? null;
    const sjcPrice = priceData?.sjc_gold.price ?? null;
    const phuquyPrice = priceData?.phuquy_silver.price ?? null;
    const xauUsd = priceData?.intl_gold.price ?? null;
    const xagUsd = priceData?.intl_silver.price ?? null;
    const paxgUsd = priceData?.paxg?.price ?? null;
    const xautUsd = priceData?.xaut?.price ?? null;

    const value = {
      sjc: sjcPrice === null ? null : sjcPrice * holdings.sjc_luong,
      phuquy: phuquyPrice === null ? null : phuquyPrice * holdings.phuquy_luong,
      xau: xauUsd === null || usdVnd === null ? null : xauUsd * usdVnd * holdings.xau_oz,
      xag: xagUsd === null || usdVnd === null ? null : xagUsd * usdVnd * holdings.xag_oz,
      paxg: paxgUsd === null || usdVnd === null ? null : paxgUsd * usdVnd * holdings.paxg_oz,
      xaut: xautUsd === null || usdVnd === null ? null : xautUsd * usdVnd * holdings.xaut_oz,
    };

    const parts = Object.values(value);
    let total = 0;
    let has = false;
    for (const v of parts) {
      if (typeof v === 'number' && Number.isFinite(v)) {
        total += v;
        has = true;
      }
    }
    return { usdVnd, sjcPrice, phuquyPrice, xauUsd, xagUsd, paxgUsd, xautUsd, value, total: has ? total : null };
  }, [holdings, priceData]);

  const totalChangeDay = latestIdx >= 0 && prevIdx >= 0 && computed.total[prevIdx] !== null && computed.total[latestIdx] !== null
    ? (computed.total[latestIdx] as number) - (computed.total[prevIdx] as number)
    : null;

  const assets = useMemo(() => {
    const totalNow = now.total;
    const share = (v: number | null) => (totalNow && v !== null ? (v / totalNow) * 100 : null);
    const change = (arr: (number | null)[]) =>
      latestIdx >= 0 && prevIdx >= 0 && arr[latestIdx] !== null && arr[prevIdx] !== null
        ? (arr[latestIdx] as number) - (arr[prevIdx] as number)
        : null;

    return [
      {
        key: 'sjc',
        name: '🇻🇳 Vàng SJC',
        unit: 'lượng',
        qty: holdings.sjc_luong,
        nowPriceLabel: sjcPriceLabel(now.sjcPrice),
        nowValue: now.value.sjc,
        sharePct: share(now.value.sjc),
        dayChange: change(computed.sjc),
        color: '#f59e0b',
        series: computed.sjc,
      },
      {
        key: 'phuquy',
        name: '🥈 Bạc Phú Quý',
        unit: 'lượng',
        qty: holdings.phuquy_luong,
        nowPriceLabel: phuquyPriceLabel(now.phuquyPrice),
        nowValue: now.value.phuquy,
        sharePct: share(now.value.phuquy),
        dayChange: change(computed.phuquy),
        color: '#cbd5e1',
        series: computed.phuquy,
      },
      {
        key: 'xau',
        name: '🌎 Gold International (XAU)',
        unit: 'oz',
        qty: holdings.xau_oz,
        nowPriceLabel: usdOzLabel(now.xauUsd),
        nowValue: now.value.xau,
        sharePct: share(now.value.xau),
        dayChange: change(computed.xau),
        color: '#3b82f6',
        series: computed.xau,
      },
      {
        key: 'xag',
        name: '🌎 Silver International (XAG)',
        unit: 'oz',
        qty: holdings.xag_oz,
        nowPriceLabel: usdOzLabel(now.xagUsd),
        nowValue: now.value.xag,
        sharePct: share(now.value.xag),
        dayChange: change(computed.xag),
        color: '#94a3b8',
        series: computed.xag,
      },
      {
        key: 'paxg',
        name: '🪙 PAXG',
        unit: 'oz',
        qty: holdings.paxg_oz,
        nowPriceLabel: usdOzLabel(now.paxgUsd),
        nowValue: now.value.paxg,
        sharePct: share(now.value.paxg),
        dayChange: change(computed.paxg),
        color: '#22c55e',
        series: computed.paxg,
      },
      {
        key: 'xaut',
        name: '🪙 XAUT',
        unit: 'oz',
        qty: holdings.xaut_oz,
        nowPriceLabel: usdOzLabel(now.xautUsd),
        nowValue: now.value.xaut,
        sharePct: share(now.value.xaut),
        dayChange: change(computed.xaut),
        color: '#14b8a6',
        series: computed.xaut,
      },
    ];
  }, [computed, holdings, latestIdx, now, prevIdx]);

  const anyHolding = useMemo(() => assets.some((a) => a.qty > 0), [assets]);
  const visibleAssets = useMemo(() => (hideZeroAssets ? assets.filter((a) => a.qty > 0) : assets), [assets, hideZeroAssets]);

  const chartSeries = useMemo(
    () =>
      visibleAssets
        .map((a) => ({ name: a.name, color: a.color, values: a.series })),
    [visibleAssets]
  );

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h3 className="text-xl font-bold text-white">📦 Portfolio</h3>
          <div className="flex items-center gap-3">
            <label className="text-white/70 text-sm">Days:</label>
            <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="glass-input px-4 py-2 rounded-lg">
              <option value={30}>30</option>
              <option value={90}>90</option>
              <option value={180}>180</option>
              <option value={365}>365</option>
              <option value={730}>730</option>
            </select>
            <label className="flex items-center gap-2 text-white/80 text-sm ml-2 select-none">
              <input
                type="checkbox"
                checked={hideZeroAssets}
                onChange={(e) => setHideZeroAssets(e.target.checked)}
                className="w-4 h-4"
              />
              Ẩn tài sản = 0
            </label>
          </div>
        </div>
        <div className="text-white/60 text-sm mt-2">
          Nhập số lượng để theo dõi tổng giá trị & tỷ trọng theo thời gian. Quy đổi tài sản USD sang VND theo USD/VND từng ngày.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-2xl p-6">
          <div className="text-white font-semibold mb-4">Số lượng</div>
          {hideZeroAssets && !anyHolding ? (
            <div className="text-white/60 text-sm">
              Chưa có tài sản nào (tất cả = 0). Tắt “Ẩn tài sản = 0” để nhập số lượng.
            </div>
          ) : (
            <div className="space-y-3">
              {(!hideZeroAssets || holdings.sjc_luong > 0) && (
                <HoldingInput label="🇻🇳 Vàng SJC" unit="lượng" value={holdings.sjc_luong} onChange={(v) => setHoldings((h) => ({ ...h, sjc_luong: v }))} />
              )}
              {(!hideZeroAssets || holdings.phuquy_luong > 0) && (
                <HoldingInput label="🥈 Bạc Phú Quý" unit="lượng" value={holdings.phuquy_luong} onChange={(v) => setHoldings((h) => ({ ...h, phuquy_luong: v }))} />
              )}
              {(!hideZeroAssets || holdings.xau_oz > 0) && (
                <HoldingInput label="🌎 XAU (Gold Intl)" unit="oz" value={holdings.xau_oz} onChange={(v) => setHoldings((h) => ({ ...h, xau_oz: v }))} />
              )}
              {(!hideZeroAssets || holdings.xag_oz > 0) && (
                <HoldingInput label="🌎 XAG (Silver Intl)" unit="oz" value={holdings.xag_oz} onChange={(v) => setHoldings((h) => ({ ...h, xag_oz: v }))} />
              )}
              {(!hideZeroAssets || holdings.paxg_oz > 0) && (
                <HoldingInput label="🪙 PAXG" unit="oz" value={holdings.paxg_oz} onChange={(v) => setHoldings((h) => ({ ...h, paxg_oz: v }))} />
              )}
              {(!hideZeroAssets || holdings.xaut_oz > 0) && (
                <HoldingInput label="🪙 XAUT" unit="oz" value={holdings.xaut_oz} onChange={(v) => setHoldings((h) => ({ ...h, xaut_oz: v }))} />
              )}
            </div>
          )}
        </div>

        <div className="glass-panel rounded-2xl p-6">
          <div className="text-white font-semibold mb-4">Tổng quan</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="glass-card rounded-xl p-4">
              <div className="text-white/60 text-sm">Tổng giá trị (hiện tại)</div>
              <div className="text-2xl font-bold text-white">{now.total === null ? 'N/A' : `${formatCompactNumber(now.total)} VND`}</div>
              <div className="text-white/50 text-xs mt-1">USD/VND: {formatInteger(now.usdVnd)}</div>
            </div>
            <div className="glass-card rounded-xl p-4">
              <div className="text-white/60 text-sm">Thay đổi theo ngày</div>
              <div className={`text-2xl font-bold ${totalChangeDay === null ? 'text-white' : totalChangeDay >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {totalChangeDay === null ? 'N/A' : `${totalChangeDay >= 0 ? '+' : ''}${formatCompactNumber(totalChangeDay)} VND`}
              </div>
              <div className="text-white/50 text-xs mt-1">
                {latestIdx >= 0 ? `Từ ${computed.x[Math.max(0, prevIdx)]} → ${computed.x[latestIdx]}` : 'N/A'}
              </div>
            </div>
          </div>

          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-white">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-2 pr-4">Tài sản</th>
                  <th className="text-right py-2 px-2">Qty</th>
                  <th className="text-right py-2 px-2">Giá</th>
                  <th className="text-right py-2 px-2">Giá trị</th>
                  <th className="text-right py-2 pl-2">% TT</th>
                  <th className="text-right py-2 pl-2">Δ ngày</th>
                </tr>
              </thead>
              <tbody>
                {visibleAssets.map((a) => (
                  <tr key={a.key} className="border-b border-white/5">
                    <td className="py-2 pr-4 font-semibold">{a.name}</td>
                    <td className="py-2 px-2 text-right text-white/80">
                      {a.qty ? `${formatNumber(a.qty)} ${a.unit}` : <span className="text-white/40">0</span>}
                    </td>
                    <td className="py-2 px-2 text-right text-white/80">{a.nowPriceLabel}</td>
                    <td className="py-2 px-2 text-right">{a.nowValue === null ? 'N/A' : `${formatCompactNumber(a.nowValue)} VND`}</td>
                    <td className="py-2 pl-2 text-right text-white/80">{formatPercent(a.sharePct, 1)}</td>
                    <td
                      className={`py-2 pl-2 text-right ${
                        a.dayChange === null ? 'text-white/50' : a.dayChange >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {a.dayChange === null ? 'N/A' : `${a.dayChange >= 0 ? '+' : ''}${formatCompactNumber(a.dayChange)} VND`}
                    </td>
                  </tr>
                ))}
                {visibleAssets.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-white/60">
                      Không có tài sản nào để hiển thị.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="text-white/50 text-xs mt-3">
            Ghi chú: thay đổi theo ngày được tính từ dữ liệu lịch sử (1 điểm/ngày). Giá trị hiện tại dùng dữ liệu realtime.
          </div>
        </div>
      </div>

      {loading ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-white/70" />
          <p className="text-white/70">Loading portfolio history...</p>
        </div>
      ) : error ? (
        <div className="glass-card rounded-2xl p-8 text-center text-white/70">{error}</div>
      ) : series.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center text-white/70">Chưa có dữ liệu lịch sử.</div>
      ) : chartSeries.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center text-white/70">Nhập số lượng &gt; 0 để vẽ biểu đồ.</div>
      ) : (
        <StackedAreaChart
          title="📈 Portfolio (stacked) – Tổng giá trị & tỷ trọng"
          x={computed.x}
          series={chartSeries}
          yTitle="Value"
        />
      )}
    </div>
  );
}

function HoldingInput({
  label,
  unit,
  value,
  onChange,
}: {
  label: string;
  unit: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="text-white/80 text-sm">{label}</div>
      <div className="flex items-center gap-2">
        <input
          type="number"
          min={0}
          step="0.0001"
          value={value}
          onChange={(e) => onChange(normalizeHoldingValue(e.target.value))}
          className="glass-input px-3 py-2 rounded-lg w-36 text-right"
        />
        <span className="text-white/50 text-sm w-10">{unit}</span>
      </div>
    </div>
  );
}

function sjcPriceLabel(v: number | null): string {
  return v === null ? 'N/A' : `${formatInteger(v)} VND/lượng`;
}

function phuquyPriceLabel(v: number | null): string {
  return v === null ? 'N/A' : `${formatInteger(v)} VND/lượng`;
}

function usdOzLabel(v: number | null): string {
  return v === null ? 'N/A' : `$${formatNumber(v)}/oz`;
}

// Reserves Tab Component
function ReservesTab({
  onOpenCountry,
  onOpenWgc,
}: {
  onOpenCountry: (kind: ReservesKind, country: ReservesCountryMeta, rows: ReservesCountryRow[]) => void;
  onOpenWgc: (row: WgcGoldRow) => void;
}) {
  const [kind, setKind] = useState<ReservesKind>('gold');
  const [goldSource, setGoldSource] = useState<'wgc' | 'wdi'>('wgc');
  const [wgcMetric, setWgcMetric] = useState<'tonnes' | 'value_usd'>('tonnes');
  const [rows, setRows] = useState<ReservesTopRow[]>([]);
  const [wgcRows, setWgcRows] = useState<WgcGoldRow[]>([]);
  const [wgcMeta, setWgcMeta] = useState<WgcMeta | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [globalEndYear, setGlobalEndYear] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (kind === 'gold' && goldSource === 'wgc') {
        const resp = await api.getWgcTop(20, 'tonnes');
        if (resp.success) {
          setWgcRows(resp.data || []);
          setWgcMeta(resp.meta || null);
        }
      } else {
        const resp = await api.getReservesTop(kind, 20);
        if (resp.success) {
          setRows(resp.data || []);
          setYear(resp.year);
          setGlobalEndYear(resp.global_end_year);
        }
      }
    } catch (e) {
      console.error(e);
      setError('Không thể tải dữ liệu dự trữ.');
    } finally {
      setLoading(false);
    }
  }, [kind, goldSource]);

  useEffect(() => {
    load();
  }, [load]);

  const handleClickCountry = async (iso2: string, fallbackName?: string) => {
    try {
      const resp = await api.getReservesCountry(iso2);
      if (!resp.success) return;
      const meta = resp.country || {
        iso2,
        country_name: fallbackName || iso2,
        year_range: { start: resp.global_year_range.start, end: resp.global_year_range.end },
        note: null,
      };
      onOpenCountry(kind, meta, resp.data || []);
    } catch (e) {
      console.error(e);
      setError('Không thể tải dữ liệu quốc gia.');
    }
  };

  const title =
    kind === 'gold'
      ? 'Dự trữ vàng'
      : kind === 'non_gold'
        ? 'Dự trữ không bao gồm vàng'
        : 'Tổng dự trữ (bao gồm vàng)';

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h3 className="text-xl font-bold text-white">🏦 Dự trữ</h3>
          <div className="flex items-center gap-3">
            <label className="text-white/70 text-sm">Loại:</label>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value as ReservesKind)}
              className="glass-input px-4 py-2 rounded-lg"
            >
              <option value="gold">Dự trữ vàng</option>
              <option value="non_gold">Không bao gồm vàng</option>
              <option value="total">Tổng dự trữ</option>
            </select>
            {kind === 'gold' && (
              <>
                <label className="text-white/70 text-sm ml-2">Nguồn:</label>
                <select
                  value={goldSource}
                  onChange={(e) => setGoldSource(e.target.value as 'wgc' | 'wdi')}
                  className="glass-input px-4 py-2 rounded-lg"
                >
                  <option value="wgc">WGC (latest)</option>
                  <option value="wdi">WDI (history)</option>
                </select>
                {goldSource === 'wgc' && (
                  <>
                    <label className="text-white/70 text-sm ml-2">Biểu đồ:</label>
                    <select
                      value={wgcMetric}
                      onChange={(e) => setWgcMetric(e.target.value as 'tonnes' | 'value_usd')}
                      className="glass-input px-4 py-2 rounded-lg"
                    >
                      <option value="tonnes">Tonnes</option>
                      <option value="value_usd">Value (USD)</option>
                    </select>
                  </>
                )}
              </>
            )}
          </div>
        </div>
        <p className="text-white/60 text-sm mt-2">
          Top 20 • {title}
          {kind === 'gold' && goldSource === 'wgc'
            ? wgcMeta?.holdings_as_of
              ? ` • As of ${wgcMeta.holdings_as_of}`
              : ''
            : year
              ? ` • Năm ${year}`
              : ''}
          {kind === 'gold' && goldSource === 'wgc' && wgcMeta?.valuation?.spot_price_usd_oz ? (
            <span className="ml-2">
              • Valuation: ${formatNumber(wgcMeta.valuation.spot_price_usd_oz)} /oz ({wgcMeta.valuation.spot_source || 'spot'})
            </span>
          ) : null}
        </p>
      </div>

      {loading ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-white/70" />
          <p className="text-white/70">Loading reserves...</p>
        </div>
      ) : error ? (
        <div className="glass-card rounded-2xl p-8 text-center text-white/70">{error}</div>
      ) : (
        <div className="glass-panel rounded-2xl p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-white">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-3 px-4">#</th>
                  <th className="text-left py-3 px-4">Quốc gia</th>
                  {kind === 'gold' && goldSource === 'wgc' ? (
                    <>
                      <th className="text-right py-3 px-4">Tonnes</th>
                      <th className="text-right py-3 px-4">% dự trữ</th>
                      <th className="text-right py-3 px-4">Value (USD)</th>
                    </>
                  ) : (
                    <>
                      <th className="text-right py-3 px-4">Giá trị</th>
                      <th className="text-right py-3 px-4">Năm dữ liệu</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {kind === 'gold' && goldSource === 'wgc'
                  ? (wgcRows || []).map((r) => (
                      <tr
                        key={(r.iso2 || r.country_name) + String(r.rank ?? '')}
                        className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                        onClick={() => onOpenWgc(r)}
                      >
                        <td className="py-3 px-4 text-white/70">{r.rank ?? ''}</td>
                        <td className="py-3 px-4 font-semibold">
                          {r.country_name}
                          {!r.iso2 ? <span className="text-white/50 text-xs ml-2">(no ISO2)</span> : null}
                        </td>
                        <td className="py-3 px-4 text-right">{formatTonnes(r.tonnes)}</td>
                        <td className="py-3 px-4 text-right">
                          {formatPercent(r.pct_of_reserves ?? null, 2)}
                        </td>
                        <td className="py-3 px-4 text-right">{formatCompactUsd(r.value_usd)} USD</td>
                      </tr>
                    ))
                  : (rows || []).map((r) => {
                      const endedEarly =
                        globalEndYear !== null && typeof r.data_end_year === 'number' && r.data_end_year < globalEndYear;
                      return (
                        <tr
                          key={r.iso2}
                          className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                          onClick={() => handleClickCountry(r.iso2, r.country_name)}
                        >
                          <td className="py-3 px-4 text-white/70">{r.rank}</td>
                          <td className="py-3 px-4 font-semibold">{r.country_name}</td>
                          <td className="py-3 px-4 text-right">{formatCompactUsd(r.value_usd)} USD</td>
                          <td className="py-3 px-4 text-right">
                            {r.data_end_year}
                            {endedEarly ? <span className="text-white/50 text-xs ml-2">(dừng)</span> : null}
                          </td>
                        </tr>
                      );
                    })}

                {((kind === 'gold' && goldSource === 'wgc' ? wgcRows.length : rows.length) === 0) && (
                  <tr>
                    <td colSpan={kind === 'gold' && goldSource === 'wgc' ? 5 : 4} className="py-10 text-center text-white/60">
                      Không có dữ liệu.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 text-white/50 text-xs border-t border-white/10">
            {kind === 'gold' && goldSource === 'wgc'
              ? 'Value (USD) được tính hậu kỳ từ tonnes × giá vàng spot hiện tại.'
              : 'Nhấn vào quốc gia để xem toàn thời gian. Nếu dữ liệu dừng trước năm mới nhất sẽ có chú thích.'}
          </div>
        </div>
      )}

      {kind === 'gold' && goldSource === 'wgc' && (wgcRows?.length ?? 0) > 0 && (
        <BarChart
          title={
            wgcMetric === 'tonnes'
              ? '📊 Top 20 dự trữ vàng (Tonnes)'
              : '📊 Top 20 dự trữ vàng (Value USD)'
          }
          labels={(wgcRows || []).map((r) => r.country_name)}
          values={
            (wgcRows || []).map((r) =>
              wgcMetric === 'tonnes' ? (r.tonnes ?? null) : (r.value_usd ?? null)
            ) as (number | null)[]
          }
          xTitle={wgcMetric === 'tonnes' ? 'Tonnes' : 'USD'}
          valueType={wgcMetric === 'tonnes' ? 'number' : 'usd'}
        />
      )}
    </div>
  );
}
