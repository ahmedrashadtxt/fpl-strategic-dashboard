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


def render_defensive_stats_tab(conn, current_gw):
    col_def_hdr, col_def_pop = st.columns([6, 1])
    with col_def_hdr:
        section_header(
            "Defensive Resilience & Contributions",
            "Evaluate clean sheet sustainability, defensive workrate, and shot-stopping",
        )
    with col_def_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Defensive Metrics & Regression Guide**
                
                * **DC (Defensive Contributions):** Cumulative actions tracked for the +2 DC match bonus point threshold.
                    * **DEF Threshold:** 10 actions in a single match (`CBI + T`).
                    * **MID & FWD Threshold:** 12 actions in a single match (`CBI + T + R`).
                * **CBI:** Combined Clearances, Blocks, and Interceptions.
                * **T:** Tackles won.
                * **R:** Ball Recoveries.
                * **DC / 90:** Defensive contribution rate per 90 minutes.
                * **xGC (Expected Goals Conceded):** Cumulative chance quality allowed while on pitch.
                * **ΔxGC (Goals Conceded Delta):** Calculated as `Actual Goals Conceded - xGC`.
                    * 🟢 **Buy Signal (ΔxGC ≥ +0.5):** Unlucky defense. Conceding fluke goals despite low opponent chance creation. Clean sheet regression expected upward.
                    * 🔴 **Sell Signal (ΔxGC ≤ -0.5):** Overperforming defense. Riding poor opponent finishing; clean sheet regression risk.
                """
            )

    col_search, col1, col2, col3 = st.columns([1.5, 1, 1, 1])
    with col_search:
        search_query = st.text_input(
            "🔍 Search Player / Club",
            placeholder="e.g. Egan, Gabriel, Raya, HUL...",
            key="def_search",
        )
    with col1:
        min_minutes = st.slider(
            "Minimum Minutes Played", 0, 900, 45, step=45, key="def_min_mins"
        )
    with col2:
        position_filter = st.selectbox(
            "Filter Position", ["DEF", "GKP", "MID", "All"], index=0, key="def_pos"
        )
    with col3:
        sort_by = st.selectbox(
            "Rank By",
            [
                "DC per 90",
                "Total DC",
                "CBI (Clearances, Blocks, Int)",
                "Tackles (T)",
                "Recoveries (R)",
                "Goals Conceded Above Expected (Unlucky)",
                "Expected Goals Conceded (Lowest xGC)",
                "Clean Sheets",
                "Total Points",
                "Goalkeeper Saves",
            ],
            key="def_sort",
        )

    col_toggle1, col_toggle2 = st.columns([1, 1])
    with col_toggle1:
        only_my_squad_tab = st.toggle(
            "🎯 Only My Squad Players", key="def_only_squad"
        )
    with col_toggle2:
        show_career_baseline = st.toggle(
            "🏛️ Show Career Baselines (Past Seasons)", value=False, key="def_show_career"
        )

    pos_clause = (
        f"AND p.element_type = {pos_map[position_filter]}"
        if position_filter != "All"
        else ""
    )

    # Database column introspection
    player_cols = [
        c.lower()
        for c in pd.read_sql("PRAGMA table_info(players)", conn)["name"].tolist()
    ]

    # 1. Tackles (T)
    if "tackles" in player_cols:
        t_expr = "p.tackles AS T"
    elif "t" in player_cols:
        t_expr = "p.t AS T"
    else:
        t_expr = "0 AS T"

    # 2. Clearances, Blocks & Interceptions (CBI)
    if "clearances_blocks_interceptions" in player_cols:
        cbi_expr = "p.clearances_blocks_interceptions AS CBI"
    elif "cbi" in player_cols:
        cbi_expr = "p.cbi AS CBI"
    elif all(c in player_cols for c in ["clearances", "blocks", "interceptions"]):
        cbi_expr = "(p.clearances + p.blocks + p.interceptions) AS CBI"
    else:
        cbi_expr = "0 AS CBI"

    # 3. Recoveries (R)
    if "recoveries" in player_cols:
        r_expr = "p.recoveries AS R"
    elif "r" in player_cols:
        r_expr = "p.r AS R"
    else:
        r_expr = "0 AS R"

    # 4. Defensive Contribution (DC)
    if "defensive_contribution" in player_cols:
        dc_expr = "p.defensive_contribution AS DC"
    elif "defensive_contributions" in player_cols:
        dc_expr = "p.defensive_contributions AS DC"
    elif "dc" in player_cols:
        dc_expr = "p.dc AS DC"
    else:
        # Fallback to official FPL formula: DEF = CBI + T; MID/FWD = CBI + T + R
        cbi_col = (
            "p.clearances_blocks_interceptions"
            if "clearances_blocks_interceptions" in player_cols
            else ("p.cbi" if "cbi" in player_cols else "0")
        )
        t_col = "p.tackles" if "tackles" in player_cols else "0"
        r_col = "p.recoveries" if "recoveries" in player_cols else "0"
        dc_expr = f"""
            CASE 
                WHEN p.element_type = 2 THEN (COALESCE({cbi_col}, 0) + COALESCE({t_col}, 0))
                ELSE (COALESCE({cbi_col}, 0) + COALESCE({t_col}, 0) + COALESCE({r_col}, 0))
            END AS DC
        """

    # Expected Goals Conceded (xGC)
    xgc_expr = "p.expected_goals_conceded AS xGC" if "expected_goals_conceded" in player_cols else "0.0 AS xGC"
    xgc_90_expr = (
        "p.expected_goals_conceded_per_90 AS xGC_per_90"
        if "expected_goals_conceded_per_90" in player_cols
        else "0.0 AS xGC_per_90"
    )

    # Historical career baseline table check
    table_check = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='player_past_seasons'",
        conn,
    )
    has_history = not table_check.empty

    past_cols = (
        [c.lower() for c in pd.read_sql("PRAGMA table_info(player_past_seasons)", conn)["name"].tolist()]
        if has_history
        else []
    )

    gc_hist_col = "SUM(goals_conceded)" if "goals_conceded" in past_cols else "0"
    cs_hist_col = "SUM(clean_sheets)" if "clean_sheets" in past_cols else "0"

    hist_join = f"""
        LEFT JOIN (
            SELECT 
                element_id,
                ROUND(({gc_hist_col} * 1.0 / NULLIF(SUM(minutes), 0)) * 90.0, 2) AS Career_GC_90,
                ROUND(({cs_hist_col} * 1.0 / NULLIF(SUM(minutes), 0)) * 90.0, 2) AS Career_CS_90,
                ROUND((SUM(total_points) * 1.0 / NULLIF(SUM(minutes), 0)) * 90.0, 2) AS Career_Pts_90,
                SUM(minutes) AS Career_Mins
            FROM player_past_seasons
            GROUP BY element_id
        ) hist ON p.id = hist.element_id
    """ if has_history else ""

    hist_select = """
        hist.Career_GC_90,
        hist.Career_CS_90,
        hist.Career_Pts_90,
        hist.Career_Mins,
    """ if has_history else """
        NULL AS Career_GC_90,
        NULL AS Career_CS_90,
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
        p.clean_sheets AS Clean_Sheets,
        p.goals_conceded AS Goals_Conceded,
        p.saves AS Saves,
        {xgc_expr},
        {xgc_90_expr},
        {t_expr},
        {cbi_expr},
        {r_expr},
        {dc_expr},
        {hist_select}
        p.now_cost / 10.0 AS price_val
    FROM players p
    INNER JOIN teams t ON p.team = t.id
    {hist_join}
    WHERE p.minutes >= {min_minutes} {pos_clause}
    """
    df_def = pd.read_sql(query, conn)

    numeric_cols = [
        "Price",
        "Minutes",
        "Total_Points",
        "Clean_Sheets",
        "Goals_Conceded",
        "Saves",
        "xGC",
        "xGC_per_90",
        "T",
        "CBI",
        "R",
        "DC",
        "Career_GC_90",
        "Career_CS_90",
        "Career_Pts_90",
        "Career_Mins",
    ]
    for col_name in numeric_cols:
        if col_name in df_def.columns:
            df_def[col_name] = pd.to_numeric(df_def[col_name], errors="coerce").fillna(0)

    # Calculate xGC Delta & per-90 metrics
    df_def["xGC_Delta"] = (df_def["Goals_Conceded"] - df_def["xGC"]).round(2)
    df_def["DC_per_90"] = (
        (df_def["DC"] / df_def["Minutes"].replace(0, pd.NA)) * 90.0
    ).fillna(0.0).round(2)
    df_def["Saves_per_90"] = (
        (df_def["Saves"] / df_def["Minutes"].replace(0, pd.NA)) * 90.0
    ).fillna(0.0).round(2)

    if (df_def["xGC_per_90"] == 0).all():
        df_def["xGC_per_90"] = (
            (df_def["xGC"] / df_def["Minutes"].replace(0, pd.NA)) * 90.0
        ).fillna(0.0).round(2)

    df_def = df_def.dropna(subset=["Player"])
    df_def = df_def[df_def["Player"].astype(str).str.strip() != ""]

    df_def["Photo"] = [
        get_player_img_url(ph, c) for ph, c in zip(df_def["photo"], df_def["code"])
    ]

    active_manager_id = st.session_state.get("manager_id", "").strip()
    if only_my_squad_tab:
        if not active_manager_id:
            st.info(
                "💡 Enter your FPL Team ID in the sidebar or Squad Analyzer tab to filter by your squad."
            )
            squad_ids = []
        else:
            squad_ids = get_manager_squad_ids(active_manager_id, current_gw)
        df_def = df_def[df_def["element_id"].isin(squad_ids)]

    if search_query.strip():
        q1 = search_query.strip()
        df_def = df_def[
            df_def["Player"].str.contains(q1, case=False, na=False)
            | df_def["Full_Name"].str.contains(q1, case=False, na=False)
            | df_def["Team"].str.contains(q1, case=False, na=False)
            | df_def["Club_Name"].str.contains(q1, case=False, na=False)
        ]

    sort_map = {
        "DC per 90": ("DC_per_90", False),
        "Total DC": ("DC", False),
        "CBI (Clearances, Blocks, Int)": ("CBI", False),
        "Tackles (T)": ("T", False),
        "Recoveries (R)": ("R", False),
        "Goals Conceded Above Expected (Unlucky)": ("xGC_Delta", False),
        "Expected Goals Conceded (Lowest xGC)": ("xGC", True),
        "Clean Sheets": ("Clean_Sheets", False),
        "Total Points": ("Total_Points", False),
        "Goalkeeper Saves": ("Saves", False),
    }
    sort_col, sort_asc = sort_map[sort_by]
    df_def = df_def.sort_values(by=sort_col, ascending=sort_asc)

    if df_def.empty:
        st.info(f"No players found matching '{search_query}'. Try adjusting your filters.")
    else:
        top_cards = df_def.head(min(4, len(df_def)))
        card_cols = st.columns(len(top_cards))
        for i, (_, row) in enumerate(top_cards.iterrows()):
            delta = float(row["xGC_Delta"])
            if delta >= 0.5:
                signal_tag = ("Buy Signal", "green")
            elif delta <= -0.5:
                signal_tag = ("Sell Signal", "red")
            else:
                signal_tag = ("Neutral", "gray")

            with card_cols[i]:
                hist_note = (
                    f" · <span>Career CS/90</span> {fmt_num(row['Career_CS_90'])}"
                    if pd.notna(row.get("Career_CS_90")) and show_career_baseline
                    else ""
                )
                card_img = get_player_img_url(row.get("photo"), row.get("code"))
                render_list_card(
                    f"{row['Player']} ({row['Team']})",
                    [(row["Pos"], "blue"), signal_tag],
                    f'<span>Price</span> £{fmt_num(row["Price"], ".1f")} · <span>xGC</span>'
                    f' {fmt_num(row["xGC"])} · <span>DC/90</span>'
                    f' {fmt_num(row["DC_per_90"])} · <span>Pts</span>'
                    f' {int(float(row["Total_Points"]))} · <span>ΔxGC</span>'
                    f' {fmt_num(delta, "+.2f")}{hist_note}',
                    img_url=card_img,
                )

        def highlight_xgc_delta(val):
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

        display_cols_def = [
            "Photo",
            "Player",
            "Team",
            "Pos",
            "Price",
            "Minutes",
            "Total_Points",
            "Clean_Sheets",
            "Goals_Conceded",
            "xGC",
            "xGC_Delta",
            "xGC_per_90",
            "DC",
            "DC_per_90",
            "CBI",
            "R",
            "T",
            "Saves",
            "Saves_per_90",
        ]

        if show_career_baseline:
            display_cols_def.extend(["Career_GC_90", "Career_CS_90", "Career_Pts_90", "Career_Mins"])

        col_config = {
            "Photo": st.column_config.ImageColumn("", width="small", help="Player Photo"),
            "Player": st.column_config.TextColumn("Player"),
            "Team": st.column_config.TextColumn("Club"),
            "Pos": st.column_config.TextColumn("Pos"),
            "Price": st.column_config.NumberColumn("Price", format="£%.1f"),
            "Minutes": st.column_config.NumberColumn("Mins", format="%d"),
            "Total_Points": st.column_config.NumberColumn("Pts", format="%d"),
            "Clean_Sheets": st.column_config.NumberColumn("CS", format="%d", help="Clean Sheets kept"),
            "Goals_Conceded": st.column_config.NumberColumn("GC", format="%d", help="Actual Goals Conceded"),
            "xGC": st.column_config.NumberColumn("xGC", format="%.2f", help="Expected Goals Conceded based on chance quality"),
            "xGC_Delta": st.column_config.NumberColumn("ΔxGC", format="%.2f", help="Actual GC - xGC. Positive = Unlucky (conceding fluke goals). Negative = Lucky / regression risk."),
            "xGC_per_90": st.column_config.NumberColumn("xGC/90", format="%.2f"),
            "DC": st.column_config.NumberColumn("DC", format="%d", help="Total Defensive Contributions (CBI + T for DEF; CBI + T + R for MID/FWD)"),
            "DC_per_90": st.column_config.NumberColumn("DC/90", format="%.2f", help="Defensive actions per 90 mins (target threshold: 10 for DEF, 12 for MID)"),
            "CBI": st.column_config.NumberColumn("CBI", format="%d", help="Clearances, Blocks, and Interceptions"),
            "R": st.column_config.NumberColumn("R", format="%d", help="Ball Recoveries"),
            "T": st.column_config.NumberColumn("T", format="%d", help="Tackles"),
            "Saves": st.column_config.NumberColumn("Saves", format="%d", help="Goalkeeper Saves"),
            "Saves_per_90": st.column_config.NumberColumn("Saves/90", format="%.2f"),
            "Career_GC_90": st.column_config.NumberColumn("Career GC/90", format="%.2f", help="Historical Goals Conceded per 90 mins"),
            "Career_CS_90": st.column_config.NumberColumn("Career CS/90", format="%.2f", help="Historical Clean Sheets per 90 mins"),
            "Career_Pts_90": st.column_config.NumberColumn("Career Pts/90", format="%.2f", help="Historical FPL Points per 90 mins"),
            "Career_Mins": st.column_config.NumberColumn("Career Mins", format="%d", help="Historical minutes played in Premier League"),
        }

        display_df = df_def[display_cols_def].head(35)
        table_height = (len(display_df) + 1) * 35 + 3

        st.dataframe(
            display_df.style.map(highlight_xgc_delta, subset=["xGC_Delta"]),
            hide_index=True,
            width="stretch",
            height=table_height,
            column_config=col_config,
        )