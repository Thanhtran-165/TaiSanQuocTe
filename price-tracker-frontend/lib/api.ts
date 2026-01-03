/**
 * API Client for Price Tracker Backend
 * Communicates with FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface PriceData {
  update_time: string;
  usd_vnd: number | null;
  sjc_gold: {
    price: number | null;
    unit: string;
    source: string;
  };
  phuquy_silver: {
    price: number | null;
    unit: string;
    source: string;
  };
  intl_gold: {
    price: number | null;
    change: number | null;
    change_percent: number | null;
    unit: string;
    source: string | null;
  };
  intl_silver: {
    price: number | null;
    change: number | null;
    change_percent: number | null;
    unit: string;
    source: string | null;
  };
  gold_spread: {
    spread_vnd: number | null;
    spread_percent: number | null;
    intl_in_vnd: number | null;
    intl_per_luong: number | null;
  };
  silver_spread: {
    spread_vnd: number | null;
    spread_percent: number | null;
    intl_in_vnd: number | null;
    intl_per_luong: number | null;
    unit: string;
  };
}

export interface HistoryData {
  ts: string;
  usd_vnd: number | null;
  sjc_vnd_luong: number | null;
  phuquy_silver_vnd: number | null;
  phuquy_silver_unit: string | null;
  intl_gold_usd_oz: number | null;
  intl_gold_source: string | null;
  intl_silver_usd_oz: number | null;
  intl_silver_source: string | null;
  gold_spread_vnd: number | null;
  gold_spread_percent: number | null;
  silver_spread_vnd: number | null;
  silver_spread_percent: number | null;
  silver_spread_unit: string | null;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getTodayPrices(): Promise<{ success: boolean; data: PriceData }> {
    return this.request<{ success: boolean; data: PriceData }>('/api/prices/today');
  }

  async getPriceHistory(days: number = 7): Promise<{
    success: boolean;
    data: HistoryData[];
    count: number;
  }> {
    return this.request<{ success: boolean; data: HistoryData[]; count: number }>(
      `/api/prices/history?days=${days}`
    );
  }

  async getSjcItems(): Promise<{
    success: boolean;
    data: any[];
    count: number;
  }> {
    return this.request('/api/prices/sjc-items');
  }

  async getSjcItemHistory(
    name: string,
    branch?: string,
    days: number = 365
  ): Promise<{ success: boolean; data: any[]; count: number }> {
    const params = new URLSearchParams({
      name,
      days: days.toString(),
    });

    if (branch) {
      params.append('branch', branch);
    }

    return this.request(`/api/prices/sjc-item-history?${params.toString()}`);
  }

  async getPhuQuyItems(): Promise<{
    success: boolean;
    data: any[];
    count: number;
  }> {
    return this.request('/api/prices/phuquy-items');
  }

  async getPhuQuyItemHistory(
    product: string,
    days: number = 365
  ): Promise<{ success: boolean; data: any[]; count: number }> {
    return this.request(
      `/api/prices/phuquy-item-history?product=${encodeURIComponent(product)}&days=${days}`
    );
  }

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/api/health');
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for custom instances
export default ApiClient;
