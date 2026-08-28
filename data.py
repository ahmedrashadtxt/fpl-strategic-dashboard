import os
from pathlib import Path
import sqlite3
import pandas as pd
import requests
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fpl.db"


def get_connection():
    """Returns a SQLite connection to fpl.db."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


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


def get_global_gameweek_info(conn):
    """Fetches current and next gameweek metadata."""
    events_df = pd.read_sql(
        "SELECT id, name, is_current, is_next, finished FROM events", conn
    )
    next_gw_row = events_df[events_df["is_next"] == 1]
    current_gw = int(next_gw_row["id"].values[0]) if not next_gw_row.empty else 1
    gw_name = (
        next_gw_row["name"].values[0]
        if not next_gw_row.empty
        else f"Gameweek {current_gw}"
    )
    return events_df, current_gw, gw_name


def get_summary_stats(conn):
    """Fetches global player tracking, signal counts, and transfer trends."""
    return pd.read_sql(
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


@st.cache_data(ttl=3600, show_spinner=False)
def get_teams_fdr_map(_conn, current_gw: int):
    """Precalculates and caches 5-GW fixture difficulty ratings per club."""
    fixtures_5gw = pd.read_sql(
        """
        SELECT event, team_h, team_a, team_h_difficulty, team_a_difficulty
        FROM fixtures
        WHERE event >= ? AND event < ? AND finished = 0
    """,
        _conn,
        params=[current_gw, current_gw + 5],
    )

    teams_fdr_map = {}
    for t_id in range(1, 21):
        h_diff = fixtures_5gw[fixtures_5gw["team_h"] == t_id]["team_h_difficulty"].sum()
        a_diff = fixtures_5gw[fixtures_5gw["team_a"] == t_id]["team_a_difficulty"].sum()
        teams_fdr_map[t_id] = int(h_diff + a_diff) if (h_diff + a_diff) > 0 else 15
    return teams_fdr_map


@st.cache_data(ttl=3600, show_spinner=False)
def get_historical_player_baselines(_conn):
    """
    Computes career weighted Points per 90 across previous seasons.
    Most recent season receives a 2x weighting factor.
    """
    try:
        query = """
        WITH ranked_seasons AS (
            SELECT 
                element_id,
                season_name,
                total_points,
                minutes,
                ROW_NUMBER() OVER (PARTITION BY element_id ORDER BY season_name DESC) AS recency_rank
            FROM player_past_seasons
            WHERE minutes >= 450
        )
        SELECT 
            element_id,
            (SUM(total_points * CASE WHEN recency_rank = 1 THEN 2.0 ELSE 1.0 END) * 1.0 / 
             NULLIF(SUM(minutes * CASE WHEN recency_rank = 1 THEN 2.0 ELSE 1.0 END), 0)) * 90.0 AS hist_pts_per_90,
            SUM(minutes) AS hist_total_mins
        FROM ranked_seasons
        GROUP BY element_id;
        """
        df = pd.read_sql(query, _conn)
        if not df.empty and "element_id" in df.columns:
            return df.set_index("element_id")
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def get_manager_squad_ids(mgr_id: str, target_gw: int):
    """Fetches and caches the list of player element IDs in the user's squad."""
    if not mgr_id:
        return []
    try:
        gw = target_gw if target_gw >= 1 else 1
        picks_url = (
            f"https://fantasy.premierleague.com/api/entry/{mgr_id}/event/{gw}/picks/"
        )
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


@st.cache_data(ttl=600, show_spinner=False)
def get_motw_data(target_gw: int):
    """Fetches Manager of the Week picks or Dream Team fallback for finished gameweeks."""
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
            "manager_name": "Kings of the Gameweek",
            "player_name": "Official Dream Team",
            "total_score": top_pts,
            "picks": picks_list,
        }
    except Exception:
        return None


def get_fixture_for_team(fixtures_df, team_id, target_gw):
    """Extracts opponent, venue, and FDR for a given team and gameweek."""
    match = fixtures_df[
        (fixtures_df["GW"] == target_gw)
        & (
            (fixtures_df["team_h_id"] == team_id)
            | (fixtures_df["team_a_id"] == team_id)
        )
    ]
    if match.empty:
        return {"opponent": "Blank", "fdr": 5, "is_home": False}

    row = match.iloc[0]
    if row["team_h_id"] == team_id:
        return {
            "opponent": f"{row['Away_Team']} (H)",
            "fdr": int(row["Home_Diff"]),
            "is_home": True,
        }
    return {
        "opponent": f"{row['Home_Team']} (A)",
        "fdr": int(row["Away_Diff"]),
        "is_home": False,
    }


def calculate_projected_points(player_row, fix_info, current_gw_num, hist_baselines_df=None):
    """
    Probabilistic Expected Points (xP) Model.
    Uses Empirical Bayesian Shrinkage to blend historical baseline performance
    with current-season underlying metrics and form.
    """
    pos = str(player_row.get("Pos", "MID")).upper()
    fdr = fix_info.get("fdr", 3)
    is_home = fix_info.get("is_home", False)
    p_id = player_row.get("id")

    season_mins = float(player_row.get("minutes", 0) or 0.0)
    recent_avg_mins = float(
        player_row.get("Rolling_Avg_Mins", season_mins) or 0.0
    )

    if current_gw_num > 1 and recent_avg_mins < 15 and season_mins < 15:
        starter_factor = 0.0
    elif recent_avg_mins >= 60 or season_mins >= 60:
        starter_factor = 1.0
    else:
        starter_factor = max(
            0.1, min(1.0, max(recent_avg_mins, season_mins) / 90.0)
        )

    if starter_factor == 0.0:
        return 0.0

    # ── Bayesian Shrinkage Weights ───────────────────────────────────────────
    w_curr = min(1.0, season_mins / 900.0) if current_gw_num > 1 else 0.0
    w_hist = 1.0 - w_curr

    # Default baseline points per 90 if player has no historical Premier League records
    pos_default_pts = {"GKP": 3.8, "DEF": 3.6, "MID": 4.2, "FWD": 4.5}
    hist_pts_90 = pos_default_pts.get(pos, 4.0)

    if hist_baselines_df is not None and not hist_baselines_df.empty and p_id in hist_baselines_df.index:
        val = hist_baselines_df.loc[p_id, "hist_pts_per_90"]
        if pd.notna(val) and float(val) > 0:
            hist_pts_90 = float(val)

    curr_ppg = float(player_row.get("PPG", 0.0) or 0.0)
    form = float(player_row.get("Form", 0.0) or 0.0)

    # Current rate estimate
    curr_base_rate = (curr_ppg * 0.7) + (form * 0.3) if curr_ppg > 0 else hist_pts_90
    blended_base_rate = (w_curr * curr_base_rate) + (w_hist * hist_pts_90)

    # Fixture difficulty & home advantage
    fdr_cs_probs = {2: 0.44, 3: 0.28, 4: 0.16, 5: 0.08}
    cs_prob = fdr_cs_probs.get(fdr, 0.25) * (1.15 if is_home else 0.88)
    atk_mult = max(0.4, (6.0 - fdr) / 3.0) * (1.08 if is_home else 0.94)

    xgi_90 = float(player_row.get("xGI_per_90", 0.0) or 0.0)
    xg_season = float(player_row.get("expected_goals", 0.0) or 0.0)
    xa_season = float(player_row.get("expected_assists", 0.0) or 0.0)

    app_pts = 2.0 * starter_factor

    if pos in ("GKP", "DEF"):
        pts_per_goal = 6.0
        cs_pts = 4.0
        def_concede_deduction = 0.55 if fdr >= 4 else 0.20
        xp_clean_sheet = (cs_prob * cs_pts) * starter_factor
        xp_attacking = (xgi_90 * pts_per_goal * 0.45) * atk_mult * starter_factor
        xp_saves_bonus = 1.0 if pos == "GKP" else 0.3
        
        # Combine blended baseline with match-specific expected outputs
        xp = (
            (blended_base_rate * 0.4)
            + app_pts
            + xp_clean_sheet
            + xp_attacking
            + (xp_saves_bonus * starter_factor)
            - def_concede_deduction
        )

    elif pos == "MID":
        pts_per_goal = 5.0
        pts_per_assist = 3.0
        xp_clean_sheet = cs_prob * 1.0 * starter_factor
        est_xg = (xg_season / max(1, current_gw_num)) if xg_season > 0 else (xgi_90 * 0.6)
        est_xa = (xa_season / max(1, current_gw_num)) if xa_season > 0 else (xgi_90 * 0.4)
        xp_attacking = (((est_xg * pts_per_goal) + (est_xa * pts_per_assist)) * atk_mult * starter_factor)
        
        xp = (blended_base_rate * 0.45) + app_pts + xp_clean_sheet + xp_attacking

    else:  # FWD
        pts_per_goal = 4.0
        pts_per_assist = 3.0
        est_xg = (xg_season / max(1, current_gw_num)) if xg_season > 0 else (xgi_90 * 0.75)
        est_xa = (xa_season / max(1, current_gw_num)) if xa_season > 0 else (xgi_90 * 0.25)
        xp_attacking = (((est_xg * pts_per_goal) + (est_xa * pts_per_assist)) * atk_mult * starter_factor)

        xp = (blended_base_rate * 0.5) + app_pts + xp_attacking

    status = str(player_row.get("Status", "a"))
    chance = player_row.get("Chance")
    if status in ("i", "u", "s"):
        avail_mult = 0.0
    elif pd.notna(chance) and str(chance).strip() not in ("", "None"):
        avail_mult = float(chance) / 100.0
    else:
        avail_mult = 1.0

    return round(max(0.0, xp * avail_mult), 2)


def solve_optimal_xi(squad_df_evaluated):
    """Greedy Optimization Engine: Solves for highest scoring legal FPL XI and ordered bench."""
    gkps = squad_df_evaluated[squad_df_evaluated["Pos"] == "GKP"].sort_values(
        "Proj_Pts", ascending=False
    )
    defs = squad_df_evaluated[squad_df_evaluated["Pos"] == "DEF"].sort_values(
        "Proj_Pts", ascending=False
    )
    mids = squad_df_evaluated[squad_df_evaluated["Pos"] == "MID"].sort_values(
        "Proj_Pts", ascending=False
    )
    fwds = squad_df_evaluated[squad_df_evaluated["Pos"] == "FWD"].sort_values(
        "Proj_Pts", ascending=False
    )

    starter_gkp = gkps.head(1)
    bench_gkp = gkps.tail(max(0, len(gkps) - 1))

    mandatory_defs = defs.head(3)
    mandatory_mids = mids.head(2)
    mandatory_fwds = fwds.head(1)

    rem_pool = pd.concat(
        [defs.iloc[3:], mids.iloc[2:], fwds.iloc[1:]]
    ).sort_values("Proj_Pts", ascending=False)

    extra_starters = rem_pool.head(4)
    bench_outfield = rem_pool.tail(max(0, len(rem_pool) - 4))

    starters = pd.concat([
        starter_gkp,
        mandatory_defs,
        mandatory_mids,
        mandatory_fwds,
        extra_starters,
    ]).sort_values("Proj_Pts", ascending=False)

    bench = pd.concat([bench_gkp, bench_outfield])
    formation = f"{len(starters[starters['Pos'] == 'DEF'])}-{len(starters[starters['Pos'] == 'MID'])}-{len(starters[starters['Pos'] == 'FWD'])}"
    return starters, bench, formation