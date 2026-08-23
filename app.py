import streamlit as st
import sqlite3
import pandas as pd
import requests
from streamlit.runtime.scriptrunner import get_script_run_ctx

if get_script_run_ctx() is None:
    import subprocess
    import sys

    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", __file__]))

st.set_page_config(page_title="The Hype Press - FPL Analytics Hub", layout="wide")

# ==========================================
# HEADER & REFRESH BUTTON
# ==========================================
header_col, btn_col = st.columns([5, 1])

with header_col:
    st.title("⚽ FPL Strategic Dashboard")

with btn_col:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh", width="stretch"):
        st.cache_data.clear()
        st.rerun()

conn = sqlite3.connect('fpl.db')

# Identify the upcoming gameweek
events_df = pd.read_sql("SELECT id, name, is_current, is_next FROM events", conn)
next_gw_row = events_df[events_df['is_next'] == 1]
current_gw = int(next_gw_row['id'].values[0]) if not next_gw_row.empty else 1

# Create 4 dedicated strategic tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Expected Stats & Underperformance", 
    "🗓️ Fixture Difficulty Ticker", 
    "👤 Manager Squad Analyzer",
    "📈 Transfer Market Watch"
])

# ==========================================
# TAB 1: EXPECTED STATS & UNDERPERFORMANCE
# ==========================================
with tab1:
    st.subheader("Identify High-Value & Unlucky Assets")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        min_minutes = st.slider("Minimum Minutes Played", 0, 900, 0, step=45)
    with col2:
        position_filter = st.selectbox("Filter Position", ["All", "GKP", "DEF", "MID", "FWD"])
    with col3:
        sort_by = st.selectbox(
            "Rank By",
            [
                "Expected Goal Involvements (xGI)",
                "Goals Below Expected (Unlucky)",
                "xGI per 90",
                "Total Points",
                "Clean Sheets",
                "Goalkeeper Saves"
            ]
        )

    # Position mapping (1: GKP, 2: DEF, 3: MID, 4: FWD)
    pos_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}
    pos_clause = f"AND p.element_type = {pos_map[position_filter]}" if position_filter != "All" else ""

    # SQL query including Total Points
    query = f"""
    SELECT 
        p.web_name AS Player,
        t.short_name AS Team,
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

    # Sorting logic
    if sort_by == "Expected Goal Involvements (xGI)":
        df_xgi = df_xgi.sort_values(by="xGI", ascending=False)
    elif sort_by == "Goals Below Expected (Unlucky)":
        df_xgi = df_xgi.sort_values(by="xG_Delta", ascending=False)
    elif sort_by == "xGI per 90":
        df_xgi = df_xgi.sort_values(by="xGI_per_90", ascending=False)
    elif sort_by == "Total Points":
        df_xgi = df_xgi.sort_values(by="Total_Points", ascending=False)
    elif sort_by == "Clean Sheets":
        df_xgi = df_xgi.sort_values(by="Clean_Sheets", ascending=False)
    elif sort_by == "Goalkeeper Saves":
        df_xgi = df_xgi.sort_values(by="Saves", ascending=False)

    # Styling helper for xG Delta
    def highlight_xg_delta(val):
        try:
            val = float(val)
            if val >= 0.5:
                return 'background-color: rgba(39, 174, 96, 0.4)'
            elif val > 0:
                return 'background-color: rgba(39, 174, 96, 0.15)'
            elif val <= -0.5:
                return 'background-color: rgba(231, 76, 60, 0.2)'
        except (ValueError, TypeError):
            pass
        return ''

    df_display = df_xgi.head(25)
    styled_df = df_display.style.map(highlight_xg_delta, subset=['xG_Delta'])

    # Render table with custom column formatting
    st.dataframe(
        styled_df,
        hide_index=True,
        width="stretch",
        column_config={
            "Price": st.column_config.NumberColumn(format="£%.1f"),
            "Minutes": st.column_config.NumberColumn("Mins"),
            "Total_Points": st.column_config.NumberColumn("Pts", help="Total FPL points accumulated this season"),
            "Goals": st.column_config.NumberColumn("G"),
            "Assists": st.column_config.NumberColumn("A"),
            "Clean_Sheets": st.column_config.NumberColumn("CS", help="Clean Sheets kept"),
            "Saves": st.column_config.NumberColumn("Saves", help="Total shots saved (Goalkeepers)"),
            "xG": st.column_config.NumberColumn(format="%.2f"),
            "xA": st.column_config.NumberColumn(format="%.2f"),
            "xGI": st.column_config.NumberColumn(format="%.2f"),
            "xG_Delta": st.column_config.NumberColumn(
                format="%.2f",
                help="Positive = Underperforming (Due for a haul). Dark green indicates a buy signal."
            ),
            "xGI_per_90": st.column_config.NumberColumn("xGI/90", format="%.2f")
        }
    )

# ==========================================
# TAB 2: FIXTURE DIFFICULTY TICKER (FDR)
# ==========================================
with tab2:
    st.subheader(f"Upcoming Schedule: GW{current_gw} to GW{current_gw + 4}")
    
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

    # Reconstruct matrix of Teams vs Upcoming GWs
    teams_list = pd.read_sql("SELECT short_name FROM teams ORDER BY name", conn)['short_name'].tolist()
    ticker_data = []

    for team in teams_list:
        row = {"Team": team}
        total_difficulty = 0
        
        for gw in range(current_gw, current_gw + 5):
            match = fixtures_df[(fixtures_df['GW'] == gw) & ((fixtures_df['Home_Team'] == team) | (fixtures_df['Away_Team'] == team))]
            if not match.empty:
                m = match.iloc[0]
                if m['Home_Team'] == team:
                    opp = f"{m['Away_Team']} (H)"
                    diff = m['Home_Diff']
                else:
                    opp = f"{m['Home_Team']} (A)"
                    diff = m['Away_Diff']
                row[f"GW {gw}"] = f"{opp} [{diff}]"
                total_difficulty += diff
            else:
                row[f"GW {gw}"] = "Blank"
                total_difficulty += 5
        
        row["Difficulty Rating"] = total_difficulty
        ticker_data.append(row)

    ticker_df = pd.DataFrame(ticker_data).sort_values(by="Difficulty Rating", ascending=True)
    st.dataframe(ticker_df, width="stretch")

# ==========================================
# TAB 3: MANAGER SQUAD LOOKUP
# ==========================================
with tab3:
    st.subheader("Import FPL Manager Team")
    manager_id = st.text_input("Enter FPL Team / Entry ID (e.g., from your FPL points URL):", "")

    if manager_id:
        try:
            # 1. Fetch Manager Profile & Summary
            mgr_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
            mgr_data = requests.get(mgr_url).json()

            # Determine the target gameweek
            target_gw = current_gw if current_gw >= 1 else 1

            # 2. Fetch Gameweek Picks
            picks_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{target_gw}/picks/"
            picks_res = requests.get(picks_url)
            
            # Fallback to GW1 if the target gameweek picks haven't unlocked yet
            if picks_res.status_code != 200 and target_gw > 1:
                target_gw -= 1
                picks_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{target_gw}/picks/"
                picks_res = requests.get(picks_url)
                
            picks_data = picks_res.json()

            # 3. Fetch Live Gameweek Points from FPL Live API
            live_url = f"https://fantasy.premierleague.com/api/event/{target_gw}/live/"
            live_res = requests.get(live_url).json()
            live_points_map = {item['id']: item['stats']['total_points'] for item in live_res.get('elements', [])}

            # 4. Extract Squad Information & Metadata
            entry_history = picks_data.get('entry_history', {})
            transfers_cost = entry_history.get('event_transfers_cost', 0)
            total_points = mgr_data.get('summary_overall_points', 0)

            picks_list = picks_data.get('picks', [])
            pick_ids = [p['element'] for p in picks_list]
            placeholders = ','.join(['?'] * len(pick_ids))

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

            # Map Pick metadata
            meta_dict = {
                p['element']: {
                    'multiplier': p['multiplier'],
                    'is_captain': p['is_captain'],
                    'is_vice': p['is_vice_captain'],
                    'order': p['position']
                } for p in picks_list
            }

            squad_df['order'] = squad_df['id'].map(lambda x: meta_dict[x]['order'])
            squad_df['Multiplier'] = squad_df['id'].map(lambda x: meta_dict[x]['multiplier'])
            squad_df['is_cap'] = squad_df['id'].map(lambda x: meta_dict[x]['is_captain'])
            squad_df['is_vc'] = squad_df['id'].map(lambda x: meta_dict[x]['is_vice'])

            # Calculate Live Gameweek Points with captain multiplier
            squad_df['Raw_GW_Pts'] = squad_df['id'].map(lambda x: live_points_map.get(x, 0))
            squad_df['GW_Points'] = squad_df['Raw_GW_Pts'] * squad_df['Multiplier']

            # Calculate Live GW Points directly from Starting XI (positions 1 to 11)
            starting_xi_pts = squad_df[squad_df['order'] <= 11]['GW_Points'].sum()
            live_gw_pts = int(starting_xi_pts) - transfers_cost

            # Render Manager Summary Header (Single Block)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Manager", mgr_data.get('name', 'My Team'))
            col2.metric("Overall Rank", f"{mgr_data.get('summary_overall_rank', 0):,}")
            col3.metric("Total Points", f"{total_points:,}")
            col4.metric(
                f"GW {target_gw} Points", 
                live_gw_pts, 
                delta=f"-{transfers_cost} pts hit" if transfers_cost > 0 else None, 
                delta_color="inverse"
            )

            def format_player_name(row):
                name = row['Player']
                if row['is_cap']:
                    return f"{name} (C)"
                if row['is_vc']:
                    return f"{name} (VC)"
                if row['order'] > 11:
                    return f"{name} (Bench)"
                return name

            squad_df['Player'] = squad_df.apply(format_player_name, axis=1)
            squad_df = squad_df.sort_values(by='order', ascending=True)

            # 5. Display Layout
            col_table, col_news = st.columns([7, 3])

            with col_table:
                display_cols = ['Player', 'Team', 'Position', 'Cost', 'GW_Points', 'Season_Points']
                st.dataframe(
                    squad_df[display_cols],
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Cost": st.column_config.NumberColumn(format="£%.1f"),
                        "GW_Points": st.column_config.NumberColumn(help=f"Points scored in Gameweek {target_gw} (Captain points doubled)"),
                        "Season_Points": st.column_config.NumberColumn("Total Points")
                    }
                )

            with col_news:
                st.subheader("🏥 Squad News")
                flagged_players = squad_df[
                    (squad_df['Status'] != 'a') & 
                    (squad_df['News'].notna()) & 
                    (squad_df['News'] != '') & 
                    (squad_df['News'] != 'None')
                ]

                if flagged_players.empty:
                    st.success("All players are available. No injuries or suspensions reported.")
                else:
                    for _, row in flagged_players.iterrows():
                        chance_val = row['Chance']
                        chance_str = f" ({int(float(chance_val))}% chance)" if pd.notna(chance_val) and str(chance_val).strip() not in ['', 'None'] else ""
                        
                        if row['Status'] in ['i', 'u']:
                            st.error(f"**{row['Player']}** (Out)\n\n{row['News']}")
                        elif row['Status'] == 'd':
                            st.warning(f"**{row['Player']}**{chance_str}\n\n{row['News']}")
                        elif row['Status'] == 's':
                            st.error(f"**{row['Player']}** (Suspended)\n\n{row['News']}")
                        else:
                            st.info(f"**{row['Player']}**\n\n{row['News']}")

        except Exception as e:
            st.error(f"Could not load team. Verify your FPL ID. (Error: {e})")

# ==========================================
# TAB 4: TRANSFER MARKET WATCH
# ==========================================
with tab4:
    st.subheader("Live Transfer Market Trends")
    st.write("Track net transfers to anticipate price rises and falls before the midnight deadline.")

    market_query = """
    SELECT 
        p.web_name AS Player,
        t.short_name AS Team,
        (p.now_cost - p.cost_change_start) / 10.0 AS Start_Price,
        p.now_cost / 10.0 AS Current_Price,
        p.cost_change_start / 10.0 AS Total_Change,
        (p.transfers_in_event - p.transfers_out_event) AS Net_Transfers
    FROM players p
    INNER JOIN teams t ON p.team = t.id
    ORDER BY Net_Transfers DESC
    """
    market_df = pd.read_sql(market_query, conn)

    def highlight_total_change(val):
        try:
            val = float(val)
            if val > 0:
                return 'background-color: rgba(39, 174, 96, 0.35)'
            elif val < 0:
                return 'background-color: rgba(231, 76, 60, 0.35)'
        except (ValueError, TypeError):
            pass
        return ''

    col_config = {
        "Start_Price": st.column_config.NumberColumn("Start Price", format="£%.1f"),
        "Current_Price": st.column_config.NumberColumn("Current Price", format="£%.1f"),
        "Total_Change": st.column_config.NumberColumn(
            "Change", 
            format="%+.1fm", 
            help="Total price change since GW1. Green indicates a rise; red indicates a drop."
        ),
        "Net_Transfers": st.column_config.NumberColumn("Net Transfers")
    }

    THRESHOLD = 60000

    col_in, col_out = st.columns(2)

    with col_in:
        st.markdown("### 🔥 Heating Up (Likely to Rise)")
        top_in = market_df.head(20).copy()
        top_in['Progress'] = (top_in['Net_Transfers'] / THRESHOLD) * 100
        top_in['Progress'] = top_in['Progress'].clip(upper=100)
        
        styled_top_in = top_in.style.map(highlight_total_change, subset=['Total_Change'])
        
        col_config_in = col_config.copy()
        col_config_in["Progress"] = st.column_config.ProgressColumn(
            "Rise Probability",
            help=f"Estimated progress toward a price rise based on a {THRESHOLD:,} net transfer threshold.",
            format="%d%%",
            min_value=0,
            max_value=100,
        )
        
        st.dataframe(
            styled_top_in,
            hide_index=True,
            width="stretch",
            column_config=col_config_in
        )

    with col_out:
        st.markdown("### ❄️ Cooling Down (Likely to Drop)")
        top_out = market_df.tail(20).copy()
        top_out = top_out.sort_values(by="Net_Transfers", ascending=True)
        top_out['Progress'] = (top_out['Net_Transfers'].abs() / THRESHOLD) * 100
        top_out['Progress'] = top_out['Progress'].clip(upper=100)
        
        styled_top_out = top_out.style.map(highlight_total_change, subset=['Total_Change'])
        
        col_config_out = col_config.copy()
        col_config_out["Progress"] = st.column_config.ProgressColumn(
            "Drop Probability",
            help=f"Estimated progress toward a price drop based on a {THRESHOLD:,} net transfer threshold.",
            format="%d%%",
            min_value=0,
            max_value=100,
        )
        
        st.dataframe(
            styled_top_out,
            hide_index=True,
            width="stretch",
            column_config=col_config_out
        )

conn.close()