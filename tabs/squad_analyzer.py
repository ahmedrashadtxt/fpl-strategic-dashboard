import html
import pandas as pd
import requests
import streamlit as st
from data import (
    calculate_projected_points,
    get_fixture_for_team,
    get_historical_player_baselines,
    solve_optimal_xi,
)
from theme import fmt_num, render_list_card, section_header

SILHOUETTE_BASE64 = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmci"
    "IHZpZXdCb3g9IjAgMCA0NCA0NCIgZmlsbD0ibm9uZSI+PHJlY3Qgd2lkdGg9IjQ0IiBoZWlnaHQ9"
    "IjQ0IiByeD0iMjIiIGZpbGw9IiMxZTI5M2IiLz48Y2lyY2xlIGN4PSIyMiIgY3k9IjE2IiByPSI3"
    "LjUiIGZpbGw9IiM2NDc0OGIiLz48cGF0aCBkPSJNOSAzOWMwLTcuMTggNS44Mi0xMyAxMy0xM3Mx"
    "MyA1LjgyIDEzIDEzIiBmaWxsPSIjNjQ3NDhiIi8+PC9zdmc+"
)


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


@st.cache_data(ttl=300, show_spinner=False)
def fetch_manager_entry(manager_id: str):
    try:
        url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
        res = requests.get(url, timeout=10)
        return res.json() if res.status_code == 200 else {}
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_manager_picks(manager_id: str, eval_gw: int, current_gw: int):
    try:
        picks_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{eval_gw}/picks/"
        picks_res = requests.get(picks_url, timeout=10)
        if picks_res.status_code == 200:
            return picks_res.json()
        for g in range(current_gw, 0, -1):
            url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{g}/picks/"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res.json()
        return {}
    except Exception:
        return {}


@st.cache_data(ttl=120, show_spinner=False)
def fetch_live_gameweek_points(eval_gw: int):
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


@st.cache_data(ttl=300, show_spinner=False)
def fetch_dream_team_data(target_gw: int):
    try:
        dt_res = requests.get(
            f"https://fantasy.premierleague.com/api/dream-team/{target_gw}/",
            timeout=10,
        ).json()
        dt_elements = dt_res.get("team", [])
        picks_list = [
            {
                "element": el["element"],
                "position": i + 1,
                "multiplier": 2 if i == 0 else 1,
                "is_captain": i == 0,
                "is_vice_captain": i == 1,
            }
            for i, el in enumerate(dt_elements)
        ]
        top_pts = sum(el.get("points", 0) for el in dt_elements)
        return {
            "type": "dream_team",
            "manager_name": "Super Team",
            "player_name": "Official Dream Team",
            "total_score": top_pts,
            "picks": picks_list,
        }
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_motw_manager_data(target_gw: int):
    motw_id = None
    motw_score = None
    try:
        bs_res = requests.get(
            "https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10
        )
        if bs_res.status_code == 200:
            bs_events = bs_res.json().get("events", [])
            for ev in bs_events:
                if ev.get("id") == target_gw:
                    motw_id = ev.get("highest_scoring_entry")
                    motw_score = ev.get("highest_score")
                    break
    except Exception:
        pass

    if motw_id:
        try:
            mgr_info = requests.get(
                f"https://fantasy.premierleague.com/api/entry/{motw_id}/", timeout=10
            ).json()
            mgr_name = mgr_info.get("name", "Top Manager")
            player_name = (
                f"{mgr_info.get('player_first_name', '')}"
                f" {mgr_info.get('player_last_name', '')}".strip()
            )
            picks_res = requests.get(
                f"https://fantasy.premierleague.com/api/entry/{motw_id}/event/{target_gw}/picks/",
                timeout=10,
            ).json()
            picks_list = picks_res.get("picks", [])
            return {
                "type": "motw",
                "manager_name": mgr_name,
                "player_name": player_name,
                "total_score": (
                    motw_score
                    or picks_res.get("entry_history", {}).get("points", 0)
                ),
                "picks": picks_list,
            }
        except Exception:
            pass
    return None


def quick_sync_live_prices(conn):
    try:
        res = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
        if res.status_code == 200:
            elements = res.json().get("elements", [])
            cursor = conn.cursor()
            cursor.executemany(
                """
                UPDATE players 
                SET now_cost = ?, status = ?, news = ?, chance_of_playing_next_round = ?,
                    total_points = ?, form = ?, points_per_game = ?
                WHERE id = ?
                """,
                [
                    (
                        el["now_cost"],
                        el.get("status"),
                        el.get("news"),
                        el.get("chance_of_playing_next_round"),
                        el.get("total_points"),
                        el.get("form"),
                        el.get("points_per_game"),
                        el["id"],
                    )
                    for el in elements
                ],
            )
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Failed to refresh player prices: {e}")
    return False


def solve_budget_dream_15(league_eval_df: pd.DataFrame, max_budget: float = 100.0) -> pd.DataFrame:
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


def solve_unconstrained_super_15(league_eval_df: pd.DataFrame) -> pd.DataFrame:
    df = league_eval_df.sort_values(by="Proj_Pts", ascending=False).copy()
    pos_targets = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
    selected_ids = []
    team_counts = {}

    for pos, target_count in pos_targets.items():
        pos_df = df[df["Pos"] == pos]
        for _, row in pos_df.iterrows():
            t_id = row["team_id"]
            if len([p for p in selected_ids if df.loc[df["id"] == p, "Pos"].values[0] == pos]) < target_count:
                if team_counts.get(t_id, 0) < 3:
                    selected_ids.append(row["id"])
                    team_counts[t_id] = team_counts.get(t_id, 0) + 1

    return df[df["id"].isin(selected_ids)].copy()


@st.cache_data(ttl=600, show_spinner=False)
def get_cached_league_dream_15(_conn, current_gw: int, selected_eval_gw: int, total_budget: float):
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
        p.code,
        p.photo,
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


@st.cache_data(ttl=600, show_spinner=False)
def get_cached_league_super_15(_conn, current_gw: int, selected_eval_gw: int):
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
        p.code,
        p.photo,
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
    super_15 = solve_unconstrained_super_15(league_eval_df)
    return solve_optimal_xi(super_15)


def render_pitch_component(starters_df: pd.DataFrame, bench_df: pd.DataFrame, is_live: bool = False):
    pos_rows = ["GKP", "DEF", "MID", "FWD"]
    pitch_rows_html = ""

    for pos in pos_rows:
        row_players = starters_df[starters_df["Pos"] == pos]
        players_html = ""
        for _, p in row_players.iterrows():
            mult = p.get("Multiplier", 1)
            is_c = p.get("is_cap", False) or mult >= 2
            is_v = p.get("is_vc", False)

            cap_badge = ""
            if mult == 3:
                cap_badge = '<div class="pitch-cap-badge tc">3x</div>'
            elif is_c:
                cap_badge = '<div class="pitch-cap-badge c">C</div>'
            elif is_v:
                cap_badge = '<div class="pitch-cap-badge vc">V</div>'

            img_url = get_player_img_url(p.get("photo"), p.get("code"))
            player_name = p.get("Player", "")

            if is_live:
                pts = int(p.get("GW_Points", 0))
                mult_txt = f" ({mult}x)" if mult > 1 else ""
                pts_sub = f"{pts} pts{mult_txt}"
                sub_color = "#4ade80" if pts >= 6 else "#f8fafc"
                stat_pill_content = f'<span style="color: {sub_color};">{pts_sub}</span>'
            else:
                proj = p.get("Proj_Pts", 0.0)
                cost = p.get("Cost", 0.0)
                cost_str = f"£{fmt_num(cost, '.1f')}m" if cost else ""
                stat_pill_content = (
                    f'<span style="color: #60a5fa; font-weight: 700;">{fmt_num(proj, ".1f")} xP</span>'
                    f'<span style="color: #94a3b8; font-size: 0.62rem; display: block; line-height: 1.1; margin-top: 1px;">{cost_str}</span>'
                )

            clean_url = html.escape(str(img_url))
            avatar_style = f"background-image: url('{clean_url}'), url('{SILHOUETTE_BASE64}');"

            players_html += (
                f'<div class="pitch-player-node">'
                f'<div class="pitch-avatar-wrap">'
                f'<div class="pitch-player-avatar" style="{avatar_style}"></div>'
                f'{cap_badge}'
                f'</div>'
                f'<div class="pitch-name-pill">{html.escape(player_name)}</div>'
                f'<div class="pitch-stat-pill">{stat_pill_content}</div>'
                f'</div>'
            )
        pitch_rows_html += f'<div class="pitch-formation-row">{players_html}</div>'

    dugout_html = ""
    if bench_df is not None and not bench_df.empty:
        bench_html = ""
        for idx, (_, b) in enumerate(bench_df.iterrows()):
            img_url = get_player_img_url(b.get("photo"), b.get("code"))
            player_name = b.get("Player", "")
            pos = b.get("Pos", "")

            if is_live:
                pts = int(b.get("Raw_GW_Pts", 0))
                b_stat_content = f"<span>{pts} pts</span>"
            else:
                proj = b.get("Proj_Pts", 0.0)
                b_cost = b.get("Cost", 0.0)
                b_cost_str = f"£{fmt_num(b_cost, '.1f')}m" if b_cost else ""
                b_stat_content = (
                    f'<span style="color: #60a5fa; font-weight: 700;">{fmt_num(proj, ".1f")} xP</span>'
                    f'<span style="color: #94a3b8; font-size: 0.62rem; display: block; line-height: 1.1; margin-top: 1px;">{b_cost_str}</span>'
                )

            sub_label = "Sub GKP" if pos == "GKP" else f"Sub {idx}"
            clean_url = html.escape(str(img_url))
            bench_avatar_style = f"background-image: url('{clean_url}'), url('{SILHOUETTE_BASE64}');"

            bench_html += (
                f'<div class="pitch-player-node bench-node">'
                f'<div class="bench-order-tag">{sub_label}</div>'
                f'<div class="pitch-avatar-wrap">'
                f'<div class="pitch-player-avatar bench-avatar" style="{bench_avatar_style}"></div>'
                f'</div>'
                f'<div class="pitch-name-pill">{html.escape(player_name)}</div>'
                f'<div class="pitch-stat-pill">{b_stat_content}</div>'
                f'</div>'
            )
        dugout_html = (
            f'<div class="pitch-dugout">'
            f'<div class="dugout-title">BENCH DUGOUT</div>'
            f'<div class="dugout-row">{bench_html}</div>'
            f'</div>'
        )

    full_pitch_html = (
        f'<style>'
        f'.pitch-board-wrap {{ width: 100%; max-width: 100%; margin: 0 auto 1rem auto; }}'
        f'.tactical-pitch {{'
        f'  background: radial-gradient(circle at 50% 50%, #154323 0%, #0c2714 100%);'
        f'  border: 2px solid rgba(255, 255, 255, 0.2);'
        f'  border-radius: 12px;'
        f'  position: relative;'
        f'  overflow: hidden;'
        f'  padding: 18px 4px;'
        f'  display: flex;'
        f'  flex-direction: column;'
        f'  justify-content: space-around;'
        f'  min-height: 520px;'
        f'  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);'
        f'}}'
        f'.pitch-line {{ position: absolute; pointer-events: none; }}'
        f'.center-line {{ top: 50%; left: 0; right: 0; height: 1.5px; background: rgba(255, 255, 255, 0.12); }}'
        f'.center-circle {{ top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90px; height: 90px; border-radius: 50%; border: 1.5px solid rgba(255, 255, 255, 0.12); }}'
        f'.penalty-box-top {{ top: 0; left: 50%; transform: translateX(-50%); width: 170px; height: 55px; border: 1.5px solid rgba(255, 255, 255, 0.12); border-top: none; }}'
        f'.penalty-arc-top {{ top: 55px; left: 50%; transform: translateX(-50%); width: 60px; height: 25px; border-bottom-left-radius: 30px; border-bottom-right-radius: 30px; border: 1.5px solid rgba(255, 255, 255, 0.12); border-top: none; }}'
        f'.penalty-box-bottom {{ bottom: 0; left: 50%; transform: translateX(-50%); width: 170px; height: 55px; border: 1.5px solid rgba(255, 255, 255, 0.12); border-bottom: none; }}'
        f'.penalty-arc-bottom {{ bottom: 55px; left: 50%; transform: translateX(-50%); width: 60px; height: 25px; border-top-left-radius: 30px; border-top-right-radius: 30px; border: 1.5px solid rgba(255, 255, 255, 0.12); border-bottom: none; }}'
        f'.pitch-formation-row {{ display: flex; justify-content: space-around; align-items: center; z-index: 2; width: 100%; margin: 6px 0; }}'
        f'.pitch-player-node {{ display: flex; flex-direction: column; align-items: center; flex: 1; max-width: 68px; min-width: 0; text-align: center; }}'
        f'.pitch-avatar-wrap {{ position: relative; width: 44px; height: 44px; margin-bottom: 4px; }}'
        f'.pitch-player-avatar {{'
        f'  width: 44px !important;'
        f'  height: 44px !important;'
        f'  min-width: 44px !important;'
        f'  min-height: 44px !important;'
        f'  border-radius: 50% !important;'
        f'  background-size: cover, cover !important;'
        f'  background-position: top center, center !important;'
        f'  background-repeat: no-repeat, no-repeat !important;'
        f'  border: 2px solid #ffffff !important;'
        f'  background-color: #1e293b !important;'
        f'  box-shadow: 0 2px 6px rgba(0,0,0,0.35) !important;'
        f'}}'
        f'.bench-avatar {{ border-color: #94a3b8 !important; opacity: 0.9; }}'
        f'.pitch-cap-badge {{ position: absolute; top: -4px; right: -4px; width: 18px; height: 18px; border-radius: 50%; font-size: 0.65rem; font-weight: 800; display: flex; align-items: center; justify-content: center; border: 1.5px solid #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.4); }}'
        f'.pitch-cap-badge.c {{ background: #22c55e; color: #ffffff; }}'
        f'.pitch-cap-badge.tc {{ background: #eab308; color: #000000; }}'
        f'.pitch-cap-badge.vc {{ background: #3b82f6; color: #ffffff; }}'
        f'.pitch-name-pill {{ background: #0f172a; color: #f8fafc; font-size: 0.70rem; font-weight: 700; padding: 2px 4px; border-radius: 4px; width: 94%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border: 1px solid rgba(255, 255, 255, 0.12); box-shadow: 0 1px 3px rgba(0,0,0,0.25); }}'
        f'.pitch-stat-pill {{ background: rgba(15, 23, 42, 0.85); font-size: 0.68rem; font-weight: 700; padding: 1px 4px; border-radius: 3px; margin-top: 2px; border: 1px solid rgba(255, 255, 255, 0.08); }}'
        f'.pitch-dugout {{ background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; margin-top: 8px; padding: 8px 6px 10px 6px; }}'
        f'.dugout-title {{ font-size: 0.7rem; font-weight: 800; color: #94a3b8; letter-spacing: 0.05em; text-align: center; margin-bottom: 6px; }}'
        f'.dugout-row {{ display: flex; justify-content: space-around; align-items: center; }}'
        f'.bench-node {{ flex: 1; max-width: 64px; }}'
        f'.bench-order-tag {{ font-size: 0.65rem; color: #94a3b8; font-weight: 600; margin-bottom: 2px; }}'
        f'</style>'
        f'<div class="pitch-board-wrap">'
        f'<div class="tactical-pitch">'
        f'<div class="pitch-line penalty-box-top"></div>'
        f'<div class="pitch-line penalty-arc-top"></div>'
        f'<div class="pitch-line center-circle"></div>'
        f'<div class="pitch-line center-line"></div>'
        f'<div class="pitch-line penalty-box-bottom"></div>'
        f'<div class="pitch-line penalty-arc-bottom"></div>'
        f'{pitch_rows_html}'
        f'</div>'
        f'{dugout_html}'
        f'</div>'
    )
    st.markdown(full_pitch_html, unsafe_allow_html=True)


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
                
                * **FPL Team ID:** Enter your manager ID from your FPL team URL.
                * **Pitch vs. List View:** Toggle between a visual soccer pitch formation and detailed list cards.
                * **Comparison & Super Team:**
                    * **Finished GWs:** Compare against actual **Manager of the Week** or the theoretical **Super Team**.
                    * **Live GWs:** Compare against the **Live Top Manager** or the **Live Super Team**.
                    * **Upcoming GWs:** Compare against the **Budget Dream 11** (£100m budget) or the unconstrained **Super Team** (No budget cap).
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

            finished_gw_ids = (
                [int(r["id"]) for _, r in events_df[events_df["finished"] == 1].iterrows()]
                if "finished" in events_df.columns
                else []
            )
            next_gw_row = events_df[events_df["is_next"] == 1]
            next_gw_id = int(next_gw_row["id"].values[0]) if not next_gw_row.empty else current_gw

            ongoing_gw_ids = [
                int(r["id"]) for _, r in events_df.iterrows()
                if int(r["id"]) not in finished_gw_ids and int(r["id"]) < next_gw_id
            ]
            ongoing_gw = ongoing_gw_ids[0] if ongoing_gw_ids else None
            last_finished_gw = max(finished_gw_ids) if finished_gw_ids else None

            all_gw_options = []
            if last_finished_gw is not None:
                all_gw_options.append(last_finished_gw)
            if ongoing_gw is not None:
                all_gw_options.append(ongoing_gw)

            upcoming_gws = [g for g in range(next_gw_id, min(39, next_gw_id + 3))]
            all_gw_options.extend(upcoming_gws)
            all_gw_options = sorted(list(dict.fromkeys(all_gw_options)))

            def format_gw_label(g):
                if g in finished_gw_ids:
                    return f"Gameweek {g} (Finished)"
                elif g == ongoing_gw:
                    return f"Gameweek {g} (Live)"
                elif g == next_gw_id:
                    return f"Gameweek {g} (Upcoming)"
                else:
                    return f"Gameweek {g}"

            default_gw = ongoing_gw if ongoing_gw else next_gw_id
            default_idx = all_gw_options.index(default_gw) if default_gw in all_gw_options else 0

            # ── ROW 1: Gameweek Selector + Styled Refresh Button ──────────────
            col_gw_sel, col_gw_ref = st.columns([5.0, 1.2])
            with col_gw_sel:
                selected_eval_gw = st.radio(
                    "📅 **Select Gameweek:**",
                    options=all_gw_options,
                    index=default_idx,
                    format_func=format_gw_label,
                    horizontal=True,
                    key="tab4_selected_gw",
                )
            with col_gw_ref:
                st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
                if st.button("🔄 Refresh", width="stretch", help="Sync latest prices, live points, and clear manager cache"):
                    fetch_manager_entry.clear()
                    fetch_manager_picks.clear()
                    fetch_live_gameweek_points.clear()
                    fetch_motw_manager_data.clear()
                    fetch_dream_team_data.clear()
                    with st.spinner("Updating prices..."):
                        quick_sync_live_prices(conn)
                    st.toast("Dashboard and prices refreshed!", icon="⚡")
                    st.rerun()

            # ── ROW 2: View Toggles ───────────────────────────────────────────
            col_tgl1, col_tgl2, col_tgl3, col_tgl_fill = st.columns([1.5, 2.2, 2.0, 1.5])
            with col_tgl1:
                pitch_view = st.toggle(
                    "🏟️ **Pitch View**",
                    value=True,
                    key="tab4_pitch_toggle",
                )

            with col_tgl2:
                enable_comparison = st.toggle(
                    "⚖️ **Side-by-Side Comparison**",
                    value=False,
                    key="tab4_compare_toggle",
                )

            with col_tgl3:
                super_team_mode = False
                if enable_comparison:
                    super_team_mode = st.toggle(
                        "🌟 **Super Team**",
                        value=False,
                        key="tab4_super_team_toggle",
                    )

            is_finished_gw = selected_eval_gw in finished_gw_ids
            is_ongoing_gw = (selected_eval_gw == ongoing_gw)
            is_live_or_finished = is_finished_gw or is_ongoing_gw

            picks_data = fetch_manager_picks(mgr_to_use, selected_eval_gw, next_gw_id)
            entry_history = picks_data.get("entry_history", {})
            transfers_cost = entry_history.get("event_transfers_cost", 0)
            bank_balance = entry_history.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0

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
                p.code,
                p.photo,
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

            squad_value = float(squad_df["Cost"].sum()) if not squad_df.empty else 100.0
            total_team_value = squad_value + bank_balance

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

            col1, col2, col3 = st.columns(3)
            col1.metric("Manager", mgr_data.get("name", "My Team"))
            col2.metric("Overall Rank", f"{overall_rank:,}")
            col3.metric("Total Points", f"{total_points:,}")

            st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

            col4, col5, col6 = st.columns(3)
            col4.metric(
                f"GW {selected_eval_gw} Pts",
                f"{user_gw_pts} (Live)" if is_ongoing_gw else f"{user_gw_pts} pts",
                delta=f"-{transfers_cost} hit" if transfers_cost > 0 else None,
                delta_color="inverse",
            )
            col5.metric("Squad Value", f"£{squad_value:.1f}m")
            col6.metric("In The Bank", f"£{bank_balance:.1f}m")

            st.markdown("<br>", unsafe_allow_html=True)

            # Theme detection for banners
            is_dark = st.session_state.get("theme_mode", "dark") == "dark"
            banner_bg = "#151d24" if is_dark else "#ffffff"
            banner_border = "rgba(255, 255, 255, 0.08)" if is_dark else "#e2e8f0"
            banner_title_col = "#f8fafc" if is_dark else "#0f172a"
            banner_sub_col = "#94a3b8" if is_dark else "#64748b"

            # ── SCENARIO A: FINISHED OR ONGOING (LIVE TRACKING) ───────────────
            if is_live_or_finished:
                motw_manager_data = fetch_motw_manager_data(selected_eval_gw)
                dream_team_data = fetch_dream_team_data(selected_eval_gw)

                if super_team_mode:
                    comp_data = dream_team_data or motw_manager_data
                    comp_title = "Super Team"
                else:
                    comp_data = motw_manager_data or dream_team_data
                    raw_title = comp_data.get("manager_name", "Manager of the Week") if comp_data else "Top Performer"
                    comp_title = (raw_title[:20] + "..") if len(raw_title) > 22 else raw_title

                comp_pts = comp_data["total_score"] if comp_data else 0
                pts_diff = user_gw_pts - comp_pts

                banner_title = f"Gameweek {selected_eval_gw} Live Match Center" if is_ongoing_gw else f"Gameweek {selected_eval_gw} Performance Review"
                score_subtext = f"Your Score: <strong>{user_gw_pts} pts (Live)</strong>" if is_ongoing_gw else f"Your Score: <strong>{user_gw_pts} pts</strong>"
                top_subtext = f"Comparing against <strong>{comp_title}</strong>: <strong>{comp_pts} pts</strong>"

                st.markdown(
                    f"""
                    <div style="background-color: {banner_bg}; border: 1px solid {banner_border}; border-radius: 10px; padding: 1.2rem; margin: 0.5rem 0 1.5rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 1.1rem; font-weight: 700; color: {banner_title_col};">{banner_title}</span><br>
                                <span style="font-size: 0.85rem; color: {banner_sub_col};">{score_subtext} · {top_subtext}</span>
                            </div>
                            <span style="font-size: 1.3rem; font-weight: 800; color: {'#22c55e' if pts_diff >= 0 else '#ef4444'};">{pts_diff:+d} pts vs Comp</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                user_starters = squad_df[squad_df["order"] <= 11].sort_values("order")
                user_bench = squad_df[squad_df["order"] > 11].sort_values("order")

                squad_heading = f"#### 👤 Your Squad · GW{selected_eval_gw} ({user_gw_pts} pts Live)" if is_ongoing_gw else f"#### 👤 Your Squad · GW{selected_eval_gw} ({user_gw_pts} pts)"
                badge_prefix = "🌟" if super_team_mode else "👑"
                top_performer_heading = (
                    f"#### {badge_prefix} {comp_title} ({comp_pts} pts Live)"
                    if is_ongoing_gw
                    else f"#### {badge_prefix} {comp_title} ({comp_pts} pts)"
                )

                if enable_comparison and comp_data:
                    comp_pick_ids = [p["element"] for p in comp_data["picks"]]
                    comp_placeholders = ",".join(["?"] * len(comp_pick_ids))
                    comp_df = pd.read_sql(
                        squad_query.replace(placeholders, comp_placeholders),
                        conn,
                        params=comp_pick_ids,
                    )

                    comp_meta = {p["element"]: p for p in comp_data["picks"]}
                    comp_df["order"] = comp_df["id"].map(lambda x: comp_meta[x]["position"])
                    comp_df["Multiplier"] = comp_df["id"].map(lambda x: comp_meta[x]["multiplier"])
                    comp_df["is_cap"] = comp_df["id"].map(lambda x: comp_meta[x]["is_captain"])
                    comp_df["is_vc"] = comp_df["id"].map(lambda x: comp_meta[x]["is_vice_captain"])
                    comp_df["Raw_GW_Pts"] = comp_df["id"].map(lambda x: live_points_map.get(x, 0))
                    comp_df["GW_Points"] = comp_df["Raw_GW_Pts"] * comp_df["Multiplier"]

                    comp_starters = comp_df[comp_df["order"] <= 11].sort_values("order")
                    comp_bench = comp_df[comp_df["order"] > 11].sort_values("order")

                    col_left, col_right = st.columns(2)
                    with col_left:
                        st.markdown(squad_heading)
                        if pitch_view:
                            render_pitch_component(user_starters, user_bench, is_live=True)
                        else:
                            for _, row in user_starters.iterrows():
                                tags = [(row["Pos"], "blue")]
                                mult_label = " (2x)" if row["Multiplier"] == 2 else (" (3x)" if row["Multiplier"] == 3 else "")
                                if row["Multiplier"] >= 2:
                                    tags.append((f"Captain{mult_label}", "green"))
                                elif row["is_vc"]:
                                    tags.append(("Vice Captain", "yellow"))
                                card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                render_list_card(
                                    f"{row['Player']} · {row['Team']}",
                                    tags,
                                    f'<span>GW Pts</span> <strong>{int(row["GW_Points"])}</strong>{mult_label} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                    img_url=card_img,
                                )
                            if not user_bench.empty:
                                st.markdown("##### 🪑 Bench")
                                for _, row in user_bench.iterrows():
                                    sub_idx = int(row["order"]) - 11
                                    card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                    render_list_card(
                                        f"{row['Player']} · {row['Team']}",
                                        [(f"Sub {sub_idx} ({row['Pos']})", "gray")],
                                        f'<span>GW Pts</span> {int(row["Raw_GW_Pts"])} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                        img_url=card_img,
                                    )

                    with col_right:
                        st.markdown(top_performer_heading)
                        if pitch_view:
                            render_pitch_component(comp_starters, comp_bench, is_live=True)
                        else:
                            for _, row in comp_starters.iterrows():
                                tags = [(row["Pos"], "blue")]
                                mult_label = " (2x)" if row["Multiplier"] == 2 else (" (3x)" if row["Multiplier"] == 3 else "")
                                if row["Multiplier"] >= 2:
                                    tags.append((f"Captain{mult_label}", "green"))
                                elif row["is_vc"]:
                                    tags.append(("Vice Captain", "yellow"))
                                card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                render_list_card(
                                    f"{row['Player']} · {row['Team']}",
                                    tags,
                                    f'<span>GW Pts</span> <strong>{int(row["GW_Points"])}</strong>{mult_label} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                    img_url=card_img,
                                )
                            if not comp_bench.empty:
                                st.markdown("##### 🪑 Bench")
                                for _, row in comp_bench.iterrows():
                                    sub_idx = int(row["order"]) - 11
                                    card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                    render_list_card(
                                        f"{row['Player']} · {row['Team']}",
                                        [(f"Sub {sub_idx} ({row['Pos']})", "gray")],
                                        f'<span>GW Pts</span> {int(row["Raw_GW_Pts"])} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                        img_url=card_img,
                                    )
                else:
                    col_squad, col_news = st.columns([7, 3])
                    with col_squad:
                        st.markdown(squad_heading)
                        if pitch_view:
                            render_pitch_component(user_starters, user_bench, is_live=True)
                        else:
                            for _, row in user_starters.iterrows():
                                tags = [(row["Pos"], "blue")]
                                mult_label = " (2x)" if row["Multiplier"] == 2 else (" (3x)" if row["Multiplier"] == 3 else "")
                                if row["Multiplier"] >= 2:
                                    tags.append((f"Captain{mult_label}", "green"))
                                elif row["is_vc"]:
                                    tags.append(("Vice Captain", "yellow"))
                                card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                render_list_card(
                                    f"{row['Player']} · {row['Team']}",
                                    tags,
                                    f'<span>GW Pts</span> <strong>{int(row["GW_Points"])}</strong>{mult_label} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                    img_url=card_img,
                                )
                            if not user_bench.empty:
                                st.markdown("##### 🪑 Bench")
                                for _, row in user_bench.iterrows():
                                    sub_idx = int(row["order"]) - 11
                                    card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                    render_list_card(
                                        f"{row['Player']} · {row['Team']}",
                                        [(f"Sub {sub_idx} ({row['Pos']})", "gray")],
                                        f'<span>GW Pts</span> {int(row["Raw_GW_Pts"])} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                        img_url=card_img,
                                    )

                    with col_news:
                        st.markdown("#### ℹ️ Match Intel")
                        if comp_data:
                            if super_team_mode:
                                st.info(f"🌟 **{comp_title}** features the theoretical highest scorers with **{comp_pts} points**.")
                            else:
                                st.info(f"👑 **{comp_title}** scored **{comp_pts} points** in GW{selected_eval_gw}.")
                        else:
                            st.info("Live scoring in progress. Top performer updating as fixtures conclude.")

                        flagged_players = squad_df[
                            (squad_df["Status"] != "a") &
                            (squad_df["News"].notna()) &
                            (squad_df["News"] != "") &
                            (squad_df["News"] != "None")
                        ]
                        if not flagged_players.empty:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("##### ⚠️ Availability Flags")
                            for _, row in flagged_players.iterrows():
                                chance_val = row["Chance"]
                                chance_str = f" ({int(float(chance_val))}% chance)" if pd.notna(chance_val) and str(chance_val).strip() not in ("", "None") else ""
                                st.warning(f"**{row['Player']}**{chance_str}: {row['News']}")

            # ── SCENARIO B: UPCOMING GAMEWEEKS ────────────────────────────────
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

                if super_team_mode:
                    comp_xi, comp_bench, comp_formation = get_cached_league_super_15(
                        conn, current_gw, selected_eval_gw
                    )
                    comp_target_label = "Super Team"
                    comp_badge_icon = "👑"
                else:
                    comp_xi, comp_bench, comp_formation = get_cached_league_dream_15(
                        conn, current_gw, selected_eval_gw, total_team_value
                    )
                    comp_target_label = "Budget Dream 11"
                    comp_badge_icon = "🌟"

                comp_proj_xi_pts = comp_xi["Proj_Pts"].sum()

                st.markdown(
                    f"""
                    <div style="background-color: {banner_bg}; border: 1px solid {banner_border}; border-radius: 10px; padding: 1.2rem; margin: 0.5rem 0 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                            <span style="font-size: 1.1rem; font-weight: 700; color: {banner_title_col};">GW{selected_eval_gw} Squad Rating</span>
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
                    delta=f"{user_proj_xi_pts - comp_proj_xi_pts:+.1f} vs {comp_target_label}",
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
                        if pitch_view:
                            render_pitch_component(optimal_xi, optimal_bench, is_live=False)
                        else:
                            for idx, (_, row) in enumerate(optimal_xi.iterrows()):
                                tags = [(row["Pos"], "blue"), (f"FDR {row['FDR']}", "gray")]
                                mult_label = ""
                                if idx == 0:
                                    tags.append(("Captain (2x)", "green"))
                                    mult_label = " (2x)"
                                elif idx == 1:
                                    tags.append(("Vice Captain", "yellow"))
                                card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                render_list_card(
                                    f"{row['Player']} · {row['Team']}",
                                    tags,
                                    f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> <strong>{fmt_num(row["Proj_Pts"], ".1f")}</strong>{mult_label} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                    img_url=card_img,
                                )
                            if not optimal_bench.empty:
                                st.markdown("##### 🪑 Projected Bench")
                                for idx, (_, row) in enumerate(optimal_bench.iterrows()):
                                    sub_label = "Sub GKP" if row["Pos"] == "GKP" else f"Sub {idx}"
                                    card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                    render_list_card(
                                        f"{row['Player']} · {row['Team']}",
                                        [(sub_label, "gray"), (f"FDR {row['FDR']}", "gray")],
                                        f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> {fmt_num(row["Proj_Pts"], ".1f")} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                        img_url=card_img,
                                    )

                    with col_right:
                        st.markdown(
                            f"#### {comp_badge_icon} {comp_target_label} · GW{selected_eval_gw} "
                            f"({comp_formation} · {comp_proj_xi_pts:.1f} xP)"
                        )
                        if pitch_view:
                            render_pitch_component(comp_xi, comp_bench, is_live=False)
                        else:
                            for idx, (_, row) in enumerate(comp_xi.iterrows()):
                                tags = [(row["Pos"], "blue"), (f"FDR {row['FDR']}", "gray")]
                                mult_label = ""
                                if idx == 0:
                                    tags.append(("Captain (2x)", "green"))
                                    mult_label = " (2x)"
                                elif idx == 1:
                                    tags.append(("Vice Captain", "yellow"))
                                card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                render_list_card(
                                    f"{row['Player']} · {row['Team']}",
                                    tags,
                                    f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> <strong>{fmt_num(row["Proj_Pts"], ".1f")}</strong>{mult_label} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                    img_url=card_img,
                                )
                            if not comp_bench.empty:
                                st.markdown("##### 🪑 Dream Bench")
                                for idx, (_, row) in enumerate(comp_bench.iterrows()):
                                    sub_label = "Sub GKP" if row["Pos"] == "GKP" else f"Sub {idx}"
                                    card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                    render_list_card(
                                        f"{row['Player']} · {row['Team']}",
                                        [(sub_label, "gray"), (f"FDR {row['FDR']}", "gray")],
                                        f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> {fmt_num(row["Proj_Pts"], ".1f")} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                        img_url=card_img,
                                    )
                else:
                    col_squad, col_news = st.columns([7, 3])
                    with col_squad:
                        st.markdown(
                            f"#### 👤 Your Optimal XI · GW{selected_eval_gw} "
                            f"({optimal_formation} · {user_proj_xi_pts:.1f} xP)"
                        )
                        if pitch_view:
                            render_pitch_component(optimal_xi, optimal_bench, is_live=False)
                        else:
                            for idx, (_, row) in enumerate(optimal_xi.iterrows()):
                                tags = [(row["Pos"], "blue")]
                                mult_label = " (2x)" if row["Multiplier"] == 2 else (" (3x)" if row["Multiplier"] == 3 else "")
                                if row["Multiplier"] >= 2:
                                    tags.append((f"Captain{mult_label}", "green"))
                                elif row["is_vc"]:
                                    tags.append(("Vice Captain", "yellow"))
                                card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                render_list_card(
                                    f"{row['Player']} · {row['Team']}",
                                    tags,
                                    f'<span>GW Pts</span> <strong>{int(row["GW_Points"])}</strong>{mult_label} · <span>Season</span> {int(row["Season_Points"])} pts · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                    img_url=card_img,
                                )
                            if not optimal_bench.empty:
                                st.markdown("##### 🪑 Projected Bench")
                                for idx, (_, row) in enumerate(optimal_bench.iterrows()):
                                    sub_label = "Sub GKP" if row["Pos"] == "GKP" else f"Sub {idx}"
                                    card_img = get_player_img_url(row.get("photo"), row.get("code"))
                                    render_list_card(
                                        f"{row['Player']} · {row['Team']}",
                                        [(sub_label, "gray"), (f"FDR {row['FDR']}", "gray")],
                                        f'<span>Fixture</span> {row["Opponent"]} · <span>Proj Pts</span> {fmt_num(row["Proj_Pts"], ".1f")} · <span>Cost</span> £{fmt_num(row["Cost"], ".1f")}',
                                        img_url=card_img,
                                    )

                    with col_news:
                        st.markdown("#### 📰 Squad News")
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