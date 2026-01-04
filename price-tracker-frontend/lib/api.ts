/**
 * API Client for Price Tracker Backend
 * Communicates with FastAPI backend
 */

// Prefer same-origin `/api/*` and rely on Next.js rewrites (see `next.config.ts`)
// to proxy to the backend. This avoids CORS and "wrong URL" issues in dev/prod.
const API_BASE_URL = '';
const FALLBACK_BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || 'http://localhost:8000';

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
  paxg?: {
    price: number | null;
    change: number | null;
    change_percent: number | null;
    unit: string;
    source: string | null;
  };
  xaut?: {
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
  paxg_usd_oz?: number | null;
  paxg_source?: string | null;
  xaut_usd_oz?: number | null;
  xaut_source?: string | null;
  gold_spread_vnd: number | null;
  gold_spread_percent: number | null;
  silver_spread_vnd: number | null;
  silver_spread_percent: number | null;
  silver_spread_unit: string | null;
}

export type ReservesKind = 'gold' | 'non_gold' | 'total';

export interface ReservesTopRow {
  rank: number;
  iso2: string;
  country_name: string;
  value_usd: number;
  data_end_year: number;
}

export interface ReservesCountryMeta {
  iso2: string;
  country_name: string;
  year_range: { start: number; end: number };
  note: string | null;
}

export interface ReservesCountryRow {
  year: number;
  total_reserves_usd: number | null;
  non_gold_reserves_usd: number | null;
  gold_value_usd_inferred: number | null;
  quality_flag: string | null;
}

export interface WgcGoldRow {
  rank?: number;
  country_name: string;
  iso2?: string | null;
  tonnes: number | null;
  pct_of_reserves: number | null;
  value_usd: number | null;
  holdings_as_of: string | null;
  retrieved_at_utc: string | null;
  source: 'WGC';
}

export interface WgcMeta {
  holdings_as_of: string | null;
  retrieved_at_utc: string | null;
  valuation?: {
    spot_price_usd_oz: number | null;
    spot_source: string | null;
    spot_retrieved_at: string | null;
    note: string | null;
  };
}

export interface SjcItemRow {
  ts: string;
  name: string;
  branch?: string | null;
  buy_price?: number | null;
  sell_price?: number | null;
  date?: string | null;
}

export interface SjcItemHistoryRow {
  ts: string;
  name?: string;
  branch?: string | null;
  buy_price?: number | null;
  sell_price?: number | null;
}

export interface PhuQuyItemRow {
  ts: string;
  product: string;
  unit?: string | null;
  buy_price?: number | null;
  sell_price?: number | null;
}

export interface PhuQuyItemHistoryRow {
  ts: string;
  product?: string;
  unit?: string | null;
  buy_price?: number | null;
  sell_price?: number | null;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const primaryUrl = `${this.baseUrl}${endpoint}`;

    const method = (options?.method || 'GET').toUpperCase();
    const headers = new Headers(options?.headers);
    if (!headers.has('Accept')) headers.set('Accept', 'application/json');
    if ((method !== 'GET' && method !== 'HEAD') && options?.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const doFetch = async (url: string) => {
      const response = await fetch(url, { ...options, method, headers });
      if (!response.ok) {
        const err = new Error(`API Error: ${response.status} ${response.statusText}`);
        (err as Error & { status?: number }).status = response.status;
        throw err;
      }
      return response.json();
    };

    try {
      return await doFetch(primaryUrl);
    } catch (error) {
      // If Next.js rewrite/proxy isn't active (common when dev server runs on a different port),
      // fall back to calling the backend directly.
      const shouldFallback =
        this.baseUrl === '' &&
        endpoint.startsWith('/api/') &&
        typeof FALLBACK_BACKEND_URL === 'string' &&
        FALLBACK_BACKEND_URL.length > 0;

      if (shouldFallback) {
        try {
          const fallbackUrl = `${FALLBACK_BACKEND_URL}${endpoint}`;
          return await doFetch(fallbackUrl);
        } catch (fallbackError) {
          console.error(`API request failed (primary+fallback): ${endpoint}`, error, fallbackError);
          throw fallbackError;
        }
      }

      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getTodayPrices(): Promise<{ success: boolean; data: PriceData }> {
    const res = await this.request<{ success: boolean; data: any }>('/api/prices/today');
    if (res?.success && res?.data) {
      const tokenDefault = { price: null, change: null, change_percent: null, unit: 'USD/oz', source: null };
      res.data.paxg = res.data.paxg ?? tokenDefault;
      res.data.xaut = res.data.xaut ?? tokenDefault;
    }
    return res as { success: boolean; data: PriceData };
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
    data: SjcItemRow[];
    count: number;
  }> {
    return this.request('/api/prices/sjc-items');
  }

  async getSjcItemHistory(
    name: string,
    branch?: string,
    days: number = 365
  ): Promise<{ success: boolean; data: SjcItemHistoryRow[]; count: number }> {
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
    data: PhuQuyItemRow[];
    count: number;
  }> {
    return this.request('/api/prices/phuquy-items');
  }

  async getPhuQuyItemHistory(
    product: string,
    days: number = 365
  ): Promise<{ success: boolean; data: PhuQuyItemHistoryRow[]; count: number }> {
    return this.request(
      `/api/prices/phuquy-item-history?product=${encodeURIComponent(product)}&days=${days}`
    );
  }

  async getReservesTop(kind: ReservesKind = 'gold', limit: number = 20): Promise<{
    success: boolean;
    kind: ReservesKind;
    year: number;
    global_end_year: number;
    count: number;
    data: ReservesTopRow[];
  }> {
    return this.request(`/api/reserves/top?kind=${kind}&limit=${limit}`);
  }

  async getReservesCountry(iso2: string): Promise<{
    success: boolean;
    global_year_range: { start: number; end: number };
    country: ReservesCountryMeta;
    data: ReservesCountryRow[];
    count: number;
  }> {
    const params = new URLSearchParams({ iso2 });
    return this.request(`/api/reserves/country?${params.toString()}`);
  }

  async getWgcTop(limit: number = 20, sort: 'tonnes' | 'value_usd' = 'tonnes'): Promise<{
    success: boolean;
    meta: WgcMeta | null;
    sort: 'tonnes' | 'value_usd';
    count: number;
    data: WgcGoldRow[];
  }> {
    return this.request(`/api/reserves/wgc/top?limit=${limit}&sort=${sort}`);
  }

  async refreshWgc(): Promise<{ success: boolean; meta: WgcMeta | null; count: number }> {
    return this.request(`/api/reserves/wgc/refresh`, { method: 'POST' });
  }

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/api/health');
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for custom instances
export default ApiClient;
