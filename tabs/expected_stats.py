from data import get_manager_squad_ids
import pandas as pd
import streamlit as st
from theme import fmt_num, render_list_card, section_header

pos_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}


def get_player_img_url(photo, code=None):
    photo_str = str(photo) if pd.notna(photo) else ""
    if not photo_str or "Photo-Missing" in photo_str or photo_str == "None":
        if pd.notna(code) and str(code).strip():
            return f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{int(code)}.png"
        return "https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png"

    base_name = photo_str.replace(".jpg", "").replace(".png", "")
    if not base_name.startswith("p"):
        base_name = f"p{base_name}"
    return f"https://resources.premierleague.com/premierleague/photos/players/110x140/{base_name}.png"


def render_expected_stats_tab(conn, current_gw):
    col_t1_hdr, col_t1_pop = st.columns([6, 1])
    with col_t1_hdr:
        section_header(
            "Expected Stats & Underperformance",
            "Identify high-value and unlucky assets",
        )
    with col_t1_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Expected Stats & Regression Guide**
                
                * **xG / xA / xGI:** Expected Goals, Assists, and Goal Involvements based on shot location and chance quality.
                * **ΔxG (xG Delta):** Calculated as `xG - Actual Goals`.
                    * 🟢 **Buy Signal (ΔxG ≥ +0.5):** Creating/receiving high-quality chances but unlucky with finishing.
                    * 🔴 **Sell Signal (ΔxG ≤ -0.5):** Outperforming underlying metrics significantly. Current scoring conversion is historically unsustainable.
                * **xGI / 90:** Current season chance involvement per 90 minutes played.
                * **Career GI / 90:** Multi-season historical actual `(Goals + Assists) / Minutes * 90` baseline from prior Premier League campaigns.
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
        min_minutes = st.slider(
            "Minimum Minutes Played", 0, 900, 0, step=45, key="tab1_min_mins"
        )
    with col2:
        position_filter = st.selectbox(
            "Filter Position", ["All", "GKP", "DEF", "MID", "FWD"], key="tab1_pos"
        )
    with col3:
        sort_by = st.selectbox(
            "Rank By",
            [
                "Expected Goal Involvements (xGI)",
                "Goals Below Expected (Unlucky)",
                "xGI per 90",
                "Career GI / 90 (Past Seasons)",
                "Total Points",
                "Clean Sheets",
                "Goalkeeper Saves",
            ],
            key="tab1_sort",
        )

    col_toggle1, col_toggle2 = st.columns([1, 1])
    with col_toggle1:
        only_my_squad_tab1 = st.toggle(
            "🎯 Only My Squad Players", key="tab1_only_squad"
        )
    with col_toggle2:
        show_career_baseline = st.toggle(
            "🏛️ Show Career Baselines (Past Seasons)", value=False, key="tab1_show_career"
        )

    pos_clause = (
        f"AND p.element_type = {pos_map[position_filter]}"
        if position_filter != "All"
        else ""
    )

    table_check = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='player_past_seasons'",
        conn,
    )
    has_history = not table_check.empty

    hist_join = """
        LEFT JOIN (
            SELECT 
                element_id,
                ROUND((SUM(goals_scored + assists) * 1.0 / NULLIF(SUM(minutes), 0)) * 90.0, 2) AS Career_GI_90,
                ROUND((SUM(total_points) * 1.0 / NULLIF(SUM(minutes), 0)) * 90.0, 2) AS Career_Pts_90,
                SUM(minutes) AS Career_Mins
            FROM player_past_seasons
            GROUP BY element_id
        ) hist ON p.id = hist.element_id
    """ if has_history else ""

    hist_select = """
        hist.Career_GI_90,
        hist.Career_Pts_90,
        hist.Career_Mins,
    """ if has_history else """
        NULL AS Career_GI_90,
        NULL AS Career_Pts_90,
        NULL AS Career_Mins,
    """

    query = f"""
    SELECT
        p.id AS element_id,
        p.code,
        p.photo,
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
        p.expected_goal_involvements_per_90 AS xGI_per_90,
        {hist_select}
        p.now_cost / 10.0 AS price_val
    FROM players p
    INNER JOIN teams t ON p.team = t.id
    {hist_join}
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
        "Career_GI_90",
        "Career_Pts_90",
        "Career_Mins",
    ):
        if col_name in df_xgi.columns:
            df_xgi[col_name] = pd.to_numeric(df_xgi[col_name], errors="coerce")

    # Clean any invalid rows
    df_xgi = df_xgi.dropna(subset=["Player"])
    df_xgi = df_xgi[df_xgi["Player"].astype(str).str.strip() != ""]

    df_xgi["Photo"] = [
        get_player_img_url(ph, c) for ph, c in zip(df_xgi["photo"], df_xgi["code"])
    ]

    active_manager_id_tab1 = st.session_state.get("manager_id", "").strip()
    if only_my_squad_tab1:
        if not active_manager_id_tab1:
            st.info(
                "💡 Enter your FPL Team ID in the sidebar or Squad Analyzer tab to filter by your squad."
            )
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
        "Career GI / 90 (Past Seasons)": ("Career_GI_90", False),
        "Total Points": ("Total_Points", False),
        "Clean Sheets": ("Clean_Sheets", False),
        "Goalkeeper Saves": ("Saves", False),
    }
    col, asc = sort_map[sort_by]
    df_xgi = df_xgi.sort_values(by=col, ascending=asc)

    if df_xgi.empty:
        st.info(f"No players found matching '{search_query}'. Try adjusting your filters.")
    else:
        top_cards = df_xgi.head(min(4, len(df_xgi)))
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
                hist_note = (
                    f" · <span>Career GI/90</span> {fmt_num(row['Career_GI_90'])}"
                    if pd.notna(row.get("Career_GI_90")) and show_career_baseline
                    else ""
                )
                card_img = get_player_img_url(row.get("photo"), row.get("code"))
                render_list_card(
                    f"{row['Player']} ({row['Team']})",
                    [(row["Pos"], "blue"), signal_tag],
                    f'<span>Price</span> £{fmt_num(row["Price"], ".1f")} · <span>xGI</span>'
                    f' {fmt_num(row["xGI"])} · <span>Pts</span>'
                    f' {int(float(row["Total_Points"]))} · <span>ΔxG</span>'
                    f' {fmt_num(delta, "+.2f")}{hist_note}',
                    img_url=card_img,
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
            "Photo",
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

        if show_career_baseline:
            display_cols_tab1.extend(["Career_GI_90", "Career_Pts_90", "Career_Mins"])

        col_config = {
            "Photo": st.column_config.ImageColumn("", width="small", help="Player Photo"),
            "Player": st.column_config.TextColumn("Player"),
            "Team": st.column_config.TextColumn("Club"),
            "Pos": st.column_config.TextColumn("Pos"),
            "Price": st.column_config.NumberColumn("Price", format="£%.1f"),
            "Minutes": st.column_config.NumberColumn("Mins", format="%d"),
            "Total_Points": st.column_config.NumberColumn("Pts", format="%d"),
            "Goals": st.column_config.NumberColumn("Gls", format="%d"),
            "Assists": st.column_config.NumberColumn("Ast", format="%d"),
            "Clean_Sheets": st.column_config.NumberColumn("CS", format="%d"),
            "Saves": st.column_config.NumberColumn("Saves", format="%d"),
            "xG": st.column_config.NumberColumn("xG", format="%.2f"),
            "xA": st.column_config.NumberColumn("xA", format="%.2f"),
            "xGI": st.column_config.NumberColumn("xGI", format="%.2f"),
            "xG_Delta": st.column_config.NumberColumn("ΔxG", format="%.2f"),
            "xGI_per_90": st.column_config.NumberColumn("xGI/90", format="%.2f"),
            "Career_GI_90": st.column_config.NumberColumn("Career GI/90", format="%.2f", help="Career actual (Goals+Assists)/90 from previous Premier League seasons"),
            "Career_Pts_90": st.column_config.NumberColumn("Career Pts/90", format="%.2f", help="Career FPL Points per 90 from previous seasons"),
            "Career_Mins": st.column_config.NumberColumn("Career Mins", format="%d", help="Total minutes played in previous Premier League seasons"),
        }

        display_df = df_xgi[display_cols_tab1].head(35)
        # Exact row-height sizing (35px per row + 35px header + 3px border padding)
        table_height = (len(display_df) + 1) * 35 + 3

        st.dataframe(
            display_df.style.map(highlight_xg_delta, subset=["xG_Delta"]),
            hide_index=True,
            width="stretch",
            height=table_height,
            column_config=col_config,
        )