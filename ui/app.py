"""
Price Tracker UI - Streamlit Application
Displays gold and silver prices from Vietnam and International markets
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from data_fetcher import PriceDataFetcher
import os
import time

# Page configuration
st.set_page_config(
    page_title="Price Tracker - Vàng & Bạc",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FFD700;
        background: linear-gradient(90deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .price-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        min-height: 260px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .price-value {
        font-size: 2.2rem;
        font-weight: bold;
        margin: 1rem 0;
        line-height: 1.05;
    }
    .price-label {
        font-size: 1.2rem;
        opacity: 0.9;
        min-height: 3.2rem;
    }
    .spread-positive {
        color: #4CAF50;
        font-weight: bold;
    }
    .spread-negative {
        color: #f44336;
        font-weight: bold;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
	    .compact-block {
	        color: #6b7280;
	        font-size: 0.74rem;
	        line-height: 1.15;
	    }
	    .compact-title {
	        font-size: 0.82rem;
	        font-weight: 700;
	        color: #111827;
	        margin: 0 0 0.2rem 0;
	    }
	    .compact-label {
	        font-size: 0.72rem;
	        margin: 0.2rem 0 0.1rem 0;
	    }
	    .compact-value {
	        font-size: 0.95rem;
	        font-weight: 700;
	        color: #111827;
	        margin: 0 0 0.15rem 0;
	    }
	    .compact-item {
	        margin: 0.2rem 0;
	    }
    .compact-item b {
        font-weight: 600;
    }

    /* Sidebar compact mode */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 0.8rem;
        padding-bottom: 0.8rem;
    }
    section[data-testid="stSidebar"] .stButton > button {
        padding: 0.35rem 0.7rem;
        font-size: 0.85rem;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stCheckbox {
        font-size: 0.85rem;
    }
    section[data-testid="stSidebar"] .stAlert {
        padding: 0.5rem 0.7rem;
        font-size: 0.82rem;
        line-height: 1.25;
    }
    .sidebar-title {
        font-size: 1.05rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        color: #111827;
    }
    .sidebar-subtitle {
        font-size: 0.92rem;
        font-weight: 700;
        margin: 0.4rem 0 0.2rem 0;
        color: #111827;
    }
    .card-footer {
        font-size: 0.9rem;
        opacity: 0.95;
    }
    .card-sub {
        font-size: 0.9rem;
        opacity: 0.9;
    }
	    .card-link {
	        display: block;
	        text-decoration: none;
	        color: inherit;
	        cursor: pointer;
	    }
	    .card-link:hover .price-card {
	        transform: translateY(-2px);
	        box-shadow: 0 8px 14px rgba(0,0,0,0.12);
	        transition: all 120ms ease-in-out;
	    }
    .detail-panel {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# Initialize data fetcher (avoid caching the object to prevent stale state when sources are flaky)
fetcher = PriceDataFetcher()

# Main title
st.markdown('<h1 class="main-title">🪙 PRICE TRACKER - VÀNG & BẠC</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False

    if st.button("⚙️ Cài đặt", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings

    # Defaults when settings are collapsed
    auto_refresh = st.session_state.get("auto_refresh", False)
    refresh_interval = st.session_state.get("refresh_interval", 60)
    st_autorefresh = st.session_state.get("st_autorefresh", False)

    if st.session_state.show_settings:
        st.markdown('<div class="sidebar-title">Cài đặt</div>', unsafe_allow_html=True)

        if st.button("🔄 Làm mới dữ liệu", type="primary", use_container_width=True, key="refresh_data"):
            st.success("Đã làm mới dữ liệu!")
            st.rerun()

        st.divider()

        auto_refresh = st.checkbox("Tự động làm mới", key="auto_refresh")
        if auto_refresh:
            refresh_interval = st.slider("Khoảng thời gian (giây)", 30, 300, 60, key="refresh_interval")
            st_autorefresh = st.checkbox("Bật tự động refresh", key="st_autorefresh")

        st.divider()

    # Info
    st.markdown('<div class="sidebar-subtitle">📊 Thông tin</div>', unsafe_allow_html=True)
    st.info(f"""
    **Cập nhật lần cuối:**
    {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}

    **Các nguồn dữ liệu:**
    - 🇻🇳 Vàng SJC
    - 🥈 Bạc Phú Quý
    - 🌎 MSN Money (quốc tế)
    """)

    if os.getenv("PRICE_TRACKER_DEBUG") == "1":
        with st.expander("🛠 Debug", expanded=False):
            import sys
            import uuid
            import requests

            st.code(f"python: {sys.executable}")
            st.code(f"fetcher: {type(fetcher).__name__}")
            st.code(f"intl_fetcher: {type(getattr(fetcher, 'intl_fetcher', None)).__name__}")
            try:
                fail_reason = getattr(fetcher.intl_fetcher, "_msn_state_fail_reason", None)
                failed_at = getattr(fetcher.intl_fetcher, "_msn_state_failed_at", None)
                st.code(f"msn_fail_reason: {fail_reason} at {failed_at}")
            except Exception:
                pass

            mod = sys.modules.get("international_metals_pkg")
            st.code(f"international_metals_pkg: {getattr(mod, '__file__', 'not imported')}")

            try:
                test_url = "https://www.msn.com/en-us/money"
                params = {"ocid": "msn", "cvid": uuid.uuid4().hex}
                r = requests.get(
                    test_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    params=params,
                    timeout=10,
                )
                redux_ok = 'id="redux-data"' in r.text
                st.code(f"MSN status={r.status_code} len={len(r.text)} redux_data={redux_ok}")
            except Exception as e:
                st.code(f"MSN request error: {e}")

# Tabs
tab1, tab2, tab3 = st.tabs(["📅 Today", "📈 History", "📊 Comparison"])

# ==================== TAB 1: TODAY ====================
with tab1:
    st.header("📅 GIÁ HÔM NAY")

    # Fetch data
    with st.spinner("Đang tải dữ liệu..."):
        data = fetcher.get_formatted_data()

    # Display update time
    st.caption(f"🕐 Cập nhật: {datetime.fromisoformat(data['update_time']).strftime('%H:%M:%S %d/%m/%Y')}")

    def _get_qparam(name: str):
        try:
            v = st.query_params.get(name)
            if isinstance(v, list):
                return v[0] if v else None
            return v
        except Exception:
            params = st.experimental_get_query_params()
            vals = params.get(name)
            return vals[0] if vals else None

    def _set_qparams(**kwargs):
        cleaned = {k: v for k, v in kwargs.items() if v is not None and v != ""}
        try:
            st.query_params.clear()
            st.query_params.update(cleaned)
        except Exception:
            st.experimental_set_query_params(**cleaned)

    if "selected_card" not in st.session_state:
        st.session_state.selected_card = None

    # Sync query param -> session state
    qp_card = _get_qparam("card")
    if qp_card:
        st.session_state.selected_card = qp_card
    else:
        st.session_state.selected_card = None

    selected = st.session_state.selected_card
    nonce = str(int(time.time() * 1000))

    def _card_href(key: str) -> str:
        return f"?n={nonce}" if selected == key else f"?card={key}&n={nonce}"

    # Main prices - 4 columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sjc_price = int(data["sjc_gold"]["price"]) if data["sjc_gold"]["price"] else 0
        sjc_html = """
        <a class="card-link" href="{href}" target="_self" aria-label="Chi tiết Vàng SJC">
          <div class="price-card">
              <div class="price-label">🇻🇳 Vàng SJC (1L-10L)</div>
              <div class="price-value">{price:,} VND</div>
              <div class="card-footer">/lượng</div>
          </div>
        </a>
        """.format(href=_card_href("sjc"), price=sjc_price)
        st.markdown(sjc_html, unsafe_allow_html=True)

    with col2:
        silver_vn_unit = data.get("phuquy_silver", {}).get("unit") or "VND/lượng"
        silver_vn_suffix = "/kg" if "kg" in silver_vn_unit.lower() else "/lượng"
        silver_vn_label = "🥈 Bạc Phú Quý (1 kg)" if "kg" in silver_vn_unit.lower() else "🥈 Bạc Phú Quý (1 lượng)"
        pq_price = int(data["phuquy_silver"]["price"]) if data["phuquy_silver"]["price"] else 0
        pq_html = """
        <a class="card-link" href="{href}" target="_self" aria-label="Chi tiết Bạc Phú Quý">
          <div class="price-card">
              <div class="price-label">{label}</div>
              <div class="price-value">{price:,} VND</div>
              <div class="card-footer">{unit}</div>
          </div>
        </a>
        """.format(href=_card_href("phuquy"), label=silver_vn_label, price=pq_price, unit=silver_vn_suffix)
        st.markdown(pq_html, unsafe_allow_html=True)

    with col3:
        gold_price = data["intl_gold"]["price"]
        gold_change = data["intl_gold"]["change"]
        gold_change_pct = data["intl_gold"]["change_percent"]

        if gold_price is None:
            gold_price_html = "N/A"
            gold_change_html = '<div class="card-sub">Không có dữ liệu</div>'
        else:
            gold_change = gold_change or 0
            gold_change_pct = gold_change_pct or 0
            gold_change_class = "spread-positive" if gold_change >= 0 else "spread-negative"
            gold_price_html = f"${gold_price:.2f}"
            gold_change_html = f'<div class="{gold_change_class}">{gold_change:+.2f} ({gold_change_pct:+.2f}%)</div>'

        intl_gold_html = f"""
        <a class="card-link" href="{_card_href('intl_gold')}" target="_self" aria-label="Chi tiết Vàng Thế Giới">
          <div class="price-card">
              <div class="price-label">🌎 Vàng Thế Giới (COMEX Futures)</div>
              <div class="price-value">{gold_price_html}</div>
              {gold_change_html}
              <div class="card-footer">/oz</div>
          </div>
        </a>
        """
        st.markdown(intl_gold_html, unsafe_allow_html=True)

    with col4:
        silver_price = data["intl_silver"]["price"]
        silver_change = data["intl_silver"]["change"]
        silver_change_pct = data["intl_silver"]["change_percent"]

        if silver_price is None:
            silver_price_html = "N/A"
            silver_change_html = '<div class="card-sub">Không có dữ liệu</div>'
        else:
            silver_change = silver_change or 0
            silver_change_pct = silver_change_pct or 0
            silver_change_class = "spread-positive" if silver_change >= 0 else "spread-negative"
            silver_price_html = f"${silver_price:.2f}"
            silver_change_html = f'<div class="{silver_change_class}">{silver_change:+.2f} ({silver_change_pct:+.2f}%)</div>'

        intl_silver_html = f"""
        <a class="card-link" href="{_card_href('intl_silver')}" target="_self" aria-label="Chi tiết Bạc Thế Giới">
          <div class="price-card">
              <div class="price-label">🌎 Bạc Thế Giới (COMEX Futures)</div>
              <div class="price-value">{silver_price_html}</div>
              {silver_change_html}
              <div class="card-footer">/oz</div>
          </div>
        </a>
        """
        st.markdown(intl_silver_html, unsafe_allow_html=True)

    if selected:
        st.divider()
        with st.expander("🔎 Chi tiết", expanded=True):
            if st.button("Đóng", key="close_details", use_container_width=False):
                _set_qparams(n=nonce)
                st.rerun()

            def _pick_past_value(df, time_col: str, value_col: str, target_ts):
                if df is None or df.empty or value_col not in df.columns:
                    return None
                x = df[df[time_col] <= target_ts]
                if x.empty:
                    return None
                val = x[value_col].iloc[-1]
                try:
                    return float(val)
                except Exception:
                    return None

            def _delta_block(current, past):
                if current is None or past is None or past == 0:
                    return None, None
                return current - past, ((current - past) / past) * 100

            df_snap = fetcher.get_history(days_back=400)
            if df_snap is not None and not df_snap.empty:
                df_snap["time"] = pd.to_datetime(df_snap["ts"], errors="coerce")
                df_snap = df_snap.dropna(subset=["time"])
            now_ts = datetime.now()

            if selected == "sjc":
                st.subheader("🇻🇳 Vàng SJC")
                items = fetcher.get_sjc_items_latest()
                if items is None or items.empty:
                    st.info("Chưa có dữ liệu chi tiết SJC trong DB. Hãy refresh tab Today vài lần.")
                else:
                    names = sorted(items["name"].dropna().unique().tolist(), key=lambda x: str(x))
                    default_name = next((n for n in names if "SJC" in str(n)), names[0])
                    name = st.selectbox("Sản phẩm", names, index=names.index(default_name) if default_name in names else 0)
                    branches = (
                        sorted(items[items["name"] == name]["branch"].dropna().unique().tolist(), key=lambda x: str(x))
                        if "branch" in items.columns
                        else []
                    )
                    branch = None
                    if branches:
                        branch = st.selectbox("Chi nhánh", branches, index=0)

                    df_item = fetcher.get_sjc_item_history(name=name, branch=branch, days_back=400)
                    df_item["time"] = pd.to_datetime(df_item["ts"], errors="coerce")
                    df_item = df_item.dropna(subset=["time"])
                    current = df_item["buy_price"].iloc[-1] if not df_item.empty else None
                    if current is not None:
                        st.caption(f"Giá mua hiện tại: {current:,.0f} VND/lượng")

                    periods = [("1D", 1), ("1W", 7), ("1M", 30), ("1Y", 365)]
                    cols = st.columns(4)
                    for i, (label, days) in enumerate(periods):
                        target = now_ts - timedelta(days=days)
                        past = _pick_past_value(df_item, "time", "buy_price", target)
                        d, p = _delta_block(current, past)
                        cols[i].metric(
                            label=label,
                            value=f"{d:+,.0f} VND" if d is not None else "N/A",
                            delta=f"{p:+.2f}%" if p is not None else "N/A",
                        )

                    st.divider()
                    if not df_item.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df_item["time"], y=df_item["buy_price"], mode="lines+markers"))
                        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                    show_cols = [c for c in ["ts", "branch", "buy_price", "sell_price"] if c in df_item.columns]
                    st.dataframe(df_item[show_cols].sort_values("ts", ascending=False), use_container_width=True)

            elif selected == "phuquy":
                st.subheader("🥈 Bạc Phú Quý")
                items = fetcher.get_phuquy_items_latest()
                if items is None or items.empty:
                    st.info("Chưa có dữ liệu chi tiết Phú Quý trong DB. Hãy refresh tab Today vài lần.")
                else:
                    products = sorted(items["product"].dropna().unique().tolist(), key=lambda x: str(x))
                    default_p = next((p for p in products if "1KILO" in str(p).upper()), products[0])
                    product = st.selectbox("Sản phẩm", products, index=products.index(default_p) if default_p in products else 0)
                    df_item = fetcher.get_phuquy_item_history(product=product, days_back=400)
                    df_item["time"] = pd.to_datetime(df_item["ts"], errors="coerce")
                    df_item = df_item.dropna(subset=["time"])
                    current = df_item["buy_price"].iloc[-1] if not df_item.empty else None
                    unit = df_item["unit"].dropna().iloc[-1] if "unit" in df_item.columns and df_item["unit"].notna().any() else ""
                    if current is not None:
                        st.caption(f"Giá mua hiện tại: {current:,.0f} {unit}")

                    periods = [("1D", 1), ("1W", 7), ("1M", 30), ("1Y", 365)]
                    cols = st.columns(4)
                    for i, (label, days) in enumerate(periods):
                        target = now_ts - timedelta(days=days)
                        past = _pick_past_value(df_item, "time", "buy_price", target)
                        d, p = _delta_block(current, past)
                        cols[i].metric(
                            label=label,
                            value=f"{d:+,.0f}" if d is not None else "N/A",
                            delta=f"{p:+.2f}%" if p is not None else "N/A",
                        )

                    st.divider()
                    if not df_item.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df_item["time"], y=df_item["buy_price"], mode="lines+markers"))
                        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                    show_cols = [c for c in ["ts", "buy_price", "sell_price", "unit"] if c in df_item.columns]
                    st.dataframe(df_item[show_cols].sort_values("ts", ascending=False), use_container_width=True)

            elif selected in {"intl_gold", "intl_silver"}:
                is_gold = selected == "intl_gold"
                title = "🌎 Vàng Thế Giới (COMEX Futures)" if is_gold else "🌎 Bạc Thế Giới (COMEX Futures)"
                col = "intl_gold_usd_oz" if is_gold else "intl_silver_usd_oz"
                st.subheader(title)
                if df_snap is None or df_snap.empty or col not in df_snap.columns:
                    st.info("Chưa có dữ liệu lịch sử thế giới. Hãy refresh tab Today vài lần.")
                else:
                    series = df_snap[["time", col]].dropna()
                    current = float(series[col].iloc[-1]) if not series.empty else None
                    if current is not None:
                        st.caption(f"Giá hiện tại: ${current:.2f}/oz")
                    periods = [("1D", 1), ("1W", 7), ("1M", 30), ("1Y", 365)]
                    cols = st.columns(4)
                    for i, (label, days) in enumerate(periods):
                        target = now_ts - timedelta(days=days)
                        past = _pick_past_value(series, "time", col, target)
                        d, p = _delta_block(current, past)
                        cols[i].metric(
                            label=label,
                            value=f"{d:+.2f}" if d is not None else "N/A",
                            delta=f"{p:+.2f}%" if p is not None else "N/A",
                        )
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=series["time"], y=series[col], mode="lines+markers"))
                    fig.update_layout(height=280, margin=dict(l=10, r=10, t=20, b=10))
                    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Spreads section
    st.subheader("📊 CHÊNH LỆCH GIÁ (VN vs THẾ GIỚI)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🪙 Vàng SJC vs Thế Giới")

        if data['gold_spread']['spread_vnd'] is not None:
            spread_vnd = data['gold_spread']['spread_vnd']
            spread_pct = data['gold_spread']['spread_percent']
            intl_vnd = data['gold_spread']['intl_in_vnd']
            intl_luong = data['gold_spread']['intl_per_luong']

            spread_class = "spread-positive" if spread_vnd > 0 else "spread-negative"

            st.metric(
                label="Chênh lệch",
                value=f"{spread_vnd:,.0f} VND/lượng",
                delta=f"{spread_pct:+.2f}%"
            )

            st.info(f"""
            **Giá thế giới quy đổi:**
            - {intl_vnd:,.0f} VND/oz
            - {intl_luong:,.0f} VND/lượng
            - (1 oz = {PriceDataFetcher.OZ_TO_GRAM}g = {PriceDataFetcher.OZ_TO_LUONG:.4f} lượng)
            """)
        else:
            st.warning("Không thể tính chênh lệch (thiếu dữ liệu)")

    with col2:
        st.markdown("### 🥈 Bạc Phú Quý vs Thế Giới")

        if data['silver_spread']['spread_vnd'] is not None:
            spread_vnd = data['silver_spread']['spread_vnd']
            spread_pct = data['silver_spread']['spread_percent']
            intl_vnd = data['silver_spread']['intl_in_vnd']
            intl_luong = data['silver_spread']['intl_per_luong']
            spread_unit = data.get('silver_spread', {}).get('unit') or 'VND/lượng'
            spread_suffix = "/kg" if "kg" in spread_unit.lower() else "/lượng"

            spread_class = "spread-positive" if spread_vnd > 0 else "spread-negative"

            st.metric(
                label="Chênh lệch",
                value=f"{spread_vnd:,.0f} VND{spread_suffix}",
                delta=f"{spread_pct:+.2f}%"
            )

            st.info(f"""
            **Giá thế giới quy đổi:**
            - {intl_vnd:,.0f} VND/oz
            - {intl_luong:,.0f} VND{spread_suffix}
            - (1 oz = {PriceDataFetcher.OZ_TO_GRAM}g = {PriceDataFetcher.OZ_TO_LUONG:.4f} lượng)
            """)
        else:
            st.warning("Không thể tính chênh lệch (thiếu dữ liệu)")

    st.divider()

    # Additional info
    col1, col2, col3 = st.columns(3)

    with col1:
        usd_vnd = data.get("usd_vnd")
        usd_text = f"{usd_vnd:,.0f} VND" if usd_vnd else "N/A"
        st.markdown(
            f"""
            <div class="compact-block">
              <div class="compact-title">💵 Tỷ giá USD/VND</div>
              <div class="compact-label">USD bán ra</div>
              <div class="compact-value">{usd_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="compact-block">
              <div class="compact-title">📈 Conversion Factors</div>
              <div class="compact-label">1 Oz → Gram</div>
              <div class="compact-value">{PriceDataFetcher.OZ_TO_GRAM}g</div>
              <div class="compact-label">1 Lượng → Gram</div>
              <div class="compact-value">{PriceDataFetcher.LUONG_TO_GRAM}g</div>
              <div class="compact-label">1 Oz → Lượng</div>
              <div class="compact-value">{PriceDataFetcher.OZ_TO_LUONG:.4f} lượng</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        gold_src = data.get("intl_gold", {}).get("source") or "N/A"
        silver_src = data.get("intl_silver", {}).get("source") or "N/A"
        st.markdown(
            f"""
            <div class="compact-block">
              <div class="compact-title">🔗 Nguồn dữ liệu</div>
              <div class="compact-item">🇻🇳 <b>Vàng SJC</b>: vnstock/phuquygroup.vn</div>
              <div class="compact-item">🥈 <b>Bạc PQ</b>: giabac.phuquygroup.vn</div>
              <div class="compact-item">🌎 <b>World Gold</b>: {gold_src}</div>
              <div class="compact-item">🌎 <b>World Silver</b>: {silver_src}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==================== TAB 2: HISTORY ====================
with tab2:
    st.header("📈 LỊCH SỬ GIÁ")

    days_back = st.slider("Số ngày hiển thị", 1, 30, 7)
    # Day-by-day history (1 point/day), instead of every refresh.
    df_hist = fetcher.get_history_daily(days_back=days_back)

    if df_hist is None or df_hist.empty:
        st.info("Chưa có dữ liệu lịch sử. Hãy mở tab Today để tải dữ liệu vài lần.")
    else:
        df_hist["time"] = pd.to_datetime(df_hist["ts"].astype(str).str.slice(0, 10), errors="coerce")
        df_hist = df_hist.dropna(subset=["time"])
        st.caption(f"📦 {len(df_hist)} điểm dữ liệu | Từ {df_hist['time'].min()} đến {df_hist['time'].max()}")

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hist["time"],
                    y=df_hist["sjc_vnd_luong"],
                    mode="lines+markers",
                    name="Vàng SJC (VND/lượng)",
                )
            )
            fig.update_layout(title="Vàng SJC", height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = go.Figure()
            silver_unit = (
                (df_hist["phuquy_silver_unit"].dropna().iloc[-1])
                if "phuquy_silver_unit" in df_hist.columns and df_hist["phuquy_silver_unit"].notna().any()
                else "VND/lượng"
            )
            fig.add_trace(
                go.Scatter(
                    x=df_hist["time"],
                    y=df_hist["phuquy_silver_vnd"],
                    mode="lines+markers",
                    name=f"Bạc Phú Quý ({silver_unit})",
                )
            )
            fig.update_layout(title="Bạc Phú Quý", height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hist["time"],
                    y=df_hist["intl_gold_usd_oz"],
                    mode="lines+markers",
                    name="Gold (USD/oz)",
                )
            )
            fig.update_layout(title="Vàng Thế Giới (USD/oz)", height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hist["time"],
                    y=df_hist["intl_silver_usd_oz"],
                    mode="lines+markers",
                    name="Silver (USD/oz)",
                )
            )
            fig.update_layout(title="Bạc Thế Giới (USD/oz)", height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=df_hist["time"],
                    y=df_hist["gold_spread_vnd"],
                    name="Chênh lệch vàng (VND/lượng)",
                )
            )
            fig.update_layout(title="Chênh lệch Vàng (VN - World)", height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = go.Figure()
            spread_unit = (
                (df_hist["silver_spread_unit"].dropna().iloc[-1])
                if "silver_spread_unit" in df_hist.columns and df_hist["silver_spread_unit"].notna().any()
                else "VND/lượng"
            )
            fig.add_trace(
                go.Bar(
                    x=df_hist["time"],
                    y=df_hist["silver_spread_vnd"],
                    name=f"Chênh lệch bạc ({spread_unit})",
                )
            )
            fig.update_layout(title="Chênh lệch Bạc (VN - World)", height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Xem dữ liệu thô", expanded=False):
            show_cols = [
                "ts",
                "usd_vnd",
                "sjc_vnd_luong",
                "phuquy_silver_vnd",
                "phuquy_silver_unit",
                "intl_gold_usd_oz",
                "intl_gold_source",
                "intl_silver_usd_oz",
                "intl_silver_source",
                "gold_spread_vnd",
                "gold_spread_percent",
                "silver_spread_vnd",
                "silver_spread_percent",
                "silver_spread_unit",
            ]
            existing = [c for c in show_cols if c in df_hist.columns]
            st.dataframe(df_hist[existing].sort_values("ts", ascending=False), use_container_width=True)

# ==================== TAB 3: COMPARISON ====================
with tab3:
    st.header("📊 SO SÁNH CHI TIẾT")

    # Create comparison table
    if all([
        data["sjc_gold"]["price"],
        data["phuquy_silver"]["price"],
        data["intl_gold"]["price"],
        data["intl_silver"]["price"],
    ]):
        comparison_data = {
            "Loại": ["Vàng SJC", "Bạc Phú Quý", "Vàng Thế Giới", "Bạc Thế Giới"],
            "Giá": [
                f"{data['sjc_gold']['price']:,.0f} VND/lượng",
                f"{data['phuquy_silver']['price']:,.0f} VND{('/kg' if 'kg' in (data.get('phuquy_silver', {}).get('unit') or '').lower() else '/lượng')}",
                f"${data['intl_gold']['price']:.2f}/oz",
                f"${data['intl_silver']['price']:.2f}/oz",
            ],
            "Thay đổi": [
                "N/A",
                "N/A",
                f"{data['intl_gold']['change']:+.2f} ({data['intl_gold']['change_percent']:+.2f}%)",
                f"{data['intl_silver']['change']:+.2f} ({data['intl_silver']['change_percent']:+.2f}%)",
            ],
            "Nguồn": [
                "SJC",
                "Phú Quý",
                data.get("intl_gold", {}).get("source") or "N/A",
                data.get("intl_silver", {}).get("source") or "N/A",
            ],
        }

        df = pd.DataFrame(comparison_data)
        st.table(df)

        # Ratio: Gold/Silver
        if data["intl_gold"]["price"] and data["intl_silver"]["price"]:
            ratio = data["intl_gold"]["price"] / data["intl_silver"]["price"]
            st.metric("📊 Tỷ lệ Gold/Silver", f"{ratio:.2f}:1")

    else:
        st.warning("Thiếu dữ liệu để so sánh")

    st.divider()

    # Gold/Silver ratio chart
    st.subheader("📊 Biểu đồ so sánh")

    # Simple bar chart
    fig = go.Figure()

    # Add bars
    if data['sjc_gold']['price']:
        fig.add_trace(go.Bar(
            name='Vàng SJC (triệu VND)',
            x=['Vàng VN'],
            y=[data['sjc_gold']['price'] / 1_000_000],
            marker_color='gold'
        ))

    if data['phuquy_silver']['price']:
        fig.add_trace(go.Bar(
            name='Bạc PQ (nghìn VND)',
            x=['Bạc VN'],
            y=[data['phuquy_silver']['price'] / 1_000],
            marker_color='silver'
        ))

    fig.update_layout(
        title='So sánh giá vàng và bạc (khác đơn vị)',
        barmode='group',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9rem;'>
    <p>💡 Dữ liệu chỉ mang tính tham khảo. Vui lòng xác nhận với nguồn chính thức trước khi giao dịch.</p>
    <p>🔄 Tự động làm mới mỗi 10 phút | 📊 Cập nhật real-time từ các nguồn uy tín</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh logic
if auto_refresh and st_autorefresh:
    import time
    time.sleep(refresh_interval)
    st.rerun()
