import sqlite3
import pandas as pd
from tabs.transfer_analyzer import solve_chip_transfers_pulp
import time

conn = sqlite3.connect('fpl.db')

# Get all players
df = pd.read_sql('''
    SELECT p.id, p.code, p.photo, p.web_name AS Player, p.team AS team_id,
           t.short_name AS Team,
           CASE p.element_type WHEN 1 THEN 'GKP' WHEN 2 THEN 'DEF' WHEN 3 THEN 'MID' WHEN 4 THEN 'FWD' END AS Pos,
           p.now_cost / 10.0 AS Cost, p.minutes AS minutes,
           p.total_points AS Season_Points, p.form AS Form, p.points_per_game AS PPG,
           p.status AS Status, p.chance_of_playing_next_round AS Chance, p.news AS News
    FROM players p
    INNER JOIN teams t ON p.team = t.id
''', conn)

df['Horizon_xP'] = df['Cost'] * 1.5  # mock xP
df['Status'] = 'a'
df['Chance'] = 100

current_squad_df = df.head(15).copy()

start = time.time()
res, swaps = solve_chip_transfers_pulp(
    current_squad_df=current_squad_df,
    candidate_league_df=df,
    team_value=100.0,
    locked_player_ids=[],
    target_in_player_ids=[],
    force_out_player_ids=[],
    blocked_in_player_ids=[],
    is_free_hit=True
)
print(f"Solved in {time.time() - start:.2f}s")
print(res.shape)
