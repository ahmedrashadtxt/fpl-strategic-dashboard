import sqlite3
conn = sqlite3.connect('fpl.db')
pick_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] # dummy
placeholders = ','.join(['?']*len(pick_ids))
cur = conn.cursor()
cur.execute(f'SELECT SUM(now_cost) FROM players WHERE id IN ({placeholders})', pick_ids)
print(cur.fetchone()[0])
