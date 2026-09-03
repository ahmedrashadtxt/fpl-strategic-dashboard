import sqlite3; conn=sqlite3.connect('fpl.db'); print(conn.execute('SELECT web_name, status, chance_of_playing_next_round, can_select FROM players WHERE web_name LIKE ''%Kulusevski%''').fetchall())
