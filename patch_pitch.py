import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_live_pill = '''            if is_live:
                pts = int(p.get("GW_Points", 0))
                mult_txt = f" ({mult}x)" if mult > 1 else ""
                pts_sub = f"{pts} pts{mult_txt}"
                sub_color = "#4ade80" if pts >= 6 else "#f8fafc"
                stat_pill_content = f'<span style="color: {sub_color};">{pts_sub}</span>'
            else:'''

new_live_pill = '''            if is_live:
                pts = int(p.get("GW_Points", 0))
                mult_txt = f" ({mult}x)" if mult > 1 else ""
                pts_sub = f"{pts} pts{mult_txt}"
                
                live_mins = p.get("Live_Mins", 0)
                live_bonus = p.get("Live_Bonus", 0)
                live_bps = p.get("Live_BPS", 0)
                
                mins_str = f"{int(live_mins)}'" if live_mins > 0 else "0'"
                bonus_str = f" (+{int(live_bonus)}B)" if live_bonus > 0 else (f" ({int(live_bps)} bps)" if live_bps > 0 else "")
                
                sub_color = "#4ade80" if pts >= 6 else "#f8fafc"
                stat_pill_content = (
                    f'<span style="color: {sub_color}; font-weight: 700; display: block;">{pts_sub}</span>'
                    f'<span style="color: #94a3b8; font-size: 0.62rem; display: block;">{mins_str}{bonus_str}</span>'
                )
            else:'''

text = text.replace(old_live_pill, new_live_pill)

old_bench_live_pill = '''            if is_live:
                pts = int(p.get("GW_Points", 0))
                mult_txt = f" ({mult}x)" if mult > 1 else ""
                pts_sub = f"{pts} pts{mult_txt}"
                sub_color = "#4ade80" if pts >= 6 else "#f8fafc"
                stat_pill_content = f'<span style="color: {sub_color};">{pts_sub}</span>'
            else:'''

new_bench_live_pill = '''            if is_live:
                pts = int(p.get("GW_Points", 0))
                mult_txt = f" ({mult}x)" if mult > 1 else ""
                pts_sub = f"{pts} pts{mult_txt}"
                
                live_mins = p.get("Live_Mins", 0)
                live_bonus = p.get("Live_Bonus", 0)
                live_bps = p.get("Live_BPS", 0)
                
                mins_str = f"{int(live_mins)}'" if live_mins > 0 else "0'"
                bonus_str = f" (+{int(live_bonus)}B)" if live_bonus > 0 else (f" ({int(live_bps)} bps)" if live_bps > 0 else "")
                
                sub_color = "#4ade80" if pts >= 6 else "#f8fafc"
                stat_pill_content = (
                    f'<span style="color: {sub_color}; font-weight: 700; display: block;">{pts_sub}</span>'
                    f'<span style="color: #94a3b8; font-size: 0.62rem; display: block;">{mins_str}{bonus_str}</span>'
                )
            else:'''

# There is a second occurrence for the bench players
text = text.replace(old_bench_live_pill, new_bench_live_pill)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched pitch component")
