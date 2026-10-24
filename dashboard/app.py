"""
Argus Platform — Multi-Source Public Health Intelligence
Ultra-premium Streamlit command interface.
"""
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────
API_BASE = "https://api.savflux.com"

st.set_page_config(
    page_title="ARGUS · Surveillance Intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────────────────────
OBSIDIAN     = "#05070B"
GRAPHITE     = "#0B0F17"
GLASS        = "rgba(20, 26, 38, 0.55)"
HAIRLINE     = "rgba(120, 180, 255, 0.12)"
SIGNAL_CYAN  = "#4FE3FF"
SIGNAL_AMBER = "#FFB347"
SIGNAL_RED   = "#FF4D6D"
SIGNAL_MINT  = "#5CF2B4"
TEXT_PRIMARY = "#E8EEF7"
TEXT_MUTED   = "#7A8699"

CUSTOM_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {{
      font-family: 'Inter', -apple-system, sans-serif;
      color: {TEXT_PRIMARY};
  }}

  .stApp {{
      background:
        radial-gradient(1200px 600px at 15% -10%, rgba(79, 227, 255, 0.06), transparent 60%),
        radial-gradient(900px 500px at 95% 110%, rgba(255, 77, 109, 0.05), transparent 60%),
        {OBSIDIAN};
  }}

  /* Kill Streamlit chrome */
  #MainMenu, footer, header {{ visibility: hidden; }}

  /* Sidebar — glass slab */
  section[data-testid="stSidebar"] > div {{
      background: linear-gradient(180deg, rgba(11,15,23,0.95), rgba(5,7,11,0.98));
      border-right: 1px solid {HAIRLINE};
      backdrop-filter: blur(18px);
  }}
  section[data-testid="stSidebar"] * {{
      font-family: 'JetBrains Mono', monospace !important;
  }}

  /* Typography hierarchy */
  h1, h2, h3 {{
      font-family: 'Inter', sans-serif;
      letter-spacing: -0.02em;
      color: {TEXT_PRIMARY};
  }}

  /* Hero strip */
  .argus-hero {{
      position: relative;
      padding: 2.2rem 2.4rem;
      margin-bottom: 1.8rem;
      border-radius: 18px;
      background: linear-gradient(135deg, rgba(20,26,38,0.85), rgba(11,15,23,0.85));
      border: 1px solid {HAIRLINE};
      backdrop-filter: blur(24px);
      overflow: hidden;
  }}
  .argus-hero::before {{
      content: "";
      position: absolute; inset: 0;
      background: linear-gradient(90deg,
        transparent 0%,
        rgba(79, 227, 255, 0.10) 50%,
        transparent 100%);
      animation: scan 6s linear infinite;
      pointer-events: none;
  }}
  @keyframes scan {{
      0%   {{ transform: translateX(-100%); }}
      100% {{ transform: translateX(100%); }}
  }}
  .argus-eyebrow {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      letter-spacing: 0.32em;
      color: {SIGNAL_CYAN};
      text-transform: uppercase;
      margin-bottom: 0.6rem;
      opacity: 0.85;
  }}
  .argus-title {{
      font-size: 2.6rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      line-height: 1.05;
      background: linear-gradient(120deg, #FFFFFF 0%, {SIGNAL_CYAN} 55%, #FFFFFF 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
  }}
  .argus-subtitle {{
      margin-top: 0.55rem;
      font-size: 0.95rem;
      color: {TEXT_MUTED};
      font-weight: 300;
      max-width: 720px;
  }}

  /* Metric tiles */
  div[data-testid="stMetric"] {{
      background: {GLASS};
      border: 1px solid {HAIRLINE};
      border-radius: 14px;
      padding: 1.1rem 1.25rem;
      backdrop-filter: blur(20px);
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }}
  div[data-testid="stMetric"]:hover {{
      border-color: rgba(79, 227, 255, 0.35);
      box-shadow: 0 0 24px rgba(79, 227, 255, 0.12);
      transform: translateY(-2px);
  }}
  div[data-testid="stMetricLabel"] {{
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 0.72rem !important;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: {TEXT_MUTED} !important;
  }}
  div[data-testid="stMetricValue"] {{
      font-family: 'Inter', sans-serif !important;
      font-size: 2.0rem !important;
      font-weight: 600;
      color: {TEXT_PRIMARY} !important;
      letter-spacing: -0.02em;
  }}

  /* Section labels */
  .section-label {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      letter-spacing: 0.32em;
      text-transform: uppercase;
      color: {TEXT_MUTED};
      margin: 1.8rem 0 0.8rem 0;
      display: flex;
      align-items: center;
      gap: 0.8rem;
  }}
  .section-label::after {{
      content: "";
      flex: 1;
      height: 1px;
      background: linear-gradient(90deg, {HAIRLINE}, transparent);
  }}

  /* Plotly container */
  div[data-testid="stPlotlyChart"] {{
      background: {GLASS};
      border: 1px solid {HAIRLINE};
      border-radius: 16px;
      padding: 1rem 1rem 0.5rem 1rem;
      backdrop-filter: blur(20px);
  }}

  /* Buttons / selectors */
  .stRadio > label, .stSelectbox > label, .stSlider > label {{
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 0.7rem !important;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: {TEXT_MUTED} !important;
  }}

  /* Status pill */
  .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.4rem 0.85rem;
      border-radius: 999px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      border: 1px solid;
  }}
  .status-online  {{ color: {SIGNAL_MINT}; border-color: rgba(92,242,180,0.4); background: rgba(92,242,180,0.08); }}
  .status-offline {{ color: {SIGNAL_RED};  border-color: rgba(255,77,109,0.4); background: rgba(255,77,109,0.08); }}
  .status-dot     {{ width: 8px; height: 8px; border-radius: 50%; }}
  .status-dot.online  {{ background: {SIGNAL_MINT}; box-shadow: 0 0 10px {SIGNAL_MINT}; animation: pulse 2s ease-in-out infinite; }}
  .status-dot.offline {{ background: {SIGNAL_RED};  box-shadow: 0 0 10px {SIGNAL_RED}; }}
  @keyframes pulse {{
      0%, 100% {{ opacity: 1; }}
      50%      {{ opacity: 0.35; }}
  }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="argus-hero">
        <div class="argus-eyebrow">◉ &nbsp; Argus · Surveillance Intelligence</div>
        <div class="argus-title">Multi-Source Public Health<br/>Signal Detection</div>
        <div class="argus-subtitle">
            Real-time epidemiological surveillance across wastewater, clinical,
            and syndromic data streams — powered by adaptive anomaly detection.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR — COMMAND DECK
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    f"<div class='argus-eyebrow' style='margin-bottom:1.2rem;'>◉ Command Deck</div>",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    "<div class='section-label'>Query Parameters</div>",
    unsafe_allow_html=True,
)
state = st.sidebar.selectbox("Region · NWSS", ["CA", "TX", "NY", "FL", "GA"])
model_choice = st.sidebar.radio(
    "Detection Algorithm",
    ["farrington", "hybrid"],
    help="Farrington: classical epidemic threshold. Hybrid: adaptive ensemble.",
)
warmup_weeks = st.sidebar.slider(
    "Warmup Window (weeks)", min_value=5, max_value=30, value=10
)

# ─────────────────────────────────────────────────────────────────────────────
#  API HEALTH
# ─────────────────────────────────────────────────────────────────────────────
api_online = False
try:
    health = requests.get(f"{API_BASE}/health", timeout=5).json()
    api_online = health.get("status") == "ok"
except Exception:
    api_online = False

pill_class = "online" if api_online else "offline"
pill_label = "Uplink Active" if api_online else "Uplink Offline"
st.sidebar.markdown(
    f"""
    <div style="margin-top:1.2rem;">
        <div class="status-pill status-{pill_class}">
            <span class="status-dot {pill_class}"></span>
            {pill_label}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
#  DATA FETCH (PARALLEL)
# ─────────────────────────────────────────────────────────────────────────────
import concurrent.futures

def fetch_backtest(model: str, state: str, warmup: int) -> pd.DataFrame:
    url = f"{API_BASE}/backtest?state={state}&model={model}&warmup={warmup}"
    res = requests.get(url, timeout=90)
    res.raise_for_status()
    df = pd.DataFrame(res.json()["results"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

with st.spinner(f"Calibrating detection engines for {state}…"):
    try:
        # Fetch metrics and both models concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_metrics = executor.submit(requests.get, f"{API_BASE}/alerts?state={state}&p90_window=6", timeout=30)
            future_farr = executor.submit(fetch_backtest, "farrington", state, warmup_weeks)
            future_hyb = executor.submit(fetch_backtest, "hybrid", state, warmup_weeks)
            
            metrics = future_metrics.result().json()
            df_farr = future_farr.result()
            df_hyb = future_hyb.result()

        # ── Metrics ──
        st.markdown(
            "<div class='section-label'>Detection Performance · Farrington Baseline</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sensitivity", f"{metrics.get('sensitivity', 0)*100:.1f}%")
        c2.metric("Specificity", f"{metrics.get('specificity', 0)*100:.1f}%")
        lead = metrics.get("lead_time_median_days")
        c3.metric("Median Lead Time", f"{lead:.0f} d" if lead else "—")
        c4.metric("Alerts Emitted", metrics.get("n_alerts", 0))

        # ── Chart ──
        st.markdown(
            f"<div class='section-label'>Signal Telemetry · {state} · Algorithm Comparison</div>",
            unsafe_allow_html=True,
        )

        pio.templates["argus"] = go.layout.Template(
            layout=go.Layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color=TEXT_PRIMARY, size=12),
                xaxis=dict(
                    gridcolor="rgba(120,180,255,0.06)",
                    zerolinecolor="rgba(120,180,255,0.12)",
                    tickfont=dict(family="JetBrains Mono", color=TEXT_MUTED, size=10),
                ),
                yaxis=dict(
                    gridcolor="rgba(120,180,255,0.06)",
                    zerolinecolor="rgba(120,180,255,0.12)",
                    tickfont=dict(family="JetBrains Mono", color=TEXT_MUTED, size=10),
                ),
                legend=dict(
                    bgcolor="rgba(11,15,23,0.6)",
                    bordercolor=HAIRLINE,
                    borderwidth=1,
                    font=dict(family="JetBrains Mono", size=10, color=TEXT_PRIMARY),
                ),
                hoverlabel=dict(
                    bgcolor=GRAPHITE,
                    bordercolor=SIGNAL_CYAN,
                    font=dict(family="JetBrains Mono", size=11, color=TEXT_PRIMARY),
                ),
            )
        )
        pio.templates.default = "argus"

        fig = go.Figure()

        # Observed (Base line)
        fig.add_trace(go.Scatter(
            x=df_farr["timestamp"], y=df_farr["observed"],
            mode="lines", name="Observed",
            line=dict(color=SIGNAL_CYAN, width=2.2),
            fill="tozeroy",
            fillcolor="rgba(79, 227, 255, 0.06)",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Observed: %{y:,.0f}<extra></extra>",
        ))

        # Farrington Threshold (Amber)
        fig.add_trace(go.Scatter(
            x=df_farr["timestamp"], y=df_farr["threshold"],
            mode="lines", name="Farrington Threshold",
            line=dict(color=SIGNAL_AMBER, width=1.8, dash="dot"),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Farrington: %{y:,.0f}<extra></extra>",
        ))

        # Hybrid Threshold (Purple)
        fig.add_trace(go.Scatter(
            x=df_hyb["timestamp"], y=df_hyb["threshold"],
            mode="lines", name="Hybrid Threshold",
            line=dict(color="#B36BFF", width=1.8, dash="dash"), # Purple
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Hybrid: %{y:,.0f}<extra></extra>",
        ))

        # Alerts (Red dots from Farrington)
        alerts = df_farr[df_farr["alert"]]
        if not alerts.empty:
            fig.add_trace(go.Scatter(
                x=alerts["timestamp"], y=alerts["observed"],
                mode="markers", name="Farrington Alert",
                marker=dict(color=SIGNAL_RED, size=12, symbol="circle", line=dict(color="#FFFFFF", width=1.2)),
                hovertemplate="<b>⚠ FARRINGTON ALERT</b><br>%{x|%b %d, %Y}<extra></extra>",
            ))

        # Alerts (Yellow diamonds from Hybrid)
        alerts_hyb = df_hyb[df_hyb["alert"]]
        if not alerts_hyb.empty:
            fig.add_trace(go.Scatter(
                x=alerts_hyb["timestamp"], y=alerts_hyb["observed"],
                mode="markers", name="Hybrid Alert",
                marker=dict(color="#FFD700", size=10, symbol="diamond", line=dict(color="#FFFFFF", width=1.2)),
                hovertemplate="<b>⚠ HYBRID ALERT</b><br>%{x|%b %d, %Y}<extra></extra>",
            ))

        fig.update_layout(
            height=520,
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode="x unified",
            showlegend=True,
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    except Exception as e:
        st.error(f"Uplink failure · {e}")
