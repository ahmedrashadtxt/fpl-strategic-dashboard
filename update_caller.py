import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

caller_pattern = r'if chip_mode in \[":material/style:  Wildcard", ":material/bolt:  Free Hit"\]:.*?transferred_squad_df, swaps = solve_chip_transfers_pulp\(.*?blocked_in_player_ids=blocked_in_players,\s*\)'

caller_repl = '''if chip_mode in [":material/style:  Wildcard", ":material/bolt:  Free Hit"]:
            transferred_squad_df, swaps = solve_chip_transfers_pulp(
                current_squad_df=curr_squad_horizon,
                candidate_league_df=solver_candidate_df,
                team_value=team_val,
                locked_player_ids=locked_players,
                target_in_player_ids=targeted_in_players,
                force_out_player_ids=forced_out_players,
                blocked_in_player_ids=blocked_in_players,
                is_free_hit=(chip_mode == ":material/bolt:  Free Hit"),
            )'''

text = re.sub(caller_pattern, caller_repl, text, flags=re.DOTALL)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated caller")
