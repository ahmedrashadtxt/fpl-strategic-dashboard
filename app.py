import os
from pathlib import Path
import sqlite3
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit.runtime.scriptrunner import get_script_run_ctx

from theme import (
    apply_theme,
    fmt_num,
    render_list_card,
    render_sidebar_card,
    render_stats_banner,
    render_top_bar,
    section_header,
)

if get_script_run_ctx() is None:
    import subprocess
    import sys

    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", __file__]))

st.set_page_config(
    page_title="FPL Strategic Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

# ── Google Analytics 4 (From Secrets / Env) ──────────────────────────────────
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

# ── Auto-Initialize Database ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fpl.db"


def ensure_database_ready():
    """Checks if fpl.db exists and contains tables; if not, triggers fetch_data.py"""
    needs_init = False

    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        needs_init = True
    else:
        try:
            temp_conn = sqlite3.connect(DB_PATH)
            table_check = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='events'",
                temp_conn,
            )
            temp_conn.close()
            if table_check.empty:
                needs_init = True
        except Exception:
            needs_init = True

    if needs_init:
        with st.spinner("Initializing database from official FPL API..."):
            import fetch_data

            if hasattr(fetch_data, "main"):
                fetch_data.main()
            elif hasattr(fetch_data, "fetch_all_data"):
                fetch_data.fetch_all_data()
            elif hasattr(fetch_data, "fetch_data"):
                fetch_data.fetch_data()


ensure_database_ready()

conn = sqlite3.connect(DB_PATH)

# ── Global Gameweek & Summary Queries ─────────────────────────────────────────
events_df = pd.read_sql("SELECT id, name, is_current, is_next FROM events", conn)
next_gw_row = events_df[events_df["is_next"] == 1]
current_gw_row = events_df[events_df["is_current"] == 1]
current_gw = int(next_gw_row["id"].values[0]) if not next_gw_row.empty else 1
gw_name = next_gw_row["name"].values[0] if not next_gw_row.empty else f"Gameweek {current_gw}"

summary_df = pd.read_sql(
    """
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN (expected_goals - goals_scored) >= 0.5 THEN 1 ELSE 0 END) AS buy_signals,
        SUM(CASE WHEN (expected_goals - goals_scored) <= -0.5 THEN 1 ELSE 0 END) AS sell_signals,
        SUM(CASE WHEN (transfers_in_event - transfers_out_event) > 30000 THEN 1 ELSE 0 END) AS heating,
        SUM(CASE WHEN (transfers_in_event - transfers_out_event) < -30000 THEN 1 ELSE 0 END) AS cooling
    FROM players
    WHERE minutes > 0
    """,
    conn,
)

# Precalculate 5-GW upcoming fixture difficulty per team for rolling analysis
fixtures_5gw = pd.read_sql(
    """
    SELECT event, team_h, team_a, team_h_difficulty, team_a_difficulty
    FROM fixtures
    WHERE event >= ? AND event < ? AND finished = 0
    """,
    conn,
    params=[current_gw, current_gw + 5],
)

teams_fdr_map = {}
for t_id in range(1, 21):
    h_diff = fixtures_5gw[fixtures_5gw["team_h"] == t_id]["team_h_difficulty"].sum()
    a_diff = fixtures_5gw[fixtures_5gw["team_a"] == t_id]["team_a_difficulty"].sum()
    teams_fdr_map[t_id] = int(h_diff + a_diff) if (h_diff + a_diff) > 0 else 15


@st.cache_data(ttl=300)
def get_manager_squad_ids(mgr_id, target_gw):
    """Fetches and caches the list of player element IDs in the user's squad."""
    if not mgr_id:
        return []
    try:
        gw = target_gw if target_gw >= 1 else 1
        picks_url = f"https://fantasy.premierleague.com/api/entry/{mgr_id}/event/{gw}/picks/"
        res = requests.get(picks_url, timeout=10)
        if res.status_code != 200 and gw > 1:
            gw -= 1
            picks_url = f"https://fantasy.premierleague.com/api/entry/{mgr_id}/event/{gw}/picks/"
            res = requests.get(picks_url, timeout=10)
        if res.status_code == 200:
            return [p["element"] for p in res.json().get("picks", [])]
    except Exception:
        return []
    return []


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<span class="gw-badge">NEXT · {gw_name}</span>', unsafe_allow_html=True)
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

    if st.button("Refresh Data", width="stretch", type="primary"):
        with st.spinner("Fetching latest Premier League data and match histories..."):
            import fetch_data

            if hasattr(fetch_data, "main"):
                fetch_data.main()
            elif hasattr(fetch_data, "fetch_all_data"):
                fetch_data.fetch_all_data()
            elif hasattr(fetch_data, "fetch_data"):
                fetch_data.fetch_data()
        st.cache_data.clear()
        st.rerun()

# ── Main Header ──────────────────────────────────────────────────────────────
render_top_bar(f"Strategic analytics · {gw_name}")

header_left, header_right = st.columns([4, 1])
with header_left:
    render_stats_banner(
        int(summary_df["total"].values[0]),
        int(summary_df["buy_signals"].values[0]),
        int(summary_df["sell_signals"].values[0]),
    )
with header_right:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:right;color:#555;font-size:0.75rem;margin-top:1.5rem">'
        "Data sourced from FPL API<br>Updated on refresh"
        "</div>",
        unsafe_allow_html=True,
    )

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Expected Stats",
        "Rolling Form",
        "Fixture Ticker",
        "Squad Analyzer",
        "Transfer Market",
    ]
)

pos_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}

# ── TAB 1: Expected Stats ────────────────────────────────────────────────────
with tab1:
    col_t1_hdr, col_t1_pop = st.columns([6, 1])
    with col_t1_hdr:
        section_header("Expected Stats & Underperformance", "Identify high-value and unlucky assets")
    with col_t1_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Expected Stats & Regression Guide**
                
                * **xG / xA / xGI:** Expected Goals, Assists, and Goal Involvements based on shot location and chance quality.
                * **ΔxG (xG Delta):** Calculated as `xG - Actual Goals`.
                    * 🟢 **Buy Signal (ΔxG ≥ +0.5):** Creating/receiving high-quality chances but unlucky with finishing. Positive scoring regression expected.
                    * 🔴 **Sell Signal (ΔxG ≤ -0.5):** Outperforming underlying metrics significantly. Current scoring conversion is historically unsustainable.
                * **xGI / 90:** Normalizes chance involvement per 90 minutes played to spot high-impact assets with managed minutes.
                """
            )

    col_search, col1, col2, col3 = st.columns([1.5, 1, 1, 1])
    with col_search:
        search_query = st.text_input(
            "🔍 Search Player / Club",
            placeholder="e.g. Palmer, Haaland, Arsenal, MCI...",
            key="tab1_search",
        )
    with col1:
        min_minutes = st.slider("Minimum Minutes Played", 0, 900, 0, step=45, key="tab1_min_mins")
    with col2:
        position_filter = st.selectbox("Filter Position", ["All", "GKP", "DEF", "MID", "FWD"], key="tab1_pos")
    with col3:
        sort_by = st.selectbox(
            "Rank By",
            [
                "Expected Goal Involvements (xGI)",
                "Goals Below Expected (Unlucky)",
                "xGI per 90",
                "Total Points",
                "Clean Sheets",
                "Goalkeeper Saves",
            ],
            key="tab1_sort",
        )

    only_my_squad_tab1 = st.checkbox("🎯 Only My Squad Players", key="tab1_only_squad")

    pos_clause = f"AND p.element_type = {pos_map[position_filter]}" if position_filter != "All" else ""

    query = f"""
    SELECT
        p.id AS element_id,
        p.web_name AS Player,
        p.first_name || ' ' || p.second_name AS Full_Name,
        t.short_name AS Team,
        t.name AS Club_Name,
        CASE p.element_type
            WHEN 1 THEN 'GKP'
            WHEN 2 THEN 'DEF'
            WHEN 3 THEN 'MID'
            WHEN 4 THEN 'FWD'
        END AS Pos,
        p.now_cost / 10.0 AS Price,
        p.minutes AS Minutes,
        p.total_points AS Total_Points,
        p.goals_scored AS Goals,
        p.assists AS Assists,
        p.clean_sheets AS Clean_Sheets,
        p.saves AS Saves,
        p.expected_goals AS xG,
        p.expected_assists AS xA,
        p.expected_goal_involvements AS xGI,
        (p.expected_goals - p.goals_scored) AS xG_Delta,
        p.expected_goal_involvements_per_90 AS xGI_per_90
    FROM players p
    INNER JOIN teams t ON p.team = t.id
    WHERE p.minutes >= {min_minutes} {pos_clause}
    """
    df_xgi = pd.read_sql(query, conn)
    for col_name in (
        "Price",
        "Minutes",
        "Total_Points",
        "Goals",
        "Assists",
        "Clean_Sheets",
        "Saves",
        "xG",
        "xA",
        "xGI",
        "xG_Delta",
        "xGI_per_90",
    ):
        df_xgi[col_name] = pd.to_numeric(df_xgi[col_name], errors="coerce")

    # Filter by Manager Squad if checkbox is selected
    active_manager_id_tab1 = st.session_state.get("manager_id", "").strip()
    if only_my_squad_tab1:
        if not active_manager_id_tab1:
            st.info("💡 Enter your FPL Team ID in the sidebar or Tab 4 to filter by your squad.")
            squad_ids_tab1 = []
        else:
            squad_ids_tab1 = get_manager_squad_ids(active_manager_id_tab1, current_gw)
        df_xgi = df_xgi[df_xgi["element_id"].isin(squad_ids_tab1)]

    if search_query.strip():
        q1 = search_query.strip()
        df_xgi = df_xgi[
            df_xgi["Player"].str.contains(q1, case=False, na=False)
            | df_xgi["Full_Name"].str.contains(q1, case=False, na=False)
            | df_xgi["Team"].str.contains(q1, case=False, na=False)
            | df_xgi["Club_Name"].str.contains(q1, case=False, na=False)
        ]

    sort_map = {
        "Expected Goal Involvements (xGI)": ("xGI", False),
        "Goals Below Expected (Unlucky)": ("xG_Delta", False),
        "xGI per 90": ("xGI_per_90", False),
        "Total Points": ("Total_Points", False),
        "Clean Sheets": ("Clean_Sheets", False),
        "Goalkeeper Saves": ("Saves", False),
    }
    col, asc = sort_map[sort_by]
    df_xgi = df_xgi.sort_values(by=col, ascending=asc)

    if df_xgi.empty:
        st.info(f"No players found matching '{search_query}'. Try adjusting your filters.")
    else:
        top_cards = df_xgi.head(min(5, len(df_xgi)))
        card_cols = st.columns(len(top_cards))
        for i, (_, row) in enumerate(top_cards.iterrows()):
            delta = float(row["xG_Delta"])
            if delta >= 0.5:
                signal_tag = ("Buy Signal", "green")
            elif delta <= -0.5:
                signal_tag = ("Sell Signal", "red")
            else:
                signal_tag = ("Neutral", "gray")
            with card_cols[i]:
                render_list_card(
                    f"{row['Player']} ({row['Team']})",
                    [(row["Pos"], "blue"), signal_tag],
                    f'<span>Price</span> £{fmt_num(row["Price"], ".1f")} · <span>xGI</span> {fmt_num(row["xGI"])} · <span>Pts</span> {int(float(row["Total_Points"]))} · <span>ΔxG</span> {fmt_num(delta, "+.2f")}',
                )

        def highlight_xg_delta(val):
            try:
                val = float(val)
                if val >= 0.5:
                    return "background-color: rgba(34, 197, 94, 0.25)"
                if val > 0:
                    return "background-color: rgba(34, 197, 94, 0.1)"
                if val <= -0.5:
                    return "background-color: rgba(239, 68, 68, 0.2)"
            except (ValueError, TypeError):
                pass
            return ""

        display_cols_tab1 = [
            "Player",
            "Team",
            "Pos",
            "Price",
            "Minutes",
            "Total_Points",
            "Goals",
            "Assists",
            "Clean_Sheets",
            "Saves",
            "xG",
            "xA",
            "xGI",
            "xG_Delta",
            "xGI_per_90",
        ]

        st.dataframe(
            df_xgi[display_cols_tab1].head(25).style.map(highlight_xg_delta, subset=["xG_Delta"]),
            hide_index=True,
            width="stretch",
            column_config={
                "Price": st.column_config.NumberColumn(format="£%.1f"),
                "Minutes": st.column_config.NumberColumn("Mins"),
                "Total_Points": st.column_config.NumberColumn("Pts"),
                "Goals": st.column_config.NumberColumn("G"),
                "Assists": st.column_config.NumberColumn("A"),
                "Clean_Sheets": st.column_config.NumberColumn("CS"),
                "Saves": st.column_config.NumberColumn("Saves"),
                "xG": st.column_config.NumberColumn(format="%.2f"),
                "xA": st.column_config.NumberColumn(format="%.2f"),
                "xGI": st.column_config.NumberColumn(format="%.2f"),
                "xG_Delta": st.column_config.NumberColumn(format="%.2f"),
                "xGI_per_90": st.column_config.NumberColumn("xGI/90", format="%.2f"),
            },
        )

# ── TAB 2: Rolling Form & Scatter Plot ────────────────────────────────────────
with tab2:
    col_t2_hdr, col_t2_pop = st.columns([6, 1])
    with col_t2_hdr:
        section_header("Rolling Form & Trends", "Analyze form trajectory vs upcoming fixture schedule")
    with col_t2_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Form vs. Fixtures Scatter Matrix**
                
                * **Y-Axis (Rolling Sum xGI):** Total attacking threat accumulated across the selected match window.
                * **X-Axis (Upcoming 5-GW FDR):** Total fixture difficulty rating over the next 5 games (lower score = easier schedule).
                * **Min Matches Filter (e.g. ≥ 3):** Filters out rotational cameos and short injury returns so you only evaluate nailed starters with meaningful sample sizes.
                
                ---
                
                **How to Read the Quadrants (Example with Min 3 Matches):**
                
                * 🔥 **Top-Left (High Form + Easy Fixtures) → Prime Buys**
                  * *Example:* **Bukayo Saka / Erling Haaland** — Sustained high xGI entering weak defensive matchups. Priority transfer-in targets and top captaincy options.
                * ⚠️ **Top-Right (High Form + Tough Fixtures) → Hold, Don't Buy**
                  * *Example:* **Mohamed Salah / Cole Palmer** — Generating strong underlying chances but facing top-4 defenses. Keep if owned, but avoid captaining over Top-Left assets.
                * 🛡️ **Bottom-Left (Low Form + Easy Fixtures) → Budget Enablers**
                  * *Example:* **Declan Rice / 4.5m Midfielders** — Consistent starters with low individual attacking output entering easier runs. Safe minutes floor, low haul ceiling.
                * ❌ **Bottom-Right (Low Form + Tough Fixtures) → Sell Candidates**
                  * *Example:* Struggling attackers from low-scoring sides facing difficult schedules. Priority transfer-out candidates.
                """
            )

    table_exists = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='player_match_history'",
        conn,
    )

    if table_exists.empty:
        st.warning(
            "⚠️ Match history table `player_match_history` was not found in `fpl.db`. "
            "Please click **Refresh Data** in the sidebar to populate match histories."
        )
    else:
        col_search2, col_w, col_pos2, col_min_matches, col_min_mins2, col_sort2 = st.columns(
            [1.4, 0.9, 0.8, 0.9, 0.9, 1.2]
        )
        with col_search2:
            search_query2 = st.text_input(
                "🔍 Search Player / Club",
                placeholder="e.g. Cherki, Saka, Chelsea, ARS...",
                key="tab2_search",
            )
        with col_w:
            window_size = st.slider("Match Window", min_value=3, max_value=10, value=5, step=1, key="tab2_window")
        with col_pos2:
            pos_filter2 = st.selectbox("Position", ["All", "GKP", "DEF", "MID", "FWD"], key="tab2_pos")
        with col_min_matches:
            min_matches = st.slider(
                "Min Matches", min_value=1, max_value=window_size, value=min(3, window_size), step=1, key="tab2_matches"
            )
        with col_min_mins2:
            min_avg_mins = st.slider("Min Avg Mins", 0, 90, 45, step=15, key="tab2_mins")
        with col_sort2:
            rolling_sort = st.selectbox(
                "Rank By",
                [
                    "Rolling Sum xGI",
                    "Rolling xGI / 90",
                    "Rolling Avg Points",
                    "Upcoming Fixture Ease",
                    "Rolling Avg Minutes",
                    "Price",
                ],
                key="tab2_sort",
            )

        only_my_squad = st.checkbox("🎯 Only My Squad Players", key="tab2_only_squad")

        pos_clause2 = f"AND p.element_type = {pos_map[pos_filter2]}" if pos_filter2 != "All" else ""

        rolling_query = f"""
        WITH ranked_matches AS (
            SELECT
                h.element_id,
                p.web_name AS Player,
                p.first_name || ' ' || p.second_name AS Full_Name,
                t.short_name AS Team,
                t.name AS Club_Name,
                p.team AS Team_ID,
                CASE p.element_type
                    WHEN 1 THEN 'GKP'
                    WHEN 2 THEN 'DEF'
                    WHEN 3 THEN 'MID'
                    WHEN 4 THEN 'FWD'
                END AS Pos,
                p.now_cost / 10.0 AS Price,
                h.round AS GW,
                h.total_points,
                h.minutes,
                CAST(h.expected_goal_involvements AS FLOAT) AS xgi,
                AVG(h.total_points) OVER (
                    PARTITION BY h.element_id
                    ORDER BY h.round
                    ROWS BETWEEN {window_size - 1} PRECEDING AND CURRENT ROW
                ) AS Rolling_Avg_Pts,
                SUM(CAST(h.expected_goal_involvements AS FLOAT)) OVER (
                    PARTITION BY h.element_id
                    ORDER BY h.round
                    ROWS BETWEEN {window_size - 1} PRECEDING AND CURRENT ROW
                ) AS Rolling_Sum_xGI,
                AVG(h.minutes) OVER (
                    PARTITION BY h.element_id
                    ORDER BY h.round
                    ROWS BETWEEN {window_size - 1} PRECEDING AND CURRENT ROW
                ) AS Rolling_Avg_Mins,
                SUM(h.minutes) OVER (
                    PARTITION BY h.element_id
                    ORDER BY h.round
                    ROWS BETWEEN {window_size - 1} PRECEDING AND CURRENT ROW
                ) AS Rolling_Total_Mins,
                SUM(CASE WHEN h.minutes > 0 THEN 1 ELSE 0 END) OVER (
                    PARTITION BY h.element_id
                    ORDER BY h.round
                    ROWS BETWEEN {window_size - 1} PRECEDING AND CURRENT ROW
                ) AS Rolling_Matches_Played,
                ROW_NUMBER() OVER (
                    PARTITION BY h.element_id
                    ORDER BY h.round DESC
                ) AS rn
            FROM player_match_history h
            INNER JOIN players p ON h.element_id = p.id
            INNER JOIN teams t ON p.team = t.id
            WHERE 1=1 {pos_clause2}
        )
        SELECT
            element_id,
            Player,
            Full_Name,
            Team,
            Club_Name,
            Team_ID,
            Pos,
            Price,
            GW AS Latest_GW,
            ROUND(Rolling_Avg_Pts, 2) AS Rolling_Avg_Pts,
            ROUND(Rolling_Sum_xGI, 2) AS Rolling_Sum_xGI,
            ROUND(Rolling_Avg_Mins, 1) AS Rolling_Avg_Mins,
            Rolling_Matches_Played,
            ROUND(
                CASE 
                    WHEN Rolling_Total_Mins > 0 
                    THEN (Rolling_Sum_xGI / Rolling_Total_Mins) * 90.0 
                    ELSE 0.0 
                END, 2
            ) AS Rolling_xGI_per_90
        FROM ranked_matches
        WHERE rn = 1 
          AND Rolling_Avg_Mins >= {min_avg_mins}
          AND Rolling_Matches_Played >= {min_matches}
        """
        df_rolling = pd.read_sql(rolling_query, conn)

        if not df_rolling.empty:
            df_rolling["Upcoming_FDR"] = df_rolling["Team_ID"].map(teams_fdr_map).fillna(15).astype(int)

            # Filter by Manager Squad if selected
            active_manager_id = st.session_state.get("manager_id", "").strip()
            if only_my_squad:
                if not active_manager_id:
                    st.info("💡 Enter your FPL Team ID in the sidebar or Tab 4 to filter by your squad.")
                    squad_ids = []
                else:
                    squad_ids = get_manager_squad_ids(active_manager_id, current_gw)
                df_rolling = df_rolling[df_rolling["element_id"].isin(squad_ids)]

            if search_query2.strip():
                q2 = search_query2.strip()
                df_rolling = df_rolling[
                    df_rolling["Player"].str.contains(q2, case=False, na=False)
                    | df_rolling["Full_Name"].str.contains(q2, case=False, na=False)
                    | df_rolling["Team"].str.contains(q2, case=False, na=False)
                    | df_rolling["Club_Name"].str.contains(q2, case=False, na=False)
                ]

            sort_rolling_map = {
                "Rolling Sum xGI": ("Rolling_Sum_xGI", False),
                "Rolling xGI / 90": ("Rolling_xGI_per_90", False),
                "Rolling Avg Points": ("Rolling_Avg_Pts", False),
                "Upcoming Fixture Ease": ("Upcoming_FDR", True),
                "Rolling Avg Minutes": ("Rolling_Avg_Mins", False),
                "Price": ("Price", False),
            }
            r_col, r_asc = sort_rolling_map[rolling_sort]
            df_rolling = df_rolling.sort_values(by=r_col, ascending=r_asc)

        if df_rolling.empty:
            st.info("No players found matching the current rolling filter criteria.")
        else:
            # Quadrant Scatter Plot
            if len(df_rolling) >= 2:
                x_mid = float(df_rolling["Upcoming_FDR"].median())
                y_mid = float(df_rolling["Rolling_Sum_xGI"].median())

                fig = px.scatter(
                    df_rolling,
                    x="Upcoming_FDR",
                    y="Rolling_Sum_xGI",
                    color="Pos",
                    size="Price",
                    hover_name="Player",
                    hover_data={
                        "Team": True,
                        "Price": ":.1f",
                        "Rolling_Sum_xGI": ":.2f",
                        "Rolling_xGI_per_90": ":.2f",
                        "Rolling_Avg_Pts": ":.2f",
                        "Upcoming_FDR": True,
                        "Rolling_Avg_Mins": ":.0f",
                        "Rolling_Matches_Played": True,
                        "Pos": False,
                    },
                    labels={
                        "Upcoming_FDR": "Upcoming 5-GW Fixture Difficulty Rating (Lower = Easier)",
                        "Rolling_Sum_xGI": f"Rolling {window_size}-Match xGI",
                        "Pos": "Position",
                    },
                    title=f"Underlying Form vs Schedule (L{window_size} xGI vs Next 5 FDR)",
                    color_discrete_map={
                        "GKP": "#f59e0b",
                        "DEF": "#3b82f6",
                        "MID": "#10b981",
                        "FWD": "#ef4444",
                    },
                )

                fig.add_vline(x=x_mid, line_dash="dash", line_color="rgba(255, 255, 255, 0.25)")
                fig.add_hline(y=y_mid, line_dash="dash", line_color="rgba(255, 255, 255, 0.25)")

                fig.add_annotation(
                    x=float(df_rolling["Upcoming_FDR"].min()),
                    y=float(df_rolling["Rolling_Sum_xGI"].max()),
                    text="🔥 Prime Buys (High Form + Easy Run)",
                    showarrow=False,
                    xanchor="left",
                    yanchor="top",
                    font=dict(size=11, color="#22c55e"),
                )
                fig.add_annotation(
                    x=float(df_rolling["Upcoming_FDR"].max()),
                    y=float(df_rolling["Rolling_Sum_xGI"].max()),
                    text="⚠️ High Form vs Tough Run",
                    showarrow=False,
                    xanchor="right",
                    yanchor="top",
                    font=dict(size=11, color="#eab308"),
                )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="rgba(15, 23, 42, 0.4)",
                    paper_bgcolor="rgba(15, 23, 42, 0.0)",
                    margin=dict(l=20, r=20, t=50, b=20),
                    height=450,
                )

                st.plotly_chart(fig, use_container_width=True)

            # Top Cards
            top_rolling = df_rolling.head(min(5, len(df_rolling)))
            cols_r = st.columns(len(top_rolling))
            for i, (_, row) in enumerate(top_rolling.iterrows()):
                with cols_r[i]:
                    render_list_card(
                        f"{row['Player']} ({row['Team']})",
                        [(row["Pos"], "blue"), (f"L{window_size} Form", "green")],
                        f'<span>Price</span> £{fmt_num(row["Price"], ".1f")} · <span>xGI</span> {fmt_num(row["Rolling_Sum_xGI"])} · <span>xGI/90</span> {fmt_num(row["Rolling_xGI_per_90"])} · <span>Next 5 FDR</span> {int(row["Upcoming_FDR"])} · <span>Avg Pts</span> {fmt_num(row["Rolling_Avg_Pts"], ".1f")}',
                    )

            display_cols_tab2 = [
                "Player",
                "Team",
                "Pos",
                "Price",
                "Latest_GW",
                "Rolling_Sum_xGI",
                "Rolling_xGI_per_90",
                "Rolling_Avg_Pts",
                "Upcoming_FDR",
                "Rolling_Avg_Mins",
                "Rolling_Matches_Played",
            ]

            # Table
            st.dataframe(
                df_rolling[display_cols_tab2].head(35),
                hide_index=True,
                width="stretch",
                column_config={
                    "Player": st.column_config.TextColumn("Player"),
                    "Team": st.column_config.TextColumn("Club"),
                    "Pos": st.column_config.TextColumn("Pos"),
                    "Price": st.column_config.NumberColumn("Price", format="£%.1f"),
                    "Latest_GW": st.column_config.NumberColumn("GW"),
                    "Rolling_Sum_xGI": st.column_config.NumberColumn(f"Sum xGI (L{window_size})", format="%.2f"),
                    "Rolling_xGI_per_90": st.column_config.NumberColumn(f"xGI/90 (L{window_size})", format="%.2f"),
                    "Rolling_Avg_Pts": st.column_config.NumberColumn(f"Avg Pts (L{window_size})", format="%.2f"),
                    "Upcoming_FDR": st.column_config.NumberColumn("Next 5 FDR (Ease)", format="%d"),
                    "Rolling_Avg_Mins": st.column_config.NumberColumn(f"Avg Mins (L{window_size})", format="%.1f"),
                    "Rolling_Matches_Played": st.column_config.NumberColumn("Apps", format="%d"),
                },
            )

# ── TAB 3: Fixture Ticker ────────────────────────────────────────────────────
with tab3:
    col_t3_hdr, col_t3_pop = st.columns([6, 1])
    with col_t3_hdr:
        section_header(f"Fixture Difficulty · GW{current_gw}–{current_gw + 4}", "Upcoming schedule ranked by difficulty")
    with col_t3_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Fixture Ticker Guide**
                
                * **Difficulty Rating:** Sum of official FDR scores across the next 5 gameweeks.
                * **(H) vs. (A):** Designates Home or Away fixtures. Home games offer historically higher clean sheet and scoring conversion probabilities.
                * 🟢 **Green Run (≤10 pts):** Prime fixture swings. Prioritize attacking transfers and defensive double-ups.
                * 🔴 **Tough Run (≥15 pts):** Hold off buying assets from these clubs until their schedule clears.
                * 🔍 **Search & Squad Filter:** Searching a player filters by their respective club; enabling squad filter isolates clubs of your 15 players.
                """
            )

    col_search3, col_sq3 = st.columns([2, 1])
    with col_search3:
        search_query3 = st.text_input(
            "🔍 Search Player / Club",
            placeholder="e.g. Saka, Arsenal, Haaland, MCI...",
            key="tab3_search",
        )
    with col_sq3:
        st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
        only_my_squad_tab3 = st.checkbox("🎯 Only My Squad Clubs", key="tab3_only_squad")

    # Fixture queries
    fixtures_query = """
    SELECT
        f.event AS GW,
        th.short_name AS Home_Team,
        ta.short_name AS Away_Team,
        f.team_h_difficulty AS Home_Diff,
        f.team_a_difficulty AS Away_Diff
    FROM fixtures f
    INNER JOIN teams th ON f.team_h = th.id
    INNER JOIN teams ta ON f.team_a = ta.id
    WHERE f.event >= ? AND f.event < ? AND f.finished = 0
    ORDER BY f.event ASC
    """
    fixtures_df = pd.read_sql(fixtures_query, conn, params=[current_gw, current_gw + 5])

    # Player-to-Team mapping table for flexible player/club searches
    pt_lookup = pd.read_sql(
        """
        SELECT 
            p.id AS element_id, 
            p.web_name, 
            p.first_name || ' ' || p.second_name AS full_name,
            t.short_name, 
            t.name AS club_name
        FROM players p
        INNER JOIN teams t ON p.team = t.id
        """,
        conn,
    )

    teams_list = pd.read_sql("SELECT short_name FROM teams ORDER BY name", conn)["short_name"].tolist()
    target_team_short_names = set(teams_list)

    # Filter clubs by manager squad
    if only_my_squad_tab3:
        active_manager_id_tab3 = st.session_state.get("manager_id", "").strip()
        if not active_manager_id_tab3:
            st.info("💡 Enter your FPL Team ID in the sidebar or Tab 4 to filter by your squad.")
            target_team_short_names = set()
        else:
            squad_ids_tab3 = get_manager_squad_ids(active_manager_id_tab3, current_gw)
            squad_teams = pt_lookup[pt_lookup["element_id"].isin(squad_ids_tab3)]["short_name"].unique()
            target_team_short_names = target_team_short_names.intersection(set(squad_teams))

    # Filter clubs by search query (checks player name, full name, club name, and club code)
    if search_query3.strip():
        q3 = search_query3.strip().lower()
        matching_from_lookup = pt_lookup[
            pt_lookup["web_name"].str.contains(q3, case=False, na=False)
            | pt_lookup["full_name"].str.contains(q3, case=False, na=False)
            | pt_lookup["short_name"].str.contains(q3, case=False, na=False)
            | pt_lookup["club_name"].str.contains(q3, case=False, na=False)
        ]["short_name"].unique()
        target_team_short_names = target_team_short_names.intersection(set(matching_from_lookup))

    ticker_data = []
    gw_cols = [f"GW {gw}" for gw in range(current_gw, current_gw + 5)]

    for team in teams_list:
        row = {"Team": team}
        total_difficulty = 0
        for gw in range(current_gw, current_gw + 5):
            match = fixtures_df[
                (fixtures_df["GW"] == gw)
                & ((fixtures_df["Home_Team"] == team) | (fixtures_df["Away_Team"] == team))
            ]
            if not match.empty:
                m = match.iloc[0]
                if m["Home_Team"] == team:
                    opp = f"{m['Away_Team']} (H)"
                    diff = m["Home_Diff"]
                else:
                    opp = f"{m['Home_Team']} (A)"
                    diff = m["Away_Diff"]
                row[f"GW {gw}"] = f"{opp} [{diff}]"
                total_difficulty += diff
            else:
                row[f"GW {gw}"] = "Blank"
                total_difficulty += 5
        row["Difficulty Rating"] = total_difficulty
        ticker_data.append(row)

    ticker_df = pd.DataFrame(ticker_data).sort_values(by="Difficulty Rating", ascending=True)

    # Apply club filter
    ticker_df = ticker_df[ticker_df["Team"].isin(target_team_short_names)]

    if ticker_df.empty:
        st.info("No clubs found matching your search or squad criteria.")
    else:
        easy_teams = ticker_df.head(min(5, len(ticker_df)))
        for _, row in easy_teams.iterrows():
            fixtures_str = " · ".join(row[f"GW {gw}"] for gw in range(current_gw, current_gw + 5))
            rating = row["Difficulty Rating"]
            tag = ("Easy Run", "green") if rating <= 10 else ("Moderate", "yellow")
            render_list_card(
                row["Team"],
                [tag, (f"Rating {rating}", "gray")],
                f"<span>Fixtures</span> {fixtures_str}",
            )

        def style_fdr_cell(val):
            val_str = str(val)
            if "[2]" in val_str:
                return "background-color: rgba(34, 197, 94, 0.25); color: #4ade80; font-weight: 600; text-align: center;"
            elif "[3]" in val_str:
                return "background-color: rgba(100, 116, 139, 0.15); color: #cbd5e1; text-align: center;"
            elif "[4]" in val_str:
                return "background-color: rgba(249, 115, 22, 0.25); color: #fb923c; font-weight: 600; text-align: center;"
            elif "[5]" in val_str:
                return "background-color: rgba(239, 68, 68, 0.3); color: #f87171; font-weight: 700; text-align: center;"
            elif "Blank" in val_str:
                return "background-color: rgba(15, 23, 42, 0.5); color: #64748b; font-style: italic; text-align: center;"
            return "text-align: center;"

        def style_rating_col(val):
            try:
                v = int(val)
                if v <= 11:
                    return "background-color: rgba(34, 197, 94, 0.25); color: #22c55e; font-weight: bold; text-align: center;"
                elif v <= 14:
                    return "background-color: rgba(234, 179, 8, 0.2); color: #eab308; font-weight: bold; text-align: center;"
                else:
                    return "background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold; text-align: center;"
            except Exception:
                return ""

        styled_ticker = (
            ticker_df.style
            .map(style_fdr_cell, subset=gw_cols)
            .map(style_rating_col, subset=["Difficulty Rating"])
        )

        st.dataframe(
            styled_ticker,
            hide_index=True,
            width="stretch",
            column_config={
                "Team": st.column_config.TextColumn("Club"),
                "Difficulty Rating": st.column_config.NumberColumn("Total FDR (5 GW)"),
            },
        )

# ── TAB 4: Squad Analyzer ────────────────────────────────────────────────────
with tab4:
    col_t4_hdr, col_t4_pop = st.columns([6, 1])
    with col_t4_hdr:
        section_header("Manager Squad Analyzer", "Import your FPL team ID to analyze your squad")
    with col_t4_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Manager Squad Sync Guide**
                
                * **FPL Team ID:** Enter your manager ID from the official FPL URL (`fantasy.premierleague.com/entry/XXXXXX/event/...`).
                * **Starting XI vs. Bench:** Automatically segregates and displays your active Starting 11 (order 1–11) and your 4 bench substitutes in priority order.
                * **Multipliers:** Accurately applies your Captain (2x) and Vice-Captain scoring multipliers with clear indicator badges.
                * **Squad News Tracker:** Flags live press-conference injury updates, suspensions, and percent chance of playing.
                """
            )

    tab4_manager_id = st.text_input(
        "FPL Team / Entry ID",
        value=st.session_state.get("manager_id", ""),
        placeholder="e.g. 1234567",
        key="tab4_manager_id",
    )
    if tab4_manager_id:
        st.session_state["manager_id"] = tab4_manager_id

    mgr_to_use = tab4_manager_id or st.session_state.get("manager_id", "")

    if mgr_to_use:
        try:
            mgr_url = f"https://fantasy.premierleague.com/api/entry/{mgr_to_use}/"
            mgr_data = requests.get(mgr_url).json()

            target_gw = current_gw if current_gw >= 1 else 1
            picks_url = f"https://fantasy.premierleague.com/api/entry/{mgr_to_use}/event/{target_gw}/picks/"
            picks_res = requests.get(picks_url)

            if picks_res.status_code != 200 and target_gw > 1:
                target_gw -= 1
                picks_url = f"https://fantasy.premierleague.com/api/entry/{mgr_to_use}/event/{target_gw}/picks/"
                picks_res = requests.get(picks_url)

            picks_data = picks_res.json()
            live_url = f"https://fantasy.premierleague.com/api/event/{target_gw}/live/"
            live_res = requests.get(live_url).json()
            live_points_map = {item["id"]: item["stats"]["total_points"] for item in live_res.get("elements", [])}

            entry_history = picks_data.get("entry_history", {})
            transfers_cost = entry_history.get("event_transfers_cost", 0)
            total_points = mgr_data.get("summary_overall_points", 0)

            picks_list = picks_data.get("picks", [])
            pick_ids = [p["element"] for p in picks_list]
            placeholders = ",".join(["?"] * len(pick_ids))

            squad_query = f"""
            SELECT
                p.id,
                p.web_name AS Player,
                t.name AS Team,
                pos.singular_name AS Position,
                p.now_cost / 10.0 AS Cost,
                p.total_points AS Season_Points,
                p.news AS News,
                p.status AS Status,
                p.chance_of_playing_next_round AS Chance
            FROM players p
            INNER JOIN teams t ON p.team = t.id
            INNER JOIN positions pos ON p.element_type = pos.id
            WHERE p.id IN ({placeholders})
            """
            squad_df = pd.read_sql(squad_query, conn, params=pick_ids)

            meta_dict = {
                p["element"]: {
                    "multiplier": p["multiplier"],
                    "is_captain": p["is_captain"],
                    "is_vice": p["is_vice_captain"],
                    "order": p["position"],
                }
                for p in picks_list
            }

            squad_df["order"] = squad_df["id"].map(lambda x: meta_dict[x]["order"])
            squad_df["Multiplier"] = squad_df["id"].map(lambda x: meta_dict[x]["multiplier"])
            squad_df["is_cap"] = squad_df["id"].map(lambda x: meta_dict[x]["is_captain"])
            squad_df["is_vc"] = squad_df["id"].map(lambda x: meta_dict[x]["is_vice"])
            squad_df["Raw_GW_Pts"] = squad_df["id"].map(lambda x: live_points_map.get(x, 0))
            squad_df["GW_Points"] = squad_df["Raw_GW_Pts"] * squad_df["Multiplier"]

            starting_xi_pts = squad_df[squad_df["order"] <= 11]["GW_Points"].sum()
            live_gw_pts = int(starting_xi_pts) - transfers_cost

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Manager", mgr_data.get("name", "My Team"))
            col2.metric("Overall Rank", f"{mgr_data.get('summary_overall_rank', 0):,}")
            col3.metric("Total Points", f"{total_points:,}")
            col4.metric(
                f"GW {target_gw} Points",
                live_gw_pts,
                delta=f"-{transfers_cost} pts hit" if transfers_cost > 0 else None,
                delta_color="inverse",
            )

            squad_df = squad_df.sort_values(by="order", ascending=True)

            col_squad, col_news = st.columns([7, 3])

            with col_squad:
                starters = squad_df[squad_df["order"] <= 11]
                bench = squad_df[squad_df["order"] > 11]

                st.markdown("#### ⚽ Starting XI")
                for _, row in starters.iterrows():
                    tags = [(row["Position"], "blue")]
                    mult_info = ""

                    if row["Multiplier"] == 2:
                        tags.append(("Captain (2x)", "green"))
                        mult_info = " (2x)"
                    elif row["Multiplier"] == 3:
                        tags.append(("Triple Captain (3x)", "green"))
                        mult_info = " (3x)"
                    elif row["is_cap"]:
                        tags.append(("Captain", "green"))

                    if row["is_vc"]:
                        tags.append(("Vice Captain", "yellow"))

                    if row["Status"] == "a":
                        tags.append(("Available", "green"))
                    elif row["Status"] in ("i", "u"):
                        tags.append(("Out", "red"))
                    elif row["Status"] == "d":
                        tags.append(("Doubtful", "yellow"))
                    elif row["Status"] == "s":
                        tags.append(("Suspended", "red"))

                    render_list_card(
                        f"{row['Player']} · {row['Team']}",
                        tags,
                        f'<span>GW Pts</span> {int(float(row["GW_Points"]))}{mult_info} · <span>Season</span> {int(float(row["Season_Points"]))} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 🪑 Substitutes / Bench")
                for _, row in bench.iterrows():
                    sub_num = int(row["order"]) - 11
                    sub_label = f"Sub {sub_num} ({row['Position']})"
                    tags = [(sub_label, "gray")]

                    if row["is_cap"]:
                        tags.append(("Captain", "green"))
                    if row["is_vc"]:
                        tags.append(("Vice Captain", "yellow"))

                    if row["Status"] == "a":
                        tags.append(("Available", "green"))
                    elif row["Status"] in ("i", "u"):
                        tags.append(("Out", "red"))
                    elif row["Status"] == "d":
                        tags.append(("Doubtful", "yellow"))
                    elif row["Status"] == "s":
                        tags.append(("Suspended", "red"))

                    render_list_card(
                        f"{row['Player']} · {row['Team']}",
                        tags,
                        f'<span>GW Pts</span> {int(float(row["Raw_GW_Pts"]))} · <span>Season</span> {int(float(row["Season_Points"]))} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                    )

            with col_news:
                st.markdown('<div class="section-card"><h3>Squad News</h3></div>', unsafe_allow_html=True)
                flagged_players = squad_df[
                    (squad_df["Status"] != "a")
                    & (squad_df["News"].notna())
                    & (squad_df["News"] != "")
                    & (squad_df["News"] != "None")
                ]

                if flagged_players.empty:
                    st.success("All players available.")
                else:
                    for _, row in flagged_players.iterrows():
                        chance_val = row["Chance"]
                        chance_str = (
                            f" ({int(float(chance_val))}% chance)"
                            if pd.notna(chance_val) and str(chance_val).strip() not in ("", "None")
                            else ""
                        )
                        if row["Status"] in ("i", "u"):
                            st.error(f"**{row['Player']}** (Out)\n\n{row['News']}")
                        elif row["Status"] == "d":
                            st.warning(f"**{row['Player']}**{chance_str}\n\n{row['News']}")
                        elif row["Status"] == "s":
                            st.error(f"**{row['Player']}** (Suspended)\n\n{row['News']}")
                        else:
                            st.info(f"**{row['Player']}**\n\n{row['News']}")

        except Exception as e:
            st.error(f"Could not load team. Verify your FPL ID. (Error: {e})")

# ── TAB 5: Transfer Market ───────────────────────────────────────────────────
with tab5:
    col_t5_hdr, col_t5_pop = st.columns([6, 1])
    with col_t5_hdr:
        section_header("Transfer Market Watch", "Track net transfers to anticipate price changes")
    with col_t5_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Transfer Velocity & Price Change Guide**
                
                * **Net Transfers:** Transfers in minus transfers out for the active gameweek.
                * 📈 **Heating Up (Green):** Rapid inbound transfers. Crossing the threshold triggers a **+£0.1m price rise** at 01:30 GMT.
                * 📉 **Cooling Down (Red):** Heavy selling momentum. Indicates an impending **-£0.1m price drop**.
                * **Strategy:** Buy targets early in the gameweek before their price rises, and sell red-flagged assets before value is eroded.
                * 🔍 **Search & Squad Filter:** Search specific targets or check the squad box to monitor transfer trends across your 15 players.
                """
            )

    col_search5, col_sq5 = st.columns([2, 1])
    with col_search5:
        search_query5 = st.text_input(
            "🔍 Search Player / Club",
            placeholder="e.g. Palmer, Chelsea, Haaland, MCI...",
            key="tab5_search",
        )
    with col_sq5:
        st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
        only_my_squad_tab5 = st.checkbox("🎯 Only My Squad Players", key="tab5_only_squad")

    market_query = """
    SELECT
        p.id AS element_id,
        p.web_name AS Player,
        p.first_name || ' ' || p.second_name AS Full_Name,
        t.short_name AS Team,
        t.name AS Club_Name,
        (p.now_cost - p.cost_change_start) / 10.0 AS Start_Price,
        p.now_cost / 10.0 AS Current_Price,
        p.cost_change_start / 10.0 AS Total_Change,
        (p.transfers_in_event - p.transfers_out_event) AS Net_Transfers
    FROM players p
    INNER JOIN teams t ON p.team = t.id
    ORDER BY Net_Transfers DESC
    """
    market_df = pd.read_sql(market_query, conn)
    for col_name in ("Start_Price", "Current_Price", "Total_Change", "Net_Transfers"):
        market_df[col_name] = pd.to_numeric(market_df[col_name], errors="coerce")
    THRESHOLD = 60000

    # Filter market by manager squad
    if only_my_squad_tab5:
        active_manager_id_tab5 = st.session_state.get("manager_id", "").strip()
        if not active_manager_id_tab5:
            st.info("💡 Enter your FPL Team ID in the sidebar or Tab 4 to filter by your squad.")
            market_df = market_df.iloc[0:0]
        else:
            squad_ids_tab5 = get_manager_squad_ids(active_manager_id_tab5, current_gw)
            market_df = market_df[market_df["element_id"].isin(squad_ids_tab5)]

    # Filter market by search query
    if search_query5.strip():
        q5 = search_query5.strip()
        market_df = market_df[
            market_df["Player"].str.contains(q5, case=False, na=False)
            | market_df["Full_Name"].str.contains(q5, case=False, na=False)
            | market_df["Team"].str.contains(q5, case=False, na=False)
            | market_df["Club_Name"].str.contains(q5, case=False, na=False)
        ]

    if market_df.empty:
        st.info("No players found matching your transfer search or squad filter criteria.")
    else:
        col_in, col_out = st.columns(2)

        with col_in:
            st.markdown("#### Heating Up")
            heating_df = market_df.head(10)
            if heating_df.empty:
                st.write("No matching players heating up.")
            else:
                for _, row in heating_df.iterrows():
                    progress = min((max(0, row["Net_Transfers"]) / THRESHOLD) * 100, 100)
                    change_tag = ("Rising", "green") if row["Total_Change"] > 0 else ("Flat", "gray")
                    render_list_card(
                        f"{row['Player']} · {row['Team']}",
                        [("Transfer In", "green"), change_tag],
                        f'<span>Price</span> £{fmt_num(row["Current_Price"], ".1f")} · <span>Change</span> {fmt_num(row["Total_Change"], "+.1f")}m · <span>Net</span> {int(float(row["Net_Transfers"])):,}',
                        progress=progress,
                    )

        with col_out:
            st.markdown("#### Cooling Down")
            cooling_df = market_df.tail(10).sort_values(by="Net_Transfers", ascending=True)
            if cooling_df.empty:
                st.write("No matching players cooling down.")
            else:
                for _, row in cooling_df.iterrows():
                    progress = min((abs(min(0, row["Net_Transfers"])) / THRESHOLD) * 100, 100)
                    change_tag = ("Falling", "red") if row["Total_Change"] < 0 else ("Flat", "gray")
                    render_list_card(
                        f"{row['Player']} · {row['Team']}",
                        [("Transfer Out", "red"), change_tag],
                        f'<span>Price</span> £{fmt_num(row["Current_Price"], ".1f")} · <span>Change</span> {fmt_num(row["Total_Change"], "+.1f")}m · <span>Net</span> {int(float(row["Net_Transfers"])):,}',
                        progress=progress,
                        progress_red=True,
                    )

conn.close()