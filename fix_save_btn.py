import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

btn_pattern = r'(if st\.button\(":material/save:Save Transfer Plan for Simulator", key="save_transfer_sim_btn", type="primary", use_container_width=True\):\n\s*)(st\.toast\("Transfer Plan Saved! Navigate to Match Simulator to run scenarios\.", icon=":material/check_circle:"\))'

btn_repl = r'''\1st.session_state["transfer_result"] = {
          "transferred_squad_df":transferred_squad_df,
          "swaps":swaps,
          "curr_squad_horizon":curr_squad_horizon,
          "locked_players":locked_players,
          "targeted_in_players":targeted_in_players
        }
        \2'''

text = re.sub(btn_pattern, btn_repl, text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Fixed save button")
