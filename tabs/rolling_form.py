from data import get_manager_squad_ids
import pandas as pd
import plotly.express as px
import streamlit as st
from theme import SILHOUETTE_BASE64, fmt_num, render_list_card, render_sortable_table, section_header

pos_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}


def get_player_img_url(photo, code=None):
    photo_str = str(photo) if pd.notna(photo) else ""
    if not photo_str or "Photo-Missing" in photo_str or photo_str == "None":
        if pd.notna(code) and str(code).strip():
            return f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{int(code)}.png"
        return SILHOUETTE_BASE64

    base_name = photo_str.replace(".jpg", "").replace(".png", "")
    if not base_name.startswith("p"):
        base_name = f"p{base_name}"
    return f"https://resources.premierleague.com/premierleague/photos/players/110x140/{base_name}.png"


def render_rolling_form_tab(conn, current_gw, teams_fdr_map):
    col_t2_hdr, col_t2_pop = st.columns([6, 1])
    with col_t2_hdr:
        section_header(
            "Rolling Form & Trends",
            "Analyze form trajectory vs upcoming fixture schedule",
        )
    with col_t2_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Form vs. Fixtures Scatter Matrix**
                
                * **Y-Axis (Rolling Sum xGI):** Total attacking threat accumulated across the selected match window.
                * **X-Axis (Upcoming 5-GW FDR):** Total fixture difficulty rating over the next 5 games (lower score = easier schedule).
                * **Min Matches Filter:** Filters out rotational cameos so you only evaluate regular starters.
                """
            )

    table_exists = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='player_match_history'",
        conn,
    )

    if table_exists.empty:
        st.warning("⚠️ Match history table `player_match_history` was not found in `fpl.db`.")
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
            p.code,
            p.photo,
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
        code,
        photo,
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
        df_rolling = df_rolling.dropna(subset=["Player"])
        df_rolling = df_rolling[df_rolling["Player"].astype(str).str.strip() != ""]

        df_rolling["Upcoming_FDR"] = (
            df_rolling["Team_ID"].map(teams_fdr_map).fillna(15).astype(int)
        )

        active_manager_id = st.session_state.get("manager_id", "").strip()
        if only_my_squad:
            if not active_manager_id:
                st.info("💡 Enter your FPL Team ID in the top bar to filter by your squad.")
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
        return

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
        card_img = get_player_img_url(row.get("photo"), row.get("code"))
        with cols_r[i]:
            render_list_card(
                f"{row['Player']} ({row['Team']})",
                [(row["Pos"], "blue"), (f"L{window_size} Form", "green")],
                f'<span>Price</span> £{fmt_num(row["Price"], ".1f")} · <span>xGI</span>'
                f' {fmt_num(row["Rolling_Sum_xGI"])} · <span>xGI/90</span>'
                f' {fmt_num(row["Rolling_xGI_per_90"])} · <span>Next 5 FDR</span>'
                f' {int(row["Upcoming_FDR"])} · <span>Avg Pts</span>'
                f' {fmt_num(row["Rolling_Avg_Pts"], ".1f")}',
                img_url=card_img,
            )

    is_dark = st.session_state.get("theme_mode", "dark") == "dark"

    theme_styles = f"""
    <style>
    .unified-table-wrapper {{
        width: 100%;
        overflow-x: auto;
        border: 1px solid {"#222222" if is_dark else "#e2e8f0"};
        border-radius: 10px;
        background: {"#141414" if is_dark else "#ffffff"};
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-top: 1rem;
    }}
    .unified-table {{
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: {"#ffffff" if is_dark else "#0f172a"};
    }}
    .unified-table th {{
        background: {"#18181b" if is_dark else "#f8fafc"};
        color: {"#94a3b8" if is_dark else "#64748b"};
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
        padding: 0.7rem 0.75rem;
        border-bottom: 1px solid {"#27272a" if is_dark else "#e2e8f0"};
        text-align: center;
        white-space: nowrap;
    }}
    .unified-table td {{
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid {"#1f1f23" if is_dark else "#f1f5f9"};
        vertical-align: middle;
        text-align: center;
        white-space: nowrap;
    }}
    .unified-table tr:last-child td {{
        border-bottom: none;
    }}
    .unified-table tr:hover td {{
        background: {"rgba(255, 255, 255, 0.02)" if is_dark else "rgba(0, 0, 0, 0.015)"};
    }}
    .player-unified-cell {{
        display: flex;
        align-items: center;
        gap: 10px;
        white-space: nowrap;
    }}
    .player-avatar-circle {{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        object-fit: cover;
        object-position: top center;
        background-color: {"#1e293b" if is_dark else "#e2e8f0"};
        border: 1px solid {"#2a2a2a" if is_dark else "#cbd5e1"};
        flex-shrink: 0;
    }}
    .player-name-text {{
        font-weight: 600;
        color: {"#ffffff" if is_dark else "#0f172a"};
    }}
    .pos-pill {{
        display: inline-block;
        padding: 0.12rem 0.45rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
    }}
    .pos-GKP {{ background: rgba(245, 158, 11, 0.18); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .pos-DEF {{ background: rgba(59, 130, 246, 0.18); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .pos-MID {{ background: rgba(16, 185, 129, 0.18); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .pos-FWD {{ background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}

    .fdr-pill {{
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 4px;
        font-weight: 800;
        font-size: 0.82rem;
    }}
    .fdr-green {{ background: rgba(34, 197, 94, 0.2); color: {"#4ade80" if is_dark else "#15803d"}; }}
    .fdr-yellow {{ background: rgba(234, 179, 8, 0.2); color: {"#facc15" if is_dark else "#a16207"}; }}
    .fdr-red {{ background: rgba(239, 68, 68, 0.2); color: {"#f87171" if is_dark else "#b91c1c"}; }}
    </style>
    """

    display_df = df_rolling.head(35)
    html_out = [theme_styles, '<div class="unified-table-wrapper"><table class="unified-table"><thead><tr>']
    html_out.append('<th style="text-align: left; padding-left: 1rem;">Player</th>')
    html_out.append('<th>Club</th><th>Pos</th><th>Price</th><th>GW</th>')
    html_out.append(f'<th>xGI (L{window_size})</th><th>xGI/90 (L{window_size})</th><th>Pts (L{window_size})</th>')
    html_out.append(f'<th>Next 5 FDR</th><th>Mins (L{window_size})</th><th>Apps</th>')
    html_out.append('</tr></thead><tbody>')

    for _, row in display_df.iterrows():
        p_img = get_player_img_url(row.get("photo"), row.get("code"))
        fdr_val = int(row["Upcoming_FDR"])
        fdr_cls = "fdr-green" if fdr_val <= 11 else ("fdr-yellow" if fdr_val <= 14 else "fdr-red")

        html_out.append("<tr>")
        html_out.append(
            f'<td style="text-align: left; padding-left: 1rem;">'
            f'<div class="player-unified-cell">'
            f'<img src="{p_img}" class="player-avatar-circle" onerror="this.src=\'{SILHOUETTE_BASE64}\'">'
            f'<span class="player-name-text">{row["Player"]}</span>'
            f'</div></td>'
        )
        html_out.append(f'<td>{row["Team"]}</td>')
        html_out.append(f'<td><span class="pos-pill pos-{row["Pos"]}">{row["Pos"]}</span></td>')
        html_out.append(f'<td>£{row["Price"]:.1f}</td>')
        html_out.append(f'<td>{int(row["Latest_GW"])}</td>')
        html_out.append(f'<td style="font-weight: 700;">{row["Rolling_Sum_xGI"]:.2f}</td>')
        html_out.append(f'<td>{row["Rolling_xGI_per_90"]:.2f}</td>')
        html_out.append(f'<td style="font-weight: 700;">{row["Rolling_Avg_Pts"]:.2f}</td>')
        html_out.append(f'<td><span class="fdr-pill {fdr_cls}">{fdr_val}</span></td>')
        html_out.append(f'<td>{row["Rolling_Avg_Mins"]:.1f}</td>')
        html_out.append(f'<td>{int(row["Rolling_Matches_Played"])}</td>')
        html_out.append("</tr>")

    html_out.append("</tbody></table></div>")

    # Spans full length on main page without internal scrollbars
    full_table_height = (len(display_df) * 45) + 60
    render_sortable_table("".join(html_out), is_dark=is_dark, height=full_table_height)