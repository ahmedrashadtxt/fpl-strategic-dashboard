import pandas as pd
import streamlit as st
from data import get_manager_squad_ids
from theme import section_header


def render_fixture_ticker_tab(conn, current_gw):
  col_t3_hdr, col_t3_pop = st.columns([6, 1])
  with col_t3_hdr:
    section_header(
        f"Fixture Difficulty · GW{current_gw}–{current_gw + 4}",
        "Upcoming schedule ranked by difficulty",
    )
  with col_t3_pop:
    st.markdown(
        "<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True
    )
    with st.popover("📖 Guide"):
      st.markdown("""
                **Fixture Ticker Guide**
                
                * **Difficulty Rating:** Sum of official FDR scores across the next 5 gameweeks.
                * **(H) vs. (A):** Designates Home or Away fixtures. Home games offer historically higher clean sheet and scoring conversion probabilities.
                * 🟢 **Green Run (≤10 pts):** Prime fixture swings. Prioritize attacking transfers and defensive double-ups.
                * 🔴 **Tough Run (≥15 pts):** Hold off buying assets from these clubs until their schedule clears.
                * 🔍 **Search & Squad Filter:** Searching a player filters by their respective club; enabling squad filter isolates clubs of your 15 players.
            """)

  col_search3, col_sq3 = st.columns([2, 1])
  with col_search3:
    search_query3 = st.text_input(
        "🔍 Search Player / Club",
        placeholder="e.g. Saka, Arsenal, Haaland, MCI...",
        key="tab3_search",
    )
  with col_sq3:
    st.markdown(
        "<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True
    )
    only_my_squad_tab3 = st.toggle(
        "🎯 Only My Squad Clubs", key="tab3_only_squad"
    )

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
  fixtures_df = pd.read_sql(
      fixtures_query, conn, params=[current_gw, current_gw + 5]
  )

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

  # Fetch both short_name and full name for the final dataframe mapping
  teams_df = pd.read_sql("SELECT short_name, name FROM teams ORDER BY name", conn)
  teams_list = teams_df["short_name"].tolist()
  team_name_map = dict(zip(teams_df["short_name"], teams_df["name"]))
  
  target_team_short_names = set(teams_list)

  if only_my_squad_tab3:
    active_manager_id_tab3 = st.session_state.get("manager_id", "").strip()
    if not active_manager_id_tab3:
      st.info(
          "💡 Enter your FPL Team ID in the sidebar or Squad Analyzer tab to"
          " filter by your squad."
      )
      target_team_short_names = set()
    else:
      squad_ids_tab3 = get_manager_squad_ids(active_manager_id_tab3, current_gw)
      squad_teams = pt_lookup[pt_lookup["element_id"].isin(squad_ids_tab3)][
          "short_name"
      ].unique()
      target_team_short_names = target_team_short_names.intersection(
          set(squad_teams)
      )

  if search_query3.strip():
    q3 = search_query3.strip().lower()
    matching_from_lookup = pt_lookup[
        pt_lookup["web_name"].str.contains(q3, case=False, na=False)
        | pt_lookup["full_name"].str.contains(q3, case=False, na=False)
        | pt_lookup["short_name"].str.contains(q3, case=False, na=False)
        | pt_lookup["club_name"].str.contains(q3, case=False, na=False)
    ]["short_name"].unique()
    target_team_short_names = target_team_short_names.intersection(
        set(matching_from_lookup)
    )

  ticker_data = []
  gw_cols = [f"GW {gw}" for gw in range(current_gw, current_gw + 5)]

  for team in teams_list:
    row = {"Team": team}
    total_difficulty = 0
    for gw in range(current_gw, current_gw + 5):
      match = fixtures_df[
          (fixtures_df["GW"] == gw)
          & (
              (fixtures_df["Home_Team"] == team)
              | (fixtures_df["Away_Team"] == team)
          )
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

  ticker_df = pd.DataFrame(ticker_data).sort_values(
      by="Difficulty Rating", ascending=True
  )
  ticker_df = ticker_df[ticker_df["Team"].isin(target_team_short_names)]

  if ticker_df.empty:
    st.info("No clubs found matching your search or squad criteria.")
  else:
    # Update the "Team" column to display "Full Name (TICKER)" right before rendering
    ticker_df["Team"] = ticker_df["Team"].apply(lambda x: f"{team_name_map.get(x, x)} ({x})")

    def style_fdr_cell(val):
      val_str = str(val)
      if "[2]" in val_str:
        return (
            "background-color: rgba(34, 197, 94, 0.25); color: #4ade80;"
            " font-weight: 600; text-align: center;"
        )
      elif "[3]" in val_str:
        return (
            "background-color: rgba(100, 116, 139, 0.15); color: #cbd5e1;"
            " text-align: center;"
        )
      elif "[4]" in val_str:
        return (
            "background-color: rgba(249, 115, 22, 0.25); color: #fb923c;"
            " font-weight: 600; text-align: center;"
        )
      elif "[5]" in val_str:
        return (
            "background-color: rgba(239, 68, 68, 0.3); color: #f87171;"
            " font-weight: 700; text-align: center;"
        )
      elif "Blank" in val_str:
        return (
            "background-color: rgba(15, 23, 42, 0.5); color: #64748b;"
            " font-style: italic; text-align: center;"
        )
      return "text-align: center;"

    def style_rating_col(val):
      try:
        v = int(val)
        if v <= 11:
          return (
              "background-color: rgba(34, 197, 94, 0.25); color: #22c55e;"
              " font-weight: bold; text-align: center;"
          )
        elif v <= 14:
          return (
              "background-color: rgba(234, 179, 8, 0.2); color: #eab308;"
              " font-weight: bold; text-align: center;"
          )
        else:
          return (
              "background-color: rgba(239, 68, 68, 0.25); color: #ef4444;"
              " font-weight: bold; text-align: center;"
          )
      except Exception:
        return ""

    styled_ticker = ticker_df.style.map(
        style_fdr_cell, subset=gw_cols
    ).map(style_rating_col, subset=["Difficulty Rating"])

    st.dataframe(
        styled_ticker,
        hide_index=True,
        width="stretch",
        column_config={
            "Team": st.column_config.TextColumn("Club"),
            "Difficulty Rating": st.column_config.NumberColumn(
                "Total FDR (5 GW)"
            ),
        },
    )