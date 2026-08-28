import os
import subprocess
import sys

import streamlit as st
import streamlit.components.v1 as components
from streamlit.runtime.scriptrunner import get_script_run_ctx

from data import (
    ensure_database_ready,
    get_connection,
    get_global_gameweek_info,
    get_summary_stats,
    get_teams_fdr_map,
)
from tabs import (
    render_expected_stats_tab,
    render_fixture_ticker_tab,
    render_rolling_form_tab,
    render_squad_analyzer_tab,
    render_transfer_market_tab,
)
from theme import (
    apply_theme,
    render_sidebar_card,
    render_top_bar,
)

if get_script_run_ctx() is None:
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", __file__]))

st.set_page_config(
    page_title="FPL Strategic Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme State & Root Injection ─────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

# ── Google Analytics 4 ────────────────────────────────────────────────────────
GA_MEASUREMENT_ID = st.secrets.get(
    "GA_MEASUREMENT_ID", os.getenv("GA_MEASUREMENT_ID", "")
)
if GA_MEASUREMENT_ID:
    ga_tracking_code = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_MEASUREMENT_ID}', {{
          'send_page_view': true,
          'page_location': document.referrer || window.location.href,
          'page_title': 'FPL Strategic Dashboard',
          'cookie_flags': 'SameSite=None;Secure'
      }});
    </script>
    """
    components.html(
        f"<div style='display:none;'>{ga_tracking_code}</div>",
        height=0,
        width=0,
    )

# ── Data & Connection Initialization ──────────────────────────────────────────
ensure_database_ready()
conn = get_connection()
events_df, current_gw, gw_name = get_global_gameweek_info(conn)
summary_df = get_summary_stats(conn)
teams_fdr_map = get_teams_fdr_map(conn, current_gw)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<span class="gw-badge">NEXT · {gw_name}</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ☀️ / 🌙 Theme Toggle
    is_light_mode = st.toggle("☀️ Light Mode", value=(st.session_state["theme_mode"] == "light"), key="theme_toggle_switch")
    st.session_state["theme_mode"] = "light" if is_light_mode else "dark"

    st.markdown("<br>", unsafe_allow_html=True)

    manager_id = st.text_input(
        "FPL Team ID",
        value=st.session_state.get("manager_id", ""),
        placeholder="e.g. 1234567",
        key="global_manager_id",
    )
    if manager_id:
        st.session_state["manager_id"] = manager_id

    st.markdown("<br>", unsafe_allow_html=True)

    render_sidebar_card(
        "Season Overview",
        [
            ("Gameweek", gw_name),
            ("Players Tracked", f"{int(summary_df['total'].values[0]):,}"),
            ("Buy Signals", f"{int(summary_df['buy_signals'].values[0]):,}"),
            ("Sell Signals", f"{int(summary_df['sell_signals'].values[0]):,}"),
        ],
    )

    render_sidebar_card(
        "Transfer Market",
        [
            ("Heating Up", f"{int(summary_df['heating'].values[0]):,}"),
            ("Cooling Down", f"{int(summary_df['cooling'].values[0]):,}"),
        ],
    )

# ── Inject Root Level Theme CSS ───────────────────────────────────────────────
apply_theme(is_dark=(st.session_state["theme_mode"] == "dark"))

# ── Header Bar ────────────────────────────────────────────────────────────────
render_top_bar(f"Strategic analytics & squad optimizer · {gw_name}")

# ── Main Tabs (Squad Analyzer is Tab #1) ──────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Squad Analyzer",
        "Expected Stats",
        "Rolling Form",
        "Fixture Ticker",
        "Transfer Market",
    ]
)

with tab1:
    render_squad_analyzer_tab(conn, events_df, current_gw)
with tab2:
    render_expected_stats_tab(conn, current_gw)
with tab3:
    render_rolling_form_tab(conn, current_gw, teams_fdr_map)
with tab4:
    render_fixture_ticker_tab(conn, current_gw)
with tab5:
    render_transfer_market_tab(conn, current_gw)