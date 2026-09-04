import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Patch fetch_live_gameweek_points
old_fetch = '''                    "bps": item["stats"]["bps"]
                }
                for item in res.json().get("elements", [])'''

new_fetch = '''                    "bps": item["stats"]["bps"],
                    "explain": item.get("explain", [])
                }
                for item in res.json().get("elements", [])'''

text = text.replace(old_fetch, new_fetch)

# 2. Patch squad_df and comp_df Live_Explain
old_squad = '''        squad_df["Live_BPS"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("bps", 0))'''
new_squad = '''        squad_df["Live_BPS"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("bps", 0))
        squad_df["Live_Explain"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("explain", []))'''
text = text.replace(old_squad, new_squad)

old_comp = '''                comp_df["Live_BPS"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("bps", 0))'''
new_comp = '''                comp_df["Live_BPS"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("bps", 0))
                comp_df["Live_Explain"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("explain", []))'''
text = text.replace(old_comp, new_comp)

# 3. Rewrite build_player_tooltip
pattern = re.compile(r"def build_player_tooltip\(p: pd\.Series, is_live: bool = False\) -> str:.*?(?=@st\.cache_data)", re.DOTALL)

new_func = '''def build_player_tooltip(p: pd.Series, is_live: bool = False) -> str:
    import html
    player_name = html.escape(str(p.get("Player", "")))
    pos = html.escape(str(p.get("Pos", "")))
    team = html.escape(str(p.get("Team", "")))
    cost = p.get("Cost", 0.0)
    cost_str = f"\u00a3{fmt_num(cost, '.1f')}m" if cost else "\u00a3"

    roll_pts = fmt_num(p.get("roll_pts", 0.0), ".1f")
    roll_xgi90 = fmt_num(p.get("roll_xgi90", 0.0), ".2f")
    roll_mins = int(p.get("roll_mins", 0))
    fdr5 = int(p.get("fdr5", 15))
    fdr5_cls = "tt-fdr-easy" if fdr5 <= 11 else ("tt-fdr-med" if fdr5 <= 14 else "tt-fdr-hard")

    form = fmt_num(p.get("Form", 0.0), ".1f")
    ppg = fmt_num(p.get("PPG", 0.0), ".1f")
    opp = html.escape(str(p.get("Opponent", "-")))

    status = str(p.get("Status", "a"))
    news = str(p.get("News", ""))
    news_row = ""
    if status != "a" and news and news != "None":
        clean_news = html.escape(news[:40] + ("..." if len(news) > 40 else ""))
        news_row = f'<div class="tt-row tt-news"><span>[!] {clean_news}</span></div>'

    explain_list = p.get("Live_Explain")
    if not isinstance(explain_list, list):
        explain_list = []
    
    match_started = is_live and len(explain_list) > 0

    if match_started:
        pts = int(p.get("Raw_GW_Pts", 0))
        body_content = (
            f'<div class="tt-row"><span class="tt-label">GW Points:</span>'
            f'<span class="tt-val" style="color:#4ade80; font-weight:700;">{pts} pts</span></div>'
        )
        
        stat_map = {
            "minutes": "Minutes",
            "goals_scored": "Goals",
            "assists": "Assists",
            "clean_sheets": "Clean Sheet",
            "goals_conceded": "Goals Conceded",
            "own_goals": "Own Goals",
            "penalties_saved": "Penalties Saved",
            "penalties_missed": "Penalties Missed",
            "yellow_cards": "Yellow Card",
            "red_cards": "Red Card",
            "saves": "Saves",
            "bonus": "Bonus"
        }
        
        agg_stats = {}
        for fixture in explain_list:
            for stat in fixture.get("stats", []):
                ident = stat["identifier"]
                if stat["points"] != 0 or ident == "minutes":
                    if ident not in agg_stats:
                        agg_stats[ident] = {"points": 0, "value": 0}
                    agg_stats[ident]["points"] += stat["points"]
                    agg_stats[ident]["value"] += stat["value"]
                    
        if agg_stats:
            body_content += f'<hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 6px 0;">'
            for ident, data in agg_stats.items():
                label = stat_map.get(ident, ident.replace("_", " ").title())
                val_str = str(data["value"])
                if ident == "minutes":
                    val_str += "\\'"
                    
                pt_val = data["points"]
                if pt_val > 0:
                    pt_color = "#4ade80"
                    pt_str = f"+{pt_val}"
                elif pt_val < 0:
                    pt_color = "#ef4444"
                    pt_str = f"{pt_val}"
                else:
                    pt_color = "#94a3b8"
                    pt_str = f"{pt_val}"
                    
                body_content += (
                    f'<div class="tt-row"><span class="tt-label" style="font-size: 0.70rem; color: #94a3b8; padding-left: 5px;">&bull; {label} ({val_str})</span>'
                    f'<span class="tt-val" style="color:{pt_color}; font-size: 0.75rem;">{pt_str}</span></div>'
                )
    else:
        proj = fmt_num(p.get("Proj_Pts", 0.0), ".1f")
        body_content = (
            f'<div class="tt-row"><span class="tt-label">Fixture:</span>'
            f'<span class="tt-val">{opp}</span></div>'
            f'<div class="tt-row"><span class="tt-label">Projected xP:</span>'
            f'<span class="tt-val" style="color:#60a5fa;">{proj} xP</span></div>'
            f'<div class="tt-row"><span class="tt-label">Avg Pts (L5):</span><span class="tt-val">{roll_pts}</span></div>'
            f'<div class="tt-row"><span class="tt-label">xGI / 90 (L5):</span><span class="tt-val">{roll_xgi90}</span></div>'
            f'<div class="tt-row"><span class="tt-label">Avg Mins (L5):</span><span class="tt-val">{roll_mins}m</span></div>'
            f'<div class="tt-row"><span class="tt-label">Next 5 FDR:</span><span class="tt-val {fdr5_cls}">{fdr5}</span></div>'
            f'<div class="tt-row"><span class="tt-label">Form / PPG:</span><span class="tt-val">{form} / {ppg}</span></div>'
        )

    return (
        f'<div class="player-tooltip-card">'
        f'<div class="tt-header">'
        f'<span class="tt-name">{player_name}</span>'
        f'<span class="tt-badge">{team} &middot; {pos} &middot; {cost_str}</span>'
        f'</div>'
        f'<div class="tt-body">'
        f'{body_content}'
        f'{news_row}'
        f'</div></div>'
    )

'''

text = pattern.sub(new_func, text)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("All patches applied.")
