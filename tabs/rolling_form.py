from data import get_manager_squad_ids
import pandas as pd
import plotly.express as px
import streamlit as st
from theme import fmt_num, render_list_card, section_header

pos_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}


def render_rolling_form_tab(conn, current_gw, teams_fdr_map):
  col_t2_hdr, col_t2_pop = st.columns([6, 1])
  with col_t2_hdr:
    section_header(
        "Rolling Form & Trends",
        "Analyze form trajectory vs upcoming fixture schedule",
    )
  with col_t2_pop:
    st.markdown(
        "<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True
    )
    with st.popover("📖 Guide"):
      st.markdown("""
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
            """)

  table_exists = pd.read_sql(
      "SELECT name FROM sqlite_master WHERE type='table' AND"
      " name='player_match_history'",
      conn,
  )

  if table_exists.empty:
    st.warning(
        "⚠️ Match history table `player_match_history` was not found in"
        " `fpl.db`. Please click **Refresh Data** in the sidebar to populate"
        " match histories."
    )
    return

  col_search2, col_w, col_pos2, col_min_matches, col_min_mins2, col_sort2 = (
      st.columns([1.4, 0.9, 0.8, 0.9, 0.9, 1.2])
  )
  with col_search2:
    search_query2 = st.text_input(
        "🔍 Search Player / Club",
        placeholder="e.g. Cherki, Saka, Chelsea, ARS...",
        key="tab2_search",
    )
  with col_w:
    window_size = st.slider(
        "Match Window",
        min_value=3,
        max_value=10,
        value=5,
        step=1,
        key="tab2_window",
    )
  with col_pos2:
    pos_filter2 = st.selectbox(
        "Position", ["All", "GKP", "DEF", "MID", "FWD"], key="tab2_pos"
    )
  with col_min_matches:
    min_matches = st.slider(
        "Min Matches",
        min_value=1,
        max_value=window_size,
        value=min(3, window_size),
        step=1,
        key="tab2_matches",
    )
  with col_min_mins2:
    min_avg_mins = st.slider(
        "Min Avg Mins", 0, 90, 45, step=15, key="tab2_mins"
    )
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

  only_my_squad = st.toggle("🎯 Only My Squad Players", key="tab2_only_squad")
  pos_clause2 = (
      f"AND p.element_type = {pos_map[pos_filter2]}"
      if pos_filter2 != "All"
      else ""
  )

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
    df_rolling["Upcoming_FDR"] = (
        df_rolling["Team_ID"].map(teams_fdr_map).fillna(15).astype(int)
    )

    active_manager_id = st.session_state.get("manager_id", "").strip()
    if only_my_squad:
      if not active_manager_id:
        st.info(
            "💡 Enter your FPL Team ID in the sidebar or Squad Analyzer tab to"
            " filter by your squad."
        )
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
              "Upcoming_FDR": (
                  "Upcoming 5-GW Fixture Difficulty Rating (Lower = Easier)"
              ),
              "Rolling_Sum_xGI": f"Rolling {window_size}-Match xGI",
              "Pos": "Position",
          },
          title=(
              "Underlying Form vs Schedule (L"
              f"{window_size} xGI vs Next 5 FDR)"
          ),
          color_discrete_map={
              "GKP": "#f59e0b",
              "DEF": "#3b82f6",
              "MID": "#10b981",
              "FWD": "#ef4444",
          },
      )

      fig.add_vline(
          x=x_mid, line_dash="dash", line_color="rgba(255, 255, 255, 0.25)"
      )
      fig.add_hline(
          y=y_mid, line_dash="dash", line_color="rgba(255, 255, 255, 0.25)"
      )

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

    top_rolling = df_rolling.head(min(5, len(df_rolling)))
    cols_r = st.columns(len(top_rolling))
    for i, (_, row) in enumerate(top_rolling.iterrows()):
      with cols_r[i]:
        render_list_card(
            f"{row['Player']} ({row['Team']})",
            [(row["Pos"], "blue"), (f"L{window_size} Form", "green")],
            f'<span>Price</span> £{fmt_num(row["Price"], ".1f")} · <span>xGI</span>'
            f' {fmt_num(row["Rolling_Sum_xGI"])} · <span>xGI/90</span>'
            f' {fmt_num(row["Rolling_xGI_per_90"])} · <span>Next 5 FDR</span>'
            f' {int(row["Upcoming_FDR"])} · <span>Avg Pts</span>'
            f' {fmt_num(row["Rolling_Avg_Pts"], ".1f")}',
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
            "Rolling_Sum_xGI": st.column_config.NumberColumn(
                f"Sum xGI (L{window_size})", format="%.2f"
            ),
            "Rolling_xGI_per_90": st.column_config.NumberColumn(
                f"xGI/90 (L{window_size})", format="%.2f"
            ),
            "Rolling_Avg_Pts": st.column_config.NumberColumn(
                f"Avg Pts (L{window_size})", format="%.2f"
            ),
            "Upcoming_FDR": st.column_config.NumberColumn(
                "Next 5 FDR (Ease)", format="%d"
            ),
            "Rolling_Avg_Mins": st.column_config.NumberColumn(
                f"Avg Mins (L{window_size})", format="%.1f"
            ),
            "Rolling_Matches_Played": st.column_config.NumberColumn(
                "Apps", format="%d"
            ),
        },
    )