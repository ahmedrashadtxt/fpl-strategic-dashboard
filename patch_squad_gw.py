import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r"        import time\n        now_epoch = int\(time\.time\(\)\)\n\n        finished_gw_ids =.*?\n        next_gw_id = upcoming_gws\[0\] if upcoming_gws else current_gw", re.DOTALL)

new_logic = '''        import time
        now_epoch = int(time.time())

        finished_gw_ids = []
        ongoing_gw_ids = []
        upcoming_gws = []

        for _, r in events_df.iterrows():
            gw_id = int(r["id"])
            
            # Robust boolean parsing to handle SQLite/Pandas type variations (1, "1", True, "True")
            is_fin = str(r.get("finished", "")).strip().lower() in ["1", "true", "yes"]
            is_cur = str(r.get("is_current", "")).strip().lower() in ["1", "true", "yes"]
            
            try:
                dl_epoch = int(r.get("deadline_time_epoch", 2000000000))
            except (ValueError, TypeError):
                dl_epoch = 2000000000
                
            if is_fin:
                finished_gw_ids.append(gw_id)
            elif is_cur or dl_epoch <= now_epoch:
                ongoing_gw_ids.append(gw_id)
            else:
                upcoming_gws.append(gw_id)

        ongoing_gw = ongoing_gw_ids[0] if ongoing_gw_ids else None
        last_finished_gw = max(finished_gw_ids) if finished_gw_ids else None
        next_gw_id = upcoming_gws[0] if upcoming_gws else current_gw'''

new_text = pattern.sub(new_logic, text)

if new_text != text:
    with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Patched squad_analyzer.py")
else:
    print("Regex failed to match")
