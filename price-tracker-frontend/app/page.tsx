'use client';

/**
 * Price Tracker Dashboard
 * Main dashboard with liquid glass UI
 */

import React, { useState, useEffect } from 'react';
import { Coins, Calendar, BarChart3, RefreshCw, TrendingUp, DollarSign } from 'lucide-react';
import Tabs from '@/components/Tabs';
import PriceCard from '@/components/PriceCard';
import DetailModal from '@/components/DetailModal';
import { api, PriceData, HistoryData } from '@/lib/api';

const tabs = [
  { id: 'today', label: 'Today', icon: '📅' },
  { id: 'history', label: 'History', icon: '📈' },
  { id: 'comparison', label: 'Comparison', icon: '📊' },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState('today');
  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [historyData, setHistoryData] = useState<HistoryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(60);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState<{
    type: 'sjc' | 'phuquy' | 'intl-gold' | 'intl-silver';
    title: string;
    price: number | null;
  } | null>(null);

  // Fetch today's prices
  const fetchTodayPrices = async () => {
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
  };

  // Fetch history data
  const fetchHistory = async (days: number = 7) => {
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
  };

  // Initial data fetch
  useEffect(() => {
    fetchTodayPrices();
    fetchHistory(7);
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchTodayPrices();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const formatNumber = (num: number | null): string => {
    if (num === null) return 'N/A';
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN');
  };

  // Handle card click
  const handleCardClick = (type: 'sjc' | 'phuquy' | 'intl-gold' | 'intl-silver', title: string, price: number | null) => {
    setSelectedCard({ type, title, price });
    setModalOpen(true);
  };

  // Close modal
  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedCard(null);
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="glass-card rounded-3xl p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-2 flex items-center gap-3">
                <Coins className="w-10 h-10 icon-gold icon-glow" />
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
                <RefreshCw className={`w-4 h-4 icon-glow ${loading ? 'animate-spin' : ''}`} />
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
          <ComparisonTab data={priceData} loading={loading} />
        )}
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
  onCardClick: (type: 'sjc' | 'phuquy' | 'intl-gold' | 'intl-silver', title: string, price: number | null) => void;
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
      {/* Main Price Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <PriceCard
          icon={Coins}
          title="🇻🇳 Vàng SJC"
          price={formatNumber(data.sjc_gold.price) + ' VND'}
          subtitle="per lượng"
          iconClass="icon-gold"
          onClick={() => onCardClick('sjc', '🇻🇳 Vàng SJC', data.sjc_gold.price)}
        />

        <PriceCard
          icon={Coins}
          title="🥈 Bạc Phú Quý"
          price={formatNumber(data.phuquy_silver.price) + ' VND'}
          subtitle={data.phuquy_silver.unit}
          iconClass="icon-silver"
          onClick={() => onCardClick('phuquy', '🥈 Bạc Phú Quý', data.phuquy_silver.price)}
        />

        <PriceCard
          icon={TrendingUp}
          title="🌎 Gold International"
          price={`$${formatNumber(data.intl_gold.price)}`}
          subtitle="per oz"
          change={
            data.intl_gold.change !== null
              ? {
                  value: data.intl_gold.change,
                  percent: data.intl_gold.change_percent || 0,
                }
              : undefined
          }
          iconClass="icon-gold"
          onClick={() => onCardClick('intl-gold', '🌎 Gold International', data.intl_gold.price)}
        />

        <PriceCard
          icon={TrendingUp}
          title="🌎 Silver International"
          price={`$${formatNumber(data.intl_silver.price)}`}
          subtitle="per oz"
          change={
            data.intl_silver.change !== null
              ? {
                  value: data.intl_silver.change,
                  percent: data.intl_silver.change_percent || 0,
                }
              : undefined
          }
          iconClass="icon-silver"
          onClick={() => onCardClick('intl-silver', '🌎 Silver International', data.intl_silver.price)}
        />
      </div>

      {/* Spread Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-4">🪙 Gold Spread (VN vs World)</h3>
          {data.gold_spread.spread_vnd !== null ? (
            <div className="space-y-3">
              <div>
                <div className="text-white/60 text-sm">Chênh lệch</div>
                <div className="text-2xl font-bold text-white">
                  {formatNumber(data.gold_spread.spread_vnd)} VND/lượng
                </div>
                <div className={`text-sm font-semibold ${data.gold_spread.spread_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ({data.gold_spread.spread_percent >= 0 ? '+' : ''}
                  {formatNumber(data.gold_spread.spread_percent)}%)
                </div>
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
          <h3 className="text-xl font-bold text-white mb-4">🥈 Silver Spread (VN vs World)</h3>
          {data.silver_spread.spread_vnd !== null ? (
            <div className="space-y-3">
              <div>
                <div className="text-white/60 text-sm">Chênh lệch</div>
                <div className="text-2xl font-bold text-white">
                  {formatNumber(data.silver_spread.spread_vnd)} VND{data.silver_spread.unit.replace('VND', '')}
                </div>
                <div className={`text-sm font-semibold ${data.silver_spread.spread_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ({data.silver_spread.spread_percent >= 0 ? '+' : ''}
                  {formatNumber(data.silver_spread.spread_percent)}%)
                </div>
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
  const [days, setDays] = useState(7);

  useEffect(() => {
    onRefresh(days);
  }, [days]);

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h3 className="text-xl font-bold text-white">📈 Price History</h3>
          <div className="flex items-center gap-3">
            <label className="text-white/70 text-sm">Days:</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="glass-input px-4 py-2 rounded-lg"
            >
              <option value={1}>1 day</option>
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
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
        <div className="glass-panel rounded-2xl p-6 overflow-x-auto">
          <table className="w-full text-white">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4">Time</th>
                <th className="text-right py-3 px-4">Gold SJC</th>
                <th className="text-right py-3 px-4">Silver PQ</th>
                <th className="text-right py-3 px-4">Intl Gold</th>
                <th className="text-right py-3 px-4">Intl Silver</th>
              </tr>
            </thead>
            <tbody>
              {data.slice().reverse().map((item, index) => (
                <tr key={index} className="border-b border-white/5 hover:bg-white/5">
                  <td className="py-3 px-4">{new Date(item.ts).toLocaleString('vi-VN')}</td>
                  <td className="text-right py-3 px-4">{formatNumber(item.sjc_vnd_luong)}</td>
                  <td className="text-right py-3 px-4">{formatNumber(item.phuquy_silver_vnd)}</td>
                  <td className="text-right py-3 px-4">${formatNumber(item.intl_gold_usd_oz)}</td>
                  <td className="text-right py-3 px-4">${formatNumber(item.intl_silver_usd_oz)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// Comparison Tab Component
function ComparisonTab({ data, loading }: { data: PriceData | null; loading: boolean }) {
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
            </tbody>
          </table>
        </div>

        {ratio !== null && (
          <div className="mt-6 glass-card rounded-xl p-4 text-center">
            <div className="text-white/70 text-sm mb-1">📊 Gold/Silver Ratio</div>
            <div className="text-3xl font-bold text-white">{ratio.toFixed(2)}:1</div>
          </div>
        )}
      </div>
    </div>
  );
}

function formatNumber(num: number | null): string {
  if (num === null) return 'N/A';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(num);
}
