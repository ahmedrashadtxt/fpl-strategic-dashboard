import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

tabs_pattern = r'tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st\.tabs\(\s*\[\s*"Squad Analyzer",\s*"Transfer Solver",\s*"Match Simulator",\s*"Audit Journal",\s*"Expected Stats",\s*"Defensive Contributions",\s*"Rolling Form",\s*"Fixture Ticker",\s*"Transfer Market",\s*\]\s*\)'
tabs_repl = '''tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
    [
        "Squad Analyzer",
        "Transfer Solver",
        "Match Simulator",
        "Expected Stats",
        "Defensive Contributions",
        "Rolling Form",
        "Fixture Ticker",
        "Transfer Market",
        "Audit Journal",
    ]
)'''
text = re.sub(tabs_pattern, tabs_repl, text, flags=re.DOTALL)

render_block_pattern = r'with tab1:.*?with tab9:\s*render_transfer_market_tab\(conn, events_df, current_gw\)'
render_block_repl = '''with tab1:
    render_squad_analyzer_tab(conn, events_df, current_gw)
with tab2:
    render_transfer_analyzer_tab(conn, events_df, current_gw)
with tab3:
    render_simulator_tab(conn, events_df, current_gw)
with tab4:
    render_expected_stats_tab(conn, events_df, current_gw)
with tab5:
    render_defensive_stats_tab(conn, events_df, current_gw)
with tab6:
    render_rolling_form_tab(conn, events_df, current_gw)
with tab7:
    render_fixture_ticker_tab(conn, events_df, current_gw)
with tab8:
    render_transfer_market_tab(conn, events_df, current_gw)
with tab9:
    render_audit_journal_tab(conn, events_df, current_gw)'''
text = re.sub(render_block_pattern, render_block_repl, text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated tab order")
