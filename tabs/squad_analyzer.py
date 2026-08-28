import pandas as pd
import requests
import streamlit as st
from data import (
    calculate_projected_points,
    get_fixture_for_team,
    get_historical_player_baselines,
    get_motw_data,
    solve_optimal_xi,
)
from theme import fmt_num, render_list_card, section_header


# ── CACHED API CALLS (5-minute TTL to prevent redundant HTTP requests) ─────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_manager_entry(manager_id: str):
    """Fetches manager overview details with caching."""
    try:
        url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
        res = requests.get(url, timeout=10)
        return res.json() if res.status_code == 200 else {}
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_manager_picks(manager_id: str, eval_gw: int, current_gw: int):
    """Fetches manager squad picks with fallback logic and caching."""
    try:
        picks_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{eval_gw}/picks/"
        picks_res = requests.get(picks_url, timeout=10)

        if picks_res.status_code != 200:
            fallback_gw = current_gw if current_gw >= 1 else 1
            picks_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{fallback_gw}/picks/"
            picks_res = requests.get(picks_url, timeout=10)
            if picks_res.status_code != 200 and fallback_gw > 1:
                picks_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{fallback_gw - 1}/picks/"
                picks_res = requests.get(picks_url, timeout=10)

        return picks_res.json() if picks_res.status_code == 200 else {}
    except Exception:
        return {}


@st.cache_data(ttl=120, show_spinner=False)
def fetch_live_gameweek_points(eval_gw: int):
    """Fetches live gameweek point scores with 2-minute caching."""
    try:
        live_url = f"https://fantasy.premierleague.com/api/event/{eval_gw}/live/"
        res = requests.get(live_url, timeout=10)
        if res.status_code == 200:
            return {
                item["id"]: item["stats"]["total_points"]
                for item in res.json().get("elements", [])
            }
        return {}
    except Exception:
        return {}


# ── SQUAD OPTIMIZATION SOLVER ────────────────────────────────────────────────
def solve_budget_dream_15(league_eval_df: pd.DataFrame, max_budget: float = 100.0) -> pd.DataFrame:
    """
    Selects the optimal 15-player squad (2 GKP, 5 DEF, 5 MID, 3 FWD)
    maximizing projected points subject to budget and club constraints.
    """
    df = league_eval_df.sort_values(by="Proj_Pts", ascending=False).copy()
    
    pos_targets = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
    selected_ids = []
    team_counts = {}

    for pos, count in pos_targets.items():
        cheapest_pos = df[df["Pos"] == pos].sort_values(by=["Cost", "Proj_Pts"], ascending=[True, False])
        for _, row in cheapest_pos.iterrows():
            t_id = row["team_id"]
            if len([p for p in selected_ids if df.loc[df["id"] == p, "Pos"].values[0] == pos]) < count:
                if team_counts.get(t_id, 0) < 3:
                    selected_ids.append(row["id"])
                    team_counts[t_id] = team_counts.get(t_id, 0) + 1

    current_squad = df[df["id"].isin(selected_ids)].copy()

    improved = True
    while improved:
        improved = False
        best_gain = 0
        best_swap = None

        current_cost = current_squad["Cost"].sum()
        remaining_bank = max_budget - current_cost

        for _, cur_p in current_squad.iterrows():
            pos = cur_p["Pos"]
            cur_team = cur_p["team_id"]
            
            candidates = df[
                (df["Pos"] == pos) & 
                (~df["id"].isin(current_squad["id"])) & 
                (df["Proj_Pts"] > cur_p["Proj_Pts"])
            ]

            for _, cand_p in candidates.iterrows():
                cost_diff = cand_p["Cost"] - cur_p["Cost"]
                cand_team = cand_p["team_id"]

                if cost_diff > remaining_bank:
                    continue

                team_count = len(current_squad[current_squad["team_id"] == cand_team])
                if cand_team != cur_team and team_count >= 3:
                    continue

                pts_gain = cand_p["Proj_Pts"] - cur_p["Proj_Pts"]
                if pts_gain > best_gain:
                    best_gain = pts_gain
                    best_swap = (cur_p["id"], cand_p["id"])

        if best_swap:
            drop_id, add_id = best_swap
            current_squad = current_squad[current_squad["id"] != drop_id]
            current_squad = pd.concat([current_squad, df[df["id"] == add_id]])
            improved = True

    return current_squad


@st.cache_data(ttl=600, show_spinner=False)
def get_cached_league_dream_15(_conn, current_gw: int, selected_eval_gw: int, total_budget: float):
    """Caches the full league player projection evaluation and linear optimization solver."""
    adv_fixtures_query = """
    SELECT
        f.event AS GW,
        f.team_h AS team_h_id,
        f.team_a AS team_a_id,
        th.short_name AS Home_Team,
        ta.short_name AS Away_Team,
        f.team_h_difficulty AS Home_Diff,
        f.team_a_difficulty AS Away_Diff
    FROM fixtures f
    INNER JOIN teams th ON f.team_h = th.id
    INNER JOIN teams ta ON f.team_a = ta.id
    WHERE f.event >= ? AND f.event <= ?
    """
    adv_fix_df = pd.read_sql(adv_fixtures_query, _conn, params=[current_gw, current_gw + 4])

    all_players_query = """
    SELECT
        p.id,
        p.web_name AS Player,
        p.team AS team_id,
        t.short_name AS Team,
        CASE p.element_type
            WHEN 1 THEN 'GKP'
            WHEN 2 THEN 'DEF'
            WHEN 3 THEN 'MID'
            WHEN 4 THEN 'FWD'
        END AS Pos,
        pos.singular_name AS Position,
        p.now_cost / 10.0 AS Cost,
        p.minutes AS minutes,
        p.total_points AS Season_Points,
        p.expected_goals,
        p.expected_assists,
        p.form AS Form,
        p.points_per_game AS PPG,
        p.expected_goal_involvements_per_90 AS xGI_per_90,
        p.status AS Status,
        p.chance_of_playing_next_round AS Chance
    FROM players p
    INNER JOIN teams t ON p.team = t.id
    INNER JOIN positions pos ON p.element_type = pos.id
    WHERE (p.status = 'a' OR p.chance_of_playing_next_round >= 75)
    """
    all_pl_df = pd.read_sql(all_players_query, _conn)
    hist_baselines_df = get_historical_player_baselines(_conn)

    league_eval_list = []
    for _, p_row in all_pl_df.iterrows():
        fix_data = get_fixture_for_team(adv_fix_df, p_row["team_id"], selected_eval_gw)
        proj_pts = calculate_projected_points(p_row, fix_data, current_gw, hist_baselines_df)
        p_eval = dict(p_row)
        p_eval.update({
            "Opponent": fix_data["opponent"],
            "FDR": fix_data["fdr"],
            "Proj_Pts": proj_pts,
        })
        league_eval_list.append(p_eval)

    league_eval_df = pd.DataFrame(league_eval_list)
    league_dream_15 = solve_budget_dream_15(league_eval_df, max_budget=total_budget)
    return solve_optimal_xi(league_dream_15)


def render_squad_analyzer_tab(conn, events_df, current_gw):
    col_t4_hdr, col_t4_pop = st.columns([6, 1])
    with col_t4_hdr:
        section_header(
            "Manager Squad Analyzer & Best 11",
            "Audit live lineup & solve optimal starting XI for future gameweeks",
        )
    with col_t4_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Manager Squad Sync & Optimizer Guide**
                
                * **FPL Team ID:** Enter your manager ID from your FPL team URL (`fantasy.premierleague.com/entry/XXXXXX/event/...`).
                * **Squad Value & Bank:** Live tracking of squad valuation and in-the-bank reserve.
                * **Side-by-Side Comparison:** Compares your squad against:
                    * 👑 **Manager of the Week** on finished gameweeks.
                    * 🌟 **Budget Dream 11** (optimal £100m wildcard team, max 3/club) on upcoming gameweeks.
                * **Optimal Best 11:** Mathematically solves the highest expected scoring formation.
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
            mgr_data = fetch_manager_entry(mgr_to_use)
            if not mgr_data:
                st.error("Could not load team. Verify your FPL ID.")
                return

            total_points = mgr_data.get("summary_overall_points", 0)
            overall_rank = mgr_data.get("summary_overall_rank", 0)

            finished_gws = (
                [int(r["id"]) for _, r in events_df[events_df["finished"] == 1].iterrows()]
                if "finished" in events_df.columns
                else []
            )
            if not finished_gws and current_gw > 1:
                finished_gws = list(range(1, current_gw))

            upcoming_gws = list(range(current_gw, min(39, current_gw + 4)))
            all_gw_options = sorted(list(set(finished_gws + upcoming_gws)))

            col_sel_gw, col_toggle = st.columns([4, 2])
            with col_sel_gw:
                def format_gw_label(g):
                    if g < current_gw:
                        return f"Gameweek {g} (Finished)"
                    elif g == current_gw:
                        return f"Gameweek {g} (Upcoming)"
                    else:
                        return f"Gameweek {g}"

                selected_eval_gw = st.radio(
                    "📅 **Select Gameweek to Inspect or Optimize:**",
                    options=all_gw_options,
                    index=all_gw_options.index(current_gw) if current_gw in all_gw_options else 0,
                    format_func=format_gw_label,
                    horizontal=True,
                    key="tab4_selected_gw",
                )

            with col_toggle:
                st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
                enable_comparison = st.toggle(
                    "⚖️ **Side-by-Side Comparison**",
                    value=False,
                    key="tab4_compare_toggle",
                )

            is_finished_gw = selected_eval_gw < current_gw

            picks_data = fetch_manager_picks(mgr_to_use, selected_eval_gw, current_gw)
            entry_history = picks_data.get("entry_history", {})
            transfers_cost = entry_history.get("event_transfers_cost", 0)

            bank_balance = entry_history.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0
            total_team_value = entry_history.get("value", mgr_data.get("last_deadline_value", 1000)) / 10.0
            squad_value = total_team_value - bank_balance

            live_points_map = fetch_live_gameweek_points(selected_eval_gw)

            picks_list = picks_data.get("picks", [])
            pick_ids = [p["element"] for p in picks_list]
            if not pick_ids:
                st.warning("No squad picks found for the selected gameweek.")
                return

            placeholders = ",".join(["?"] * len(pick_ids))

            squad_query = f"""
            SELECT
                p.id,
                p.web_name AS Player,
                p.team AS team_id,
                t.short_name AS Team,
                CASE p.element_type
                    WHEN 1 THEN 'GKP'
                    WHEN 2 THEN 'DEF'
                    WHEN 3 THEN 'MID'
                    WHEN 4 THEN 'FWD'
                END AS Pos,
                pos.singular_name AS Position,
                p.now_cost / 10.0 AS Cost,
                p.minutes AS minutes,
                p.total_points AS Season_Points,
                p.expected_goals,
                p.expected_assists,
                p.form AS Form,
                p.points_per_game AS PPG,
                p.expected_goal_involvements_per_90 AS xGI_per_90,
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
            user_gw_pts = int(starting_xi_pts) - transfers_cost

            # ── Top Metrics Grid ──────────────────────────────────────────────
            col1, col2, col3 = st.columns(3)
            col1.metric("Manager", mgr_data.get("name", "My Team"))
            col2.metric("Overall Rank", f"{overall_rank:,}")
            col3.metric("Total Points", f"{total_points:,}")
            
            st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
            
            col4, col5, col6 = st.columns(3)
            col4.metric(
                f"GW {selected_eval_gw} Pts",
                user_gw_pts if is_finished_gw else f"{user_gw_pts} (Live)",
                delta=f"-{transfers_cost} hit" if transfers_cost > 0 else None,
                delta_color="inverse",
            )
            col5.metric("Squad Value", f"£{squad_value:.1f}m")
            col6.metric("In The Bank", f"£{bank_balance:.1f}m")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── SCENARIO A: FINISHED GAMEWEEK ─────────────────────────────────
            if is_finished_gw:
                motw_data = get_motw_data(selected_eval_gw)
                motw_pts = motw_data["total_score"] if motw_data else 0
                motw_name = motw_data["manager_name"] if motw_data else "Manager of the Week"
                pts_diff = user_gw_pts - motw_pts

                st.markdown(
                    f"""
                    <div style="background-color: #151d24; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 1.2rem; margin: 0.5rem 0 1.5rem 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 1.1rem; font-weight: 700; color: #f8fafc;">Gameweek {selected_eval_gw} Performance Review</span><br>
                                <span style="font-size: 0.85rem; color: #94a3b8;">Your Score: <strong>{user_gw_pts} pts</strong> · Top Score in FPL: <strong>{motw_pts} pts</strong> ({motw_name})</span>
                            </div>
                            <span style="font-size: 1.3rem; font-weight: 800; color: {'#22c55e' if pts_diff >= 0 else '#ef4444'};">{pts_diff:+d} pts vs Top</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                user_starters = squad_df[squad_df["order"] <= 11].sort_values("order")
                user_bench = squad_df[squad_df["order"] > 11].sort_values("order")

                if enable_comparison and motw_data:
                    motw_pick_ids = [p["element"] for p in motw_data["picks"]]
                    motw_placeholders = ",".join(["?"] * len(motw_pick_ids))
                    motw_df = pd.read_sql(
                        squad_query.replace(placeholders, motw_placeholders),
                        conn,
                        params=motw_pick_ids,
                    )

                    motw_meta = {p["element"]: p for p in motw_data["picks"]}
                    motw_df["order"] = motw_df["id"].map(lambda x: motw_meta[x]["position"])
                    motw_df["Multiplier"] = motw_df["id"].map(lambda x: motw_meta[x]["multiplier"])
                    motw_df["is_cap"] = motw_df["id"].map(lambda x: motw_meta[x]["is_captain"])
                    motw_df["is_vc"] = motw_df["id"].map(lambda x: motw_meta[x]["is_vice_captain"])
                    motw_df["Raw_GW_Pts"] = motw_df["id"].map(lambda x: live_points_map.get(x, 0))
                    motw_df["GW_Points"] = motw_df["Raw_GW_Pts"] * motw_df["Multiplier"]

                    motw_starters = motw_df[motw_df["order"] <= 11].sort_values("order")
                    motw_bench = motw_df[motw_df["order"] > 11].sort_values("order")

                    col_left, col_right = st.columns(2)
                    with col_left:
                        st.markdown(f"#### 👤 Your Squad · GW{selected_eval_gw} ({user_gw_pts} pts)")
                        for _, row in user_starters.iterrows():
                            tags = [(row["Pos"], "blue")]
                            mult_label = " (2x)" if row["Multiplier"] == 2 else (" (3x)" if row["Multiplier"] == 3 else "")
                            if row["Multiplier"] >= 2:
                                tags.append((f"Captain{mult_label}", "green"))
                            elif row["is_vc"]:
                                tags.append(("Vice Captain", "yellow"))
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                tags,
                                f'<span>GW Pts</span> <strong>{int(row["GW_Points"])}</strong>{mult_label} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                        st.markdown("##### 🪑 Bench")
                        for _, row in user_bench.iterrows():
                            sub_idx = int(row["order"]) - 11
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                [(f"Sub {sub_idx} ({row['Pos']})", "gray")],
                                f'<span>GW Pts</span> {int(row["Raw_GW_Pts"])} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                    with col_right:
                        st.markdown(f"#### 👑 {motw_name} ({motw_pts} pts)")
                        for _, row in motw_starters.iterrows():
                            tags = [(row["Pos"], "blue")]
                            mult_label = " (2x)" if row["Multiplier"] == 2 else (" (3x)" if row["Multiplier"] == 3 else "")
                            if row["Multiplier"] >= 2:
                                tags.append((f"Captain{mult_label}", "green"))
                            elif row["is_vc"]:
                                tags.append(("Vice Captain", "yellow"))
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                tags,
                                f'<span>GW Pts</span> <strong>{int(row["GW_Points"])}</strong>{mult_label} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                        st.markdown("##### 🪑 Bench")
                        for _, row in motw_bench.iterrows():
                            sub_idx = int(row["order"]) - 11
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                [(f"Sub {sub_idx} ({row['Pos']})", "gray")],
                                f'<span>GW Pts</span> {int(row["Raw_GW_Pts"])} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )
                else:
                    col_squad, col_news = st.columns([7, 3])
                    with col_squad:
                        st.markdown(f"#### 👤 Your Squad · GW{selected_eval_gw} ({user_gw_pts} pts)")
                        for _, row in user_starters.iterrows():
                            tags = [(row["Pos"], "blue")]
                            mult_label = " (2x)" if row["Multiplier"] == 2 else (" (3x)" if row["Multiplier"] == 3 else "")
                            if row["Multiplier"] >= 2:
                                tags.append((f"Captain{mult_label}", "green"))
                            elif row["is_vc"]:
                                tags.append(("Vice Captain", "yellow"))
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                tags,
                                f'<span>GW Pts</span> <strong>{int(row["GW_Points"])}</strong>{mult_label} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                        st.markdown("##### 🪑 Bench")
                        for _, row in user_bench.iterrows():
                            sub_idx = int(row["order"]) - 11
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                [(f"Sub {sub_idx} ({row['Pos']})", "gray")],
                                f'<span>GW Pts</span> {int(row["Raw_GW_Pts"])} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                    with col_news:
                        st.markdown('<div class="section-card"><h3>Top Performer</h3></div>', unsafe_allow_html=True)
                        if motw_data:
                            st.info(f"🏆 **{motw_name}** scored **{motw_pts} points** in GW{selected_eval_gw}!")
                        else:
                            st.info("Top performer data not available yet.")

            # ── SCENARIO B: PROJECTED GAMEWEEKS ───────────────────────────────
            else:
                adv_fixtures_query = """
                SELECT
                    f.event AS GW,
                    f.team_h AS team_h_id,
                    f.team_a AS team_a_id,
                    th.short_name AS Home_Team,
                    ta.short_name AS Away_Team,
                    f.team_h_difficulty AS Home_Diff,
                    f.team_a_difficulty AS Away_Diff
                FROM fixtures f
                INNER JOIN teams th ON f.team_h = th.id
                INNER JOIN teams ta ON f.team_a = ta.id
                WHERE f.event >= ? AND f.event <= ?
                """
                adv_fix_df = pd.read_sql(adv_fixtures_query, conn, params=[current_gw, current_gw + 4])
                hist_baselines_df = get_historical_player_baselines(conn)

                squad_eval_list = []
                for _, p_row in squad_df.iterrows():
                    fix_data = get_fixture_for_team(adv_fix_df, p_row["team_id"], selected_eval_gw)
                    proj_pts = calculate_projected_points(p_row, fix_data, current_gw, hist_baselines_df)
                    p_eval = dict(p_row)
                    p_eval.update({
                        "Opponent": fix_data["opponent"],
                        "FDR": fix_data["fdr"],
                        "Proj_Pts": proj_pts,
                    })
                    squad_eval_list.append(p_eval)

                squad_eval_df = pd.DataFrame(squad_eval_list)
                optimal_xi, optimal_bench, optimal_formation = solve_optimal_xi(squad_eval_df)

                user_proj_xi_pts = optimal_xi["Proj_Pts"].sum()
                avg_xi_fdr = float(optimal_xi["FDR"].mean())
                fdr_ease_pct = max(0.0, min(100.0, ((5.0 - avg_xi_fdr) / 3.0) * 100.0))
                pts_index_pct = max(0.0, min(100.0, (user_proj_xi_pts / 52.0) * 100.0))
                squad_rating = round((0.50 * fdr_ease_pct) + (0.50 * pts_index_pct), 1)

                # Fetch cached Dream 11 calculation (inherits multi-season shrinkage)
                dream_xi, dream_bench, dream_formation = get_cached_league_dream_15(
                    conn, current_gw, selected_eval_gw, total_team_value
                )
                dream_proj_xi_pts = dream_xi["Proj_Pts"].sum()

                st.markdown(
                    f"""
                    <div style="background-color: #151d24; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 1.2rem; margin: 0.5rem 0 1rem 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                            <span style="font-size: 1.1rem; font-weight: 700; color: #f8fafc;">GW{selected_eval_gw} Squad Rating</span>
                            <span style="font-size: 1.4rem; font-weight: 800; color: #22c55e;">{squad_rating}%</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                col_met1.metric("Optimal Formation", optimal_formation)
                col_met2.metric(
                    "Projected XI Points",
                    f"{user_proj_xi_pts:.1f} pts",
                    delta=f"{user_proj_xi_pts - dream_proj_xi_pts:+.1f} vs £{total_team_value:.1f}m Best",
                )
                col_met3.metric("Avg Starting FDR", f"{avg_xi_fdr:.2f}")
                col_met4.metric(
                    "Squad Health",
                    f"{len(squad_df[squad_df['Status'] == 'a'])}/15 Fit",
                    delta=(
                        f"{len(squad_df[squad_df['Status'] != 'a'])} Flagged"
                        if len(squad_df[squad_df['Status'] != 'a']) > 0
                        else "Full Squad Available"
                    ),
                    delta_color="normal" if len(squad_df[squad_df['Status'] != 'a']) == 0 else "inverse",
                )

                if enable_comparison:
                    col_left, col_right = st.columns(2)
                    with col_left:
                        st.markdown(
                            f"#### 👤 Your Optimal XI · GW{selected_eval_gw} "
                            f"({optimal_formation} · {user_proj_xi_pts:.1f} xP)"
                        )
                        for idx, (_, row) in enumerate(optimal_xi.iterrows()):
                            tags = [(row["Pos"], "blue"), (f"FDR {row['FDR']}", "gray")]
                            mult_label = ""
                            if idx == 0:
                                tags.append(("Captain (2x)", "green"))
                                mult_label = " (2x)"
                            elif idx == 1:
                                tags.append(("Vice Captain", "yellow"))

                            if row["Status"] in ("i", "u"):
                                tags.append(("Out", "red"))
                            elif row["Status"] == "d":
                                tags.append(("Doubtful", "yellow"))

                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                tags,
                                f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> <strong>{fmt_num(row["Proj_Pts"], ".1f")}</strong>{mult_label} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                        st.markdown("##### 🪑 Projected Bench")
                        for idx, (_, row) in enumerate(optimal_bench.iterrows()):
                            sub_label = "Sub GKP" if row["Pos"] == "GKP" else f"Sub {idx}"
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                [(sub_label, "gray"), (f"FDR {row['FDR']}", "gray")],
                                f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> {fmt_num(row["Proj_Pts"], ".1f")} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                    with col_right:
                        st.markdown(
                            f"#### 🌟 Budget Dream 11 · GW{selected_eval_gw} "
                            f"({dream_formation} · {dream_proj_xi_pts:.1f} xP)"
                        )
                        for idx, (_, row) in enumerate(dream_xi.iterrows()):
                            tags = [(row["Pos"], "blue"), (f"FDR {row['FDR']}", "gray")]
                            mult_label = ""
                            if idx == 0:
                                tags.append(("Captain (2x)", "green"))
                                mult_label = " (2x)"
                            elif idx == 1:
                                tags.append(("Vice Captain", "yellow"))

                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                tags,
                                f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> <strong>{fmt_num(row["Proj_Pts"], ".1f")}</strong>{mult_label} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                        st.markdown("##### 🪑 Dream Bench")
                        for idx, (_, row) in enumerate(dream_bench.iterrows()):
                            sub_label = "Sub GKP" if row["Pos"] == "GKP" else f"Sub {idx}"
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                [(sub_label, "gray"), (f"FDR {row['FDR']}", "gray")],
                                f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> {fmt_num(row["Proj_Pts"], ".1f")} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )
                else:
                    col_squad, col_news = st.columns([7, 3])
                    with col_squad:
                        st.markdown(
                            f"#### 👤 Your Optimal XI · GW{selected_eval_gw} "
                            f"({optimal_formation} · {user_proj_xi_pts:.1f} xP)"
                        )
                        for idx, (_, row) in enumerate(optimal_xi.iterrows()):
                            tags = [(row["Pos"], "blue"), (f"FDR {row['FDR']}", "gray")]
                            mult_label = ""
                            if idx == 0:
                                tags.append(("Captain (2x)", "green"))
                                mult_label = " (2x)"
                            elif idx == 1:
                                tags.append(("Vice Captain", "yellow"))

                            if row["Status"] in ("i", "u"):
                                tags.append(("Out", "red"))
                            elif row["Status"] == "d":
                                tags.append(("Doubtful", "yellow"))

                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                tags,
                                f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> <strong>{fmt_num(row["Proj_Pts"], ".1f")}</strong>{mult_label} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                        st.markdown("##### 🪑 Projected Bench")
                        for idx, (_, row) in enumerate(optimal_bench.iterrows()):
                            sub_label = "Sub GKP" if row["Pos"] == "GKP" else f"Sub {idx}"
                            render_list_card(
                                f"{row['Player']} · {row['Team']}",
                                [(sub_label, "gray"), (f"FDR {row['FDR']}", "gray")],
                                f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> {fmt_num(row["Proj_Pts"], ".1f")} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                            )

                    with col_news:
                        st.markdown('<div class="section-card"><h3>Squad News</h3></div>', unsafe_allow_html=True)
                        flagged_players = squad_df[
                            (squad_df["Status"] != "a") & 
                            (squad_df["News"].notna()) & 
                            (squad_df["News"] != "") & 
                            (squad_df["News"] != "None")
                        ]
                        
                        if flagged_players.empty:
                            st.success("All squad players available.")
                        else:
                            for _, row in flagged_players.iterrows():
                                chance_val = row["Chance"]
                                chance_str = f" ({int(float(chance_val))}% chance)" if pd.notna(chance_val) and str(chance_val).strip() not in ("", "None") else ""
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