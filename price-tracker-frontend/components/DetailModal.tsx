/**
 * DetailModal Component
 * Shows detailed product list when a price card is clicked
 */

import React, { useState, useEffect } from 'react';
import { X, Search } from 'lucide-react';
import { api } from '@/lib/api';

interface DetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  type: 'sjc' | 'phuquy' | 'intl-gold' | 'intl-silver';
  title: string;
  currentPrice: number | null;
}

interface ProductItem {
  name?: string;
  product?: string;
  branch?: string;
  buy_price?: number;
  sell_price?: number;
  price?: number;
  date?: string;
  ts?: string;
}

export default function DetailModal({
  isOpen,
  onClose,
  type,
  title,
  currentPrice,
}: DetailModalProps) {
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<ProductItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItem, setSelectedItem] = useState<ProductItem | null>(null);
  const [itemHistory, setItemHistory] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const fetchProducts = async () => {
      setLoading(true);
      try {
        let response;

        switch (type) {
          case 'sjc':
            response = await api.getSjcItems();
            break;
          case 'phuquy':
            response = await api.getPhuQuyItems();
            break;
          case 'intl-gold':
          case 'intl-silver':
            // For international, we'll show summary data
            const histResponse = await api.getPriceHistory(30);
            if (histResponse.success && histResponse.data.length > 0) {
              const latest = histResponse.data[histResponse.data.length - 1];
              const goldData = {
                name: 'International Gold',
                buy_price: latest.intl_gold_usd_oz,
                date: latest.ts,
              };
              const silverData = {
                name: 'International Silver',
                buy_price: latest.intl_silver_usd_oz,
                date: latest.ts,
              };
              response = {
                success: true,
                data: type === 'intl-gold' ? [goldData] : [silverData]
              };
            }
            break;
        }

        if (response && response.success) {
          setItems(response.data);
        }
      } catch (error) {
        console.error('Error fetching products:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [isOpen, type]);

  const handleItemClick = async (item: ProductItem) => {
    setSelectedItem(item);
    setShowHistory(true);

    // Fetch history for this specific item
    try {
      let historyResponse;
      const itemName = item.name || item.product || '';

      if (type === 'sjc') {
        historyResponse = await api.getSjcItemHistory(itemName, item.branch, 30);
      } else if (type === 'phuquy') {
        historyResponse = await api.getPhuQuyItemHistory(itemName, 30);
      }

      if (historyResponse && historyResponse.success) {
        setItemHistory(historyResponse.data);
      }
    } catch (error) {
      console.error('Error fetching item history:', error);
    }
  };

  const filteredItems = items.filter(item => {
    const query = searchQuery.toLowerCase();
    const name = (item.name || item.product || '').toLowerCase();
    const branch = (item.branch || '').toLowerCase();
    return name.includes(query) || branch.includes(query);
  });

  if (!isOpen) return null;

  const formatPrice = (price: number | undefined) => {
    if (price === null || price === undefined) return 'N/A';
    if (type.includes('intl')) {
      return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `${Number(price).toLocaleString()} VND`;
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-panel rounded-2xl max-w-4xl w-full max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div>
            <h2 className="text-2xl font-bold text-white">{title}</h2>
            <p className="text-white/60 text-sm mt-1">{filteredItems.length} sản phẩm</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5 text-white/70" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-white/30"></div>
              <p className="text-white/70 mt-4">Loading products...</p>
            </div>
          ) : showHistory && selectedItem ? (
            <div>
              {/* Back button */}
              <button
                onClick={() => setShowHistory(false)}
                className="mb-4 text-white/70 hover:text-white flex items-center gap-2 text-sm"
              >
                ← Back to product list
              </button>

              {/* Selected Item Details */}
              <div className="glass-card rounded-xl p-6 mb-6">
                <h3 className="text-xl font-bold text-white mb-2">
                  {selectedItem.name || selectedItem.product}
                </h3>
                {selectedItem.branch && (
                  <p className="text-white/60 text-sm mb-4">Chi nhánh: {selectedItem.branch}</p>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-white/60 text-sm">Giá mua</div>
                    <div className="text-2xl font-bold text-green-400">
                      {formatPrice(selectedItem.buy_price)}
                    </div>
                  </div>
                  {selectedItem.sell_price && (
                    <div>
                      <div className="text-white/60 text-sm">Giá bán</div>
                      <div className="text-2xl font-bold text-red-400">
                        {formatPrice(selectedItem.sell_price)}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* History */}
              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Lịch sửắc giá (30 ngày gần nhất)</h4>
                <div className="glass-panel rounded-xl overflow-hidden">
                  <div className="max-h-96 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-white/5 sticky top-0">
                        <tr>
                          <th className="text-left py-3 px-4 text-white/70 font-medium">Thời gian</th>
                          <th className="text-right py-3 px-4 text-white/70 font-medium">Giá mua</th>
                          {itemHistory[0]?.sell_price && (
                            <th className="text-right py-3 px-4 text-white/70 font-medium">Giá bán</th>
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {itemHistory.slice().reverse().map((item, idx) => (
                          <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
                            <td className="py-3 px-4 text-white/70">
                              {new Date(item.ts).toLocaleString('vi-VN')}
                            </td>
                            <td className="py-3 px-4 text-right text-green-400 font-medium">
                              {formatPrice(item.buy_price)}
                            </td>
                            {item.sell_price && (
                              <td className="py-3 px-4 text-right text-red-400 font-medium">
                                {formatPrice(item.sell_price)}
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div>
              {/* Search Bar */}
              <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                <input
                  type="text"
                  placeholder="Tìm kiếm sản phẩm..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/50 focus:outline-none focus:border-white/30"
                />
              </div>

              {/* Products List */}
              <div className="space-y-3">
                {filteredItems.length === 0 ? (
                  <div className="text-center py-8 text-white/60">
                    Không tìm thấy sản phẩm nào
                  </div>
                ) : (
                  filteredItems.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleItemClick(item)}
                      className="glass-card rounded-xl p-4 cursor-pointer hover:border-white/30 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="text-white font-semibold mb-1">
                            {item.name || item.product}
                          </h4>
                          {item.branch && (
                            <p className="text-white/60 text-sm">📍 {item.branch}</p>
                          )}
                          {item.date && (
                            <p className="text-white/50 text-xs mt-1">
                              {new Date(item.date).toLocaleDateString('vi-VN')}
                            </p>
                          )}
                        </div>
                        <div className="text-right ml-4">
                          {item.buy_price !== undefined && (
                            <div>
                              <div className="text-white/60 text-xs">Mua</div>
                              <div className="text-green-400 font-bold">{formatPrice(item.buy_price)}</div>
                            </div>
                          )}
                          {item.sell_price && (
                            <div className="mt-2">
                              <div className="text-white/60 text-xs">Bán</div>
                              <div className="text-red-400 font-bold">{formatPrice(item.sell_price)}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
