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
    render_defensive_stats_tab,
    render_expected_stats_tab,
    render_fixture_ticker_tab,
    render_rolling_form_tab,
    render_squad_analyzer_tab,
    render_transfer_market_tab,
)
from theme import apply_theme

if get_script_run_ctx() is None:
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", __file__]))

st.set_page_config(
    page_title="FPL Optimizer",
    page_icon="assets/fplo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Theme State ───────────────────────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

is_dark = st.session_state["theme_mode"] == "dark"
apply_theme(is_dark=is_dark)

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

# ── Header & Action Bar ───────────────────────────────────────────────────────
col_brand, col_search, col_theme = st.columns([5.4, 2.1, 0.5], vertical_alignment="center")

with col_brand:
    badge_html = (
        f'<span class="gw-badge live">● {gw_name.upper()}</span>'
        if "(Live)" in gw_name
        else f'<span class="gw-badge">NEXT · {gw_name}</span>'
    )
    st.markdown(
        f"""
        <div class="top-nav-brand">
            <span class="top-nav-title">FPL Optimizer</span>
            {badge_html}
        </div>
        <div class="top-nav-sub">Strategic analytics & squad optimizer</div>
        """,
        unsafe_allow_html=True,
    )

with col_search:
    manager_id = st.text_input(
        "FPL Team ID",
        value=st.session_state.get("manager_id", ""),
        placeholder="Search Team ID...",
        key="global_manager_id",
        label_visibility="collapsed",
    )
    if manager_id:
        st.session_state["manager_id"] = manager_id

with col_theme:
    st.markdown('<span class="theme-toggle-marker"></span>', unsafe_allow_html=True)
    theme_icon = "🌞" if is_dark else "🌙"
    if st.button(theme_icon, key="theme_toggle_btn", help="Toggle Theme"):
        st.session_state["theme_mode"] = "light" if is_dark else "dark"
        st.rerun()

# ── Main Sticky Tabs ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Squad Analyzer",
        "Expected Stats",
        "Defensive Contributions",
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
    render_defensive_stats_tab(conn, current_gw)
with tab4:
    render_rolling_form_tab(conn, current_gw, teams_fdr_map)
with tab5:
    render_fixture_ticker_tab(conn, current_gw)
with tab6:
    render_transfer_market_tab(conn, current_gw)