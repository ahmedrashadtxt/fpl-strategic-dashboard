import re

with open('app.py', 'r', encoding='utf-8') as f:
  text = f.read()

render_block_pattern = r'with tab1:.*?with tab7:\s*render_transfer_market_tab\(conn, current_gw\)'
render_block_repl = '''with tab1:
  render_squad_analyzer_tab(conn, events_df, current_gw)
with tab2:
  render_transfer_analyzer_tab(conn, events_df, current_gw)
with tab3:
  render_simulator_tab(conn, events_df, current_gw)
with tab4:
  render_expected_stats_tab(conn, current_gw)
with tab5:
  render_defensive_stats_tab(conn, current_gw)
with tab6:
  render_rolling_form_tab(conn, current_gw, teams_fdr_map)
with tab7:
  render_fixture_ticker_tab(conn, current_gw)
with tab8:
  render_transfer_market_tab(conn, current_gw)
with tab9:
  render_audit_journal_tab(conn, events_df, current_gw)'''

text = re.sub(render_block_pattern, render_block_repl, text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Fixed tab rendering")
