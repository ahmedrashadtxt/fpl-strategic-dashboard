import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'(\s*)transferred_squad_df, swaps = solve_multi_gw_transfers\(\n\s*current_squad_df=curr_squad_horizon,\n\s*candidate_league_df=solver_candidate_df,\n\s*bank=bank_balance,\n\s*num_transfers=total_allowed_transfers,\n\s*locked_player_ids=locked_players,\n\s*target_in_player_ids=targeted_in_players,\n\s*force_out_player_ids=force_out_players,\n\s*blocked_in_player_ids=blocked_in_players,\n\s*min_avg_minutes=min_avg_mins,\n\s*\)'

replacement = r'''\1if chip_mode in [":material/style:  Wildcard", ":material/bolt:  Free Hit"]:
\1    transferred_squad_df, swaps = solve_chip_transfers_pulp(
\1        current_squad_df=curr_squad_horizon,
\1        candidate_league_df=league_eval_df,
\1        team_value=team_val,
\1        locked_player_ids=locked_players,
\1        target_in_player_ids=targeted_in_players,
\1        force_out_player_ids=force_out_players,
\1        blocked_in_player_ids=blocked_in_players,
\1        is_free_hit=(chip_mode == ":material/bolt:  Free Hit"),
\1    )
\1else:
\1    transferred_squad_df, swaps = solve_multi_gw_transfers(
\1        current_squad_df=curr_squad_horizon,
\1        candidate_league_df=solver_candidate_df,
\1        bank=bank_balance,
\1        num_transfers=total_allowed_transfers,
\1        locked_player_ids=locked_players,
\1        target_in_player_ids=targeted_in_players,
\1        force_out_player_ids=force_out_players,
\1        blocked_in_player_ids=blocked_in_players,
\1        min_avg_minutes=min_avg_mins,
\1    )'''

text = re.sub(pattern, replacement, text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Routed chip modes to pulp!")
